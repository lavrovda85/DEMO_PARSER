"""
Модуль нормализации данных Google Places API.
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class PlaceDataNormalizer:
    """
    Класс для нормализации данных мест из Google Places API.
    """

    @staticmethod
    def normalize(place: Dict) -> Dict:
        """
        Нормализует данные места из Google Places API.

        Args:
            place: Данные места из API

        Returns:
            Нормализованный словарь с данными
        """
        normalized = {
            'place_id': place.get('place_id'),
            'name': place.get('name'),
            'address': place.get('formatted_address'),
            'phone': place.get('formatted_phone_number'),
            'website': place.get('website'),
            'location': place.get('geometry', {}).get('location'),
            'rating': place.get('rating'),
            'user_ratings_total': place.get('user_ratings_total'),
            'types': place.get('types', []),
            'price_level': place.get('price_level'),
            'opening_hours': place.get('opening_hours')
        }

        place_id = normalized.get('place_id')
        if not place_id:
            logger.warning(
                f"normalize_place_data: place_id отсутствует. "
                f"Данные: {place}"
            )

        return normalized

