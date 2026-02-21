"""
Inventory Module - Stock Receipt & Delivery
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from datetime import datetime
import logging

from database import get_db_connection
from routers.auth import get_current_user
from utils.permissions import require_permission
from .schemas import StockMovementCreate

stock_movements_router = APIRouter()
logger = logging.getLogger(__name__)


@stock_movements_router.post("/receipt", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("stock.manage"))])
def create_stock_receipt(
    movement: StockMovementCreate,
    current_user: dict = Depends(get_current_user)
):
    """إضافة مخزون (استلام بضاعة)"""
    db = get_db_connection(current_user.company_id)
    try:
        # Validate warehouse
        wh = db.execute(text("SELECT warehouse_name FROM warehouses WHERE id = :id"), {"id": movement.warehouse_id}).fetchone()
        if not wh:
            raise HTTPException(status_code=404, detail="المستودع غير موجود")

        import random
        ref = movement.reference or f"REC-{datetime.now().year}-{random.randint(10000, 99999)}"
        txn_date = movement.date or datetime.now().strftime("%Y-%m-%d")

        for item in movement.items:
            # Upsert inventory
            exists = db.execute(text("""
                SELECT 1 FROM inventory WHERE product_id = :pid AND warehouse_id = :wh
            """), {"pid": item.product_id, "wh": movement.warehouse_id}).scalar()

            if exists:
                db.execute(text("""
                    UPDATE inventory SET quantity = quantity + :qty 
                    WHERE product_id = :pid AND warehouse_id = :wh
                """), {"qty": item.quantity, "pid": item.product_id, "wh": movement.warehouse_id})
            else:
                db.execute(text("""
                    INSERT INTO inventory (product_id, warehouse_id, quantity)
                    VALUES (:pid, :wh, :qty)
                """), {"pid": item.product_id, "wh": movement.warehouse_id, "qty": item.quantity})

            # Log Transaction
            db.execute(text("""
                INSERT INTO inventory_transactions (
                    product_id, warehouse_id, transaction_type, reference_type, 
                    quantity, notes, created_by, created_at
                ) VALUES (
                    :pid, :wh, 'stock_in', 'receipt', 
                    :qty, :notes, :user, :date
                )
            """), {
                "pid": item.product_id,
                "wh": movement.warehouse_id,
                "qty": item.quantity,
                "notes": f"Stock Receipt {ref} - {movement.notes or ''}",
                "user": current_user.id,
                "date": txn_date
            })

        db.commit()
        return {"message": "تم استلام البضاعة بنجاح", "reference": ref}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@stock_movements_router.post("/delivery", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("stock.manage"))])
def create_stock_delivery(
    movement: StockMovementCreate,
    current_user: dict = Depends(get_current_user)
):
    """صرف مخزون (تسليم بضاعة)"""
    db = get_db_connection(current_user.company_id)
    try:
        # Validate warehouse
        wh = db.execute(text("SELECT warehouse_name FROM warehouses WHERE id = :id"), {"id": movement.warehouse_id}).fetchone()
        if not wh:
            raise HTTPException(status_code=404, detail="المستودع غير موجود")

        import random
        ref = movement.reference or f"DEL-{datetime.now().year}-{random.randint(10000, 99999)}"
        txn_date = movement.date or datetime.now().strftime("%Y-%m-%d")

        for item in movement.items:
            # Check availability
            current_qty = db.execute(text("""
                SELECT quantity FROM inventory 
                WHERE product_id = :pid AND warehouse_id = :wh
            """), {"pid": item.product_id, "wh": movement.warehouse_id}).scalar() or 0

            if current_qty < item.quantity:
                prod_name = db.execute(text("SELECT product_name FROM products WHERE id = :pid"), {"pid": item.product_id}).scalar()
                raise HTTPException(status_code=400, detail=f"الكمية غير متوفرة للمنتج: {prod_name}")

            # Deduct inventory
            db.execute(text("""
                UPDATE inventory SET quantity = quantity - :qty 
                WHERE product_id = :pid AND warehouse_id = :wh
            """), {"qty": item.quantity, "pid": item.product_id, "wh": movement.warehouse_id})

            # Log Transaction
            db.execute(text("""
                INSERT INTO inventory_transactions (
                    product_id, warehouse_id, transaction_type, reference_type, 
                    quantity, notes, created_by, created_at
                ) VALUES (
                    :pid, :wh, 'stock_out', 'delivery', 
                    :qty, :notes, :user, :date
                )
            """), {
                "pid": item.product_id,
                "wh": movement.warehouse_id,
                "qty": -item.quantity,
                "notes": f"Stock Delivery {ref} - {movement.notes or ''}",
                "user": current_user.id,
                "date": txn_date
            })

        db.commit()
        return {"message": "تم تسليم البضاعة بنجاح", "reference": ref}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
