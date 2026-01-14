"""
Модуль для работы с Google Places API.

Предоставляет асинхронный клиент и функции для поиска мест.
"""

from .client import AsyncGooglePlacesAPI
from .factory import create_async_places_client
from .search import search_all_places_async, stream_places_async

__all__ = [
    'AsyncGooglePlacesAPI',
    'create_async_places_client',
    'search_all_places_async',
    'stream_places_async'
]

