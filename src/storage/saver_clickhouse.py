"""
Компонент сохранения данных в ClickHouse Data Vault.
"""

import asyncio
import logging
from typing import Dict, Any
from src.database.clickhouse import ClickHouseDataVaultClient
from ..pipeline.base import ETLStep, PipelineContext

logger = logging.getLogger(__name__)


class ClickHouseDataSaver(ETLStep):
    """
    Компонент для асинхронного сохранения данных магазинов в ClickHouse Data Vault.

    Использует ClickHouse Data Vault архитектуру для хранения данных
    в нормализованном виде с поддержкой расширяемых полей.
    """

    def __init__(self):
        """
        Инициализирует компонент сохранения.
        """
        from ..config import settings
        super().__init__("ClickHouse Data Saving")
        self.client = ClickHouseDataVaultClient(
            host="clickhouse",  # временно хардкодим для Docker
            port=settings.database.port,
            database=settings.database.db,
            user=settings.database.user,
            password=settings.database.password
        )
        self.max_concurrent_writes = settings.pipeline.max_concurrent_db_writes
        self.semaphore = asyncio.Semaphore(self.max_concurrent_writes)

    async def execute(self, context: PipelineContext) -> None:
        """
        Асинхронно сохраняет данные магазинов в ClickHouse Data Vault.

        Args:
            context: Контекст выполнения pipeline
        """
        self.logger.info(f"Начинаем сохранение. Данных для сохранения: {len(context.transformed_data) if context.transformed_data else 0}")

        if not context.transformed_data:
            self.logger.warning("Нет данных для сохранения")
            return

        # Логируем первые несколько записей для отладки
        for i, store in enumerate(context.transformed_data[:3]):
            self.logger.debug(f"Запись {i+1}: place_id={store.get('place_id')}, name={store.get('name', 'N/A')}")

        # Инициализируем клиента, если нужно
        if self.client.client is None:
            try:
                await self.client.init_pool()
            except Exception as e:
                self.logger.warning(f"ClickHouse недоступен, сохранение пропущено: {e}")
                return

        try:
            # Сохраняем данные последовательно из-за ограничений ClickHouse драйвера
            # (одновременные запросы на одном соединении вызывают ошибки)
            results = []
            self.logger.info(f"Начинаем последовательное сохранение {len(context.transformed_data)} записей")

            for store_data in context.transformed_data:
                try:
                    result = await self._save_single_store(store_data)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Исключение при сохранении: {e}")
                    results.append(e)

            # Подсчитываем успешные сохранения
            successful_saves = 0
            for i, result in enumerate(results):
                store_name = context.transformed_data[i].get('name', f'index_{i}') if i < len(context.transformed_data) else f'index_{i}'

                self.logger.info(f"Результат {i+1} ({store_name}): type={type(result)}, value={repr(result)}")

                if isinstance(result, Exception):
                    self.logger.error(f"❌ Исключение при сохранении {store_name}: {result}")
                elif result is None:
                    self.logger.debug(f"⏭️  Пропущено {store_name}")
                elif result == "skipped":
                    self.logger.debug(f"⏭️  Пропущено {store_name}")
                else:
                    successful_saves += 1
                    self.logger.info(f"✅ Успешно сохранен {store_name}")

            self.logger.info(f"📊 Итого: обработано {len(results)}, успешно {successful_saves}")

            context.saved_count = successful_saves

            self.logger.info(
                f"Сохранение в ClickHouse завершено. "
                f"Сохранено: {successful_saves}/{len(context.transformed_data)} "
                f"(последовательно)"
            )

        except Exception as e:
            self.logger.error(f"Ошибка при сохранении данных в ClickHouse: {e}")
            raise

    async def _save_single_store(self, store_data: Dict[str, Any]) -> str:
        """
        Асинхронно сохраняет данные одного магазина в Data Vault.

        Args:
            store_data: Данные магазина для сохранения

        Returns:
            Статус операции или None при ошибке
        """
        if store_data is None:
            self.logger.debug("Пропускаем сохранение пустой записи")
            return None

        if not isinstance(store_data, dict):
            self.logger.error(f"Некорректный тип данных: {type(store_data)}, пропускаем")
            return None

        place_id = store_data.get("place_id")
        store_name = store_data.get('name', 'Unknown')

        self.logger.info(f"Сохраняем магазин '{store_name}' с place_id: {place_id}")

        if not place_id:
            self.logger.error(f"Place ID обязателен для сохранения магазина '{store_name}'")
            return None

        try:
            # Сохраняем в Data Vault
            status = await self.client.upsert_store(store_data)

            # Отмечаем как успешно обработанный
            if place_id:
                await self.client.mark_place_processed(place_id, "success")

            store_name = store_data.get('name', 'Unknown')
            self.logger.debug(f"Магазин '{store_name}' сохранен в Data Vault")
            return status

        except Exception as e:
            store_name = store_data.get('name', 'Unknown')
            self.logger.error(f"Ошибка сохранения магазина {store_name}: {e}")

            # Логируем ошибку в ClickHouse
            try:
                await self.client.log_processing_error(
                    place_id, "save_error", str(e)
                )
            except Exception:
                pass  # Игнорируем ошибки логирования

            raise


if __name__ == "__main__":  # noqa
    import asyncio

    async def test_clickhouse_saver():
        """Тест ClickHouseDataSaver."""
        saver = ClickHouseDataSaver()

        # Проверяем инициализацию
        assert saver.max_concurrent_writes > 0
        assert isinstance(saver.semaphore, asyncio.Semaphore)
        assert isinstance(saver.client, ClickHouseDataVaultClient)

        print("[OK] ClickHouseDataSaver инициализация тест пройден")

        # Тест подключения к ClickHouse (если доступен)
        try:
            await saver.client.init_pool()
            print("[OK] ClickHouse подключение успешно")
            await saver.client.close_pool()
        except Exception as e:
            print(f"[WARN] ClickHouse недоступен: {e}")

    asyncio.run(test_clickhouse_saver())
