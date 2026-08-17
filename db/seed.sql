-- =============================================================================
-- FreshFlow B2B Ordering Platform - Development Seed
-- Run only after: python -m alembic upgrade head
-- Development data only. Do not use real customer information.
-- =============================================================================

USE freshflow_b2b;

SET NAMES utf8mb4;

START TRANSACTION;

-- -----------------------------------------------------------------------------
-- 1. Categories
-- -----------------------------------------------------------------------------

INSERT INTO categories (
    id,
    name,
    description,
    active
)
VALUES
    (
        1,
        'ירקות',
        'ירקות טריים המסופקים לעסקים',
        TRUE
    ),
    (
        2,
        'פירות',
        'פירות עונתיים וטריים',
        TRUE
    )
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    description = VALUES(description),
    active = VALUES(active);

-- -----------------------------------------------------------------------------
-- 2. Products
-- -----------------------------------------------------------------------------

INSERT INTO products (
    id,
    category_id,
    name,
    description,
    default_price,
    stock,
    image_url,
    active
)
VALUES
    (
        1,
        1,
        'עגבניות',
        'עגבניות טריות, מחיר לקילוגרם',
        8.90,
        250.000,
        NULL,
        TRUE
    ),
    (
        2,
        1,
        'מלפפונים',
        'מלפפונים טריים, מחיר לקילוגרם',
        7.50,
        180.000,
        NULL,
        TRUE
    ),
    (
        3,
        2,
        'תפוחים',
        'תפוחים טריים, מחיר לקילוגרם',
        11.90,
        120.000,
        NULL,
        TRUE
    )
ON DUPLICATE KEY UPDATE
    category_id = VALUES(category_id),
    name = VALUES(name),
    description = VALUES(description),
    default_price = VALUES(default_price),
    stock = VALUES(stock),
    image_url = VALUES(image_url),
    active = VALUES(active);

-- -----------------------------------------------------------------------------
-- 3. Customer
-- -----------------------------------------------------------------------------

INSERT INTO customers (
    id,
    company_name,
    phone,
    business_number,
    active
)
VALUES
    (
        1,
        'מסעדת הגן בע"מ',
        '02-555-0101',
        '515000001',
        TRUE
    )
ON DUPLICATE KEY UPDATE
    company_name = VALUES(company_name),
    phone = VALUES(phone),
    business_number = VALUES(business_number),
    active = VALUES(active);

-- -----------------------------------------------------------------------------
-- 4. Users
-- Passwords are placeholders until authentication and password hashing exist.
-- -----------------------------------------------------------------------------

INSERT INTO users (
    id,
    customer_id,
    name,
    email,
    password_hash,
    role,
    active
)
VALUES
    (
        1,
        NULL,
        'מנהל מערכת',
        'admin@example.com',
        'NOT_A_REAL_PASSWORD_HASH',
        'admin',
        TRUE
    ),
    (
        2,
        1,
        'נועה כהן',
        'manager@example.com',
        'NOT_A_REAL_PASSWORD_HASH',
        'customer_manager',
        TRUE
    ),
    (
        3,
        1,
        'דניאל לוי',
        'buyer@example.com',
        'NOT_A_REAL_PASSWORD_HASH',
        'customer_user',
        TRUE
    )
ON DUPLICATE KEY UPDATE
    customer_id = VALUES(customer_id),
    name = VALUES(name),
    email = VALUES(email),
    password_hash = VALUES(password_hash),
    role = VALUES(role),
    active = VALUES(active);

-- -----------------------------------------------------------------------------
-- 5. Contract
-- -----------------------------------------------------------------------------

INSERT INTO contracts (
    id,
    customer_id,
    contract_name,
    valid_from,
    valid_until,
    active
)
VALUES
    (
        1,
        1,
        'הסכם מסחרי לדוגמה',
        '2026-01-01',
        '2026-12-31',
        TRUE
    )
ON DUPLICATE KEY UPDATE
    customer_id = VALUES(customer_id),
    contract_name = VALUES(contract_name),
    valid_from = VALUES(valid_from),
    valid_until = VALUES(valid_until),
    active = VALUES(active);

-- -----------------------------------------------------------------------------
-- 6. Negotiated contract prices
-- -----------------------------------------------------------------------------

INSERT INTO contract_prices (
    id,
    contract_id,
    product_id,
    price
)
VALUES
    (
        1,
        1,
        1,
        7.90
    ),
    (
        2,
        1,
        2,
        6.80
    )
ON DUPLICATE KEY UPDATE
    contract_id = VALUES(contract_id),
    product_id = VALUES(product_id),
    price = VALUES(price);

COMMIT;