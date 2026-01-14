"""
Базовые классы для ETL паттерна.

Определяет абстрактные интерфейсы для компонентов pipeline.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)



@dataclass
class PipelineContext:
    """
    Контекст выполнения pipeline.

    Содержит общие данные и настройки для всех этапов pipeline.
    """
    api_key: str
    search_region: str
    search_category: str
    postal_code: Optional[str] = None

    # Runtime данные
    extracted_data: List[Dict[str, Any]] = None
    transformed_data: List[Dict[str, Any]] = None
    saved_count: int = 0
    enriched_count: int = 0

    def __post_init__(self):
        # Берем настройки из config
        from ..config import settings
        self.max_results = settings.google_places.max_results
        self.enrich_data = True  # Всегда обогащаем данные

        if self.extracted_data is None:
            self.extracted_data = []
        if self.transformed_data is None:
            self.transformed_data = []


class ETLStep(ABC):
    """
    Абстрактный базовый класс для этапа ETL pipeline.

    Каждый этап должен реализовывать метод execute.
    """

    def __init__(self, name: str):
        self.name = name
        class_name = self.__class__.__name__
        self.logger = logging.getLogger(f"{__name__}.{class_name}")

    @abstractmethod
    async def execute(self, context: PipelineContext) -> None:
        """
        Выполняет этап pipeline.

        Args:
            context: Контекст выполнения pipeline
        """
        pass

    def log_start(self) -> None:
        """Логирует начало выполнения этапа."""
        self.logger.info(f"Начало этапа: {self.name}")

    def log_finish(self) -> None:
        """Логирует завершение выполнения этапа."""
        self.logger.info(f"Завершен этап: {self.name}")

    async def safe_execute(self, context: PipelineContext) -> None:
        """
        Безопасное выполнение этапа с обработкой ошибок.

        Args:
            context: Контекст выполнения pipeline
        """
        try:
            self.log_start()
            await self.execute(context)
            self.log_finish()
        except Exception as e:
            self.logger.error(f"Ошибка в этапе {self.name}: {e}")
            raise



if __name__ == "__main__":
    import asyncio

    async def test_pipeline_context():
        """Тест PipelineContext."""
        # Устанавливаем тестовые переменные окружения
        import os
        old_max_results = os.environ.get('GOOGLE_PLACES_MAX_RESULTS')
        os.environ['GOOGLE_PLACES_MAX_RESULTS'] = '10'

        try:
            context = PipelineContext(
                api_key="test_key",
                search_region="Test City",
                search_category="Test Stores"
            )

            assert context.api_key == "test_key"
            assert context.search_region == "Test City"
            assert context.search_category == "Test Stores"
            assert context.max_results == 10  # Берется из settings
            assert context.enrich_data is True  # Всегда True
            assert context.extracted_data == []
            assert context.transformed_data == []
            assert context.saved_count == 0
            assert context.enriched_count == 0

            print("[OK] PipelineContext тест пройден")
        finally:
            # Восстанавливаем переменную окружения
            if old_max_results is not None:
                os.environ['GOOGLE_PLACES_MAX_RESULTS'] = old_max_results
            elif 'GOOGLE_PLACES_MAX_RESULTS' in os.environ:
                del os.environ['GOOGLE_PLACES_MAX_RESULTS']

    asyncio.run(test_pipeline_context())


