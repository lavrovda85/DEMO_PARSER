"""
Модуль конфигурации приложения.

Предоставляет настройки для подключения к базе данных и внешним API,
а также параметры поиска через переменные окружения.
"""

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()


class DatabaseSettings(BaseSettings):
    """Настройки подключения к PostgreSQL."""
    
    host: str = "localhost"
    port: int = 5432
    db: str = "places_db"
    user: str = "places_user"
    password: str = "places_password"
    
    class Config:
        env_prefix = "POSTGRES_"
        case_sensitive = False
    
    @property
    def connection_string(self) -> str:
        """Возвращает строку подключения к базе данных."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class GooglePlacesSettings(BaseSettings):
    """Настройки для Google Places API."""
    
    api_key: str
    
    class Config:
        env_prefix = "GOOGLE_PLACES_"
        case_sensitive = False


class SearchSettings(BaseSettings):
    """Параметры поиска магазинов."""
    
    region: str = "Byron Bay, NSW, Australia"
    postal_code: str = "2481"
    category: str = "Women's Clothing Store"
    
    class Config:
        env_prefix = "SEARCH_"
        case_sensitive = False


class EnrichmentSettings(BaseSettings):
    """Настройки модуля обогащения данных."""
    
    # Выбор библиотеки для браузерной автоматизации
    # Возможные значения: "playwright", "pyppeteer", "auto"
    # "auto" - автоматический выбор на основе доступности библиотек
    browser_library: str = "auto"
    
    # Headless режим браузера
    headless: bool = True
    
    # Таймаут загрузки страницы в миллисекундах
    timeout: int = 30000
    
    class Config:
        env_prefix = "ENRICHMENT_"
        case_sensitive = False


class PipelineSettings(BaseSettings):
    """Настройки параллелизма pipeline."""
    
    max_concurrent_enrichment: int = 5
    max_concurrent_db_writes: int = 10
    
    class Config:
        env_prefix = "PIPELINE_"
        case_sensitive = False


class Settings:
    """Главный класс настроек приложения."""
    
    def __init__(self):
        self.database = DatabaseSettings()
        self.google_places = GooglePlacesSettings()
        self.search = SearchSettings()
        self.enrichment = EnrichmentSettings()
        self.pipeline = PipelineSettings()


# Глобальный экземпляр настроек
settings = Settings()

