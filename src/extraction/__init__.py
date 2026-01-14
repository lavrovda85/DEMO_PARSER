"""
Модули для извлечения данных из веб-сайтов.
"""

from .templates import ExtractionTemplates
from .browser import BrowserManager
from .extractor import DataExtractor

__all__ = ["ExtractionTemplates", "BrowserManager", "DataExtractor"]
