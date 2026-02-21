"""
وحدة الضرائب — AMAN ERP
إدارة أنواع الضرائب، الإقرارات الضريبية، المدفوعات، التسويات، وتقارير VAT
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field
from database import get_db_connection
from routers.auth import get_current_user
from utils.permissions import require_permission, validate_branch_access
from utils.audit import log_activity
from utils.accounting import (
    generate_sequential_number,
    get_mapped_account_id,
    update_account_balance,
    get_base_currency
)
import logging

router = APIRouter(prefix="/taxes", tags=["الضرائب"])
logger = logging.getLogger(__name__)
from schemas.taxes import TaxRateCreate, TaxRateUpdate, TaxGroupCreate, TaxReturnCreate, TaxPaymentCreate

# ==================== TAX RATES CRUD ====================

@router.get("/rates", dependencies=[Depends(require_permission(["accounting.view", "taxes.view"]))])
def list_tax_rates(
    is_active: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    """جلب جميع أنواع الضرائب"""
    db = get_db_connection(current_user.company_id)
    try:
        where = "WHERE 1=1"
        params = {}
        if is_active is not None:
            where += " AND is_active = :active"
            params["active"] = is_active

        rows = db.execute(text(f"""
            SELECT id, tax_code, tax_name, tax_name_en, rate_type, rate_value,
                   description, effective_from, effective_to, is_active, created_at
            FROM tax_rates {where}
            ORDER BY created_at DESC
        """), params).fetchall()

        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.get("/rates/{rate_id}", dependencies=[Depends(require_permission(["accounting.view", "taxes.view"]))])
def get_tax_rate(rate_id: int, current_user: dict = Depends(get_current_user)):
    """جلب تفاصيل نوع ضريبة"""
    db = get_db_connection(current_user.company_id)
    try:
        row = db.execute(text("SELECT * FROM tax_rates WHERE id = :id"), {"id": rate_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="نوع الضريبة غير موجود")
        return dict(row._mapping)
    finally:
        db.close()


@router.post("/rates", status_code=201, dependencies=[Depends(require_permission(["accounting.edit", "taxes.manage"]))])
def create_tax_rate(
    request: Request,
    data: TaxRateCreate,
    current_user: dict = Depends(get_current_user)
):
    """إنشاء نوع ضريبة جديد"""
    db = get_db_connection(current_user.company_id)
    try:
        exists = db.execute(text("SELECT 1 FROM tax_rates WHERE tax_code = :code"), {"code": data.tax_code}).fetchone()
        if exists:
            raise HTTPException(status_code=400, detail="كود الضريبة موجود مسبقاً")

        result = db.execute(text("""
            INSERT INTO tax_rates (tax_code, tax_name, tax_name_en, rate_type, rate_value,
                                   description, effective_from, effective_to, is_active)
            VALUES (:code, :name, :name_en, :rate_type, :rate_value,
                    :desc, :eff_from, :eff_to, :active)
            RETURNING id
        """), {
            "code": data.tax_code, "name": data.tax_name, "name_en": data.tax_name_en,
            "rate_type": data.rate_type, "rate_value": data.rate_value,
            "desc": data.description, "eff_from": data.effective_from,
            "eff_to": data.effective_to, "active": data.is_active
        })
        new_id = result.fetchone()[0]
        db.commit()

        log_activity(db, user_id=current_user.id, username=current_user.username,
                     action="taxes.rate.create", resource_type="tax_rate",
                     resource_id=str(new_id), details={"tax_code": data.tax_code, "rate": data.rate_value},
                     request=request)

        return {"success": True, "id": new_id, "message": "تم إنشاء نوع الضريبة بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating tax rate: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.put("/rates/{rate_id}", dependencies=[Depends(require_permission(["accounting.edit", "taxes.manage"]))])
def update_tax_rate(
    rate_id: int, request: Request, data: TaxRateUpdate,
    current_user: dict = Depends(get_current_user)
):
    """تحديث نوع ضريبة"""
    db = get_db_connection(current_user.company_id)
    try:
        existing = db.execute(text("SELECT 1 FROM tax_rates WHERE id = :id"), {"id": rate_id}).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="نوع الضريبة غير موجود")

        updates = []
        params = {"id": rate_id}
        for field, val in data.dict(exclude_unset=True).items():
            updates.append(f"{field} = :{field}")
            params[field] = val

        if not updates:
            raise HTTPException(status_code=400, detail="لا توجد بيانات للتحديث")

        db.execute(text(f"UPDATE tax_rates SET {', '.join(updates)} WHERE id = :id"), params)
        db.commit()

        log_activity(db, user_id=current_user.id, username=current_user.username,
                     action="taxes.rate.update", resource_type="tax_rate",
                     resource_id=str(rate_id), details=params, request=request)

        return {"success": True, "message": "تم تحديث نوع الضريبة بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating tax rate: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.delete("/rates/{rate_id}", dependencies=[Depends(require_permission(["accounting.manage", "taxes.manage"]))])
def delete_tax_rate(rate_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    """حذف نوع ضريبة (إيقاف تفعيل فقط)"""
    db = get_db_connection(current_user.company_id)
    try:
        existing = db.execute(text("SELECT tax_code FROM tax_rates WHERE id = :id"), {"id": rate_id}).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="نوع الضريبة غير موجود")

        db.execute(text("UPDATE tax_rates SET is_active = FALSE WHERE id = :id"), {"id": rate_id})
        db.commit()

        log_activity(db, user_id=current_user.id, username=current_user.username,
                     action="taxes.rate.delete", resource_type="tax_rate",
                     resource_id=str(rate_id), details={"tax_code": existing.tax_code},
                     request=request)

        return {"success": True, "message": "تم إيقاف نوع الضريبة بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ==================== TAX GROUPS ====================

@router.get("/groups", dependencies=[Depends(require_permission(["accounting.view", "taxes.view"]))])
def list_tax_groups(current_user: dict = Depends(get_current_user)):
    """جلب مجموعات الضرائب"""
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(text("""
            SELECT id, group_code, group_name, group_name_en, description, tax_ids, is_active, created_at
            FROM tax_groups ORDER BY created_at DESC
        """)).fetchall()

        result = []
        for r in rows:
            item = dict(r._mapping)
            tax_ids = item.get("tax_ids") or []
            if tax_ids:
                placeholders = ",".join([str(tid) for tid in tax_ids if isinstance(tid, int)])
                if placeholders:
                    taxes = db.execute(text(f"SELECT id, tax_name, rate_value FROM tax_rates WHERE id IN ({placeholders})")).fetchall()
                    item["taxes"] = [dict(t._mapping) for t in taxes]
                    item["combined_rate"] = sum(float(t.rate_value) for t in taxes)
                else:
                    item["taxes"] = []
                    item["combined_rate"] = 0
            else:
                item["taxes"] = []
                item["combined_rate"] = 0
            result.append(item)

        return result
    finally:
        db.close()


@router.post("/groups", status_code=201, dependencies=[Depends(require_permission(["accounting.edit", "taxes.manage"]))])
def create_tax_group(request: Request, data: TaxGroupCreate, current_user: dict = Depends(get_current_user)):
    """إنشاء مجموعة ضريبية جديدة"""
    db = get_db_connection(current_user.company_id)
    try:
        exists = db.execute(text("SELECT 1 FROM tax_groups WHERE group_code = :code"), {"code": data.group_code}).fetchone()
        if exists:
            raise HTTPException(status_code=400, detail="كود المجموعة موجود مسبقاً")

        import json
        result = db.execute(text("""
            INSERT INTO tax_groups (group_code, group_name, group_name_en, description, tax_ids, is_active)
            VALUES (:code, :name, :name_en, :desc, CAST(:tax_ids AS jsonb), :active)
            RETURNING id
        """), {
            "code": data.group_code, "name": data.group_name, "name_en": data.group_name_en,
            "desc": data.description, "tax_ids": json.dumps(data.tax_ids), "active": data.is_active
        })
        new_id = result.fetchone()[0]
        db.commit()

        log_activity(db, user_id=current_user.id, username=current_user.username,
                     action="taxes.group.create", resource_type="tax_group",
                     resource_id=str(new_id), details={"group_code": data.group_code},
                     request=request)

        return {"success": True, "id": new_id, "message": "تم إنشاء المجموعة الضريبية بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ==================== TAX RETURNS (الإقرارات الضريبية) ====================

@router.get("/returns", dependencies=[Depends(require_permission(["accounting.view", "taxes.view"]))])
def list_tax_returns(
    status: Optional[str] = None,
    tax_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """جلب الإقرارات الضريبية"""
    db = get_db_connection(current_user.company_id)
    try:
        where = "WHERE 1=1"
        params = {}
        if status:
            where += " AND tr.status = :status"
            params["status"] = status
        if tax_type:
            where += " AND tr.tax_type = :tax_type"
            params["tax_type"] = tax_type

        rows = db.execute(text(f"""
            SELECT tr.*,
                   cu.username as created_by_name,
                   COALESCE((SELECT SUM(tp.amount) FROM tax_payments tp WHERE tp.tax_return_id = tr.id AND tp.status = 'confirmed'), 0) as paid_amount
            FROM tax_returns tr
            LEFT JOIN company_users cu ON tr.created_by = cu.id
            {where}
            ORDER BY tr.created_at DESC
        """), params).fetchall()

        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.get("/returns/{return_id}", dependencies=[Depends(require_permission(["accounting.view", "taxes.view"]))])
def get_tax_return(return_id: int, current_user: dict = Depends(get_current_user)):
    """جلب تفاصيل إقرار ضريبي"""
    db = get_db_connection(current_user.company_id)
    try:
        row = db.execute(text("""
            SELECT tr.*,
                   cu.username as created_by_name
            FROM tax_returns tr
            LEFT JOIN company_users cu ON tr.created_by = cu.id
            WHERE tr.id = :id
        """), {"id": return_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="الإقرار الضريبي غير موجود")

        result = dict(row._mapping)

        # Get payments
        payments = db.execute(text("""
            SELECT tp.*, cu.username as created_by_name
            FROM tax_payments tp
            LEFT JOIN company_users cu ON tp.created_by = cu.id
            WHERE tp.tax_return_id = :id
            ORDER BY tp.payment_date DESC
        """), {"id": return_id}).fetchall()
        result["payments"] = [dict(p._mapping) for p in payments]
        result["paid_amount"] = sum(float(p.amount) for p in payments if p.status == "confirmed")
        result["remaining_amount"] = float(result.get("total_amount", 0)) - result["paid_amount"]

        return result
    finally:
        db.close()


@router.post("/returns", status_code=201, dependencies=[Depends(require_permission(["accounting.edit", "taxes.manage"]))])
def create_tax_return(
    request: Request,
    data: TaxReturnCreate,
    current_user: dict = Depends(get_current_user)
):
    """إنشاء إقرار ضريبي جديد — يحسب المبالغ تلقائياً من الفواتير"""
    branch_id = validate_branch_access(current_user, data.branch_id)
    db = get_db_connection(current_user.company_id)
    try:
        period = data.tax_period
        if "-Q" in period:
            year, q = period.split("-Q")
            quarter = int(q)
            month_start = (quarter - 1) * 3 + 1
            month_end = quarter * 3
            start_date = f"{year}-{month_start:02d}-01"
            if month_end == 12:
                end_date = f"{year}-12-31"
            else:
                end_date = f"{year}-{month_end + 1:02d}-01"
        else:
            parts = period.split("-")
            year, month = int(parts[0]), int(parts[1])
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year + 1}-01-01"
            else:
                end_date = f"{year}-{month + 1:02d}-01"

        params = {"start": start_date, "end": end_date}
        branch_filter = ""
        if branch_id:
            branch_filter = "AND i.branch_id = :branch_id"
            params["branch_id"] = branch_id

        # Check for duplicate
        dup = db.execute(text(
            "SELECT 1 FROM tax_returns WHERE tax_period = :period AND tax_type = :type AND status != 'cancelled'"
        ), {"period": period, "type": data.tax_type}).fetchone()
        if dup:
            raise HTTPException(status_code=400, detail=f"يوجد إقرار ضريبي لنفس الفترة ({period}) بالفعل")

        # Output VAT (sales)
        output = db.execute(text(f"""
            SELECT
                COALESCE(SUM(il.quantity * il.unit_price * i.exchange_rate), 0) as taxable,
                COALESCE(SUM(il.quantity * il.unit_price * i.exchange_rate * (il.tax_rate / 100)), 0) as vat
            FROM invoice_lines il JOIN invoices i ON il.invoice_id = i.id
            WHERE i.invoice_type = 'sales' AND i.status NOT IN ('draft', 'cancelled')
            AND i.invoice_date >= :start AND i.invoice_date < :end {branch_filter}
        """), params).fetchone()

        # Sales returns
        output_returns = db.execute(text(f"""
            SELECT
                COALESCE(SUM(il.quantity * il.unit_price * i.exchange_rate), 0) as taxable,
                COALESCE(SUM(il.quantity * il.unit_price * i.exchange_rate * (il.tax_rate / 100)), 0) as vat
            FROM invoice_lines il JOIN invoices i ON il.invoice_id = i.id
            WHERE i.invoice_type = 'sales_return' AND i.status NOT IN ('draft', 'cancelled')
            AND i.invoice_date >= :start AND i.invoice_date < :end {branch_filter}
        """), params).fetchone()

        # Input VAT (purchases)
        input_vat = db.execute(text(f"""
            SELECT
                COALESCE(SUM(il.quantity * il.unit_price * i.exchange_rate), 0) as taxable,
                COALESCE(SUM(il.quantity * il.unit_price * i.exchange_rate * (il.tax_rate / 100)), 0) as vat
            FROM invoice_lines il JOIN invoices i ON il.invoice_id = i.id
            WHERE i.invoice_type = 'purchase' AND i.status NOT IN ('draft', 'cancelled')
            AND i.invoice_date >= :start AND i.invoice_date < :end {branch_filter}
        """), params).fetchone()

        # Purchase returns
        input_returns = db.execute(text(f"""
            SELECT
                COALESCE(SUM(il.quantity * il.unit_price * i.exchange_rate), 0) as taxable,
                COALESCE(SUM(il.quantity * il.unit_price * i.exchange_rate * (il.tax_rate / 100)), 0) as vat
            FROM invoice_lines il JOIN invoices i ON il.invoice_id = i.id
            WHERE i.invoice_type = 'purchase_return' AND i.status NOT IN ('draft', 'cancelled')
            AND i.invoice_date >= :start AND i.invoice_date < :end {branch_filter}
        """), params).fetchone()

        net_output_vat = float(output.vat or 0) - float(output_returns.vat or 0)
        net_input_vat = float(input_vat.vat or 0) - float(input_returns.vat or 0)
        taxable_amount = (float(output.taxable or 0) - float(output_returns.taxable or 0)) + \
                         (float(input_vat.taxable or 0) - float(input_returns.taxable or 0))
        tax_amount = net_output_vat - net_input_vat

        return_number = generate_sequential_number(db, "TR", "tax_returns", "return_number")

        result = db.execute(text("""
            INSERT INTO tax_returns (return_number, tax_period, tax_type, taxable_amount, tax_amount,
                                     penalty_amount, interest_amount, total_amount, due_date,
                                     status, notes, created_by)
            VALUES (:num, :period, :type, :taxable, :tax, 0, 0, :total, :due, 'draft', :notes, :user)
            RETURNING id
        """), {
            "num": return_number, "period": period, "type": data.tax_type,
            "taxable": taxable_amount, "tax": tax_amount, "total": tax_amount,
            "due": data.due_date, "notes": data.notes, "user": current_user.id
        })
        new_id = result.fetchone()[0]
        db.commit()

        log_activity(db, user_id=current_user.id, username=current_user.username,
                     action="taxes.return.create", resource_type="tax_return",
                     resource_id=str(new_id),
                     details={"period": period, "tax_amount": tax_amount, "return_number": return_number},
                     request=request)

        return {
            "success": True, "id": new_id, "return_number": return_number,
            "message": "تم إنشاء الإقرار الضريبي بنجاح",
            "summary": {
                "output_vat": net_output_vat, "input_vat": net_input_vat,
                "net_payable": tax_amount, "taxable_amount": taxable_amount
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating tax return: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.put("/returns/{return_id}/file", dependencies=[Depends(require_permission(["accounting.manage", "taxes.manage"]))])
def file_tax_return(
    return_id: int, request: Request,
    body: dict = None,
    current_user: dict = Depends(get_current_user)
):
    """تقديم الإقرار الضريبي (تغيير الحالة من draft إلى filed)"""
    db = get_db_connection(current_user.company_id)
    try:
        row = db.execute(text("SELECT * FROM tax_returns WHERE id = :id"), {"id": return_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="الإقرار الضريبي غير موجود")
        if row.status != "draft":
            raise HTTPException(status_code=400, detail="لا يمكن تقديم إقرار غير في حالة مسودة")

        penalty = float((body or {}).get("penalty_amount", 0))
        interest = float((body or {}).get("interest_amount", 0))
        total = float(row.tax_amount) + penalty + interest

        db.execute(text("""
            UPDATE tax_returns SET status = 'filed', filed_date = CURRENT_DATE,
                penalty_amount = :penalty, interest_amount = :interest, total_amount = :total
            WHERE id = :id
        """), {"id": return_id, "penalty": penalty, "interest": interest, "total": total})
        db.commit()

        log_activity(db, user_id=current_user.id, username=current_user.username,
                     action="taxes.return.file", resource_type="tax_return",
                     resource_id=str(return_id),
                     details={"return_number": row.return_number, "total": total},
                     request=request)

        return {"success": True, "message": "تم تقديم الإقرار الضريبي بنجاح", "total_amount": total}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.put("/returns/{return_id}/cancel", dependencies=[Depends(require_permission(["accounting.manage", "taxes.manage"]))])
def cancel_tax_return(return_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    """إلغاء إقرار ضريبي"""
    db = get_db_connection(current_user.company_id)
    try:
        row = db.execute(text("SELECT * FROM tax_returns WHERE id = :id"), {"id": return_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="الإقرار الضريبي غير موجود")
        if row.status == "paid":
            raise HTTPException(status_code=400, detail="لا يمكن إلغاء إقرار مدفوع")

        has_payments = db.execute(text(
            "SELECT 1 FROM tax_payments WHERE tax_return_id = :id AND status = 'confirmed'"
        ), {"id": return_id}).fetchone()
        if has_payments:
            raise HTTPException(status_code=400, detail="لا يمكن إلغاء إقرار له مدفوعات مؤكدة")

        db.execute(text("UPDATE tax_returns SET status = 'cancelled' WHERE id = :id"), {"id": return_id})
        db.commit()

        log_activity(db, user_id=current_user.id, username=current_user.username,
                     action="taxes.return.cancel", resource_type="tax_return",
                     resource_id=str(return_id), details={"return_number": row.return_number},
                     request=request)

        return {"success": True, "message": "تم إلغاء الإقرار الضريبي"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ==================== TAX PAYMENTS ====================

@router.get("/payments", dependencies=[Depends(require_permission(["accounting.view", "taxes.view"]))])
def list_tax_payments(
    tax_return_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """جلب مدفوعات الضرائب"""
    db = get_db_connection(current_user.company_id)
    try:
        where = "WHERE 1=1"
        params = {}
        if tax_return_id:
            where += " AND tp.tax_return_id = :return_id"
            params["return_id"] = tax_return_id
        if status:
            where += " AND tp.status = :status"
            params["status"] = status

        rows = db.execute(text(f"""
            SELECT tp.*, tr.return_number, tr.tax_period, tr.tax_type,
                   cu.username as created_by_name
            FROM tax_payments tp
            JOIN tax_returns tr ON tp.tax_return_id = tr.id
            LEFT JOIN company_users cu ON tp.created_by = cu.id
            {where}
            ORDER BY tp.payment_date DESC
        """), params).fetchall()

        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.post("/payments", status_code=201, dependencies=[Depends(require_permission(["accounting.edit", "taxes.manage"]))])
def create_tax_payment(
    request: Request,
    data: TaxPaymentCreate,
    current_user: dict = Depends(get_current_user)
):
    """تسجيل دفعة ضريبية مع قيد محاسبي تلقائي"""
    db = get_db_connection(current_user.company_id)
    try:
        tr = db.execute(text("SELECT * FROM tax_returns WHERE id = :id"), {"id": data.tax_return_id}).fetchone()
        if not tr:
            raise HTTPException(status_code=404, detail="الإقرار الضريبي غير موجود")
        if tr.status in ("cancelled", "draft"):
            raise HTTPException(status_code=400, detail="لا يمكن الدفع على إقرار ملغى أو مسودة. يجب تقديمه أولاً")

        paid = db.execute(text(
            "SELECT COALESCE(SUM(amount), 0) FROM tax_payments WHERE tax_return_id = :id AND status = 'confirmed'"
        ), {"id": data.tax_return_id}).scalar()
        remaining = float(tr.total_amount) - float(paid)
        if data.amount > remaining + 0.01:
            raise HTTPException(status_code=400, detail=f"المبلغ يتجاوز المتبقي ({remaining:.2f})")

        payment_number = generate_sequential_number(db, "TP", "tax_payments", "payment_number")

        result = db.execute(text("""
            INSERT INTO tax_payments (payment_number, tax_return_id, payment_date, amount,
                                      payment_method, reference, status, notes, created_by)
            VALUES (:num, :return_id, :date, :amount, :method, :ref, 'confirmed', :notes, :user)
            RETURNING id
        """), {
            "num": payment_number, "return_id": data.tax_return_id,
            "date": data.payment_date, "amount": data.amount,
            "method": data.payment_method, "ref": data.reference,
            "notes": data.notes, "user": current_user.id
        })
        new_id = result.fetchone()[0]

        # ===== ACCOUNTING INTEGRATION =====
        vat_account_id = get_mapped_account_id(db, "acc_map_vat_out")
        if not vat_account_id:
            vat_account_id = get_mapped_account_id(db, "acc_map_vat_in")

        bank_account_id = None
        if data.treasury_account_id:
            bank_row = db.execute(text(
                "SELECT gl_account_id FROM treasury_accounts WHERE id = :id"
            ), {"id": data.treasury_account_id}).fetchone()
            if bank_row:
                bank_account_id = bank_row.gl_account_id

        if not bank_account_id:
            bank_row = db.execute(text(
                "SELECT gl_account_id FROM treasury_accounts WHERE is_active = true AND gl_account_id IS NOT NULL LIMIT 1"
            )).fetchone()
            if bank_row:
                bank_account_id = bank_row.gl_account_id

        if vat_account_id and bank_account_id:
            base_currency = get_base_currency(db)
            entry_number = generate_sequential_number(db, "JE", "journal_entries", "entry_number")

            je_id = db.execute(text("""
                INSERT INTO journal_entries (entry_number, entry_date, description, reference,
                                             status, created_by, currency, exchange_rate)
                VALUES (:num, :date, :desc, :ref, 'posted', :user, :curr, 1)
                RETURNING id
            """), {
                "num": entry_number, "date": data.payment_date,
                "desc": f"دفع ضريبة — إقرار {tr.return_number} — فترة {tr.tax_period}",
                "ref": payment_number, "user": current_user.id, "curr": base_currency
            }).scalar()

            # Debit VAT Payable (reduce liability)
            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description, currency, amount_currency)
                VALUES (:jid, :aid, :amount, 0, :desc, :curr, :amount)
            """), {"jid": je_id, "aid": vat_account_id, "amount": data.amount,
                   "desc": f"دفع ضريبة — {tr.tax_period}", "curr": base_currency})
            update_account_balance(db, vat_account_id, debit_base=data.amount, credit_base=0)

            # Credit Bank
            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description, currency, amount_currency)
                VALUES (:jid, :aid, 0, :amount, :desc, :curr, :amount)
            """), {"jid": je_id, "aid": bank_account_id, "amount": data.amount,
                   "desc": f"دفع ضريبة — {tr.tax_period}", "curr": base_currency})
            update_account_balance(db, bank_account_id, debit_base=0, credit_base=data.amount)

        # Update return status if fully paid
        new_paid = float(paid) + data.amount
        if new_paid >= float(tr.total_amount) - 0.01:
            db.execute(text("UPDATE tax_returns SET status = 'paid' WHERE id = :id"), {"id": data.tax_return_id})

        db.commit()

        log_activity(db, user_id=current_user.id, username=current_user.username,
                     action="taxes.payment.create", resource_type="tax_payment",
                     resource_id=str(new_id),
                     details={"payment_number": payment_number, "amount": data.amount, "return": tr.return_number},
                     request=request)

        return {"success": True, "id": new_id, "payment_number": payment_number,
                "message": "تم تسجيل الدفعة الضريبية بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating tax payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ==================== VAT REPORT ====================

@router.get("/vat-report", response_model=Dict[str, Any], dependencies=[Depends(require_permission(["accounting.view", "taxes.view", "reports.view"]))])
def get_vat_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """جلب تقرير ضريبة القيمة المضافة للفترة المحددة"""
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    try:
        if not start_date:
            start_date = date.today().replace(day=1)
        if not end_date:
            end_date = date.today()

        params = {"start": start_date, "end": end_date}
        branch_filter = "AND i.branch_id = :branch_id" if branch_id else ""
        if branch_id:
            params["branch_id"] = branch_id

        output_vat = db.execute(text(f"""
            SELECT COALESCE(SUM(il.quantity * il.unit_price * i.exchange_rate), 0) as taxable_amount,
                   COALESCE(SUM(il.quantity * il.unit_price * i.exchange_rate * (il.tax_rate / 100)), 0) as vat_amount
            FROM invoice_lines il JOIN invoices i ON il.invoice_id = i.id
            WHERE i.invoice_type = 'sales' AND i.status NOT IN ('draft', 'cancelled')
            AND i.invoice_date BETWEEN :start AND :end {branch_filter}
        """), params).fetchone()

        input_vat = db.execute(text(f"""
            SELECT COALESCE(SUM(il.quantity * il.unit_price * i.exchange_rate), 0) as taxable_amount,
                   COALESCE(SUM(il.quantity * il.unit_price * i.exchange_rate * (il.tax_rate / 100)), 0) as vat_amount
            FROM invoice_lines il JOIN invoices i ON il.invoice_id = i.id
            WHERE i.invoice_type = 'purchase' AND i.status NOT IN ('draft', 'cancelled')
            AND i.invoice_date BETWEEN :start AND :end {branch_filter}
        """), params).fetchone()

        output_vat_returns = db.execute(text(f"""
            SELECT COALESCE(SUM(il.quantity * il.unit_price * i.exchange_rate), 0) as taxable_amount,
                   COALESCE(SUM(il.quantity * il.unit_price * i.exchange_rate * (il.tax_rate / 100)), 0) as vat_amount
            FROM invoice_lines il JOIN invoices i ON il.invoice_id = i.id
            WHERE i.invoice_type = 'sales_return' AND i.status NOT IN ('draft', 'cancelled')
            AND i.invoice_date BETWEEN :start AND :end {branch_filter}
        """), params).fetchone()

        input_vat_returns = db.execute(text(f"""
            SELECT COALESCE(SUM(il.quantity * il.unit_price * i.exchange_rate), 0) as taxable_amount,
                   COALESCE(SUM(il.quantity * il.unit_price * i.exchange_rate * (il.tax_rate / 100)), 0) as vat_amount
            FROM invoice_lines il JOIN invoices i ON il.invoice_id = i.id
            WHERE i.invoice_type = 'purchase_return' AND i.status NOT IN ('draft', 'cancelled')
            AND i.invoice_date BETWEEN :start AND :end {branch_filter}
        """), params).fetchone()

        net_output_taxable = float(output_vat.taxable_amount or 0) - float(output_vat_returns.taxable_amount or 0)
        net_output_vat = float(output_vat.vat_amount or 0) - float(output_vat_returns.vat_amount or 0)
        net_input_taxable = float(input_vat.taxable_amount or 0) - float(input_vat_returns.taxable_amount or 0)
        net_input_vat = float(input_vat.vat_amount or 0) - float(input_vat_returns.vat_amount or 0)

        return {
            "period": {"start": start_date, "end": end_date},
            "output_vat": {"taxable": net_output_taxable, "vat": net_output_vat},
            "input_vat": {"taxable": net_input_taxable, "vat": net_input_vat},
            "net_vat_payable": net_output_vat - net_input_vat
        }
    finally:
        db.close()


# ==================== TAX AUDIT ====================

@router.get("/audit-report", response_model=List[dict], dependencies=[Depends(require_permission(["accounting.view", "taxes.view", "reports.view"]))])
def get_tax_audit(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """تقرير تدقيق ضريبي مفصل لكل معاملة خاضعة للضريبة بالفترة"""
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    try:
        if not start_date:
            start_date = date.today().replace(day=1)
        if not end_date:
            end_date = date.today()

        params = {"start": start_date, "end": end_date}
        branch_filter = "AND i.branch_id = :branch_id" if branch_id else ""
        if branch_id:
            params["branch_id"] = branch_id

        results = db.execute(text(f"""
            SELECT i.id, i.invoice_number, i.invoice_date, i.invoice_type,
                p.name as party_name, p.tax_number,
                SUM(il.quantity * il.unit_price * i.exchange_rate) as taxable_amount,
                SUM(il.quantity * il.unit_price * i.exchange_rate * (il.tax_rate / 100)) as vat_amount
            FROM invoices i
            JOIN invoice_lines il ON i.id = il.invoice_id
            LEFT JOIN parties p ON i.party_id = p.id
            WHERE i.invoice_date BETWEEN :start AND :end
              AND il.tax_rate > 0 AND i.status != 'draft'
              {branch_filter}
            GROUP BY i.id, i.invoice_number, i.invoice_date, i.invoice_type, p.name, p.tax_number
            ORDER BY i.invoice_date DESC
        """), params).fetchall()

        return [
            {
                "id": r.id, "number": r.invoice_number, "date": r.invoice_date,
                "type": r.invoice_type, "party": r.party_name, "tax_number": r.tax_number,
                "taxable": float(r.taxable_amount or 0), "vat": float(r.vat_amount or 0)
            }
            for r in results
        ]
    finally:
        db.close()


# ==================== TAX SUMMARY ====================

@router.get("/summary", dependencies=[Depends(require_permission(["accounting.view", "taxes.view"]))])
def get_tax_summary(current_user: dict = Depends(get_current_user)):
    """ملخص وحدة الضرائب (لوحة تحكم)"""
    db = get_db_connection(current_user.company_id)
    try:
        rates_count = db.execute(text("SELECT COUNT(*) FROM tax_rates WHERE is_active = TRUE")).scalar() or 0

        returns_stats = db.execute(text("""
            SELECT COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'draft') as draft,
                COUNT(*) FILTER (WHERE status = 'filed') as filed,
                COUNT(*) FILTER (WHERE status = 'paid') as paid,
                COALESCE(SUM(total_amount) FILTER (WHERE status = 'filed'), 0) as pending_amount,
                COALESCE(SUM(total_amount) FILTER (WHERE status = 'paid'), 0) as paid_amount
            FROM tax_returns WHERE status != 'cancelled'
        """)).fetchone()

        today = date.today()
        first_of_month = today.replace(day=1)
        current_vat = db.execute(text("""
            SELECT
                COALESCE(SUM(CASE WHEN i.invoice_type = 'sales' THEN il.quantity * il.unit_price * i.exchange_rate * (il.tax_rate / 100) ELSE 0 END), 0) as output_vat,
                COALESCE(SUM(CASE WHEN i.invoice_type = 'purchase' THEN il.quantity * il.unit_price * i.exchange_rate * (il.tax_rate / 100) ELSE 0 END), 0) as input_vat
            FROM invoice_lines il JOIN invoices i ON il.invoice_id = i.id
            WHERE i.invoice_date >= :start AND i.invoice_date <= :end
            AND i.status NOT IN ('draft', 'cancelled') AND il.tax_rate > 0
        """), {"start": first_of_month, "end": today}).fetchone()

        overdue = db.execute(text(
            "SELECT COUNT(*) FROM tax_returns WHERE status = 'filed' AND due_date < CURRENT_DATE"
        )).scalar() or 0

        return {
            "active_rates": rates_count,
            "returns": {
                "total": returns_stats.total or 0, "draft": returns_stats.draft or 0,
                "filed": returns_stats.filed or 0, "paid": returns_stats.paid or 0,
                "pending_amount": float(returns_stats.pending_amount or 0),
                "paid_amount": float(returns_stats.paid_amount or 0)
            },
            "current_period": {
                "output_vat": float(current_vat.output_vat or 0),
                "input_vat": float(current_vat.input_vat or 0),
                "net_vat": float(current_vat.output_vat or 0) - float(current_vat.input_vat or 0)
            },
            "overdue_returns": overdue
        }
    finally:
        db.close()


# ==================== TAX SETTLEMENT ====================

@router.post("/settle", dependencies=[Depends(require_permission(["accounting.manage", "taxes.manage"]))])
def create_tax_settlement(
    request: Request, body: dict,
    current_user: dict = Depends(get_current_user)
):
    """تسوية ضريبية — قيد محاسبي لتسوية رصيد ضريبة المدخلات مع المخرجات"""
    db = get_db_connection(current_user.company_id)
    try:
        start = body.get("period_start")
        end = body.get("period_end")
        branch_id = validate_branch_access(current_user, body.get("branch_id"))

        if not start or not end:
            raise HTTPException(status_code=400, detail="يجب تحديد فترة التسوية")

        params = {"start": start, "end": end}
        branch_filter = ""
        if branch_id:
            branch_filter = "AND i.branch_id = :branch_id"
            params["branch_id"] = branch_id

        output = db.execute(text(f"""
            SELECT COALESCE(SUM(il.quantity * il.unit_price * i.exchange_rate * (il.tax_rate / 100)), 0) as vat
            FROM invoice_lines il JOIN invoices i ON il.invoice_id = i.id
            WHERE i.invoice_type = 'sales' AND i.status NOT IN ('draft','cancelled')
            AND i.invoice_date BETWEEN :start AND :end {branch_filter}
        """), params).scalar() or 0

        input_v = db.execute(text(f"""
            SELECT COALESCE(SUM(il.quantity * il.unit_price * i.exchange_rate * (il.tax_rate / 100)), 0) as vat
            FROM invoice_lines il JOIN invoices i ON il.invoice_id = i.id
            WHERE i.invoice_type = 'purchase' AND i.status NOT IN ('draft','cancelled')
            AND i.invoice_date BETWEEN :start AND :end {branch_filter}
        """), params).scalar() or 0

        net = float(output) - float(input_v)

        vat_out_id = get_mapped_account_id(db, "acc_map_vat_out")
        vat_in_id = get_mapped_account_id(db, "acc_map_vat_in")

        if not vat_out_id or not vat_in_id:
            raise HTTPException(status_code=400, detail="حسابات ضريبة المدخلات/المخرجات غير معينة في الإعدادات")

        base_currency = get_base_currency(db)
        entry_number = generate_sequential_number(db, "JE", "journal_entries", "entry_number")

        je_id = db.execute(text("""
            INSERT INTO journal_entries (entry_number, entry_date, description, reference,
                                         status, branch_id, created_by, currency, exchange_rate)
            VALUES (:num, CURRENT_DATE, :desc, :ref, 'posted', :bid, :user, :curr, 1)
            RETURNING id
        """), {
            "num": entry_number, "desc": f"تسوية ضريبية — الفترة {start} إلى {end}",
            "ref": f"TAX-SETTLE-{start}-{end}",
            "bid": branch_id, "user": current_user.id, "curr": base_currency
        }).scalar()

        settle_amount = min(float(output), float(input_v))
        if settle_amount > 0:
            # Debit Input VAT (clear input)
            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description, currency, amount_currency)
                VALUES (:jid, :aid, :amt, 0, :desc, :curr, :amt)
            """), {"jid": je_id, "aid": vat_in_id, "amt": settle_amount,
                   "desc": "تسوية ضريبة المدخلات", "curr": base_currency})
            update_account_balance(db, vat_in_id, debit_base=settle_amount, credit_base=0)

            # Credit Output VAT (reduce output by input amount)
            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description, currency, amount_currency)
                VALUES (:jid, :aid, 0, :amt, :desc, :curr, :amt)
            """), {"jid": je_id, "aid": vat_out_id, "amt": settle_amount,
                   "desc": "تسوية ضريبة المدخلات مع المخرجات", "curr": base_currency})
            update_account_balance(db, vat_out_id, debit_base=0, credit_base=settle_amount)

        db.commit()

        log_activity(db, user_id=current_user.id, username=current_user.username,
                     action="taxes.settlement.create", resource_type="tax_settlement",
                     resource_id=entry_number,
                     details={"period": f"{start} - {end}", "net": net, "je": entry_number},
                     request=request)

        return {
            "success": True, "message": "تم إنشاء التسوية الضريبية بنجاح",
            "journal_entry": entry_number,
            "output_vat": float(output), "input_vat": float(input_v),
            "net_amount": net,
            "settlement_type": "payable" if net >= 0 else "refundable"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating tax settlement: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
