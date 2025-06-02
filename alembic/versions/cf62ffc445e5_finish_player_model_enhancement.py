"""finish player model enhancement

Revision ID: cf62ffc445e5
Revises: e2382a95aa0d
Create Date: 2024-12-30 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cf62ffc445e5'
down_revision = 'e2382a95aa0d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add remaining columns that weren't added in the previous migration
    try:
        op.add_column('player', sa.Column('created_at', sa.DateTime(), nullable=True))
    except Exception:
        pass  # Column might already exist

    try:
        op.add_column('player', sa.Column('updated_at', sa.DateTime(), nullable=True))
    except Exception:
        pass  # Column might already exist

    try:
        op.add_column('player', sa.Column('team_id', sa.Integer(), nullable=True))
    except Exception:
        pass  # Column might already exist

    # Create foreign key constraint for team_id (if not exists)
    try:
        op.create_foreign_key('fk_player_team_id', 'player', 'team', ['team_id'], ['id'])
    except Exception:
        pass  # Constraint might already exist

    # Create indexes for commonly queried fields (if not exists)
    try:
        op.create_index('ix_player_status', 'player', ['status'])
    except Exception:
        pass  # Index might already exist

    try:
        op.create_index('ix_player_team_id', 'player', ['team_id'])
    except Exception:
        pass  # Index might already exist


def downgrade() -> None:
    # Drop indexes
    try:
        op.drop_index('ix_player_team_id', table_name='player')
    except Exception:
        pass

    try:
        op.drop_index('ix_player_status', table_name='player')
    except Exception:
        pass

    # Drop foreign key constraint
    try:
        op.drop_constraint('fk_player_team_id', 'player', type_='foreignkey')
    except Exception:
        pass

    # Drop columns
    try:
        op.drop_column('player', 'team_id')
    except Exception:
        pass

    try:
        op.drop_column('player', 'updated_at')
    except Exception:
        pass

    try:
        op.drop_column('player', 'created_at')
    except Exception:
        pass