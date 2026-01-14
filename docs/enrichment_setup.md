# Настройка модуля обогащения данных

## Проблема с pyppeteer

`pyppeteer` больше не может автоматически скачивать Chromium из-за изменений в хранилище Google. Для решения этой проблемы доступны два варианта:

## Вариант 1: Использование Playwright (рекомендуется)

Playwright активно поддерживается и автоматически управляет браузерами.

### Установка

```bash
# Установка библиотеки
pip install playwright

# Установка браузеров (требуется только один раз)
playwright install chromium
```

### Преимущества

- Активная поддержка и обновления
- Автоматическая установка браузеров
- Лучшая производительность
- Поддержка нескольких браузеров (Chromium, Firefox, WebKit)

## Вариант 2: Использование pyppeteer с системным Chrome

Если вы предпочитаете использовать pyppeteer, необходимо установить Google Chrome вручную.

### Требования

1. Установите Google Chrome на вашу систему
2. Код автоматически найдет Chrome в стандартных местах:
   - Windows: `C:\Program Files\Google\Chrome\Application\chrome.exe`
   - macOS: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
   - Linux: `/usr/bin/google-chrome`

### Использование

Код автоматически определит, какая библиотека доступна, и использует её. Если установлены обе, приоритет отдается Playwright.

## Принудительный выбор библиотеки

Вы можете принудительно выбрать библиотеку при создании `WebsiteEnricher`:

```python
# Принудительно использовать Playwright
enricher = WebsiteEnricher(use_playwright=True)

# Принудительно использовать pyppeteer
enricher = WebsiteEnricher(use_playwright=False)
```

## Проверка установки

После установки Playwright проверьте, что всё работает:

```python
from src.enrichment import WebsiteEnricher

# Создаем обогатитель
enricher = WebsiteEnricher()

# Проверяем, какая библиотека используется
print(f"Используется Playwright: {enricher.use_playwright}")
```

## Решение проблем

### Ошибка: "Не установлена ни одна из библиотек"

Установите Playwright:
```bash
pip install playwright
playwright install chromium
```

### Ошибка: "Chrome/Chromium не найден в системе"

Если используете pyppeteer, установите Google Chrome или переключитесь на Playwright.

### Ошибка при установке браузеров Playwright

Проверьте подключение к интернету и права доступа. На Windows может потребоваться запуск от имени администратора.

