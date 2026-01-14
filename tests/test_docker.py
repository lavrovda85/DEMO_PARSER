#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы системы в Docker контейнере.
"""

import sys
import asyncio
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, '/app/src')

async def test_system():
    """Тестирование основных компонентов системы."""
    print("🧪 Тестирование системы v3.0...")

    try:
        # Тест импортов
        from src.config import settings
        print("✅ Конфигурация загружена")

        from src.api import create_async_places_client
        print("✅ API клиент импортирован")

        from src.database.clickhouse import ClickHouseDataVaultClient
        print("✅ ClickHouse клиент импортирован")

        from src.extraction.templates import ExtractionTemplates
        templates = ExtractionTemplates.get_available_fields()
        print(f"✅ Шаблоны загружены: {templates}")

        from src.pipeline import PipelineOrchestrator
        print("✅ Pipeline оркестратор импортирован")

        # Тест создания ClickHouse клиента (без подключения для Docker теста)
        ch_client = ClickHouseDataVaultClient()
        print("✅ ClickHouse клиент создан")

        # Проверяем методы клиента
        assert hasattr(ch_client, 'upsert_store')
        assert hasattr(ch_client, 'check_store_exists')
        print("✅ Методы ClickHouse клиента доступны")

        print("\\n🎉 Все тесты пройдены! Система готова к работе.")
        return True

    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_system())
    sys.exit(0 if success else 1)
