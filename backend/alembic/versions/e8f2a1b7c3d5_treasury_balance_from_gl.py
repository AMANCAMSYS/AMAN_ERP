"""Sync treasury_accounts.current_balance from GL account balance

Revision ID: e8f2a1b7c3d5
Revises: d7a3b5c9e1f4
Create Date: 2026-04-01

Chain: journal_lines INSERT → accounts.balance updated (Phase 1 trigger)
       → accounts UPDATE detected → treasury_accounts.current_balance synced (this trigger)

For base-currency treasuries:  current_balance = accounts.balance
For foreign-currency treasuries: current_balance = accounts.balance_currency
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "e8f2a1b7c3d5"
down_revision: Union[str, None] = "d7a3b5c9e1f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _tables_exist() -> bool:
    conn = op.get_bind()
    return bool(conn.execute(sa.text("""
        SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'accounts')
           AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'treasury_accounts')
    """)).scalar())


def upgrade() -> None:
    if not _tables_exist():
        return

    op.execute("""
        CREATE OR REPLACE FUNCTION fn_sync_treasury_from_gl() RETURNS TRIGGER AS $$
        BEGIN
            -- Only act when balance columns actually changed
            IF NEW.balance IS DISTINCT FROM OLD.balance
               OR NEW.balance_currency IS DISTINCT FROM OLD.balance_currency
            THEN
                UPDATE treasury_accounts ta
                   SET current_balance = CASE
                       -- Foreign-currency treasury: use the GL foreign-currency balance
                       WHEN NEW.currency IS NOT NULL
                            AND NEW.currency != ''
                            AND ta.currency = NEW.currency
                       THEN COALESCE(NEW.balance_currency, 0)
                       -- Base-currency treasury: use the GL base balance
                       ELSE COALESCE(NEW.balance, 0)
                   END
                 WHERE ta.gl_account_id = NEW.id;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_trigger
                 WHERE tgname = 'trg_sync_treasury_from_gl'
                   AND tgrelid = 'accounts'::regclass
            ) THEN
                DROP TRIGGER trg_sync_treasury_from_gl ON accounts;
            END IF;

            CREATE TRIGGER trg_sync_treasury_from_gl
            AFTER UPDATE OF balance, balance_currency ON accounts
            FOR EACH ROW EXECUTE FUNCTION fn_sync_treasury_from_gl();
        END
        $$;
    """)


def downgrade() -> None:
    if not _tables_exist():
        return

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_trigger
                 WHERE tgname = 'trg_sync_treasury_from_gl'
                   AND tgrelid = 'accounts'::regclass
            ) THEN
                DROP TRIGGER trg_sync_treasury_from_gl ON accounts;
            END IF;
        END
        $$;
    """)
    op.execute("DROP FUNCTION IF EXISTS fn_sync_treasury_from_gl() CASCADE;")
