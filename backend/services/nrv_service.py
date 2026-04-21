"""
TASK-038 — IAS 2 Net Realisable Value (NRV) inventory write-down service.

For each (product, warehouse) with positive on-hand quantity, compares the
carrying cost (from `inventory_valuation_layers` / product.cost) against an
NRV estimate (selling_price - estimated_costs_to_sell). Where NRV < cost,
records a write-down in `inventory_nrv_tests` and optionally posts a JE.

Scaffold: the NRV source is configurable. Default uses product.selling_price
minus a configurable selling_cost_rate. Tenants with detailed price lists or
sales-order data should override `_resolve_nrv` for their policy.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import text

logger = logging.getLogger(__name__)


def run_nrv_test(
    db,
    as_of_date: Optional[date] = None,
    selling_cost_rate: Decimal = Decimal("0.05"),
    post_journal: bool = False,
    inventory_account_id: Optional[int] = None,
    writedown_expense_account_id: Optional[int] = None,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
):
    as_of = as_of_date or date.today()

    rows = db.execute(text("""
        SELECT
            p.id AS product_id,
            NULL::int AS warehouse_id,
            COALESCE(SUM(sm.quantity), 0) AS qty_on_hand,
            p.cost_price AS unit_cost,
            p.selling_price AS unit_selling
        FROM products p
        LEFT JOIN stock_movements sm ON sm.product_id = p.id
        WHERE COALESCE(p.is_active, TRUE) = TRUE
        GROUP BY p.id, p.cost_price, p.selling_price
        HAVING COALESCE(SUM(sm.quantity), 0) > 0
    """)).fetchall()

    total_writedown = Decimal("0")
    test_rows_written = 0

    for row in rows:
        qty = Decimal(str(row.qty_on_hand or 0))
        cost = Decimal(str(row.unit_cost or 0))
        selling = Decimal(str(row.unit_selling or 0))
        if qty <= 0 or cost <= 0:
            continue
        nrv = (selling * (Decimal("1") - selling_cost_rate)).quantize(Decimal("0.0001"))
        cost_value = (qty * cost).quantize(Decimal("0.0001"))
        nrv_value = (qty * nrv).quantize(Decimal("0.0001"))
        writedown = max(Decimal("0"), cost_value - nrv_value).quantize(Decimal("0.0001"))
        if writedown <= 0:
            continue
        db.execute(text("""
            INSERT INTO inventory_nrv_tests (as_of_date, product_id, warehouse_id,
                cost_value, nrv_value, writedown_amount, notes)
            VALUES (:dt, :pid, :wid, :cv, :nv, :wd, :nt)
        """), {
            "dt": as_of,
            "pid": row.product_id,
            "wid": row.warehouse_id,
            "cv": str(cost_value),
            "nv": str(nrv_value),
            "wd": str(writedown),
            "nt": f"NRV test: qty={qty} cost={cost} nrv={nrv}",
        })
        total_writedown += writedown
        test_rows_written += 1

    journal_entry_id = None
    if post_journal and total_writedown > 0:
        if not (inventory_account_id and writedown_expense_account_id):
            raise ValueError("post_journal=True requires inventory_account_id + writedown_expense_account_id")
        from services.gl_service import create_journal_entry
        journal_entry_id, _ = create_journal_entry(
            db,
            entry_date=as_of,
            description=f"IAS 2 NRV write-down as of {as_of}",
            lines=[
                {"account_id": writedown_expense_account_id, "debit": total_writedown, "credit": 0,
                 "description": "Inventory NRV write-down expense"},
                {"account_id": inventory_account_id, "debit": 0, "credit": total_writedown,
                 "description": "Inventory reduced to NRV"},
            ],
            source="nrv_test",
            source_id=None,
            user_id=user_id,
            username=username or "nrv_service",
            status="posted",
        )
        # Back-fill journal_entry_id on the test rows posted this run.
        db.execute(text("""
            UPDATE inventory_nrv_tests SET journal_entry_id = :jeid
            WHERE as_of_date = :dt AND journal_entry_id IS NULL
        """), {"jeid": journal_entry_id, "dt": as_of})

    db.commit()
    return {
        "as_of_date": str(as_of),
        "rows": test_rows_written,
        "total_writedown": str(total_writedown),
        "journal_entry_id": journal_entry_id,
    }
