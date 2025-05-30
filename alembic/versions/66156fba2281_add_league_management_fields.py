"""Add league management fields

Revision ID: 66156fba2281
Revises: 4a615af8fb1f
Create Date: 2024-01-01 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '66156fba2281'
down_revision = '4a615af8fb1f'
branch_labels = None
depends_on = None


def upgrade():
    # Get connection and inspector
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('league')]

    # Add columns only if they don't exist
    if 'invite_code' not in columns:
        op.add_column('league', sa.Column('invite_code', sa.String(), nullable=True))
    if 'max_teams' not in columns:
        op.add_column('league', sa.Column('max_teams', sa.Integer(), nullable=False, default=12))
    if 'draft_date' not in columns:
        op.add_column('league', sa.Column('draft_date', sa.DateTime(), nullable=True))
    if 'settings' not in columns:
        op.add_column('league', sa.Column('settings', sa.JSON(), nullable=True))
    if 'is_active' not in columns:
        op.add_column('league', sa.Column('is_active', sa.Boolean(), nullable=False, default=True))

    # Update existing rows to have unique invite codes
    op.execute("UPDATE league SET invite_code = 'LEAGUE-' || SUBSTR('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', ABS(RANDOM()) % 36 + 1, 1) || SUBSTR('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', ABS(RANDOM()) % 36 + 1, 1) || SUBSTR('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', ABS(RANDOM()) % 36 + 1, 1) || SUBSTR('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', ABS(RANDOM()) % 36 + 1, 1) || '-' || SUBSTR('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', ABS(RANDOM()) % 36 + 1, 1) || SUBSTR('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', ABS(RANDOM()) % 36 + 1, 1) || SUBSTR('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', ABS(RANDOM()) % 36 + 1, 1) || SUBSTR('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', ABS(RANDOM()) % 36 + 1, 1) WHERE invite_code IS NULL")

    # Now make invite_code NOT NULL and add unique constraint
    with op.batch_alter_table('league', schema=None) as batch_op:
        batch_op.alter_column('invite_code', nullable=False)
        batch_op.create_unique_constraint('uq_league_invite_code', ['invite_code'])


def downgrade():
    with op.batch_alter_table('league', schema=None) as batch_op:
        batch_op.drop_constraint('uq_league_invite_code', type_='unique')

    op.drop_column('league', 'is_active')
    op.drop_column('league', 'settings')
    op.drop_column('league', 'draft_date')
    op.drop_column('league', 'max_teams')
    op.drop_column('league', 'invite_code')