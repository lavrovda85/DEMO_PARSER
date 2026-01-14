"""
Модели данных для хранения информации о магазинах.

Определяет структуру таблиц в базе данных PostgreSQL с использованием SQLAlchemy ORM.
"""

from sqlalchemy import Column, String, Text, DateTime, Index
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()


def _get_utc_now() -> datetime:
    """
    Возвращает текущее время в UTC.
    
    Returns:
        datetime: Текущее время с timezone UTC.
    """
    return datetime.now(timezone.utc)


class Store(Base):
    """
    Модель для хранения информации о розничных магазинах.
    
    Атрибуты:
        id: Первичный ключ (автоматически генерируется).
        name: Название магазина.
        website: URL веб-сайта магазина.
        phone: Номер телефона.
        address: Полный адрес магазина.
        place_id: Уникальный идентификатор Google Places.
        description: Описание магазина, полученное при обогащении данных.
        created_at: Дата и время создания записи.
        updated_at: Дата и время последнего обновления записи.
    """
    
    __tablename__ = "stores"
    
    id = Column(String(255), primary_key=True)
    name = Column(String(500), nullable=False, index=True)
    website = Column(String(1000), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    place_id = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_get_utc_now, onupdate=_get_utc_now, nullable=False)
    
    # Индексы для оптимизации запросов
    __table_args__ = (
        Index('idx_store_name', 'name'),
        Index('idx_store_place_id', 'place_id'),
    )
    
    def __repr__(self) -> str:
        """Строковое представление объекта."""
        return f"<Store(name='{self.name}', place_id='{self.place_id}')>"

