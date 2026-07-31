import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# Импортируем как в документации goblin-ai[reference:3]
from goblin import generate

app = FastAPI(title="Goblin AI Server")

class GenRequest(BaseModel):
    prompt: str
    model: str = "goblin-anime-uncensored"  # 18+ модель[reference:4]
    quality: str = "ultra"
    width: int = 1024
    height: int = 1024

@app.post("/generate")
async def generate_endpoint(req: GenRequest):
    try:
        # Генерируем уникальное имя файла
        out_path = f"/tmp/{uuid.uuid4()}.png"
        
        # Вызываем generate как в примере[reference:5]
        await generate(
            prompt=req.prompt,
            model=req.model,
            output=out_path,
            quality=req.quality,
            width=req.width,
            height=req.height
        )
        
        # Проверяем, создался ли файл
        if not os.path.exists(out_path):
            raise Exception("Файл не создан")
        
        # Читаем и возвращаем
        with open(out_path, 'rb') as f:
            img_data = f.read()
        os.remove(out_path)
        
        # Сохраняем для отдачи по URL
        fname = f"{uuid.uuid4()}.png"
        fpath = f"/tmp/{fname}"
        with open(fpath, 'wb') as f:
            f.write(img_data)
        
        return JSONResponse({
            "success": True,
            "image_url": f"/images/{fname}"
        })
    except Exception as e:
        raise HTTPException(500, f"Ошибка: {str(e)}")

@app.get("/images/{fname}")
async def get_image(fname: str):
    path = f"/tmp/{fname}"
    if not os.path.exists(path):
        raise HTTPException(404, "Not found")
    return FileResponse(path)

@app.get("/health")
async def health():
    return {"status": "ok", "goblin_available": True}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
