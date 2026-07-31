FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости для playwright
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем браузеры для playwright (нужен для goblin-ai)
RUN python -m playwright install

COPY server.py .

CMD ["python", "server.py"]
