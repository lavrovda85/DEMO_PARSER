"""
Модульные тесты для Google Places API клиента.

Проверяет корректность работы методов поиска и получения деталей мест.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.places_api import GooglePlacesAPI


class TestGooglePlacesAPI:
    """Тесты для класса GooglePlacesAPI."""
    
    @pytest.fixture
    def api_client(self):
        """Создает экземпляр API клиента для тестов."""
        return GooglePlacesAPI(api_key="test_api_key")
    
    def test_init(self, api_client):
        """Тест инициализации API клиента."""
        assert api_client.api_key == "test_api_key"
        assert api_client.BASE_URL == "https://maps.googleapis.com/maps/api/place"
    
    def test_search_places_empty_query(self, api_client):
        """Тест обработки пустого запроса."""
        with pytest.raises(ValueError, match="query не может быть пустым"):
            api_client.search_places("")
    
    @patch('src.places_api.requests.get')
    def test_search_places_success(self, mock_get, api_client):
        """Тест успешного поиска мест."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "OK",
            "results": [
                {
                    "place_id": "test_place_id_1",
                    "name": "Test Store 1",
                    "formatted_address": "123 Test St"
                },
                {
                    "place_id": "test_place_id_2",
                    "name": "Test Store 2",
                    "formatted_address": "456 Test Ave"
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        results = api_client.search_places("Women's Clothing Store", location="Byron Bay")
        
        assert len(results) == 2
        assert results[0]["place_id"] == "test_place_id_1"
        assert results[1]["name"] == "Test Store 2"
    
    @patch('src.places_api.requests.get')
    def test_search_places_api_error(self, mock_get, api_client):
        """Тест обработки ошибки API."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "REQUEST_DENIED",
            "error_message": "API key invalid"
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        with pytest.raises(ValueError, match="Доступ запрещен"):
            api_client.search_places("test query")
    
    def test_get_place_details_empty_id(self, api_client):
        """Тест обработки пустого Place ID."""
        with pytest.raises(ValueError, match="Place ID не может быть пустым"):
            api_client.get_place_details("")
    
    @patch('src.places_api.requests.get')
    def test_get_place_details_success(self, mock_get, api_client):
        """Тест успешного получения деталей места."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "OK",
            "result": {
                "place_id": "test_place_id",
                "name": "Test Store",
                "website": "https://teststore.com",
                "formatted_phone_number": "+61 2 1234 5678",
                "formatted_address": "123 Test St, Byron Bay"
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = api_client.get_place_details("test_place_id")
        
        assert result is not None
        assert result["name"] == "Test Store"
        assert result["website"] == "https://teststore.com"
    
    def test_normalize_place_data(self, api_client):
        """Тест нормализации данных места."""
        place_data = {
            "place_id": "test_place_id",
            "name": "Test Store",
            "formatted_address": "123 Test St"
        }
        
        with patch.object(api_client, 'get_place_details', return_value=None):
            normalized = api_client.normalize_place_data(place_data)
            assert normalized["place_id"] == "test_place_id"
            assert normalized["name"] == "Test Store"

