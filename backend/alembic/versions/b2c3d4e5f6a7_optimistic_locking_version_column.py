"""Add version column for optimistic locking to editable tables

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-02
"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None

# Tables that benefit from optimistic locking — user-editable entities
# with realistic concurrent-edit risk.
TABLES = [
    "invoices",
    "assets",
    "products",
    "projects",
    "project_tasks",
    "contracts",
    "purchase_orders",
    "budgets",
    "parties",
    "employees",
    "sales_quotations",
    "sales_orders",
    "sales_opportunities",
    "support_tickets",
    "service_requests",
]


def _table_exists(conn, table_name: str) -> bool:
    return conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_name = :t AND table_schema = 'public')"
    ), {"t": table_name}).scalar()


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    return conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_name = :t AND column_name = :c AND table_schema = 'public')"
    ), {"t": table_name, "c": column_name}).scalar()


def upgrade():
    conn = op.get_bind()

    for table in TABLES:
        if not _table_exists(conn, table):
            continue
        if _column_exists(conn, table, "version"):
            continue
        conn.execute(sa.text(
            f'ALTER TABLE "{table}" ADD COLUMN version INTEGER NOT NULL DEFAULT 1'
        ))


def downgrade():
    conn = op.get_bind()

    for table in TABLES:
        if not _table_exists(conn, table):
            continue
        if not _column_exists(conn, table, "version"):
            continue
        conn.execute(sa.text(
            f'ALTER TABLE "{table}" DROP COLUMN version'
        ))
