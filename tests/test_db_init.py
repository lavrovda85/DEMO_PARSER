#!/usr/bin/env python3
"""
Тест инициализации БД.
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, 'src')

async def test_db_init():
    """Тестируем инициализацию БД."""
    from src.main import init_database_schema

    print("🧪 Тестирование инициализации БД...")
    try:
        result = await init_database_schema()
        print(f"✅ Результат: {result}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_db_init())
