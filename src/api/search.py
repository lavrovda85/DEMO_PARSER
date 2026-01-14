"""
Функции для поиска мест через Google Places API.
"""

import asyncio
import logging
from typing import List, Dict, Optional, AsyncGenerator

from src.config import settings
from .factory import create_async_places_client
from .normalizer import PlaceDataNormalizer

logger = logging.getLogger(__name__)


async def search_all_places_async(
    query: str,
    location: Optional[str] = None
) -> List[Dict]:
    """
    Выполняет полный поиск всех мест асинхронно.

    Args:
        query: Поисковый запрос
        location: Локация для поиска

    Returns:
        Список нормализованных данных мест
    """
    api_key = settings.google_places.api_key
    normalizer = PlaceDataNormalizer()

    async with create_async_places_client(api_key) as client:
        places = []
        async for place in client.search_places_paginated(
            query=query,
            location=location
        ):
            normalized = normalizer.normalize(place)
            if normalized.get('place_id'):
                places.append(normalized)

        logger.info(f"Найдено мест асинхронно: {len(places)}")
        return places


async def stream_places_async(
    query: str,
    location: Optional[str] = None,
    include_details: bool = True
) -> AsyncGenerator[List[Dict], None]:
    """
    Асинхронный генератор для постраничного получения мест.

    Args:
        query: Поисковый запрос
        location: Локация для поиска
        include_details: Включать детальную информацию

    Yields:
        Список мест (страница) для обработки
    """
    api_key = settings.google_places.api_key
    page_size = settings.google_places.page_size
    normalizer = PlaceDataNormalizer()

    async with create_async_places_client(api_key) as client:
        page = []
        total_yielded = 0

        async for place in client.search_places_paginated(
            query=query,
            location=location
        ):
            if include_details:
                try:
                    details = await client.get_place_details(place['place_id'])
                    if details:
                        normalized = normalizer.normalize(details)
                        logger.debug(
                            f"Получены детали для {place.get('name')}: "
                            f"телефон={details.get('formatted_phone_number')}, "
                            f"сайт={details.get('website')}"
                        )
                    else:
                        logger.warning(
                            f"Не удалось получить детали для {place.get('name')} "
                            f"(ID: {place.get('place_id')})"
                        )
                        normalized = normalizer.normalize(place)
                except Exception as e:
                    logger.error(
                        f"Ошибка при получении деталей для "
                        f"{place.get('name')}: {e}"
                    )
                    normalized = normalizer.normalize(place)

                await asyncio.sleep(settings.google_places.request_delay)
            else:
                normalized = normalizer.normalize(place)

            if normalized.get('place_id'):
                page.append(normalized)
                if len(page) >= page_size:
                    logger.info(f"Отправляю страницу из {len(page)} мест")
                    yield page
                    total_yielded += len(page)
                    page = []
                    logger.info(
                        f"Отдана страница из {page_size} мест "
                        f"(всего: {total_yielded})"
                    )
                    await asyncio.sleep(0.1)
            else:
                logger.warning(
                    f"Пропущено место без place_id: {place.get('name')}"
                )

        if page:
            yield page
            total_yielded += len(page)
            logger.info(
                f"Отдана последняя страница из {len(page)} мест "
                f"(всего: {total_yielded})"
            )

