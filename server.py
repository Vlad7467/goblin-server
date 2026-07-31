import os
import uuid
import asyncio
import aiohttp
import urllib.parse
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# Пытаемся импортировать goblin, но если ошибка — используем резерв
try:
    from goblin import generate
    GOBLIN_AVAILABLE = True
    print("[OK] Goblin-ai loaded")
except Exception as e:
    GOBLIN_AVAILABLE = False
    print(f"[WARN] Goblin-ai not available: {e}")

app = FastAPI(title="Goblin AI + Pollinations Fallback")

class GenerateRequest(BaseModel):
    prompt: str
    model: str = "goblin-anime-uncensored"
    quality: str = "ultra"
    width: int = 1024
    height: int = 1024

# ---- РЕЗЕРВНЫЙ ГЕНЕРАТОР (POLLINATIONS) ----
async def generate_pollinations(prompt: str, width=1024, height=1024):
    safe_prompt = f"{prompt}, photorealistic, 8k, high quality, masterpiece"
    encoded = urllib.parse.quote(safe_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&safe=false&model=flux-realism"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=30) as resp:
            if resp.status == 200 and 'image' in resp.headers.get('content-type', ''):
                return await resp.read()
            return None

# ---- ОСНОВНОЙ ГЕНЕРАТОР (С ПРИОРИТЕТОМ GOBLIN) ----
async def generate_image(request: GenerateRequest):
    # Если goblin доступен — пробуем его
    if GOBLIN_AVAILABLE:
        try:
            output_path = f"/tmp/{uuid.uuid4()}.png"
            await generate(
                prompt=request.prompt,
                model=request.model,
                output=output_path,
                quality=request.quality,
                aspect_ratio=f"{request.width}:{request.height}"
            )
            if os.path.exists(output_path):
                with open(output_path, 'rb') as f:
                    image_data = f.read()
                os.remove(output_path)
                return image_data
        except Exception as e:
            print(f"[GOBLIN ERROR] {e}")
            # Если goblin упал — идём в резерв

    # РЕЗЕРВ: POLLINATIONS
    print("[INFO] Using Pollinations fallback")
    return await generate_pollinations(request.prompt, request.width, request.height)

@app.post("/generate")
async def generate_endpoint(request: GenerateRequest):
    image_data = await generate_image(request)
    if image_data is None:
        raise HTTPException(500, "Не удалось сгенерировать изображение")
    
    # Сохраняем временный файл для отдачи
    filename = f"{uuid.uuid4()}.png"
    filepath = f"/tmp/{filename}"
    with open(filepath, 'wb') as f:
        f.write(image_data)
    
    return JSONResponse({
        "success": True,
        "image_url": f"/images/{filename}"
    })

@app.get("/images/{filename}")
async def get_image(filename: str):
    filepath = f"/tmp/{filename}"
    if not os.path.exists(filepath):
        raise HTTPException(404, "Not found")
    return FileResponse(filepath)

@app.get("/health")
async def health():
    return {"status": "ok", "goblin_available": GOBLIN_AVAILABLE}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
