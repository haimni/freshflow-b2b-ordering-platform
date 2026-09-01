"""Snapshot product names in order items.

Revision ID: c0cbf030baee
Revises: 28cccd78d28f
Create Date: 2026-09-01 15:52:58.270098
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c0cbf030baee"
down_revision: str | None = "28cccd78d28f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add and populate the product-name snapshot."""

    op.add_column(
        "order_items",
        sa.Column(
            "product_name",
            sa.String(length=150),
            nullable=True,
        ),
    )

    op.execute(
        sa.text(
            """
            UPDATE order_items AS order_item
            INNER JOIN products AS product
                ON product.id = order_item.product_id
            SET order_item.product_name = product.name
            WHERE order_item.product_name IS NULL
            """
        )
    )

    op.alter_column(
        "order_items",
        "product_name",
        existing_type=sa.String(length=150),
        nullable=False,
    )


def downgrade() -> None:
    """Remove the product-name snapshot."""

    op.drop_column(
        "order_items",
        "product_name",
    )