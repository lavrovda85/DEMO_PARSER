"""
Модульные тесты для компонентов извлечения данных.

Проверяет корректность извлечения описаний с веб-сайтов.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.extraction import BrowserManager, DataExtractor, ExtractionTemplates


class TestBrowserManager:
    """Тесты для BrowserManager."""

    @pytest.fixture
    def browser_manager(self):
        """Создает экземпляр менеджера браузера для тестов."""
        return BrowserManager(headless=True, timeout=30000)

    def test_init(self, browser_manager):
        """Тест инициализации менеджера браузера."""
        assert browser_manager.headless is True
        assert browser_manager.timeout == 30000
        assert browser_manager.browser is None

    @pytest.mark.asyncio
    async def test_browser_lifecycle(self, browser_manager):
        """Тест жизненного цикла браузера."""
        with patch('src.extraction.browser.launch') as mock_launch:
            mock_browser = AsyncMock()
            mock_launch.return_value = mock_browser

            # Тест запуска браузера
            await browser_manager.start_browser()
            assert browser_manager.browser == mock_browser
            mock_launch.assert_called_once()

            # Тест остановки браузера
            await browser_manager.stop_browser()
            assert browser_manager.browser is None
            mock_browser.close.assert_called_once()


class TestDataExtractor:
    """Тесты для DataExtractor."""

    @pytest.fixture
    def browser_manager(self):
        """Создает мок менеджера браузера."""
        return AsyncMock()

    @pytest.fixture
    def extractor(self, browser_manager):
        """Создает экземпляр экстрактора для тестов."""
        return DataExtractor(browser_manager)

    @pytest.mark.asyncio
    async def test_extract_invalid_url(self, extractor):
        """Тест обработки некорректного URL."""
        result = await extractor.extract_data("not-a-url")
        assert result is None

        result = await extractor.extract_data("")
        assert result is None

    @pytest.mark.asyncio
    async def test_extract_description_success(self, extractor, browser_manager):
        """Тест успешного извлечения описания."""
        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value="Test description")
        mock_page.close = AsyncMock()

        browser_manager.create_page = AsyncMock(return_value=mock_page)

        result = await extractor.extract_description("https://teststore.com")

        assert result == "Test description"
        mock_page.evaluate.assert_called_once()
        mock_page.close.assert_called_once()


class TestExtractionTemplates:
    """Тесты для ExtractionTemplates."""

    def test_get_description_extractor(self):
        """Тест получения шаблона извлечения описания."""
        template = ExtractionTemplates.get_description_extractor()
        assert isinstance(template, str)
        assert "meta[name=\"description\"]" in template
        assert "og:description" in template

    def test_get_extractor_by_type(self):
        """Тест получения шаблона по типу."""
        desc_template = ExtractionTemplates.get_extractor_by_type("description")
        assert isinstance(desc_template, str)

        # Тест неизвестного типа
        with pytest.raises(ValueError):
            ExtractionTemplates.get_extractor_by_type("unknown")

