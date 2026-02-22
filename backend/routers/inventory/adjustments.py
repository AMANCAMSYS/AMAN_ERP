"""
Inventory Module - Stock Adjustments
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime
import logging

from database import get_db_connection
from routers.auth import get_current_user
from utils.audit import log_activity
from utils.permissions import require_permission
from .schemas import StockAdjustmentCreate

adjustments_router = APIRouter()
logger = logging.getLogger(__name__)


@adjustments_router.get("/adjustments", response_model=List[dict], dependencies=[Depends(require_permission("stock.view"))])
def list_adjustments(
    branch_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """عرض قائمة تسويات الجرد"""
    db = get_db_connection(current_user.company_id)
    try:
        query = """
            SELECT sa.id, sa.adjustment_number, sa.adjustment_type, sa.reason, 
                   sa.created_at, sa.status, sa.difference,
                   w.warehouse_name, p.product_name
            FROM stock_adjustments sa
            JOIN warehouses w ON sa.warehouse_id = w.id
            JOIN products p ON sa.product_id = p.id
            WHERE 1=1
        """
        params = {"limit": limit, "skip": skip}

        if branch_id:
            query += " AND w.branch_id = :branch_id"
            params["branch_id"] = branch_id

        query += " ORDER BY sa.created_at DESC LIMIT :limit OFFSET :skip"
        result = db.execute(text(query), params).fetchall()

        adjustments = []
        for row in result:
            adjustments.append({
                "id": row.id,
                "adjustment_number": row.adjustment_number,
                "type": row.adjustment_type,
                "reason": row.reason,
                "created_at": row.created_at,
                "status": row.status,
                "difference": row.difference,
                "warehouse_name": row.warehouse_name,
                "product_name": row.product_name
            })
        return adjustments
    finally:
        db.close()


@adjustments_router.post("/adjustments", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("stock.adjustment"))])
def create_adjustment(
    data: StockAdjustmentCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """إنشاء تسوية جردية (تعديل الكمية يدوياً)"""
    db = get_db_connection(current_user.company_id)
    try:
        # Get base currency
        from utils.accounting import get_base_currency
        base_currency = get_base_currency(db)
        # Get user info safely
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        username = current_user.username if hasattr(current_user, 'username') else current_user.get('username')
        company_id = current_user.company_id if hasattr(current_user, 'company_id') else current_user.get('company_id')

        # 1. Get Current Stock
        stock_query = """
            SELECT quantity FROM inventory 
            WHERE product_id = :pid AND warehouse_id = :wh
        """
        current_qty = db.execute(text(stock_query), {"pid": data.product_id, "wh": data.warehouse_id}).scalar() or 0.0

        difference = data.new_quantity - float(current_qty)

        if difference == 0:
            raise HTTPException(status_code=400, detail="الكمية الجديدة تطابق الكمية الحالية، لا يوجد تعديل")

        # Prevent negative stock
        if data.new_quantity < 0:
            raise HTTPException(status_code=400, detail="لا يمكن تعيين كمية المخزون بقيمة سالبة")

        adjustment_type = 'increase' if difference > 0 else 'decrease'

        # 2. Generate Number (unique via MAX)
        year = datetime.now().year
        max_num = db.execute(text("""
            SELECT MAX(CAST(SUBSTRING(adjustment_number FROM 'ADJ-\\d{4}-(\\d+)') AS INTEGER))
            FROM stock_adjustments 
            WHERE adjustment_number LIKE :pattern
        """), {"pattern": f"ADJ-{year}-%"}).scalar() or 0
        adj_number = f"ADJ-{year}-{str(max_num + 1).zfill(4)}"

        # 3. Create Adjustment Record
        adj_id_result = db.execute(text("""
            INSERT INTO stock_adjustments (
                adjustment_number, warehouse_id, product_id,
                adjustment_type, reason, old_quantity, new_quantity, difference,
                notes, status, created_by
            ) VALUES (
                :num, :wh, :pid,
                :type, :reason, :old, :new, :diff,
                :notes, 'approved', :uid
            ) RETURNING id
        """), {
            "num": adj_number, "wh": data.warehouse_id, "pid": data.product_id,
            "type": adjustment_type, "reason": data.reason,
            "old": current_qty, "new": data.new_quantity, "diff": difference,
            "notes": data.notes, "uid": user_id
        }).fetchone()

        if not adj_id_result:
            raise Exception("Failed to insert stock adjustment record")

        adj_id = adj_id_result[0]

        # 4. Update Inventory
        exists = db.execute(text("SELECT 1 FROM inventory WHERE product_id=:pid AND warehouse_id=:wh"),
                           {"pid": data.product_id, "wh": data.warehouse_id}).scalar()

        if exists:
            db.execute(text("""
                UPDATE inventory 
                SET quantity = :new_qty, last_movement_date = NOW()
                WHERE product_id = :pid AND warehouse_id = :wh
            """), {"new_qty": data.new_quantity, "pid": data.product_id, "wh": data.warehouse_id})
        else:
            db.execute(text("""
                INSERT INTO inventory (product_id, warehouse_id, quantity, last_movement_date)
                VALUES (:pid, :wh, :new_qty, NOW())
            """), {"pid": data.product_id, "wh": data.warehouse_id, "new_qty": data.new_quantity})

        # 5. Log Transaction
        trans_type = 'adjustment_in' if difference > 0 else 'adjustment_out'

        db.execute(text("""
            INSERT INTO inventory_transactions (
                product_id, warehouse_id, transaction_type, 
                reference_type, reference_id, reference_document,
                quantity, notes, created_by
            ) VALUES (
                :pid, :wh, :type,
                'adjustment', :ref_id, :doc_num,
                :qty, :notes, :uid
            )
        """), {
            "pid": data.product_id, "wh": data.warehouse_id, "type": trans_type,
            "ref_id": adj_id, "doc_num": adj_number,
            "qty": difference, "notes": data.notes or f"Stock Adjustment {adjustment_type}",
            "uid": user_id
        })

        # 6. Create GL Journal Entry for Inventory Adjustment
        from utils.accounting import get_mapped_account_id, update_account_balance
        acc_inventory = get_mapped_account_id(db, "acc_map_inventory")
        acc_adjustment = get_mapped_account_id(db, "acc_map_inventory_adjustment")

        if acc_inventory and acc_adjustment:
            cost_price = db.execute(text("SELECT cost_price FROM products WHERE id = :id"), {"id": data.product_id}).scalar() or 0
            adjustment_value = abs(difference) * float(cost_price)

            if adjustment_value > 0.01:
                import uuid
                je_num = f"JE-ADJ-{adj_number}"
                branch_id = db.execute(text("SELECT branch_id FROM warehouses WHERE id = :id"), {"id": data.warehouse_id}).scalar()

                je_id = db.execute(text("""
                    INSERT INTO journal_entries (
                        entry_number, entry_date, description, reference, status, created_by, branch_id,
                        currency, exchange_rate
                    )
                    VALUES (:num, NOW(), :desc, :ref, 'posted', :uid, :bid, :base_curr, 1.0) RETURNING id
                """), {
                    "num": je_num,
                    "desc": f"Stock Adjustment - {adj_number}",
                    "ref": adj_number,
                    "uid": user_id,
                    "bid": branch_id,
                    "base_curr": base_currency
                }).scalar()

                if difference > 0:
                    # Increase: Debit Inventory, Credit Adjustment (gain)
                    db.execute(text("INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES (:jid, :aid, :amt, 0, :desc)"),
                              {"jid": je_id, "aid": acc_inventory, "amt": adjustment_value, "desc": f"Inventory Increase - {adj_number}"})
                    db.execute(text("INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES (:jid, :aid, 0, :amt, :desc)"),
                              {"jid": je_id, "aid": acc_adjustment, "amt": adjustment_value, "desc": f"Adjustment Gain - {adj_number}"})
                    update_account_balance(db, account_id=acc_inventory, debit_base=adjustment_value, credit_base=0)
                    update_account_balance(db, account_id=acc_adjustment, debit_base=0, credit_base=adjustment_value)
                else:
                    # Decrease: Debit Adjustment (loss), Credit Inventory
                    db.execute(text("INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES (:jid, :aid, :amt, 0, :desc)"),
                              {"jid": je_id, "aid": acc_adjustment, "amt": adjustment_value, "desc": f"Adjustment Loss - {adj_number}"})
                    db.execute(text("INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES (:jid, :aid, 0, :amt, :desc)"),
                              {"jid": je_id, "aid": acc_inventory, "amt": adjustment_value, "desc": f"Inventory Decrease - {adj_number}"})
                    update_account_balance(db, account_id=acc_adjustment, debit_base=adjustment_value, credit_base=0)
                    update_account_balance(db, account_id=acc_inventory, debit_base=0, credit_base=adjustment_value)

        db.commit()

        # AUDIT LOG
        try:
            branch_id = db.execute(text("SELECT branch_id FROM warehouses WHERE id = :id"), {"id": data.warehouse_id}).scalar()

            log_activity(
                db,
                user_id=user_id,
                username=username,
                action="stock.adjustment",
                resource_type="stock_adjustment",
                resource_id=str(adj_id),
                details={"adjustment_number": adj_number, "product_id": data.product_id, "difference": difference},
                request=request,
                branch_id=branch_id
            )
        except Exception as audit_err:
            logger.warning(f"Audit logging failed: {audit_err}")

        return {"id": adj_id, "message": "تم حفظ تسوية الجرد بنجاح"}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Stock adjustment error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"حدث خطأ أثناء حفظ التسوية: {str(e)}")
    finally:
        db.close()
