"""
SQL запросы для работы с базой данных.
"""

# Запросы для работы со stores
CHECK_STORE_EXISTS = "SELECT 1 FROM stores WHERE place_id = $1 LIMIT 1"

UPDATE_STORE = """
UPDATE stores SET
    name = $2, website = $3, phone = $4, address = $5, description = $6,
    updated_at = CURRENT_TIMESTAMP
WHERE place_id = $1
"""

INSERT_STORE = """
INSERT INTO stores (id, name, website, phone, address, place_id, description, created_at, updated_at)
VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
"""

