"""Create the initial FreshFlow database schema."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision: str = "20260811_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamp_columns() -> tuple[sa.Column, sa.Column]:
    """Return the shared created/updated timestamp columns."""
    return (
        sa.Column(
            "created_at",
            mysql.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            mysql.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("company_name", sa.String(length=150), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("business_number", sa.String(length=30), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("business_number", name="uq_customers_business_number"),
    )

    op.create_table(
        "categories",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_categories_name"),
    )

    op.create_table(
        "users",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("customer_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            mysql.ENUM("admin", "customer_manager", "customer_user", name="user_role"),
            nullable=False,
        ),
        sa.Column("active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint(
            "(role = 'admin' AND customer_id IS NULL) OR "
            "(role IN ('customer_manager', 'customer_user') AND customer_id IS NOT NULL)",
            name="chk_users_role_customer",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            name="fk_users_customer",
            onupdate="RESTRICT",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("idx_users_customer_id", "users", ["customer_id"])
    op.create_index("idx_users_role", "users", ["role"])

    op.create_table(
        "products",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("category_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("default_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("stock", sa.Numeric(12, 3), server_default=sa.text("0"), nullable=False),
        sa.Column("image_url", sa.String(length=2048), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint("default_price >= 0", name="chk_products_default_price"),
        sa.CheckConstraint("stock >= 0", name="chk_products_stock"),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name="fk_products_category",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_products_active", "products", ["active"])
    op.create_index("idx_products_category_id", "products", ["category_id"])

    op.create_table(
        "contracts",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("customer_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("contract_name", sa.String(length=150), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint(
            "valid_until IS NULL OR valid_until >= valid_from",
            name="chk_contracts_dates",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customers.id"],
            name="fk_contracts_customer", onupdate="CASCADE", ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_contracts_customer_active", "contracts", ["customer_id", "active"])
    op.create_index("idx_contracts_customer_id", "contracts", ["customer_id"])

    op.create_table(
        "contract_prices",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("contract_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("product_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint("price >= 0", name="chk_contract_prices_price"),
        sa.ForeignKeyConstraint(
            ["contract_id"], ["contracts.id"],
            name="fk_contract_prices_contract", onupdate="CASCADE", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"],
            name="fk_contract_prices_product", onupdate="CASCADE", ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "contract_id", "product_id", name="uq_contract_prices_contract_product"
        ),
    )
    op.create_index("idx_contract_prices_product_id", "contract_prices", ["product_id"])

    op.create_table(
        "orders",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("customer_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("created_by_user_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "status",
            mysql.ENUM(
                "pending", "confirmed", "processing", "completed", "cancelled",
                name="order_status",
            ),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        *timestamp_columns(),
        sa.CheckConstraint("total >= 0", name="chk_orders_total"),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.id"],
            name="fk_orders_created_by_user", onupdate="CASCADE", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customers.id"],
            name="fk_orders_customer", onupdate="CASCADE", ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_orders_created_at", "orders", ["created_at"])
    op.create_index("idx_orders_created_by_user_id", "orders", ["created_by_user_id"])
    op.create_index("idx_orders_customer_id", "orders", ["customer_id"])
    op.create_index("idx_orders_status", "orders", ["status"])

    op.create_table(
        "order_items",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("order_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("product_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(12, 2), nullable=False),
        sa.CheckConstraint("line_total >= 0", name="chk_order_items_line_total"),
        sa.CheckConstraint("quantity > 0", name="chk_order_items_quantity"),
        sa.CheckConstraint("unit_price >= 0", name="chk_order_items_unit_price"),
        sa.ForeignKeyConstraint(
            ["order_id"], ["orders.id"],
            name="fk_order_items_order", onupdate="CASCADE", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"],
            name="fk_order_items_product", onupdate="CASCADE", ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id", "product_id", name="uq_order_items_order_product"),
    )
    op.create_index("idx_order_items_product_id", "order_items", ["product_id"])


def downgrade() -> None:
    op.drop_index("idx_order_items_product_id", table_name="order_items")
    op.drop_table("order_items")
    op.drop_index("idx_orders_status", table_name="orders")
    op.drop_index("idx_orders_customer_id", table_name="orders")
    op.drop_index("idx_orders_created_by_user_id", table_name="orders")
    op.drop_index("idx_orders_created_at", table_name="orders")
    op.drop_table("orders")
    op.drop_index("idx_contract_prices_product_id", table_name="contract_prices")
    op.drop_table("contract_prices")
    op.drop_index("idx_contracts_customer_id", table_name="contracts")
    op.drop_index("idx_contracts_customer_active", table_name="contracts")
    op.drop_table("contracts")
    op.drop_index("idx_products_category_id", table_name="products")
    op.drop_index("idx_products_active", table_name="products")
    op.drop_table("products")
    op.drop_index("idx_users_role", table_name="users")
    op.drop_index("idx_users_customer_id", table_name="users")
    op.drop_table("users")
    op.drop_table("categories")
    op.drop_table("customers")