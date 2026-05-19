"""create stories table

Revision ID: e45d157ca814
Revises: 0ca9298f53de
Create Date: 2026-05-19 08:29:18.152942

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e45d157ca814'
down_revision: Union[str, Sequence[str], None] = '0ca9298f53de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('stories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('age_group', sa.String(), nullable=False),
        sa.Column('theme', sa.String(), nullable=False),
        sa.Column('skills', sa.String(), nullable=False),
        sa.Column('difficulty', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stories_age_group'), 'stories', ['age_group'], unique=False)
    op.create_index(op.f('ix_stories_theme'), 'stories', ['theme'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_stories_theme'), table_name='stories')
    op.drop_index(op.f('ix_stories_age_group'), table_name='stories')
    op.drop_table('stories')