"""
Динамическая система шаблонов для извлечения данных из веб-страниц.

Автоматически загружает JavaScript шаблоны из папки templates/
в порядке нумерации файлов.
"""

import os
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ExtractionTemplates:
    """
    Динамическая система шаблонов для извлечения данных.

    Автоматически загружает и применяет JavaScript шаблоны
    из папки templates/ в алфавитном порядке.
    """

    _templates_cache: Optional[Dict[str, str]] = None

    @classmethod
    def _load_templates(cls) -> Dict[str, str]:
        """
        Загружает все шаблоны из папки templates/.

        Returns:
            Словарь {field_name: javascript_code}
        """
        if cls._templates_cache is not None:
            return cls._templates_cache

        templates_dir = Path(__file__).parent / "templates"
        templates = {}

        if not templates_dir.exists():
            logger.warning(f"Папка шаблонов не найдена: {templates_dir}")
            return templates

        # Загружаем все .js файлы в алфавитном порядке
        js_files = sorted(templates_dir.glob("*.js"))

        for js_file in js_files:
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                if content:
                    # Извлекаем имя поля из имени файла (без номера и расширения)
                    field_name = js_file.stem.split('_', 1)[-1]
                    templates[field_name] = content
                    logger.debug(f"Загружен шаблон: {field_name} из {js_file.name}")
                else:
                    logger.warning(f"Пустой шаблон: {js_file}")

            except Exception as e:
                logger.error(f"Ошибка загрузки шаблона {js_file}: {e}")

        cls._templates_cache = templates
        logger.info(f"Загружено {len(templates)} шаблонов")
        return templates

    @classmethod
    def get_available_fields(cls) -> List[str]:
        """
        Возвращает список доступных полей для извлечения.

        Returns:
            Список имен полей
        """
        return list(cls._load_templates().keys())

    @classmethod
    def get_template(cls, field_name: str) -> Optional[str]:
        """
        Возвращает JavaScript код для указанного поля.

        Args:
            field_name: Имя поля

        Returns:
            JavaScript код или None если поле не найдено
        """
        templates = cls._load_templates()
        return templates.get(field_name)

    @classmethod
    def get_all_templates(cls) -> Dict[str, str]:
        """
        Возвращает все загруженные шаблоны.

        Returns:
            Словарь всех шаблонов {field_name: javascript_code}
        """
        return cls._load_templates().copy()

    @classmethod
    def clear_cache(cls) -> None:
        """
        Очищает кэш шаблонов. Следующий вызов перезагрузит их.
        """
        cls._templates_cache = None
        logger.info("Кэш шаблонов очищен")


if __name__ == "__main__":  # noqa
    """Тест ExtractionTemplates."""
    # Тест загрузки шаблонов
    templates = ExtractionTemplates.get_all_templates()
    print(f"Загружено шаблонов: {len(templates)}")

    fields = ExtractionTemplates.get_available_fields()
    print(f"Доступные поля: {fields}")

    if fields:
        # Тест получения конкретного шаблона
        first_field = fields[0]
        template = ExtractionTemplates.get_template(first_field)
        print(f"Шаблон для поля '{first_field}': {'найден' if template else 'не найден'}")

    # Тест очистки кэша
    ExtractionTemplates.clear_cache()
    print("Кэш очищен")

    print("[OK] ExtractionTemplates тест пройден")