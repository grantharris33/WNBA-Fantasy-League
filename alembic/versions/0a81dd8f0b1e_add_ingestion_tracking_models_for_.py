"""Add ingestion tracking models for backfill system

Revision ID: 0a81dd8f0b1e
Revises: f7d1b34e5a2c
Create Date: 2024-01-15 10:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '0a81dd8f0b1e'
down_revision = '6bb0a33ec1ca'
branch_labels = None
depends_on = None


def upgrade():
    # Create ingestion_run table
    op.create_table(
        'ingestion_run',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('target_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('games_found', sa.Integer(), nullable=True),
        sa.Column('games_processed', sa.Integer(), nullable=True),
        sa.Column('players_updated', sa.Integer(), nullable=True),
        sa.Column('errors', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ingestion_run_id'), 'ingestion_run', ['id'], unique=False)

    # Create ingestion_queue table
    op.create_table(
        'ingestion_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.String(), nullable=False),
        sa.Column('game_date', sa.Date(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('attempts', sa.Integer(), nullable=True),
        sa.Column('last_attempt', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('game_id'),
    )
    op.create_index(op.f('ix_ingestion_queue_id'), 'ingestion_queue', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_ingestion_queue_id'), table_name='ingestion_queue')
    op.drop_table('ingestion_queue')
    op.drop_index(op.f('ix_ingestion_run_id'), table_name='ingestion_run')
    op.drop_table('ingestion_run')
