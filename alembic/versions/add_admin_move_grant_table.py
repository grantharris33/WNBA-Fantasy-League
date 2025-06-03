"""add admin move grant table

Revision ID: c3d2e1f4a5b6
Revises: 31e6f5bd5e68
Create Date: 2024-12-28 00:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'c3d2e1f4a5b6'
down_revision = '31e6f5bd5e68'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'admin_move_grant',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('admin_user_id', sa.Integer(), nullable=False),
        sa.Column('moves_granted', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(), nullable=False),
        sa.Column('granted_at', sa.DateTime(), nullable=False),
        sa.Column('week_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['admin_user_id'], ['user.id']),
        sa.ForeignKeyConstraint(['team_id'], ['team.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_admin_move_grant_id'), 'admin_move_grant', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_admin_move_grant_id'), table_name='admin_move_grant')
    op.drop_table('admin_move_grant')