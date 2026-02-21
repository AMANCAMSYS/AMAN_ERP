from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import date, timedelta
import logging

from database import get_db_connection
from routers.auth import get_current_user, UserResponse
from schemas.contracts import ContractCreate, ContractResponse
from utils.permissions import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contracts", tags=["Contracts"])

@router.post("", response_model=ContractResponse, dependencies=[Depends(require_permission("contracts.create"))])
def create_contract(
    contract: ContractCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    db = get_db_connection(current_user.company_id)
    try:
        # Validate dates
        if contract.start_date and contract.end_date and contract.end_date < contract.start_date:
            raise HTTPException(status_code=400, detail="تاريخ نهاية العقد يجب أن يكون بعد تاريخ البداية")

        # Validate contract number uniqueness
        if contract.contract_number:
            existing = db.execute(
                text("SELECT id FROM contracts WHERE contract_number = :num"),
                {"num": contract.contract_number}
            ).fetchone()
            if existing:
                raise HTTPException(status_code=400, detail="رقم العقد مكرر، يرجى استخدام رقم مختلف")

        # Recalculate total_amount from items to prevent client manipulation
        calculated_total = 0
        for item in contract.items:
            calculated_total += item.quantity * item.unit_price * (1 + item.tax_rate / 100)
        
        # Use calculated total (override client-provided total)
        final_total = round(calculated_total, 2)

        # Create Contract Header
        contract_id = db.execute(
            text("""
                INSERT INTO contracts (
                    contract_number, party_id, contract_type, status, 
                    start_date, end_date, billing_interval, total_amount, 
                    currency, notes, created_by, created_at
                ) VALUES (
                    :num, :pid, :ctype, 'active', :start, :end, :interval, :total,
                    :cur, :notes, :uid, CURRENT_TIMESTAMP
                ) RETURNING id
            """),
            {
                "num": contract.contract_number,
                "pid": contract.party_id,
                "ctype": contract.contract_type,
                "start": contract.start_date,
                "end": contract.end_date,
                "interval": contract.billing_interval,
                "total": final_total,
                "cur": contract.currency,
                "notes": contract.notes,
                "uid": current_user.id
            }
        ).scalar()

        # Create Contract Items
        for item in contract.items:
            item_total = item.quantity * item.unit_price * (1 + item.tax_rate/100)
            db.execute(
                text("""
                    INSERT INTO contract_items (
                        contract_id, product_id, description, quantity, 
                        unit_price, tax_rate, total
                    ) VALUES (
                        :cid, :pid, :desc, :qty, :price, :tax, :total
                    )
                """),
                {
                    "cid": contract_id,
                    "pid": item.product_id,
                    "desc": item.description,
                    "qty": item.quantity,
                    "price": item.unit_price,
                    "tax": item.tax_rate,
                    "total": item_total
                }
            )
        
        db.commit()
        return get_contract(contract_id, current_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("", response_model=List[ContractResponse], dependencies=[Depends(require_permission("contracts.view"))])
def list_contracts(current_user: UserResponse = Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        contracts = db.execute(text("""
            SELECT c.*, p.name as party_name 
            FROM contracts c
            JOIN parties p ON c.party_id = p.id
            ORDER BY c.created_at DESC
        """)).fetchall()
        
        result = []
        for c in contracts:
            items = db.execute(
                text("SELECT * FROM contract_items WHERE contract_id = :cid"),
                {"cid": c.id}
            ).fetchall()
            
            result.append({
                **c._mapping,
                "items": [dict(row._mapping) for row in items]
            })
        return result
    finally:
        db.close()

@router.get("/{contract_id}", response_model=ContractResponse, dependencies=[Depends(require_permission("contracts.view"))])
def get_contract(
    contract_id: int, 
    current_user: UserResponse = Depends(get_current_user)
):
    db = get_db_connection(current_user.company_id)
    try:
        contract = db.execute(
            text("""
                SELECT c.*, p.name as party_name 
                FROM contracts c
                JOIN parties p ON c.party_id = p.id
                WHERE c.id = :id
            """),
            {"id": contract_id}
        ).fetchone()
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
            
        items = db.execute(
            text("SELECT * FROM contract_items WHERE contract_id = :id"),
            {"id": contract_id}
        ).fetchall()
        
        return {
            **contract._mapping,
            "items": [dict(row._mapping) for row in items]
        }
    finally:
        db.close()


@router.put("/{contract_id}", response_model=ContractResponse, dependencies=[Depends(require_permission("contracts.edit"))])
def update_contract(
    contract_id: int,
    data: ContractCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    db = get_db_connection(current_user.company_id)
    trans = db.begin()
    try:
        existing = db.execute(text("SELECT * FROM contracts WHERE id = :id"), {"id": contract_id}).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="العقد غير موجود")

        db.execute(text("""
            UPDATE contracts SET
                party_id = :party_id, contract_type = :contract_type,
                start_date = :start_date, end_date = :end_date,
                billing_interval = :billing_interval, total_amount = :total_amount,
                currency = :currency, notes = :notes
            WHERE id = :id
        """), {
            "id": contract_id, "party_id": data.party_id,
            "contract_type": data.contract_type, "start_date": data.start_date,
            "end_date": data.end_date, "billing_interval": data.billing_interval,
            "total_amount": data.total_amount, "currency": data.currency, "notes": data.notes
        })

        db.execute(text("DELETE FROM contract_items WHERE contract_id = :id"), {"id": contract_id})
        for item in data.items:
            total = item.quantity * item.unit_price * (1 + item.tax_rate / 100)
            db.execute(text("""
                INSERT INTO contract_items (contract_id, product_id, description, quantity, unit_price, tax_rate, total)
                VALUES (:cid, :pid, :desc, :qty, :price, :tax, :total)
            """), {
                "cid": contract_id, "pid": item.product_id, "desc": item.description,
                "qty": item.quantity, "price": item.unit_price, "tax": item.tax_rate, "total": total
            })

        trans.commit()
        return get_contract(contract_id, current_user)
    except HTTPException:
        trans.rollback()
        raise
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/{contract_id}/renew", response_model=ContractResponse, dependencies=[Depends(require_permission("contracts.manage"))])
def renew_contract(
    contract_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """تجديد العقد - ينشئ فترة جديدة بناءً على فترة الفوترة"""
    db = get_db_connection(current_user.company_id)
    try:
        contract = db.execute(
            text("SELECT * FROM contracts WHERE id = :id"),
            {"id": contract_id}
        ).fetchone()
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        if contract.status != 'active':
            raise HTTPException(status_code=400, detail="يمكن تجديد العقود النشطة فقط")
        
        from datetime import timedelta
        from dateutil.relativedelta import relativedelta
        
        old_end = contract.end_date
        interval = contract.billing_interval or 'monthly'
        
        # Calculate new dates based on billing interval
        if interval == 'monthly':
            delta = relativedelta(months=1)
        elif interval == 'quarterly':
            delta = relativedelta(months=3)
        elif interval == 'semi_annual':
            delta = relativedelta(months=6)
        elif interval == 'annual':
            delta = relativedelta(years=1)
        else:
            delta = relativedelta(months=1)
        
        new_start = old_end + timedelta(days=1)
        new_end = new_start + delta - timedelta(days=1)
        
        # Update contract dates
        db.execute(
            text("""
                UPDATE contracts 
                SET start_date = :start, end_date = :end, 
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """),
            {"start": new_start, "end": new_end, "id": contract_id}
        )
        
        db.commit()
        return get_contract(contract_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/{contract_id}/generate-invoice", dependencies=[Depends(require_permission("contracts.manage"))])
def generate_contract_invoice(
    contract_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """إنشاء فاتورة من العقد"""
    db = get_db_connection(current_user.company_id)
    try:
        contract = db.execute(
            text("SELECT * FROM contracts WHERE id = :id AND status = 'active'"),
            {"id": contract_id}
        ).fetchone()
        
        if not contract:
            raise HTTPException(status_code=404, detail="العقد غير موجود أو غير نشط")
        
        items = db.execute(
            text("SELECT * FROM contract_items WHERE contract_id = :id"),
            {"id": contract_id}
        ).fetchall()
        
        if not items:
            raise HTTPException(status_code=400, detail="لا توجد بنود في العقد")
        
        import uuid
        from datetime import date as dt_date
        from utils.accounting import generate_sequential_number
        
        inv_num = generate_sequential_number(db, f"INV-CTR-{dt_date.today().year}", "invoices", "invoice_number")
        subtotal = sum(float(i.quantity) * float(i.unit_price) for i in items)
        tax_total = sum(float(i.quantity) * float(i.unit_price) * float(i.tax_rate) / 100 for i in items)
        total = subtotal + tax_total
        
        inv_id = db.execute(text("""
            INSERT INTO invoices (
                invoice_number, invoice_type, party_id, invoice_date, due_date,
                subtotal, tax_amount, total, paid_amount, status, notes,
                created_by, currency, exchange_rate
            ) VALUES (
                :num, :type, :pid, CURRENT_DATE, CURRENT_DATE + 30,
                :sub, :tax, :total, 0, 'unpaid', :notes,
                :uid, :curr, 1.0
            ) RETURNING id
        """), {
            "num": inv_num,
            "type": 'sales' if contract.contract_type == 'sales' else 'purchase',
            "pid": contract.party_id,
            "sub": subtotal, "tax": tax_total, "total": total,
            "notes": f"فاتورة عقد #{contract.contract_number}",
            "uid": current_user.id,
            "curr": contract.currency or 'SYP'
        }).scalar()
        
        for item in items:
            item_total = float(item.quantity) * float(item.unit_price) * (1 + float(item.tax_rate) / 100)
            db.execute(text("""
                INSERT INTO invoice_lines (invoice_id, product_id, description, quantity, unit_price, tax_rate, total)
                VALUES (:iid, :pid, :desc, :qty, :price, :tax, :total)
            """), {
                "iid": inv_id, "pid": item.product_id, "desc": item.description,
                "qty": item.quantity, "price": item.unit_price, "tax": item.tax_rate, "total": item_total
            })
        
        db.commit()
        return {"success": True, "invoice_id": inv_id, "invoice_number": inv_num, "total": total}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/{contract_id}/cancel", dependencies=[Depends(require_permission("contracts.manage"))])
def cancel_contract(
    contract_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """إلغاء عقد نشط"""
    db = get_db_connection(current_user.company_id)
    try:
        contract = db.execute(
            text("SELECT * FROM contracts WHERE id = :id"),
            {"id": contract_id}
        ).fetchone()
        
        if not contract:
            raise HTTPException(status_code=404, detail="العقد غير موجود")
        
        if contract.status == 'cancelled':
            raise HTTPException(status_code=400, detail="العقد ملغي بالفعل")
        
        db.execute(
            text("UPDATE contracts SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
            {"id": contract_id}
        )
        db.commit()
        return {"message": "تم إلغاء العقد بنجاح", "id": contract_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error cancelling contract {contract_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/alerts/expiring", dependencies=[Depends(require_permission("contracts.view"))])
def get_expiring_contracts(
    days: int = 30,
    current_user: UserResponse = Depends(get_current_user)
):
    """جلب العقود التي ستنتهي خلال فترة محددة (افتراضي 30 يوم)"""
    db = get_db_connection(current_user.company_id)
    try:
        today = date.today()
        future_date = today + timedelta(days=days)
        
        contracts = db.execute(text("""
            SELECT c.*, p.name as party_name,
                   (c.end_date - CURRENT_DATE) as days_remaining
            FROM contracts c
            JOIN parties p ON c.party_id = p.id
            WHERE c.status = 'active' 
              AND c.end_date IS NOT NULL
              AND c.end_date BETWEEN :today AND :future
            ORDER BY c.end_date ASC
        """), {"today": today, "future": future_date}).fetchall()
        
        result = []
        for c in contracts:
            result.append({
                "id": c.id,
                "contract_number": c.contract_number,
                "party_name": c.party_name,
                "contract_type": c.contract_type,
                "end_date": str(c.end_date),
                "days_remaining": c.days_remaining,
                "total_amount": float(c.total_amount or 0),
                "billing_interval": c.billing_interval,
                "currency": c.currency
            })
        
        return {
            "count": len(result),
            "contracts": result,
            "period_days": days
        }
    except Exception as e:
        logger.error(f"Error fetching expiring contracts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/stats/summary", dependencies=[Depends(require_permission("contracts.view"))])
def get_contracts_summary(
    current_user: UserResponse = Depends(get_current_user)
):
    """ملخص إحصائيات العقود"""
    db = get_db_connection(current_user.company_id)
    try:
        stats = db.execute(text("""
            SELECT 
                COUNT(*) as total_contracts,
                COUNT(*) FILTER (WHERE status = 'active') as active_count,
                COUNT(*) FILTER (WHERE status = 'expired') as expired_count,
                COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled_count,
                COALESCE(SUM(total_amount) FILTER (WHERE status = 'active'), 0) as active_value,
                COALESCE(SUM(total_amount), 0) as total_value,
                COUNT(*) FILTER (WHERE status = 'active' AND end_date IS NOT NULL AND end_date <= CURRENT_DATE + INTERVAL '30 days') as expiring_soon
            FROM contracts
        """)).fetchone()
        
        return {
            "total_contracts": stats.total_contracts,
            "active_count": stats.active_count,
            "expired_count": stats.expired_count,
            "cancelled_count": stats.cancelled_count,
            "active_value": float(stats.active_value),
            "total_value": float(stats.total_value),
            "expiring_soon": stats.expiring_soon
        }
    except Exception as e:
        logger.error(f"Error fetching contract stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
