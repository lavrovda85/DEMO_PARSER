# Быстрый старт

## Предварительные требования

- Docker и Docker Compose установлены
- Google Places API ключ

## Шаги запуска

### 1. Создайте файл `.env`

Скопируйте `env.example` в `.env` и заполните значения:

```bash
# Windows PowerShell
Copy-Item env.example .env

# Linux/Mac
cp env.example .env
```

### 2. Отредактируйте `.env`

Убедитесь, что указан ваш Google Places API ключ:

```env
GOOGLE_PLACES_API_KEY=ваш_api_ключ_здесь
```

Также проверьте настройки ClickHouse (используется префикс `POSTGRES_` для совместимости):
```env
POSTGRES_HOST=clickhouse
POSTGRES_PORT=9000
POSTGRES_DB=places_db
POSTGRES_USER=places_user
POSTGRES_PASSWORD=places_password
```

### 3. Запустите систему

```bash
docker-compose up
```

Система автоматически:
- Поднимет ClickHouse сервер
- Инициализирует Data Vault схему
- Запустит pipeline для извлечения данных

### 4. Просмотр результатов

Подключитесь к ClickHouse:

```bash
docker-compose exec clickhouse clickhouse-client --user places_user --password places_password --database places_db
```

Выполните запрос:

```sql
SELECT name, website, phone, address FROM vw_store_data LIMIT 10;
```

Или используйте материализованное представление для поиска:

```sql
SELECT * FROM mv_store_search WHERE place_id = 'ChIJ...' LIMIT 1;
```

## Изменение параметров поиска

Отредактируйте переменные в `.env`:

```env
SEARCH_REGION=Byron Bay, NSW, Australia
SEARCH_POSTAL_CODE=2481
SEARCH_CATEGORY=Women's Clothing Store
```

Или передайте через командную строку:

```bash
docker-compose run -e SEARCH_CATEGORY="Men's Clothing Store" app
```

## Jupyter аналитика

Для запуска Jupyter Lab с аналитическими ноутбуками:

```bash
docker-compose --profile jupyter up jupyter
```

Откройте браузер по адресу `http://localhost:8888` с токеном из `.env` (по умолчанию `places_api_token`).

## Остановка системы

```bash
docker-compose down
```

Для удаления данных базы данных:

```bash
docker-compose down -v
```

## Устранение проблем

### Ошибка подключения к ClickHouse

Убедитесь, что ClickHouse контейнер запущен:

```bash
docker-compose ps
docker-compose logs clickhouse
```

Проверьте healthcheck:
```bash
docker-compose exec clickhouse clickhouse-client --user places_user --password places_password --database places_db --query 'SELECT 1'
```

### Проблемы с браузером в Docker

Если возникают проблемы с обогащением данных (браузер не запускается):

1. Пересоберите образ:
```bash
docker-compose build --no-cache app
```

2. Проверьте логи:
```bash
docker-compose logs app
```

Подробнее см. [docs/docker_setup.md](docs/docker_setup.md) и [docs/enrichment_setup.md](docs/enrichment_setup.md)

### Ошибка Google Places API

Проверьте:
- Корректность API ключа в `.env`
- Наличие квот в Google Cloud Console
- Включен ли Places API в проекте

### Ошибки обогащения данных

Обогащение может занимать время. Проверьте логи:

```bash
docker-compose logs app
```

### Проблемы с Data Vault схемой

Если схема не инициализировалась автоматически:

```bash
docker-compose exec clickhouse clickhouse-client --user places_user --password places_password --database places_db < sql/init-clickhouse.sql
```
