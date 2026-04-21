"""
TASK-039 — IAS 36 Impairment of Cash-Generating Units (scaffold).

Records impairment test results comparing carrying amount of a CGU against
recoverable amount (max of value-in-use and fair-value-less-costs-to-sell).
When impaired, optionally posts a JE (Dr: Impairment loss, Cr: Accumulated
impairment/asset) via gl_service.

This is a scaffold — determining value-in-use requires discounted cash flow
modelling (management projections + discount rate), which is a policy
decision per tenant. The service accepts pre-computed figures.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import text

logger = logging.getLogger(__name__)


def record_impairment_test(
    db,
    cgu_id: int,
    carrying_amount: Decimal,
    value_in_use: Optional[Decimal] = None,
    fair_value_less_costs: Optional[Decimal] = None,
    as_of_date: Optional[date] = None,
    post_journal: bool = False,
    impairment_expense_account_id: Optional[int] = None,
    accumulated_impairment_account_id: Optional[int] = None,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    details: Optional[dict] = None,
):
    as_of = as_of_date or date.today()
    carrying_amount = Decimal(str(carrying_amount))
    viu = Decimal(str(value_in_use)) if value_in_use is not None else None
    fvlcs = Decimal(str(fair_value_less_costs)) if fair_value_less_costs is not None else None

    if viu is None and fvlcs is None:
        raise ValueError("at least one of value_in_use / fair_value_less_costs is required")
    candidates = [v for v in (viu, fvlcs) if v is not None]
    recoverable = max(candidates)

    impairment_loss = max(Decimal("0"), carrying_amount - recoverable).quantize(Decimal("0.01"))

    journal_entry_id = None
    if post_journal and impairment_loss > 0:
        if not (impairment_expense_account_id and accumulated_impairment_account_id):
            raise ValueError("post_journal=True requires both account ids")
        from services.gl_service import create_journal_entry
        journal_entry_id, _ = create_journal_entry(
            db,
            entry_date=as_of,
            description=f"IAS 36 impairment loss CGU#{cgu_id} as of {as_of}",
            lines=[
                {"account_id": impairment_expense_account_id, "debit": impairment_loss, "credit": 0,
                 "description": "Impairment loss (IAS 36)"},
                {"account_id": accumulated_impairment_account_id, "debit": 0, "credit": impairment_loss,
                 "description": "Accumulated impairment"},
            ],
            source="impairment_test",
            source_id=cgu_id,
            user_id=user_id,
            username=username or "impairment_service",
            status="posted",
        )

    import json
    ins = db.execute(text("""
        INSERT INTO impairment_tests (cgu_id, as_of_date, carrying_amount, value_in_use,
            fair_value_less_costs, recoverable_amount, impairment_loss, journal_entry_id, details)
        VALUES (:cgu, :dt, :ca, :viu, :fv, :rec, :loss, :jeid, CAST(:det AS JSONB))
        RETURNING id
    """), {
        "cgu": cgu_id, "dt": as_of,
        "ca": str(carrying_amount),
        "viu": str(viu) if viu is not None else None,
        "fv": str(fvlcs) if fvlcs is not None else None,
        "rec": str(recoverable),
        "loss": str(impairment_loss),
        "jeid": journal_entry_id,
        "det": json.dumps(details or {}, default=str, ensure_ascii=False),
    })
    test_id = ins.scalar()
    db.commit()

    return {
        "test_id": test_id,
        "cgu_id": cgu_id,
        "as_of_date": str(as_of),
        "carrying_amount": str(carrying_amount),
        "recoverable_amount": str(recoverable),
        "impairment_loss": str(impairment_loss),
        "journal_entry_id": journal_entry_id,
    }
