"""Cash-flow forecast generation service.

Generates forecast lines from open AR/AP invoices and recurring journal
entries, then computes a running balance per bank account + consolidated.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import text

logger = logging.getLogger(__name__)

_ZERO = Decimal("0")
_D4 = Decimal("0.0001")


def _dec(val) -> Decimal:
    if val is None:
        return _ZERO
    return Decimal(str(val))


def generate_cashflow_forecast(
    db,
    *,
    name: str,
    horizon_days: int,
    mode: str,
    user_id: int,
) -> dict:
    """Build a cashflow forecast and persist it.

    Returns dict with ``forecast_id`` and ``line_count``.
    """
    today = date.today()
    end_date = today + timedelta(days=horizon_days)

    # 1) Create the forecast header
    row = db.execute(
        text(
            "INSERT INTO cashflow_forecasts (name, forecast_date, horizon_days, mode, generated_by) "
            "VALUES (:name, :fd, :hd, :mode, :uid) RETURNING id"
        ),
        {"name": name, "fd": today, "hd": horizon_days, "mode": mode, "uid": user_id},
    ).fetchone()
    forecast_id = row[0]

    # 2) Collect projected cash-flow items
    lines: list[dict] = []

    # --- AR (receivables): open sales invoices with due_date in horizon ---
    ar_sql = text(
        "SELECT id, due_date, (total - paid_amount) AS balance "
        "FROM invoices "
        "WHERE invoice_type = 'sales' AND status NOT IN ('paid','cancelled','draft') "
        "  AND due_date BETWEEN :start AND :end "
        "  AND (total - paid_amount) > 0"
    )
    for inv in db.execute(ar_sql, {"start": today, "end": end_date}):
        due = inv.due_date
        if mode == "expected":
            # Shift by average collection lag (simple: +7 days)
            due = due + timedelta(days=7)
            if due > end_date:
                continue
        lines.append({
            "date": due,
            "bank_account_id": None,
            "source_type": "ar",
            "source_document_id": inv.id,
            "inflow": _dec(inv.balance),
            "outflow": _ZERO,
        })

    # --- AP (payables): open purchase invoices with due_date in horizon ---
    ap_sql = text(
        "SELECT id, due_date, (total - paid_amount) AS balance "
        "FROM invoices "
        "WHERE invoice_type = 'purchase' AND status NOT IN ('paid','cancelled','draft') "
        "  AND due_date BETWEEN :start AND :end "
        "  AND (total - paid_amount) > 0"
    )
    for inv in db.execute(ap_sql, {"start": today, "end": end_date}):
        due = inv.due_date
        if mode == "expected":
            due = due + timedelta(days=3)
            if due > end_date:
                continue
        lines.append({
            "date": due,
            "bank_account_id": None,
            "source_type": "ap",
            "source_document_id": inv.id,
            "inflow": _ZERO,
            "outflow": _dec(inv.balance),
        })

    # --- Recurring journal entries ---
    rec_sql = text(
        "SELECT id, next_run_date, total_amount "
        "FROM recurring_journal_templates "
        "WHERE is_active = true AND next_run_date BETWEEN :start AND :end"
    )
    for rec in db.execute(rec_sql, {"start": today, "end": end_date}):
        amt = _dec(rec.total_amount)
        lines.append({
            "date": rec.next_run_date,
            "bank_account_id": None,
            "source_type": "recurring",
            "source_document_id": rec.id,
            "inflow": amt if amt > 0 else _ZERO,
            "outflow": abs(amt) if amt < 0 else _ZERO,
        })

    # 3) Sort by date and compute running balance
    lines.sort(key=lambda l: l["date"])
    running_balance = _ZERO
    for line in lines:
        running_balance += line["inflow"] - line["outflow"]
        line["balance"] = running_balance

    # 4) Persist lines
    if lines:
        insert_sql = text(
            "INSERT INTO cashflow_forecast_lines "
            "(forecast_id, date, bank_account_id, source_type, source_document_id, "
            " projected_inflow, projected_outflow, projected_balance) "
            "VALUES (:fid, :dt, :ba, :st, :sd, :inf, :out, :bal)"
        )
        for line in lines:
            db.execute(insert_sql, {
                "fid": forecast_id,
                "dt": line["date"],
                "ba": line["bank_account_id"],
                "st": line["source_type"],
                "sd": line["source_document_id"],
                "inf": line["inflow"],
                "out": line["outflow"],
                "bal": line["balance"],
            })

    db.commit()
    logger.info("Forecast %s created with %d lines (horizon=%d, mode=%s)",
                forecast_id, len(lines), horizon_days, mode)
    return {"forecast_id": forecast_id, "line_count": len(lines)}
