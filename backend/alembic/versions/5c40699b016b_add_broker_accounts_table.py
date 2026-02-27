"""add_broker_accounts_table

Revision ID: 5c40699b016b
Revises: c0ec13a8dba6
Create Date: 2026-01-24 08:56:43.292866

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c40699b016b'
down_revision: Union[str, Sequence[str], None] = 'c0ec13a8dba6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('broker_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('broker_name', sa.String(), nullable=False),
        sa.Column('account_id', sa.String(), nullable=True),
        sa.Column('api_key', sa.String(), nullable=True),
        sa.Column('api_secret', sa.String(), nullable=True),
        sa.Column('base_url', sa.String(), nullable=True),
        sa.Column('is_active', sa.Integer(), nullable=True, default=1),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('mt5_path', sa.String(), nullable=True),
        sa.Column('mt5_password', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_broker_accounts_user_id', 'user_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('broker_accounts')
