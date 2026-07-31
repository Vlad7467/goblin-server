FROM python:3.11-slim

WORKDIR /app

# Устанавливаем все возможные системные зависимости для браузеров и opencv
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm \
    libxkbcommon \
    libgbm \
    libasound2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    libgtk-3-0 \
    libxshmfence1 \
    libgl1 \
    libgomp1 \
    wget \
    unzip \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем питоновские зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем браузеры для playwright (используется goblin-ai)
RUN playwright install chromium
RUN playwright install-deps

# Дополнительно устанавливаем движок camoufox (если требуется)
RUN camoufox fetch || true

# Копируем сервер
COPY server.py .

CMD ["python", "server.py"]
