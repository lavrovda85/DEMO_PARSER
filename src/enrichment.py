"""
Модуль для обогащения данных о магазинах.

Использует Stealth Puppeteer или Playwright для извлечения описания главной страницы
веб-сайта магазина.
"""

import logging
import asyncio
import os
import platform
from typing import Optional, Callable, Any
from src.utils import async_retry
# Попытка импорта Playwright (предпочтительный вариант)
from playwright.async_api import async_playwright
from pyppeteer import launch as pyppeteer_launch
from pyppeteer_stealth import stealth as stealth_func

logger = logging.getLogger(__name__)


def _find_chrome_executable() -> Optional[str]:
    """
    Находит путь к исполняемому файлу Chrome/Chromium в системе.
    
    Returns:
        Путь к chrome.exe или None, если не найден.
    """
    system = platform.system()
    
    # Проверяем переменные окружения (для Docker)
    chrome_bin = os.environ.get('CHROME_BIN') or os.environ.get('CHROMIUM_BIN')
    if chrome_bin and os.path.exists(chrome_bin):
        return chrome_bin
    
    if system == "Windows":
        # Стандартные пути для Chrome на Windows
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
            r"C:\Program Files\Chromium\Application\chrome.exe",
        ]
    elif system == "Darwin":  # macOS
        possible_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
    else:  # Linux (включая Docker)
        possible_paths = [
            "/usr/bin/google-chrome-stable",  # Google Chrome в Debian/Ubuntu
            "/usr/bin/google-chrome",         # Альтернативный путь
            "/usr/bin/chromium-browser",       # Chromium
            "/usr/bin/chromium",               # Chromium (альтернативный путь)
            "/snap/bin/chromium",              # Snap пакет
        ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None


class WebsiteEnricher:
    """
    Класс для обогащения данных о магазинах через извлечение информации с веб-сайтов.
    
    Использует Playwright (предпочтительно) или Stealth Puppeteer для обхода защиты 
    от ботов и извлечения описания главной страницы.
    """
    
    def __init__(
        self, 
        headless: bool = None, 
        timeout: int = None, 
        use_playwright: bool = None,
        browser_library: str = None
    ):
        """
        Инициализирует обогатитель данных.
        
        Args:
            headless: Запускать браузер в headless режиме. Если None, берется из настроек.
            timeout: Таймаут для загрузки страницы в миллисекундах. Если None, берется из настроек.
            use_playwright: Принудительно использовать Playwright (True) или pyppeteer (False).
                          Если None, выбирается из настроек или автоматически.
            browser_library: Строка "playwright", "pyppeteer" или "auto". Если None, берется из настроек.
        """
        from src.config import settings
        
        # Используем настройки из конфигурации, если параметры не указаны
        self.headless = headless if headless is not None else settings.enrichment.headless
        self.timeout = timeout if timeout is not None else settings.enrichment.timeout
        
        # Определяем, какую библиотеку использовать
        library_choice = browser_library or settings.enrichment.browser_library
        
        if library_choice == "playwright":
            self.use_playwright = True
        elif library_choice == "pyppeteer":
            self.use_playwright = False
        else:
            raise ValueError(
                f"Неизвестное значение browser_library: {library_choice}. "
                f"Используйте 'playwright', 'pyppeteer' или 'auto'"
            )
        
        
        # Для pyppeteer находим системный Chrome
        self.chrome_executable = None
        if not self.use_playwright:
            self.chrome_executable = _find_chrome_executable()
            if not self.chrome_executable:
                logger.warning(
                    "Chrome/Chromium не найден в системе. "
                    "Установите Chrome или используйте Playwright: pip install playwright"
                )
            launch_options = {
                'handleSIGTERM' : False,
                'handleSIGINT' : False,
                'autoClose' : False,
                'headless': self.headless,
                'args': [
                    '--no-sandbox',                    # Требуется для Docker
                    '--disable-setuid-sandbox',        # Требуется для Docker
                    '--disable-dev-shm-usage',          # Избегает проблем с /dev/shm в Docker
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',                   # Отключает GPU в headless режиме
                    '--disable-software-rasterizer',
                    '--disable-extensions',
                    '--window-size=1920x1080',
                    '--single-process',                 # Для Docker (опционально)
                ]
            }
            # Используем системный Chrome, если найден
            if self.chrome_executable:
                launch_options['executablePath'] = self.chrome_executable
                logger.debug("Используется системный Chrome: %s", self.chrome_executable)
            
            if pyppeteer_launch is None:
                raise RuntimeError("pyppeteer не установлен")
            
            self.browser =  pyppeteer_launch(executablePath=self.chrome_executable)
    async def _extract_with_playwright(self, url: str) -> Optional[str]:
        """
        Извлекает описание с использованием Playwright.
        
        Args:
            url: URL веб-сайта для анализа.
            
        Returns:
            Текст описания главной страницы или None при ошибке.
        """
        async with async_playwright() as p:
            browser = None
            try:
                browser = await p.chromium.launch(headless=self.headless)
                page = await browser.new_page()
                
                # Устанавливаем user agent
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                                 '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                })
                
                logger.info("Загрузка страницы (Playwright): %s", url)
                
                # Загружаем страницу с таймаутом
                await page.goto(url, wait_until='networkidle', timeout=self.timeout)
                
                # Извлекаем мета-описание или текст из основных элементов
                description = await page.evaluate('''() => {
                    // Пытаемся получить мета-описание
                    const metaDesc = document.querySelector('meta[name="description"]');
                    if (metaDesc && metaDesc.content) {
                        return metaDesc.content.trim();
                    }
                    
                    // Пытаемся получить Open Graph описание
                    const ogDesc = document.querySelector('meta[property="og:description"]');
                    if (ogDesc && ogDesc.content) {
                        return ogDesc.content.trim();
                    }
                    
                    // Извлекаем текст из основного контента
                    const mainContent = document.querySelector('main') || 
                                       document.querySelector('article') ||
                                       document.querySelector('.content') ||
                                       document.querySelector('body');
                    
                    if (mainContent) {
                        // Берем первые несколько параграфов
                        const paragraphs = mainContent.querySelectorAll('p');
                        const texts = Array.from(paragraphs)
                            .slice(0, 3)
                            .map(p => p.textContent.trim())
                            .filter(text => text.length > 20);
                        
                        if (texts.length > 0) {
                            return texts.join(' ').substring(0, 1000);
                        }
                    }
                    
                    return null;
                }''')
                
                if description:
                    logger.info("Описание успешно извлечено для %s", url)
                    return description[:2000]  # Ограничение длины
                else:
                    logger.warning("Не удалось извлечь описание для %s", url)
                    return None
                    
            except asyncio.TimeoutError:
                logger.error("Таймаут при загрузке страницы: %s", url)
                return None
            except Exception as e:
                logger.error("Ошибка при извлечении описания с %s: %s", url, e)
                return None
            finally:
                if browser:
                    await browser.close()
    
    @async_retry(max_attempts=3, delay=1.0)
    async def _extract_with_pyppeteer(self, url: str) -> Optional[str]:
        """
        Извлекает описание с использованием pyppeteer.
        
        Args:
            url: URL веб-сайта для анализа.
            
        Returns:
            Текст описания главной страницы или None при ошибке.
        """
        try:
            
            page = await self.browser.newPage()
            
            # Применяем stealth режим для обхода защиты от ботов
            if stealth_func:
                await stealth_func(page)
            
            # Устанавливаем user agent
            await page.setUserAgent(
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            logger.info("Загрузка страницы (pyppeteer): %s", url)
            
            # Загружаем страницу с таймаутом
            await page.goto(url, waitUntil='networkidle2', timeout=self.timeout)
            description = await page.evaluate('sdocument.body.textContent', force_expr=True)
            # Извлекаем мета-описание или текст из основных элементов
            """description = await page.evaluate('''() => {
                            return {
                        width: document.documentElement.clientWidth
                                                    }
                                                }''')"""
            print(description)
            if description:
                logger.info("Описание успешно извлечено для %s", url)
                return description[:2000]  # Ограничение длины
            else:
                logger.warning("Не удалось извлечь описание для %s", url)
                return None
                
        except asyncio.TimeoutError:
            logger.error("Таймаут при загрузке страницы: %s", url)
            return None
        except Exception as e:
            logger.error("Ошибка при извлечении описания с %s: %s", url, e)
            return None
    
    async def extract_description(self, url: str) -> Optional[str]:
        """
        Извлекает описание главной страницы веб-сайта.
        
        Args:
            url: URL веб-сайта для анализа.
            
        Returns:
            Текст описания главной страницы или None при ошибке.
        """
        if not url or not url.startswith(("http://", "https://")):
            logger.warning("Некорректный URL: %s", url)
            return None
        
        if self.use_playwright:
            return await self._extract_with_playwright(url)
        else:
            return await self._extract_with_pyppeteer(url)
    
    def extract_description_sync(self, url: str) -> Optional[str]:
        """
        Синхронная обертка для извлечения описания.
        
        Args:
            url: URL веб-сайта для анализа.
            
        Returns:
            Текст описания главной страницы или None при ошибке.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.extract_description(url))

