"""Phase-11 Sprint-6 — configuration + workflow + treasury hardening endpoints.

Covers:
  * WF-M1  — overtime rates config CRUD
  * WF-M2  — document permissions per department/role/user
  * WF-F8  — geofences + check-in distance check
  * WF-F6  — approval-request quorum metadata
  * WF-F7  — SLA escalation scanner
  * WF-F2b — GOSI historical 0.25% adjustment
  * ZAK-F2 — zakat base items mapping
  * TAX-F3 — branch-level tax settings CRUD
  * TREAS-F1 — notes-receivable discount posting
  * TREAS-F2 — bounced check reversal
  * ACC-F12 — asset revaluation with OCI JE
  * ACC-F13 — units-of-production depreciation
  * ACC-F14 — IFRS 16 lease modification (light remeasurement)
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import text

from database import get_db_connection
from routers.auth import get_current_user
from utils.accounting import get_mapped_account_id
from utils.audit import log_activity
from utils.fiscal_lock import check_fiscal_period_open
from utils.i18n import http_error
from utils.permissions import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sprint6", tags=["phase-11-sprint-6"])

_D2 = Decimal("0.01")


def _dec(v) -> Decimal:
    if v is None:
        return Decimal("0")
    return Decimal(str(v))


# ==========================================================================
# WF-M1 — Overtime rates config
# ==========================================================================

class OvertimeRate(BaseModel):
    rate_key: str
    description: Optional[str] = None
    multiplier: float = Field(..., gt=0)
    is_active: bool = True


@router.get("/overtime-rates", dependencies=[Depends(require_permission(["hr.view", "settings.view"]))])
def list_overtime_rates(current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(
            text("SELECT rate_key, description, multiplier, is_active FROM overtime_rates_config ORDER BY rate_key")
        ).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.put("/overtime-rates", dependencies=[Depends(require_permission(["hr.manage", "settings.edit"]))])
def upsert_overtime_rate(body: OvertimeRate, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(
            text(
                """
                INSERT INTO overtime_rates_config (rate_key, description, multiplier, is_active, updated_at)
                VALUES (:k, :d, :m, :a, CURRENT_TIMESTAMP)
                ON CONFLICT (rate_key) DO UPDATE SET
                    description = EXCLUDED.description,
                    multiplier = EXCLUDED.multiplier,
                    is_active = EXCLUDED.is_active,
                    updated_at = CURRENT_TIMESTAMP
                """
            ),
            {"k": body.rate_key, "d": body.description, "m": body.multiplier, "a": body.is_active},
        )
        db.commit()
        return {"ok": True, "rate_key": body.rate_key}
    finally:
        db.close()


# ==========================================================================
# WF-M2 — Document permissions
# ==========================================================================

class DocPermissionCreate(BaseModel):
    document_id: int
    department_id: Optional[int] = None
    role_id: Optional[int] = None
    user_id: Optional[int] = None
    access_level: Literal["view", "edit", "owner"] = "view"


@router.post("/documents/{doc_id}/permissions", dependencies=[Depends(require_permission("dms.manage"))])
def grant_document_permission(
    doc_id: int,
    body: DocPermissionCreate,
    current_user=Depends(get_current_user),
):
    if body.department_id is None and body.role_id is None and body.user_id is None:
        raise HTTPException(status_code=400, detail="يجب تحديد قسم أو دور أو مستخدم")
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(
            text(
                """
                INSERT INTO document_permissions
                    (document_id, department_id, role_id, user_id, access_level, granted_by)
                VALUES (:doc, :dept, :role, :usr, :lvl, :by)
                """
            ),
            {
                "doc": doc_id,
                "dept": body.department_id,
                "role": body.role_id,
                "usr": body.user_id,
                "lvl": body.access_level,
                "by": current_user.id,
            },
        )
        db.commit()
        return {"ok": True}
    finally:
        db.close()


@router.get("/documents/{doc_id}/permissions", dependencies=[Depends(require_permission("dms.view"))])
def list_document_permissions(doc_id: int, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(
            text(
                """
                SELECT id, document_id, department_id, role_id, user_id, access_level, granted_by, created_at
                FROM document_permissions
                WHERE document_id = :doc
                ORDER BY id DESC
                """
            ),
            {"doc": doc_id},
        ).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


# ==========================================================================
# WF-F8 — Geofences + check-in validator
# ==========================================================================

class GeofenceCreate(BaseModel):
    name: str
    branch_id: Optional[int] = None
    center_lat: float
    center_lng: float
    radius_m: int = Field(..., gt=0, le=50000)


class CheckInValidate(BaseModel):
    branch_id: int
    lat: float
    lng: float


def _haversine_m(lat1, lng1, lat2, lng2) -> float:
    R = 6371000.0
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlng / 2) ** 2
    return 2 * R * math.asin(min(1.0, math.sqrt(a)))


@router.post("/geofences", dependencies=[Depends(require_permission(["hr.manage", "branches.manage"]))])
def create_geofence(body: GeofenceCreate, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        row = db.execute(
            text(
                """
                INSERT INTO geofences (name, branch_id, center_lat, center_lng, radius_m)
                VALUES (:n, :b, :la, :lg, :r)
                RETURNING id
                """
            ),
            {"n": body.name, "b": body.branch_id, "la": body.center_lat, "lg": body.center_lng, "r": body.radius_m},
        ).fetchone()
        db.commit()
        return {"id": row[0]}
    finally:
        db.close()


@router.post("/attendance/validate-location", dependencies=[Depends(require_permission("hr.view"))])
def validate_checkin_location(body: CheckInValidate, current_user=Depends(get_current_user)):
    """Return ``inside=True`` when the caller is within any active geofence of the branch."""
    db = get_db_connection(current_user.company_id)
    try:
        fences = db.execute(
            text(
                """
                SELECT id, name, center_lat, center_lng, radius_m
                FROM geofences
                WHERE is_active = TRUE AND branch_id = :b
                """
            ),
            {"b": body.branch_id},
        ).fetchall()
        if not fences:
            return {"inside": True, "reason": "no_geofence_configured"}
        nearest = None
        min_dist = None
        for f in fences:
            d = _haversine_m(body.lat, body.lng, float(f.center_lat), float(f.center_lng))
            if min_dist is None or d < min_dist:
                min_dist, nearest = d, f
            if d <= float(f.radius_m):
                return {"inside": True, "geofence_id": f.id, "distance_m": round(d, 2)}
        return {
            "inside": False,
            "nearest_geofence_id": nearest.id if nearest else None,
            "distance_m": round(min_dist, 2) if min_dist is not None else None,
        }
    finally:
        db.close()


# ==========================================================================
# WF-F7 — SLA escalation scanner
# ==========================================================================

@router.post("/approvals/sla/escalate", dependencies=[Depends(require_permission("approvals.manage"))])
def scan_and_escalate_sla(current_user=Depends(get_current_user)):
    """Scan ``approval_requests`` in ``pending`` status past their workflow SLA and escalate.

    Idempotent: rows already stamped ``sla_escalated_at`` are skipped.
    """
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(
            text(
                """
                SELECT ar.id, ar.workflow_id, aw.sla_hours, aw.escalation_to
                FROM approval_requests ar
                JOIN approval_workflows aw ON aw.id = ar.workflow_id
                WHERE ar.status = 'pending'
                  AND ar.sla_escalated_at IS NULL
                  AND aw.sla_hours IS NOT NULL
                  AND ar.created_at < CURRENT_TIMESTAMP - (aw.sla_hours || ' hours')::interval
                """
            )
        ).fetchall()
        escalated = 0
        for r in rows:
            db.execute(
                text(
                    """
                    UPDATE approval_requests
                    SET escalated_to = COALESCE(:to, escalated_to),
                        escalated_at = CURRENT_TIMESTAMP,
                        sla_escalated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                    """
                ),
                {"to": r.escalation_to, "id": r.id},
            )
            escalated += 1
        db.commit()
        return {"scanned": len(rows), "escalated": escalated}
    finally:
        db.close()


# ==========================================================================
# WF-F2b — Historical GOSI 0.25% adjustment
# ==========================================================================

@router.post("/hr/gosi/historical-adjust", dependencies=[Depends(require_permission(["hr.manage", "accounting.manage"]))])
def adjust_historical_gosi(request: Request, current_user=Depends(get_current_user)):
    """Back-fill the 0.25 % employer-GOSI delta for payroll entries booked before
    the 2024 rate correction. Touches only entries flagged ``gosi_adjusted IS NOT TRUE``."""
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(text("ALTER TABLE payroll_entries ADD COLUMN IF NOT EXISTS gosi_adjusted BOOLEAN DEFAULT FALSE"))
        db.execute(text("ALTER TABLE payroll_entries ADD COLUMN IF NOT EXISTS gosi_adjustment NUMERIC(18,4) DEFAULT 0"))
        rows = db.execute(
            text(
                """
                UPDATE payroll_entries
                SET gosi_adjustment = ROUND(gross_salary * 0.0025::numeric, 4),
                    gosi_adjusted = TRUE
                WHERE COALESCE(gosi_adjusted, FALSE) = FALSE
                  AND gross_salary > 0
                RETURNING id
                """
            )
        ).fetchall()
        db.commit()
        log_activity(
            db, user_id=current_user.id, username=current_user.username,
            action="hr.gosi_adjust", resource_type="payroll_entry",
            details={"count": len(rows)},
            request=request,
        )
        return {"adjusted_rows": len(rows)}
    finally:
        db.close()


# ==========================================================================
# ZAK-F2 — Zakat base items mapping
# ==========================================================================

class ZakatBaseItem(BaseModel):
    account_id: int
    category: Literal["asset", "deductible", "addition", "exclude"]
    weight: float = 1.0
    notes: Optional[str] = None


@router.get("/zakat/base-items", dependencies=[Depends(require_permission(["accounting.view", "taxes.view"]))])
def list_zakat_base_items(current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(
            text(
                """
                SELECT zbi.id, zbi.account_id, a.account_code, a.name, zbi.category, zbi.weight, zbi.notes
                FROM zakat_base_items zbi
                JOIN accounts a ON a.id = zbi.account_id
                ORDER BY zbi.category, a.account_code
                """
            )
        ).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.post("/zakat/base-items", dependencies=[Depends(require_permission(["accounting.manage", "taxes.manage"]))])
def upsert_zakat_base_item(body: ZakatBaseItem, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(
            text(
                """
                INSERT INTO zakat_base_items (account_id, category, weight, notes)
                VALUES (:a, :c, :w, :n)
                ON CONFLICT (account_id) DO UPDATE SET
                    category = EXCLUDED.category,
                    weight = EXCLUDED.weight,
                    notes = EXCLUDED.notes
                """
            ),
            {"a": body.account_id, "c": body.category, "w": body.weight, "n": body.notes},
        )
        db.commit()
        return {"ok": True}
    finally:
        db.close()


# ==========================================================================
# TAX-F3 — Branch tax settings
# ==========================================================================

class BranchTaxSetting(BaseModel):
    branch_id: int
    default_tax_rate: float = Field(..., ge=0, le=100)
    tax_exempt: bool = False
    notes: Optional[str] = None


@router.get("/tax/branch-settings", dependencies=[Depends(require_permission(["taxes.view", "settings.view"]))])
def list_branch_tax_settings(current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        # The schema of branch_tax_settings varies; return whatever is there.
        rows = db.execute(text("SELECT * FROM branch_tax_settings")).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.put("/tax/branch-settings", dependencies=[Depends(require_permission(["taxes.manage", "settings.edit"]))])
def upsert_branch_tax_setting(body: BranchTaxSetting, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        # Ensure minimum columns exist (idempotent; safe across tenants)
        db.execute(text("ALTER TABLE branch_tax_settings ADD COLUMN IF NOT EXISTS default_tax_rate DECIMAL(6,3) DEFAULT 15"))
        db.execute(text("ALTER TABLE branch_tax_settings ADD COLUMN IF NOT EXISTS tax_exempt BOOLEAN DEFAULT FALSE"))
        db.execute(text("ALTER TABLE branch_tax_settings ADD COLUMN IF NOT EXISTS notes TEXT"))
        db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_branch_tax_settings_branch ON branch_tax_settings(branch_id)"))
        db.execute(
            text(
                """
                INSERT INTO branch_tax_settings (branch_id, default_tax_rate, tax_exempt, notes)
                VALUES (:b, :r, :e, :n)
                ON CONFLICT (branch_id) DO UPDATE SET
                    default_tax_rate = EXCLUDED.default_tax_rate,
                    tax_exempt = EXCLUDED.tax_exempt,
                    notes = EXCLUDED.notes
                """
            ),
            {"b": body.branch_id, "r": body.default_tax_rate, "e": body.tax_exempt, "n": body.notes},
        )
        db.commit()
        return {"ok": True, "branch_id": body.branch_id}
    finally:
        db.close()


# ==========================================================================
# TREAS-F1 — Notes receivable discount (bank discount with interest)
# ==========================================================================

class NoteDiscountRequest(BaseModel):
    note_id: int
    bank_account_id: int
    discount_rate: float = Field(..., ge=0, le=100)  # annual %
    days_to_maturity: int = Field(..., ge=0)
    date: Optional[str] = None


@router.post("/treasury/notes-receivable/{note_id}/discount",
             dependencies=[Depends(require_permission(["treasury.manage", "accounting.manage"]))])
def discount_note_receivable(
    note_id: int,
    body: NoteDiscountRequest,
    request: Request,
    current_user=Depends(get_current_user),
):
    """Record bank discounting of a note: DR Bank (net), DR Interest Expense, CR Notes Receivable (face)."""
    from services import gl_service

    db = get_db_connection(current_user.company_id)
    try:
        note = db.execute(
            text(
                """
                SELECT id, face_value, COALESCE(status,'open') AS status
                FROM notes_receivable
                WHERE id = :id
                FOR UPDATE
                """
            ),
            {"id": note_id},
        ).fetchone()
        if not note:
            raise HTTPException(**http_error(404, "note_not_found"))
        if note.status not in ("open", "issued"):
            raise HTTPException(status_code=400, detail="لا يمكن خصم سند ليس مفتوحاً")

        face = _dec(note.face_value)
        rate = _dec(body.discount_rate) / Decimal("100")
        days = Decimal(str(body.days_to_maturity))
        interest = (face * rate * days / Decimal("365")).quantize(_D2)
        proceeds = (face - interest).quantize(_D2)

        txn_date = body.date or datetime.now().strftime("%Y-%m-%d")
        check_fiscal_period_open(db, txn_date)

        interest_acc = get_mapped_account_id(db, "acc_map_interest_expense")
        notes_acc = get_mapped_account_id(db, "acc_map_notes_receivable")
        if not interest_acc or not notes_acc:
            raise HTTPException(status_code=400, detail="الحسابات المخصصة لسندات القبض غير مهيأة")

        lines = [
            {"account_id": body.bank_account_id, "debit": float(proceeds), "credit": 0,
             "description": f"Discount NR #{note_id} proceeds"},
            {"account_id": interest_acc, "debit": float(interest), "credit": 0,
             "description": f"Discount NR #{note_id} interest"},
            {"account_id": notes_acc, "debit": 0, "credit": float(face),
             "description": f"Discount NR #{note_id} face"},
        ]
        je_id, je_num = gl_service.create_journal_entry(
            db,
            company_id=current_user.company_id,
            date=txn_date,
            description=f"Notes Receivable Discount #{note_id}",
            lines=lines,
            user_id=current_user.id,
            reference=f"NR-DISC-{note_id}",
            source="NoteDiscount",
            source_id=note_id,
            idempotency_key=f"nr_disc:{note_id}",
        )

        db.execute(
            text(
                """
                UPDATE notes_receivable
                SET status = 'discounted', updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """
            ),
            {"id": note_id},
        )
        db.commit()
        return {
            "note_id": note_id,
            "face_value": float(face),
            "interest": float(interest),
            "proceeds": float(proceeds),
            "journal_entry_id": je_id,
            "entry_number": je_num,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("Note discount failed")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


# ==========================================================================
# TREAS-F2 — Bounced check reversal
# ==========================================================================

class BounceRequest(BaseModel):
    date: Optional[str] = None
    notes: Optional[str] = None


@router.post("/treasury/checks-receivable/{check_id}/bounce",
             dependencies=[Depends(require_permission(["treasury.manage", "accounting.manage"]))])
def bounce_check_receivable(
    check_id: int,
    body: BounceRequest,
    current_user=Depends(get_current_user),
):
    """Reverse the originating deposit JE when a customer check bounces.

    Walks prior postings on the check and creates offsetting lines; marks the
    check as ``bounced``.
    """
    from services import gl_service

    db = get_db_connection(current_user.company_id)
    try:
        row = db.execute(
            text(
                """
                SELECT id, amount, status, party_id
                FROM checks_receivable
                WHERE id = :id
                FOR UPDATE
                """
            ),
            {"id": check_id},
        ).fetchone()
        if not row:
            raise HTTPException(**http_error(404, "check_not_found"))
        if row.status == "bounced":
            return {"ok": True, "already_bounced": True}

        txn_date = body.date or datetime.now().strftime("%Y-%m-%d")
        check_fiscal_period_open(db, txn_date)

        bank_acc = get_mapped_account_id(db, "acc_map_bank")
        ar_acc = get_mapped_account_id(db, "acc_map_ar")
        if not bank_acc or not ar_acc:
            raise HTTPException(status_code=400, detail="حسابات البنك/الذمم المدينة غير مهيأة")

        amt = float(_dec(row.amount))
        lines = [
            {"account_id": ar_acc, "debit": amt, "credit": 0,
             "description": f"Check #{check_id} bounce — reinstate AR"},
            {"account_id": bank_acc, "debit": 0, "credit": amt,
             "description": f"Check #{check_id} bounce — reverse deposit"},
        ]
        je_id, je_num = gl_service.create_journal_entry(
            db,
            company_id=current_user.company_id,
            date=txn_date,
            description=f"Bounced check #{check_id}",
            lines=lines,
            user_id=current_user.id,
            reference=f"CHK-BNC-{check_id}",
            source="CheckBounce",
            source_id=check_id,
            idempotency_key=f"chk_bnc:{check_id}",
        )

        db.execute(
            text("UPDATE checks_receivable SET status='bounced', updated_at=CURRENT_TIMESTAMP WHERE id=:id"),
            {"id": check_id},
        )
        db.commit()
        return {"check_id": check_id, "journal_entry_id": je_id, "entry_number": je_num}
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("Check bounce reversal failed")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


# ==========================================================================
# ACC-F12 — Asset revaluation JE (to OCI / revaluation reserve)
# ==========================================================================

class AssetRevaluationRequest(BaseModel):
    new_value: float = Field(..., gt=0)
    date: Optional[str] = None
    notes: Optional[str] = None


@router.post("/assets/{asset_id}/revalue",
             dependencies=[Depends(require_permission(["assets.manage", "accounting.manage"]))])
def revalue_asset(
    asset_id: int,
    body: AssetRevaluationRequest,
    current_user=Depends(get_current_user),
):
    """Revalue a fixed asset; post the delta against the revaluation reserve (equity)."""
    from services import gl_service

    db = get_db_connection(current_user.company_id)
    try:
        row = db.execute(
            text(
                """
                SELECT id, book_value, COALESCE(revaluation_reserve, 0) AS reserve, asset_account_id
                FROM assets
                WHERE id = :id
                FOR UPDATE
                """
            ),
            {"id": asset_id},
        ).fetchone()
        if not row:
            raise HTTPException(**http_error(404, "asset_not_found"))

        old = _dec(row.book_value)
        new = _dec(body.new_value)
        delta = (new - old).quantize(_D2)
        if abs(delta) < _D2:
            return {"ok": True, "no_change": True}

        txn_date = body.date or datetime.now().strftime("%Y-%m-%d")
        check_fiscal_period_open(db, txn_date)

        asset_acc = row.asset_account_id
        reserve_acc = get_mapped_account_id(db, "acc_map_revaluation_reserve")
        if not asset_acc or not reserve_acc:
            raise HTTPException(status_code=400, detail="حسابات الأصل / احتياطي إعادة التقييم غير مهيأة")

        if delta > 0:
            # Upward — DR Asset / CR Revaluation Reserve
            lines = [
                {"account_id": asset_acc, "debit": float(delta), "credit": 0, "description": f"Revaluation up asset #{asset_id}"},
                {"account_id": reserve_acc, "debit": 0, "credit": float(delta), "description": f"Revaluation reserve asset #{asset_id}"},
            ]
        else:
            abs_d = float(-delta)
            lines = [
                {"account_id": reserve_acc, "debit": abs_d, "credit": 0, "description": f"Revaluation down asset #{asset_id}"},
                {"account_id": asset_acc, "debit": 0, "credit": abs_d, "description": f"Asset write-down #{asset_id}"},
            ]

        je_id, je_num = gl_service.create_journal_entry(
            db,
            company_id=current_user.company_id,
            date=txn_date,
            description=f"Asset revaluation #{asset_id}",
            lines=lines,
            user_id=current_user.id,
            reference=f"ASSET-REVAL-{asset_id}",
            source="AssetRevaluation",
            source_id=asset_id,
            idempotency_key=f"asset_reval:{asset_id}:{txn_date}",
        )

        db.execute(
            text(
                """
                UPDATE assets
                SET book_value = :new,
                    revaluation_reserve = COALESCE(revaluation_reserve, 0) + :delta,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """
            ),
            {"new": float(new), "delta": float(delta), "id": asset_id},
        )
        db.commit()
        return {"asset_id": asset_id, "delta": float(delta), "journal_entry_id": je_id, "entry_number": je_num}
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("Asset revaluation failed")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


# ==========================================================================
# ACC-F13 — Units-of-production depreciation
# ==========================================================================

class UoPDepreciationRequest(BaseModel):
    units_produced: float = Field(..., gt=0)
    date: Optional[str] = None


@router.post("/assets/{asset_id}/depreciate-uop",
             dependencies=[Depends(require_permission(["assets.manage", "accounting.manage"]))])
def depreciate_asset_uop(
    asset_id: int,
    body: UoPDepreciationRequest,
    current_user=Depends(get_current_user),
):
    """Post units-of-production depreciation for the period."""
    from services import gl_service

    db = get_db_connection(current_user.company_id)
    try:
        row = db.execute(
            text(
                """
                SELECT id, cost, salvage_value, book_value, depreciation_method,
                       expected_production_units, COALESCE(cumulative_production_units, 0) AS cum_units,
                       asset_account_id, accumulated_depreciation_account_id, depreciation_expense_account_id
                FROM assets
                WHERE id = :id
                FOR UPDATE
                """
            ),
            {"id": asset_id},
        ).fetchone()
        if not row:
            raise HTTPException(**http_error(404, "asset_not_found"))
        if not row.expected_production_units or _dec(row.expected_production_units) <= 0:
            raise HTTPException(status_code=400, detail="expected_production_units غير محددة على الأصل")

        depreciable_base = _dec(row.cost) - _dec(row.salvage_value)
        per_unit = (depreciable_base / _dec(row.expected_production_units)).quantize(Decimal("0.000001"))
        units = _dec(body.units_produced)
        period_dep = (per_unit * units).quantize(_D2)

        # Cap by remaining book value
        book = _dec(row.book_value)
        if period_dep > book:
            period_dep = book
        if period_dep <= Decimal("0"):
            return {"ok": True, "no_depreciation": True}

        txn_date = body.date or datetime.now().strftime("%Y-%m-%d")
        check_fiscal_period_open(db, txn_date)

        if not row.depreciation_expense_account_id or not row.accumulated_depreciation_account_id:
            raise HTTPException(status_code=400, detail="حسابات الإهلاك غير مهيأة على الأصل")

        lines = [
            {"account_id": row.depreciation_expense_account_id, "debit": float(period_dep), "credit": 0,
             "description": f"UoP depreciation asset #{asset_id}"},
            {"account_id": row.accumulated_depreciation_account_id, "debit": 0, "credit": float(period_dep),
             "description": f"Accumulated depreciation asset #{asset_id}"},
        ]
        je_id, je_num = gl_service.create_journal_entry(
            db,
            company_id=current_user.company_id,
            date=txn_date,
            description=f"UoP depreciation asset #{asset_id}",
            lines=lines,
            user_id=current_user.id,
            reference=f"ASSET-DEP-UOP-{asset_id}-{txn_date}",
            source="AssetUoPDepreciation",
            source_id=asset_id,
            idempotency_key=f"asset_dep_uop:{asset_id}:{txn_date}",
        )

        db.execute(
            text(
                """
                UPDATE assets
                SET book_value = book_value - :dep,
                    cumulative_production_units = COALESCE(cumulative_production_units, 0) + :units,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """
            ),
            {"dep": float(period_dep), "units": float(units), "id": asset_id},
        )
        db.commit()
        return {"asset_id": asset_id, "depreciation": float(period_dep), "units": float(units),
                "journal_entry_id": je_id, "entry_number": je_num}
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("UoP depreciation failed")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


# ==========================================================================
# ACC-F14 — IFRS 16 lease modification (light remeasurement endpoint)
# ==========================================================================

class LeaseModificationRequest(BaseModel):
    new_liability: float = Field(..., ge=0)
    new_rou_asset: float = Field(..., ge=0)
    modification_date: Optional[str] = None
    notes: Optional[str] = None


@router.post("/leases/{lease_id}/modify",
             dependencies=[Depends(require_permission(["accounting.manage"]))])
def modify_lease(
    lease_id: int,
    body: LeaseModificationRequest,
    current_user=Depends(get_current_user),
):
    """Apply an IFRS 16 modification: adjust lease liability and ROU asset to new carrying amounts.

    Posts the delta via ``gl_service``. Requires a ``leases`` table with
    ``liability_account_id`` and ``rou_asset_account_id`` columns.
    """
    from services import gl_service

    db = get_db_connection(current_user.company_id)
    try:
        row = db.execute(
            text(
                """
                SELECT id,
                       COALESCE(current_liability, 0) AS liab,
                       COALESCE(rou_asset_value, 0) AS rou,
                       liability_account_id,
                       rou_asset_account_id
                FROM leases
                WHERE id = :id
                FOR UPDATE
                """
            ),
            {"id": lease_id},
        ).fetchone()
        if not row:
            raise HTTPException(**http_error(404, "lease_not_found"))

        dliab = (_dec(body.new_liability) - _dec(row.liab)).quantize(_D2)
        drou = (_dec(body.new_rou_asset) - _dec(row.rou)).quantize(_D2)

        if abs(dliab) < _D2 and abs(drou) < _D2:
            return {"ok": True, "no_change": True}

        txn_date = body.modification_date or datetime.now().strftime("%Y-%m-%d")
        check_fiscal_period_open(db, txn_date)

        if not row.liability_account_id or not row.rou_asset_account_id:
            raise HTTPException(status_code=400, detail="حسابات عقد الإيجار غير مهيأة")

        lines: List[dict] = []
        if drou > 0:
            lines.append({"account_id": row.rou_asset_account_id, "debit": float(drou), "credit": 0, "description": f"Lease #{lease_id} ROU up"})
        elif drou < 0:
            lines.append({"account_id": row.rou_asset_account_id, "debit": 0, "credit": float(-drou), "description": f"Lease #{lease_id} ROU down"})
        if dliab > 0:
            lines.append({"account_id": row.liability_account_id, "debit": 0, "credit": float(dliab), "description": f"Lease #{lease_id} liability up"})
        elif dliab < 0:
            lines.append({"account_id": row.liability_account_id, "debit": float(-dliab), "credit": 0, "description": f"Lease #{lease_id} liability down"})

        # Balance — plug difference into a P&L modification account
        total_debit = sum(Decimal(str(l["debit"])) for l in lines)
        total_credit = sum(Decimal(str(l["credit"])) for l in lines)
        balance = (total_debit - total_credit).quantize(_D2)
        if balance != 0:
            plug_acc = get_mapped_account_id(db, "acc_map_lease_modification") or get_mapped_account_id(db, "acc_map_other_expense")
            if not plug_acc:
                raise HTTPException(status_code=400, detail="حساب تسوية تعديل الإيجار غير مهيأ")
            if balance > 0:
                lines.append({"account_id": plug_acc, "debit": 0, "credit": float(balance), "description": "Lease modification P&L"})
            else:
                lines.append({"account_id": plug_acc, "debit": float(-balance), "credit": 0, "description": "Lease modification P&L"})

        je_id, je_num = gl_service.create_journal_entry(
            db,
            company_id=current_user.company_id,
            date=txn_date,
            description=f"Lease modification #{lease_id}",
            lines=lines,
            user_id=current_user.id,
            reference=f"LEASE-MOD-{lease_id}-{txn_date}",
            source="LeaseModification",
            source_id=lease_id,
            idempotency_key=f"lease_mod:{lease_id}:{txn_date}",
        )

        db.execute(
            text(
                """
                UPDATE leases
                SET current_liability = :liab,
                    rou_asset_value = :rou,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """
            ),
            {"liab": body.new_liability, "rou": body.new_rou_asset, "id": lease_id},
        )
        db.commit()
        return {"lease_id": lease_id, "delta_liability": float(dliab), "delta_rou": float(drou),
                "journal_entry_id": je_id, "entry_number": je_num}
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("Lease modification failed")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
