"""Add inventory adjustments.

Revision ID: b39f20f114c5
Revises: c0cbf030baee
Create Date: 2026-09-06 15:37:31.014031
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision: str = "b39f20f114c5"
down_revision: str | None = "c0cbf030baee"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the manual inventory-adjustment ledger."""

    op.create_table(
        "inventory_adjustments",
        sa.Column(
            "id",
            mysql.BIGINT(unsigned=True),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            mysql.BIGINT(unsigned=True),
            nullable=False,
        ),
        sa.Column(
            "performed_by_user_id",
            mysql.BIGINT(unsigned=True),
            nullable=False,
        ),
        sa.Column(
            "quantity_change",
            sa.Numeric(12, 3),
            nullable=False,
        ),
        sa.Column(
            "stock_before",
            sa.Numeric(12, 3),
            nullable=False,
        ),
        sa.Column(
            "stock_after",
            sa.Numeric(12, 3),
            nullable=False,
        ),
        sa.Column(
            "reason",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            mysql.TIMESTAMP(),
            server_default=sa.text(
                "CURRENT_TIMESTAMP"
            ),
            nullable=False,
        ),
        sa.CheckConstraint(
            "quantity_change <> 0",
            name=(
                "chk_inventory_adjustments_"
                "quantity_change"
            ),
        ),
        sa.CheckConstraint(
            "stock_before >= 0",
            name=(
                "chk_inventory_adjustments_"
                "stock_before"
            ),
        ),
        sa.CheckConstraint(
            "stock_after >= 0",
            name=(
                "chk_inventory_adjustments_"
                "stock_after"
            ),
        ),
        sa.CheckConstraint(
            "stock_after = stock_before + quantity_change",
            name=(
                "chk_inventory_adjustments_"
                "stock_balance"
            ),
        ),
        sa.CheckConstraint(
            "CHAR_LENGTH(TRIM(reason)) > 0",
            name=(
                "chk_inventory_adjustments_"
                "reason"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=(
                "fk_inventory_adjustments_"
                "product"
            ),
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["performed_by_user_id"],
            ["users.id"],
            name=(
                "fk_inventory_adjustments_"
                "performed_by_user"
            ),
            onupdate="RESTRICT",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_inventory_adjustments",
        ),
    )

    op.create_index(
        "idx_inventory_adjustments_product_id",
        "inventory_adjustments",
        ["product_id"],
        unique=False,
    )

    op.create_index(
        "idx_inventory_adjustments_performed_by_user_id",
        "inventory_adjustments",
        ["performed_by_user_id"],
        unique=False,
    )

    op.create_index(
        "idx_inventory_adjustments_created_at",
        "inventory_adjustments",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the manual inventory-adjustment ledger."""

    op.drop_index(
        "idx_inventory_adjustments_created_at",
        table_name="inventory_adjustments",
    )

    op.drop_index(
        "idx_inventory_adjustments_performed_by_user_id",
        table_name="inventory_adjustments",
    )

    op.drop_index(
        "idx_inventory_adjustments_product_id",
        table_name="inventory_adjustments",
    )

    op.drop_table("inventory_adjustments")