# Data Ingestion Pipeline - Google Places API

## Описание

Система автоматизированной выгрузки данных о розничных магазинах через Google Maps Platform (Places API) с сохранением в ClickHouse Data Vault и обогащением данных через динамические JavaScript шаблоны для извлечения информации с веб-сайтов магазинов.

## Возможности

- Поиск магазинов по категории и региону через Google Places API
- Извлечение детальной информации о местах (название, адрес, телефон, веб-сайт, координаты, рейтинг)
- Обогащение данных через динамические JavaScript шаблоны для извлечения дополнительной информации с веб-сайтов
- Сохранение данных в нормализованном виде в ClickHouse с использованием Data Vault архитектуры
- Гибкая настройка параметров поиска через переменные окружения
- Полная контейнеризация через Docker Compose
- Jupyter ноутбуки для аналитики и визуализации данных

## Архитектура

### Компоненты системы

1. **Google Places API Client** (`src/api/`)
   - Асинхронный клиент для работы с Google Places API
   - Поиск мест по текстовому запросу
   - Получение детальной информации о местах
   - Нормализация данных для сохранения

2. **Data Extraction** (`src/extraction/`)
   - Динамические JavaScript шаблоны для извлечения данных
   - Автоматическая загрузка шаблонов из папки `templates/`
   - Поддержка pyppeteer для браузерной автоматизации
   - Извлечение описания, контактов, часов работы, адресов, социальных сетей

3. **ClickHouse Data Vault** (`src/database/clickhouse/`)
   - Клиент для работы с ClickHouse
   - Data Vault архитектура (Hub-Satellite-Link)
   - Автоматическое расширение схемы для новых полей
   - Историчность данных с поддержкой версий

4. **Pipeline Orchestrator** (`src/pipeline/`)
   - Координация процесса извлечения и сохранения данных
   - Асинхронная обработка с параллельным обогащением
   - Обработка ошибок и логирование

### Схема базы данных (Data Vault)

#### Hub таблицы
- `hub_stores` - уникальные магазины (по place_id)
- `hub_fields` - метаданные полей данных
- `hub_attributes` - метаданные атрибутов

#### Satellite таблицы
- `sat_store_attributes` - атрибуты магазинов (name, address, phone, website, координаты, рейтинг)
- `sat_field_values` - значения динамических полей
- `sat_store_raw` - сырые данные из API

#### Link таблицы
- `link_store_fields` - связи магазин-поле

#### Представления
- `vw_store_data` - удобное чтение данных (последняя версия для каждого магазина)
- `mv_store_search` - материализованное представление для быстрого поиска по place_id
- `mv_field_stats` - статистика по полям

## Установка и запуск

### Требования

- Docker и Docker Compose
- Google Places API ключ

### Быстрый старт

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd DEMO_PARSER
```

2. Создайте файл `.env` на основе `env.example`:
```bash
cp env.example .env
```

3. Отредактируйте `.env` и укажите ваш API ключ Google Places:
```env
GOOGLE_PLACES_API_KEY=your_api_key_here
```

4. Запустите систему одной командой:
```bash
docker-compose up
```

Система автоматически:
- Поднимет ClickHouse сервер
- Инициализирует Data Vault схему
- Запустит pipeline для извлечения данных

### Параметры поиска

Параметры поиска можно изменить через переменные окружения в `.env`:

```env
SEARCH_REGION=Byron Bay, NSW, Australia
SEARCH_POSTAL_CODE=2481
SEARCH_CATEGORY=Women's Clothing Store
```

Или через переменные окружения Docker Compose:

```bash
docker-compose run -e SEARCH_CATEGORY="Men's Clothing Store" app
```

## Использование

### Запуск pipeline

По умолчанию pipeline запускается автоматически при старте контейнера. Для повторного запуска:

```bash
docker-compose run app python -m src.main
```

### Просмотр данных

Подключение к ClickHouse:

```bash
docker-compose exec clickhouse clickhouse-client --user places_user --password places_password --database places_db
```

Запросы для просмотра данных:

```sql
-- Все магазины (последняя версия)
SELECT name, website, phone, address FROM vw_store_data LIMIT 10;

-- Магазины с обогащенными данными
SELECT name, extracted_fields FROM vw_store_data 
WHERE extracted_fields != '' LIMIT 10;

-- Статистика
SELECT 
    COUNT(*) as total_stores,
    COUNTIf(extracted_fields != '') as enriched_stores
FROM vw_store_data;

-- Поиск по place_id
SELECT * FROM mv_store_search WHERE place_id = 'ChIJ...' LIMIT 1;
```

### Jupyter аналитика

Запустите Jupyter Lab:

```bash
docker-compose --profile jupyter up jupyter
```

Откройте браузер по адресу `http://localhost:8888` с токеном из `.env`.

## Разработка

### Структура проекта

```
DEMO_PARSER/
├── docker-compose.yml      # Конфигурация Docker Compose
├── Dockerfile              # Образ для Python приложения
├── requirements.txt        # Python зависимости
├── env.example            # Пример конфигурации
├── src/                   # Исходный код
│   ├── __init__.py
│   ├── config.py          # Конфигурация
│   ├── google_places_parser.py  # Главный парсер
│   ├── main.py            # Точка входа
│   ├── api/               # Google Places API клиент
│   │   ├── client.py
│   │   ├── normalizer.py
│   │   ├── factory.py
│   │   └── search.py
│   ├── database/          # Работа с БД
│   │   ├── manager.py
│   │   ├── queries.py
│   │   └── clickhouse/    # ClickHouse Data Vault
│   │       ├── client.py
│   │       └── schema.py
│   ├── extraction/        # Извлечение данных
│   │   ├── browser.py
│   │   ├── extractor.py
│   │   ├── templates.py
│   │   └── templates/     # JavaScript шаблоны
│   │       ├── 01_description.js
│   │       ├── 02_contact.js
│   │       ├── 03_hours.js
│   │       ├── 04_address.js
│   │       └── 05_social.js
│   ├── pipeline/          # ETL компоненты
│   │   ├── base.py
│   │   ├── orchestrator.py
│   │   ├── fetcher.py
│   │   └── enricher.py
│   └── storage/           # Сохранение данных
│       ├── saver.py
│       └── saver_clickhouse.py
├── tests/                 # Тесты
│   ├── test_clickhouse.py
│   ├── test_enrichment.py
│   ├── test_google_places_parser.py
│   └── test_pipeline.py
├── notebooks/             # Jupyter ноутбуки
│   ├── store_analytics_dashboard.ipynb
│   └── google_places_parser_demo.ipynb
└── docs/                  # Документация
    ├── README.md
    ├── architecture.md
    ├── configuration.md
    └── ...
```

### Запуск тестов

```bash
docker-compose run app pytest tests/ -v
```

### Логирование

Логи выводятся в консоль с уровнем, заданным в `PIPELINE_LOGLEVEL` (по умолчанию INFO). Для изменения уровня логирования отредактируйте `.env`:

```env
PIPELINE_LOGLEVEL=DEBUG
```

## Динамические шаблоны извлечения

Система автоматически загружает JavaScript шаблоны из папки `src/extraction/templates/` в порядке нумерации файлов (01_, 02_, etc.).

### Добавление нового шаблона

1. Создайте файл `NN_fieldname.js` в папке `src/extraction/templates/`
2. Напишите JavaScript код для извлечения данных
3. Шаблон будет автоматически загружен при следующем запуске

Пример шаблона:
```javascript
() => {
    const description = document.querySelector('meta[name="description"]');
    return description ? description.content.trim() : null;
}
```

## Ограничения и особенности

1. **Google Places API**
   - Text Search API имеет ограничение на количество страниц результатов (обычно 3)
   - Требуется задержка между запросами для токенов следующей страницы
   - Настройка через `GOOGLE_PLACES_REQUEST_DELAY` и `GOOGLE_PLACES_INITIAL_DELAY`

2. **Обогащение данных**
   - Извлечение данных может занимать значительное время
   - Некоторые сайты могут блокировать автоматизированный доступ
   - Таймаут загрузки страницы настраивается через `BROWSER_TIMEOUT`
   - Параллелизм настраивается через `PIPELINE_MAX_CONCURRENT_ENRICHMENT`

3. **База данных**
   - Дубликаты определяются по `place_id` (в hub_stores)
   - При повторном запуске создаются новые версии в satellite таблицах
   - Data Vault сохраняет историю изменений

## Устранение неполадок

### Ошибка подключения к базе данных

Убедитесь, что ClickHouse контейнер запущен и здоров:

```bash
docker-compose ps
docker-compose logs clickhouse
```

Проверьте healthcheck:
```bash
docker-compose exec clickhouse clickhouse-client --user places_user --password places_password --database places_db --query 'SELECT 1'
```

### Ошибка Google Places API

Проверьте:
- Корректность API ключа в `.env`
- Наличие квот в Google Cloud Console
- Включен ли Places API в проекте

### Ошибки обогащения данных

- Проверьте доступность веб-сайтов
- Увеличьте таймаут в `.env` (`BROWSER_TIMEOUT`)
- Проверьте логи на наличие блокировок
- Убедитесь, что браузер запускается (см. [docker_setup.md](docker_setup.md))

### Проблемы с Data Vault схемой

Если схема не инициализировалась автоматически:

```bash
docker-compose exec clickhouse clickhouse-client --user places_user --password places_password --database places_db < docker/init-clickhouse.sql
```

## Лицензия

Проект создан для внутреннего использования.
