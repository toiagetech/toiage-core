"""change learning_style column to JSON

Revision ID: a1b2c3d4e5f6
Revises: 93a8be9fd172
Create Date: 2026-07-19 16:09:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '93a8be9fd172'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: change children.learning_style from VARCHAR to JSON."""
    # SQLite doesn't support ALTER COLUMN type directly, so we use batch mode.
    with op.batch_alter_table('children', schema=None) as batch_op:
        batch_op.alter_column(
            'learning_style',
            existing_type=sqlmodel.sql.sqltypes.AutoString(),
            type_=sa.JSON(),
            existing_nullable=True,
            postgresql_using='NULL',
        )


def downgrade() -> None:
    """Downgrade schema: change children.learning_style back to VARCHAR."""
    with op.batch_alter_table('children', schema=None) as batch_op:
        batch_op.alter_column(
            'learning_style',
            existing_type=sa.JSON(),
            type_=sqlmodel.sql.sqltypes.AutoString(),
            existing_nullable=True,
        )