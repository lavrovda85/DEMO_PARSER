# Быстрый старт

## Предварительные требования

- Docker и Docker Compose установлены
- Google Places API ключ

## Шаги запуска

### 1. Создайте файл `.env`

Скопируйте `.env.example` в `.env` и заполните значения:

```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux/Mac
cp .env.example .env
```

### 2. Отредактируйте `.env`

Убедитесь, что указан ваш Google Places API ключ:

```env
GOOGLE_PLACES_API_KEY=ваш_api_ключ_здесь
```

### 3. Запустите систему

```bash
docker-compose up
```

Система автоматически:
- Поднимет PostgreSQL
- Инициализирует схему базы данных
- Запустит pipeline для извлечения данных

### 4. Просмотр результатов

Подключитесь к базе данных:

```bash
docker-compose exec postgres psql -U places_user -d places_db
```

Выполните запрос:

```sql
SELECT name, website, phone, address, description FROM stores LIMIT 10;
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

## Остановка системы

```bash
docker-compose down
```

Для удаления данных базы данных:

```bash
docker-compose down -v
```

## Устранение проблем

### Ошибка подключения к БД

Убедитесь, что PostgreSQL контейнер запущен:

```bash
docker-compose ps
docker-compose logs postgres
```

### Проблемы с Chrome в Docker

Если возникают проблемы с обогащением данных (Chrome не запускается):

1. Пересоберите образ:
```bash
docker-compose build --no-cache app
```

2. Проверьте, что Chrome установлен:
```bash
docker-compose exec app google-chrome-stable --version
```

3. Проверьте логи:
```bash
docker-compose logs app
```

Подробнее см. [docs/docker_setup.md](docs/docker_setup.md)

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

