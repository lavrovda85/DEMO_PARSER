#!/usr/bin/env python3
"""
Тест подключения к ClickHouse
"""
import asyncio
from src.database.clickhouse import ClickHouseDataVaultClient

async def test():
    client = ClickHouseDataVaultClient(
        host='clickhouse',
        port=9000,
        database='places_db',
        user='places_user',
        password='places_password'
    )
    try:
        await client.init_pool()
        print('✅ ClickHouse подключение успешно')

        # Проверяем количество записей
        result = await client.client.execute('SELECT count(*) FROM places_db.hub_stores')
        print(f'📊 Записей в hub_stores: {result[0][0]}')

        await client.close_pool()
    except Exception as e:
        print(f'❌ Ошибка: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
