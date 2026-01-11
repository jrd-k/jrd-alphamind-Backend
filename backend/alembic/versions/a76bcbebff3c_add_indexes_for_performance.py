"""add_indexes_for_performance

Revision ID: a76bcbebff3c
Revises: fb3013f4c4ed
Create Date: 2025-12-26 00:06:28.910328

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a76bcbebff3c'
down_revision: Union[str, Sequence[str], None] = 'fb3013f4c4ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # All planned indexes already exist in the database
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # Indexes already existed, so no need to drop them
    pass
