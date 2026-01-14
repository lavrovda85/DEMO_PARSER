# Настройка Docker для работы с Chrome

## Обзор

Docker-образ настроен для работы с Google Chrome, который используется модулем обогащения данных (`enrichment.py`) для извлечения информации с веб-сайтов.

## Что установлено в Docker

### Google Chrome

В Dockerfile установлен Google Chrome Stable из официального репозитория Google:

- **Путь**: `/usr/bin/google-chrome-stable`
- **Версия**: Последняя стабильная версия из репозитория Google
- **Автоматическое обновление**: При пересборке образа

### Системные зависимости

Установлены все необходимые библиотеки для работы Chrome в headless режиме:

- Библиотеки для рендеринга (libgbm1, libdrm2)
- Библиотеки для работы с окнами (libx11, libxcomposite, libxdamage)
- Шрифты (fonts-liberation)
- И другие зависимости

## Конфигурация

### Dockerfile

```dockerfile
# Установка Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*
```

### docker-compose.yml

Настроены переменные окружения и параметры для работы Chrome:

```yaml
environment:
  CHROME_BIN: /usr/bin/google-chrome-stable
  CHROMIUM_BIN: /usr/bin/google-chrome-stable
shm_size: '2gb'  # Увеличенный shared memory для Chrome
```

## Автоматическое определение Chrome

Модуль `enrichment.py` автоматически находит Chrome в следующих местах (в порядке приоритета):

1. Переменные окружения `CHROME_BIN` или `CHROMIUM_BIN`
2. `/usr/bin/google-chrome-stable` (Google Chrome в Debian/Ubuntu)
3. `/usr/bin/google-chrome` (альтернативный путь)
4. `/usr/bin/chromium-browser` (Chromium)
5. `/usr/bin/chromium` (Chromium альтернативный путь)

## Параметры запуска Chrome в Docker

Для стабильной работы Chrome в Docker используются следующие параметры:

- `--no-sandbox` - Отключает sandbox (требуется в Docker)
- `--disable-setuid-sandbox` - Отключает setuid sandbox
- `--disable-dev-shm-usage` - Использует /tmp вместо /dev/shm
- `--disable-gpu` - Отключает GPU в headless режиме
- `--single-process` - Запуск в одном процессе (опционально)

## Пересборка образа

После изменений в Dockerfile пересоберите образ:

```bash
docker-compose build --no-cache app
```

Или пересоберите все сервисы:

```bash
docker-compose build --no-cache
```

## Проверка установки Chrome

Проверьте, что Chrome установлен в контейнере:

```bash
# Запустите контейнер
docker-compose up -d

# Проверьте версию Chrome
docker-compose exec app google-chrome-stable --version

# Проверьте путь к Chrome
docker-compose exec app which google-chrome-stable
```

## Альтернатива: Использование Playwright

Если вы предпочитаете использовать Playwright вместо pyppeteer:

1. Раскомментируйте строки в Dockerfile:
```dockerfile
RUN playwright install chromium
RUN playwright install-deps chromium
```

2. Установите Playwright в requirements.txt (уже добавлен)

3. Код автоматически переключится на Playwright при его наличии

## Решение проблем

### Ошибка: "Chrome не найден"

Убедитесь, что образ пересобран:

```bash
docker-compose build --no-cache app
docker-compose up -d
```

### Ошибка: "Failed to move to new namespace"

Увеличьте shared memory в docker-compose.yml:

```yaml
shm_size: '2gb'
```

### Ошибка: "No usable sandbox"

Параметры `--no-sandbox` и `--disable-setuid-sandbox` уже добавлены в код. Если ошибка сохраняется, проверьте права доступа.

### Chrome не запускается

Проверьте логи контейнера:

```bash
docker-compose logs app
```

Убедитесь, что все зависимости установлены и Chrome доступен:

```bash
docker-compose exec app ls -la /usr/bin/google-chrome-stable
```

## Оптимизация размера образа

Текущий образ включает все зависимости для Chrome. Для уменьшения размера можно:

1. Использовать multi-stage build
2. Удалить ненужные пакеты после установки Chrome
3. Использовать более легкий базовый образ (но может потребоваться больше зависимостей)

Текущая конфигурация оптимизирована для стабильности и простоты использования.

