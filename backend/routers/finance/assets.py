
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import date
from database import get_db_connection
from routers.auth import get_current_user
from pydantic import BaseModel
from datetime import datetime
from utils.permissions import require_permission, validate_branch_access
from utils.accounting import get_mapped_account_id
from schemas.assets import AssetCreate, AssetUpdate, AssetDisposal

router = APIRouter(prefix="/assets", tags=["الأصول الثابتة"])

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
            depreciable_amount = asset.cost - asset.residual_value
            annual_depreciation = depreciable_amount / asset.life_years
            
            # Partial first year based on purchase month
            current_accumulated = 0
            purchase_year = asset.purchase_date.year
            purchase_month = asset.purchase_date.month
            
            # Calculate first year fraction (remaining months / 12)
            remaining_months_first_year = 12 - purchase_month + 1  # Include purchase month
            first_year_fraction = remaining_months_first_year / 12
            first_year_amount = round(annual_depreciation * first_year_fraction, 2)
            
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
                    amount = round(depreciable_amount - current_accumulated, 2)
                else:
                    # Full intermediate years
                    year = purchase_year + i - 1
                    amount = annual_depreciation
                
                # Safety: ensure we don't exceed depreciable amount
                if current_accumulated + amount > depreciable_amount:
                    amount = round(depreciable_amount - current_accumulated, 2)
                if amount <= 0:
                    break
                
                current_accumulated = round(current_accumulated + amount, 2)
                book_val = round(asset.cost - current_accumulated, 2)
                
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
        raise HTTPException(status_code=500, detail=str(e))
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
        raise HTTPException(status_code=500, detail=str(e))
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
        
        # Use Dynamic Mappings for Depreciation
        exp_acc_id = get_mapped_account_id(conn, "acc_map_depr_exp")
        acc_depr_id = get_mapped_account_id(conn, "acc_map_acc_depr")
        
        if not exp_acc_id or not acc_depr_id:
             raise HTTPException(status_code=400, detail="Depreciation accounts (mapped roles: acc_map_depr_exp, acc_map_acc_depr) not found.")

        # Create Header
        je_res = conn.execute(text("""
            INSERT INTO journal_entries (
                company_id, branch_id, entry_date, reference, description, status, created_by,
                currency, exchange_rate
            ) VALUES (
                :cid, :bid, :date, :ref, :desc, 'posted', :user, :curr, :rate
            ) RETURNING id
        """), {
            "cid": current_user.company_id,
            "bid": asset.branch_id,
            "date": item.date,
            "ref": f"DEPR-{asset.code}-{item.fiscal_year}",
            "desc": f"Depreciation for asset {asset.name} ({asset.code}) - {item.fiscal_year}",
            "user": current_user.username,
            "curr": asset.currency or base_currency,
            "rate": 1.0
        }).fetchone()
        je_id = je_res.id
        
        # DB Lines Created
        # Debit Expense
        conn.execute(text("""
            INSERT INTO journal_lines (
                journal_entry_id, account_id, description, debit, credit,
                amount_currency, currency
            )
            VALUES (:jid, :aid, :desc, :dr, 0, :amt_curr, :curr)
        """), {"jid": je_id, "aid": exp_acc_id, "desc": "Depreciation Expense", "dr": item.amount, "amt_curr": item.amount, "curr": asset.currency or base_currency})
        
        # Credit Accumulated Depr
        conn.execute(text("""
            INSERT INTO journal_lines (
                journal_entry_id, account_id, description, debit, credit,
                amount_currency, currency
            )
            VALUES (:jid, :aid, :desc, 0, :cr, :amt_curr, :curr)
        """), {"jid": je_id, "aid": acc_depr_id, "desc": "Accumulated Depreciation", "cr": item.amount, "amt_curr": item.amount, "curr": asset.currency or base_currency})

        # Update Account Balances
        from utils.accounting import update_account_balance
        update_account_balance(conn, account_id=exp_acc_id, debit_base=float(item.amount), credit_base=0)
        update_account_balance(conn, account_id=acc_depr_id, debit_base=0, credit_base=float(item.amount))

        # Update Schedule
        conn.execute(text("UPDATE asset_depreciation_schedule SET posted = TRUE, journal_entry_id = :jid WHERE id = :sid"), 
                     {"jid": je_id, "sid": schedule_id})
                     
        trans.commit()
        return {"message": "Depreciation posted successfully", "journal_entry_id": je_id}
        
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=500, detail=str(e))
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
            
        book_value = float(asset.cost) - float(acc_depr_recorded)
        gain_loss = float(disposal.disposal_price) - book_value
        
        # Use UUID OR simple generation
        import uuid
        ts = datetime.now().strftime('%Y%m%d%H%M%S')
        je_num = f"JE-ASSET-DISP-{asset_id}-{ts}"
        
        # Check if JE exists for this asset disposal (to avoid double posting)
        exists = conn.execute(text("SELECT 1 FROM journal_entries WHERE reference = :ref"), {"ref": f"ASSET-DISP-{asset_id}"}).fetchone()
        if exists:
             raise HTTPException(status_code=400, detail="تم ترحيل قيد استبعاد لهذا الأصل مسبقاً")

        je_id = conn.execute(text("""
            INSERT INTO journal_entries (
                entry_number, entry_date, reference, description, status, created_by, branch_id,
                currency, exchange_rate
            )
            VALUES (:num, :date, :ref, :desc, 'posted', :uid, :bid, :curr, :rate) RETURNING id
        """), {
            "num": je_num, "date": disposal.disposal_date, "ref": f"ASSET-DISP-{asset_id}",
            "desc": f"استبعاد الأصل {asset.name} ({asset.code})", 
            "uid": current_user.get("id") if isinstance(current_user, dict) else current_user.id, 
            "bid": asset.branch_id,
            "curr": asset.currency or base_currency,
            "rate": 1.0
        }).scalar()
        
        # A. Debit Cash (Sales Price)
        if disposal.disposal_price > 0:
            conn.execute(text("""
                INSERT INTO journal_lines (
                    journal_entry_id, account_id, debit, credit, description,
                    amount_currency, currency
                ) VALUES (:jid, :acc, :amt, 0, :desc, :amt, :curr)
            """), {"jid": je_id, "acc": acc_cash, "amt": disposal.disposal_price, "desc": 'ثمن بيع أصل', "curr": asset.currency or base_currency})
                         
        # B. Debit Accumulated Depreciation
        if acc_depr_recorded > 0:
            conn.execute(text("""
                INSERT INTO journal_lines (
                    journal_entry_id, account_id, debit, credit, description,
                    amount_currency, currency
                ) VALUES (:jid, :acc, :amt, 0, :desc, :amt, :curr)
            """), {"jid": je_id, "acc": acc_acc_depr, "amt": acc_depr_recorded, "desc": 'استبعاد إهلاك متراكم', "curr": asset.currency or base_currency})
                         
        # C. Credit Fixed Asset (Original Cost)
        conn.execute(text("""
            INSERT INTO journal_lines (
                journal_entry_id, account_id, debit, credit, description,
                amount_currency, currency
            ) VALUES (:jid, :acc, 0, :amt, :desc, :amt, :curr)
        """), {"jid": je_id, "acc": acc_fixed_assets, "amt": asset.cost, "desc": 'استبعاد تكلفة أصل تاريخية', "curr": asset.currency or base_currency})
                     
        # D. Gain or Loss
        if gain_loss > 0:
            # Credit Gain (Revenue)
            conn.execute(text("""
                INSERT INTO journal_lines (
                    journal_entry_id, account_id, debit, credit, description,
                    amount_currency, currency
                ) VALUES (:jid, :acc, 0, :amt, :desc, :amt, :curr)
            """), {"jid": je_id, "acc": acc_gain, "amt": gain_loss, "desc": 'أرباح بيع أصول', "curr": asset.currency or base_currency})
        elif gain_loss < 0:
            # Debit Loss (Expense)
            conn.execute(text("""
                INSERT INTO journal_lines (
                    journal_entry_id, account_id, debit, credit, description,
                    amount_currency, currency
                ) VALUES (:jid, :acc, :amt, 0, :desc, :amt, :curr)
            """), {"jid": je_id, "acc": acc_loss, "amt": abs(gain_loss), "desc": 'خسائر بيع أصول', "curr": asset.currency or base_currency})
        
        # --- Update Account Balances ---
        from utils.accounting import update_account_balance
        if disposal.disposal_price > 0 and acc_cash:
            update_account_balance(conn, account_id=acc_cash, debit_base=float(disposal.disposal_price), credit_base=0)
        if acc_depr_recorded > 0 and acc_acc_depr:
            update_account_balance(conn, account_id=acc_acc_depr, debit_base=float(acc_depr_recorded), credit_base=0)
        if acc_fixed_assets:
            update_account_balance(conn, account_id=acc_fixed_assets, debit_base=0, credit_base=float(asset.cost))
        if gain_loss > 0 and acc_gain:
            update_account_balance(conn, account_id=acc_gain, debit_base=0, credit_base=float(gain_loss))
        elif gain_loss < 0 and acc_loss:
            update_account_balance(conn, account_id=acc_loss, debit_base=float(abs(gain_loss)), credit_base=0)
                         
        trans.commit()
        return {"id": asset_id, "status": "disposed", "journal_entry": je_num}
    except HTTPException:
        trans.rollback()
        raise
    except Exception as e:
        trans.rollback()
        print(f"Error disposing asset: {e}")
        raise HTTPException(status_code=500, detail=str(e))
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

        cost = float(asset.cost)

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
            ts = datetime.now().strftime('%Y%m%d%H%M%S')
            je_num = f"JE-ASSET-XFER-{je_type}-{asset_id}-{ts}"
            je_id = conn.execute(text("""
                INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, created_by, branch_id, currency, exchange_rate)
                VALUES (:num, CURRENT_DATE, :ref, :desc, 'posted', :uid, :br, :curr, 1)
                RETURNING id
            """), {
                "num": je_num, "ref": f"ASSET-XFER-{asset_id}",
                "desc": f"نقل أصل #{asset_id} — {je_type}",
                "uid": current_user.id, "br": branch_id, "curr": base_currency
            }).scalar()

            for acc_id, debit, credit, desc in lines:
                conn.execute(text("""
                    INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description, amount_currency, currency)
                    VALUES (:jid, :acc, :d, :c, :desc, :amt, :curr)
                """), {"jid": je_id, "acc": acc_id, "d": debit, "c": credit, "desc": desc, "amt": debit or credit, "curr": base_currency})
                update_account_balance(conn, account_id=acc_id, debit_base=debit, credit_base=credit)

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
        raise HTTPException(status_code=500, detail=str(e))
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

        acc_depr_recorded = float(conn.execute(text("""
            SELECT COALESCE(SUM(amount), 0) FROM asset_depreciation_schedule WHERE asset_id = :id AND posted = TRUE
        """), {"id": asset_id}).scalar())

        old_book = float(asset.cost) - acc_depr_recorded
        diff = reval.new_value - old_book

        if abs(diff) < 0.01:
            return {"success": True, "message": "لا يوجد فرق في القيمة"}

        base_currency = get_base_currency(conn)
        acc_fixed = get_mapped_account_id(conn, "acc_map_fixed_assets")
        acc_reval = get_mapped_account_id(conn, "acc_map_revaluation_reserve")
        acc_loss = get_mapped_account_id(conn, "acc_map_asset_loss")
        if diff > 0 and not acc_reval:
            raise HTTPException(status_code=400, detail="لم يتم تعيين حساب احتياطي إعادة التقييم في الإعدادات")
        if diff < 0 and not acc_loss:
            raise HTTPException(status_code=400, detail="لم يتم تعيين حساب خسائر الأصول في الإعدادات")

        ts = datetime.now().strftime('%Y%m%d%H%M%S')
        je_num = f"JE-ASSET-REVAL-{asset_id}-{ts}"
        je_id = conn.execute(text("""
            INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, created_by, branch_id, currency, exchange_rate)
            VALUES (:num, CURRENT_DATE, :ref, :desc, 'posted', :uid, :br, :curr, 1) RETURNING id
        """), {
            "num": je_num, "ref": f"ASSET-REVAL-{asset_id}", "desc": reval.reason,
            "uid": current_user.id, "br": asset.branch_id, "curr": base_currency
        }).scalar()

        if diff > 0:
            # Increase: Debit fixed assets, Credit revaluation reserve
            conn.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description, amount_currency, currency)
                VALUES (:jid, :acc, :amt, 0, :desc, :amt, :curr)
            """), {"jid": je_id, "acc": acc_fixed, "amt": abs(diff), "desc": f"زيادة قيمة أصل #{asset_id}", "curr": base_currency})
            conn.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description, amount_currency, currency)
                VALUES (:jid, :acc, 0, :amt, :desc, :amt, :curr)
            """), {"jid": je_id, "acc": acc_reval, "amt": abs(diff), "desc": "احتياطي إعادة تقييم", "curr": base_currency})
            update_account_balance(conn, account_id=acc_fixed, debit_base=abs(diff), credit_base=0)
            update_account_balance(conn, account_id=acc_reval, debit_base=0, credit_base=abs(diff))
        else:
            # Decrease: Debit loss, Credit fixed assets
            conn.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description, amount_currency, currency)
                VALUES (:jid, :acc, :amt, 0, :desc, :amt, :curr)
            """), {"jid": je_id, "acc": acc_loss, "amt": abs(diff), "desc": f"انخفاض قيمة أصل #{asset_id}", "curr": base_currency})
            conn.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description, amount_currency, currency)
                VALUES (:jid, :acc, 0, :amt, :desc, :amt, :curr)
            """), {"jid": je_id, "acc": acc_fixed, "amt": abs(diff), "desc": f"تخفيض أصل #{asset_id}", "curr": base_currency})
            update_account_balance(conn, account_id=acc_loss, debit_base=abs(diff), credit_base=0)
            update_account_balance(conn, account_id=acc_fixed, debit_base=0, credit_base=abs(diff))

        # Update asset cost
        conn.execute(text("UPDATE assets SET cost = cost + :diff, updated_at = NOW() WHERE id = :id"),
                     {"diff": diff, "id": asset_id})

        trans.commit()
        return {
            "success": True, "asset_id": asset_id,
            "old_book_value": round(old_book, 2), "new_value": reval.new_value,
            "difference": round(diff, 2), "journal_entry": je_num,
        }
    except HTTPException:
        trans.rollback()
        raise
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=500, detail=str(e))
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
        cost = float(asset.cost)
        residual = float(asset.residual_value or 0)
        life = int(asset.life_years or 5)
        rate = data.get("rate", 2.0 / life)  # Double declining by default
        schedule = []
        book_value = cost
        for year in range(1, life + 1):
            dep = round(book_value * rate, 2)
            if book_value - dep < residual:
                dep = round(book_value - residual, 2)
            book_value -= dep
            schedule.append({"year": year, "depreciation": dep, "book_value": round(book_value, 2)})
            if book_value <= residual:
                break
        return {"asset_id": asset_id, "method": "declining_balance", "rate": rate, "schedule": schedule}
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
        cost = float(asset.cost)
        residual = float(asset.residual_value or 0)
        total_units = float(data.get("total_units") or asset.total_units or 1)
        units_used = float(data.get("units_used", 0))
        dep_per_unit = (cost - residual) / total_units
        depreciation = round(dep_per_unit * units_used, 2)
        # Update used units
        conn.execute(text("UPDATE assets SET used_units = COALESCE(used_units,0) + :u WHERE id = :id"),
                     {"u": units_used, "id": asset_id})
        conn.commit()
        return {
            "asset_id": asset_id, "method": "units_of_production",
            "dep_per_unit": round(dep_per_unit, 4),
            "units_used": units_used, "depreciation": depreciation,
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
        cost = float(asset.cost)
        residual = float(asset.residual_value or 0)
        life = int(asset.life_years or 5)
        depreciable = cost - residual
        syd = life * (life + 1) / 2
        schedule = []
        for year in range(1, life + 1):
            fraction = (life - year + 1) / syd
            dep = round(depreciable * fraction, 2)
            schedule.append({"year": year, "fraction": round(fraction, 4), "depreciation": dep})
        return {"asset_id": asset_id, "method": "sum_of_years_digits", "schedule": schedule}
    finally:
        conn.close()


# ---------- ASSET-002: Asset Transfers Between Branches ----------

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
        # Calculate current book value
        dep_sum = conn.execute(text(
            "SELECT COALESCE(SUM(amount),0) FROM depreciation_schedule WHERE asset_id = :id AND is_posted = true"
        ), {"id": data["asset_id"]}).scalar()
        book_value = float(asset.cost) - float(dep_sum or 0)

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
        raise HTTPException(status_code=500, detail=str(e))
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
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ---------- ASSET-003: Asset Revaluations ----------

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
            "SELECT COALESCE(SUM(amount),0) FROM depreciation_schedule WHERE asset_id = :id AND is_posted = true"
        ), {"id": data["asset_id"]}).scalar()
        old_value = float(asset.cost) - float(dep_sum or 0)
        new_value = float(data["new_value"])
        diff = round(new_value - old_value, 2)

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
        raise HTTPException(status_code=500, detail=str(e))
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
        raise HTTPException(status_code=500, detail=str(e))
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
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


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
