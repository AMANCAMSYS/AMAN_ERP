"""Harden double-entry DB trigger for journal lines

Revision ID: 0003_je_trigger_hard
Revises: 0002_pos_session_unique
Create Date: 2026-03-30

This migration upgrades the journal balance constraint trigger to:
- cover INSERT/UPDATE/DELETE events
- use NEW/OLD safely via COALESCE
- recreate trigger idempotently on journal_lines
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_je_trigger_hard"
down_revision: Union[str, None] = "0002_pos_session_unique"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _journal_lines_exists() -> bool:
    conn = op.get_bind()
    return bool(
        conn.execute(
            sa.text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'journal_lines')"
            )
        ).scalar()
    )


def upgrade() -> None:
    if not _journal_lines_exists():
        return

    op.execute(
        """
        CREATE OR REPLACE FUNCTION check_journal_balance() RETURNS TRIGGER AS $$
        DECLARE
            target_journal_entry_id INTEGER;
            total_debit NUMERIC;
            total_credit NUMERIC;
        BEGIN
            target_journal_entry_id := COALESCE(NEW.journal_entry_id, OLD.journal_entry_id);

            SELECT COALESCE(SUM(debit), 0), COALESCE(SUM(credit), 0)
              INTO total_debit, total_credit
            FROM journal_lines
            WHERE journal_entry_id = target_journal_entry_id;

            IF ABS(total_debit - total_credit) > 0.01 THEN
                RAISE EXCEPTION
                    'Journal entry % is not balanced (debit %, credit %)',
                    target_journal_entry_id, total_debit, total_credit;
            END IF;

            RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_trigger
                WHERE tgname = 'trg_journal_balance'
                  AND tgrelid = 'journal_lines'::regclass
            ) THEN
                DROP TRIGGER trg_journal_balance ON journal_lines;
            END IF;

            CREATE CONSTRAINT TRIGGER trg_journal_balance
            AFTER INSERT OR UPDATE OR DELETE ON journal_lines
            DEFERRABLE INITIALLY DEFERRED
            FOR EACH ROW EXECUTE FUNCTION check_journal_balance();
        END
        $$;
        """
    )


def downgrade() -> None:
    if not _journal_lines_exists():
        return

    op.execute(
        """
        CREATE OR REPLACE FUNCTION check_journal_balance() RETURNS TRIGGER AS $$
        BEGIN
            IF (SELECT ABS(SUM(debit) - SUM(credit)) FROM journal_lines
                WHERE journal_entry_id = NEW.journal_entry_id) > 0.01 THEN
                RAISE EXCEPTION 'Journal entry % is not balanced', NEW.journal_entry_id;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_trigger
                WHERE tgname = 'trg_journal_balance'
                  AND tgrelid = 'journal_lines'::regclass
            ) THEN
                DROP TRIGGER trg_journal_balance ON journal_lines;
            END IF;

            CREATE CONSTRAINT TRIGGER trg_journal_balance
            AFTER INSERT OR UPDATE ON journal_lines
            DEFERRABLE INITIALLY DEFERRED
            FOR EACH ROW EXECUTE FUNCTION check_journal_balance();
        END
        $$;
        """
    )
