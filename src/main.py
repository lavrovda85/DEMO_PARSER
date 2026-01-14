"""
Главный модуль Data Ingestion Pipeline.

Высокоуровневая обертка для запуска ETL pipeline обработки данных
о магазинах.
"""
from dotenv import load_dotenv
load_dotenv()
import logging
import signal
import sys
import asyncio

# Загружаем переменные окружения из .env файла


# Теперь импортируем config, когда .env уже загружен
from src.config import settings
from src.google_places_parser import GooglePlacesParser

# Настройка логирования
logging.basicConfig(
    level=settings.pipeline.loglevel,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)




async def main():
    """Главная функция для запуска pipeline."""
    print("DEBUG: main() started")

    # Настройка signal handlers для graceful shutdown
    def signal_handler(signum, frame):
        """Обработчик сигналов для graceful shutdown."""
        logger.info(f"Получен сигнал {signum}, завершаем работу...")
        # Не нужно ничего делать, asyncio event loop сам обработает
        pass

    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        print("DEBUG: Sleeping for ClickHouse startup...")
        # Ждем, пока ClickHouse полностью запустится
        logger.info("Ждем запуска ClickHouse...")
        await asyncio.sleep(5)
        print("DEBUG: Sleep finished")
        # Создаем парсер и запускаем с настройками из конфигурации
        parser = GooglePlacesParser()
        await parser.call_with_settings()
        logger.info("Парсинг успешно завершен")

    except Exception as e:
        logger.error(f"Ошибка при выполнении парсинга: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())