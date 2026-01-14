# Настройка Docker для работы с браузером и ClickHouse

## Обзор

Docker-образ настроен для работы с:
- Google Chrome/Chromium для модуля обогащения данных (`extraction/browser.py`)
- ClickHouse для хранения данных в Data Vault архитектуре

## Что установлено в Docker

### Google Chrome / Chromium

В Dockerfile установлены системные зависимости для работы с браузером через pyppeteer:

- **Node.js** версия 18.x для поддержки pyppeteer
- **Системные библиотеки** для работы Chrome в headless режиме:
  - Библиотеки для рендеринга (libgbm1, libdrm2)
  - Библиотеки для работы с окнами (libx11, libxcomposite, libxdamage)
  - Шрифты (fonts-liberation)
  - И другие зависимости

**Примечание:** pyppeteer автоматически скачивает Chromium при первом запуске.

### ClickHouse

ClickHouse запускается в отдельном контейнере из официального образа:
- **Образ:** `clickhouse/clickhouse-server:23.8-alpine`
- **Порт:** 9000 (native protocol) и 8123 (HTTP)
- **Автоматическая инициализация:** схема Data Vault создается из `sql/init-clickhouse.sql`

## Конфигурация

### Dockerfile

```dockerfile
# Установка Node.js для pyppeteer
RUN wget -q -O - https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Установка системных зависимостей для Chrome
RUN apt-get update && apt-get install -y \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    # ... другие зависимости
    && rm -rf /var/lib/apt/lists/*
```

### docker-compose.yml

Настроены сервисы:

```yaml
services:
  clickhouse:
    image: clickhouse/clickhouse-server:23.8-alpine
    environment:
      CLICKHOUSE_DB: places_db
      CLICKHOUSE_USER: places_user
      CLICKHOUSE_PASSWORD: places_password
    ports:
      - "9000:8123"
    volumes:
      - clickhouse_data:/var/lib/clickhouse
      - ./sql/init-clickhouse.sql:/docker-entrypoint-initdb.d/init-schema.sql
    healthcheck:
      test: ["CMD-SHELL", "clickhouse-client --user places_user --password places_password --database places_db --query 'SELECT 1'"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  app:
    build:
      context: .
      dockerfile: Dockerfile
    depends_on:
      - clickhouse
    env_file:
      - .env
    environment:
      BROWSER_HEADLESS: true
```

## Автоматическое определение браузера

Модуль `extraction/browser.py` использует pyppeteer, который автоматически:
1. Скачивает Chromium при первом запуске
2. Сохраняет его в `~/.local/share/pyppeteer/`
3. Использует его для всех последующих запусков

## Параметры запуска браузера в Docker

Для стабильной работы браузера в Docker используются следующие параметры (настроены в коде):

- `--no-sandbox` - Отключает sandbox (требуется в Docker)
- `--disable-setuid-sandbox` - Отключает setuid sandbox
- `--disable-dev-shm-usage` - Использует /tmp вместо /dev/shm
- `--disable-gpu` - Отключает GPU в headless режиме

## Пересборка образа

После изменений в Dockerfile пересоберите образ:

```bash
docker-compose build --no-cache app
```

Или пересоберите все сервисы:

```bash
docker-compose build --no-cache
```

## Проверка установки

### Проверка ClickHouse

Проверьте, что ClickHouse запущен и доступен:

```bash
# Проверьте статус контейнера
docker-compose ps clickhouse

# Проверьте логи
docker-compose logs clickhouse

# Проверьте подключение
docker-compose exec clickhouse clickhouse-client --user places_user --password places_password --database places_db --query 'SELECT 1'
```

### Проверка браузера

Проверьте, что браузер работает в контейнере:

```bash
# Запустите контейнер
docker-compose up -d app

# Проверьте логи на наличие ошибок браузера
docker-compose logs app | grep -i browser

# Проверьте, что pyppeteer может запустить браузер
docker-compose exec app python -c "from pyppeteer import launch; import asyncio; asyncio.run(launch(headless=True, args=['--no-sandbox']))"
```

## Инициализация ClickHouse схемы

Схема Data Vault автоматически создается при первом запуске ClickHouse из файла `sql/init-clickhouse.sql`.

Если схема не создалась автоматически, можно инициализировать вручную:

```bash
docker-compose exec clickhouse clickhouse-client \
  --user places_user \
  --password places_password \
  --database places_db \
  < sql/init-clickhouse.sql
```

## Решение проблем

### Ошибка: "ClickHouse недоступен"

Убедитесь, что ClickHouse контейнер запущен и здоров:

```bash
docker-compose ps clickhouse
docker-compose logs clickhouse
```

Проверьте healthcheck:
```bash
docker-compose exec clickhouse clickhouse-client \
  --user places_user \
  --password places_password \
  --database places_db \
  --query 'SELECT 1'
```

Если healthcheck не проходит, подождите несколько секунд (start_period: 30s) и попробуйте снова.

### Ошибка: "Failed to move to new namespace"

Эта ошибка связана с ограничениями Docker на shared memory. Убедитесь, что в `docker-compose.yml` установлен достаточный размер:

```yaml
services:
  app:
    shm_size: '2gb'
```

### Ошибка: "No usable sandbox"

Параметры `--no-sandbox` и `--disable-setuid-sandbox` уже добавлены в код. Если ошибка сохраняется, проверьте права доступа контейнера.

### Браузер не запускается

Проверьте логи контейнера:

```bash
docker-compose logs app
```

Убедитесь, что:
1. Node.js установлен: `docker-compose exec app node --version`
2. pyppeteer может скачать Chromium (требуется интернет-соединение)
3. Все системные зависимости установлены

### Ошибка: "Chromium не скачивается"

pyppeteer пытается скачать Chromium при первом запуске. Если это не удается:

1. Проверьте интернет-соединение контейнера
2. Проверьте логи на наличие ошибок сети
3. Попробуйте пересобрать образ с очисткой кэша

### Проблемы с производительностью браузера

Если обогащение данных работает медленно:

1. Увеличьте `PIPELINE_MAX_CONCURRENT_ENRICHMENT` для параллельной обработки
2. Уменьшите `BROWSER_TIMEOUT` для быстрого пропуска недоступных сайтов
3. Проверьте ресурсы Docker (CPU, память)

### Проблемы с ClickHouse производительностью

Если сохранение данных работает медленно:

1. Увеличьте `PIPELINE_MAX_CONCURRENT_DB_WRITES` (но учтите ограничения ClickHouse драйвера)
2. Проверьте ресурсы ClickHouse контейнера
3. Оптимизируйте запросы в `src/database/clickhouse/client.py`

## Оптимизация размера образа

Текущий образ включает все зависимости для браузера. Для уменьшения размера можно:

1. Использовать multi-stage build
2. Удалить ненужные пакеты после установки
3. Использовать более легкий базовый образ (но может потребоваться больше зависимостей)

Текущая конфигурация оптимизирована для стабильности и простоты использования.

## Мониторинг

### Логи приложения

```bash
# Все логи
docker-compose logs app

# Логи в реальном времени
docker-compose logs -f app

# Логи только ошибок
docker-compose logs app | grep -i error
```

### Логи ClickHouse

```bash
# Все логи
docker-compose logs clickhouse

# Логи в реальном времени
docker-compose logs -f clickhouse
```

### Использование ресурсов

```bash
# Статистика контейнеров
docker stats

# Статистика конкретного контейнера
docker stats places_api_app
docker stats places_api_clickhouse
```