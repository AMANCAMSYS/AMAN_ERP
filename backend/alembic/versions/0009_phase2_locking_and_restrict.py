"""Phase 2: optimistic-lock version columns + FK RESTRICT on journal_lines

Revision ID: 0009_phase2_locking_and_restrict
Revises: 0008_gl_integrity_guards
Create Date: 2026-04-20

TASK-016: journal_lines FKs must be ON DELETE RESTRICT (never CASCADE).
TASK-020: Add `version INTEGER NOT NULL DEFAULT 0` to 6 tables consumed by
          utils/optimistic_lock.py (customers, products, assets, projects,
          service_requests, sales_opportunities).

NOTE: The authoritative bootstrap for fresh tenants is the canonical SQL in
      backend/database.py (create_company_tables). This migration only brings
      existing tenants up to date. Both paths must stay in sync.
"""
from alembic import op
import sqlalchemy as sa


revision = "0009_phase2_locking_and_restrict"
down_revision = "0008_gl_integrity_guards"
branch_labels = None
depends_on = None


_VERSIONED_TABLES = (
    "customers",
    "products",
    "assets",
    "projects",
    "service_requests",
    "sales_opportunities",
)


def upgrade() -> None:
    bind = op.get_bind()

    # -------- TASK-020: version column for optimistic locking --------
    for tbl in _VERSIONED_TABLES:
        bind.execute(sa.text(f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.tables
                           WHERE table_name = '{tbl}') THEN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = '{tbl}' AND column_name = 'version'
                    ) THEN
                        ALTER TABLE {tbl}
                        ADD COLUMN version INTEGER NOT NULL DEFAULT 0;
                    END IF;
                END IF;
            END$$;
        """))

    # -------- TASK-016: journal_lines FKs -> RESTRICT --------
    # Drop any existing FK on journal_entry_id / account_id (regardless of
    # action) and recreate them as ON DELETE RESTRICT.
    bind.execute(sa.text("""
        DO $$
        DECLARE
            fk RECORD;
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                           WHERE table_name = 'journal_lines') THEN
                RETURN;
            END IF;

            FOR fk IN
                SELECT tc.constraint_name, kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = 'journal_lines'
                  AND tc.constraint_type = 'FOREIGN KEY'
                  AND kcu.column_name IN ('journal_entry_id', 'account_id')
            LOOP
                EXECUTE format(
                    'ALTER TABLE journal_lines DROP CONSTRAINT %I',
                    fk.constraint_name
                );
            END LOOP;

            ALTER TABLE journal_lines
                ADD CONSTRAINT journal_lines_journal_entry_id_fkey
                FOREIGN KEY (journal_entry_id)
                REFERENCES journal_entries(id)
                ON DELETE RESTRICT;

            ALTER TABLE journal_lines
                ADD CONSTRAINT journal_lines_account_id_fkey
                FOREIGN KEY (account_id)
                REFERENCES accounts(id)
                ON DELETE RESTRICT;
        END$$;
    """))


def downgrade() -> None:
    bind = op.get_bind()

    # Revert FKs to CASCADE (historical default). Keep version columns —
    # dropping them would invalidate already-written rows.
    bind.execute(sa.text("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables
                       WHERE table_name = 'journal_lines') THEN
                ALTER TABLE journal_lines
                    DROP CONSTRAINT IF EXISTS journal_lines_journal_entry_id_fkey;
                ALTER TABLE journal_lines
                    DROP CONSTRAINT IF EXISTS journal_lines_account_id_fkey;

                ALTER TABLE journal_lines
                    ADD CONSTRAINT journal_lines_journal_entry_id_fkey
                    FOREIGN KEY (journal_entry_id)
                    REFERENCES journal_entries(id)
                    ON DELETE CASCADE;

                ALTER TABLE journal_lines
                    ADD CONSTRAINT journal_lines_account_id_fkey
                    FOREIGN KEY (account_id)
                    REFERENCES accounts(id)
                    ON DELETE CASCADE;
            END IF;
        END$$;
    """))
