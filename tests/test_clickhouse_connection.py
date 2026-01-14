#!/usr/bin/env python3
"""
Простой тест подключения к ClickHouse.
"""

import asyncio
from clickhouse_driver import Client

async def test_connection():
    """Тест подключения к ClickHouse."""
    try:
        print("Подключаемся к ClickHouse...")
        client = Client(
            host='localhost',
            port=9000,
            database='places_db',
            user='places_user',
            password='places_password'
        )

        # Проверяем соединение
        result = client.execute('SELECT 1')
        print(f"✅ Подключение успешно! Результат: {result}")

        client.disconnect()

    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
