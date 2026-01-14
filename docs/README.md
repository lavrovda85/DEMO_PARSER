# Data Ingestion Pipeline - Google Places API

## Описание

Система автоматизированной выгрузки данных о розничных магазинах через Google Maps Platform (Places API) с сохранением в реляционную базу данных PostgreSQL и обогащением данных через извлечение информации с веб-сайтов магазинов.

## Возможности

- Поиск магазинов по категории и региону через Google Places API
- Извлечение детальной информации о местах (название, адрес, телефон, веб-сайт)
- Обогащение данных через извлечение описания главной страницы веб-сайта
- Сохранение данных в нормализованном виде в PostgreSQL
- Гибкая настройка параметров поиска через переменные окружения
- Полная контейнеризация через Docker Compose

## Архитектура

### Компоненты системы

1. **Google Places API Client** (`src/places_api.py`)
   - Поиск мест по текстовому запросу
   - Получение детальной информации о местах
   - Нормализация данных для сохранения

2. **Website Enricher** (`src/enrichment.py`)
   - Извлечение описания главной страницы веб-сайта
   - Использование Stealth Puppeteer для обхода защиты от ботов

3. **Database Manager** (`src/database.py`)
   - Управление подключениями к PostgreSQL
   - Инициализация схемы базы данных
   - Управление сессиями

4. **Pipeline Orchestrator** (`src/main.py`)
   - Координация процесса извлечения и сохранения данных
   - Обработка ошибок и логирование

### Схема базы данных

Таблица `stores`:
- `id` (String, PK) - Уникальный идентификатор записи
- `name` (String) - Название магазина
- `website` (String) - URL веб-сайта
- `phone` (String) - Номер телефона
- `address` (Text) - Полный адрес
- `place_id` (String, UNIQUE) - Уникальный идентификатор Google Places
- `description` (Text) - Описание магазина (из обогащения)
- `created_at` (DateTime) - Дата создания записи
- `updated_at` (DateTime) - Дата последнего обновления

## Установка и запуск

### Требования

- Docker и Docker Compose
- Google Places API ключ

### Быстрый старт

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd TEST_API
```

2. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
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
- Поднимет PostgreSQL
- Инициализирует схему базы данных
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

Подключение к PostgreSQL:

```bash
docker-compose exec postgres psql -U places_user -d places_db
```

Запросы для просмотра данных:

```sql
-- Все магазины
SELECT name, website, phone, address FROM stores;

-- Магазины с описанием
SELECT name, description FROM stores WHERE description IS NOT NULL;

-- Статистика
SELECT COUNT(*) as total_stores, 
       COUNT(description) as enriched_stores 
FROM stores;
```

## Разработка

### Структура проекта

```
TEST_API/
├── docker-compose.yml      # Конфигурация Docker Compose
├── Dockerfile              # Образ для Python приложения
├── requirements.txt        # Python зависимости
├── .env.example           # Пример конфигурации
├── src/                   # Исходный код
│   ├── __init__.py
│   ├── config.py          # Конфигурация
│   ├── database.py        # Работа с БД
│   ├── models.py          # Модели данных
│   ├── places_api.py      # Google Places API клиент
│   ├── enrichment.py      # Обогащение данных
│   └── main.py            # Главный модуль
├── tests/                 # Тесты
│   ├── __init__.py
│   ├── test_places_api.py
│   ├── test_enrichment.py
│   └── test_models.py
└── docs/                  # Документация
    └── README.md
```

### Запуск тестов

```bash
docker-compose run app pytest tests/ -v
```

### Логирование

Логи выводятся в консоль с уровнем INFO. Для изменения уровня логирования отредактируйте `src/main.py`.

## Ограничения и особенности

1. **Google Places API**
   - Text Search API имеет ограничение на количество страниц результатов (обычно 3)
   - Требуется задержка между запросами для токенов следующей страницы

2. **Обогащение данных**
   - Извлечение описания может занимать значительное время
   - Некоторые сайты могут блокировать автоматизированный доступ
   - Таймаут загрузки страницы: 30 секунд

3. **База данных**
   - Дубликаты определяются по `place_id`
   - При повторном запуске существующие записи обновляются

## Устранение неполадок

### Ошибка подключения к базе данных

Убедитесь, что PostgreSQL контейнер запущен и здоров:
```bash
docker-compose ps
docker-compose logs postgres
```

### Ошибка Google Places API

Проверьте:
- Корректность API ключа
- Наличие квот в Google Cloud Console
- Включен ли Places API в проекте

### Ошибки обогащения данных

- Проверьте доступность веб-сайтов
- Увеличьте таймаут в `src/enrichment.py` при необходимости
- Проверьте логи на наличие блокировок

## Лицензия

Проект создан для внутреннего использования.

