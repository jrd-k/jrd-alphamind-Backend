"""add_confidence_to_brain_decisions

Revision ID: c0ec13a8dba6
Revises: a76bcbebff3c
Create Date: 2025-12-26 00:16:07.387557

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0ec13a8dba6'
down_revision: Union[str, Sequence[str], None] = 'a76bcbebff3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add confidence column to brain_decisions table
    op.add_column('brain_decisions', sa.Column('confidence', sa.Float(), nullable=True, default=0.0))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove confidence column from brain_decisions table
    op.drop_column('brain_decisions', 'confidence')
