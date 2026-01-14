"""
Оркестратор ETL pipeline.

Координирует выполнение всех этапов pipeline.
"""

import logging
from typing import List, AsyncGenerator
from .base import ETLStep, PipelineContext

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Оркестратор для выполнения ETL pipeline.

    Координирует выполнение этапов в правильном порядке.
    """

    def __init__(self, steps: List[ETLStep]):
        """
        Инициализирует оркестратор.

        Args:
            steps: Список этапов pipeline в порядке выполнения
        """
        self.steps = steps
        self.logger = logger

    async def execute_pipeline(self, context: PipelineContext) -> None:
        """
        Выполняет полный pipeline с инициализацией ресурсов.

        Args:
            context: Контекст выполнения pipeline

        Raises:
            Exception: При ошибке в любом из этапов
        """
        self.logger.info("Начало выполнения pipeline")

        try:
            # Инициализация ресурсов
            await self._init_resources()

            # Выполнение этапов
            for step in self.steps:
                await step.safe_execute(context)

            extracted_count = len(context.extracted_data or [])
            self.logger.info(
                f"Pipeline завершен. Обработано: {extracted_count}, "
                f"Сохранено: {context.saved_count}, "
                f"Обогащено: {context.enriched_count}"
            )

        except Exception as e:
            self.logger.error(f"Критическая ошибка в pipeline: {e}")
            raise
        finally:
            # Очистка ресурсов
            await self._cleanup()

    async def execute_streaming_pipeline(
        self,
        data_stream: AsyncGenerator[List[dict], None],
        context: PipelineContext
    ) -> None:
        """
        Выполняет streaming pipeline - обрабатывает данные по мере поступления.

        Args:
            data_stream: Асинхронный генератор страниц данных
            context: Контекст выполнения pipeline

        Raises:
            Exception: При ошибке в любом из этапов
        """
        self.logger.info("Начало streaming pipeline")

        try:
            # Инициализация ресурсов
            await self._init_resources()

            # Обрабатываем данные постранично
            async for page in data_stream:
                context.extracted_data = page

                # Выполняем этапы для этой страницы (начиная с Transform)
                for step in self.steps[1:]:  # Пропускаем DataFetcher
                    await step.safe_execute(context)

                # Накопительная статистика
                # Предполагаем, что все записи со страницы сохранены
                page_saved = len(page)
                # Считаем обогащенные
                page_enriched = len([
                    item for item in page if item.get('description')
                ])

                context.saved_count += page_saved
                context.enriched_count += page_enriched

                self.logger.info(
                    f"Страница обработана. Сохранено: +{page_saved}, "
                    f"Обогащено: +{page_enriched}"
                )

            self.logger.info(
                f"Streaming pipeline завершен. "
                f"Всего сохранено: {context.saved_count}, "
                f"Обогащено: {context.enriched_count}"
            )

        except Exception as e:
            self.logger.error(
                f"Критическая ошибка в streaming pipeline: {e}"
            )
            raise
        finally:
            await self._cleanup()

    async def _init_resources(self) -> None:
        """
        Инициализирует необходимые ресурсы (БД, браузер и т.д.).
        """
        from src.database import async_db_manager

        # Инициализация асинхронной БД
        if async_db_manager.pool is None:
            await async_db_manager.init_pool()
            self.logger.info("База данных инициализирована")

    async def _cleanup(self) -> None:
        """
        Очищает ресурсы после выполнения pipeline.
        """
        from src.database import async_db_manager

        try:
            # Закрываем асинхронные соединения с БД
            if async_db_manager.pool:
                await async_db_manager.close_pool()

            # Закрываем браузер если он был инициализирован
            for step in self.steps:
                if hasattr(step, 'browser_manager') and step.browser_manager:
                    try:
                        await step.browser_manager.stop_browser()
                        self.logger.debug("Браузер закрыт")
                    except Exception as e:
                        self.logger.warning(f"Ошибка при закрытии браузера: {e}")

            self.logger.debug("Ресурсы pipeline очищены")
        except Exception as e:
            self.logger.warning(f"Ошибка при очистке ресурсов: {e}")

