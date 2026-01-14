"""
ClickHouse Data Vault клиент.

Асинхронный клиент для работы с ClickHouse в архитектуре Data Vault.
"""

import asyncio
import hashlib
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from clickhouse_driver import Client

from .schema import get_init_queries, get_drop_queries
from src.config import settings

logger = logging.getLogger(__name__)


class ClickHouseDataVaultClient:
    """
    Клиент для работы с ClickHouse в архитектуре Data Vault.

    Поддерживает хранение данных о магазинах и их атрибутах
    в нормализованном виде.
    """

    def __init__(
        self,
        host: str = settings.database.host,
        port: int = settings.database.port,
        database: str = settings.database.db,
        user: str = settings.database.user,
        password: str = settings.database.password
    ):
        """
        Инициализирует ClickHouse клиент.

        Args:
            host: Хост ClickHouse
            port: Порт ClickHouse (8123 для HTTP)
            database: Имя базы данных
            user: Имя пользователя
            password: Пароль пользователя
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password

        self.connection_string = (
            f"clickhouse://{user}:{password}@{host}:{port}/{database}"
        )
        self.client = None
        self.logger = logging.getLogger(__name__)

        print(f"DEBUG: ClickHouse клиент создан: host={host}, port={port}, database={database}")
        self.logger.info(f"ClickHouse клиент создан: host={host}, port={port}, database={database}")

    async def init_pool(self) -> None:
        """Инициализирует соединение с ClickHouse."""
        try:
            logger.info("Инициализация ClickHouse клиента...")
            # Ждем, пока ClickHouse запустится (максимум 30 секунд)
            max_attempts = 30
            for attempt in range(max_attempts):
                try:
                    # Создаем синхронный клиент ClickHouse
                    self.client = Client(
                        host=self.host,
                        port=self.port,
                        database=self.database,
                        user=self.user,
                        password=self.password
                    )
                    # Тестируем соединение
                    await asyncio.to_thread(self.client.execute, "SELECT 1")
                    logger.info("ClickHouse клиент инициализирован")
                    return
                except Exception as e:
                    if attempt < max_attempts - 1:
                        logger.warning(f"ClickHouse недоступен (попытка {attempt+1}/{max_attempts}), ждем...")
                        await asyncio.sleep(1)
                    else:
                        raise e
        except Exception as e:
            logger.error(f"Ошибка инициализации ClickHouse клиента: {e}")
            raise

    async def close_pool(self) -> None:
        """Закрывает соединение."""
        if self.client:
            await asyncio.to_thread(self.client.disconnect)
            logger.info("ClickHouse клиент закрыт")

    async def init_schema(self) -> None:
        """Инициализирует Data Vault схему в ClickHouse."""
        try:
            schema_sql = get_init_queries()
            # Разбиваем SQL на отдельные запросы
            queries = [q.strip() for q in schema_sql.split(';') if q.strip()]

            for query in queries:
                if query:
                    await asyncio.to_thread(self.client.execute, query)
                    logger.debug("Выполнен запрос инициализации схемы")

            logger.info("Data Vault схема успешно инициализирована")
        except Exception as e:
            logger.error(f"Ошибка инициализации схемы: {e}")
            raise

    async def drop_schema(self) -> None:
        """Удаляет все Data Vault таблицы."""
        try:
            drop_sql = get_drop_queries()
            queries = [q.strip() for q in drop_sql.split(';') if q.strip()]

            for query in queries:
                if query:
                    await asyncio.to_thread(self.client.execute, query)

            logger.info("Data Vault схема успешно удалена")
        except Exception as e:
            logger.error(f"Ошибка удаления схемы: {e}")
            raise

    def _generate_hash(self, data: str) -> int:
        """Генерирует 64-битный хэш из строки."""
        return int(hashlib.md5(data.encode('utf-8')).hexdigest()[:16], 16)

    async def upsert_store_legacy(self, store_data: Dict[str, Any]) -> str:
        """
        Вставляет или обновяет данные магазина в Data Vault.

        Args:
            store_data: Данные магазина

        Returns:
            Статус операции
        """
        try:
            # Проверяем, что store_data не None
            if store_data is None:
                raise ValueError("store_data is None")

            place_id = store_data.get('place_id')
            if not place_id:
                raise ValueError("place_id обязателен для сохранения")

            # Создаем бизнес-ключ
            business_key = f"{store_data.get('name', '')}|{store_data.get('address', '')}"
            if not isinstance(place_id, str):
                raise ValueError(f"place_id должен быть строкой, получен: {type(place_id)}")
            store_hash = self._generate_hash(place_id)

            # Выделяем статические атрибуты
            location = store_data.get('location') or {}
            lat = location.get('lat')
            lng = location.get('lng')

            # Преобразуем координаты в числа или None
            try:
                latitude = float(lat) if lat is not None else None
            except (ValueError, TypeError):
                latitude = None

            try:
                longitude = float(lng) if lng is not None else None
            except (ValueError, TypeError):
                longitude = None

            static_attrs = {
                'name': store_data.get('name', ''),
                'address': store_data.get('address', ''),
                'phone': store_data.get('phone'),
                'website': store_data.get('website'),
                'latitude': latitude,
                'longitude': longitude,
                'rating': store_data.get('rating'),
                'user_ratings_total': store_data.get('user_ratings_total'),
                'types': store_data.get('types', []),
                'price_level': store_data.get('price_level')
            }

            # Фильтруем None значения из static_attrs
            static_attrs = {k: v for k, v in static_attrs.items() if v is not None}

            # Выделяем динамические поля (все остальные)
            dynamic_fields = {}
            for key, value in store_data.items():
                if key not in static_attrs and key not in ['place_id', 'location'] and value is not None:
                    dynamic_fields[key] = value

            # JSON для динамических полей
            try:
                extracted_fields_json = json.dumps(dynamic_fields, ensure_ascii=False)
            except Exception as json_error:
                self.logger.error(f"Ошибка сериализации dynamic_fields: {json_error}, данные: {dynamic_fields}")
                raise

            # Хэш для satellite таблицы
            try:
                attrs_str = json.dumps(static_attrs, sort_keys=True, ensure_ascii=False)
                if not isinstance(attrs_str, str):
                    raise ValueError(f"attrs_str должен быть строкой, получен: {type(attrs_str)}")
            except Exception as json_error:
                self.logger.error(f"Ошибка сериализации static_attrs: {json_error}, данные: {static_attrs}")
                raise
            hash_diff = self._generate_hash(attrs_str)

            load_date = datetime.now()
            record_source = "google_places_api"

            # Вставляем в hub_stores
            self.logger.info(f"Выполняем INSERT в hub_stores для {place_id}")
            await asyncio.to_thread(self.client.execute, """
                INSERT INTO hub_stores (store_hash, place_id, business_key, load_date, record_source)
                VALUES""", [(
                    store_hash, place_id, business_key, load_date, record_source
                )])
            self.logger.info(f"Успешно вставлено в hub_stores для {place_id}")

            # Вставляем в sat_store_attributes
            self.logger.info(f"Выполняем INSERT в sat_store_attributes для {place_id}")
            await asyncio.to_thread(self.client.execute, """
                INSERT INTO sat_store_attributes (
                    store_hash, load_date, hash_diff, name, address, phone, website,
                    latitude, longitude, rating, user_ratings_total, types, price_level,
                    extracted_fields, record_source
                ) VALUES""", [(
                    store_hash, load_date, hash_diff,
                    static_attrs.get('name'), static_attrs.get('address'), static_attrs.get('phone'),
                    static_attrs.get('website'), static_attrs.get('latitude'), static_attrs.get('longitude'),
                    static_attrs.get('rating'), static_attrs.get('user_ratings_total'),
                    static_attrs.get('types'), static_attrs.get('price_level'),
                    extracted_fields_json, record_source
                )])
            self.logger.info(f"Успешно вставлено в sat_store_attributes для {place_id}")

            # Обрабатываем динамические поля
            for field_name, field_value in dynamic_fields.items():
                try:
                    if field_name is None:
                        self.logger.warning(f"Пропускаем динамическое поле с None именем для {place_id}")
                        continue
                    if not isinstance(field_name, str):
                        field_name = str(field_name)
                    if field_value is None:
                        field_value = ""
                    field_hash = self._generate_hash(field_name)
                    field_value_str = str(field_value)
                    value_hash_diff = self._generate_hash(field_value_str)

                    # Вставляем в hub_fields (если не существует)
                    await asyncio.to_thread(self.client.execute, """
                        INSERT INTO hub_fields (field_hash, field_name, field_type, load_date, record_source)
                        VALUES""", [(
                            field_hash, field_name, "dynamic", load_date, record_source
                        )])

                    # Вставляем значение в sat_field_values
                    value_hash_diff = self._generate_hash(field_value_str)
                    await asyncio.to_thread(self.client.execute, """
                        INSERT INTO sat_field_values (
                            field_hash, store_hash, load_date, hash_diff,
                            field_value, is_active, record_source
                        ) VALUES""", [(
                            field_hash, store_hash, load_date, value_hash_diff,
                            field_value_str, 1, record_source
                        )])

                    # Вставляем связь в link_store_fields
                    await asyncio.to_thread(self.client.execute, """
                        INSERT INTO link_store_fields (
                            store_hash, field_hash, load_date, record_source
                        ) VALUES""", [(
                            store_hash, field_hash, load_date, record_source
                        )])
                except Exception as field_error:
                    self.logger.error(f"Ошибка обработки динамического поля {field_name} для {place_id}: {field_error}")
                    # Продолжаем с другими полями

            logger.debug(f"Магазин {place_id} сохранен в Data Vault")
            return "INSERT"

        except Exception as e:
            try:
                place_id_for_error = store_data.get('place_id') if store_data else 'unknown'
            except Exception:
                place_id_for_error = 'unknown'
            logger.error(f"Ошибка сохранения магазина {place_id_for_error}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def upsert_store(self, store_data: Dict[str, Any]) -> str:
        """
        Вставляет или обновляет данные магазина в новой многослойной архитектуре.

        Args:
            store_data: Данные магазина с ключами:
                - place_id: Google Places ID
                - name, address, phone, website, location, rating, etc. (core поля)
                - extracted_fields: словарь с динамическими полями
                - raw_api_response: сырой JSON ответ API (опционально)

        Returns:
            Статус операции
        """
        try:
            if store_data is None:
                raise ValueError("store_data is None")

            place_id = store_data.get('place_id')
            if not place_id:
                raise ValueError("place_id обязателен для сохранения")

            if not isinstance(place_id, str):
                raise ValueError(f"place_id должен быть строкой, получен: {type(place_id)}")

            # Генерируем хэши
            store_hash = self._generate_hash(place_id)
            business_key = f"{store_data.get('name', '')}|{store_data.get('address', '')}"

            load_date = datetime.now()
            record_source = store_data.get('record_source', 'google_places_api')

            # ===========================================
            # 1. HUB LAYER: вставляем в hub_stores (если еще не существует)
            # ===========================================
            await asyncio.to_thread(self.client.execute, """
                INSERT INTO places_db.hub_stores (store_hash, place_id, business_key, load_date, record_source)
                VALUES""", [(
                    store_hash, place_id, business_key, load_date, record_source
                )])

            # ===========================================
            # 2. RAW LAYER: сохраняем сырые данные
            # ===========================================
            raw_api_response = store_data.get('raw_api_response', json.dumps(store_data, ensure_ascii=False))
            raw_hash = self._generate_hash(raw_api_response)

            await asyncio.to_thread(self.client.execute, """
                INSERT INTO places_db.sat_store_raw (store_hash, load_date, hash_diff, raw_data, api_response, record_source)
                VALUES""", [(
                    store_hash, load_date, raw_hash, raw_api_response, raw_api_response, record_source
                )])

            # ===========================================
            # 3. ATTRIBUTE SYSTEM: сохраняем данные как атрибуты
            # ===========================================
            core_attributes = self._extract_core_attributes(store_data)

            # Вычисляем метрики качества данных
            data_quality_score = self._calculate_data_quality(core_attributes)
            validation_status = self._validate_core_data(core_attributes)

            await self._save_core_attributes(store_hash, core_attributes, load_date, record_source, data_quality_score, validation_status)

            # ===========================================
            # 4. FIELD-BASED STORAGE: сохраняем динамические поля
            # ===========================================
            extracted_fields = store_data.get('extracted_fields', {})
            await self._save_dynamic_fields(store_hash, extracted_fields, load_date, record_source)

            self.logger.info(f"Магазин {place_id} успешно сохранен в многослойной архитектуре")
            return "INSERT"

        except Exception as e:
            place_id_for_error = store_data.get('place_id') if store_data else 'unknown'
            self.logger.error(f"Ошибка сохранения магазина {place_id_for_error}: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def _extract_core_attributes(self, store_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Извлекает core атрибуты из store_data.

        Returns:
            Словарь {attribute_name: {'value': value, 'type': type, 'category': category}}
        """
        try:
            attributes = {}

            if not store_data:
                return {}

            # Базовые атрибуты
            name_val = str(store_data.get('name', '')).strip()
            attributes['name'] = {
                'value': name_val,
                'type': 'string',
                'category': 'basic'
            }

            address_val = str(store_data.get('address', '')).strip()
            attributes['address'] = {
                'value': address_val,
                'type': 'string',
                'category': 'basic'
            }

            # Контактные данные
            phone = store_data.get('phone')
            if phone:
                attributes['phone'] = {
                    'value': str(phone),
                    'type': 'string',
                    'category': 'contact'
                }

            website = store_data.get('website')
            if website:
                attributes['website'] = {
                    'value': str(website),
                    'type': 'string',
                    'category': 'contact'
                }

            # Координаты
            location = store_data.get('location')
            if location and isinstance(location, dict):
                latitude = self._parse_coordinate(location.get('lat'))
                if latitude is not None:
                    attributes['latitude'] = {
                        'value': str(latitude),
                        'type': 'number',
                        'category': 'location'
                    }

                longitude = self._parse_coordinate(location.get('lng'))
                if longitude is not None:
                    attributes['longitude'] = {
                        'value': str(longitude),
                        'type': 'number',
                        'category': 'location'
                    }

            # Рейтинг и отзывы
            rating = store_data.get('rating')
            if rating is not None:
                attributes['rating'] = {
                    'value': str(rating),
                    'type': 'number',
                    'category': 'rating'
                }

            user_ratings_total = store_data.get('user_ratings_total')
            if user_ratings_total is not None:
                attributes['user_ratings_total'] = {
                    'value': str(user_ratings_total),
                    'type': 'number',
                    'category': 'rating'
                }

            # Типы мест
            types = store_data.get('types', [])
            if types:
                attributes['types'] = {
                    'value': json.dumps(types, ensure_ascii=False),
                    'type': 'array',
                    'category': 'categorization'
                }

            # Ценовой уровень
            price_level = store_data.get('price_level')
            if price_level is not None:
                attributes['price_level'] = {
                    'value': str(price_level),
                    'type': 'number',
                    'category': 'pricing'
                }

            return attributes

        except Exception as e:
            self.logger.error(f"Error in _extract_core_attributes: {e}")
            return {}

    async def _save_core_attributes(self, store_hash: int, core_attributes: Dict[str, Dict[str, Any]],
                                  load_date: datetime, record_source: str,
                                  data_quality_score: int, validation_status: str) -> None:
        """
        Сохраняет core атрибуты в универсальной системе атрибутов.
        """
        # Добавляем атрибуты метрик качества
        core_attributes['_data_quality_score'] = {
            'value': str(data_quality_score),
            'type': 'number',
            'category': 'metadata'
        }

        core_attributes['_validation_status'] = {
            'value': validation_status,
            'type': 'string',
            'category': 'metadata'
        }

        for attr_name, attr_data in core_attributes.items():
            # Создаем/получаем attribute_hash
            attribute_hash = self._generate_hash(attr_name)

            # Сохраняем метаданные атрибута (если не существует)
            await asyncio.to_thread(self.client.execute, """
                INSERT INTO places_db.hub_attributes (
                    attribute_hash, attribute_name, attribute_type, attribute_category, is_required, load_date, record_source
                ) VALUES""", [(
                    attribute_hash, attr_name, attr_data['type'], attr_data['category'], 1, load_date, record_source
                )])

            # Вычисляем хэш значения
            value_hash_diff = self._generate_hash(attr_data['value'])

            # Определяем качество значения
            confidence_score = self._calculate_attribute_confidence(attr_name, attr_data['value'])
            validation_status = self._validate_attribute_value(attr_name, attr_data['value'])

            # Сохраняем значение атрибута
            await asyncio.to_thread(self.client.execute, """
                INSERT INTO places_db.sat_store_attributes (
                    store_hash, attribute_hash, load_date, hash_diff,
                    attribute_value, attribute_value_type, confidence_score, validation_status, source_type,
                    record_source
                ) VALUES""", [(
                    store_hash, attribute_hash, load_date, value_hash_diff,
                    attr_data['value'], attr_data['type'], confidence_score, validation_status, 'api',
                    record_source
                )])

    def _calculate_attribute_confidence(self, attr_name: str, value: str) -> float:
        """
        Вычисляет уверенность в значении атрибута.
        """
        if not value or value.strip() == '':
            return 0.0

        # Для основных атрибутов высокая уверенность
        if attr_name in ['name', 'address']:
            return 0.9 if len(value.strip()) > 3 else 0.5

        # Для координат проверяем формат
        if attr_name in ['latitude', 'longitude']:
            try:
                float(value)
                return 0.95
            except ValueError:
                return 0.1

        # Для других атрибутов средняя уверенность
        return 0.8

    def _validate_attribute_value(self, attr_name: str, value: str) -> str:
        """
        Валидирует значение атрибута.
        """
        if not value or value.strip() == '':
            return 'missing'

        if attr_name in ['latitude', 'longitude']:
            try:
                float(value)
                return 'valid'
            except ValueError:
                return 'invalid'

        if attr_name == 'rating':
            try:
                rating = float(value)
                return 'valid' if 0 <= rating <= 5 else 'invalid'
            except ValueError:
                return 'invalid'

        # Для строковых атрибутов простая проверка
        return 'valid' if len(value.strip()) > 0 else 'invalid'

    def _parse_coordinate(self, coord) -> Optional[float]:
        """Парсит координату в float или возвращает None."""
        if coord is None:
            return None
        try:
            return float(coord)
        except (ValueError, TypeError):
            return None

    def _calculate_data_quality(self, core_attributes: Dict[str, Dict[str, Any]]) -> int:
        """
        Вычисляет оценку качества данных на основе атрибутов (0-100).

        Returns:
            Оценка качества (0-100)
        """
        score = 0
        total_attributes = len(core_attributes)

        if total_attributes == 0:
            return 0

        # Название (20 баллов)
        if 'name' in core_attributes and core_attributes['name']['value']:
            score += 20

        # Адрес (15 баллов)
        if 'address' in core_attributes and core_attributes['address']['value']:
            score += 15

        # Контакты (15 баллов)
        has_contacts = ('phone' in core_attributes and core_attributes['phone']['value']) or \
                      ('website' in core_attributes and core_attributes['website']['value'])
        if has_contacts:
            score += 15

        # Координаты (15 баллов)
        has_location = ('latitude' in core_attributes and core_attributes['latitude']['value']) and \
                      ('longitude' in core_attributes and core_attributes['longitude']['value'])
        if has_location:
            score += 15

        # Рейтинг и отзывы (15 баллов)
        has_rating = ('rating' in core_attributes and core_attributes['rating']['value']) and \
                    ('user_ratings_total' in core_attributes and core_attributes['user_ratings_total']['value'])
        if has_rating:
            score += 15

        # Типы мест (10 баллов)
        if 'types' in core_attributes and core_attributes['types']['value']:
            score += 10

        # Ценовой уровень (10 баллов)
        if 'price_level' in core_attributes and core_attributes['price_level']['value']:
            score += 10

        return min(100, score)

    def _validate_core_data(self, core_attributes: Dict[str, Dict[str, Any]]) -> str:
        """
        Валидирует core атрибуты.

        Returns:
            'valid', 'partial', или 'invalid'
        """
        required_fields = ['name', 'address']
        has_required = all(field in core_attributes and core_attributes[field]['value']
                          for field in required_fields)

        has_location = ('latitude' in core_attributes and core_attributes['latitude']['value']) and \
                      ('longitude' in core_attributes and core_attributes['longitude']['value'])
        has_contacts = ('phone' in core_attributes and core_attributes['phone']['value']) or \
                      ('website' in core_attributes and core_attributes['website']['value'])

        if has_required and has_location and has_contacts:
            return 'valid'
        elif has_required:
            return 'partial'
        else:
            return 'invalid'

    async def _save_dynamic_fields(self, store_hash: int, extracted_fields: Dict[str, Any],
                                 load_date: datetime, record_source: str) -> None:
        """
        Сохраняет динамические поля в field-based storage.
        """
        if not extracted_fields:
            return

        for field_name, field_data in extracted_fields.items():
            try:
                # Определяем тип поля
                field_type = self._categorize_field(field_name)

                # Создаем хэш типа поля
                field_type_hash = self._generate_hash(field_type)

                # Сохраняем метаданные типа поля (если не существует)
                await asyncio.to_thread(self.client.execute, """
                    INSERT INTO hub_field_types (field_type_hash, field_type, field_category, load_date, record_source)
                    VALUES""", [(
                        field_type_hash, field_type, "enrichment", load_date, record_source
                    )])

                # Сохраняем значение поля
                field_value_str = json.dumps(field_data, ensure_ascii=False) if isinstance(field_data, dict) else str(field_data)
                field_hash_diff = self._generate_hash(field_value_str)

                # Определяем уверенность извлечения (простая логика)
                confidence = 0.8 if field_data else 0.5
                is_valid = 1 if field_data else 0

                await asyncio.to_thread(self.client.execute, """
                    INSERT INTO sat_field_values (
                        store_hash, field_type_hash, load_date, hash_diff,
                        field_name, field_value, field_confidence, is_valid, record_source
                    ) VALUES""", [(
                        store_hash, field_type_hash, load_date, field_hash_diff,
                        field_name, field_value_str, confidence, is_valid, record_source
                    )])

            except Exception as field_error:
                self.logger.error(f"Ошибка сохранения динамического поля {field_name}: {field_error}")

    def _categorize_field(self, field_name: str) -> str:
        """
        Определяет категорию поля по его имени.

        Returns:
            Категория поля
        """
        field_name_lower = field_name.lower()

        if any(keyword in field_name_lower for keyword in ['phone', 'contact', 'email']):
            return 'contact'
        elif any(keyword in field_name_lower for keyword in ['hour', 'time', 'open', 'close']):
            return 'hours'
        elif any(keyword in field_name_lower for keyword in ['description', 'about', 'info']):
            return 'description'
        elif any(keyword in field_name_lower for keyword in ['social', 'facebook', 'twitter', 'instagram']):
            return 'social'
        elif any(keyword in field_name_lower for keyword in ['image', 'photo', 'picture']):
            return 'media'
        else:
            return 'other'

    async def check_store_exists(self, place_id: str) -> bool:
        """
        Проверяет существование магазина по place_id.

        Args:
            place_id: Google Places ID магазина

        Returns:
            True если магазин существует
        """
        try:
            store_hash = self._generate_hash(place_id)
            result = await asyncio.to_thread(
                self.client.execute,
                "SELECT 1 FROM hub_stores WHERE store_hash = %s LIMIT 1" % store_hash
            )
            return len(result) > 0
        except Exception as e:
            logger.error(f"Ошибка проверки существования магазина {place_id}: {e}")
            return False

    async def get_store_data(self, place_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает полные данные о магазине.

        Args:
            place_id: Google Places ID магазина

        Returns:
            Словарь с данными магазина или None
        """
        try:
            # Получаем основные данные
            result = await asyncio.to_thread(self.client.execute, """
                SELECT
                    hs.place_id,
                    sa.name,
                    sa.address,
                    sa.phone,
                    sa.website,
                    sa.latitude,
                    sa.longitude,
                    sa.rating,
                    sa.user_ratings_total,
                    sa.types,
                    sa.price_level,
                    sa.extracted_fields
                FROM hub_stores hs
                LEFT JOIN sat_store_attributes sa ON hs.store_hash = sa.store_hash
                WHERE hs.place_id = '%s'
                ORDER BY sa.load_date DESC
                LIMIT 1
            """ % place_id)

            if not result:
                return None

            store_data = result[0] if result else None

            if not store_data:
                return None

            # Преобразуем в словарь
            result_dict = dict(store_data)

            # Парсим JSON с динамическими полями
            if result_dict.get('extracted_fields'):
                try:
                    dynamic_fields = json.loads(result_dict['extracted_fields'])
                    result_dict.update(dynamic_fields)
                except json.JSONDecodeError:
                    logger.warning(f"Не удалось распарсить extracted_fields для {place_id}")

            # Убираем служебные поля
            result_dict.pop('extracted_fields', None)

            return result_dict

        except Exception as e:
            logger.error(f"Ошибка получения данных магазина {place_id}: {e}")
            return None

    async def mark_place_processed(self, place_id: str, status: str = "success") -> None:
        """
        Отмечает place_id как обработанный.

        Args:
            place_id: Google Places ID
            status: Статус обработки ('success', 'error', 'partial')
        """
        try:
            await asyncio.to_thread(self.client.execute, """
                INSERT INTO processed_places (place_id, processed_date, status)
                VALUES""", [(
                    place_id, datetime.now(), status
                )])
        except Exception as e:
            logger.error(f"Ошибка отметки обработки {place_id}: {e}")

    async def log_processing_error(
        self,
        place_id: str,
        error_type: str,
        error_message: str,
        stack_trace: str = ""
    ) -> None:
        """
        Логирует ошибку обработки.

        Args:
            place_id: Google Places ID
            error_type: Тип ошибки
            error_message: Сообщение об ошибке
            stack_trace: Stack trace
        """
        try:
            await asyncio.to_thread(self.client.execute, """
                INSERT INTO processing_errors (
                    place_id, error_type, error_message, error_date, stack_trace
                ) VALUES""", [(
                    place_id, error_type, error_message, datetime.now(), stack_trace
                )])
        except Exception as e:
            logger.error(f"Ошибка логирования ошибки для {place_id}: {e}")


# Глобальный экземпляр клиента
clickhouse_client = ClickHouseDataVaultClient(host="clickhouse")
