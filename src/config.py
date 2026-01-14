"""
Модуль конфигурации приложения.

Предоставляет настройки для подключения к базе данных и внешним
API, а также параметры поиска через переменные окружения.
"""

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()


class DatabaseSettings(BaseSettings):
    """Настройки подключения к PostgreSQL."""

    host: str
    port: int
    db: str
    user: str
    password: str

    # Настройки пула соединений
    min_size: int = 5
    max_size: int = 20
    command_timeout: float = 60.0  # Таймаут команд в секундах
    # Максимальное время жизни неактивного соединения
    max_inactive_connection_lifetime: float = 300.0

    class Config:
        env_prefix = "POSTGRES_"
        case_sensitive = False
    
    @property
    def connection_string(self) -> str:
        """Возвращает строку подключения к базе данных."""
        # Убираем экранирование для тестирования
        # psycopg2 должен справляться с простыми паролями
        return (
            f"postgresql://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.db}"
        )


class GooglePlacesSettings(BaseSettings):
    """Настройки для Google Places API."""

    api_key: str
    radius: int  # Радиус поиска в метрах
    max_results: int  # Максимальное количество результатов
    page_size: int  # Размер страницы (максимум 20 по API)
    request_delay: float  # Задержка между запросами в секундах
    initial_delay: float  # Начальная задержка перед первым запросом

    class Config:
        env_prefix = "GOOGLE_PLACES_"
        case_sensitive = False


class SearchSettings(BaseSettings):
    """Параметры поиска магазинов."""

    region: str
    postal_code: str
    category: str
    
    class Config:
        env_prefix = "SEARCH_"
        case_sensitive = False


class BrowserSettings(BaseSettings):
    """Настройки браузера для веб-скрапинга."""

    timeout: int  # Таймаут операций в миллисекундах
    headless: bool  # Запуск в headless режиме

    class Config:
        env_prefix = "BROWSER_"
        case_sensitive = False


class PipelineSettings(BaseSettings):
    """Настройки параллелизма pipeline."""

    streaming: bool = False
    enrich_data: bool = True
    max_concurrent_enrichment: int = 2
    max_concurrent_db_writes: int = 5
    loglevel: str = "DEBUG"

    class Config:
        env_prefix = "PIPELINE_"
        case_sensitive = False


class Settings:
    """Главный класс настроек приложения."""

    def __init__(self):
        self.database = DatabaseSettings()
        self.google_places = GooglePlacesSettings()
        self.search = SearchSettings()
        self.pipeline = PipelineSettings()
        self.browser = BrowserSettings()


# Глобальный экземпляр настроек
settings = Settings()


if __name__ == "__main__":  # noqa
    """Тест конфигурации."""
    import os

    print("=== Тест конфигурации ===")

    # Тест настроек базы данных
    db_settings = DatabaseSettings()
    print(f"[OK] База данных: {db_settings.connection_string}")

    # Тест настроек поиска
    search_settings = SearchSettings()
    print(f"[OK] Поиск: {search_settings.category} в {search_settings.region}")

    # Тест настроек pipeline
    pipeline_settings = PipelineSettings()
    print(f"[OK] Pipeline: {pipeline_settings.max_concurrent_enrichment} параллельных обогащений")

    # Тест настроек браузера
    browser_settings = BrowserSettings()
    print(f"[OK] Браузер: таймаут {browser_settings.timeout}мс, headless={browser_settings.headless}")

    # Все переменные теперь обязательные
    required_env_vars = [
        "GOOGLE_PLACES_API_KEY",
        "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB",
        "POSTGRES_USER", "POSTGRES_PASSWORD",
        "POSTGRES_MIN_SIZE", "POSTGRES_MAX_SIZE",
        "POSTGRES_COMMAND_TIMEOUT",
        "POSTGRES_MAX_INACTIVE_CONNECTION_LIFETIME",
        "GOOGLE_PLACES_RADIUS", "GOOGLE_PLACES_MAX_RESULTS",
        "GOOGLE_PLACES_PAGE_SIZE", "GOOGLE_PLACES_REQUEST_DELAY",
        "GOOGLE_PLACES_INITIAL_DELAY",
        "SEARCH_REGION", "SEARCH_POSTAL_CODE", "SEARCH_CATEGORY",
        "PIPELINE_MAX_CONCURRENT_ENRICHMENT",
        "PIPELINE_MAX_CONCURRENT_DB_WRITES", "PIPELINE_LOGLEVEL",
        "BROWSER_TIMEOUT", "BROWSER_HEADLESS"
    ]

    print(
        "\n=== Проверка переменных среды (все обязательные) ==="
    )
    missing_vars = []
    for var in required_env_vars:
        value = os.getenv(var)
        if value:
            print(f"[OK] {var}: {value}")
        else:
            print(f"[ERROR] {var}: НЕ УСТАНОВЛЕНА")
            missing_vars.append(var)

    if missing_vars:
        missing_str = ', '.join(missing_vars)
        print(f"\n[ERROR] Отсутствуют обязательные переменные: "
              f"{missing_str}")
        print("Все переменные окружения должны быть установлены!")
    else:
        print("\n[SUCCESS] Все обязательные переменные установлены!")

    # Тест глобальных настроек
    try:
        global_settings = Settings()
        print("[OK] Глобальные настройки: инициализированы")
        api_key_status = (
            'установлен' if global_settings.google_places.api_key
            else 'не установлен'
        )
        print(f"  - API ключ: {api_key_status}")
    except Exception as e:
        print(f"[WARN] Глобальные настройки: ошибка - {e}")

    print("\n=== Все тесты завершены ===")
