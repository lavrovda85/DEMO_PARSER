#!/usr/bin/env python3
"""
Тестовый скрипт для проверки GooglePlacesParser.parse() метода.
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, 'src')

from src.main import GooglePlacesParser

async def test_parser():
    """Тестируем GooglePlacesParser.parse() метод."""
    print("🧪 Тестирование GooglePlacesParser.parse()...")

    # Создаем парсер
    parser = GooglePlacesParser()

    # Тестируем с параметрами
    result = await parser.parse(
        region="Moscow, Russia",
        category="Coffee Shop",
        max_results=5,
        enrich_data=False  # Без обогащения для быстрого теста
    )

    print(f"📊 Результат: {result}")

    if result['status'] == 'success':
        print("✅ Тест пройден!")
    else:
        print(f"❌ Тест не пройден: {result['message']}")

if __name__ == "__main__":
    asyncio.run(test_parser())
