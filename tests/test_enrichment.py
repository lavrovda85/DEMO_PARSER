"""
Модульные тесты для модуля обогащения данных.

Проверяет корректность извлечения описаний с веб-сайтов.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.enrichment import WebsiteEnricher


class TestWebsiteEnricher:
    """Тесты для класса WebsiteEnricher."""
    
    @pytest.fixture
    def enricher(self):
        """Создает экземпляр обогатителя для тестов."""
        return WebsiteEnricher(headless=True, timeout=30000)
    
    def test_init(self, enricher):
        """Тест инициализации обогатителя."""
        assert enricher.headless is True
        assert enricher.timeout == 30000
    
    @pytest.mark.asyncio
    async def test_extract_description_invalid_url(self, enricher):
        """Тест обработки некорректного URL."""
        result = await enricher.extract_description("not-a-url")
        assert result is None
        
        result = await enricher.extract_description("")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_extract_description_success(self, enricher):
        """Тест успешного извлечения описания."""
        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value="Test description from website")
        mock_page.setUserAgent = AsyncMock()
        mock_page.goto = AsyncMock()
        
        mock_browser = AsyncMock()
        mock_browser.newPage = AsyncMock(return_value=mock_page)
        mock_browser.close = AsyncMock()
        
        with patch('src.enrichment.launch', return_value=mock_browser):
            with patch('src.enrichment.stealth', return_value=AsyncMock()):
                result = await enricher.extract_description("https://teststore.com")
                
                assert result == "Test description from website"
                mock_page.goto.assert_called_once()
                mock_browser.close.assert_called_once()
    
    def test_extract_description_sync(self, enricher):
        """Тест синхронной обертки для извлечения описания."""
        with patch.object(enricher, 'extract_description', return_value=AsyncMock(return_value="Test")):
            # Мокируем asyncio.run
            with patch('asyncio.get_event_loop') as mock_loop:
                mock_loop.return_value.run_until_complete = MagicMock(return_value="Test description")
                result = enricher.extract_description_sync("https://teststore.com")
                assert result == "Test description"

