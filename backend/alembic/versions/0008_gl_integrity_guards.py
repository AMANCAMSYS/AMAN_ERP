"""GL integrity guards: CHECK constraints, UNIQUE indexes, immutability and closed-period triggers

Revision ID: 0008_gl_integrity_guards
Revises: 0007_add_project_asset_indexes
Create Date: 2026-04-21

Closes audit findings FIN-C1, FIN-C2, FIN-C3, FIN-C4, FIN-C8, DB-C1..C3, DB-C6, DB-C8.

Enforces on the database (not only in Python) the invariants of double-entry
accounting, idempotency, period-locking, status vocabulary, and single base
currency.

Idempotent: each object is created with IF NOT EXISTS / EXCEPTION guards so
this migration is safe to re-run against already-partially-migrated tenants.
"""

from alembic import op


revision = "0008_gl_integrity_guards"
down_revision = "0007_add_project_asset_indexes"
branch_labels = None
depends_on = None


def upgrade():
    # ------------------------------------------------------------------
    # FIN-C1 / DB-C1 — Idempotency and source-duplicate unique indexes
    # ------------------------------------------------------------------
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_je_idempotency
            ON journal_entries (idempotency_key)
            WHERE idempotency_key IS NOT NULL;
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_je_source
            ON journal_entries (source, source_id, entry_date)
            WHERE source <> 'Manual' AND source_id IS NOT NULL;
    """)

    # ------------------------------------------------------------------
    # FIN-C2 / DB-C2 — CHECK constraints on journal_lines
    # ------------------------------------------------------------------
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_jl_nonneg') THEN
                ALTER TABLE journal_lines
                    ADD CONSTRAINT chk_jl_nonneg CHECK (debit >= 0 AND credit >= 0);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_jl_exclusive') THEN
                ALTER TABLE journal_lines
                    ADD CONSTRAINT chk_jl_exclusive CHECK (NOT (debit > 0 AND credit > 0));
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_jl_nonzero') THEN
                ALTER TABLE journal_lines
                    ADD CONSTRAINT chk_jl_nonzero CHECK (debit + credit > 0);
            END IF;
        END $$;
    """)

    # ------------------------------------------------------------------
    # DB-C3 — status vocabulary CHECK on journal_entries
    # ------------------------------------------------------------------
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_je_status') THEN
                ALTER TABLE journal_entries
                    ADD CONSTRAINT chk_je_status
                    CHECK (status IN ('draft','posted','void','reversed'));
            END IF;
        END $$;
    """)

    # ------------------------------------------------------------------
    # FIN-C8 / DB-C6 — at most one base currency
    # ------------------------------------------------------------------
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_currency_one_base
            ON currencies ((TRUE))
            WHERE is_base = TRUE;
    """)

    # ------------------------------------------------------------------
    # FIN-C3 — Closed-period guard at the database level
    # ------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION assert_period_open() RETURNS trigger AS $$
        DECLARE
            v_closed BOOLEAN;
        BEGIN
            IF NEW.status IS DISTINCT FROM 'posted' THEN
                RETURN NEW;
            END IF;
            SELECT TRUE INTO v_closed
            FROM fiscal_periods
            WHERE NEW.entry_date BETWEEN start_date AND end_date
              AND is_closed = TRUE
            LIMIT 1;
            IF v_closed THEN
                RAISE EXCEPTION 'Posting into a closed fiscal period is forbidden (entry_date=%)', NEW.entry_date
                    USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        DROP TRIGGER IF EXISTS trg_je_period_open ON journal_entries;
        CREATE TRIGGER trg_je_period_open
            BEFORE INSERT OR UPDATE OF status, entry_date ON journal_entries
            FOR EACH ROW EXECUTE FUNCTION assert_period_open();
    """)

    # ------------------------------------------------------------------
    # FIN-C4 — Posted journal entries are immutable
    # Allowed transitions: posted -> void, posted -> reversed.
    # Any other UPDATE or DELETE on a posted header is rejected.
    # ------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION block_posted_je_changes() RETURNS trigger AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                IF OLD.status = 'posted' THEN
                    RAISE EXCEPTION 'Posted journal entries cannot be deleted (id=%)', OLD.id
                        USING ERRCODE = '23514';
                END IF;
                RETURN OLD;
            END IF;
            -- UPDATE path
            IF OLD.status = 'posted' AND NEW.status NOT IN ('void','reversed','posted') THEN
                RAISE EXCEPTION 'Posted journal entries are immutable (id=%, old=%, new=%)',
                    OLD.id, OLD.status, NEW.status USING ERRCODE = '23514';
            END IF;
            IF OLD.status = 'posted' AND NEW.status = 'posted' THEN
                -- Only allow bookkeeping columns to be touched by the service layer.
                IF (NEW.entry_date <> OLD.entry_date)
                   OR (NEW.description IS DISTINCT FROM OLD.description)
                   OR (NEW.currency IS DISTINCT FROM OLD.currency)
                   OR (NEW.exchange_rate IS DISTINCT FROM OLD.exchange_rate)
                   OR (NEW.branch_id IS DISTINCT FROM OLD.branch_id)
                   OR (NEW.reference IS DISTINCT FROM OLD.reference) THEN
                    RAISE EXCEPTION 'Posted journal entry fields are immutable (id=%)', OLD.id
                        USING ERRCODE = '23514';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        DROP TRIGGER IF EXISTS trg_je_immutable ON journal_entries;
        CREATE TRIGGER trg_je_immutable
            BEFORE UPDATE OR DELETE ON journal_entries
            FOR EACH ROW EXECUTE FUNCTION block_posted_je_changes();
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION block_posted_jl_changes() RETURNS trigger AS $$
        DECLARE
            v_status TEXT;
            v_id     BIGINT;
        BEGIN
            IF TG_OP = 'DELETE' THEN
                v_id := OLD.journal_entry_id;
            ELSE
                v_id := NEW.journal_entry_id;
            END IF;
            SELECT status INTO v_status FROM journal_entries WHERE id = v_id;
            IF v_status = 'posted' THEN
                RAISE EXCEPTION 'Lines of a posted journal entry are immutable (je_id=%)', v_id
                    USING ERRCODE = '23514';
            END IF;
            IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        DROP TRIGGER IF EXISTS trg_jl_immutable ON journal_lines;
        CREATE TRIGGER trg_jl_immutable
            BEFORE UPDATE OR DELETE ON journal_lines
            FOR EACH ROW EXECUTE FUNCTION block_posted_jl_changes();
    """)

    # ------------------------------------------------------------------
    # Deferred balanced-JE constraint trigger (Σ debit = Σ credit)
    # Supersedes the older `trg_journal_balance` / `check_journal_balance`
    # that asserted balance regardless of status (and therefore fired on
    # drafts). The new version is status-aware: drafts may be unbalanced
    # until posted.
    # ------------------------------------------------------------------
    op.execute("DROP TRIGGER IF EXISTS trg_journal_balance ON journal_lines;")
    op.execute("""
        CREATE OR REPLACE FUNCTION assert_je_balanced() RETURNS trigger AS $$
        DECLARE
            v_je  BIGINT;
            v_sum NUMERIC;
            v_status TEXT;
        BEGIN
            IF TG_OP = 'DELETE' THEN
                v_je := OLD.journal_entry_id;
            ELSE
                v_je := NEW.journal_entry_id;
            END IF;
            SELECT status INTO v_status FROM journal_entries WHERE id = v_je;
            IF v_status IS DISTINCT FROM 'posted' THEN
                IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
                RETURN NEW;
            END IF;
            SELECT COALESCE(SUM(debit),0) - COALESCE(SUM(credit),0)
              INTO v_sum
              FROM journal_lines
             WHERE journal_entry_id = v_je;
            IF ABS(v_sum) > 0.005 THEN
                RAISE EXCEPTION 'Unbalanced journal entry (je_id=%, diff=%)', v_je, v_sum
                    USING ERRCODE = '23514';
            END IF;
            IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        DROP TRIGGER IF EXISTS trg_je_balanced ON journal_lines;
        CREATE CONSTRAINT TRIGGER trg_je_balanced
            AFTER INSERT OR UPDATE OR DELETE ON journal_lines
            DEFERRABLE INITIALLY DEFERRED
            FOR EACH ROW EXECUTE FUNCTION assert_je_balanced();
    """)

    # ------------------------------------------------------------------
    # PERF-H1 / DB-H8 — composite indexes on GL headers/lines
    # (Per-tenant DB architecture: journal_entries has no company_id column;
    # tenant isolation is enforced at the DB-connection layer.)
    # ------------------------------------------------------------------
    op.execute("CREATE INDEX IF NOT EXISTS idx_je_branch_date  ON journal_entries (branch_id, entry_date);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_je_status_date  ON journal_entries (status, entry_date);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_je_entry_date   ON journal_entries (entry_date);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_jl_account_je   ON journal_lines (account_id, journal_entry_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_jl_je           ON journal_lines (journal_entry_id);")

    # ------------------------------------------------------------------
    # FIN-H (TASK-018): exchange_rates is append-only FX history
    # ------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION block_exchange_rate_mutation() RETURNS trigger AS $$
        BEGIN
            IF TG_OP = 'UPDATE' THEN
                RAISE EXCEPTION 'exchange_rates rows are immutable; insert a new row for a new rate_date'
                    USING ERRCODE = '23514';
            END IF;
            RAISE EXCEPTION 'exchange_rates rows cannot be deleted; mark corrections via a new dated row'
                USING ERRCODE = '23514';
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        DROP TRIGGER IF EXISTS trg_exchange_rates_immutable ON exchange_rates;
        CREATE TRIGGER trg_exchange_rates_immutable
            BEFORE UPDATE OR DELETE ON exchange_rates
            FOR EACH ROW EXECUTE FUNCTION block_exchange_rate_mutation();
    """)

    # ------------------------------------------------------------------
    # FIN-H (TASK-019): fiscal_periods non-overlap exclusion constraint
    # ------------------------------------------------------------------
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")
    op.execute("""
        DO $fp$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'excl_fp_nooverlap'
            ) THEN
                ALTER TABLE fiscal_periods
                    ADD CONSTRAINT excl_fp_nooverlap
                    EXCLUDE USING GIST (
                        daterange(start_date, end_date, '[]') WITH &&
                    );
            END IF;
        END $fp$;
    """)


def downgrade():
    # Reverse order — triggers first, then constraints, then indexes.
    op.execute("ALTER TABLE fiscal_periods DROP CONSTRAINT IF EXISTS excl_fp_nooverlap;")
    op.execute("DROP TRIGGER IF EXISTS trg_exchange_rates_immutable ON exchange_rates;")
    op.execute("DROP FUNCTION IF EXISTS block_exchange_rate_mutation();")

    op.execute("DROP TRIGGER IF EXISTS trg_je_balanced ON journal_lines;")
    op.execute("DROP FUNCTION IF EXISTS assert_je_balanced();")

    op.execute("DROP TRIGGER IF EXISTS trg_jl_immutable ON journal_lines;")
    op.execute("DROP FUNCTION IF EXISTS block_posted_jl_changes();")

    op.execute("DROP TRIGGER IF EXISTS trg_je_immutable ON journal_entries;")
    op.execute("DROP FUNCTION IF EXISTS block_posted_je_changes();")

    op.execute("DROP TRIGGER IF EXISTS trg_je_period_open ON journal_entries;")
    op.execute("DROP FUNCTION IF EXISTS assert_period_open();")

    op.execute("ALTER TABLE journal_entries DROP CONSTRAINT IF EXISTS chk_je_status;")
    op.execute("ALTER TABLE journal_lines   DROP CONSTRAINT IF EXISTS chk_jl_nonzero;")
    op.execute("ALTER TABLE journal_lines   DROP CONSTRAINT IF EXISTS chk_jl_exclusive;")
    op.execute("ALTER TABLE journal_lines   DROP CONSTRAINT IF EXISTS chk_jl_nonneg;")

    op.execute("DROP INDEX IF EXISTS uq_je_idempotency;")
    op.execute("DROP INDEX IF EXISTS uq_je_source;")
    op.execute("DROP INDEX IF EXISTS uq_currency_one_base;")
    op.execute("DROP INDEX IF EXISTS idx_je_branch_date;")
    op.execute("DROP INDEX IF EXISTS idx_je_status_date;")
    op.execute("DROP INDEX IF EXISTS idx_je_entry_date;")
    op.execute("DROP INDEX IF EXISTS idx_jl_account_je;")
    op.execute("DROP INDEX IF EXISTS idx_jl_je;")
