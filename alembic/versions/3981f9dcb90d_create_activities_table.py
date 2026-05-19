"""create activities table

Revision ID: 3981f9dcb90d
Revises: e45d157ca814
Create Date: 2026-05-19 08:41:23.102134

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3981f9dcb90d'
down_revision: Union[str, Sequence[str], None] = 'e45d157ca814'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('activities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('story_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('materials', sa.String(), nullable=False),
        sa.Column('instructions', sa.String(), nullable=False),
        sa.Column('challenge_question', sa.String(), nullable=False),
        sa.Column('age_group', sa.String(), nullable=False),
        sa.Column('activity_mode', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activities_age_group'), 'activities', ['age_group'], unique=False)
    op.create_index(op.f('ix_activities_story_id'), 'activities', ['story_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_activities_story_id'), table_name='activities')
    op.drop_index(op.f('ix_activities_age_group'), table_name='activities')
    op.drop_table('activities')