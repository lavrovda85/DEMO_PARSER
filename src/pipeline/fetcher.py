"""
Компонент извлечения данных из Google Places API.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, AsyncGenerator
from src.api.search import stream_places_async
from .base import ETLStep, PipelineContext

logger = logging.getLogger(__name__)


class DataFetcher(ETLStep):
    """
    Компонент для асинхронного извлечения данных о магазинах из
    Google Places API.

    Работает как streaming processor - извлекает данные постранично
    и передает их дальше для немедленной обработки.
    """

    def __init__(self):
        """
        Инициализирует компонент извлечения данных.
        """
        from ..config import settings
        super().__init__("Data Fetching")
        self.page_size = settings.google_places.page_size

    def _build_search_query(self, context: PipelineContext) -> str:
        """
        Формирует поисковый запрос на основе параметров контекста.

        Args:
            context: Контекст выполнения pipeline

        Returns:
            Строка поискового запроса
        """
        query_parts = [context.search_category]
        if context.postal_code:
            query_parts.append(f"postal code {context.postal_code}")
        return " ".join(query_parts)

    async def stream_data(
        self, context: PipelineContext
    ) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """
        Асинхронный генератор данных - извлекает места постранично.

        Args:
            context: Контекст выполнения pipeline

        Yields:
            Страницы данных для обработки
        """
        query = self._build_search_query(context)
        location = context.search_region

        self.logger.info(
            f"Streaming поиск магазинов: {context.search_category} "
            f"в {context.search_region} "
            f"(макс. {context.max_results}, "
            f"страницы по {self.page_size})"
        )

        try:
            async for page in stream_places_async(
                query=query,
                location=location,
                include_details=True
            ):
                self.logger.info(f"Извлечена страница из {len(page)} мест")

                # Добавляем raw_api_response к каждому месту для новой архитектуры
                for place in page:
                    # Сохраняем полный сырой ответ API для raw layer
                    place['raw_api_response'] = json.dumps(place, ensure_ascii=False)
                    place['record_source'] = 'google_places_api'

                # Покажем первые 2 места для отладки
                for place in page[:2]:
                    place_name = place.get('name')
                    place_phone = place.get('phone')
                    place_website = place.get('website')
                    self.logger.info(
                        f"  Место: {place_name}, "
                        f"телефон: {place_phone}, "
                        f"сайт: {place_website}"
                    )
                yield page

        except Exception as e:
            self.logger.error(
            f"Ошибка при streaming извлечении данных: {e}"
        )
            raise

    async def execute(self, context: PipelineContext) -> None:
        """
        Для обратной совместимости - собирает все данные в context.

        В будущем этапы должны работать со streaming данными
        напрямую.
        """
        context.extracted_data = []

        async for page in self.stream_data(context):
            context.extracted_data.extend(page)

        self.logger.info(f"Всего извлечено мест: {len(context.extracted_data)}")


if __name__ == "__main__":  # noqa
    import asyncio

    async def test_data_fetcher():
        """Тест DataFetcher."""
        fetcher = DataFetcher()

        # Тест формирования запроса
        context = type('MockContext', (), {
            'search_category': 'Test Stores',
            'postal_code': '12345',
            'search_region': 'Test City',
            'max_results': 10,
            'extracted_data': []
        })()

        query = await fetcher._build_search_query(context)  # noqa: protected-access
        assert query == "Test Stores postal code 12345"

        print("[OK] DataFetcher тест пройден")

    asyncio.run(test_data_fetcher())
