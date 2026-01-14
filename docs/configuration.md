# Конфигурация приложения

## Переменные окружения

Все настройки приложения управляются через переменные окружения. Файл `.env` должен быть создан на основе `env.example`.

## Категории настроек

### 1. База данных (POSTGRES_*)

Настройки подключения к PostgreSQL:

- `POSTGRES_HOST` - хост базы данных (по умолчанию: `localhost`)
- `POSTGRES_PORT` - порт базы данных (по умолчанию: `5432`)
- `POSTGRES_DB` - имя базы данных (по умолчанию: `places_db`)
- `POSTGRES_USER` - пользователь базы данных (по умолчанию: `places_user`)
- `POSTGRES_PASSWORD` - пароль базы данных (по умолчанию: `places_password`)

### 2. Google Places API (GOOGLE_PLACES_*)

- `GOOGLE_PLACES_API_KEY` - **обязательный** API ключ для доступа к Google Places API

### 3. Параметры поиска (SEARCH_*)

- `SEARCH_REGION` - регион для поиска (по умолчанию: `Byron Bay, NSW, Australia`)
- `SEARCH_POSTAL_CODE` - почтовый индекс региона (по умолчанию: `2481`)
- `SEARCH_CATEGORY` - категория магазинов для поиска (по умолчанию: `Women's Clothing Store`)

### 4. Настройки обогащения данных (ENRICHMENT_*)

- `ENRICHMENT_BROWSER_LIBRARY` - выбор библиотеки для браузерной автоматизации:
  - `playwright` - использовать Playwright (рекомендуется)
  - `pyppeteer` - использовать Pyppeteer
  - `auto` - автоматический выбор на основе доступности (по умолчанию)
  
- `ENRICHMENT_HEADLESS` - запуск браузера в headless режиме (по умолчанию: `true`)
- `ENRICHMENT_TIMEOUT` - таймаут загрузки страницы в миллисекундах (по умолчанию: `30000`)

### 5. Настройки параллелизма (PIPELINE_*)

- `PIPELINE_MAX_CONCURRENT_ENRICHMENT` - максимальное количество параллельных задач обогащения данных (по умолчанию: `5`)
- `PIPELINE_MAX_CONCURRENT_DB_WRITES` - максимальное количество параллельных записей в базу данных (по умолчанию: `10`)

## Пример конфигурации

```env
# База данных
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=places_db
POSTGRES_USER=places_user
POSTGRES_PASSWORD=places_password

# Google Places API
GOOGLE_PLACES_API_KEY=your_api_key_here

# Параметры поиска
SEARCH_REGION=Byron Bay, NSW, Australia
SEARCH_POSTAL_CODE=2481
SEARCH_CATEGORY=Women's Clothing Store

# Настройки обогащения
ENRICHMENT_BROWSER_LIBRARY=playwright
ENRICHMENT_HEADLESS=true
ENRICHMENT_TIMEOUT=30000

# Параллелизм
PIPELINE_MAX_CONCURRENT_ENRICHMENT=5
PIPELINE_MAX_CONCURRENT_DB_WRITES=10
```

## Выбор библиотеки обогащения

### Playwright (рекомендуется)

**Преимущества:**
- Активная поддержка и обновления
- Автоматическая установка браузеров
- Лучшая производительность
- Поддержка нескольких браузеров

**Установка:**
```bash
pip install playwright
playwright install chromium
```

**Использование:**
```env
ENRICHMENT_BROWSER_LIBRARY=playwright
```

### Pyppeteer

**Преимущества:**
- Легче в использовании для простых задач
- Меньше зависимостей

**Требования:**
- Установленный Google Chrome или Chromium в системе
- Для Docker: Chrome устанавливается автоматически

**Использование:**
```env
ENRICHMENT_BROWSER_LIBRARY=pyppeteer
```

### Автоматический выбор

Если установлены обе библиотеки, приоритет отдается Playwright:

```env
ENRICHMENT_BROWSER_LIBRARY=auto
```

## Docker Compose

В `docker-compose.yml` все переменные окружения передаются из `.env` файла:

```yaml
environment:
  ENRICHMENT_BROWSER_LIBRARY: ${ENRICHMENT_BROWSER_LIBRARY:-auto}
  ENRICHMENT_HEADLESS: ${ENRICHMENT_HEADLESS:-true}
  ENRICHMENT_TIMEOUT: ${ENRICHMENT_TIMEOUT:-30000}
```

Значения по умолчанию используются, если переменные не заданы в `.env`.

## Валидация конфигурации

Все настройки валидируются через Pydantic при загрузке приложения. При неверных значениях приложение выдаст ошибку с описанием проблемы.

## Безопасность

⚠️ **Важно:** Никогда не коммитьте файл `.env` в систему контроля версий. Он содержит чувствительные данные (API ключи, пароли).

Используйте `.env.example` как шаблон для создания `.env` файла.

