"""
Balance reconciliation utility.

Compares three sources of account balances:
1. accounts.balance (maintained by DB trigger)
2. SUM(debit - credit) from journal_lines on posted entries
3. treasury_accounts.current_balance (synced from GL trigger)

Reports any divergences exceeding a configurable tolerance.
"""
import logging
from decimal import Decimal
from sqlalchemy import text

logger = logging.getLogger(__name__)

_TOLERANCE = Decimal("0.01")


def reconcile_account_balances(db) -> list[dict]:
    """Compare accounts.balance against aggregate journal_lines for posted entries.

    Returns a list of divergence dicts (empty list = all OK).
    Each dict: {account_id, account_number, name, trigger_balance, computed_balance, diff}
    """
    rows = db.execute(text("""
        SELECT
            a.id,
            a.account_number,
            a.name,
            a.balance AS trigger_balance,
            COALESCE(agg.net, 0) AS computed_balance
        FROM accounts a
        LEFT JOIN (
            SELECT jl.account_id,
                   SUM(jl.debit) - SUM(jl.credit) AS net
            FROM journal_lines jl
            JOIN journal_entries je ON jl.journal_entry_id = je.id
            WHERE je.status = 'posted'
            GROUP BY jl.account_id
        ) agg ON agg.account_id = a.id
        WHERE a.is_header = FALSE
    """)).fetchall()

    divergences = []
    for r in rows:
        trigger_bal = Decimal(str(r.trigger_balance or 0))
        computed_bal = Decimal(str(r.computed_balance or 0))
        diff = abs(trigger_bal - computed_bal)
        if diff > _TOLERANCE:
            divergences.append({
                "account_id": r.id,
                "account_number": r.account_number,
                "name": r.name,
                "trigger_balance": str(trigger_bal),
                "computed_balance": str(computed_bal),
                "diff": str(diff),
            })
    return divergences


def reconcile_treasury_balances(db) -> list[dict]:
    """Compare treasury_accounts.current_balance against linked accounts.balance.

    Returns a list of divergence dicts (empty list = all OK).
    Each dict: {treasury_id, treasury_name, gl_account_id, treasury_balance, gl_balance, diff}
    """
    rows = db.execute(text("""
        SELECT
            t.id AS treasury_id,
            t.name AS treasury_name,
            t.gl_account_id,
            t.current_balance AS treasury_balance,
            a.balance AS gl_balance
        FROM treasury_accounts t
        JOIN accounts a ON t.gl_account_id = a.id
        WHERE t.gl_account_id IS NOT NULL
    """)).fetchall()

    divergences = []
    for r in rows:
        t_bal = Decimal(str(r.treasury_balance or 0))
        gl_bal = Decimal(str(r.gl_balance or 0))
        diff = abs(t_bal - gl_bal)
        if diff > _TOLERANCE:
            divergences.append({
                "treasury_id": r.treasury_id,
                "treasury_name": r.treasury_name,
                "gl_account_id": r.gl_account_id,
                "treasury_balance": str(t_bal),
                "gl_balance": str(gl_bal),
                "diff": str(diff),
            })
    return divergences


def run_full_reconciliation(db) -> dict:
    """Run both account and treasury reconciliation. Returns combined report."""
    acct = reconcile_account_balances(db)
    treas = reconcile_treasury_balances(db)
    return {
        "account_divergences": acct,
        "treasury_divergences": treas,
        "account_divergence_count": len(acct),
        "treasury_divergence_count": len(treas),
        "is_clean": len(acct) == 0 and len(treas) == 0,
    }
