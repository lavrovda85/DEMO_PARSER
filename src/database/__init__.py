"""
Модуль для работы с базой данных ClickHouse.

Предоставляет асинхронные функции для работы с ClickHouse Data Vault.
Совместимый интерфейс с предыдущей версией (async_db_manager).
"""

from .clickhouse import ClickHouseDataVaultClient

# Lazy инициализация для совместимости
_async_db_manager = None

def get_async_db_manager():
    """Получить глобальный экземпляр ClickHouse клиента."""
    global _async_db_manager
    if _async_db_manager is None:
        from ..config import settings
        _async_db_manager = ClickHouseDataVaultClient(
            host="clickhouse",  # для Docker
            port=settings.database.port,
            database=settings.database.db,
            user=settings.database.user,
            password=settings.database.password
        )
    return _async_db_manager

# Для совместимости - создаем прокси объект
class AsyncDBManagerProxy:
    """Прокси для отложенной инициализации ClickHouse клиента."""

    @property
    def pool(self):
        return get_async_db_manager().client

    async def init_pool(self):
        return await get_async_db_manager().init_pool()

    async def close_pool(self):
        return await get_async_db_manager().close_pool()

    async def upsert_store(self, *args, **kwargs):
        return await get_async_db_manager().upsert_store(*args, **kwargs)

    async def check_store_exists(self, *args, **kwargs):
        return await get_async_db_manager().check_store_exists(*args, **kwargs)

# Создаем прокси для совместимости
async_db_manager = AsyncDBManagerProxy()

__all__ = ['ClickHouseDataVaultClient', 'async_db_manager', 'get_async_db_manager']

