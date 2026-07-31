import os
import uuid
import asyncio
import logging
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from goblin import generate
    GOBLIN_AVAILABLE = True
except Exception as e:
    GOBLIN_AVAILABLE = False
    logger.error(f"Goblin-ai не загрузился: {e}")

app = FastAPI(title="Goblin AI Server")

class GenRequest(BaseModel):
    prompt: str
    model: str = "goblin-anime"      # легче, чем uncensored
    quality: str = "fast"            # быстрое качество
    width: int = 512                 # меньше памяти
    height: int = 512

@app.post("/generate")
async def generate_endpoint(req: GenRequest):
    if not GOBLIN_AVAILABLE:
        raise HTTPException(503, "Goblin-ai недоступен")
    try:
        out_path = f"/tmp/{uuid.uuid4()}.png"
        logger.info(f"Начало генерации: {req.model_dump()}, out_path={out_path}")
        
        # Запускаем синхронную функцию в потоке и получаем результат
        result = await asyncio.to_thread(
            generate,
            prompt=req.prompt,
            model=req.model,
            output=out_path,           # возможно, библиотека игнорирует этот аргумент
            quality=req.quality,
            width=req.width,
            height=req.height
        )
        logger.info(f"Генерация завершена, проверяем файл {out_path}")
        
        # Если файл не создался, но result не None – сохраняем result
        if not os.path.exists(out_path):
            logger.info(f"Файл не создан, пытаемся сохранить возвращаемое значение типа {type(result)}")
            if result is None:
                raise HTTPException(500, "Функция generate вернула None и не создала файл")
            if isinstance(result, bytes):
                with open(out_path, 'wb') as f:
                    f.write(result)
                logger.info(f"Сохранены байты в {out_path}")
            elif hasattr(result, 'save'):  # PIL Image или аналоги
                result.save(out_path)
                logger.info(f"Сохранён объект с методом save в {out_path}")
            else:
                # Если не байты и не картинка, попробуем записать как есть (строку?)
                logger.error(f"Неизвестный тип результата: {type(result)}")
                raise HTTPException(500, f"Неизвестный тип результата: {type(result)}")
        
        # Теперь файл должен существовать
        if not os.path.exists(out_path):
            raise HTTPException(500, f"Файл всё ещё не создан: {out_path}")
        
        # Читаем и возвращаем изображение
        with open(out_path, 'rb') as f:
            img_data = f.read()
        os.remove(out_path)  # удаляем оригинал
        fname = f"{uuid.uuid4()}.png"
        fpath = f"/tmp/{fname}"
        with open(fpath, 'wb') as f:
            f.write(img_data)
        logger.info(f"Изображение сохранено как {fpath}")
        return JSONResponse({"success": True, "image_url": f"/images/{fname}"})
    
    except Exception as e:
        logger.exception("Ошибка при генерации")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e), "traceback": traceback.format_exc()}
        )

@app.get("/images/{fname}")
async def get_image(fname: str):
    path = f"/tmp/{fname}"
    if not os.path.exists(path):
        raise HTTPException(404, "Not found")
    return FileResponse(path)

@app.get("/health")
async def health():
    return {"status": "ok", "goblin_available": GOBLIN_AVAILABLE}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
