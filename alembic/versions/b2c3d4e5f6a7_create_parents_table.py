"""create parents table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-19 16:24:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create parents table."""
    op.create_table(
        'parents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('mobile_number', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('preferred_language', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('avatar_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('mobile_number'),
    )
    op.create_index(op.f('ix_parents_email'), 'parents', ['email'], unique=True)
    op.create_index(op.f('ix_parents_mobile_number'), 'parents', ['mobile_number'], unique=True)


def downgrade() -> None:
    """Downgrade schema: drop parents table."""
    op.drop_index(op.f('ix_parents_mobile_number'), table_name='parents')
    op.drop_index(op.f('ix_parents_email'), table_name='parents')
    op.drop_table('parents')