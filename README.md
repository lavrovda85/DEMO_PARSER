# Data Ingestion Pipeline - Google Places API

Система автоматизированной выгрузки данных о розничных магазинах через Google Maps Platform (Places API) с сохранением в PostgreSQL и обогащением данных.

## Быстрый старт

1. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

2. Отредактируйте `.env` и укажите ваш API ключ Google Places

3. Запустите систему:
```bash
docker-compose up
```

## Параметры поиска

Настройте через переменные окружения в `.env`:
- `SEARCH_REGION` - Регион поиска
- `SEARCH_POSTAL_CODE` - Почтовый индекс
- `SEARCH_CATEGORY` - Категория магазинов

## Документация

Подробная документация находится в директории `docs/`:
- [README.md](docs/README.md) - Полное описание системы
- [architecture.md](docs/architecture.md) - Архитектура системы

## Тестирование

```bash
docker-compose run app pytest tests/ -v
```

