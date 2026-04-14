"""
Migration: Add idempotency_key column to journal_entries table.
Supports Constitution XXIII — duplicate prevention on JE creation retries.
"""
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

MIGRATION_SQL = """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'journal_entries' AND column_name = 'idempotency_key'
    ) THEN
        ALTER TABLE journal_entries ADD COLUMN idempotency_key VARCHAR(255) NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_journal_entries_idempotency_key
            ON journal_entries (idempotency_key) WHERE idempotency_key IS NOT NULL;
    END IF;
END $$;
"""


def run_migration(db):
    """Apply the migration to add idempotency_key column."""
    try:
        db.execute(text(MIGRATION_SQL))
        db.commit()
        logger.info("Migration: idempotency_key column added to journal_entries")
    except Exception as e:
        db.rollback()
        logger.error("Migration failed: %s", e)
        raise
