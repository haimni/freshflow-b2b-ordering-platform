-- =============================================================================
-- FreshFlow B2B Ordering Platform - Database Schema
-- =============================================================================
-- Purpose:
--   Creates the MySQL database structure for business customers, their users,
--   products, contracts, negotiated prices, orders, and order items.
--
-- Environment: MySQL 8.0+ using utf8mb4 for Hebrew and full Unicode support.
--
-- Main model decision:
--   One customer represents one business organization. A customer can have
--   many users; each customer user belongs to exactly one customer. Internal
--   administrators do not belong to a customer.
--
-- Execution:
--   Run this file before db/seed.sql. Tables are intentionally created in
--   dependency order. Future structural changes should use migrations.
-- =============================================================================

-- =============================================================================
-- 1. DATABASE INITIALIZATION
-- Creates the database and selects it for all statements that follow.
-- =============================================================================

CREATE DATABASE IF NOT EXISTS freshflow_b2b
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE freshflow_b2b;

-- =============================================================================
-- 2. CUSTOMERS
-- Purpose: stores the business organizations that purchase through FreshFlow.
-- Relationship: one customer can own many users, contracts, and orders.
-- =============================================================================

CREATE TABLE customers (
    -- Primary identifier
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    -- Business details
    company_name VARCHAR(150) NOT NULL,
    phone VARCHAR(30) NULL,
    business_number VARCHAR(30) NOT NULL,

    -- Soft-delete / availability flag
    active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Audit timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- A registered business number may identify only one customer.
    CONSTRAINT uq_customers_business_number UNIQUE (business_number)
) ENGINE=InnoDB;

-- =============================================================================
-- 3. USERS
-- Purpose: stores authenticated people who use the platform.
-- Roles: admin / customer_manager / customer_user.
-- Relationship: many customer users can belong to one customer.
-- Important: customer_id is NULL only for internal administrators.
-- =============================================================================

CREATE TABLE users (
    -- Primary identifier and owning organization
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    customer_id BIGINT UNSIGNED NULL,

    -- Authentication identity
    name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,

    -- Authorization and account state
    role ENUM('admin', 'customer_manager', 'customer_user') NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Audit timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Uniqueness and relationships
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT fk_users_customer
        FOREIGN KEY (customer_id) REFERENCES customers(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_users_role_customer CHECK (
        (role = 'admin' AND customer_id IS NULL)
        OR
        (role IN ('customer_manager', 'customer_user') AND customer_id IS NOT NULL)
    ),

    -- Query-supporting indexes
    INDEX idx_users_customer_id (customer_id),
    INDEX idx_users_role (role)
) ENGINE=InnoDB;

-- =============================================================================
-- 4. CATEGORIES
-- Purpose: groups products for catalog navigation and administration.
-- Relationship: one category can contain many products.
-- =============================================================================

CREATE TABLE categories (
    -- Primary identifier
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    -- Category content
    name VARCHAR(120) NOT NULL,
    description TEXT NULL,

    -- State and audit timestamps
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_categories_name UNIQUE (name)
) ENGINE=InnoDB;

-- =============================================================================
-- 5. PRODUCTS
-- Purpose: stores sellable catalog items, stock, and fallback prices.
-- Pricing rule: default_price is used when no contract price exists.
-- Quantity rule: DECIMAL stock supports products sold in fractional units.
-- =============================================================================

CREATE TABLE products (
    -- Primary identifier and category relationship
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    category_id BIGINT UNSIGNED NOT NULL,

    -- Product content
    name VARCHAR(150) NOT NULL,
    description TEXT NULL,

    -- Commercial and inventory data
    default_price DECIMAL(10, 2) NOT NULL,
    stock DECIMAL(12, 3) NOT NULL DEFAULT 0,
    image_url VARCHAR(2048) NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Audit timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_products_category
        FOREIGN KEY (category_id) REFERENCES categories(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_products_default_price CHECK (default_price >= 0),
    CONSTRAINT chk_products_stock CHECK (stock >= 0),
    INDEX idx_products_category_id (category_id),
    INDEX idx_products_active (active)
) ENGINE=InnoDB;

-- =============================================================================
-- 6. CONTRACTS
-- Purpose: stores dated commercial agreements with business customers.
-- Relationship: one customer may have multiple historical contracts.
-- =============================================================================

CREATE TABLE contracts (
    -- Primary identifier and customer relationship
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    customer_id BIGINT UNSIGNED NOT NULL,

    -- Contract identity and validity period
    contract_name VARCHAR(150) NOT NULL,
    valid_from DATE NOT NULL,
    valid_until DATE NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_contracts_customer
        FOREIGN KEY (customer_id) REFERENCES customers(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_contracts_dates CHECK (
        valid_until IS NULL OR valid_until >= valid_from
    ),
    INDEX idx_contracts_customer_id (customer_id),
    INDEX idx_contracts_customer_active (customer_id, active)
) ENGINE=InnoDB;

-- =============================================================================
-- 7. CONTRACT PRICES
-- Purpose: stores product-specific price overrides within a contract.
-- Rule: a contract can define only one price for a given product.
-- =============================================================================

CREATE TABLE contract_prices (
    -- Primary identifier and relationships
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    contract_id BIGINT UNSIGNED NOT NULL,
    product_id BIGINT UNSIGNED NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_contract_prices_contract_product UNIQUE (contract_id, product_id),
    CONSTRAINT fk_contract_prices_contract
        FOREIGN KEY (contract_id) REFERENCES contracts(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_contract_prices_product
        FOREIGN KEY (product_id) REFERENCES products(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_contract_prices_price CHECK (price >= 0),
    INDEX idx_contract_prices_product_id (product_id)
) ENGINE=InnoDB;

-- =============================================================================
-- 8. ORDERS
-- Purpose: stores order headers, ownership, creator, status, and total.
-- Security rule: the service layer must verify that created_by_user_id belongs
-- to the same customer stored in customer_id.
-- =============================================================================

CREATE TABLE orders (
    -- Primary identifier and ownership
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    customer_id BIGINT UNSIGNED NOT NULL,
    created_by_user_id BIGINT UNSIGNED NOT NULL,
    -- Financial total and workflow state
    total DECIMAL(12, 2) NOT NULL,
    status ENUM('pending', 'confirmed', 'processing', 'completed', 'cancelled')
        NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id) REFERENCES customers(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_orders_created_by_user
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_orders_total CHECK (total >= 0),
    INDEX idx_orders_customer_id (customer_id),
    INDEX idx_orders_created_by_user_id (created_by_user_id),
    INDEX idx_orders_status (status),
    INDEX idx_orders_created_at (created_at)
) ENGINE=InnoDB;

-- =============================================================================
-- 9. ORDER ITEMS
-- Purpose: stores the products, quantities, and prices within each order.
-- Snapshot rule: unit_price and line_total remain unchanged when catalog or
-- contract prices are updated later.
-- =============================================================================

CREATE TABLE order_items (
    -- Primary identifier and relationships
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT UNSIGNED NOT NULL,
    product_id BIGINT UNSIGNED NOT NULL,
    -- Historical quantity and price snapshot
    quantity DECIMAL(12, 3) NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    line_total DECIMAL(12, 2) NOT NULL,
    CONSTRAINT uq_order_items_order_product UNIQUE (order_id, product_id),
    CONSTRAINT fk_order_items_order
        FOREIGN KEY (order_id) REFERENCES orders(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_order_items_product
        FOREIGN KEY (product_id) REFERENCES products(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_order_items_quantity CHECK (quantity > 0),
    CONSTRAINT chk_order_items_unit_price CHECK (unit_price >= 0),
    CONSTRAINT chk_order_items_line_total CHECK (line_total >= 0),
    INDEX idx_order_items_product_id (product_id)
) ENGINE=InnoDB;

-- =============================================================================
-- End of schema. Next step: run db/seed.sql for development sample data.
-- =============================================================================
