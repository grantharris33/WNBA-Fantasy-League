"""Add data quality monitoring models

Revision ID: add_data_quality_monitoring_models
Revises: f148c9022616
Create Date: 2025-01-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_data_quality_monitoring_models'
down_revision = 'f148c9022616'
branch_labels = None
depends_on = None


def upgrade():
    # Create data_quality_check table
    op.create_table(
        'data_quality_check',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('check_name', sa.String(), nullable=False),
        sa.Column('check_type', sa.String(), nullable=False),
        sa.Column('target_table', sa.String(), nullable=False),
        sa.Column('check_query', sa.Text(), nullable=False),
        sa.Column('expected_result', sa.String(), nullable=True),
        sa.Column('last_run', sa.DateTime(), nullable=True),
        sa.Column('last_result', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True, default='pending'),
        sa.Column('failure_threshold', sa.Integer(), nullable=True, default=1),
        sa.Column('consecutive_failures', sa.Integer(), nullable=True, default=0),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create data_validation_rule table
    op.create_table(
        'data_validation_rule',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('field_name', sa.String(), nullable=False),
        sa.Column('rule_type', sa.String(), nullable=False),
        sa.Column('rule_config', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create data_anomaly_log table
    op.create_table(
        'data_anomaly_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('detected_at', sa.DateTime(), nullable=True),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=False),
        sa.Column('anomaly_type', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('is_resolved', sa.Boolean(), nullable=True, default=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('data_anomaly_log')
    op.drop_table('data_validation_rule')
    op.drop_table('data_quality_check')