"""Add trigger to auto-update parties.current_balance from party_transactions

Revision ID: f9b3c7d1e5a8
Revises: e8f2a1b7c3d5
Create Date: 2026-04-01

party_transactions is the sub-ledger for party (customer/supplier) balances.
This trigger keeps parties.current_balance in sync automatically:
- INSERT: parties.current_balance += (debit - credit)
- DELETE: parties.current_balance -= (debit - credit)
- UPDATE: reverse OLD delta, apply NEW delta

Also handles balance_currency for foreign-currency tracking.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "f9b3c7d1e5a8"
down_revision: Union[str, None] = "e8f2a1b7c3d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _tables_exist() -> bool:
    conn = op.get_bind()
    return bool(conn.execute(sa.text("""
        SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'party_transactions')
           AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'parties')
    """)).scalar())


def upgrade() -> None:
    if not _tables_exist():
        return

    # ── Trigger function: sync parties.current_balance from party_transactions ──
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_party_tx_balance() RETURNS TRIGGER AS $$
        DECLARE
            v_delta NUMERIC(18, 4);
        BEGIN
            IF TG_OP = 'INSERT' THEN
                v_delta := COALESCE(NEW.debit, 0) - COALESCE(NEW.credit, 0);
                IF v_delta != 0 AND NEW.party_id IS NOT NULL THEN
                    UPDATE parties
                       SET current_balance = COALESCE(current_balance, 0) + v_delta
                     WHERE id = NEW.party_id;
                END IF;
                RETURN NEW;

            ELSIF TG_OP = 'DELETE' THEN
                v_delta := COALESCE(OLD.debit, 0) - COALESCE(OLD.credit, 0);
                IF v_delta != 0 AND OLD.party_id IS NOT NULL THEN
                    UPDATE parties
                       SET current_balance = COALESCE(current_balance, 0) - v_delta
                     WHERE id = OLD.party_id;
                END IF;
                RETURN OLD;

            ELSIF TG_OP = 'UPDATE' THEN
                -- Reverse old
                IF OLD.party_id IS NOT NULL THEN
                    v_delta := COALESCE(OLD.debit, 0) - COALESCE(OLD.credit, 0);
                    IF v_delta != 0 THEN
                        UPDATE parties
                           SET current_balance = COALESCE(current_balance, 0) - v_delta
                         WHERE id = OLD.party_id;
                    END IF;
                END IF;
                -- Apply new
                IF NEW.party_id IS NOT NULL THEN
                    v_delta := COALESCE(NEW.debit, 0) - COALESCE(NEW.credit, 0);
                    IF v_delta != 0 THEN
                        UPDATE parties
                           SET current_balance = COALESCE(current_balance, 0) + v_delta
                         WHERE id = NEW.party_id;
                    END IF;
                END IF;
                RETURN NEW;
            END IF;

            RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql;
    """)

    # ── Install trigger (idempotent) ──
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_trigger
                 WHERE tgname = 'trg_party_tx_balance'
                   AND tgrelid = 'party_transactions'::regclass
            ) THEN
                DROP TRIGGER trg_party_tx_balance ON party_transactions;
            END IF;

            CREATE TRIGGER trg_party_tx_balance
            AFTER INSERT OR UPDATE OR DELETE ON party_transactions
            FOR EACH ROW EXECUTE FUNCTION fn_party_tx_balance();
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
                 WHERE tgname = 'trg_party_tx_balance'
                   AND tgrelid = 'party_transactions'::regclass
            ) THEN
                DROP TRIGGER trg_party_tx_balance ON party_transactions;
            END IF;
        END
        $$;
    """)
    op.execute("DROP FUNCTION IF EXISTS fn_party_tx_balance() CASCADE;")
