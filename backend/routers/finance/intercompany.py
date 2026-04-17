"""
AMAN ERP - Intercompany Transactions & Revenue Recognition (DEPRECATED)
المعاملات بين الشركات والاعتراف بالإيرادات (IFRS 15)

WARNING: This module (v1) uses single-sided journal entries.
Use intercompany_v2.py which creates reciprocal (dual-sided) JEs.
This module will be removed in a future release.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from utils.i18n import http_error
from sqlalchemy import text
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from decimal import Decimal, ROUND_HALF_UP
import logging
import json
import uuid

from database import get_db_connection
from routers.auth import get_current_user
from utils.permissions import require_permission
from services.gl_service import create_journal_entry as gl_create_journal_entry

router = APIRouter(prefix="/accounting/intercompany-v1", tags=["المعاملات بين الشركات (v1)"])
logger = logging.getLogger(__name__)

_D2 = Decimal('0.01')


def _dec(v) -> Decimal:
    return Decimal(str(v)) if v is not None else Decimal('0')


def _normalize_company_uuid(company_identifier: str) -> str:
    """Convert company code/ID to a valid UUID string for intercompany tables."""
    raw = str(company_identifier or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="رمز الشركة غير صالح")
    try:
        return str(uuid.UUID(raw))
    except ValueError:
        # Support legacy/non-UUID company codes by mapping deterministically.
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, raw.lower()))


# ======================== Schemas ========================

class IntercompanyTransactionCreate(BaseModel):
    target_company_id: str
    transaction_type: str = "sale"
    description: str
    amount: float
    currency: str = "SAR"
    reference: Optional[str] = None

class RevenueScheduleCreate(BaseModel):
    invoice_id: Optional[int] = None
    contract_id: Optional[int] = None
    total_amount: float
    start_date: str
    end_date: str
    method: str = "straight_line"


# ======================== Intercompany Transactions ========================

@router.get("/transactions", dependencies=[Depends(require_permission("accounting.view"))])
def list_intercompany_transactions(
    status_filter: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    """قائمة المعاملات بين الشركات"""
    db = get_db_connection(current_user.company_id)
    try:
        conditions = ["1=1"]
        params = {}
        if status_filter:
            conditions.append("status = :status")
            params["status"] = status_filter

        rows = db.execute(text(f"""
            SELECT it.*, u.full_name as created_by_name
            FROM intercompany_transactions it
            LEFT JOIN company_users u ON it.created_by = u.id
            WHERE {' AND '.join(conditions)}
            ORDER BY it.created_at DESC
        """), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.post("/transactions", status_code=201,
             dependencies=[Depends(require_permission("accounting.edit"))])
def create_intercompany_transaction(
    data: IntercompanyTransactionCreate,
    current_user=Depends(get_current_user)
):
    """إنشاء معاملة بين الشركات"""
    db = get_db_connection(current_user.company_id)
    try:
        ref = data.reference or f"IC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        source_company_uuid = _normalize_company_uuid(str(current_user.company_id))
        target_company_uuid = _normalize_company_uuid(data.target_company_id)

        tid = db.execute(text("""
            INSERT INTO intercompany_transactions (
                source_company_id, target_company_id, transaction_type,
                reference, description, amount, currency, status, created_by
            ) VALUES (
                :source, :target, :type,
                :ref, :desc, :amount, :curr, 'pending', :uid
            ) RETURNING id
        """), {
            "source": source_company_uuid,
            "target": target_company_uuid,
            "type": data.transaction_type,
            "ref": ref, "desc": data.description,
            "amount": data.amount, "curr": data.currency,
            "uid": current_user.id
        }).scalar()
        db.commit()
        return {"id": tid, "reference": ref, "message": "تم إنشاء المعاملة بين الشركات"}
    except Exception as e:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@router.post("/transactions/{txn_id}/process",
             dependencies=[Depends(require_permission("accounting.edit"))])
def process_intercompany_transaction(txn_id: int, current_user=Depends(get_current_user)):
    """معالجة المعاملة — إنشاء قيود محاسبية"""
    db = get_db_connection(current_user.company_id)
    try:
        txn = db.execute(text(
            "SELECT * FROM intercompany_transactions WHERE id = :id AND status = 'pending'"
        ), {"id": txn_id}).fetchone()
        if not txn:
            raise HTTPException(404, "المعاملة غير موجودة أو تمت معالجتها")
        txn = dict(txn._mapping)

        # Find intercompany accounts
        ic_receivable = db.execute(text(
            "SELECT id FROM accounts WHERE account_code LIKE '13%' LIMIT 1"
        )).scalar()
        ic_revenue = db.execute(text(
            "SELECT id FROM accounts WHERE account_type = 'revenue' LIMIT 1"
        )).scalar()

        if not ic_receivable or not ic_revenue:
            raise HTTPException(400, "يجب إعداد حسابات المعاملات بين الشركات أولاً")

        txn_amount = _dec(txn["amount"]).quantize(_D2, ROUND_HALF_UP)
        je_lines = [
            {
                "account_id": ic_receivable,
                "debit": txn_amount,
                "credit": 0,
                "description": txn["description"],
            },
            {
                "account_id": ic_revenue,
                "debit": 0,
                "credit": txn_amount,
                "description": txn["description"],
            },
        ]

        je_id, _ = gl_create_journal_entry(
            db=db,
            company_id=current_user.company_id,
            date=datetime.now().date().isoformat(),
            description=f"معاملة بين الشركات: {txn['description']}",
            lines=je_lines,
            user_id=current_user.id,
            reference=txn["reference"],
            source="intercompany_transaction",
            source_id=txn_id,
        )

        db.execute(text("""
            UPDATE intercompany_transactions
            SET status = 'processed', source_journal_id = :je, processed_at = NOW()
            WHERE id = :id
        """), {"je": je_id, "id": txn_id})
        db.commit()

        return {"message": "تمت معالجة المعاملة بنجاح", "source_journal_id": je_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@router.get("/elimination-report", dependencies=[Depends(require_permission("accounting.view"))])
def intercompany_elimination_report(current_user=Depends(get_current_user)):
    """تقرير استبعاد المعاملات بين الشركات للتجميع"""
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(text("""
            SELECT target_company_id, transaction_type,
                   COUNT(*) as txn_count,
                   SUM(amount) as total_amount,
                   SUM(amount) FILTER (WHERE status = 'processed') as processed_amount,
                   SUM(amount) FILTER (WHERE status = 'pending') as pending_amount
            FROM intercompany_transactions
            GROUP BY target_company_id, transaction_type
            ORDER BY total_amount DESC
        """)).fetchall()

        total = db.execute(text("""
            SELECT COALESCE(SUM(amount), 0) as total_intercompany,
                   COALESCE(SUM(amount) FILTER (WHERE status = 'processed'), 0) as total_eliminated,
                   COALESCE(SUM(amount) FILTER (WHERE status = 'pending'), 0) as pending_elimination
            FROM intercompany_transactions
        """)).fetchone()

        return {
            "by_company": [dict(r._mapping) for r in rows],
            "totals": dict(total._mapping) if total else {}
        }
    finally:
        db.close()


# ======================== Revenue Recognition (IFRS 15) ========================

rev_router = APIRouter(prefix="/accounting/revenue-recognition", tags=["الاعتراف بالإيرادات"])


@rev_router.get("/schedules", dependencies=[Depends(require_permission("accounting.view"))])
def list_revenue_schedules(status_filter: Optional[str] = None, current_user=Depends(get_current_user)):
    """قائمة جداول الاعتراف بالإيرادات"""
    db = get_db_connection(current_user.company_id)
    try:
        conditions = ["1=1"]
        params = {}
        if status_filter:
            conditions.append("status = :status")
            params["status"] = status_filter

        rows = db.execute(text(f"""
            SELECT rs.*,
                   ROUND(100.0 * recognized_amount / NULLIF(total_amount, 0), 1) as pct_recognized
            FROM revenue_recognition_schedules rs
            WHERE {' AND '.join(conditions)}
            ORDER BY rs.start_date DESC
        """), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@rev_router.post("/schedules", status_code=201,
                 dependencies=[Depends(require_permission("accounting.edit"))])
def create_revenue_schedule(data: RevenueScheduleCreate, current_user=Depends(get_current_user)):
    """إنشاء جدول اعتراف بالإيرادات — IFRS 15"""
    db = get_db_connection(current_user.company_id)
    try:
        start = datetime.strptime(data.start_date, "%Y-%m-%d").date()
        end = datetime.strptime(data.end_date, "%Y-%m-%d").date()
        if end <= start:
            raise HTTPException(400, "تاريخ النهاية يجب أن يكون بعد تاريخ البداية")

        lines = []

        if data.method == "straight_line":
            from dateutil.relativedelta import relativedelta
            current = start
            periods = 0
            temp = start
            while temp < end:
                temp += relativedelta(months=1)
                periods += 1
            if periods == 0:
                periods = 1
            total_amount = _dec(data.total_amount)
            monthly_amount = (total_amount / _dec(periods)).quantize(_D2, ROUND_HALF_UP)
            for i in range(periods):
                period_start = start + relativedelta(months=i)
                period_end = min(start + relativedelta(months=i + 1) - relativedelta(days=1), end)
                amt = monthly_amount if i < periods - 1 else (total_amount - (monthly_amount * _dec(periods - 1))).quantize(_D2, ROUND_HALF_UP)
                lines.append({
                    "period": period_start.strftime("%Y-%m"),
                    "start_date": period_start.isoformat(),
                    "end_date": period_end.isoformat(),
                    "amount": float(amt), "recognized": False
                })
        elif data.method == "percentage_completion":
            total_amount = _dec(data.total_amount)
            for i in range(4):
                lines.append({
                    "milestone": f"مرحلة {i + 1}",
                    "percentage": (i + 1) * 25,
                    "amount": float((total_amount * Decimal('0.25')).quantize(_D2, ROUND_HALF_UP)),
                    "recognized": False
                })
        else:
            lines.append({
                "milestone": "إنجاز كامل",
                "percentage": 100,
                "amount": float(_dec(data.total_amount).quantize(_D2, ROUND_HALF_UP)),
                "recognized": False
            })

        sid = db.execute(text("""
            INSERT INTO revenue_recognition_schedules (
                invoice_id, contract_id, total_amount, recognized_amount, deferred_amount,
                start_date, end_date, method, status, schedule_lines, created_by
            ) VALUES (:inv, :cont, :total, 0, :total, :start, :end, :method, 'active', :lines, :uid)
            RETURNING id
        """), {
            "inv": data.invoice_id, "cont": data.contract_id,
            "total": data.total_amount, "start": data.start_date,
            "end": data.end_date, "method": data.method,
            "lines": json.dumps(lines), "uid": current_user.id
        }).scalar()
        db.commit()
        return {"id": sid, "periods": len(lines), "message": "تم إنشاء جدول الاعتراف بالإيرادات"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@rev_router.get("/schedules/{schedule_id}", dependencies=[Depends(require_permission("accounting.view"))])
def get_revenue_schedule(schedule_id: int, current_user=Depends(get_current_user)):
    """تفاصيل جدول الاعتراف"""
    db = get_db_connection(current_user.company_id)
    try:
        row = db.execute(text("SELECT * FROM revenue_recognition_schedules WHERE id = :id"), {"id": schedule_id}).fetchone()
        if not row:
            raise HTTPException(404, "الجدول غير موجود")
        result = dict(row._mapping)
        if isinstance(result.get("schedule_lines"), str):
            result["schedule_lines"] = json.loads(result["schedule_lines"])
        return result
    finally:
        db.close()


@rev_router.post("/schedules/{schedule_id}/recognize",
                  dependencies=[Depends(require_permission("accounting.edit"))])
def recognize_revenue_period(schedule_id: int, period_index: int = 0, current_user=Depends(get_current_user)):
    """الاعتراف بإيرادات فترة محددة وإنشاء قيد محاسبي"""
    db = get_db_connection(current_user.company_id)
    try:
        row = db.execute(text(
            "SELECT * FROM revenue_recognition_schedules WHERE id = :id AND status = 'active'"
        ), {"id": schedule_id}).fetchone()
        if not row:
            raise HTTPException(404, "الجدول غير موجود أو غير نشط")

        schedule = dict(row._mapping)
        lines = schedule.get("schedule_lines", [])
        if isinstance(lines, str):
            lines = json.loads(lines)

        if period_index >= len(lines):
            raise HTTPException(400, "رقم الفترة غير صالح")
        period = lines[period_index]
        if period.get("recognized"):
            raise HTTPException(400, "تم الاعتراف بهذه الفترة مسبقاً")

        amount = _dec(period["amount"]).quantize(_D2, ROUND_HALF_UP)

        # Create journal entry: Deferred Revenue (Dr) → Revenue (Cr)
        deferred_acc = db.execute(text("SELECT id FROM accounts WHERE account_code LIKE '22%' LIMIT 1")).scalar()
        revenue_acc = db.execute(text("SELECT id FROM accounts WHERE account_type = 'revenue' LIMIT 1")).scalar()

        if deferred_acc and revenue_acc:
            gl_create_journal_entry(
                db=db,
                company_id=current_user.company_id,
                date=datetime.now().date().isoformat(),
                description=f"اعتراف بإيرادات - جدول #{schedule_id}",
                lines=[
                    {
                        "account_id": deferred_acc,
                        "debit": amount,
                        "credit": 0,
                        "description": "اعتراف بإيرادات مؤجلة",
                    },
                    {
                        "account_id": revenue_acc,
                        "debit": 0,
                        "credit": amount,
                        "description": "إيرادات معترف بها",
                    },
                ],
                user_id=current_user.id,
                reference=f"RR-{schedule_id}-{period_index}",
                source="revenue_recognition",
                source_id=schedule_id,
            )

        # Update schedule
        lines[period_index]["recognized"] = True
        lines[period_index]["recognized_at"] = datetime.now().isoformat()
        existing_recognized = _dec(schedule.get("recognized_amount") or 0)
        total_amount = _dec(schedule.get("total_amount") or 0)
        new_recognized = existing_recognized + amount
        new_deferred = total_amount - new_recognized
        new_status = "completed" if new_deferred <= 0 else "active"

        db.execute(text("""
            UPDATE revenue_recognition_schedules
            SET recognized_amount = :rec, deferred_amount = :def,
                schedule_lines = :lines, status = :status
            WHERE id = :id
        """), {
            "rec": new_recognized.quantize(_D2, ROUND_HALF_UP), "def": max(new_deferred, Decimal('0')).quantize(_D2, ROUND_HALF_UP),
            "lines": json.dumps(lines), "status": new_status, "id": schedule_id
        })
        db.commit()
        return {
            "message": f"تم الاعتراف بمبلغ {float(amount):.2f}",
            "recognized_total": float(new_recognized.quantize(_D2, ROUND_HALF_UP)),
            "remaining": float(max(new_deferred, Decimal('0')).quantize(_D2, ROUND_HALF_UP)), "status": new_status
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@rev_router.get("/summary", dependencies=[Depends(require_permission("accounting.view"))])
def revenue_recognition_summary(current_user=Depends(get_current_user)):
    """ملخص الاعتراف بالإيرادات"""
    db = get_db_connection(current_user.company_id)
    try:
        summary = db.execute(text("""
            SELECT COUNT(*) as total_schedules,
                   COUNT(*) FILTER (WHERE status = 'active') as active_schedules,
                   COUNT(*) FILTER (WHERE status = 'completed') as completed_schedules,
                   COALESCE(SUM(total_amount), 0) as total_contract_value,
                   COALESCE(SUM(recognized_amount), 0) as total_recognized,
                   COALESCE(SUM(deferred_amount), 0) as total_deferred,
                   CASE WHEN SUM(total_amount) > 0
                        THEN ROUND(100.0 * SUM(recognized_amount) / SUM(total_amount), 1)
                        ELSE 0 END as recognition_pct
            FROM revenue_recognition_schedules
        """)).fetchone()
        return dict(summary._mapping) if summary else {}
    finally:
        db.close()
