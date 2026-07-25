"""add language column to stories table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-25 19:09:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add language column to stories table."""
    op.add_column('stories', sa.Column('language', sa.String(), nullable=False, server_default='en'))
    op.create_index(op.f('ix_stories_language'), 'stories', ['language'], unique=False)


def downgrade() -> None:
    """Remove language column from stories table."""
    op.drop_index(op.f('ix_stories_language'), table_name='stories')
    op.drop_column('stories', 'language')