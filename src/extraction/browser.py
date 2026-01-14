"""
Управление браузером для извлечения данных.
"""

import os
import logging
import platform
from typing import Optional
import asyncio
from pyppeteer import launch

try:
    from pyppeteer_stealth import stealth
except ImportError:
    try:
        # Альтернативный импорт
        from pyppeteer.stealth import stealth
    except ImportError:
        # Fallback если pyppeteer-stealth не установлен
        async def stealth(page):  # noqa: ARG001
            """Заглушка для stealth функции."""
            pass


if __name__ == "__main__":

    async def test_browser_manager():
        """Тест BrowserManager."""
        manager = BrowserManager()

        assert manager.headless is True
        assert manager.timeout == 10000
        assert manager.browser is None

        print("[OK] BrowserManager инициализация тест пройден")

        # Тест поиска пути к Chrome (может быть недоступен в тестовой среде)
        chrome_path = manager._find_chrome_executable()
        if chrome_path:
            print(f"[OK] Chrome найден: {chrome_path}")
        else:
            print("[WARN] Chrome не найден (нормально в тестовой среде)")

    asyncio.run(test_browser_manager())

logger = logging.getLogger(__name__)


class BrowserManager:
    """
    Менеджер браузера для извлечения данных с веб-сайтов.

    Управляет жизненным циклом браузера и созданием страниц.
    """

    def __init__(self):
        """
        Инициализирует менеджер браузера.
        """
        from ..config import settings
        self.logger = logging.getLogger(__name__)
        self.headless = settings.browser.headless
        self.timeout = settings.browser.timeout
        self.browser = None

    def _find_chrome_executable(self) -> Optional[str]:
        """
        Находит путь к исполняемому файлу Chrome/Chromium в системе.

        Returns:
            Путь к chrome.exe или None, если не найден
        """
        system = platform.system()

        # Проверяем переменные окружения (для Docker)
        chrome_bin = (
            os.environ.get('CHROME_BIN') or
            os.environ.get('CHROMIUM_BIN')
        )
        if chrome_bin and os.path.exists(chrome_bin):
            return chrome_bin

        if system == "Windows":
            # Стандартные пути для Chrome на Windows
            possible_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expanduser(
                    r"~\AppData\Local\Google\Chrome\Application\chrome.exe"
                ),
                r"C:\Program Files\Chromium\Application\chrome.exe",
            ]
        elif system == "Darwin":  # macOS
            possible_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
            ]
        else:  # Linux (включая Docker)
            # Google Chrome в Debian/Ubuntu
            possible_paths = [
                "/usr/bin/google-chrome-stable",
                "/usr/bin/google-chrome",  # Альтернативный путь
                "/usr/bin/chromium-browser",  # Chromium
                "/usr/bin/chromium",  # Chromium (альтернативный путь)
                "/snap/bin/chromium",  # Snap пакет
            ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        return None

    async def launch_browser(self) -> None:
        """
        Запускает браузер (алиас для start_browser для совместимости).
        """
        await self.start_browser()

    async def close_browser(self) -> None:
        """
        Закрывает браузер (алиас для stop_browser для совместимости).
        """
        await self.stop_browser()

    async def start_browser(self) -> None:
        """
        Запускает браузер.

        Raises:
            Exception: При ошибке запуска браузера
        """
        try:
            executable_path = self._find_chrome_executable()
            self.browser = await launch(
                ignoreHTTSErrors=True,
                executablePath=executable_path,
                headless=self.headless,
                autoClose=False,  # Отключаем автоматическое закрытие браузера
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-extensions',
                    '--disable-plugins',
                    # Отключаем загрузку изображений для скорости
                    '--disable-images',
                    # Дополнительно отключаем изображения
                    '--blink-settings=imagesEnabled=false',
                    '--disable-software-rasterizer',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-ipc-flooding-protection',
                ]
            )
            logger.info("Браузер успешно запущен")
        except Exception as e:
            logger.error(f"Ошибка при запуске браузера: {e}")
            raise

    async def stop_browser(self) -> None:
        """
        Останавливает браузер и очищает ресурсы.
        """
        if self.browser:
            try:
                # Graceful shutdown - закрываем все страницы сначала
                if hasattr(self.browser, 'pages'):
                    try:
                        pages = await self.browser.pages()
                        self.logger.debug(f"Закрываем {len(pages)} страниц браузера")

                        close_tasks = []
                        for page in pages:
                            try:
                                # Создаем задачу для закрытия каждой страницы
                                task = page.close()
                                close_tasks.append(task)
                            except Exception as e:
                                self.logger.debug(f"Ошибка создания задачи закрытия страницы: {e}")

                        # Ждем закрытия всех страниц с таймаутом
                        if close_tasks:
                            try:
                                results = await asyncio.wait_for(
                                    asyncio.gather(*close_tasks, return_exceptions=True),
                                    timeout=5.0  # 5 секунд на закрытие всех страниц
                                )
                                closed_count = sum(1 for r in results if not isinstance(r, Exception))
                                self.logger.debug(f"Закрыто {closed_count}/{len(close_tasks)} страниц")
                            except asyncio.TimeoutError:
                                self.logger.warning("Таймаут при закрытии страниц браузера")
                            except Exception as e:
                                self.logger.debug(f"Ошибка при закрытии страниц: {e}")
                    except Exception as e:
                        self.logger.debug(f"Ошибка получения списка страниц: {e}")

                # Небольшая пауза перед закрытием браузера
                await asyncio.sleep(0.1)

                # Закрываем браузер
                await self.browser.close()

                # Дополнительная пауза для полного завершения
                await asyncio.sleep(0.1)

                logger.info("Браузер успешно закрыт")
            except Exception as e:
                logger.warning(f"Ошибка при закрытии браузера: {e}")
            finally:
                self.browser = None

    async def create_page(self):
        """
        Создает новую страницу с примененными stealth настройками.

        Returns:
            Объект страницы браузера
        """
        if not self.browser:
            raise RuntimeError(
                "Браузер не запущен. Вызовите start_browser() сначала."
            )

        page = await self.browser.newPage()

        # Применяем stealth режим
        await stealth(page)

        # Устанавливаем user agent
        user_agent = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )
        await page.setUserAgent(user_agent)

        return page

    async def __aenter__(self):
        """Контекстный менеджер - вход."""
        await self.start_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - выход."""
        await self.stop_browser()
