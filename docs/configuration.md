# Конфигурация приложения

## Переменные окружения

Все настройки приложения управляются через переменные окружения. Файл `.env` должен быть создан на основе `env.example`.

## Категории настроек

### 1. База данных (POSTGRES_*)

**Примечание:** Для совместимости используется префикс `POSTGRES_`, но фактически используется ClickHouse.

Настройки подключения к ClickHouse:

- `POSTGRES_HOST` - хост базы данных (по умолчанию: `clickhouse` в Docker, `localhost` локально)
- `POSTGRES_PORT` - порт базы данных (по умолчанию: `9000` для ClickHouse native protocol)
- `POSTGRES_DB` - имя базы данных (по умолчанию: `places_db`)
- `POSTGRES_USER` - пользователь базы данных (по умолчанию: `places_user`)
- `POSTGRES_PASSWORD` - пароль базы данных (по умолчанию: `places_password`)
- `POSTGRES_MIN_SIZE` - минимальный размер пула соединений (по умолчанию: `5`)
- `POSTGRES_MAX_SIZE` - максимальный размер пула соединений (по умолчанию: `20`)
- `POSTGRES_COMMAND_TIMEOUT` - таймаут команд в секундах (по умолчанию: `60.0`)
- `POSTGRES_MAX_INACTIVE_CONNECTION_LIFETIME` - максимальное время жизни неактивного соединения в секундах (по умолчанию: `300.0`)

### 2. Google Places API (GOOGLE_PLACES_*)

- `GOOGLE_PLACES_API_KEY` - **обязательный** API ключ для доступа к Google Places API
- `GOOGLE_PLACES_RADIUS` - радиус поиска в метрах (по умолчанию: `5000`)
- `GOOGLE_PLACES_MAX_RESULTS` - максимальное количество результатов (по умолчанию: `60`)
- `GOOGLE_PLACES_PAGE_SIZE` - размер страницы (максимум 20 по API, по умолчанию: `20`)
- `GOOGLE_PLACES_REQUEST_DELAY` - задержка между запросами в секундах (по умолчанию: `0.1`)
- `GOOGLE_PLACES_INITIAL_DELAY` - начальная задержка перед первым запросом в секундах (по умолчанию: `0.5`)

### 3. Параметры поиска (SEARCH_*)

- `SEARCH_REGION` - регион для поиска (по умолчанию: `Byron Bay, NSW, Australia`)
- `SEARCH_POSTAL_CODE` - почтовый индекс региона (по умолчанию: `2481`)
- `SEARCH_CATEGORY` - категория магазинов для поиска (по умолчанию: `Women's Clothing Store`)

### 4. Настройки браузера (BROWSER_*)

- `BROWSER_TIMEOUT` - таймаут операций в миллисекундах (по умолчанию: `15000`)
- `BROWSER_HEADLESS` - запуск браузера в headless режиме (по умолчанию: `true`)

### 5. Настройки параллелизма (PIPELINE_*)

- `PIPELINE_STREAMING` - использовать streaming режим (по умолчанию: `false`)
- `PIPELINE_ENRICH_DATA` - обогащать ли данные веб-скрапингом (по умолчанию: `true`)
- `PIPELINE_MAX_CONCURRENT_ENRICHMENT` - максимальное количество параллельных задач обогащения данных (по умолчанию: `3`)
- `PIPELINE_MAX_CONCURRENT_DB_WRITES` - максимальное количество параллельных записей в базу данных (по умолчанию: `10`)
- `PIPELINE_LOGLEVEL` - уровень логирования (по умолчанию: `INFO`, возможные значения: `DEBUG`, `INFO`, `WARNING`, `ERROR`)

### 6. Jupyter Configuration (JUPYTER_*)

- `JUPYTER_PORT` - порт для Jupyter Lab (по умолчанию: `8888`)
- `JUPYTER_TOKEN` - токен для доступа к Jupyter Lab (по умолчанию: `places_api_token`)
- `JUPYTER_PASSWORD` - пароль для доступа (опционально, если не указан, используется только токен)

## Пример конфигурации

```env
# ClickHouse Configuration (использует POSTGRES_ префикс для совместимости)
POSTGRES_HOST=clickhouse
POSTGRES_PORT=9000
POSTGRES_DB=places_db
POSTGRES_USER=places_user
POSTGRES_PASSWORD=places_password
POSTGRES_MIN_SIZE=5
POSTGRES_MAX_SIZE=20
POSTGRES_COMMAND_TIMEOUT=60.0
POSTGRES_MAX_INACTIVE_CONNECTION_LIFETIME=300.0

# Google Places API
GOOGLE_PLACES_API_KEY=your_api_key_here
GOOGLE_PLACES_RADIUS=5000
GOOGLE_PLACES_MAX_RESULTS=60
GOOGLE_PLACES_PAGE_SIZE=20
GOOGLE_PLACES_REQUEST_DELAY=0.1
GOOGLE_PLACES_INITIAL_DELAY=0.5

# Параметры поиска
SEARCH_REGION=Byron Bay, NSW, Australia
SEARCH_POSTAL_CODE=2481
SEARCH_CATEGORY=Women's Clothing Store

# Настройки браузера
BROWSER_TIMEOUT=15000
BROWSER_HEADLESS=true

# Параллелизм
PIPELINE_STREAMING=false
PIPELINE_ENRICH_DATA=true
PIPELINE_MAX_CONCURRENT_ENRICHMENT=3
PIPELINE_MAX_CONCURRENT_DB_WRITES=10
PIPELINE_LOGLEVEL=INFO

# Jupyter Configuration
JUPYTER_PORT=8888
JUPYTER_TOKEN=places_api_token
JUPYTER_PASSWORD=
```

## Docker Compose

В `docker-compose.yml` все переменные окружения передаются из `.env` файла:

```yaml
env_file:
  - .env
```

Значения по умолчанию используются, если переменные не заданы в `.env`.

## Валидация конфигурации

Все настройки валидируются через Pydantic при загрузке приложения. При неверных значениях приложение выдаст ошибку с описанием проблемы.

Для проверки конфигурации можно запустить:

```bash
python -m src.config
```

## Безопасность

⚠️ **Важно:** Никогда не коммитьте файл `.env` в систему контроля версий. Он содержит чувствительные данные (API ключи, пароли).

Используйте `env.example` как шаблон для создания `.env` файла.

## Рекомендации по настройке

### Производительность

- Увеличьте `PIPELINE_MAX_CONCURRENT_ENRICHMENT` для более быстрого обогащения (но учтите нагрузку на браузер)
- Уменьшите `GOOGLE_PLACES_REQUEST_DELAY` для более быстрого получения данных (но соблюдайте rate limits API)
- Настройте `POSTGRES_MAX_SIZE` в зависимости от нагрузки на ClickHouse

### Отладка

- Установите `PIPELINE_LOGLEVEL=DEBUG` для детального логирования
- Установите `BROWSER_HEADLESS=false` для визуального наблюдения за браузером (только локально)
- Увеличьте `BROWSER_TIMEOUT` для медленных сайтов

### Тестирование

- Используйте меньшие значения `GOOGLE_PLACES_MAX_RESULTS` для быстрого тестирования
- Установите `PIPELINE_ENRICH_DATA=false` для пропуска обогащения при тестировании API
- Используйте тестовую базу данных с другим `POSTGRES_DB`
