"""Add user profile and preferences models

Revision ID: 08407d878e2c
Revises: 3d3393ec9a95
Create Date: 2025-01-06 14:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '08407d878e2c'
down_revision = '3d3393ec9a95'
branch_labels = None
depends_on = None


def upgrade():
    # Create user_profile table
    op.create_table(
        'user_profile',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('email_verification_token', sa.String(length=255), nullable=True),
        sa.Column('email_verification_sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index(op.f('ix_user_profile_id'), 'user_profile', ['id'], unique=False)
    op.create_index(op.f('ix_user_profile_user_id'), 'user_profile', ['user_id'], unique=True)

    # Create user_preferences table
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('theme', sa.String(length=20), nullable=False, server_default='light'),
        sa.Column('accent_color', sa.String(length=7), nullable=True),
        sa.Column('email_notifications', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('email_draft_reminders', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('email_trade_offers', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('email_league_updates', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('email_weekly_summary', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('dashboard_layout', sa.JSON(), nullable=True),
        sa.Column('default_league_id', sa.Integer(), nullable=True),
        sa.Column('show_player_photos', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('favorite_team_ids', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('profile_visibility', sa.String(length=20), nullable=False, server_default='public'),
        sa.Column('show_email', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('show_stats', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['default_league_id'], ['league.id']),
        sa.ForeignKeyConstraint(['profile_id'], ['user_profile.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('profile_id'),
    )
    op.create_index(op.f('ix_user_preferences_id'), 'user_preferences', ['id'], unique=False)
    op.create_index(op.f('ix_user_preferences_profile_id'), 'user_preferences', ['profile_id'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_user_preferences_profile_id'), table_name='user_preferences')
    op.drop_index(op.f('ix_user_preferences_id'), table_name='user_preferences')
    op.drop_table('user_preferences')
    op.drop_index(op.f('ix_user_profile_user_id'), table_name='user_profile')
    op.drop_index(op.f('ix_user_profile_id'), table_name='user_profile')
    op.drop_table('user_profile')
