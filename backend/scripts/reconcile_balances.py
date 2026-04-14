#!/usr/bin/env python3
"""
Balance Reconciliation Script
Verifies that cached balances match their source-of-truth sub-ledgers:
  1. accounts.balance == SUM(debit-credit) FROM journal_lines WHERE status='posted'
  2. treasury_accounts.current_balance == linked accounts.balance (converted to treasury currency)
  3. parties.current_balance == SUM(debit-credit) FROM party_transactions
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from config import settings

def get_company_dbs():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT database_name FROM system_companies WHERE status = 'active'")).fetchall()
    engine.dispose()
    dbs = []
    for r in rows:
        db_name = r[0]
        url = settings.DATABASE_URL.rsplit("/", 1)[0] + "/" + db_name
        try:
            e = create_engine(url)
            with e.connect() as c:
                c.execute(text("SELECT 1"))
            dbs.append((db_name, url))
            e.dispose()
        except Exception:
            pass
    return dbs


def check_account_balances(conn, fix=False):
    """Check accounts.balance vs SUM from journal_lines (posted entries only)"""
    rows = conn.execute(text("""
        SELECT a.id, a.account_number, a.name,
               COALESCE(a.balance, 0) AS cached_balance,
               COALESCE(gl.computed, 0) AS computed_balance
        FROM accounts a
        LEFT JOIN (
            SELECT jl.account_id,
                   SUM(jl.debit - jl.credit) AS computed
            FROM journal_lines jl
            JOIN journal_entries je ON je.id = jl.journal_entry_id
            WHERE je.status = 'posted'
            GROUP BY jl.account_id
        ) gl ON gl.account_id = a.id
        WHERE ABS(COALESCE(a.balance, 0) - COALESCE(gl.computed, 0)) > 0.01
        ORDER BY ABS(COALESCE(a.balance, 0) - COALESCE(gl.computed, 0)) DESC
    """)).fetchall()

    if not rows:
        print("  ✓ All account balances match journal_lines")
        return 0

    print(f"  ✗ {len(rows)} account balance mismatches:")
    for r in rows:
        diff = float(r.cached_balance) - float(r.computed_balance)
        print(f"    Account {r.account_number} ({r.name}): cached={r.cached_balance}, computed={r.computed_balance}, diff={diff:+.2f}")

    if fix:
        conn.execute(text("""
            UPDATE accounts a SET balance = CAST(COALESCE(sub.computed, 0) AS NUMERIC(18,4))
            FROM (
                SELECT jl.account_id,
                       CAST(SUM(jl.debit - jl.credit) AS NUMERIC(18,4)) AS computed
                FROM journal_lines jl
                JOIN journal_entries je ON je.id = jl.journal_entry_id
                WHERE je.status = 'posted'
                GROUP BY jl.account_id
            ) sub
            WHERE sub.account_id = a.id
              AND ABS(COALESCE(a.balance, 0) - COALESCE(sub.computed, 0)) > 0.01
        """))
        # Also zero out accounts with no journal lines
        conn.execute(text("""
            UPDATE accounts SET balance = CAST(0 AS NUMERIC(18,4))
            WHERE balance != 0
              AND id NOT IN (
                  SELECT DISTINCT jl.account_id FROM journal_lines jl
                  JOIN journal_entries je ON je.id = jl.journal_entry_id
                  WHERE je.status = 'posted'
              )
        """))
        conn.commit()
        print(f"    → Fixed {len(rows)} account balances")

    return len(rows)


def check_treasury_balances(conn, fix=False):
    """Check treasury_accounts.current_balance vs linked GL account balance"""
    rows = conn.execute(text("""
        SELECT ta.id, ta.name, ta.currency,
               COALESCE(ta.current_balance, 0) AS cached_balance,
               CASE
                   WHEN ta.currency IS NOT NULL AND ta.currency != '' THEN
                       COALESCE(a.balance_currency, a.balance, 0)
                   ELSE
                       COALESCE(a.balance, 0)
               END AS gl_balance
        FROM treasury_accounts ta
        JOIN accounts a ON a.id = ta.gl_account_id
        WHERE ta.is_active = TRUE
          AND ABS(
              COALESCE(ta.current_balance, 0) -
              CASE
                  WHEN ta.currency IS NOT NULL AND ta.currency != '' THEN
                      COALESCE(a.balance_currency, a.balance, 0)
                  ELSE
                      COALESCE(a.balance, 0)
              END
          ) > 0.01
    """)).fetchall()

    if not rows:
        print("  ✓ All treasury balances match GL accounts")
        return 0

    print(f"  ✗ {len(rows)} treasury balance mismatches:")
    for r in rows:
        print(f"    Treasury '{r.name}' ({r.currency}): cached={r.cached_balance}, GL={r.gl_balance}")

    if fix:
        conn.execute(text("""
            UPDATE treasury_accounts ta
            SET current_balance = CAST(CASE
                WHEN ta.currency IS NOT NULL AND ta.currency != '' THEN
                    COALESCE(a.balance_currency, a.balance, 0)
                ELSE
                    COALESCE(a.balance, 0)
            END AS NUMERIC(18,4))
            FROM accounts a
            WHERE a.id = ta.gl_account_id
              AND ta.is_active = TRUE
              AND ABS(
                  COALESCE(ta.current_balance, 0) -
                  CASE
                      WHEN ta.currency IS NOT NULL AND ta.currency != '' THEN
                          COALESCE(a.balance_currency, a.balance, 0)
                      ELSE
                          COALESCE(a.balance, 0)
                  END
              ) > 0.01
        """))
        conn.commit()
        print(f"    → Fixed {len(rows)} treasury balances")

    return len(rows)


def check_party_balances(conn, fix=False):
    """Check parties.current_balance vs SUM from party_transactions"""
    rows = conn.execute(text("""
        SELECT p.id, p.name, p.party_type,
               COALESCE(p.current_balance, 0) AS cached_balance,
               COALESCE(pt.computed, 0) AS computed_balance
        FROM parties p
        LEFT JOIN (
            SELECT party_id,
                   SUM(debit - credit) AS computed
            FROM party_transactions
            GROUP BY party_id
        ) pt ON pt.party_id = p.id
        WHERE ABS(COALESCE(p.current_balance, 0) - COALESCE(pt.computed, 0)) > 0.01
        ORDER BY ABS(COALESCE(p.current_balance, 0) - COALESCE(pt.computed, 0)) DESC
    """)).fetchall()

    if not rows:
        print("  ✓ All party balances match party_transactions")
        return 0

    print(f"  ✗ {len(rows)} party balance mismatches:")
    for r in rows:
        diff = float(r.cached_balance) - float(r.computed_balance)
        print(f"    Party '{r.name}' ({r.party_type}): cached={r.cached_balance}, tx_sum={r.computed_balance}, diff={diff:+.2f}")

    if fix:
        conn.execute(text("""
            UPDATE parties p SET current_balance = CAST(COALESCE(sub.computed, 0) AS NUMERIC(18,4))
            FROM (
                SELECT party_id,
                       CAST(SUM(debit - credit) AS NUMERIC(18,4)) AS computed
                FROM party_transactions
                GROUP BY party_id
            ) sub
            WHERE sub.party_id = p.id
              AND ABS(COALESCE(p.current_balance, 0) - COALESCE(sub.computed, 0)) > 0.01
        """))
        conn.commit()
        print(f"    → Fixed {len(rows)} party balances")

    return len(rows)


def main():
    fix = "--fix" in sys.argv
    if fix:
        print("=== RECONCILIATION (FIX MODE) ===\n")
    else:
        print("=== RECONCILIATION (READ-ONLY) ===")
        print("    Add --fix to auto-correct mismatches\n")

    dbs = get_company_dbs()
    if not dbs:
        print("No active company databases found")
        return

    total_issues = 0
    for db_name, url in dbs:
        print(f"── {db_name} ──")
        engine = create_engine(url)
        with engine.connect() as conn:
            total_issues += check_account_balances(conn, fix)
            total_issues += check_treasury_balances(conn, fix)
            total_issues += check_party_balances(conn, fix)
        engine.dispose()
        print()

    if total_issues == 0:
        print("✓ All balances reconciled across all companies")
    else:
        print(f"✗ {total_issues} total mismatches found")
        if not fix:
            print("  Run with --fix to auto-correct")


if __name__ == "__main__":
    main()
