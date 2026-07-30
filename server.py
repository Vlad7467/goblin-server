import os
import uuid
import subprocess
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Goblin AI Server (Stable)")

class GenerateRequest(BaseModel):
    prompt: str
    model: str = "goblin-anime-uncensored"
    quality: str = "ultra"
    width: int = 1024
    height: int = 1024

@app.post("/generate")
async def generate_image(request: GenerateRequest):
    try:
        filename = f"{uuid.uuid4()}.png"
        output_path = os.path.join("/tmp", filename)

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
        proc = subprocess.run(
            ["python", "-c", script_content],
            capture_output=True,
            text=True,
            timeout=120
        )

        if proc.returncode != 0:
            raise Exception(f"Ошибка: {proc.stderr}")

        if not os.path.exists(output_path):
            raise Exception("Файл не создан")

        return {"success": True, "image_url": f"/images/{filename}"}
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Генерация слишком долгая")
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/images/{filename}")
async def get_image(filename: str):
    path = os.path.join("/tmp", filename)
    if not os.path.exists(path):
        raise HTTPException(404, "Not found")
    return FileResponse(path)

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
