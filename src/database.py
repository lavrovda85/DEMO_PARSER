"""
Модуль для работы с базой данных PostgreSQL.

Предоставляет функции для создания подключения, инициализации схемы
и управления сессиями базы данных.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from typing import Generator
import logging

from src.config import settings
from src.models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Менеджер для управления подключениями к базе данных."""
    
    def __init__(self, connection_string: str):
        """
        Инициализирует менеджер базы данных.
        
        Args:
            connection_string: Строка подключения к PostgreSQL.
        """
        self.connection_string = connection_string
        self.engine = create_engine(
            connection_string,
            poolclass=NullPool,
            echo=False,
            connect_args={"connect_timeout": 10}
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def init_db(self) -> None:
        """
        Инициализирует схему базы данных.
        
        Создает все таблицы, определенные в моделях.
        """
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("База данных успешно инициализирована")
        except Exception as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Контекстный менеджер для получения сессии базы данных.
        
        Yields:
            Session: Сессия SQLAlchemy.
            
        Example:
            with db_manager.get_session() as session:
                # Работа с базой данных
                pass
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка в сессии базы данных: {e}")
            raise
        finally:
            session.close()
    
    def close(self) -> None:
        """Закрывает все подключения к базе данных."""
        self.engine.dispose()
        logger.info("Подключения к базе данных закрыты")


# Глобальный экземпляр менеджера базы данных
db_manager = DatabaseManager(settings.database.connection_string)

