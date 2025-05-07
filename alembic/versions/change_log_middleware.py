"""Add is_admin flag to User and path/method/patch to TransactionLog

Revision ID: d2e8f7a92b1e
Revises: b6b22f877e2a
Create Date: 2024-06-08 14:35:14.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd2e8f7a92b1e'
down_revision: Union[str, None] = 'b6b22f877e2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_admin column to user table with default False
    op.add_column('user', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='0'))

    # Add the new columns to transaction_log table
    op.add_column('transaction_log', sa.Column('path', sa.String(), nullable=True))
    op.add_column('transaction_log', sa.Column('method', sa.String(), nullable=True))
    op.add_column('transaction_log', sa.Column('patch', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove the columns in transaction_log
    op.drop_column('transaction_log', 'patch')
    op.drop_column('transaction_log', 'method')
    op.drop_column('transaction_log', 'path')

    # Remove is_admin column from user table
    op.drop_column('user', 'is_admin')
