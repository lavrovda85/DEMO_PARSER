"""
Асинхронный менеджер для работы с PostgreSQL.
"""

import asyncpg
import logging
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from src.config import settings
from .queries import CHECK_STORE_EXISTS, UPDATE_STORE, INSERT_STORE

logger = logging.getLogger(__name__)


class AsyncDatabaseManager:
    """
    Асинхронный менеджер для работы с PostgreSQL через asyncpg.

    Оптимизирован для высокой производительности в асинхронных
    приложениях.
    """

    def __init__(self):
        """Инициализирует асинхронный менеджер базы данных."""
        self.connection_string = settings.database.connection_string
        self.pool: Optional[asyncpg.Pool] = None

    async def init_pool(self) -> None:
        """Инициализирует пул соединений."""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=settings.database.min_size,
                max_size=settings.database.max_size,
                command_timeout=settings.database.command_timeout,
                max_inactive_connection_lifetime=(
                    settings.database.max_inactive_connection_lifetime
                )
            )
            min_size = settings.database.min_size
            max_size = settings.database.max_size
            logger.info(
                f"Пул соединений инициализирован "
                f"(min: {min_size}, max: {max_size})"
            )
        except Exception as e:
            logger.error(f"Ошибка при инициализации пула соединений: {e}")
            raise

    async def close_pool(self) -> None:
        """Закрывает пул соединений."""
        if self.pool:
            await self.pool.close()
            logger.info("Пул соединений закрыт")

    @asynccontextmanager
    async def get_connection(self):
        """
        Асинхронный контекстный менеджер для получения соединения.

        Yields:
            asyncpg.Connection: Соединение с базой данных
        """
        if not self.pool:
            raise RuntimeError(
                "Пул соединений не инициализирован. "
                "Вызовите init_pool() сначала."
            )

        conn = None
        try:
            conn = await self.pool.acquire()
            yield conn
        except Exception as e:
            logger.error(f"Ошибка при работе с соединением: {e}")
            raise
        finally:
            if conn:
                await self.pool.release(conn)

    async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """
        Выполняет SELECT запрос и возвращает результаты.

        Args:
            query: SQL запрос
            *args: Параметры запроса

        Returns:
            Список словарей с результатами
        """
        async with self.get_connection() as conn:
            try:
                records = await conn.fetch(query, *args)
                return [dict(record) for record in records]
            except Exception as e:
                logger.error(f"Ошибка при выполнении запроса: {e}")
                raise

    async def execute_command(self, command: str, *args) -> str:
        """
        Выполняет команду (INSERT, UPDATE, DELETE) и возвращает статус.

        Args:
            command: SQL команда
            *args: Параметры команды

        Returns:
            Статус выполнения
        """
        async with self.get_connection() as conn:
            try:
                status = await conn.execute(command, *args)
                return status
            except Exception as e:
                logger.error(f"Ошибка при выполнении команды: {e}")
                raise

    async def check_store_exists(self, place_id: str) -> bool:
        """
        Проверяет существование магазина по place_id.

        Args:
            place_id: Google Places ID магазина

        Returns:
            True если магазин существует
        """
        results = await self.execute_query(CHECK_STORE_EXISTS, place_id)
        return len(results) > 0

    async def upsert_store(self, store_data: Dict[str, Any]) -> str:
        """
        Вставляет или обновляет данные магазина.

        Args:
            store_data: Данные магазина

        Returns:
            Статус операции
        """
        exists = await self.check_store_exists(store_data['place_id'])

        if exists:
            params = (
                store_data['place_id'],
                store_data.get('name', ''),
                store_data.get('website'),
                store_data.get('phone'),
                store_data.get('address'),
                store_data.get('description')
            )
            return await self.execute_command(UPDATE_STORE, *params)
        else:
            params = (
                store_data.get('name', ''),
                store_data.get('website'),
                store_data.get('phone'),
                store_data.get('address'),
                store_data['place_id'],
                store_data.get('description')
            )
            return await self.execute_command(INSERT_STORE, *params)


# Глобальный экземпляр асинхронного менеджера
async_db_manager = AsyncDatabaseManager()

