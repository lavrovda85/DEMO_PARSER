"""
Тесты для ETL pipeline компонентов.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.pipeline import PipelineContext
from src.pipeline.fetcher import DataFetcher
from src.pipeline.enricher import DataEnricher
from src.storage.saver import DataSaver


class TestPipelineContext:
    """Тесты для PipelineContext."""

    def test_context_creation(self):
        """Тест создания контекста pipeline."""
        context = PipelineContext(
            api_key="test_key",
            search_region="Test City",
            search_category="Test Stores",
            postal_code="12345",
            max_results=10,
            enrich_data=True
        )

        assert context.api_key == "test_key"
        assert context.search_region == "Test City"
        assert context.search_category == "Test Stores"
        assert context.postal_code == "12345"
        assert context.max_results == 10
        assert context.enrich_data is True
        assert context.extracted_data == []
        assert context.transformed_data == []
        assert context.saved_count == 0
        assert context.enriched_count == 0


class TestDataFetcher:
    """Тесты для DataFetcher."""

class TestDataFetcher:
    """Тесты для DataFetcher."""

    @pytest.fixture
    def fetcher(self):
        """Создает экземпляр DataFetcher."""
        return DataFetcher()

    @pytest.mark.asyncio
    async def test_successful_fetch(self, fetcher):
        """Тест успешного извлечения данных."""
        context = PipelineContext(
            api_key="test_key",
            search_region="Test City",
            search_category="Test Stores",
            max_results=10
        )

        # Мокаем асинхронную функцию поиска
        test_data = [
            {"place_id": "test_1", "name": "Store 1"},
            {"place_id": "test_2", "name": "Store 2"}
        ]

        with patch('src.pipeline.fetcher.search_all_places_async', return_value=test_data):
            await fetcher.execute(context)

            assert len(context.extracted_data) == 2
            assert context.extracted_data[0]["place_id"] == "test_1"
            assert context.extracted_data[1]["place_id"] == "test_2"


class TestDataEnricher:
    """Тесты для DataEnricher."""

    @pytest.fixture
    def enricher(self):
        """Создает экземпляр DataEnricher."""
        return DataEnricher(max_concurrent_requests=2)

    @pytest.mark.asyncio
    async def test_enrichment_disabled(self, enricher):
        """Тест когда обогащение отключено."""
        context = PipelineContext(
            api_key="test_key",
            search_region="Test City",
            search_category="Test Stores",
            enrich_data=False
        )
        context.extracted_data = [{"name": "Test Store", "place_id": "test_1"}]

        await enricher.execute(context)

        assert context.transformed_data == [{"name": "Test Store", "place_id": "test_1"}]
        assert context.enriched_count == 0

    @pytest.mark.asyncio
    async def test_enrichment_enabled(self, enricher):
        """Тест когда обогащение включено."""
        with patch('src.pipeline.enricher.BrowserManager') as mock_bm_class:
            mock_bm = AsyncMock()
            mock_bm_class.return_value.__aenter__ = AsyncMock(return_value=mock_bm)
            mock_bm_class.return_value.__aexit__ = AsyncMock()

            mock_extractor = AsyncMock()
            mock_extractor.extract_description.return_value = "Test description"

            with patch('src.pipeline.enricher.DataExtractor', return_value=mock_extractor):
                context = PipelineContext(
                    api_key="test_key",
                    search_region="Test City",
                    search_category="Test Stores",
                    enrich_data=True
                )
                context.extracted_data = [
                    {"name": "Test Store", "place_id": "test_1", "website": "http://test.com"}
                ]

                await enricher.execute(context)

                assert len(context.transformed_data) == 1
                assert context.transformed_data[0]["description"] == "Test description"
                assert context.enriched_count == 1


class TestDataSaver:
    """Тесты для DataSaver."""

    @pytest.fixture
    def saver(self):
        """Создает экземпляр DataSaver."""
        return DataSaver(max_concurrent_writes=2)

    @pytest.mark.asyncio
    async def test_save_data(self, saver):
        """Тест сохранения данных."""
        with patch('src.storage.saver.async_db_manager') as mock_async_db:
            # Мокаем пул соединений
            mock_async_db.pool = None
            mock_async_db.init_pool = AsyncMock()
            mock_async_db.upsert_store = AsyncMock(return_value="INSERT")

            context = PipelineContext(
                api_key="test_key",
                search_region="Test City",
                search_category="Test Stores"
            )
            context.transformed_data = [
                {
                    "name": "Test Store",
                    "place_id": "test_1",
                    "website": "http://test.com",
                    "address": "Test Address",
                    "phone": "123-456",
                    "description": "Test description"
                }
            ]

            await saver.execute(context)

            assert context.saved_count == 1
            mock_async_db.init_pool.assert_called_once()
            mock_async_db.upsert_store.assert_called_once()
