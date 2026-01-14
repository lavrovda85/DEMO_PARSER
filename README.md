# Data Ingestion Pipeline - Google Places API

Система автоматизированной выгрузки данных о розничных магазинах через Google Maps Platform (Places API) с сохранением в ClickHouse Data Vault и обогащением данных через динамические JavaScript шаблоны.

## Основные возможности

- 🔍 Поиск магазинов по категории и региону через Google Places API
- 📊 Хранение данных в ClickHouse с использованием Data Vault архитектуры
- 🎯 Динамические JavaScript шаблоны для извлечения данных с веб-сайтов
- 🚀 Асинхронная обработка с параллельным обогащением данных
- 📈 Jupyter ноутбуки для аналитики и визуализации
- 🐳 Полная контейнеризация через Docker Compose

## Быстрый старт

1. Создайте файл `.env` на основе `env.example`:
```bash
cp env.example .env
```

2. Отредактируйте `.env` и укажите ваш API ключ Google Places:
```env
GOOGLE_PLACES_API_KEY=your_api_key_here
```

3. Запустите систему:
```bash
docker-compose up
```

Система автоматически:
- Поднимет ClickHouse сервер
- Инициализирует Data Vault схему
- Запустит pipeline для извлечения данных

## Параметры поиска

Настройте через переменные окружения в `.env`:
- `SEARCH_REGION` - Регион поиска (например, "Byron Bay, NSW, Australia")
- `SEARCH_POSTAL_CODE` - Почтовый индекс
- `SEARCH_CATEGORY` - Категория магазинов (например, "Women's Clothing Store")

## Просмотр данных

Подключитесь к ClickHouse:
```bash
docker-compose exec clickhouse clickhouse-client --user places_user --password places_password --database places_db
```

Выполните запрос:
```sql
SELECT name, website, phone, address FROM vw_store_data LIMIT 10;
```

## Jupyter аналитика

Запустите Jupyter Lab для интерактивной аналитики:
```bash
docker-compose --profile jupyter up jupyter
```

Откройте браузер по адресу `http://localhost:8888` с токеном из `.env` (по умолчанию `places_api_token`).

## Документация

Подробная документация находится в директории `docs/`:
- [README.md](docs/README.md) - Полное описание системы
- [architecture.md](docs/architecture.md) - Архитектура системы
- [configuration.md](docs/configuration.md) - Настройка конфигурации
- [docker_setup.md](docs/docker_setup.md) - Настройка Docker
- [enrichment_setup.md](docs/enrichment_setup.md) - Настройка обогащения данных

## Тестирование

```bash
docker-compose run app pytest tests/ -v
```

## Архитектура

Проект использует:
- **ClickHouse** для аналитического хранения данных
- **Data Vault** архитектуру для нормализованного хранения
- **Динамические JavaScript шаблоны** для извлечения данных
- **Асинхронный ETL pipeline** для обработки данных
