"""Merge migration heads

Revision ID: feda888bea0d
Revises: c3d2e1f4a5b6, add_data_quality_monitoring_models
Create Date: 2025-01-06 12:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'feda888bea0d'
down_revision = ('c3d2e1f4a5b6', 'add_data_quality_monitoring_models')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
