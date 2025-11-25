"""create brain_decisions table

Revision ID: b1a2c3d4e5f6
Revises: 4975dd530ef4
Create Date: 2025-11-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from typing import Union, Sequence


# revision identifiers, used by Alembic.
revision: str = "b1a2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "4975dd530ef4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "brain_decisions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("symbol", sa.String(length=255), nullable=False, index=True),
        sa.Column("decision", sa.String(length=50), nullable=False),
        sa.Column("indicator", sa.JSON, nullable=True),
        sa.Column("deepseek", sa.JSON, nullable=True),
        sa.Column("openai", sa.JSON, nullable=True),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("brain_decisions")
