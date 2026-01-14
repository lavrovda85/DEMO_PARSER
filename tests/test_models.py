"""
Модульные тесты для моделей данных.

Проверяет корректность определения моделей и их атрибутов.
"""

import pytest
from datetime import datetime
from src.models import Store, Base


class TestStore:
    """Тесты для модели Store."""
    
    def test_store_creation(self):
        """Тест создания экземпляра Store."""
        store = Store(
            id="test-id-123",
            name="Test Store",
            website="https://teststore.com",
            phone="+61 2 1234 5678",
            address="123 Test St, Byron Bay",
            place_id="test_place_id_123",
            description="Test description"
        )
        
        assert store.id == "test-id-123"
        assert store.name == "Test Store"
        assert store.website == "https://teststore.com"
        assert store.phone == "+61 2 1234 5678"
        assert store.address == "123 Test St, Byron Bay"
        assert store.place_id == "test_place_id_123"
        assert store.description == "Test description"
        assert isinstance(store.created_at, datetime)
    
    def test_store_repr(self):
        """Тест строкового представления Store."""
        store = Store(
            id="test-id",
            name="Test Store",
            place_id="test_place_id"
        )
        
        repr_str = repr(store)
        assert "Test Store" in repr_str
        assert "test_place_id" in repr_str
    
    def test_store_table_name(self):
        """Тест имени таблицы."""
        assert Store.__tablename__ == "stores"
    
    def test_store_indexes(self):
        """Тест наличия индексов."""
        table_args = Store.__table_args__
        assert table_args is not None

