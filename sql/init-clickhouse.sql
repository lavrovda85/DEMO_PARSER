-- ClickHouse Multi-Layer Data Architecture
-- Raw Layer: сырые данные из API
-- Core Layer: очищенные данные для аналитики
-- Views: динамические представления для развертывания полей

-- ===========================================
-- HUB LAYER (Business Keys)
-- ===========================================

-- Hub таблица для магазинов (остается без изменений)
CREATE TABLE IF NOT EXISTS places_db.hub_stores (
    store_hash UInt64,                    -- Хэш идентификатора магазина
    place_id String,                      -- Google Places ID
    business_key String,                  -- Бизнес-ключ (название + адрес)
    load_date DateTime,                   -- Дата загрузки
    record_source String                  -- Источник данных
) ENGINE = MergeTree()
ORDER BY (store_hash, load_date)
PARTITION BY toYYYYMM(load_date);

-- ===========================================
-- RAW LAYER (Row Data - большие неразобранные данные)
-- ===========================================

-- Satellite таблица для сырых данных из Google Places API
CREATE TABLE IF NOT EXISTS places_db.sat_store_raw (
    store_hash UInt64,                    -- Ссылка на hub_stores
    load_date DateTime,                   -- Дата загрузки
    hash_diff UInt64,                     -- Хэш изменений сырых данных

    -- Сырые данные как есть (большие JSON объекты)
    raw_data String,                      -- Полный JSON ответ от Google Places API
    api_response String,                  -- Сырой ответ API
    scraping_data String,                 -- Сырые данные веб-скрапинга (если есть)

    record_source String                  -- Источник данных
) ENGINE = MergeTree()
ORDER BY (store_hash, load_date)
PARTITION BY toYYYYMM(load_date);

-- ===========================================
-- ATTRIBUTE SYSTEM (Универсальная система атрибутов)
-- ===========================================

-- Hub таблица атрибутов (справочник всех возможных атрибутов)
CREATE TABLE IF NOT EXISTS places_db.hub_attributes (
    attribute_hash UInt64,                -- Хэш идентификатора атрибута
    attribute_name String,                -- Название атрибута (name, address, phone, etc.)
    attribute_type String,                -- Тип данных (string, number, array, etc.)
    attribute_category String,            -- Категория (basic, contact, location, rating, etc.)
    is_required UInt8,                    -- Обязательный атрибут (1/0)
    load_date DateTime,                   -- Дата загрузки
    record_source String                  -- Источник данных
) ENGINE = MergeTree()
ORDER BY (attribute_hash, load_date)
PARTITION BY toYYYYMM(load_date);

-- Satellite таблица значений атрибутов для магазинов
CREATE TABLE IF NOT EXISTS places_db.sat_store_attributes (
    store_hash UInt64,                    -- Ссылка на hub_stores
    attribute_hash UInt64,                -- Ссылка на hub_attributes
    load_date DateTime,                   -- Дата загрузки
    hash_diff UInt64,                     -- Хэш изменений значения

    -- Значение атрибута
    attribute_value String,               -- Значение (всегда как строка для универсальности)
    attribute_value_type String,          -- Реальный тип значения (string, number, array, json)

    -- Метаданные качества
    confidence_score Float32,             -- Уверенность в значении (0-1)
    validation_status String,             -- Статус валидации ('valid', 'invalid', 'unknown')
    source_type String,                   -- Источник значения ('api', 'scraping', 'derived')

    record_source String                  -- Источник данных
) ENGINE = MergeTree()
ORDER BY (store_hash, attribute_hash, load_date)
PARTITION BY toYYYYMM(load_date);

-- ===========================================
-- CORE LAYER (Представления для аналитики)
-- ===========================================

-- Виртуальная таблица для core данных (сводная информация по магазину)
CREATE VIEW IF NOT EXISTS places_db.vw_store_core AS
SELECT
    hs.place_id,
    hs.business_key as store_name,

    -- Извлекаем значения атрибутов через groupArray
    groupArrayIf(sa.attribute_value, ha.attribute_name = 'name')[1] as name,
    groupArrayIf(sa.attribute_value, ha.attribute_name = 'address')[1] as address,
    groupArrayIf(sa.attribute_value, ha.attribute_name = 'phone')[1] as phone,
    groupArrayIf(sa.attribute_value, ha.attribute_name = 'website')[1] as website,

    -- Координаты (преобразуем в числа)
    toFloat64OrNull(groupArrayIf(sa.attribute_value, ha.attribute_name = 'latitude')[1]) as latitude,
    toFloat64OrNull(groupArrayIf(sa.attribute_value, ha.attribute_name = 'longitude')[1]) as longitude,

    -- Рейтинг и отзывы
    toFloat32OrNull(groupArrayIf(sa.attribute_value, ha.attribute_name = 'rating')[1]) as rating,
    toUInt32OrNull(groupArrayIf(sa.attribute_value, ha.attribute_name = 'user_ratings_total')[1]) as user_ratings_total,

    -- Типы мест (как массив)
    arrayFilter(x -> length(x) > 0, groupArrayIf(sa.attribute_value, ha.attribute_name = 'types')) as types,

    -- Ценовой уровень
    toUInt8OrNull(groupArrayIf(sa.attribute_value, ha.attribute_name = 'price_level')[1]) as price_level,

    -- Метаданные
    max(sa.load_date) as last_updated,
    argMax(sa.record_source, sa.load_date) as record_source

FROM places_db.hub_stores hs
LEFT JOIN places_db.sat_store_attributes sa ON hs.store_hash = sa.store_hash
LEFT JOIN places_db.hub_attributes ha ON sa.attribute_hash = ha.attribute_hash
GROUP BY hs.place_id, hs.business_key, hs.store_hash;

-- ===========================================
-- FIELD-BASED STORAGE (для динамических полей)
-- ===========================================

-- Hub таблица для типов полей (метаданные полей)
CREATE TABLE IF NOT EXISTS places_db.hub_field_types (
    field_type_hash UInt64,               -- Хэш типа поля
    field_type String,                    -- Тип поля (contact, hours, description, etc.)
    field_category String,                -- Категория (basic, enrichment, metadata)
    load_date DateTime,                   -- Дата загрузки
    record_source String                  -- Источник данных
) ENGINE = MergeTree()
ORDER BY (field_type_hash, load_date)
PARTITION BY toYYYYMM(load_date);

-- Satellite таблица для значений динамических полей
CREATE TABLE IF NOT EXISTS places_db.sat_field_values (
    store_hash UInt64,                    -- Ссылка на hub_stores
    field_type_hash UInt64,               -- Ссылка на hub_field_types
    load_date DateTime,                   -- Дата загрузки
    hash_diff UInt64,                     -- Хэш изменений значения

    field_name String,                    -- Название поля
    field_value String,                   -- Значение поля (может быть JSON)
    field_confidence Float32,             -- Уверенность извлечения (0-1)
    is_valid UInt8,                       -- Валидность данных (1/0)

    record_source String                  -- Источник данных
) ENGINE = MergeTree()
ORDER BY (store_hash, field_type_hash, load_date)
PARTITION BY toYYYYMM(load_date);

-- ===========================================
-- METADATA TABLES
-- ===========================================

-- Таблица для отслеживания обработанных place_id
CREATE TABLE IF NOT EXISTS places_db.processed_places (
    place_id String,
    processed_date DateTime,
    status String,                       -- 'raw_loaded', 'core_processed', 'fully_enriched'
    processing_stage String,             -- 'api_fetch', 'web_scraping', 'data_cleaning'
    error_count UInt32                   -- Количество ошибок обработки
) ENGINE = MergeTree()
ORDER BY (place_id, processed_date)
PARTITION BY toYYYYMM(processed_date);

-- Таблица для логирования ошибок обработки
CREATE TABLE IF NOT EXISTS places_db.processing_errors (
    place_id String,
    error_type String,                   -- 'api_error', 'parsing_error', 'validation_error'
    error_message String,
    error_stage String,                  -- 'fetch', 'enrich', 'clean', 'save'
    error_date DateTime,
    stack_trace String,
    retry_count UInt32
) ENGINE = MergeTree()
ORDER BY (error_date, place_id)
PARTITION BY toYYYYMM(error_date);

-- ===========================================
-- DYNAMIC VIEWS (развертывание полей в столбцы)
-- ===========================================

-- Базовое представление: последняя версия данных для каждого магазина
CREATE VIEW IF NOT EXISTS places_db.vw_store_latest AS
SELECT
    hs.place_id,
    hs.business_key as store_name,
    sr.raw_data,
    sr.api_response,
    GREATEST(hs.load_date, sr.load_date) as last_updated
FROM places_db.hub_stores hs
LEFT JOIN places_db.sat_store_raw sr ON hs.store_hash = sr.store_hash;

-- ===========================================
-- MATERIALIZED VIEWS (для производительности)
-- ===========================================

-- MV для быстрого поиска по place_id (упрощенная версия)
CREATE MATERIALIZED VIEW IF NOT EXISTS places_db.mv_store_search
ENGINE = MergeTree()
PARTITION BY toYYYYMM(load_date)
ORDER BY (place_id, load_date)
POPULATE
AS SELECT
    place_id,
    business_key,
    load_date,
    record_source
FROM places_db.hub_stores;

-- Другие MV создаются после тестирования основной функциональности
