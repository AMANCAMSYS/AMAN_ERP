"""add soft delete columns to phase 2-6 tables

Revision ID: f1a2b3c4d5e6
Revises: e6f7a8b9c0d1
Create Date: 2026-04-03
"""
from alembic import op
import sqlalchemy as sa

revision = 'f1a2b3c4d5e6'
down_revision = 'e6f7a8b9c0d1'
branch_labels = None
depends_on = None

# All 13 tables that need soft-delete columns
TABLES = [
    'sso_configurations',
    'sso_group_role_mappings',
    'sso_fallback_admins',
    'match_tolerances',
    'three_way_matches',
    'three_way_match_lines',
    'entity_groups',
    'intercompany_transactions_v2',
    'intercompany_account_mappings',
    'cost_layers',
    'cost_layer_consumptions',
    'print_templates',
    'report_templates',
]


def upgrade() -> None:
    for table in TABLES:
        op.add_column(table, sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))
        op.add_column(table, sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
        op.add_column(table, sa.Column('deleted_by', sa.String(100), nullable=True))
        op.create_index(f'ix_{table}_is_deleted', table, ['is_deleted'])


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_index(f'ix_{table}_is_deleted', table_name=table)
        op.drop_column(table, 'deleted_by')
        op.drop_column(table, 'deleted_at')
        op.drop_column(table, 'is_deleted')
