"""Add Files Table

Revision ID: 865c82738fac
Revises: 8a940f3fdf72
Create Date: 2026-01-08 14:18:40.895075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '865c82738fac'
down_revision: Union[str, Sequence[str], None] = '8a940f3fdf72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'files',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('logical_name', sa.String(), nullable=False),
        sa.Column('is_directory', sa.Boolean(), nullable=True),
        sa.Column('hash', sa.String(length=128), nullable=True),
        sa.Column('mime_type', sa.String(), nullable=True),
        sa.Column('size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['files.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # unique partial index with parent_id
    op.create_index(
        'ix_unique_active_file_per_user_folder',
        'files',
        [
            'user_id',
            sa.text(
                "COALESCE(parent_id, '00000000-0000-0000-0000-000000000000')"
            ),
            'hash',
            'logical_name',
        ],
        unique=True,
        postgresql_where=sa.text(
            "status = 'active' AND is_directory = false"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        'ix_unique_active_file_per_user_folder',
        table_name='files',
    )
    op.drop_table('files')
