import os
import uuid
import subprocess
import json
import tempfile
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Goblin AI Server (Stable)")

class GenerateRequest(BaseModel):
    prompt: str
    model: str = "goblin-anime-uncensored"  # Основная NSFW-модель
    quality: str = "ultra"
    width: int = 1024
    height: int = 1024

@app.post("/generate")
async def generate_image(request: GenerateRequest):
    try:
        filename = f"{uuid.uuid4()}.png"
        output_path = os.path.join("/tmp", filename)

        # Создаём временный Python-скрипт для вызова goblin
        script_content = f'''
import asyncio
from goblin import generate
import sys

async def main():
    await generate(
        prompt="{request.prompt}",
        model="{request.model}",
        output="{output_path}",
        quality="{request.quality}",
        aspect_ratio="{request.width}:{request.height}"
    )
    print("OK")

asyncio.run(main())
'''
        # Запускаем скрипт в отдельном процессе с таймаутом 120 секунд
        proc = subprocess.run(
            ["python", "-c", script_content],
            capture_output=True,
            text=True,
            timeout=120
        )

        if proc.returncode != 0:
            raise Exception(f"Ошибка генерации: {proc.stderr}")

        if not os.path.exists(output_path):
            raise Exception("Файл не создан")

        return {
            "success": True,
            "image_url": f"/images/{filename}"
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Генерация слишком долгая")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/images/{filename}")
async def get_image(filename: str):
    file_path = os.path.join("/tmp", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Изображение не найдено")
    return FileResponse(file_path, media_type="image/png")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)