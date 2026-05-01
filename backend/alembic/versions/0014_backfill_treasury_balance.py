"""T1.3a: backfill `treasury_accounts.current_balance` from journal_lines.

Historically `current_balance` was maintained by ad-hoc ± UPDATEs scattered
across 17 call sites (audit P0 #3). The Python helper
`utils.treasury_balance.recalc_treasury_from_gl` is now the single source
of truth and is invoked after every JE posting affecting a treasury.

This migration brings every existing tenant's `current_balance` into
agreement with `journal_lines` for the linked `gl_account_id`, so the new
helper does not need to "catch up" gradually as activity occurs.

Idempotent: re-running yields identical values.
"""
from alembic import op


revision = "0014_backfill_treasury_balance"
down_revision = "0013_add_ufx_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Recompute every linked treasury's current_balance from posted journal
    # lines, respecting the treasury's denominated currency.
    #
    # Uses a correlated subquery (rather than LEFT JOIN) so that lines
    # belonging to non-posted journal entries are unconditionally excluded
    # — a LEFT JOIN with `je.status='posted'` in WHERE would still include
    # rows whose join produced je IS NULL, leaking draft amounts into SUM.
    op.execute(
        """
        UPDATE treasury_accounts ta
        SET current_balance = COALESCE((
            SELECT
                CASE
                    WHEN ta.currency IS NULL OR UPPER(ta.currency) = 'SAR' THEN
                        SUM(jl.debit) - SUM(jl.credit)
                    ELSE
                        SUM(
                            CASE
                                WHEN jl.debit  > 0 THEN COALESCE(jl.amount_currency, jl.debit)
                                WHEN jl.credit > 0 THEN -COALESCE(jl.amount_currency, jl.credit)
                                ELSE 0
                            END
                        )
                END
            FROM journal_lines jl
            JOIN journal_entries je ON je.id = jl.journal_entry_id
            WHERE jl.account_id = ta.gl_account_id
              AND je.status = 'posted'
              AND (
                    ta.currency IS NULL
                 OR UPPER(ta.currency) = 'SAR'
                 OR jl.currency IS NULL
                 OR jl.currency = ta.currency
              )
        ), 0),
        updated_at = NOW()
        WHERE ta.gl_account_id IS NOT NULL;
        """
    )


def downgrade() -> None:
    # Backfill is non-destructive — there is no meaningful downgrade.
    pass
