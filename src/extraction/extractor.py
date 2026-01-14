"""
Компонент для извлечения данных из веб-страниц.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from src.utils import async_retry
from .templates import ExtractionTemplates
from .browser import BrowserManager

logger = logging.getLogger(__name__)


class DataExtractor:
    """
    Компонент для извлечения данных из веб-страниц.

    Использует шаблоны извлечения и менеджер браузера для
    получения структурированных данных с сайтов.
    """

    def __init__(self, browser_manager: BrowserManager):
        """
        Инициализирует экстрактор данных.

        Args:
            browser_manager: Менеджер браузера
        """
        self.browser_manager = browser_manager

    @async_retry(
        max_attempts=3, delay=1.0, return_none_on_failure=True
    )
    async def extract_data(
        self, url: str, data_type: str = "description"
    ) -> Optional[str]:
        """
        Извлекает данные указанного типа с веб-страницы.

        Args:
            url: URL страницы для анализа
            data_type: Тип данных для извлечения

        Returns:
            Извлеченные данные или None при ошибке
        """
        if not url or not url.startswith(("http://", "https://")):
            logger.warning(f"Некорректный URL: {url}")
            return None

        page = None
        try:
            page = await self.browser_manager.create_page()

            logger.info(f"Загрузка страницы: {url}")
            await page.goto(
                url,
                waitUntil='domcontentloaded',
                timeout=self.browser_manager.timeout
            )

            # Получаем JavaScript код для извлечения
            js_code = ExtractionTemplates.get_extractor_by_type(data_type)

            # Извлекаем данные
            result = await page.evaluate(js_code)

            if result:
                logger.info(f"Данные успешно извлечены для {url}")
                # Ограничиваем длину результата
                if isinstance(result, str):
                    return result[:2000]
                return result
            else:
                logger.warning(f"Не удалось извлечь данные для {url}")
                return None

        except asyncio.TimeoutError:
            logger.error(f"Таймаут при загрузке страницы: {url}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при извлечении данных с {url}: {e}")
            return None
        finally:
            # Закрываем страницу
            if page:
                try:
                    await page.close()
                except Exception:
                    # Игнорируем ошибки закрытия страницы
                    pass

    async def extract_description(self, url: str) -> Optional[str]:
        """
        Извлекает описание страницы.

        Args:
            url: URL страницы

        Returns:
            Описание страницы или None
        """
        return await self.extract_data(url, "description")

    async def extract_contact_info(
        self, url: str
    ) -> Optional[Dict[str, Any]]:
        """
        Извлекает контактную информацию со страницы.

        Args:
            url: URL страницы

        Returns:
            Словарь с контактной информацией или None
        """
        return await self.extract_data(url, "contact")

    async def extract_business_hours(self, url: str) -> Optional[str]:
        """
        Извлекает часы работы со страницы.

        Args:
            url: URL страницы

        Returns:
            Часы работы или None
        """
        return await self.extract_data(url, "hours")

    async def extract_all_fields(self, url: str) -> Dict[str, Any]:
        """
        Извлекает все доступные поля со страницы используя все шаблоны.

        Args:
            url: URL страницы

        Returns:
            Словарь с извлеченными данными {field_name: value}
        """
        if not url or not url.startswith(("http://", "https://")):
            logger.warning(f"Некорректный URL: {url}")
            return {}

        page = None
        extracted_data = {}

        try:
            page = await self.browser_manager.create_page()

            logger.info(f"Загрузка страницы для извлечения всех полей: {url}")
            await page.goto(
                url,
                waitUntil='domcontentloaded',
                timeout=self.browser_manager.timeout
            )

            # Получаем все доступные шаблоны
            templates = ExtractionTemplates.get_all_templates()

            if not templates:
                logger.warning("Не найдено ни одного шаблона для извлечения")
                return extracted_data

            # Применяем все шаблоны последовательно
            for field_name, js_code in templates.items():
                try:
                    logger.debug(f"Извлечение поля '{field_name}'")
                    result = await page.evaluate(js_code)

                    if result is not None:
                        # Ограничиваем длину результата
                        if isinstance(result, str):
                            result = result[:2000]
                        elif isinstance(result, dict):
                            # Для словарей тоже ограничиваем строковые значения
                            result = {
                                k: (v[:2000] if isinstance(v, str) else v)
                                for k, v in result.items()
                            }

                        extracted_data[field_name] = result
                        logger.debug(f"Поле '{field_name}' успешно извлечено")

                except Exception as e:
                    logger.warning(f"Ошибка извлечения поля '{field_name}': {e}")
                    continue

            logger.info(f"Извлечено полей: {len(extracted_data)} из {len(templates)}")

        except asyncio.TimeoutError:
            logger.error(f"Таймаут при загрузке страницы: {url}")
        except Exception as e:
            logger.error(f"Ошибка при извлечении данных с {url}: {e}")
        finally:
            # Закрываем страницу
            if page:
                try:
                    await page.close()
                except Exception:
                    pass  # Игнорируем ошибки закрытия

        return extracted_data


if __name__ == "__main__":
    from unittest.mock import AsyncMock
    import asyncio

    async def test_data_extractor():
        """Тест DataExtractor."""
        # Мок браузерного менеджера
        mock_manager = AsyncMock()
        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value="Test description")
        mock_page.close = AsyncMock()
        mock_manager.create_page = AsyncMock(return_value=mock_page)

        extractor = DataExtractor(mock_manager)

        # Тест с некорректным URL
        result = await extractor.extract_data("")
        assert result is None

        result = await extractor.extract_data("not-a-url")
        assert result is None

        print("[OK] DataExtractor тест пройден")

    asyncio.run(test_data_extractor())
