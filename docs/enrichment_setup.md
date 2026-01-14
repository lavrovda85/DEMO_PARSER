# Настройка модуля обогащения данных

## Обзор

Модуль обогащения данных использует pyppeteer для извлечения информации с веб-сайтов магазинов через динамические JavaScript шаблоны.

## Текущая реализация

### pyppeteer

Проект использует **pyppeteer** для браузерной автоматизации:

- **Автоматическая установка:** pyppeteer автоматически скачивает Chromium при первом запуске
- **Stealth режим:** используется `pyppeteer-stealth` для обхода защиты от ботов
- **Асинхронная обработка:** поддержка async/await для неблокирующих операций

### Динамические JavaScript шаблоны

Система автоматически загружает JavaScript шаблоны из папки `src/extraction/templates/`:

- **Порядок выполнения:** по нумерации файлов (01_, 02_, etc.)
- **Автоматическая загрузка:** шаблоны загружаются при первом использовании
- **Кэширование:** шаблоны кэшируются в памяти для производительности

### Доступные шаблоны

По умолчанию доступны следующие шаблоны:

- `01_description.js` - извлечение описания страницы (meta description или основной контент)
- `02_contact.js` - контактная информация (email, телефон)
- `03_hours.js` - часы работы
- `04_address.js` - адрес
- `05_social.js` - социальные сети

## Установка

### В Docker

Все зависимости уже установлены в Docker образе. При первом запуске pyppeteer автоматически скачает Chromium.

### Локально

Если вы запускаете проект локально (без Docker):

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. pyppeteer автоматически скачает Chromium при первом использовании

3. Для работы в headless режиме убедитесь, что установлены системные зависимости:
   - На Linux: библиотеки для работы с окнами (libx11, libxcomposite, etc.)
   - На macOS: обычно все уже установлено
   - На Windows: обычно все уже установлено

## Конфигурация

### Переменные окружения

Настройка через `.env` файл:

```env
# Настройки браузера
BROWSER_TIMEOUT=15000          # Таймаут в миллисекундах
BROWSER_HEADLESS=true          # Headless режим

# Настройки параллелизма
PIPELINE_ENRICH_DATA=true      # Включить обогащение
PIPELINE_MAX_CONCURRENT_ENRICHMENT=3  # Количество параллельных обогащений
```

### Программная настройка

Можно настроить через код:

```python
from src.extraction import BrowserManager

browser_manager = BrowserManager()
await browser_manager.launch_browser(
    headless=True,
    timeout=15000
)
```

## Использование

### Базовое использование

Модуль обогащения автоматически используется в pipeline:

```python
from src.google_places_parser import GooglePlacesParser

parser = GooglePlacesParser()
await parser.call_with_settings()  # Обогащение включено по умолчанию
```

### Отключение обогащения

Для отключения обогащения данных:

1. В `.env`:
```env
PIPELINE_ENRICH_DATA=false
```

2. Или программно:
```python
context.enrich_data = False
```

### Добавление нового шаблона

1. Создайте файл `NN_fieldname.js` в папке `src/extraction/templates/`:
   - `NN` - номер для порядка выполнения (06, 07, etc.)
   - `fieldname` - имя поля (будет использовано как ключ в extracted_fields)

2. Напишите JavaScript код для извлечения данных:
```javascript
() => {
    // Ваш код извлечения данных
    const element = document.querySelector('selector');
    return element ? element.textContent.trim() : null;
}
```

3. Шаблон будет автоматически загружен при следующем запуске

4. Для принудительной перезагрузки кэша:
```python
from src.extraction.templates import ExtractionTemplates

ExtractionTemplates.clear_cache()
```

### Пример шаблона

Пример шаблона для извлечения email:

```javascript
() => {
    // Ищем email в тексте страницы
    const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
    const bodyText = document.body.innerText;
    const matches = bodyText.match(emailRegex);
    return matches ? matches[0] : null;
}
```

## Решение проблем

### Ошибка: "Chromium не скачивается"

pyppeteer пытается скачать Chromium при первом запуске. Если это не удается:

1. Проверьте интернет-соединение
2. Проверьте права доступа на запись в `~/.local/share/pyppeteer/`
3. Попробуйте скачать вручную и поместить в нужную папку

### Ошибка: "Chrome/Chromium не найден"

Убедитесь, что:
1. pyppeteer успешно скачал Chromium
2. Путь к Chromium доступен
3. В Docker контейнере все системные зависимости установлены

### Ошибка: "Timeout при загрузке страницы"

Увеличьте таймаут в `.env`:
```env
BROWSER_TIMEOUT=30000  # 30 секунд
```

Или для конкретного сайта можно обработать таймаут в коде.

### Ошибка: "Сайт блокирует доступ"

Некоторые сайты могут блокировать автоматизированный доступ. Система использует `pyppeteer-stealth` для обхода защиты, но это не всегда работает.

В этом случае:
1. Данные сохраняются без обогащения
2. Ошибка логируется
3. Pipeline продолжает работу с другими сайтами

### Проблемы с производительностью

Если обогащение работает медленно:

1. Увеличьте `PIPELINE_MAX_CONCURRENT_ENRICHMENT` для параллельной обработки
2. Уменьшите `BROWSER_TIMEOUT` для быстрого пропуска недоступных сайтов
3. Отключите обогащение для тестирования: `PIPELINE_ENRICH_DATA=false`

### Проблемы с памятью

Если браузер потребляет много памяти:

1. Уменьшите `PIPELINE_MAX_CONCURRENT_ENRICHMENT`
2. Убедитесь, что браузер правильно закрывается после использования
3. Проверьте логи на наличие утечек памяти

## Отладка

### Включение детального логирования

Установите в `.env`:
```env
PIPELINE_LOGLEVEL=DEBUG
```

### Визуальное наблюдение за браузером

Для локальной разработки можно отключить headless режим:

```env
BROWSER_HEADLESS=false
```

**Примечание:** Это работает только локально, в Docker контейнере нужен headless режим.

### Проверка шаблонов

Для проверки загруженных шаблонов:

```python
from src.extraction.templates import ExtractionTemplates

# Получить список доступных полей
fields = ExtractionTemplates.get_available_fields()
print(f"Доступные поля: {fields}")

# Получить конкретный шаблон
template = ExtractionTemplates.get_template('description')
print(f"Шаблон description: {template}")

# Получить все шаблоны
all_templates = ExtractionTemplates.get_all_templates()
print(f"Всего шаблонов: {len(all_templates)}")
```

## Будущие улучшения

В будущем планируется:

1. **Поддержка Playwright** - альтернативная библиотека для браузерной автоматизации
2. **Кэширование результатов** - сохранение извлеченных данных для повторного использования
3. **Расширенные шаблоны** - поддержка более сложных сценариев извлечения
4. **Мониторинг качества** - отслеживание успешности извлечения по шаблонам