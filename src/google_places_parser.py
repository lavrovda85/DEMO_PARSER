"""
Google Places Parser - основная обертка для парсинга данных.

Предоставляет синхронные и асинхронные интерфейсы для работы
с Google Places API через ETL pipeline.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from .config import settings
from .pipeline import PipelineOrchestrator, PipelineContext
from .pipeline.fetcher import DataFetcher
from .pipeline.enricher import DataEnricher
from .storage import ClickHouseDataSaver

logger = logging.getLogger(__name__)


class PipelineExecutor:
    """
    Исполнитель ETL pipeline.

    Управляет жизненным циклом pipeline и его ресурсами.
    """

    def __init__(self):
        """
        Инициализирует исполнитель pipeline.
        """
        self.logger = logging.getLogger(__name__)

        # Создаем оркестратор с последовательностью этапов
        self.orchestrator = PipelineOrchestrator([
            DataFetcher(),
            DataEnricher(),
            ClickHouseDataSaver()
        ])

    async def _run_pipeline(self, context) -> None:
        """
        Выполняет ETL pipeline с заданным контекстом.
        """
        if settings.pipeline.streaming:
            await self._run_streaming_pipeline(context)
        else:
            await self._run_batch_pipeline(context)

    async def _run_batch_pipeline(self, context) -> None:
        """
        Запускает pipeline в batch режиме.
        """
        # Параллельная инициализация ресурсов
        await self._init_resources_parallel(context)

        # Выполнение pipeline
        await self.orchestrator.execute_pipeline(context)

    async def _run_streaming_pipeline(self, context) -> None:
        """
        Запускает pipeline в streaming режиме.
        """
        # Параллельная инициализация ресурсов
        await self._init_resources_parallel(context)

        # Получаем streaming данные от fetcher
        fetcher = None
        for step in self.orchestrator.steps:
            if hasattr(step, 'stream_data'):
                fetcher = step
                break

        if not fetcher:
            raise ValueError("DataFetcher не найден в pipeline")

        data_stream = fetcher.stream_data(context)
        await self.orchestrator.execute_streaming_pipeline(
            data_stream, context
        )

    async def _init_resources_parallel(self, context) -> None:
        """
        Параллельно инициализирует все необходимые ресурсы.
        """
        import asyncio
        from .database import async_db_manager

        # Создаем задачи для параллельной инициализации
        tasks = []

        # Задача инициализации БД (если сохранение включено)
        db_available = True
        if self._should_save_to_db():
            db_task = asyncio.create_task(async_db_manager.init_pool())
            tasks.append(db_task)
        else:
            db_available = False
            self._disable_db_saving()

        # Задача запуска браузера (если используется обогащение)
        if context.enrich_data:
            browser_task = None
            enricher = None
            for step in self.orchestrator.steps:
                if hasattr(step, 'browser_manager'):
                    enricher = step
                    break

            if enricher:
                from .extraction import BrowserManager
                browser_manager = BrowserManager()
                browser_task = asyncio.create_task(browser_manager.launch_browser())
                tasks.append(browser_task)
                enricher.browser_manager = browser_manager

        # Ждем завершения всех задач инициализации
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if not isinstance(r, Exception))

            # Проверяем, удалось ли инициализировать БД
            if db_available and any(isinstance(r, Exception) for r in results[:1]):  # Первый результат - БД
                self.logger.warning("БД недоступна, сохранение отключено")
                db_available = False
                self._disable_db_saving()

            if db_available:
                self.logger.info(f"Ресурсы инициализированы: {success_count}/{len(tasks)} (БД+браузер)")
            else:
                self.logger.info(f"Ресурсы инициализированы: {success_count}/{len(tasks)} (БД отключена)")
        except Exception as e:
            self.logger.error(f"Ошибка инициализации ресурсов: {e}")
            raise

    def _should_save_to_db(self) -> bool:
        """
        Определяет, нужно ли сохранять данные в БД.
        """
        # Можно добавить настройку для отключения БД
        return True  # Пока всегда пытаемся сохранять

    def _disable_db_saving(self):
        """
        Отключает сохранение в БД, удаляя DataSaver из pipeline.
        """
        # Удаляем все шаги сохранения из оркестратора
        steps_to_remove = []
        for i, step in enumerate(self.orchestrator.steps):
            if step.__class__.__name__ == 'ClickHouseDataSaver':
                steps_to_remove.append(i)

        # Удаляем с конца, чтобы индексы не смещались
        for i in reversed(steps_to_remove):
            del self.orchestrator.steps[i]

        self.logger.info("Сохранение в БД отключено")


class GooglePlacesParser:
    """
    Парсер Google Places API с поддержкой ETL pipeline.

    Предоставляет интерфейс для парсинга данных о местах из Google Places API
    с возможностью обогащения через веб-скрапинг и сохранения в ClickHouse.
    """

    def __init__(self):
        """
        Инициализирует парсер.
        """
        self.logger = logging.getLogger(__name__)
        self.executor = PipelineExecutor()

    async def _call_with_settings(self) -> None:
        """
        Запускает парсинг с настройками из конфигурации (для main).

        Использует параметры из settings для поиска и обработки данных.
        """
        # Создаем контекст выполнения с настройками из config
        context = PipelineContext(
            api_key=settings.google_places.api_key,
            search_region=settings.search.region,
            search_category=settings.search.category,
            postal_code=settings.search.postal_code
        )

        # Запускаем pipeline
        await self.executor._run_pipeline(context)

    async def call_with_settings(self) -> None:
        """
        Асинхронная обертка для _call_with_settings().

        Используется в main.py для запуска с настройками из конфигурации.
        """
        await self._call_with_settings()

    async def parse(
        self,
        region: str,
        category: str,
        postal_code: str = "",
        max_results: int = 50,
        enrich_data: bool = True
    ) -> Dict[str, Any]:
        """
        Парсит данные о местах с заданными параметрами (для Jupyter).

        Args:
            region: Регион поиска (например, "Byron Bay, NSW, Australia")
            category: Категория мест (например, "Women's Clothing Store")
            postal_code: Почтовый индекс (опционально)
            max_results: Максимальное количество результатов
            enrich_data: Обогащать ли данные веб-скрапингом

        Returns:
            Словарь с результатами выполнения
        """
        # Создаем контекст выполнения с переданными параметрами
        context = PipelineContext(
            api_key=settings.google_places.api_key,
            search_region=region,
            search_category=category,
            postal_code=postal_code
        )
        # Переопределяем настройки из параметров
        context.max_results = max_results
        context.enrich_data = enrich_data

        try:
            # Запускаем pipeline
            await self.executor._run_pipeline(context)

            return {
                "status": "success",
                "message": f"Успешно обработано мест: {len(context.extracted_data) if hasattr(context, 'extracted_data') and context.extracted_data else 'неизвестно'}",
                "region": region,
                "category": category,
                "max_results": max_results,
                "enrich_data": enrich_data
            }

        except Exception as e:
            self.logger.error(f"Ошибка при парсинге: {e}")
            return {
                "status": "error",
                "message": str(e),
                "region": region,
                "category": category
            }

    def parse_sync(
        self,
        region: str,
        category: str,
        postal_code: str = "",
        max_results: int = 50,
        enrich_data: bool = True
    ) -> Dict[str, Any]:
        """
        Синхронная обертка для parse().

        Удобна для использования в Jupyter notebook без async/await.
        """
        return asyncio.run(self.parse(
            region=region,
            category=category,
            postal_code=postal_code,
            max_results=max_results,
            enrich_data=enrich_data
        ))
