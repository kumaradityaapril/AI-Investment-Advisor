"""add_name_to_users

Revision ID: e3d8f7a1b2c4
Revises: c562f0167d89
Create Date: 2026-11-14 23:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3d8f7a1b2c4'
down_revision: Union[str, Sequence[str], None] = 'c562f0167d89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add name column to users table."""
    op.add_column('users', sa.Column('name', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema: Remove name column from users table."""
    op.drop_column('users', 'name')

