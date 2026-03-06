"""add_kimi_column_to_brain_decisions

Revision ID: ea232c9401d6
Revises: 5c40699b016b
Create Date: 2026-03-06 14:48:10.244728

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea232c9401d6'
down_revision: Union[str, Sequence[str], None] = '5c40699b016b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add kimi column to brain_decisions table
    op.add_column('brain_decisions', sa.Column('kimi', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove kimi column from brain_decisions table
    op.drop_column('brain_decisions', 'kimi')
