#!/usr/bin/env python3
"""
Тест нового шаблона structured_data
"""

import sys
import os

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.extraction.templates import ExtractionTemplates

def test_structured_data_template():
    """Тестирование шаблона structured_data"""
    print("Testing structured_data template...")

    # Получаем список всех шаблонов
    fields = ExtractionTemplates.get_available_fields()
    print(f"Доступные шаблоны: {fields}")
    print(f"Всего шаблонов: {len(fields)}")

    # Проверяем, что наш шаблон есть
    if 'structured_data' in fields:
        print("OK: structured_data template found!")

        # Получаем код шаблона
        template = ExtractionTemplates.get_template('structured_data')
        print(f"Template length: {len(template)} characters")

        # Проверяем ключевые части
        checks = [
            ('JSON-LD search', 'application/ld+json' in template),
            ('Microdata', 'extractMicrodata' in template),
            ('OpenGraph', 'og:' in template),
            ('Twitter Card', 'twitter:' in template),
            ('Tables', 'extractTableData' in template),
            ('Schema.org', 'itemtype' in template),
        ]

        print("\nFunctionality checks:")
        for name, check in checks:
            status = "[OK]" if check else "[FAIL]"
            print(f"  {status} {name}")

        # Показываем превью
        print("\nПревью шаблона:")
        print("=" * 50)
        print(template[:500] + "..." if len(template) > 500 else template)
        print("=" * 50)

        return True
    else:
        print("FAIL: structured_data template not found!")
        return False

if __name__ == "__main__":
    success = test_structured_data_template()
    print(f"\n{'Test PASSED!' if success else 'Test FAILED!'}")
    sys.exit(0 if success else 1)
