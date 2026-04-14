
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from database import get_db_connection
from routers.auth import get_current_user
from pydantic import BaseModel
from datetime import datetime
from utils.permissions import require_permission, validate_branch_access, require_module
from utils.accounting import get_mapped_account_id
from utils.fiscal_lock import check_fiscal_period_open
from schemas.assets import AssetCreate, AssetUpdate, AssetDisposal
import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assets", tags=["الأصول الثابتة"], dependencies=[Depends(require_module("assets"))])

_D2 = Decimal("0.01")
_D4 = Decimal("0.0001")


def _dec(v) -> Decimal:
    return Decimal(str(v)) if v is not None else Decimal("0")

# ============================================================
# ❗️ IMPORTANT: Static routes MUST come before /{asset_id}
#   to prevent FastAPI from treating 'transfers'/'revaluations'
#   as an integer path parameter (causing 422 errors).
# ============================================================

# ---------- ASSET-002: Asset Transfers (STATIC - must be before /{asset_id}) ----------

@router.get("/transfers", dependencies=[Depends(require_permission("assets.view"))])
def list_asset_transfers(status: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        q = "SELECT * FROM asset_transfers WHERE 1=1"
        params = {}
        if status:
            q += " AND status = :status"
            params["status"] = status
        q += " ORDER BY created_at DESC"
        rows = conn.execute(text(q), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()


@router.post("/transfers", dependencies=[Depends(require_permission("assets.create"))])
def create_asset_transfer(data: dict, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        asset = conn.execute(text("SELECT * FROM assets WHERE id = :id"), {"id": data["asset_id"]}).fetchone()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        dep_sum = conn.execute(text(
            "SELECT COALESCE(SUM(amount),0) FROM asset_depreciation_schedule WHERE asset_id = :id AND posted = true"
        ), {"id": data["asset_id"]}).scalar()
        book_value = (_dec(asset.cost) - _dec(dep_sum or 0)).quantize(_D2, ROUND_HALF_UP)

        result = conn.execute(text("""
            INSERT INTO asset_transfers (asset_id, from_branch_id, to_branch_id, transfer_date,
                reason, book_value_at_transfer, status, created_by)
            VALUES (:aid, :from, :to, :date, :reason, :bv, 'pending', :uid)
            RETURNING *
        """), {
            "aid": data["asset_id"], "from": asset.branch_id,
            "to": data["to_branch_id"], "date": data.get("transfer_date", date.today().isoformat()),
            "reason": data.get("reason"), "bv": book_value, "uid": current_user.id,
        }).fetchone()
        conn.commit()
        return dict(result._mapping)
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.exception("Internal error")
        raise HTTPException(status_code=500, detail="حدث خطأ داخلي")
    finally:
        conn.close()


@router.put("/transfers/{transfer_id}/approve", dependencies=[Depends(require_permission("assets.create"))])
def approve_transfer(transfer_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        t = conn.execute(text("SELECT * FROM asset_transfers WHERE id = :id"), {"id": transfer_id}).fetchone()
        if not t or t.status != 'pending':
            raise HTTPException(status_code=404, detail="Pending transfer not found")
        conn.execute(text("UPDATE asset_transfers SET status = 'approved', approved_by = :uid WHERE id = :id"),
                     {"uid": current_user.id, "id": transfer_id})
        conn.execute(text("UPDATE assets SET branch_id = :bid WHERE id = :aid"),
                     {"bid": t.to_branch_id, "aid": t.asset_id})
        conn.commit()
        return {"message": "Transfer approved, asset moved to new branch"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.exception("Internal error")
        raise HTTPException(status_code=500, detail="حدث خطأ داخلي")
    finally:
        conn.close()


# ---------- ASSET-003: Asset Revaluations (STATIC - must be before /{asset_id}) ----------

@router.get("/revaluations", dependencies=[Depends(require_permission("assets.view"))])
def list_revaluations(asset_id: Optional[int] = None, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        q = "SELECT * FROM asset_revaluations WHERE 1=1"
        params = {}
        if asset_id:
            q += " AND asset_id = :aid"
            params["aid"] = asset_id
        q += " ORDER BY revaluation_date DESC"
        rows = conn.execute(text(q), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()


@router.post("/revaluations", dependencies=[Depends(require_permission("assets.create"))])
def create_revaluation(data: dict, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        asset = conn.execute(text("SELECT * FROM assets WHERE id = :id"), {"id": data["asset_id"]}).fetchone()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        dep_sum = conn.execute(text(
            "SELECT COALESCE(SUM(amount),0) FROM asset_depreciation_schedule WHERE asset_id = :id AND posted = true"
        ), {"id": data["asset_id"]}).scalar()
        old_value = (_dec(asset.cost) - _dec(dep_sum or 0)).quantize(_D2, ROUND_HALF_UP)
        new_value = _dec(data["new_value"]).quantize(_D2, ROUND_HALF_UP)
        diff = (new_value - old_value).quantize(_D2, ROUND_HALF_UP)

        result = conn.execute(text("""
            INSERT INTO asset_revaluations (asset_id, revaluation_date, old_value, new_value, difference, reason, created_by)
            VALUES (:aid, :date, :old, :new, :diff, :reason, :uid)
            RETURNING *
        """), {
            "aid": data["asset_id"], "date": data.get("revaluation_date", date.today().isoformat()),
            "old": old_value, "new": new_value, "diff": diff,
            "reason": data.get("reason"), "uid": current_user.id,
        }).fetchone()
        conn.commit()
        return dict(result._mapping)
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.exception("Internal error")
        raise HTTPException(status_code=500, detail="حدث خطأ داخلي")
    finally:
        conn.close()


# ---------- Maintenance complete (STATIC - must be before /{asset_id}) ----------

@router.put("/maintenance/{maint_id}/complete", dependencies=[Depends(require_permission("assets.create"))])
def complete_maintenance(maint_id: int, data: dict = {}, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        conn.execute(text("""
            UPDATE asset_maintenance SET status = 'completed', completed_date = :d,
                cost = COALESCE(:cost, cost) WHERE id = :id
        """), {"d": data.get("completed_date", date.today().isoformat()),
               "cost": data.get("actual_cost"), "id": maint_id})
        conn.commit()
        return {"message": "Maintenance completed"}
    finally:
        conn.close()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ASSET REPORTS (Static routes — MUST come before /{asset_id})
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/reports/register", dependencies=[Depends(require_permission("assets.view"))])
def asset_register_report(
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """تقرير سجل الأصول الثابتة"""
    conn = get_db_connection(current_user.company_id)
    try:
        params = {}
        branch_filter = "AND a.branch_id = :branch_id" if branch_id else ""
        if branch_id:
            params["branch_id"] = branch_id

        rows = conn.execute(text(f"""
            SELECT
                a.id, a.code, a.name, a.type, a.purchase_date,
                a.cost, a.residual_value, a.life_years,
                a.depreciation_method, a.status, a.currency,
                COALESCE(ds.total_depreciation, 0) as accumulated_depreciation,
                a.cost - COALESCE(ds.total_depreciation, 0) as net_book_value,
                b.branch_name as branch_name
            FROM assets a
            LEFT JOIN branches b ON a.branch_id = b.id
            LEFT JOIN (
                SELECT asset_id, SUM(amount) as total_depreciation
                FROM asset_depreciation_schedule
                WHERE posted = TRUE
                GROUP BY asset_id
            ) ds ON ds.asset_id = a.id
            WHERE 1=1 {branch_filter}
            ORDER BY a.code
        """), params).fetchall()

        items = []
        for r in rows:
            items.append({
                "id": r.id,
                "code": r.code,
                "name": r.name,
                "category": r.type,
                "purchase_date": str(r.purchase_date) if r.purchase_date else None,
                "original_cost": float(r.cost or 0),
                "cost": float(r.cost or 0),
                "residual_value": float(r.residual_value or 0),
                "life_years": r.life_years,
                "depreciation_method": r.depreciation_method,
                "accumulated_depreciation": float(r.accumulated_depreciation),
                "net_book_value": float(r.net_book_value),
                "status": r.status,
                "currency": r.currency,
                "branch": r.branch_name,
            })

        return {"items": items, "count": len(items)}
    finally:
        conn.close()


@router.get("/reports/depreciation-summary", dependencies=[Depends(require_permission("assets.view"))])
def asset_depreciation_summary(
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """ملخص إهلاك الأصول الثابتة"""
    conn = get_db_connection(current_user.company_id)
    try:
        params = {}
        branch_filter = "AND a.branch_id = :branch_id" if branch_id else ""
        if branch_id:
            params["branch_id"] = branch_id

        rows = conn.execute(text(f"""
            SELECT
                a.id, a.code, a.name, a.type,
                a.cost, a.residual_value, a.life_years,
                a.depreciation_method, a.currency, a.status,
                COALESCE(ds.total_depreciation, 0) as total_depreciation,
                COALESCE(ds.periods_posted, 0) as periods_posted,
                CASE WHEN a.life_years > 0 AND a.cost > a.residual_value
                     THEN ROUND((a.cost - a.residual_value) / a.life_years, 2)
                     ELSE 0 END as annual_depreciation
            FROM assets a
            LEFT JOIN (
                SELECT asset_id,
                       SUM(amount) as total_depreciation,
                       COUNT(*) as periods_posted
                FROM asset_depreciation_schedule
                WHERE posted = TRUE
                GROUP BY asset_id
            ) ds ON ds.asset_id = a.id
            WHERE a.status != 'disposed' {branch_filter}
            ORDER BY a.code
        """), params).fetchall()

        items = []
        for r in rows:
            cost = _dec(r.cost or 0)
            total_depr = _dec(r.total_depreciation or 0)
            net_book_value = (cost - total_depr).quantize(_D2, ROUND_HALF_UP)
            depreciation_pct = ((total_depr / cost) * Decimal('100')).quantize(Decimal('0.1'), ROUND_HALF_UP) if cost > 0 else Decimal('0')
            items.append({
                "id": r.id,
                "code": r.code,
                "name": r.name,
                "category": r.type,
                "cost": float(cost.quantize(_D2, ROUND_HALF_UP)),
                "residual_value": float(_dec(r.residual_value or 0).quantize(_D2, ROUND_HALF_UP)),
                "life_years": r.life_years,
                "depreciation_method": r.depreciation_method,
                "annual_depreciation": float(_dec(r.annual_depreciation or 0).quantize(_D2, ROUND_HALF_UP)),
                "total_depreciation": float(total_depr.quantize(_D2, ROUND_HALF_UP)),
                "accumulated_depreciation": float(total_depr.quantize(_D2, ROUND_HALF_UP)),
                "net_book_value": float(net_book_value),
                "nbv": float(net_book_value),
                "periods_posted": r.periods_posted,
                "currency": r.currency,
                "depreciation_pct": float(depreciation_pct),
            })

        return {"items": items, "count": len(items)}
    finally:
        conn.close()


@router.get("/reports/net-book-value", dependencies=[Depends(require_permission("assets.view"))])
def asset_net_book_value_report(
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """تقرير صافي القيمة الدفترية للأصول"""
    conn = get_db_connection(current_user.company_id)
    try:
        params = {}
        branch_filter = "AND a.branch_id = :branch_id" if branch_id else ""
        if branch_id:
            params["branch_id"] = branch_id

        rows = conn.execute(text(f"""
            SELECT
                a.id, a.code, a.name, a.type,
                a.cost, a.currency, a.status, a.purchase_date,
                COALESCE(ds.total_depreciation, 0) as accumulated_depreciation,
                a.cost - COALESCE(ds.total_depreciation, 0) as net_book_value
            FROM assets a
            LEFT JOIN (
                SELECT asset_id, SUM(amount) as total_depreciation
                FROM asset_depreciation_schedule
                WHERE posted = TRUE
                GROUP BY asset_id
            ) ds ON ds.asset_id = a.id
            WHERE a.status != 'disposed' {branch_filter}
            ORDER BY (a.cost - COALESCE(ds.total_depreciation, 0)) DESC
        """), params).fetchall()

        items = []
        for r in rows:
            cost = _dec(r.cost or 0).quantize(_D2, ROUND_HALF_UP)
            acc_depr = _dec(r.accumulated_depreciation or 0).quantize(_D2, ROUND_HALF_UP)
            nbv = _dec(r.net_book_value or 0).quantize(_D2, ROUND_HALF_UP)
            items.append({
                "id": r.id,
                "code": r.code,
                "name": r.name,
                "category": r.type,
                "original_cost": float(cost),
                "cost": float(cost),
                "accumulated_depreciation": float(acc_depr),
                "total_depreciation": float(acc_depr),
                "net_book_value": float(nbv),
                "nbv": float(nbv),
                "status": r.status,
                "currency": r.currency,
                "purchase_date": str(r.purchase_date) if r.purchase_date else None,
            })

        return {"items": items, "count": len(items)}
    finally:
        conn.close()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PARAMETERIZED ROUTES (/{asset_id}) come BELOW the static routes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.get("/", dependencies=[Depends(require_permission("assets.view"))])
def list_assets(
    branch_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    # Validate branch access
    branch_id = validate_branch_access(current_user, branch_id)
    
    conn = get_db_connection(current_user.company_id)
    try:
        params = {}
        query = "SELECT * FROM assets WHERE 1=1"
        
        if branch_id:
            query += " AND branch_id = :branch_id"
            params["branch_id"] = branch_id
        if status:
            query += " AND status = :status"
            params["status"] = status
            
        query += " ORDER BY created_at DESC"
        
        assets = conn.execute(text(query), params).fetchall()
        return [dict(row._mapping) for row in assets]
    finally:
        conn.close()

@router.post("/", dependencies=[Depends(require_permission("assets.create"))])
def create_asset(asset: AssetCreate, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        # Insert Asset
        result = conn.execute(text("""
            INSERT INTO assets (
                company_id, branch_id, name, code, type, purchase_date, 
                cost, residual_value, life_years, depreciation_method, currency
            ) VALUES (
                :cid, :bid, :name, :code, :type, :pdate, 
                :cost, :res_val, :life, :method, :currency
            ) RETURNING id
        """), {
            "cid": current_user.company_id,
            "bid": asset.branch_id,
            "name": asset.name,
            "code": asset.code,
            "type": asset.type,
            "pdate": asset.purchase_date,
            "cost": asset.cost,
            "res_val": asset.residual_value,
            "life": asset.life_years,
            "method": asset.depreciation_method,
            "currency": asset.currency
        }).fetchone()
        
        asset_id = result.id
        
        # Calculate Depreciation Schedule (Straight Line)
        if asset.life_years > 0 and asset.depreciation_method == 'straight_line':
            depreciable_amount = (_dec(asset.cost) - _dec(asset.residual_value)).quantize(_D2, ROUND_HALF_UP)
            annual_depreciation = (depreciable_amount / _dec(asset.life_years)).quantize(_D4, ROUND_HALF_UP)
            
            # Partial first year based on purchase month
            current_accumulated = Decimal('0')
            purchase_year = asset.purchase_date.year
            purchase_month = asset.purchase_date.month
            
            # Calculate first year fraction (remaining months / 12)
            remaining_months_first_year = 12 - purchase_month + 1  # Include purchase month
            first_year_fraction = _dec(remaining_months_first_year) / Decimal('12')
            first_year_amount = (annual_depreciation * first_year_fraction).quantize(_D2, ROUND_HALF_UP)
            
            total_years = asset.life_years
            # If partial first year, we need an extra year at the end for the remainder
            has_partial_first_year = purchase_month > 1
            schedule_years = total_years + (1 if has_partial_first_year else 0)
            
            for i in range(1, schedule_years + 1):
                if i == 1:
                    # First year — partial (or full if purchased in January)
                    year = purchase_year
                    amount = first_year_amount
                elif i == schedule_years and has_partial_first_year:
                    # Last year — remainder from first year's partial amount
                    year = purchase_year + i - 1
                    amount = (depreciable_amount - current_accumulated).quantize(_D2, ROUND_HALF_UP)
                else:
                    # Full intermediate years
                    year = purchase_year + i - 1
                    amount = annual_depreciation.quantize(_D2, ROUND_HALF_UP)
                
                # Safety: ensure we don't exceed depreciable amount
                if current_accumulated + amount > depreciable_amount:
                    amount = (depreciable_amount - current_accumulated).quantize(_D2, ROUND_HALF_UP)
                if amount <= 0:
                    break
                
                current_accumulated = (current_accumulated + amount).quantize(_D2, ROUND_HALF_UP)
                book_val = (_dec(asset.cost) - current_accumulated).quantize(_D2, ROUND_HALF_UP)
                
                conn.execute(text("""
                    INSERT INTO asset_depreciation_schedule (
                        asset_id, fiscal_year, amount, accumulated_amount, book_value, date
                    ) VALUES (
                        :aid, :year, :amt, :acc, :bv, :date
                    )
                """), {
                    "aid": asset_id,
                    "year": year,
                    "amt": amount,
                    "acc": current_accumulated,
                    "bv": book_val,
                    "date": date(year, 12, 31)
                })
        
        trans.commit()
        return {"id": asset_id, "message": "Asset created successfully"}
    except Exception as e:
        trans.rollback()
        logger.exception("Internal error")
        raise HTTPException(status_code=500, detail="حدث خطأ داخلي")
    finally:
        conn.close()


# ===================== B6: IFRS 16 Lease Contracts =====================

@router.get("/leases", dependencies=[Depends(require_permission("assets.view"))])
def list_lease_contracts(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """عقود الإيجار IFRS 16"""
    conn = get_db_connection(current_user.company_id)
    try:
        q = """
            SELECT lc.*, a.name as asset_name, a.code as asset_code
            FROM lease_contracts lc
            LEFT JOIN assets a ON a.id = lc.asset_id
            WHERE 1=1
        """
        params = {}
        if status:
            q += " AND lc.status = :st"
            params["st"] = status
        q += " ORDER BY lc.end_date ASC"
        rows = conn.execute(text(q), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()


@router.post("/leases", dependencies=[Depends(require_permission("assets.create"))])
def create_lease_contract(lease: dict, current_user: dict = Depends(get_current_user)):
    """إنشاء عقد إيجار IFRS 16 مع قيد محاسبي الاعتراف الأولي"""
    conn = get_db_connection(current_user.company_id)
    try:
        # Calculate right-of-use value using present value of payments
        monthly = _dec(lease.get("monthly_payment", 0)).quantize(_D2, ROUND_HALF_UP)
        total = int(_dec(lease.get("total_payments", 0)))
        rate = (_dec(lease.get("discount_rate", 5)) / Decimal('100') / Decimal('12')).quantize(_D4, ROUND_HALF_UP)
        if rate > 0 and total > 0:
            one = Decimal('1')
            rou_value = (monthly * (one - (one + rate) ** (-total)) / rate).quantize(_D2, ROUND_HALF_UP)
        else:
            rou_value = (monthly * Decimal(total)).quantize(_D2, ROUND_HALF_UP)

        result = conn.execute(text("""
            INSERT INTO lease_contracts (asset_id, description, lessor_name, lease_type,
                start_date, end_date, monthly_payment, total_payments, discount_rate,
                right_of_use_value, lease_liability, accumulated_depreciation, status)
            VALUES (:aid, :desc, :ln, :lt, :sd, :ed, :mp, :tp, :dr, :rou, :ll, 0, :st)
            RETURNING id
        """), {
            "aid": lease.get("asset_id"), "desc": lease.get("description"),
            "ln": lease.get("lessor_name"), "lt": lease.get("lease_type", "operating"),
            "sd": lease["start_date"], "ed": lease["end_date"],
            "mp": monthly, "tp": total, "dr": _dec(lease.get("discount_rate", 5)).quantize(_D4, ROUND_HALF_UP),
            "rou": rou_value, "ll": rou_value, "st": lease.get("status", "active")
        })
        lid = result.fetchone()[0]

        # IFRS 16 Initial Recognition Journal Entry:
        # Dr. Right-of-Use Asset (1600) / Cr. Lease Liability (2300)
        journal_entry_id = None
        if rou_value > 0:
            from utils.accounting import update_account_balance
            rou_acc = conn.execute(text(
                "SELECT id FROM accounts WHERE account_code IN ('1600','1610','1500') AND is_active = TRUE ORDER BY account_code LIMIT 1"
            )).fetchone()
            liability_acc = conn.execute(text(
                "SELECT id FROM accounts WHERE account_code IN ('2300','2310','2200') AND is_active = TRUE ORDER BY account_code LIMIT 1"
            )).fetchone()

            if rou_acc and liability_acc:
                check_fiscal_period_open(conn, lease["start_date"])
                
                je_lines = [
                    {
                        "account_id": rou_acc.id, "debit": rou_value, "credit": 0,
                        "description": f"أصل حق الاستخدام - {lease.get('description', '')}"
                    },
                    {
                        "account_id": liability_acc.id, "debit": 0, "credit": rou_value,
                        "description": f"التزام إيجار - {lease.get('description', '')}"
                    }
                ]
                
                from services.gl_service import create_journal_entry as gl_create_journal_entry
                from utils.accounting import get_base_currency
                base_currency = get_base_currency(conn)
                
                journal_entry_id, entry_number = gl_create_journal_entry(
                    db=conn,
                    company_id=current_user.get("company_id") if isinstance(current_user, dict) else current_user.company_id,
                    date=lease["start_date"],
                    description=f"اعتراف أولي بعقد إيجار IFRS 16 - {lease.get('description', '')} - {lease.get('lessor_name', '')}",
                    lines=je_lines,
                    user_id=current_user.get("id") if isinstance(current_user, dict) else current_user.id,
                    currency=base_currency,
                    exchange_rate=1.0,
                    source="lease_contract",
                    source_id=lid
                )

        conn.commit()
        return {
            "id": lid, "right_of_use_value": float(rou_value),
            "journal_entry_id": journal_entry_id,
            "message": "تم إنشاء عقد الإيجار بنجاح" + (" مع قيد محاسبي" if journal_entry_id else "")
        }
    except Exception as e:
        conn.rollback()
        logger.exception("Internal error")
        raise HTTPException(500, "حدث خطأ داخلي")
    finally:
        conn.close()


@router.get("/leases/{lease_id}/schedule", dependencies=[Depends(require_permission("assets.view"))])
def get_lease_schedule(lease_id: int, current_user: dict = Depends(get_current_user)):
    """جدول استهلاك عقد الإيجار"""
    conn = get_db_connection(current_user.company_id)
    try:
        row = conn.execute(text("SELECT * FROM lease_contracts WHERE id = :id"),
                           {"id": lease_id}).fetchone()
        if not row:
            raise HTTPException(404, "Lease not found")
        lc = dict(row._mapping)
        monthly = _dec(lc.get("monthly_payment", 0)).quantize(_D2, ROUND_HALF_UP)
        total = int(lc.get("total_payments", 0))
        rate = (_dec(lc.get("discount_rate", 5)) / Decimal('100') / Decimal('12')).quantize(_D4, ROUND_HALF_UP)
        balance = _dec(lc.get("lease_liability", 0)).quantize(_D2, ROUND_HALF_UP)
        schedule = []
        for i in range(1, total + 1):
            interest = (balance * rate).quantize(_D2, ROUND_HALF_UP)
            principal = (monthly - interest).quantize(_D2, ROUND_HALF_UP)
            balance = (balance - principal).quantize(_D2, ROUND_HALF_UP)
            schedule.append({
                "period": i,
                "payment": float(monthly),
                "interest": float(interest),
                "principal": float(principal),
                "balance": float(max(balance, Decimal('0')))
            })
        return {"lease": lc, "schedule": schedule}
    finally:
        conn.close()


@router.get("/{asset_id}", dependencies=[Depends(require_permission("assets.view"))])
def get_asset(asset_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        asset = conn.execute(text("SELECT * FROM assets WHERE id = :id"), {"id": asset_id}).fetchone()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
            
        schedule = conn.execute(text("""
            SELECT * FROM asset_depreciation_schedule 
            WHERE asset_id = :id 
            ORDER BY fiscal_year ASC
        """), {"id": asset_id}).fetchall()
        
        return {
            "asset": dict(asset._mapping),
            "schedule": [dict(row._mapping) for row in schedule]
        }
    finally:
        conn.close()

@router.put("/{asset_id}", dependencies=[Depends(require_permission("assets.manage"))])
def update_asset(asset_id: int, data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Update an existing asset (only if not disposed)"""
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        existing = conn.execute(text("SELECT * FROM assets WHERE id = :id"), {"id": asset_id}).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="الأصل غير موجود")
        if existing.status == 'disposed':
            raise HTTPException(status_code=400, detail="لا يمكن تعديل أصل مستبعد")
        
        allowed_fields = ['name', 'code', 'type', 'cost', 'residual_value', 'life_years', 
                         'location', 'branch_id', 'notes', 'purchase_date']
        updates = []
        params = {"id": asset_id}
        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = :{field}")
                params[field] = data[field]
        
        if updates:
            conn.execute(text(f"UPDATE assets SET {', '.join(updates)} WHERE id = :id"), params)
            trans.commit()
        
        return {"message": "تم تحديث الأصل بنجاح"}
    except HTTPException:
        trans.rollback()
        raise
    except Exception as e:
        trans.rollback()
        logger.exception("Internal error")
        raise HTTPException(status_code=500, detail="حدث خطأ داخلي")
    finally:
        conn.close()

@router.post("/{asset_id}/depreciate/{schedule_id}", dependencies=[Depends(require_permission("assets.manage"))])
def post_depreciation(asset_id: int, schedule_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        from utils.accounting import get_base_currency
        base_currency = get_base_currency(conn)
        # Verify schedule item
        item = conn.execute(text("""
            SELECT * FROM asset_depreciation_schedule 
            WHERE id = :sid AND asset_id = :aid AND posted = FALSE
        """), {"sid": schedule_id, "aid": asset_id}).fetchone()
        
        if not item:
            raise HTTPException(status_code=400, detail="Schedule item not found or already posted")
            
        # Get Asset info for name/code
        asset = conn.execute(text("SELECT * FROM assets WHERE id = :id"), {"id": asset_id}).fetchone()
            
        # Create Journal Entry
        # Dr Depreciation Expense (5210)
        # Cr Accumulated Depreciation (1519)
        # We need to find these Account IDs. For now assuming they exist or using placeholders.
        # Ideally, we should fetch them from chart of accounts based on code.

        check_fiscal_period_open(conn, item.date)
        # Use Dynamic Mappings for Depreciation
        exp_acc_id = get_mapped_account_id(conn, "acc_map_depr_exp")
        acc_depr_id = get_mapped_account_id(conn, "acc_map_acc_depr")
        
        if not exp_acc_id or not acc_depr_id:
             raise HTTPException(status_code=400, detail="Depreciation accounts (mapped roles: acc_map_depr_exp, acc_map_acc_depr) not found.")

        # Create Header
        je_lines = [
            {
                "account_id": exp_acc_id, "debit": _dec(item.amount).quantize(_D2, ROUND_HALF_UP), "credit": 0,
                "description": "Depreciation Expense"
            },
            {
                "account_id": acc_depr_id, "debit": 0, "credit": _dec(item.amount).quantize(_D2, ROUND_HALF_UP),
                "description": "Accumulated Depreciation"
            }
        ]
        
        from services.gl_service import create_journal_entry as gl_create_journal_entry
        je_id, entry_number = gl_create_journal_entry(
            db=conn,
            company_id=current_user.get("company_id") if isinstance(current_user, dict) else current_user.company_id,
            date=item.date,
            description=f"Depreciation for asset {asset.name} ({asset.code}) - {item.fiscal_year}",
            lines=je_lines,
            user_id=current_user.get("username") if isinstance(current_user, dict) else current_user.username,
            branch_id=asset.branch_id,
            reference=f"DEPR-{asset.code}-{item.fiscal_year}",
            currency=asset.currency or base_currency,
            exchange_rate=1.0,
            source="asset_depreciation",
            source_id=schedule_id
        )

        # Update Account Balances handled by gl_service

        # Update Schedule
        conn.execute(text("UPDATE asset_depreciation_schedule SET posted = TRUE, journal_entry_id = :jid WHERE id = :sid"), 
                     {"jid": je_id, "sid": schedule_id})
                     
        trans.commit()
        return {"message": "Depreciation posted successfully", "journal_entry_id": je_id}
        
    except Exception as e:
        trans.rollback()
        logger.exception("Internal error")
        raise HTTPException(status_code=500, detail="حدث خطأ داخلي")
    finally:
        conn.close()
@router.post("/{asset_id}/dispose", dependencies=[Depends(require_permission("assets.manage"))])
def dispose_asset(asset_id: int, disposal: AssetDisposal, current_user: dict = Depends(get_current_user)):
    """استبعاد أصل ثابت مع معثرات محاسبية (إهلاك متراكم، ربح/خسارة)"""
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        from utils.accounting import get_base_currency
        base_currency = get_base_currency(conn)
        # 1. Get Asset & Accumulated Depreciation
        asset = conn.execute(text("SELECT * FROM assets WHERE id = :id FOR UPDATE"), {"id": asset_id}).fetchone()
        if not asset or asset.status == 'disposed':
            raise HTTPException(status_code=400, detail="الأصل غير موجود أو تم استبعاده مسبقاً")
            
        acc_depr_recorded = conn.execute(text("""
            SELECT COALESCE(SUM(amount), 0) FROM asset_depreciation_schedule 
            WHERE asset_id = :id AND posted = TRUE
        """), {"id": asset_id}).scalar()
        
        # 2. Update Asset Status
        conn.execute(text("UPDATE assets SET status = 'disposed', updated_at = NOW() WHERE id = :id"), {"id": asset_id})
        
        # 3. GL Entry (Automated)
        acc_fixed_assets = get_mapped_account_id(conn, "acc_map_fixed_assets")
        acc_acc_depr = get_mapped_account_id(conn, "acc_map_acc_depr")
        acc_gain = get_mapped_account_id(conn, "acc_map_asset_gain")
        acc_loss = get_mapped_account_id(conn, "acc_map_asset_loss")
        acc_cash = get_mapped_account_id(conn, "acc_map_cash_main")
        if disposal.payment_method == 'bank':
            acc_cash = get_mapped_account_id(conn, "acc_map_bank")
            
        book_value = (_dec(asset.cost) - _dec(acc_depr_recorded)).quantize(_D2, ROUND_HALF_UP)
        gain_loss = (_dec(disposal.disposal_price) - book_value).quantize(_D2, ROUND_HALF_UP)
        
        # Use UUID OR simple generation
        import uuid
        ts = datetime.now().strftime('%Y%m%d%H%M%S')
        je_num = f"JE-ASSET-DISP-{asset_id}-{ts}"
        
        # Check if JE exists for this asset disposal (to avoid double posting)
        exists = conn.execute(text("SELECT 1 FROM journal_entries WHERE reference = :ref"), {"ref": f"ASSET-DISP-{asset_id}"}).fetchone()
        if exists:
             raise HTTPException(status_code=400, detail="تم ترحيل قيد استبعاد لهذا الأصل مسبقاً")

        check_fiscal_period_open(conn, disposal.disposal_date)
        
        je_lines = []
        if disposal.disposal_price > 0:
            je_lines.append({
                "account_id": acc_cash, "debit": _dec(disposal.disposal_price), "credit": 0,
                "description": 'ثمن بيع أصل'
            })
            
        if acc_depr_recorded > 0:
            je_lines.append({
                "account_id": acc_acc_depr, "debit": _dec(acc_depr_recorded), "credit": 0,
                "description": 'استبعاد إهلاك متراكم'
            })
            
        je_lines.append({
            "account_id": acc_fixed_assets, "debit": 0, "credit": _dec(asset.cost),
            "description": 'استبعاد تكلفة أصل تاريخية'
        })
        
        if gain_loss > 0:
            je_lines.append({
                "account_id": acc_gain, "debit": 0, "credit": _dec(gain_loss),
                "description": 'أرباح بيع أصول'
            })
        elif gain_loss < 0:
            je_lines.append({
                "account_id": acc_loss, "debit": abs(_dec(gain_loss)), "credit": 0,
                "description": 'خسائر بيع أصول'
            })
            
        from services.gl_service import create_journal_entry as gl_create_journal_entry
        je_id, je_num = gl_create_journal_entry(
            db=conn,
            company_id=current_user.get("company_id") if isinstance(current_user, dict) else current_user.company_id,
            date=disposal.disposal_date,
            description=f"استبعاد الأصل {asset.name} ({asset.code})",
            lines=je_lines,
            user_id=current_user.get("id") if isinstance(current_user, dict) else current_user.id,
            branch_id=asset.branch_id,
            reference=f"ASSET-DISP-{asset_id}",
            currency=asset.currency or base_currency,
            exchange_rate=Decimal("1"),
            source="asset_disposal",
            source_id=asset_id
        )
                         
        trans.commit()
        return {"id": asset_id, "status": "disposed", "journal_entry": je_num}
    except HTTPException:
        trans.rollback()
        raise
    except Exception as e:
        trans.rollback()
        logger.exception("Operation failed")
        logger.exception("Internal error")
        raise HTTPException(status_code=500, detail="حدث خطأ داخلي")
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════
# GL-003: Asset Transfer Between Branches
# ═══════════════════════════════════════════════════════════

class AssetTransfer(BaseModel):
    to_branch_id: int
    notes: Optional[str] = None

@router.post("/{asset_id}/transfer", dependencies=[Depends(require_permission("assets.manage"))])
def transfer_asset(asset_id: int, transfer: AssetTransfer, current_user: dict = Depends(get_current_user)):
    """نقل أصل بين فروع مع قيد محاسبي تلقائي عبر الحساب البيني"""
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        from utils.accounting import get_base_currency, update_account_balance

        asset = conn.execute(text("SELECT * FROM assets WHERE id = :id FOR UPDATE"), {"id": asset_id}).fetchone()
        if not asset:
            raise HTTPException(status_code=404, detail="الأصل غير موجود")
        if asset.status == 'disposed':
            raise HTTPException(status_code=400, detail="لا يمكن نقل أصل مستبعد")

        from_branch_id = asset.branch_id
        if from_branch_id == transfer.to_branch_id:
            raise HTTPException(status_code=400, detail="الفرع المصدر والوجهة متطابقان")

        base_currency = get_base_currency(conn)
        acc_fixed = get_mapped_account_id(conn, "acc_map_fixed_assets")
        acc_inter = get_mapped_account_id(conn, "acc_map_intercompany")
        if not acc_inter:
            raise HTTPException(status_code=400, detail="لم يتم تعيين حساب بين الفروع (acc_map_intercompany)")

        cost = _dec(asset.cost).quantize(_D2, ROUND_HALF_UP)

        check_fiscal_period_open(conn, date.today())
        # Create 2 JEs — one for sending branch, one for receiving
        for je_type, branch_id, lines in [
            ("SEND", from_branch_id, [
                (acc_inter, cost, 0, f"نقل أصل #{asset_id} إلى فرع {transfer.to_branch_id}"),
                (acc_fixed, 0, cost, f"إخراج أصل #{asset_id}")
            ]),
            ("RECV", transfer.to_branch_id, [
                (acc_fixed, cost, 0, f"استقبال أصل #{asset_id}"),
                (acc_inter, 0, cost, f"نقل أصل #{asset_id} من فرع {from_branch_id}")
            ]),
        ]:
            je_lines_formatted = [
                {
                    "account_id": row[0],
                    "debit": _dec(row[1]).quantize(_D2, ROUND_HALF_UP),
                    "credit": _dec(row[2]).quantize(_D2, ROUND_HALF_UP),
                    "description": row[3]
                }
                for row in lines
            ]
            
            from services.gl_service import create_journal_entry as gl_create_journal_entry
            from utils.accounting import get_base_currency
            
            base_currency = get_base_currency(conn)
            
            je_id, je_num = gl_create_journal_entry(
                db=conn,
                company_id=current_user.get("company_id") if isinstance(current_user, dict) else current_user.company_id,
                date=date.today(),
                description=f"نقل أصل #{asset_id} — {je_type}",
                lines=je_lines_formatted,
                user_id=current_user.get("id") if isinstance(current_user, dict) else current_user.id,
                branch_id=branch_id,
                reference=f"ASSET-XFER-{asset_id}-{je_type}",
                currency=base_currency,
                exchange_rate=1.0,
                source="asset_transfer",
                source_id=asset_id
            )

        # Update asset branch
        conn.execute(text("UPDATE assets SET branch_id = :br, updated_at = NOW() WHERE id = :id"),
                     {"br": transfer.to_branch_id, "id": asset_id})
        trans.commit()
        return {"success": True, "asset_id": asset_id, "from_branch": from_branch_id, "to_branch": transfer.to_branch_id}
    except HTTPException:
        trans.rollback()
        raise
    except Exception as e:
        trans.rollback()
        logger.exception("Internal error")
        raise HTTPException(status_code=500, detail="حدث خطأ داخلي")
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════
# GL-007: Asset Revaluation
# ═══════════════════════════════════════════════════════════

class AssetRevaluation(BaseModel):
    new_value: float
    reason: Optional[str] = "إعادة تقييم"

@router.post("/{asset_id}/revalue", dependencies=[Depends(require_permission("assets.manage"))])
def revalue_asset(asset_id: int, reval: AssetRevaluation, current_user: dict = Depends(get_current_user)):
    """إعادة تقييم أصل ثابت — الزيادة تسجل في احتياطي إعادة التقييم"""
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        from utils.accounting import get_base_currency, update_account_balance

        asset = conn.execute(text("SELECT * FROM assets WHERE id = :id FOR UPDATE"), {"id": asset_id}).fetchone()
        if not asset or asset.status == 'disposed':
            raise HTTPException(status_code=400, detail="الأصل غير موجود أو مستبعد")

        acc_depr_recorded = _dec(conn.execute(text("""
            SELECT COALESCE(SUM(amount), 0) FROM asset_depreciation_schedule WHERE asset_id = :id AND posted = TRUE
        """), {"id": asset_id}).scalar())

        old_book = (_dec(asset.cost) - acc_depr_recorded).quantize(_D2, ROUND_HALF_UP)
        diff = (_dec(reval.new_value) - old_book).quantize(_D2, ROUND_HALF_UP)

        if diff.copy_abs() < _D2:
            return {"success": True, "message": "لا يوجد فرق في القيمة"}

        base_currency = get_base_currency(conn)
        acc_fixed = get_mapped_account_id(conn, "acc_map_fixed_assets")
        acc_reval = get_mapped_account_id(conn, "acc_map_revaluation_reserve")
        acc_loss = get_mapped_account_id(conn, "acc_map_asset_loss")
        if diff > 0 and not acc_reval:
            raise HTTPException(status_code=400, detail="لم يتم تعيين حساب احتياطي إعادة التقييم في الإعدادات")
        if diff < 0 and not acc_loss:
            raise HTTPException(status_code=400, detail="لم يتم تعيين حساب خسائر الأصول في الإعدادات")

        check_fiscal_period_open(conn, date.today())
        check_fiscal_period_open(conn, date.today())
        
        je_lines = []
        if diff > 0:
            je_lines.extend([
                {"account_id": acc_fixed, "debit": abs(diff), "credit": 0, "description": f"زيادة قيمة أصل #{asset_id}"},
                {"account_id": acc_reval, "debit": 0, "credit": abs(diff), "description": "احتياطي إعادة تقييم"}
            ])
        else:
            je_lines.extend([
                {"account_id": acc_loss, "debit": abs(diff), "credit": 0, "description": f"انخفاض قيمة أصل #{asset_id}"},
                {"account_id": acc_fixed, "debit": 0, "credit": abs(diff), "description": f"تخفيض أصل #{asset_id}"}
            ])
            
        from services.gl_service import create_journal_entry as gl_create_journal_entry
        je_id, je_num = gl_create_journal_entry(
            db=conn,
            company_id=current_user.get("company_id") if isinstance(current_user, dict) else current_user.company_id,
            date=date.today(),
            description=reval.reason or "إعادة تقييم أصل",
            lines=je_lines,
            user_id=current_user.get("id") if isinstance(current_user, dict) else current_user.id,
            branch_id=asset.branch_id,
            reference=f"ASSET-REVAL-{asset_id}",
            currency=base_currency,
            exchange_rate=Decimal("1"),
            source="asset_revaluation",
            source_id=asset_id
        )

        # Update asset cost
        conn.execute(text("UPDATE assets SET cost = cost + :diff, updated_at = NOW() WHERE id = :id"),
                     {"diff": diff, "id": asset_id})

        trans.commit()
        return {
            "success": True, "asset_id": asset_id,
            "old_book_value": float(old_book.quantize(_D2, ROUND_HALF_UP)), "new_value": float(_dec(reval.new_value).quantize(_D2, ROUND_HALF_UP)),
            "difference": float(diff.quantize(_D2, ROUND_HALF_UP)), "journal_entry": je_num,
        }
    except HTTPException:
        trans.rollback()
        raise
    except Exception as e:
        trans.rollback()
        logger.exception("Internal error")
        raise HTTPException(status_code=500, detail="حدث خطأ داخلي")
    finally:
        conn.close()


# =====================================================
# 8.14 ASSETS IMPROVEMENTS
# =====================================================

# ---------- ASSET-001: Additional Depreciation Methods ----------

@router.post("/{asset_id}/depreciation/declining-balance", dependencies=[Depends(require_permission("assets.create"))])
def calc_declining_balance(asset_id: int, data: dict = {}, current_user: dict = Depends(get_current_user)):
    """Calculate Declining Balance depreciation schedule."""
    conn = get_db_connection(current_user.company_id)
    try:
        asset = conn.execute(text("SELECT * FROM assets WHERE id = :id"), {"id": asset_id}).fetchone()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        cost = _dec(asset.cost)
        residual = _dec(asset.residual_value or 0)
        life = int(asset.life_years or 5)
        rate = _dec(data.get("rate", Decimal('2') / _dec(life)))  # Double declining by default
        schedule = []
        book_value = cost
        for year in range(1, life + 1):
            dep = (book_value * rate).quantize(_D2, ROUND_HALF_UP)
            if book_value - dep < residual:
                dep = (book_value - residual).quantize(_D2, ROUND_HALF_UP)
            book_value -= dep
            schedule.append({"year": year, "depreciation": float(dep), "book_value": float(book_value.quantize(_D2, ROUND_HALF_UP))})
            if book_value <= residual:
                break
        return {"asset_id": asset_id, "method": "declining_balance", "rate": float(rate), "schedule": schedule}
    finally:
        conn.close()


@router.post("/{asset_id}/depreciation/units-of-production", dependencies=[Depends(require_permission("assets.create"))])
def calc_units_of_production(asset_id: int, data: dict, current_user: dict = Depends(get_current_user)):
    """Depreciation based on units produced."""
    conn = get_db_connection(current_user.company_id)
    try:
        asset = conn.execute(text("SELECT * FROM assets WHERE id = :id"), {"id": asset_id}).fetchone()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        cost = _dec(asset.cost)
        residual = _dec(asset.residual_value or 0)
        total_units = _dec(data.get("total_units") or asset.total_units or 1)
        units_used = _dec(data.get("units_used", 0))
        dep_per_unit = (cost - residual) / total_units
        depreciation = (dep_per_unit * units_used).quantize(_D2, ROUND_HALF_UP)
        # Update used units
        conn.execute(text("UPDATE assets SET used_units = COALESCE(used_units,0) + :u WHERE id = :id"),
                     {"u": units_used, "id": asset_id})
        conn.commit()
        return {
            "asset_id": asset_id, "method": "units_of_production",
            "dep_per_unit": float(dep_per_unit.quantize(_D4, ROUND_HALF_UP)),
            "units_used": float(units_used), "depreciation": float(depreciation),
        }
    finally:
        conn.close()


@router.post("/{asset_id}/depreciation/sum-of-years", dependencies=[Depends(require_permission("assets.create"))])
def calc_sum_of_years_digits(asset_id: int, current_user: dict = Depends(get_current_user)):
    """Sum of Years' Digits depreciation schedule."""
    conn = get_db_connection(current_user.company_id)
    try:
        asset = conn.execute(text("SELECT * FROM assets WHERE id = :id"), {"id": asset_id}).fetchone()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        cost = _dec(asset.cost)
        residual = _dec(asset.residual_value or 0)
        life = int(asset.life_years or 5)
        depreciable = cost - residual
        syd = _dec(life * (life + 1)) / Decimal('2')
        schedule = []
        for year in range(1, life + 1):
            fraction = _dec(life - year + 1) / syd
            dep = (depreciable * fraction).quantize(_D2, ROUND_HALF_UP)
            schedule.append({"year": year, "fraction": float(fraction.quantize(_D4, ROUND_HALF_UP)), "depreciation": float(dep)})
        return {"asset_id": asset_id, "method": "sum_of_years_digits", "schedule": schedule}
    finally:
        conn.close()




# ---------- ASSET-004: Insurance & Maintenance ----------

@router.get("/{asset_id}/insurance", dependencies=[Depends(require_permission("assets.view"))])
def list_asset_insurance(asset_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        rows = conn.execute(text("SELECT * FROM asset_insurance WHERE asset_id = :id ORDER BY end_date DESC"),
                            {"id": asset_id}).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()


@router.post("/{asset_id}/insurance", dependencies=[Depends(require_permission("assets.create"))])
def add_insurance(asset_id: int, data: dict, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        result = conn.execute(text("""
            INSERT INTO asset_insurance (asset_id, policy_number, insurer, coverage_type,
                premium_amount, coverage_amount, start_date, end_date, notes)
            VALUES (:aid, :pol, :ins, :cov, :prem, :covamt, :start, :end, :notes)
            RETURNING *
        """), {
            "aid": asset_id, "pol": data.get("policy_number"), "ins": data.get("insurer"),
            "cov": data.get("coverage_type"), "prem": data.get("premium_amount", 0),
            "covamt": data.get("coverage_amount", 0),
            "start": data.get("start_date"), "end": data.get("end_date"),
            "notes": data.get("notes"),
        }).fetchone()
        conn.commit()
        return dict(result._mapping)
    except Exception as e:
        conn.rollback()
        logger.exception("Internal error")
        raise HTTPException(status_code=500, detail="حدث خطأ داخلي")
    finally:
        conn.close()


@router.get("/{asset_id}/maintenance", dependencies=[Depends(require_permission("assets.view"))])
def list_asset_maintenance(asset_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        rows = conn.execute(text("SELECT * FROM asset_maintenance WHERE asset_id = :id ORDER BY scheduled_date DESC"),
                            {"id": asset_id}).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()


@router.post("/{asset_id}/maintenance", dependencies=[Depends(require_permission("assets.create"))])
def add_maintenance(asset_id: int, data: dict, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        result = conn.execute(text("""
            INSERT INTO asset_maintenance (asset_id, maintenance_type, description,
                scheduled_date, cost, vendor, status, notes, created_by)
            VALUES (:aid, :type, :desc, :date, :cost, :vendor, 'scheduled', :notes, :uid)
            RETURNING *
        """), {
            "aid": asset_id, "type": data.get("maintenance_type", "preventive"),
            "desc": data.get("description"), "date": data.get("scheduled_date"),
            "cost": data.get("cost", 0), "vendor": data.get("vendor"),
            "notes": data.get("notes"), "uid": current_user.id,
        }).fetchone()
        conn.execute(text("UPDATE assets SET last_maintenance_date = :d WHERE id = :id"),
                     {"d": data.get("scheduled_date"), "id": asset_id})
        conn.commit()
        return dict(result._mapping)
    except Exception as e:
        conn.rollback()
        logger.exception("Internal error")
        raise HTTPException(status_code=500, detail="حدث خطأ داخلي")
    finally:
        conn.close()




# ---------- ASSET-005: QR / Barcode ----------

@router.put("/{asset_id}/qr", dependencies=[Depends(require_permission("assets.create"))])
def update_asset_qr(asset_id: int, data: dict, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        conn.execute(text("UPDATE assets SET qr_code = :qr, barcode = :bc WHERE id = :id"),
                     {"qr": data.get("qr_code"), "bc": data.get("barcode"), "id": asset_id})
        conn.commit()
        return {"message": "QR/Barcode updated"}
    finally:
        conn.close()


@router.get("/{asset_id}/qr", dependencies=[Depends(require_permission("assets.view"))])
def get_asset_qr(asset_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        row = conn.execute(text("SELECT id, name, code, qr_code, barcode FROM assets WHERE id = :id"),
                           {"id": asset_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Asset not found")
        return dict(row._mapping)
    finally:
        conn.close()


# ===================== B6: IAS 36 Impairment Testing =====================

@router.get("/{asset_id}/impairments", dependencies=[Depends(require_permission("assets.view"))])
def list_asset_impairments(asset_id: int, current_user: dict = Depends(get_current_user)):
    """سجل اختبارات الانخفاض"""
    conn = get_db_connection(current_user.company_id)
    try:
        rows = conn.execute(text("""
            SELECT * FROM asset_impairments WHERE asset_id = :aid ORDER BY test_date DESC
        """), {"aid": asset_id}).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()


@router.post("/{asset_id}/impairment-test", dependencies=[Depends(require_permission("assets.create"))])
def run_impairment_test(asset_id: int, test_data: dict, current_user: dict = Depends(get_current_user)):
    """إجراء اختبار انخفاض القيمة IAS 36 مع قيد محاسبي تلقائي"""
    conn = get_db_connection(current_user.company_id)
    try:
        asset = conn.execute(text("SELECT * FROM assets WHERE id = :id"), {"id": asset_id}).fetchone()
        if not asset:
            raise HTTPException(404, "Asset not found")
        asset = dict(asset._mapping)

        carrying = _dec(asset.get("current_value") or asset.get("purchase_cost", 0)).quantize(_D2, ROUND_HALF_UP)
        recoverable = _dec(test_data.get("recoverable_amount", 0)).quantize(_D2, ROUND_HALF_UP)
        impairment_loss = max(carrying - recoverable, Decimal('0')).quantize(_D2, ROUND_HALF_UP)

        result = conn.execute(text("""
            INSERT INTO asset_impairments (asset_id, test_date, carrying_amount,
                recoverable_amount, impairment_loss, reason)
            VALUES (:aid, :td, :ca, :ra, :il, :r)
            RETURNING id
        """), {
            "aid": asset_id, "td": test_data.get("test_date", str(date.today())),
            "ca": carrying, "ra": recoverable, "il": impairment_loss,
            "r": test_data.get("reason") or test_data.get("notes")
        })
        imp_id = result.fetchone()[0]

        journal_entry_id = None
        if impairment_loss > 0:
            new_value = recoverable
            conn.execute(text("UPDATE assets SET current_value = :v WHERE id = :id"),
                         {"v": new_value, "id": asset_id})

            # Create journal entry: Dr. Impairment Loss (6800) / Cr. Accumulated Impairment (1699)
            from utils.accounting import update_account_balance
            imp_loss_acc = conn.execute(text(
                "SELECT id FROM accounts WHERE account_code IN ('6800','6810','5800') AND is_active = TRUE ORDER BY account_code LIMIT 1"
            )).fetchone()
            acc_imp_acc = conn.execute(text(
                "SELECT id FROM accounts WHERE account_code IN ('1699','1690','1680') AND is_active = TRUE ORDER BY account_code LIMIT 1"
            )).fetchone()

            if imp_loss_acc and acc_imp_acc:
                check_fiscal_period_open(conn, date.today())
                
                je_lines = [
                    {
                        "account_id": imp_loss_acc.id, "debit": impairment_loss, "credit": 0,
                        "description": f"خسارة انخفاض قيمة - {asset.get('name', '')}"
                    },
                    {
                        "account_id": acc_imp_acc.id, "debit": 0, "credit": impairment_loss,
                        "description": f"مجمع انخفاض قيمة - {asset.get('name', '')}"
                    }
                ]
                
                from services.gl_service import create_journal_entry as gl_create_journal_entry
                from utils.accounting import get_base_currency
                
                je_id, entry_number = gl_create_journal_entry(
                    db=conn,
                    company_id=current_user.get("company_id") if isinstance(current_user, dict) else current_user.company_id,
                    date=date.today(),
                    description=f"خسارة انخفاض قيمة الأصل: {asset.get('name', '')} (IAS 36)",
                    lines=je_lines,
                    user_id=current_user.get("id") if isinstance(current_user, dict) else current_user.id,
                    currency=get_base_currency(conn),
                    exchange_rate=1.0,
                    source="asset_impairment",
                    source_id=imp_id
                )

        conn.commit()
        return {
            "id": imp_id,
            "carrying_amount": carrying,
            "recoverable_amount": recoverable,
            "impairment_loss": impairment_loss,
            "impaired": impairment_loss > 0,
            "journal_entry_id": journal_entry_id,
            "message": "تم إجراء اختبار الانخفاض" + (" - تم تسجيل خسارة انخفاض وقيد محاسبي" if impairment_loss > 0 else " - لا يوجد انخفاض")
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.exception("Internal error")
        raise HTTPException(500, "حدث خطأ داخلي")
    finally:
        conn.close()
