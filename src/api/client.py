"""
Асинхронный клиент Google Places API.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Optional, AsyncGenerator

logger = logging.getLogger(__name__)


class AsyncGooglePlacesAPI:
    """
    Асинхронная версия клиента Google Places API.

    Поддерживает постраничную загрузку данных для высокой
    производительности.
    """

    BASE_URL = "https://maps.googleapis.com/maps/api/place"

    def __init__(
        self,
        api_key: str,
        session: Optional[aiohttp.ClientSession] = None
    ):
        """
        Инициализирует асинхронный клиент Google Places API.

        Args:
            api_key: API ключ для доступа к Google Places API
            session: Существующая aiohttp сессия (опционально)
        """
        self.api_key = api_key
        self.session = session

    async def __aenter__(self):
        """Контекстный менеджер - вход."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - выход."""
        if (self.session and
                self.session is not self.session._connector_owner):
            await self.session.close()

    async def search_places_paginated(
        self,
        query: str,
        location: Optional[str] = None
    ) -> AsyncGenerator[Dict, None]:
        """
        Выполняет постраничный поиск мест.

        Args:
            query: Текстовый запрос для поиска
            location: Локация для поиска

        Yields:
            Словарь с данными места
        """
        from src.config import settings

        page_token = None
        total_yielded = 0
        radius = settings.google_places.radius
        max_results = settings.google_places.max_results

        if not page_token:
            await asyncio.sleep(settings.google_places.initial_delay)

        while total_yielded < max_results:
            remaining = max_results - total_yielded
            page_size = min(20, remaining)

            places_data = await self._search_places_single_page(
                query=query,
                location=location,
                radius=radius,
                page_token=page_token,
                max_results=page_size
            )

            if not places_data.get('results'):
                break

            for place in places_data['results']:
                if total_yielded >= max_results:
                    break
                yield place
                total_yielded += 1

            page_token = places_data.get('next_page_token')
            if not page_token:
                break

            await asyncio.sleep(settings.google_places.request_delay)

    async def _search_places_single_page(
        self,
        query: str,
        location: Optional[str] = None,
        radius: int = 5000,
        page_token: Optional[str] = None,
        # Используется для ограничения размера страницы
        max_results: int = 20
    ) -> Dict:
        """
        Выполняет поиск на одной странице.

        Args:
            query: Текстовый запрос
            location: Локация
            radius: Радиус
            page_token: Токен следующей страницы
            max_results: Количество результатов на странице

        Returns:
            Ответ API в формате JSON
        """
        url = f"{self.BASE_URL}/textsearch/json"

        params = {
            'key': self.api_key,
            'query': query
        }

        if location and not page_token:
            params['location'] = location
            params['radius'] = radius

        if page_token:
            params['pagetoken'] = page_token

        if not self.session:
            async with aiohttp.ClientSession() as session:
                return await self._make_request(session, url, params)
        else:
            return await self._make_request(self.session, url, params)

    async def _make_request(
        self,
        session: aiohttp.ClientSession,
        url: str,
        params: Dict
    ) -> Dict:
        """
        Выполняет HTTP запрос к API.

        Args:
            session: aiohttp сессия
            url: URL для запроса
            params: Параметры запроса

        Returns:
            JSON ответ
        """
        async with session.get(url, params=params) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(
                    f"API request failed: {response.status} - {error_text}"
                )

            data = await response.json()

            if data.get('status') != 'OK':
                raise Exception(
                    f"API returned error status: {data.get('status')}"
                )

            return data

    async def get_place_details(self, place_id: str) -> Optional[Dict]:
        """
        Получает детальную информацию о месте по place_id.

        Args:
            place_id: Google Places ID места

        Returns:
            Детальная информация о месте или None
        """
        url = f"{self.BASE_URL}/details/json"

        params = {
            'key': self.api_key,
            'place_id': place_id,
            'fields': (
                'place_id,name,formatted_address,'
                'formatted_phone_number,website,opening_hours'
            )
        }

        if not self.session:
            async with aiohttp.ClientSession() as session:
                data = await self._make_request(session, url, params)
        else:
            data = await self._make_request(self.session, url, params)

        return data.get('result')

