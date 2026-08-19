"""Add contract type.

Revision ID: 3ff421f34990
Revises: 20260811_01
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "3ff421f34990"
down_revision: str | None = "20260811_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the contract type column."""

    op.add_column(
        "contracts",
        sa.Column(
            "contract_type",
            sa.Enum(
                "default",
                "custom",
                name="contract_type",
            ),
            server_default=sa.text("'custom'"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Remove the contract type column."""

    op.drop_column(
        "contracts",
        "contract_type",
    )