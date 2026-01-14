FROM python:3.11-slim

# Установка системных зависимостей для Puppeteer и ClickHouse
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libxss1 \
    libxtst6 \
    libpangocairo-1.0-0 \
    libcairo-gobject2 \
    && rm -rf /var/lib/apt/lists/*

# Установка Node.js для Puppeteer
RUN wget -q -O - https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование requirements и установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Установка Puppeteer через npm (для pyppeteer требуется Chromium)
# pyppeteer установит Chromium автоматически при первом запуске

# Копирование исходного кода
COPY . .

# Создание пользователя для запуска приложения
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Устанавливаем PYTHONPATH и переменные для Puppeteer
ENV PYTHONPATH=/app
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/home/appuser/.local/share/pyppeteer/local-chromium/588429/chrome-linux/chrome

CMD ["python", "-m", "src.main"]

