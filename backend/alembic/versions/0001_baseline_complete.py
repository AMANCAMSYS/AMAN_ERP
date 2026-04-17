"""Complete baseline — full schema snapshot matching database.py

Revision ID: 0001_baseline_complete
Revises:
Create Date: 2026-04-17

This is the single authoritative baseline migration.
All 280 tenant tables are created by create_company_tables() using database.py.
This migration exists only to register the schema version; it performs no DDL.

For new tenants: create_company_tables() runs the SQL from database.py then
stamps the DB at this revision via `alembic stamp 0001_baseline_complete`.

For future schema changes: create a new migration that revises this one.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_baseline_complete"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tables are created by create_company_tables() using database.py.
    # This migration is stamped (not run) on fresh tenants.
    # Future migrations should use op.add_column / op.create_table etc.
    pass


def downgrade() -> None:
    # Dropping all tables is intentionally not implemented.
    # To reset a tenant DB, drop and recreate it.
    pass
