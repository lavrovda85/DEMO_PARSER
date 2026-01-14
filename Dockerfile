FROM python:3.11-slim

# Установка системных зависимостей для Chrome/Chromium и браузерной автоматизации
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
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Установка Google Chrome
# Используем официальный репозиторий Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Альтернатива: установка Chromium из репозитория (если Chrome не установится)
# RUN apt-get update && apt-get install -y chromium chromium-driver && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование requirements и установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Установка Playwright и браузеров (если используется Playwright)
# RUN playwright install chromium
# RUN playwright install-deps chromium

# Копирование исходного кода
COPY . .

# Создание пользователя для запуска приложения
# Chrome требует запуска от root или с правильными правами
# Для безопасности создаем пользователя, но запускаем Chrome с --no-sandbox
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Устанавливаем переменные окружения для Chrome
ENV CHROME_BIN=/usr/bin/google-chrome-stable
ENV CHROMIUM_BIN=/usr/bin/google-chrome-stable

# Переключаемся на пользователя приложения
USER appuser

CMD ["python", "-m", "src.main"]

