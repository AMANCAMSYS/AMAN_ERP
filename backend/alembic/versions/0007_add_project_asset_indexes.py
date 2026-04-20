"""add missing project and asset indexes

Revision ID: 0007_add_project_asset_indexes
Revises: 0006_add_asset_revaluation_columns
Create Date: 2026-04-20

Add 6 missing foreign-key indexes on project and contract child tables
to improve JOIN performance on common access patterns.

Constitution XXVIII: Applied together with database.py CREATE TABLE update.
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "0007_add_project_asset_indexes"
down_revision = "0006_add_asset_revaluation_columns"
branch_labels = None
depends_on = None

_INDEXES = [
    ("idx_project_tasks_project", "project_tasks", ["project_id"]),
    ("idx_project_budgets_project", "project_budgets", ["project_id"]),
    ("idx_project_expenses_project", "project_expenses", ["project_id"]),
    ("idx_project_revenues_project", "project_revenues", ["project_id"]),
    ("idx_project_documents_project", "project_documents", ["project_id"]),
    ("idx_contract_items_contract", "contract_items", ["contract_id"]),
]


def upgrade():
    for name, table, columns in _INDEXES:
        op.create_index(name, table, columns, if_not_exists=True)


def downgrade():
    for name, table, _columns in _INDEXES:
        op.drop_index(name, table_name=table)
