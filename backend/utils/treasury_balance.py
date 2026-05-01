"""Treasury balance recomputation helper.

T1.3a — Single source of truth for `treasury_accounts.current_balance`.

Rationale
---------
Historically, every business path that posts a journal entry touching a
treasury's GL account also issued a manual::

    UPDATE treasury_accounts
       SET current_balance = current_balance ± :amt
     WHERE id = :id

This created two divergent sources of truth:
  * `accounts.balance` — kept in sync by the GL trigger on every JE posting.
  * `treasury_accounts.current_balance` — maintained by ad-hoc ± delta
    UPDATEs in 17 places (audit item P0 #3).

Any forgotten/duplicated ± would silently desync the cash-on-hand reported
to users from the GL truth.

Approach
--------
This helper recomputes `current_balance` **idempotently** from posted
journal lines on the linked `gl_account_id`, respecting the treasury's
denominated currency:

  * SAR / null currency → use base-currency net (`SUM(debit) - SUM(credit)`).
  * Foreign currency    → use `amount_currency` with debit/credit sign.

Call sites replace ad-hoc ± UPDATEs with::

    from utils.treasury_balance import recalc_treasury_from_gl
    recalc_treasury_from_gl(db, treasury_id)

after any JE posting that affected the treasury. The result is independent
of how many times the helper is called and self-heals any prior drift.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import text


def recalc_treasury_from_gl(db, treasury_id: int) -> Optional[Decimal]:
    """Recompute `treasury_accounts.current_balance` from posted JE lines.

    Returns the new balance, or None if the treasury does not exist or has
    no linked GL account (in which case current_balance is left untouched).

    Safe to call multiple times — always derives the same value from the
    underlying journal_lines on the linked gl_account_id.
    """
    info = db.execute(
        text(
            """
            SELECT gl_account_id, currency
            FROM treasury_accounts
            WHERE id = :id
            """
        ),
        {"id": treasury_id},
    ).fetchone()
    if not info or not info.gl_account_id:
        return None

    # Foreign-currency treasury: balance is denominated in the treasury's
    # currency, which matches `journal_lines.amount_currency` whenever the
    # line was posted under that currency.
    use_fc = bool(info.currency) and info.currency.upper() != "SAR"

    if use_fc:
        row = db.execute(
            text(
                """
                SELECT COALESCE(SUM(
                    CASE WHEN jl.debit  > 0 THEN COALESCE(jl.amount_currency, jl.debit)
                         WHEN jl.credit > 0 THEN -COALESCE(jl.amount_currency, jl.credit)
                         ELSE 0 END
                ), 0) AS bal
                FROM journal_lines jl
                JOIN journal_entries je ON je.id = jl.journal_entry_id
                WHERE jl.account_id = :acc
                  AND je.status = 'posted'
                  AND (jl.currency IS NULL OR jl.currency = :curr)
                """
            ),
            {"acc": info.gl_account_id, "curr": info.currency},
        ).fetchone()
    else:
        row = db.execute(
            text(
                """
                SELECT COALESCE(SUM(jl.debit) - SUM(jl.credit), 0) AS bal
                FROM journal_lines jl
                JOIN journal_entries je ON je.id = jl.journal_entry_id
                WHERE jl.account_id = :acc
                  AND je.status = 'posted'
                """
            ),
            {"acc": info.gl_account_id},
        ).fetchone()

    new_balance = Decimal(str(row.bal or 0))
    db.execute(
        text(
            "UPDATE treasury_accounts SET current_balance = :bal, updated_at = NOW() WHERE id = :id"
        ),
        {"bal": new_balance, "id": treasury_id},
    )
    return new_balance
