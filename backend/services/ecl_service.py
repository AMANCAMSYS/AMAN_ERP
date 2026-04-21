"""
TASK-037 — IFRS 9 Expected Credit Loss (ECL) provision service.

Computes simplified-approach ECL on trade receivables using the aging-bucket
loss-rate matrix (`ecl_rate_matrix`). Intended to run monthly (or on-demand)
and record results in `ecl_provisions`. JE posting is OPTIONAL and requires
the caller to provide the provision/expense account ids — wiring those into
the Chart of Accounts is a tenant-specific configuration decision.

This is a scaffold — the bucket boundaries and loss rates ship as a
reasonable default and can be tuned per-tenant by editing `ecl_rate_matrix`.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import text

logger = logging.getLogger(__name__)


def compute_ecl_provision(
    db,
    as_of_date: Optional[date] = None,
    post_journal: bool = False,
    provision_account_id: Optional[int] = None,
    expense_account_id: Optional[int] = None,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
):
    """
    Returns a dict: {as_of_date, total_exposure, provision_amount, buckets:[...], provision_id}.

    If `post_journal=True`, also posts a JE (Dr: Expense, Cr: Provision) via
    `gl_service.create_journal_entry`. Caller must supply account ids.
    """
    as_of = as_of_date or date.today()
    buckets = db.execute(text("""
        SELECT id, bucket_label, min_days_overdue, max_days_overdue, loss_rate
        FROM ecl_rate_matrix WHERE is_active = TRUE
        ORDER BY min_days_overdue
    """)).fetchall()
    if not buckets:
        raise RuntimeError("ecl_rate_matrix is empty — seed TASK-037 defaults first")

    # Aging query against customer AR — relies on customer_balances or a
    # receivables view; fall back to sales_invoices if that view is missing.
    rows = db.execute(text("""
        SELECT
            customer_id,
            GREATEST(0, (:as_of - due_date)::int) AS days_overdue,
            SUM(COALESCE(balance, 0)) AS exposure
        FROM sales_invoices
        WHERE status IN ('posted', 'partially_paid')
          AND due_date IS NOT NULL
          AND COALESCE(balance, 0) > 0
        GROUP BY customer_id, days_overdue
    """), {"as_of": as_of}).fetchall()

    total_exposure = Decimal("0")
    total_provision = Decimal("0")
    bucket_summary = {b.bucket_label: {"exposure": Decimal("0"), "provision": Decimal("0"), "rate": b.loss_rate} for b in buckets}

    for row in rows:
        exposure = Decimal(str(row.exposure or 0))
        days = int(row.days_overdue or 0)
        matched = None
        for b in buckets:
            hi = b.max_days_overdue if b.max_days_overdue is not None else 10**9
            if b.min_days_overdue <= days <= hi:
                matched = b
                break
        if not matched:
            continue
        provision = (exposure * Decimal(str(matched.loss_rate))).quantize(Decimal("0.01"))
        bucket_summary[matched.bucket_label]["exposure"] += exposure
        bucket_summary[matched.bucket_label]["provision"] += provision
        total_exposure += exposure
        total_provision += provision

    details = {k: {"exposure": str(v["exposure"]), "provision": str(v["provision"]), "rate": str(v["rate"])}
               for k, v in bucket_summary.items()}

    journal_entry_id = None
    if post_journal and total_provision > 0:
        if not (provision_account_id and expense_account_id):
            raise ValueError("post_journal=True requires provision_account_id + expense_account_id")
        from services.gl_service import create_journal_entry
        journal_entry_id, _ = create_journal_entry(
            db,
            entry_date=as_of,
            description=f"IFRS 9 ECL provision as of {as_of}",
            lines=[
                {"account_id": expense_account_id, "debit": total_provision, "credit": 0,
                 "description": "ECL expense (IFRS 9)"},
                {"account_id": provision_account_id, "debit": 0, "credit": total_provision,
                 "description": "Allowance for credit losses"},
            ],
            source="ecl_provision",
            source_id=None,
            user_id=user_id,
            username=username or "ecl_service",
            status="posted",
        )

    ins = db.execute(text("""
        INSERT INTO ecl_provisions (as_of_date, customer_id, total_exposure, provision_amount, details, journal_entry_id)
        VALUES (:dt, NULL, :exp, :prov, CAST(:details AS JSONB), :jeid)
        RETURNING id
    """), {
        "dt": as_of,
        "exp": str(total_exposure),
        "prov": str(total_provision),
        "details": _json_dumps(details),
        "jeid": journal_entry_id,
    })
    provision_id = ins.scalar()
    db.commit()

    return {
        "provision_id": provision_id,
        "as_of_date": str(as_of),
        "total_exposure": str(total_exposure),
        "provision_amount": str(total_provision),
        "buckets": details,
        "journal_entry_id": journal_entry_id,
    }


def _json_dumps(obj) -> str:
    import json
    return json.dumps(obj, default=str, ensure_ascii=False)
