"""
Главный модуль Data Ingestion Pipeline.

Оркестрирует процесс извлечения данных о магазинах через Google Places API,
обогащения данных и сохранения в базу данных PostgreSQL.
"""

import logging
import sys
import asyncio
from typing import List, Dict, Optional
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

from src.config import settings
from src.database import db_manager
from src.models import Store
from src.places_api import GooglePlacesAPI
from src.enrichment import WebsiteEnricher

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class PlacesIngestionPipeline:
    """
    Класс для оркестрации процесса извлечения и сохранения данных о магазинах.
    
    Координирует работу между Google Places API, обогащением данных
    и сохранением в базу данных.
    """
    
    def __init__(
        self,
        api_key: str,
        search_region: str,
        search_category: str,
        postal_code: str = None
    ):
        """
        Инициализирует pipeline.
        
        Args:
            api_key: API ключ для Google Places API.
            search_region: Регион для поиска (например, "Byron Bay, NSW, Australia").
            search_category: Категория магазинов для поиска.
            postal_code: Почтовый индекс региона (опционально).
        """
        if not api_key:
            raise ValueError(
                "Переменная окружения GOOGLE_PLACES_API_KEY не задана. "
                "Укажите ключ в файле .env или передайте его в docker-compose."
            )
        self.api_client = GooglePlacesAPI(api_key)
        self.enricher = WebsiteEnricher(headless=True)
        self.search_region = search_region
        self.search_category = search_category
        self.postal_code = postal_code
    
    def build_search_query(self) -> str:
        """
        Формирует поисковый запрос на основе параметров.
        
        Returns:
            Строка поискового запроса.
        """
        query_parts = [self.search_category]
        if self.postal_code:
            query_parts.append(f"postal code {self.postal_code}")
        return " ".join(query_parts)
    
    def fetch_stores(self, max_results: int = 60) -> List[Dict]:
        """
        Извлекает данные о магазинах через Google Places API.
        
        Args:
            max_results: Максимальное количество результатов.
            
        Returns:
            Список словарей с данными о магазинах.
        """
        logger.info(f"Начало поиска магазинов: {self.search_category} в {self.search_region}")
        
        query = self.build_search_query()
        location = self.search_region
        
        try:
            places = self.api_client.search_places(
                query=query,
                location=location,
                max_results=max_results
            )
            
            normalized_stores = []
            for place in places:
                try:
                    normalized = self.api_client.normalize_place_data(place)
                    if normalized.get("place_id"):
                        normalized_stores.append(normalized)
                except Exception as e:
                    logger.warning(f"Ошибка при нормализации данных места: {e}")
                    continue
            
            logger.info(f"Успешно обработано мест: {len(normalized_stores)}")
            return normalized_stores
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении данных о магазинах: {e}")
            raise
    
    async def enrich_store_data_async(self, store_data: Dict, semaphore: asyncio.Semaphore) -> Dict:
        """
        Асинхронно обогащает данные магазина информацией с веб-сайта.
        
        Args:
            store_data: Словарь с базовыми данными магазина.
            semaphore: Семафор для ограничения параллелизма.
            
        Returns:
            Словарь с обогащенными данными.
        """
        website = store_data.get("website")
        if not website:
            logger.debug(f"Веб-сайт отсутствует для {store_data.get('name')}")
            return store_data
        
        async with semaphore:
            try:
                logger.info(f"Обогащение данных для {store_data.get('name')}: {website}")
                description = await self.enricher.extract_description(website)
                store_data["description"] = description
                if description:
                    logger.debug(f"Описание успешно извлечено для {store_data.get('name')}")
            except Exception as e:
                logger.warning(f"Ошибка при обогащении данных для {store_data.get('name')}: {e}")
        
        return store_data
    
    def save_store_sync(self, store_data: Dict) -> Optional[Store]:
        """
        Синхронно сохраняет или обновляет данные магазина в базе данных.
        
        Args:
            store_data: Словарь с данными магазина.
            
        Returns:
            Объект Store из базы данных или None при ошибке.
        """
        place_id = store_data.get("place_id")
        if not place_id:
            logger.error("Place ID обязателен для сохранения")
            return None
        
        try:
            with db_manager.get_session() as session:
                # Проверяем существование записи
                existing_store = session.query(Store).filter_by(place_id=place_id).first()
                
                if existing_store:
                    # Обновляем существующую запись
                    existing_store.name = store_data.get("name", existing_store.name)
                    existing_store.website = store_data.get("website") or existing_store.website
                    existing_store.phone = store_data.get("phone") or existing_store.phone
                    existing_store.address = store_data.get("address") or existing_store.address
                    if store_data.get("description"):
                        existing_store.description = store_data.get("description")
                    logger.debug(f"Обновлена запись: {existing_store.name}")
                    return existing_store
                else:
                    # Создаем новую запись
                    store = Store(
                        id=str(uuid4()),
                        name=store_data.get("name", ""),
                        website=store_data.get("website"),
                        phone=store_data.get("phone"),
                        address=store_data.get("address"),
                        place_id=place_id,
                        description=store_data.get("description")
                    )
                    session.add(store)
                    logger.debug(f"Создана новая запись: {store.name}")
                    return store
        except Exception as e:
            logger.error(f"Ошибка при сохранении магазина {store_data.get('name')}: {e}")
            return None
    
    async def save_store_async(
        self, 
        store_data: Dict, 
        executor: ThreadPoolExecutor
    ) -> Optional[Store]:
        """
        Асинхронно сохраняет данные магазина в базе данных через ThreadPoolExecutor.
        
        Args:
            store_data: Словарь с данными магазина.
            executor: ThreadPoolExecutor для выполнения синхронных операций БД.
            
        Returns:
            Объект Store из базы данных или None при ошибке.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, self.save_store_sync, store_data)
    
    async def run_async(self, enrich: bool = True, max_results: int = 60) -> None:
        """
        Асинхронно запускает полный цикл извлечения и сохранения данных.
        
        Параллельно выполняет обогащение данных и запись в БД с ограничением
        параллелизма через переменные окружения.
        
        Args:
            enrich: Включить обогащение данных через веб-сайты.
            max_results: Максимальное количество результатов для обработки.
        """
        try:
            # Инициализация базы данных
            logger.info("Инициализация базы данных...")
            db_manager.init_db()
            
            # Извлечение данных
            stores_data = self.fetch_stores(max_results=max_results)
            
            if not stores_data:
                logger.warning("Не найдено магазинов для обработки")
                return
            
            # Настройки параллелизма из переменных окружения
            max_enrichment = settings.pipeline.max_concurrent_enrichment
            max_db_writes = settings.pipeline.max_concurrent_db_writes
            
            logger.info(
                f"Начало параллельной обработки {len(stores_data)} магазинов "
                f"(обогащение: {max_enrichment} параллельно, БД: {max_db_writes} параллельно)"
            )
            
            # Создаем семафоры для ограничения параллелизма
            enrichment_semaphore = asyncio.Semaphore(max_enrichment)
            db_semaphore = asyncio.Semaphore(max_db_writes)
            
            # ThreadPoolExecutor для синхронных операций БД
            db_executor = ThreadPoolExecutor(max_workers=max_db_writes)
            
            # Счетчики с блокировками для thread-safe операций
            saved_count_lock = asyncio.Lock()
            enriched_count_lock = asyncio.Lock()
            saved_count = 0
            enriched_count = 0
            
            # Создаем задачи для параллельного выполнения
            async def process_store(store_data: Dict, index: int) -> None:
                """Обрабатывает один магазин: обогащение и сохранение."""
                try:
                    logger.info(f"Обработка {index}/{len(stores_data)}: {store_data.get('name')}")
                    
                    # Обогащение данных (если включено)
                    if enrich:
                        store_data = await self.enrich_store_data_async(
                            store_data, 
                            enrichment_semaphore
                        )
                        if store_data.get("description"):
                            async with enriched_count_lock:
                                nonlocal enriched_count
                                enriched_count += 1
                    
                    # Сохранение в базу данных с ограничением параллелизма
                    async with db_semaphore:
                        result = await self.save_store_async(store_data, db_executor)
                        if result:
                            async with saved_count_lock:
                                nonlocal saved_count
                                saved_count += 1
                    
                except Exception as e:
                    logger.error(f"Ошибка при обработке магазина {store_data.get('name')}: {e}")
            
            # Запускаем все задачи параллельно
            tasks = [
                process_store(store_data, i + 1)
                for i, store_data in enumerate(stores_data)
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            logger.info(
                f"Обработка завершена. Сохранено: {saved_count}/{len(stores_data)}, "
                f"Обогащено: {enriched_count}/{len(stores_data)}"
            )
            
            # Закрываем executor
            db_executor.shutdown(wait=True)
        
        except Exception as e:
            logger.error(f"Критическая ошибка в pipeline: {e}")
            raise
        finally:
            db_manager.close()
    
    def run(self, enrich: bool = True, max_results: int = 60) -> None:
        """
        Синхронная обертка для запуска асинхронного pipeline.
        
        Args:
            enrich: Включить обогащение данных через веб-сайты.
            max_results: Максимальное количество результатов для обработки.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(self.run_async(enrich=enrich, max_results=max_results))


def main():
    """Главная функция для запуска pipeline."""
    try:
        pipeline = PlacesIngestionPipeline(
            api_key=settings.google_places.api_key,
            search_region=settings.search.region,
            search_category=settings.search.category,
            postal_code=settings.search.postal_code
        )
        
        pipeline.run(enrich=True, max_results=60)
        
        logger.info("Pipeline успешно завершен")
        
    except Exception as e:
        logger.error(f"Ошибка при выполнении pipeline: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

