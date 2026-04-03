"""Add triggers for automatic account balance updates from journal_lines

Revision ID: d7a3b5c9e1f4
Revises: c1f4e8d9b2a6
Create Date: 2026-04-01

Replaces application-level update_account_balance() with DB triggers:
- fn_apply_balance_delta(): helper to update accounts.balance / balance_currency
- fn_jl_account_balance(): fires on journal_lines INSERT/UPDATE/DELETE
- fn_je_status_balance():  fires on journal_entries UPDATE (status change)

Rules:
- Only posted JEs affect account balances
- Asset/Expense: balance += (debit - credit)
- Liability/Equity/Revenue: balance += (credit - debit)
- Foreign currency balance updated only when line.currency matches account.currency
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "d7a3b5c9e1f4"
down_revision: Union[str, None] = "c1f4e8d9b2a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _tables_exist() -> bool:
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables WHERE table_name = 'journal_lines'
        ) AND EXISTS (
            SELECT 1 FROM information_schema.tables WHERE table_name = 'journal_entries'
        ) AND EXISTS (
            SELECT 1 FROM information_schema.tables WHERE table_name = 'accounts'
        )
    """)).scalar()
    return bool(result)


def upgrade() -> None:
    if not _tables_exist():
        return

    # ── Helper function: apply a balance delta to one account ──────────
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_apply_balance_delta(
            p_account_id  INTEGER,
            p_debit       NUMERIC,
            p_credit      NUMERIC,
            p_amount_curr NUMERIC,
            p_line_curr   VARCHAR,
            p_sign        INTEGER DEFAULT 1   -- 1 = apply, -1 = reverse
        ) RETURNS VOID AS $$
        DECLARE
            v_acct_type     VARCHAR;
            v_acct_currency VARCHAR(3);
            v_change_base   NUMERIC(18, 4);
            v_change_curr   NUMERIC(18, 4) := 0;
            v_debit_curr    NUMERIC(18, 4);
            v_credit_curr   NUMERIC(18, 4);
        BEGIN
            SELECT account_type, currency
              INTO v_acct_type, v_acct_currency
              FROM accounts WHERE id = p_account_id;

            IF v_acct_type IS NULL THEN
                RETURN;
            END IF;

            -- Base-currency balance change
            IF v_acct_type IN ('asset', 'expense') THEN
                v_change_base := p_sign * ROUND(p_debit - p_credit, 2);
            ELSE
                v_change_base := p_sign * ROUND(p_credit - p_debit, 2);
            END IF;

            -- Foreign-currency balance change (only when currencies match)
            IF p_line_curr IS NOT NULL
               AND v_acct_currency IS NOT NULL
               AND p_line_curr = v_acct_currency
               AND COALESCE(p_amount_curr, 0) != 0
            THEN
                IF p_debit > 0 THEN
                    v_debit_curr  := p_amount_curr;
                    v_credit_curr := 0;
                ELSE
                    v_debit_curr  := 0;
                    v_credit_curr := p_amount_curr;
                END IF;

                IF v_acct_type IN ('asset', 'expense') THEN
                    v_change_curr := p_sign * ROUND(v_debit_curr - v_credit_curr, 2);
                ELSE
                    v_change_curr := p_sign * ROUND(v_credit_curr - v_debit_curr, 2);
                END IF;
            END IF;

            IF v_change_base != 0 THEN
                UPDATE accounts
                   SET balance = COALESCE(balance, 0) + v_change_base
                 WHERE id = p_account_id;
            END IF;

            IF v_change_curr != 0 THEN
                UPDATE accounts
                   SET balance_currency = COALESCE(balance_currency, 0) + v_change_curr
                 WHERE id = p_account_id;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # ── Trigger function on journal_lines ──────────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_jl_account_balance() RETURNS TRIGGER AS $$
        DECLARE
            v_je_status VARCHAR;
        BEGIN
            IF TG_OP = 'INSERT' THEN
                SELECT status INTO v_je_status
                  FROM journal_entries WHERE id = NEW.journal_entry_id;

                IF v_je_status = 'posted' THEN
                    PERFORM fn_apply_balance_delta(
                        NEW.account_id,
                        COALESCE(NEW.debit, 0),
                        COALESCE(NEW.credit, 0),
                        COALESCE(NEW.amount_currency, 0),
                        NEW.currency,
                        1
                    );
                END IF;
                RETURN NEW;

            ELSIF TG_OP = 'DELETE' THEN
                SELECT status INTO v_je_status
                  FROM journal_entries WHERE id = OLD.journal_entry_id;

                IF v_je_status = 'posted' THEN
                    PERFORM fn_apply_balance_delta(
                        OLD.account_id,
                        COALESCE(OLD.debit, 0),
                        COALESCE(OLD.credit, 0),
                        COALESCE(OLD.amount_currency, 0),
                        OLD.currency,
                        -1
                    );
                END IF;
                RETURN OLD;

            ELSIF TG_OP = 'UPDATE' THEN
                SELECT status INTO v_je_status
                  FROM journal_entries WHERE id = NEW.journal_entry_id;

                IF v_je_status = 'posted' THEN
                    -- Reverse OLD amounts
                    PERFORM fn_apply_balance_delta(
                        OLD.account_id,
                        COALESCE(OLD.debit, 0),
                        COALESCE(OLD.credit, 0),
                        COALESCE(OLD.amount_currency, 0),
                        OLD.currency,
                        -1
                    );
                    -- Apply NEW amounts
                    PERFORM fn_apply_balance_delta(
                        NEW.account_id,
                        COALESCE(NEW.debit, 0),
                        COALESCE(NEW.credit, 0),
                        COALESCE(NEW.amount_currency, 0),
                        NEW.currency,
                        1
                    );
                END IF;
                RETURN NEW;
            END IF;

            RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql;
    """)

    # ── Trigger function on journal_entries (status change) ────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_je_status_balance() RETURNS TRIGGER AS $$
        DECLARE
            v_line RECORD;
        BEGIN
            -- Only act on status changes
            IF OLD.status IS NOT DISTINCT FROM NEW.status THEN
                RETURN NEW;
            END IF;

            -- draft/voided → posted: apply all line balances
            IF NEW.status = 'posted' AND COALESCE(OLD.status, '') != 'posted' THEN
                FOR v_line IN
                    SELECT account_id,
                           COALESCE(debit, 0) AS debit,
                           COALESCE(credit, 0) AS credit,
                           COALESCE(amount_currency, 0) AS amount_currency,
                           currency
                      FROM journal_lines
                     WHERE journal_entry_id = NEW.id
                LOOP
                    PERFORM fn_apply_balance_delta(
                        v_line.account_id,
                        v_line.debit,
                        v_line.credit,
                        v_line.amount_currency,
                        v_line.currency,
                        1
                    );
                END LOOP;

            -- posted → anything else: reverse all line balances
            ELSIF OLD.status = 'posted' AND COALESCE(NEW.status, '') != 'posted' THEN
                FOR v_line IN
                    SELECT account_id,
                           COALESCE(debit, 0) AS debit,
                           COALESCE(credit, 0) AS credit,
                           COALESCE(amount_currency, 0) AS amount_currency,
                           currency
                      FROM journal_lines
                     WHERE journal_entry_id = OLD.id
                LOOP
                    PERFORM fn_apply_balance_delta(
                        v_line.account_id,
                        v_line.debit,
                        v_line.credit,
                        v_line.amount_currency,
                        v_line.currency,
                        -1
                    );
                END LOOP;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # ── Install triggers (idempotent) ──────────────────────────────────
    # BEFORE DELETE on journal_entries: reverse balances before cascade
    # (parent row is invisible to child triggers during CASCADE)
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_je_before_delete_balance() RETURNS TRIGGER AS $$
        DECLARE
            v_line RECORD;
        BEGIN
            IF OLD.status = 'posted' THEN
                FOR v_line IN
                    SELECT account_id,
                           COALESCE(debit, 0) AS debit,
                           COALESCE(credit, 0) AS credit,
                           COALESCE(amount_currency, 0) AS amount_currency,
                           currency
                      FROM journal_lines
                     WHERE journal_entry_id = OLD.id
                LOOP
                    PERFORM fn_apply_balance_delta(
                        v_line.account_id,
                        v_line.debit,
                        v_line.credit,
                        v_line.amount_currency,
                        v_line.currency,
                        -1
                    );
                END LOOP;
            END IF;
            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        DO $$
        BEGIN
            -- journal_lines trigger
            IF EXISTS (
                SELECT 1 FROM pg_trigger
                 WHERE tgname = 'trg_jl_account_balance'
                   AND tgrelid = 'journal_lines'::regclass
            ) THEN
                DROP TRIGGER trg_jl_account_balance ON journal_lines;
            END IF;

            CREATE TRIGGER trg_jl_account_balance
            AFTER INSERT OR UPDATE OR DELETE ON journal_lines
            FOR EACH ROW EXECUTE FUNCTION fn_jl_account_balance();

            -- journal_entries status trigger (AFTER UPDATE)
            IF EXISTS (
                SELECT 1 FROM pg_trigger
                 WHERE tgname = 'trg_je_status_balance'
                   AND tgrelid = 'journal_entries'::regclass
            ) THEN
                DROP TRIGGER trg_je_status_balance ON journal_entries;
            END IF;

            CREATE TRIGGER trg_je_status_balance
            AFTER UPDATE ON journal_entries
            FOR EACH ROW EXECUTE FUNCTION fn_je_status_balance();

            -- journal_entries BEFORE DELETE trigger
            IF EXISTS (
                SELECT 1 FROM pg_trigger
                 WHERE tgname = 'trg_je_before_delete_balance'
                   AND tgrelid = 'journal_entries'::regclass
            ) THEN
                DROP TRIGGER trg_je_before_delete_balance ON journal_entries;
            END IF;

            CREATE TRIGGER trg_je_before_delete_balance
            BEFORE DELETE ON journal_entries
            FOR EACH ROW EXECUTE FUNCTION fn_je_before_delete_balance();
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
                 WHERE tgname = 'trg_jl_account_balance'
                   AND tgrelid = 'journal_lines'::regclass
            ) THEN
                DROP TRIGGER trg_jl_account_balance ON journal_lines;
            END IF;

            IF EXISTS (
                SELECT 1 FROM pg_trigger
                 WHERE tgname = 'trg_je_status_balance'
                   AND tgrelid = 'journal_entries'::regclass
            ) THEN
                DROP TRIGGER trg_je_status_balance ON journal_entries;
            END IF;

            IF EXISTS (
                SELECT 1 FROM pg_trigger
                 WHERE tgname = 'trg_je_before_delete_balance'
                   AND tgrelid = 'journal_entries'::regclass
            ) THEN
                DROP TRIGGER trg_je_before_delete_balance ON journal_entries;
            END IF;
        END
        $$;
    """)

    op.execute("DROP FUNCTION IF EXISTS fn_jl_account_balance() CASCADE;")
    op.execute("DROP FUNCTION IF EXISTS fn_je_status_balance() CASCADE;")
    op.execute("DROP FUNCTION IF EXISTS fn_je_before_delete_balance() CASCADE;")
    op.execute("DROP FUNCTION IF EXISTS fn_apply_balance_delta(INTEGER, NUMERIC, NUMERIC, NUMERIC, VARCHAR, INTEGER) CASCADE;")
