"""
ClickHouse Data Vault база данных.

Предоставляет асинхронный клиент для работы с ClickHouse
в архитектуре Data Vault.
"""

from .client import ClickHouseDataVaultClient
from .schema import get_init_queries

__all__ = ['ClickHouseDataVaultClient', 'get_init_queries']
