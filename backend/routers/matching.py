"""
AMAN ERP — Three-Way Matching Router
Endpoints for viewing match results, approving/rejecting held matches,
and managing tolerance configurations.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import text

from database import get_db_connection
from routers.auth import get_current_user
from utils.permissions import require_permission, require_module, validate_branch_access

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/buying",
    tags=["Three-Way Matching"],
    dependencies=[Depends(require_module("buying"))],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class MatchActionRequest(BaseModel):
    exception_notes: Optional[str] = None


class ToleranceSave(BaseModel):
    id: Optional[int] = None
    name: str
    quantity_percent: float = 0
    quantity_absolute: float = 0
    price_percent: float = 0
    price_absolute: float = 0
    supplier_id: Optional[int] = None
    product_category_id: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_company_id(current_user):
    return (
        current_user.get("company_id")
        if isinstance(current_user, dict)
        else current_user.company_id
    )


def _get_user_id(current_user):
    uid = (
        current_user.get("user_id")
        if isinstance(current_user, dict)
        else getattr(current_user, "user_id", None)
    )
    return uid


# ---------------------------------------------------------------------------
# Match listing & detail
# ---------------------------------------------------------------------------

@router.get("/matches", dependencies=[Depends(require_permission("buying.view"))])
def list_matches(
    status: Optional[str] = None,
    branch_id: Optional[int] = Query(None),
    current_user=Depends(get_current_user),
):
    company_id = _get_company_id(current_user)
    resolved_branch = validate_branch_access(current_user, branch_id)
    db = get_db_connection(company_id)
    try:
        q = """
            SELECT m.id, m.purchase_order_id, m.invoice_id, m.match_status,
                   m.matched_at, m.matched_by, m.exception_notes,
                   po.po_number,
                   COALESCE(inv.invoice_number, '') AS invoice_number,
                   COALESCE(p.name, '') AS supplier_name
            FROM three_way_matches m
            LEFT JOIN purchase_orders po ON po.id = m.purchase_order_id
            LEFT JOIN invoices inv ON inv.id = m.invoice_id
            LEFT JOIN parties p ON p.id = po.supplier_id
            WHERE m.is_deleted = false
        """
        params = {}
        if status:
            q += " AND m.match_status = :status"
            params["status"] = status
        if resolved_branch is not None:
            q += " AND po.branch_id = :branch_id"
            params["branch_id"] = resolved_branch
        q += " ORDER BY m.id DESC"
        rows = db.execute(text(q), params).fetchall()
        return [
            {
                "id": r.id,
                "purchase_order_id": r.purchase_order_id,
                "invoice_id": r.invoice_id,
                "match_status": r.match_status,
                "matched_at": r.matched_at.isoformat() if r.matched_at else None,
                "po_number": r.po_number,
                "invoice_number": r.invoice_number,
                "supplier_name": r.supplier_name,
                "exception_notes": r.exception_notes,
            }
            for r in rows
        ]
    finally:
        db.close()


@router.get("/matches/{match_id}", dependencies=[Depends(require_permission("buying.view"))])
def get_match(match_id: int, current_user=Depends(get_current_user)):
    company_id = _get_company_id(current_user)
    db = get_db_connection(company_id)
    try:
        row = db.execute(text("""
            SELECT m.id, m.purchase_order_id, m.invoice_id, m.match_status,
                   m.matched_at, m.matched_by, m.exception_approved_by,
                   m.exception_notes,
                   po.po_number,
                   COALESCE(inv.invoice_number, '') AS invoice_number,
                   COALESCE(p.name, '') AS supplier_name
            FROM three_way_matches m
            LEFT JOIN purchase_orders po ON po.id = m.purchase_order_id
            LEFT JOIN invoices inv ON inv.id = m.invoice_id
            LEFT JOIN parties p ON p.id = po.supplier_id
            WHERE m.id = :mid AND m.is_deleted = false
        """), {"mid": match_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Match not found")

        # Fetch lines
        lines = db.execute(text("""
            SELECT l.id, l.po_line_id, l.invoice_line_id,
                   l.po_quantity, l.received_quantity, l.invoiced_quantity,
                   l.po_unit_price, l.invoiced_unit_price,
                   l.quantity_variance_pct, l.quantity_variance_abs,
                   l.price_variance_pct, l.price_variance_abs,
                   l.line_status
            FROM three_way_match_lines l
            WHERE l.match_id = :mid AND l.is_deleted = false
            ORDER BY l.id
        """), {"mid": match_id}).fetchall()

        return {
            "id": row.id,
            "purchase_order_id": row.purchase_order_id,
            "invoice_id": row.invoice_id,
            "match_status": row.match_status,
            "matched_at": row.matched_at.isoformat() if row.matched_at else None,
            "po_number": row.po_number,
            "invoice_number": row.invoice_number,
            "supplier_name": row.supplier_name,
            "exception_notes": row.exception_notes,
            "lines": [
                {
                    "id": ln.id,
                    "po_line_id": ln.po_line_id,
                    "invoice_line_id": ln.invoice_line_id,
                    "po_quantity": float(ln.po_quantity or 0),
                    "received_quantity": float(ln.received_quantity or 0),
                    "invoiced_quantity": float(ln.invoiced_quantity or 0),
                    "po_unit_price": float(ln.po_unit_price or 0),
                    "invoiced_unit_price": float(ln.invoiced_unit_price or 0),
                    "quantity_variance_pct": float(ln.quantity_variance_pct or 0),
                    "quantity_variance_abs": float(ln.quantity_variance_abs or 0),
                    "price_variance_pct": float(ln.price_variance_pct or 0),
                    "price_variance_abs": float(ln.price_variance_abs or 0),
                    "line_status": ln.line_status,
                }
                for ln in lines
            ],
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Approve / Reject held matches
# ---------------------------------------------------------------------------

@router.put("/matches/{match_id}/approve", dependencies=[Depends(require_permission("buying.edit"))])
def approve_match(
    match_id: int,
    body: MatchActionRequest,
    current_user=Depends(get_current_user),
):
    company_id = _get_company_id(current_user)
    user_id = _get_user_id(current_user)
    db = get_db_connection(company_id)
    try:
        row = db.execute(text(
            "SELECT id, match_status FROM three_way_matches WHERE id = :mid AND is_deleted = false"
        ), {"mid": match_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Match not found")
        if row.match_status not in ("held",):
            raise HTTPException(status_code=400, detail="Only held matches can be approved")
        db.execute(text("""
            UPDATE three_way_matches
            SET match_status = 'approved_with_exception',
                exception_approved_by = :uid,
                exception_notes = :notes,
                updated_at = NOW()
            WHERE id = :mid
        """), {"mid": match_id, "uid": user_id, "notes": body.exception_notes})
        db.commit()
        return {"detail": "Match approved with exception"}
    finally:
        db.close()


@router.put("/matches/{match_id}/reject", dependencies=[Depends(require_permission("buying.edit"))])
def reject_match(
    match_id: int,
    body: MatchActionRequest,
    current_user=Depends(get_current_user),
):
    company_id = _get_company_id(current_user)
    user_id = _get_user_id(current_user)
    db = get_db_connection(company_id)
    try:
        row = db.execute(text(
            "SELECT id, match_status FROM three_way_matches WHERE id = :mid AND is_deleted = false"
        ), {"mid": match_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Match not found")
        if row.match_status not in ("held",):
            raise HTTPException(status_code=400, detail="Only held matches can be rejected")
        db.execute(text("""
            UPDATE three_way_matches
            SET match_status = 'rejected',
                exception_approved_by = :uid,
                exception_notes = :notes,
                updated_at = NOW()
            WHERE id = :mid
        """), {"mid": match_id, "uid": user_id, "notes": body.exception_notes})
        db.commit()
        return {"detail": "Match rejected"}
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tolerance configuration
# ---------------------------------------------------------------------------

@router.get("/tolerances", dependencies=[Depends(require_permission("buying.view"))])
def list_tolerances(current_user=Depends(get_current_user)):
    company_id = _get_company_id(current_user)
    db = get_db_connection(company_id)
    try:
        rows = db.execute(text(
            "SELECT * FROM match_tolerances WHERE is_deleted = false ORDER BY id"
        )).fetchall()
        return [
            {
                "id": r.id,
                "name": r.name,
                "quantity_percent": float(r.quantity_percent or 0),
                "quantity_absolute": float(r.quantity_absolute or 0),
                "price_percent": float(r.price_percent or 0),
                "price_absolute": float(r.price_absolute or 0),
                "supplier_id": r.supplier_id,
                "product_category_id": r.product_category_id,
            }
            for r in rows
        ]
    finally:
        db.close()


@router.post("/tolerances", dependencies=[Depends(require_permission("buying.edit"))])
def save_tolerance(body: ToleranceSave, current_user=Depends(get_current_user)):
    company_id = _get_company_id(current_user)
    user_id = _get_user_id(current_user)
    db = get_db_connection(company_id)
    try:
        if body.id:
            # Update existing
            existing = db.execute(text(
                "SELECT id FROM match_tolerances WHERE id = :tid AND is_deleted = false"
            ), {"tid": body.id}).fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="Tolerance not found")
            db.execute(text("""
                UPDATE match_tolerances
                SET name = :name, quantity_percent = :qp, quantity_absolute = :qa,
                    price_percent = :pp, price_absolute = :pa,
                    supplier_id = :sid, product_category_id = :cid,
                    updated_by = :uid, updated_at = NOW()
                WHERE id = :tid
            """), {
                "tid": body.id, "name": body.name,
                "qp": body.quantity_percent, "qa": body.quantity_absolute,
                "pp": body.price_percent, "pa": body.price_absolute,
                "sid": body.supplier_id, "cid": body.product_category_id,
                "uid": str(user_id) if user_id else None,
            })
            db.commit()
            return {"id": body.id, "detail": "Tolerance updated"}
        else:
            # Create new
            result = db.execute(text("""
                INSERT INTO match_tolerances
                    (name, quantity_percent, quantity_absolute, price_percent, price_absolute,
                     supplier_id, product_category_id, created_by)
                VALUES (:name, :qp, :qa, :pp, :pa, :sid, :cid, :uid)
                RETURNING id
            """), {
                "name": body.name,
                "qp": body.quantity_percent, "qa": body.quantity_absolute,
                "pp": body.price_percent, "pa": body.price_absolute,
                "sid": body.supplier_id, "cid": body.product_category_id,
                "uid": str(user_id) if user_id else None,
            })
            new_id = result.scalar()
            db.commit()
            return {"id": new_id, "detail": "Tolerance created"}
    finally:
        db.close()
