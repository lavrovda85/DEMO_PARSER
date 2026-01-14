"""
Data Vault схема для ClickHouse.

Определяет Hub, Satellite и Link таблицы для хранения данных о магазинах.
"""

# SQL для создания Data Vault таблиц в ClickHouse
DATAVAULT_SCHEMA = """
-- Hub таблица для магазинов
CREATE TABLE IF NOT EXISTS hub_stores (
    store_hash UInt64,                    -- Хэш идентификатора магазина
    place_id String,                      -- Google Places ID
    business_key String,                  -- Бизнес-ключ (название + адрес)
    load_date DateTime,                   -- Дата загрузки
    record_source String                  -- Источник данных
) ENGINE = MergeTree()
ORDER BY (store_hash, load_date)
PARTITION BY toYYYYMM(load_date);

-- Satellite таблица для атрибутов магазинов
CREATE TABLE IF NOT EXISTS sat_store_attributes (
    store_hash UInt64,                    -- Ссылка на hub
    load_date DateTime,                   -- Дата загрузки
    hash_diff UInt64,                     -- Хэш изменений атрибутов

    -- Атрибуты магазина
    name String,
    address String,
    phone String,
    website String,
    latitude Float64,
    longitude Float64,
    rating Float32,
    user_ratings_total UInt32,
    types Array(String),
    price_level UInt8,

    -- Динамические поля (JSON для расширяемости)
    extracted_fields String,              -- JSON с извлеченными полями

    record_source String                  -- Источник данных
) ENGINE = MergeTree()
ORDER BY (store_hash, load_date)
PARTITION BY toYYYYMM(load_date);

-- Hub таблица для полей данных
CREATE TABLE IF NOT EXISTS hub_fields (
    field_hash UInt64,                    -- Хэш идентификатора поля
    field_name String,                    -- Название поля
    field_type String,                    -- Тип поля (description, contact, etc.)
    load_date DateTime,                   -- Дата загрузки
    record_source String                  -- Источник данных
) ENGINE = MergeTree()
ORDER BY (field_hash, load_date)
PARTITION BY toYYYYMM(load_date);

-- Satellite таблица для значений полей
CREATE TABLE IF NOT EXISTS sat_field_values (
    field_hash UInt64,                    -- Ссылка на hub_fields
    store_hash UInt64,                    -- Ссылка на hub_stores
    load_date DateTime,                   -- Дата загрузки
    hash_diff UInt64,                     -- Хэш изменений значения

    field_value String,                   -- Значение поля
    is_active UInt8,                      -- Активность записи (1/0)

    record_source String                  -- Источник данных
) ENGINE = MergeTree()
ORDER BY (field_hash, store_hash, load_date)
PARTITION BY toYYYYMM(load_date);

-- Link таблица для связи магазины-поле
CREATE TABLE IF NOT EXISTS link_store_fields (
    store_hash UInt64,                    -- Ссылка на hub_stores
    field_hash UInt64,                    -- Ссылка на hub_fields
    load_date DateTime,                   -- Дата загрузки
    record_source String                  -- Источник данных
) ENGINE = MergeTree()
ORDER BY (store_hash, field_hash, load_date)
PARTITION BY toYYYYMM(load_date);

-- Представление для удобного чтения данных (последняя версия для каждого магазина)
CREATE VIEW IF NOT EXISTS vw_store_data AS
SELECT
    hs.place_id,
    hs.business_key as store_name,
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
    sa.extracted_fields,
    sa.load_date as last_updated
FROM hub_stores hs
LEFT JOIN sat_store_attributes sa ON hs.store_hash = sa.store_hash
ORDER BY hs.store_hash, sa.load_date DESC;
"""

# SQL для создания вспомогательных таблиц
AUXILIARY_TABLES = """
-- Таблица для отслеживания обработанных place_id
CREATE TABLE IF NOT EXISTS processed_places (
    place_id String,
    processed_date DateTime,
    status String                    -- 'success', 'error', 'partial'
) ENGINE = MergeTree()
ORDER BY (place_id, processed_date)
PARTITION BY toYYYYMM(processed_date);

-- Таблица для логирования ошибок
CREATE TABLE IF NOT EXISTS processing_errors (
    place_id String,
    error_type String,
    error_message String,
    error_date DateTime,
    stack_trace String
) ENGINE = MergeTree()
ORDER BY (error_date, place_id)
PARTITION BY toYYYYMM(error_date);
"""

# SQL для создания индексов и материализованных представлений
OPTIMIZATION_QUERIES = """
-- Материализованное представление для быстрого поиска по place_id
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_store_search
ENGINE = MergeTree()
PARTITION BY toYYYYMM(load_date)
ORDER BY (place_id, load_date)
POPULATE
AS SELECT
    place_id,
    business_key,
    load_date,
    record_source
FROM hub_stores;

-- Материализованное представление для статистики по полям
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_field_stats
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(load_date)
ORDER BY (field_name, load_date)
AS SELECT
    field_name,
    load_date,
    count() as field_count,
    countIf(length(field_value) > 0) as non_empty_count
FROM hub_fields hf
LEFT JOIN sat_field_values sfv ON hf.field_hash = sfv.field_hash
GROUP BY field_name, load_date;
"""

# Полный SQL для инициализации схемы
INIT_SCHEMA_SQL = DATAVAULT_SCHEMA + AUXILIARY_TABLES + OPTIMIZATION_QUERIES


def get_init_queries() -> str:
    """
    Возвращает полный SQL для инициализации Data Vault схемы.

    Returns:
        SQL скрипт для создания всех таблиц
    """
    return INIT_SCHEMA_SQL


def get_drop_queries() -> str:
    """
    Возвращает SQL для удаления всех Data Vault таблиц.

    Returns:
        SQL скрипт для удаления всех таблиц
    """
    return """
    DROP VIEW IF EXISTS vw_store_data;
    DROP VIEW IF EXISTS mv_field_stats;
    DROP VIEW IF EXISTS mv_store_search;
    DROP TABLE IF EXISTS link_store_fields;
    DROP TABLE IF EXISTS sat_field_values;
    DROP TABLE IF EXISTS hub_fields;
    DROP TABLE IF EXISTS sat_store_attributes;
    DROP TABLE IF EXISTS hub_stores;
    DROP TABLE IF EXISTS processed_places;
    DROP TABLE IF EXISTS processing_errors;
    """
