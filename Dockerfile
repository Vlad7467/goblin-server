FROM python:3.11-slim

WORKDIR /app

# Устанавливаем только базовые утилиты (wget для playwright)
RUN apt-get update && apt-get install -y \
    wget \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем браузер chromium с зависимостями (это подтянет всё нужное)
RUN playwright install --with-deps chromium

COPY server.py .

CMD ["python", "server.py"]
