"""
Модуль для работы с Google Places API.

Предоставляет функции для поиска магазинов и получения детальной информации
о местах через Google Places API.
"""

import requests
import logging
from typing import List, Dict, Optional
from time import sleep

from src.config import settings

logger = logging.getLogger(__name__)


class GooglePlacesAPI:
    """
    Класс для взаимодействия с Google Places API.
    
    Предоставляет методы для поиска мест и получения детальной информации.
    """
    
    BASE_URL = "https://maps.googleapis.com/maps/api/place"
    
    def __init__(self, api_key: str):
        """
        Инициализирует клиент Google Places API.
        
        Args:
            api_key: API ключ для доступа к Google Places API.
        """
        self.api_key = api_key
    
    def search_places(
        self,
        query: str,
        location: Optional[str] = None,
        radius: int = 5000,
        max_results: int = 60
    ) -> List[Dict]:
        """
        Выполняет поиск мест по текстовому запросу.
        
        Args:
            query: Текстовый запрос для поиска (например, "Women's Clothing Store").
            location: Локация для поиска (например, "Byron Bay, NSW, Australia").
            radius: Радиус поиска в метрах (максимум 50000).
            max_results: Максимальное количество результатов для возврата.
            
        Returns:
            Список словарей с информацией о найденных местах.
            
        Raises:
            requests.RequestException: При ошибке HTTP запроса.
            ValueError: При неверных параметрах запроса.
        """
        if not query:
            raise ValueError("Параметр query не может быть пустым")
        
        all_results = []
        next_page_token = None
        request_count = 0
        max_requests = 3  # Ограничение Google API для Text Search
        
        try:
            while len(all_results) < max_results and request_count < max_requests:
                params = {
                    "query": f"{query} in {location}" if location else query,
                    "key": self.api_key,
                    "type": "clothing_store"  # Более специфичный тип
                }
                
                if next_page_token:
                    params["pagetoken"] = next_page_token
                    sleep(2)  # Задержка для токена следующей страницы
                
                response = requests.get(
                    f"{self.BASE_URL}/textsearch/json",
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("status") != "OK" and data.get("status") != "ZERO_RESULTS":
                    error_message = data.get("error_message", "Неизвестная ошибка")
                    logger.error(f"Ошибка API: {data.get('status')} - {error_message}")
                    if data.get("status") == "REQUEST_DENIED":
                        raise ValueError(f"Доступ запрещен: {error_message}")
                    break
                
                results = data.get("results", [])
                all_results.extend(results)
                
                next_page_token = data.get("next_page_token")
                if not next_page_token:
                    break
                
                request_count += 1
                sleep(1)  # Задержка между запросами
            
            logger.info(f"Найдено мест: {len(all_results)}")
            return all_results[:max_results]
            
        except requests.RequestException as e:
            logger.error(f"Ошибка при запросе к Google Places API: {e}")
            raise
    
    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """
        Получает детальную информацию о месте по его Place ID.
        
        Args:
            place_id: Уникальный идентификатор места в Google Places.
            
        Returns:
            Словарь с детальной информацией о месте или None при ошибке.
            
        Raises:
            requests.RequestException: При ошибке HTTP запроса.
        """
        if not place_id:
            raise ValueError("Place ID не может быть пустым")
        
        try:
            params = {
                "place_id": place_id,
                "key": self.api_key,
                "fields": "name,website,formatted_phone_number,formatted_address,place_id"
            }
            
            response = requests.get(
                f"{self.BASE_URL}/details/json",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") != "OK":
                error_message = data.get("error_message", "Неизвестная ошибка")
                logger.warning(f"Ошибка при получении деталей места {place_id}: {data.get('status')} - {error_message}")
                return None
            
            return data.get("result")
            
        except requests.RequestException as e:
            logger.error(f"Ошибка при запросе деталей места {place_id}: {e}")
            return None
    
    def normalize_place_data(self, place_data: Dict) -> Dict:
        """
        Нормализует данные места для сохранения в базу данных.
        
        Args:
            place_data: Словарь с данными места из API.
            
        Returns:
            Нормализованный словарь с полями для базы данных.
        """
        # Если это результат из textsearch, используем его напрямую
        if "place_id" in place_data:
            # Получаем детальную информацию
            details = self.get_place_details(place_data["place_id"])
            if details:
                return {
                    "place_id": details.get("place_id", ""),
                    "name": details.get("name", ""),
                    "website": details.get("website"),
                    "phone": details.get("formatted_phone_number"),
                    "address": details.get("formatted_address"),
                }
        
        # Fallback на данные из textsearch
        return {
            "place_id": place_data.get("place_id", ""),
            "name": place_data.get("name", ""),
            "website": place_data.get("website"),
            "phone": place_data.get("formatted_phone_number"),
            "address": place_data.get("formatted_address") or place_data.get("vicinity", ""),
        }

