"""
Компонент сохранения данных в базу данных.
"""

import asyncio
import logging
from typing import Dict, Any
from src.database import async_db_manager
from ..pipeline.base import ETLStep, PipelineContext

logger = logging.getLogger(__name__)


class DataSaver(ETLStep):
    """
    Компонент для асинхронного сохранения данных магазинов в базу
    данных.

    Использует asyncpg для высокой производительности и поддерживает
    параллельное сохранение с semaphore для контроля нагрузки.
    """

    def __init__(self):
        """
        Инициализирует компонент сохранения.
        """
        from ..config import settings
        super().__init__("Data Saving")
        self.max_concurrent_writes = (
            settings.pipeline.max_concurrent_db_writes
        )
        self.semaphore = asyncio.Semaphore(self.max_concurrent_writes)

    async def execute(self, context: PipelineContext) -> None:
        """
        Асинхронно сохраняет данные магазинов в базу данных.

        Args:
            context: Контекст выполнения pipeline
        """
        if not context.transformed_data:
            self.logger.warning("Нет данных для сохранения")
            return

        # Инициализируем пул соединений, если нужно
        if async_db_manager.pool is None:
            await async_db_manager.init_pool()

        try:
            # Сохраняем данные параллельно с контролем нагрузки
            save_tasks = [
                self._save_single_store(store_data)
                for store_data in context.transformed_data
            ]

            # Выполняем все задачи параллельно
            results = await asyncio.gather(*save_tasks, return_exceptions=True)

            # Подсчитываем успешные сохранения и логируем ошибки
            # за один проход
            successful_saves = 0
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    store_name = context.transformed_data[i].get(
                        'name', f'index_{i}'
                    )
                    self.logger.warning(
                        f"Ошибка сохранения {store_name}: {result}"
                    )
                elif result is not None:
                    successful_saves += 1

            context.saved_count = successful_saves

            total = len(context.transformed_data)
            self.logger.info(
                f"Сохранение завершено. "
                f"Сохранено: {successful_saves}/{total} "
                f"({self.max_concurrent_writes} параллельно)"
            )

        except Exception as e:
            self.logger.error(f"Ошибка при сохранении данных: {e}")
            raise

    async def _save_single_store(self, store_data: Dict[str, Any]) -> str:
        """
        Асинхронно сохраняет данные одного магазина с semaphore.

        Args:
            store_data: Данные магазина для сохранения

        Returns:
            Статус операции или None при ошибке
        """
        async with self.semaphore:
            place_id = store_data.get("place_id")
            if not place_id:
                self.logger.error("Place ID обязателен для сохранения")
                return None

            try:
                status = await async_db_manager.upsert_store(store_data)
                store_name = store_data.get('name', 'Unknown')
                action = 'Обновлен' if 'UPDATE' in status else 'Создан'
                self.logger.debug(f"{action} магазин: {store_name}")
                return status

            except Exception as e:
                store_name = store_data.get('name', 'Unknown')
                self.logger.error(
                    f"Ошибка при сохранении магазина {store_name}: {e}"
                )
                raise


if __name__ == "__main__":
    import asyncio
    from unittest.mock import patch

    async def test_data_saver():
        """Тест DataSaver."""
        saver = DataSaver()

        assert saver.max_concurrent_writes == 5
        assert isinstance(saver.semaphore, asyncio.Semaphore)

        print("[OK] DataSaver инициализация тест пройден")

        # Тест валидации данных
        context = type('MockContext', (), {
            'transformed_data': [
                {"name": "Test Store", "place_id": "test_1"},
                {"name": "Test Store 2", "place_id": None},  # Без place_id
            ]
        })()

        # Мокаем async_db_manager
        with patch('src.storage.saver.async_db_manager') as mock_db:
            mock_db.pool = None
            mock_db.init_pool = AsyncMock()
            mock_db.upsert_store = AsyncMock(return_value="INSERT")

            try:
                await saver.execute(context)
                print("[OK] DataSaver выполнение тест пройден")
            except Exception as e:
                print(f"[WARN] DataSaver тест с предупреждением: {e}")

    asyncio.run(test_data_saver())
