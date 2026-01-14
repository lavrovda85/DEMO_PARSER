"""
Компонент обогащения данных через веб-сайты.
"""

import asyncio
import logging
from typing import Dict, Any
from src.extraction import BrowserManager, DataExtractor
from ..pipeline.base import ETLStep, PipelineContext

logger = logging.getLogger(__name__)


class DataEnricher(ETLStep):
    """
    Компонент для обогащения данных магазинов информацией с
    веб-сайтов.

    Использует браузер для извлечения описаний и другой информации.
    """

    def __init__(self):
        """
        Инициализирует компонент обогащения.
        """
        from ..config import settings
        super().__init__("Data Enrichment")
        self.max_concurrent_requests = (
            settings.pipeline.max_concurrent_enrichment
        )
        self.browser_manager = None
        self.extractor = None

    async def execute(self, context: PipelineContext) -> None:
        """
        Обогащает данные магазинов информацией с веб-сайтов.

        Args:
            context: Контекст выполнения pipeline
        """
        if not context.enrich_data or not context.extracted_data:
            self.logger.info(
                "Обогащение данных отключено или нет данных "
                "для обработки"
            )
            context.transformed_data = context.extracted_data or []
            return

        # Инициализируем браузер и экстрактор
        async with BrowserManager() as browser_manager:
            self.browser_manager = browser_manager
            self.extractor = DataExtractor(browser_manager)

            # Создаем семафор для ограничения параллелизма
            semaphore = asyncio.Semaphore(self.max_concurrent_requests)

            # Создаем задачи для параллельной обработки
            tasks = []
            for store_data in context.extracted_data:
                task = asyncio.create_task(
                    self._enrich_single_store(store_data, semaphore)
                )
                tasks.append(task)

            # Запускаем все задачи параллельно и ждем результатов
            self.logger.info(
                f"Запущено {len(tasks)} задач обогащения "
                f"(макс. {self.max_concurrent_requests} одновременно)"
            )

            # Используем asyncio.as_completed для обработки по мере завершения
            enriched_data = []
            completed_count = 0

            # Собираем все результаты с таймаутом
            pending = set(tasks)
            completed = set()

            while pending:
                try:
                    done, pending = await asyncio.wait(
                        pending,
                        timeout=30.0,  # 30 секунд на задачу
                        return_when=asyncio.FIRST_COMPLETED
                    )

                    for task in done:
                        try:
                            enriched_store = await task
                            enriched_data.append(enriched_store)

                            if enriched_store.get("description"):
                                context.enriched_count += 1

                            completed_count += 1

                            if completed_count % 10 == 0:
                                total = len(context.extracted_data)
                                self.logger.info(
                                    f"Обработано магазинов: "
                                    f"{completed_count}/{total}"
                                )

                        except Exception as e:
                            store_name = "Unknown"
                            try:
                                # Пытаемся получить имя из задачи
                                if hasattr(task, '_coro') and hasattr(task._coro, 'cr_frame'):
                                    # Это сложно, просто добавим пустые данные
                                    pass
                            except:
                                pass

                            self.logger.error(f"Ошибка при обработке задачи: {e}")
                            # Добавляем базовые данные в случае ошибки
                            enriched_data.append({})

                    completed.update(done)

                except asyncio.TimeoutError:
                    self.logger.warning(f"Таймаут при ожидании задач. Завершено: {len(completed)}, Осталось: {len(pending)}")
                    # Отменяем оставшиеся задачи
                    for task in pending:
                        if not task.done():
                            task.cancel()
                            try:
                                await task
                            except asyncio.CancelledError:
                                pass
                    break

            # Фильтруем только записи с place_id для сохранения в БД
            context.transformed_data = [
                store for store in enriched_data
                if store and isinstance(store, dict) and store.get('place_id')
            ]

            self.logger.info(
                f"Обогащение завершено. Обработано: {len(enriched_data)}, "
                f"Обогащено: {context.enriched_count}, "
                f"Для сохранения: {len(context.transformed_data)}"
            )
            self.logger.info(
                f"Обогащение завершено. Обработано: {len(enriched_data)}, "
                f"Обогащено: {context.enriched_count}"
            )

    async def _enrich_single_store(
        self,
        store_data: Dict[str, Any],
        semaphore: asyncio.Semaphore
    ) -> Dict[str, Any]:
        """
        Обогащает данные одного магазина.

        Args:
            store_data: Базовые данные магазина
            semaphore: Семафор для ограничения параллелизма

        Returns:
            Обогащенные данные магазина
        """
        website = store_data.get("website")
        if not website:
            store_name = store_data.get('name')
            self.logger.debug(
                f"Веб-сайт отсутствует для {store_name}"
            )
            return store_data

        async with semaphore:
            try:
                store_name = store_data.get('name')
                self.logger.info(
                    f"Обогащение данных для {store_name}: {website}"
                )

                # Извлекаем все поля с помощью динамических шаблонов
                extracted_fields = await self.extractor.extract_all_fields(website)

                # Сохраняем извлеченные поля в отдельном поле для новой архитектуры
                if extracted_fields:
                    store_data['extracted_fields'] = extracted_fields
                    extracted_count = len(extracted_fields)
                    self.logger.debug(
                        f"Извлечено {extracted_count} полей для "
                        f"{store_data.get('name')}"
                    )
                else:
                    self.logger.debug(
                        f"Не удалось извлечь поля для {store_data.get('name')}"
                    )

            except Exception as e:
                self.logger.warning(
                    f"Ошибка при обогащении данных для "
                    f"{store_data.get('name')}: {e}"
                )

        return store_data
