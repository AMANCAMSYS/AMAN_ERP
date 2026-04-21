"""Phase 4 / TASK-031: composite index on JE (source, source_id, entry_date)

Accelerates `gl_service.create_journal_entry` duplicate-source guard which
currently performs a seq scan on journal_entries for every posting.

Aligns pre-existing tenant databases with the canonical SQL already added to
backend/database.py. Uses CREATE INDEX CONCURRENTLY so running tenants are not
blocked; the migration must therefore execute outside of a transaction.
"""
from alembic import op


revision = "0011_je_source_composite_index"
down_revision = "0010_inventory_in_transit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # CONCURRENTLY cannot run inside a transaction block.
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS
                idx_je_source_srcid_date
                ON journal_entries (source, source_id, entry_date)
        """)


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_je_source_srcid_date")
