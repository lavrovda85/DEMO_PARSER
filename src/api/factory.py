"""
Фабричные функции для создания клиентов Google Places API.
"""

from .client import AsyncGooglePlacesAPI


def create_async_places_client(api_key: str) -> AsyncGooglePlacesAPI:
    """
    Создает асинхронный клиент Google Places API.

    Args:
        api_key: API ключ

    Returns:
        Настроенный клиент
    """
    return AsyncGooglePlacesAPI(api_key)

