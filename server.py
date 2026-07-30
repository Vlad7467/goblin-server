import asyncio
import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from goblin import generate
import uvicorn

app = FastAPI(title="Goblin AI API")

class GenerateRequest(BaseModel):
    prompt: str
    model: str = "goblin-realistic"
    quality: str = "ultra"
    width: int = 1024
    height: int = 1024

@app.post("/generate")
async def generate_image(request: GenerateRequest):
    try:
        # Генерируем уникальное имя файла
        filename = f"{uuid.uuid4()}.png"
        output_path = os.path.join("/tmp", filename)

        # Запускаем генерацию
        await generate(
            prompt=request.prompt,
            model=request.model,
            output=output_path,
            quality=request.quality,
            aspect_ratio=f"{request.width}:{request.height}"
        )

        # Возвращаем URL для скачивания (Render отдаёт статику)
        return {
            "success": True,
            "image_url": f"/images/{filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/images/{filename}")
async def get_image(filename: str):
    file_path = os.path.join("/tmp", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path, media_type="image/png")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
