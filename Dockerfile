FROM python:3.11-slim

# Системные зависимости для Playwright и Camoufox
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libxtst6 \
    libxrandr2 \
    libasound2 \
    libatk1.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libpango-1.0-0 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Установка браузера для Playwright (используется Camoufox)
RUN playwright install chromium

# Ключевой шаг – установка браузера для Camoufox
RUN camoufox fetch

COPY server.py .

CMD ["python", "server.py"]
