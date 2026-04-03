"""Add materialized views for reporting (trial balance, P&L, balance sheet, cash flow)

Revision ID: a1b2c3d4e5f6
Revises: f9b3c7d1e5a8
Create Date: 2026-04-01
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'f9b3c7d1e5a8'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Skip databases that don't have journal_lines (e.g. system DB)
    has_table = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_name = 'journal_lines' AND table_schema = 'public'
        )
    """)).scalar()
    if not has_table:
        return

    # ── 1. Monthly account period balances ──
    # Covers: trial balance, P&L, balance sheet, budget vs actual, comparisons, GL opening
    conn.execute(sa.text("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_account_period_balances AS
        SELECT
            jl.account_id,
            EXTRACT(YEAR FROM je.entry_date)::int  AS period_year,
            EXTRACT(MONTH FROM je.entry_date)::int AS period_month,
            SUM(jl.debit)  AS total_debit,
            SUM(jl.credit) AS total_credit,
            SUM(jl.debit - jl.credit) AS net_balance
        FROM journal_lines jl
        JOIN journal_entries je ON je.id = jl.journal_entry_id
        WHERE je.status = 'posted'
        GROUP BY jl.account_id,
                 EXTRACT(YEAR FROM je.entry_date),
                 EXTRACT(MONTH FROM je.entry_date)
        WITH DATA
    """))

    conn.execute(sa.text("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_apb_acct_period
        ON mv_account_period_balances (account_id, period_year, period_month)
    """))

    # ── 2. Cash counterparty flows (for cash flow statements) ──
    # Each row = one cash account + one counterparty account + month
    conn.execute(sa.text("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cash_counterparty_flows AS
        SELECT
            jl_cash.account_id AS cash_account_id,
            jl_other.account_id AS counterparty_account_id,
            EXTRACT(YEAR FROM je.entry_date)::int  AS period_year,
            EXTRACT(MONTH FROM je.entry_date)::int AS period_month,
            SUM(jl_other.debit) AS counterparty_debit,
            SUM(jl_other.credit) AS counterparty_credit
        FROM journal_lines jl_cash
        JOIN journal_entries je ON je.id = jl_cash.journal_entry_id
        JOIN journal_lines jl_other ON jl_other.journal_entry_id = je.id
                                   AND jl_other.id != jl_cash.id
        JOIN accounts a_cash ON a_cash.id = jl_cash.account_id
        WHERE je.status = 'posted'
          AND a_cash.account_type = 'asset'
          AND a_cash.account_number LIKE '1%'
          AND (a_cash.name ILIKE '%نقد%' OR a_cash.name ILIKE '%صندوق%'
               OR a_cash.name ILIKE '%بنك%' OR a_cash.name ILIKE '%خزينة%'
               OR a_cash.name_en ILIKE '%cash%' OR a_cash.name_en ILIKE '%bank%')
        GROUP BY jl_cash.account_id, jl_other.account_id,
                 EXTRACT(YEAR FROM je.entry_date),
                 EXTRACT(MONTH FROM je.entry_date)
        WITH DATA
    """))

    conn.execute(sa.text("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_ccf_cash_cp_period
        ON mv_cash_counterparty_flows (cash_account_id, counterparty_account_id, period_year, period_month)
    """))

    # ── 3. Party period balances (for customer/supplier statements) ──
    conn.execute(sa.text("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_party_period_balances AS
        SELECT
            pt.party_id,
            EXTRACT(YEAR FROM pt.transaction_date)::int  AS period_year,
            EXTRACT(MONTH FROM pt.transaction_date)::int AS period_month,
            SUM(pt.debit)  AS total_debit,
            SUM(pt.credit) AS total_credit,
            SUM(pt.debit - pt.credit) AS net_balance,
            COUNT(*) AS tx_count
        FROM party_transactions pt
        GROUP BY pt.party_id,
                 EXTRACT(YEAR FROM pt.transaction_date),
                 EXTRACT(MONTH FROM pt.transaction_date)
        WITH DATA
    """))

    conn.execute(sa.text("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_ppb_party_period
        ON mv_party_period_balances (party_id, period_year, period_month)
    """))

    # ── 4. Helper function to refresh all materialized views ──
    conn.execute(sa.text("""
        CREATE OR REPLACE FUNCTION fn_refresh_report_views()
        RETURNS void LANGUAGE plpgsql AS $$
        BEGIN
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_account_period_balances;
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_cash_counterparty_flows;
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_party_period_balances;
        END;
        $$
    """))

    conn.execute(sa.text("COMMIT"))


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("DROP FUNCTION IF EXISTS fn_refresh_report_views() CASCADE"))
    conn.execute(sa.text("DROP MATERIALIZED VIEW IF EXISTS mv_party_period_balances CASCADE"))
    conn.execute(sa.text("DROP MATERIALIZED VIEW IF EXISTS mv_cash_counterparty_flows CASCADE"))
    conn.execute(sa.text("DROP MATERIALIZED VIEW IF EXISTS mv_account_period_balances CASCADE"))
    conn.execute(sa.text("COMMIT"))
