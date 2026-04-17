"""
Inventory Module - Stock Receipt & Delivery
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from utils.i18n import http_error
from sqlalchemy import text
from datetime import datetime
from decimal import Decimal
import logging
import uuid

from database import get_db_connection
from routers.auth import get_current_user
from utils.audit import log_activity
from utils.permissions import require_permission
from .schemas import StockMovementCreate

stock_movements_router = APIRouter()
logger = logging.getLogger(__name__)


@stock_movements_router.post("/receipt", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("stock.manage"))])
def create_stock_receipt(
    movement: StockMovementCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """إضافة مخزون (استلام بضاعة)"""
    db = get_db_connection(current_user.company_id)
    try:
        # Validate warehouse
        wh = db.execute(text("SELECT warehouse_name, branch_id FROM warehouses WHERE id = :id"), {"id": movement.warehouse_id}).fetchone()
        if not wh:
            raise HTTPException(**http_error(404, "warehouse_not_found"))

        # INV-007: Branch access check
        allowed = getattr(current_user, 'allowed_branches', []) or []
        if allowed and "*" not in getattr(current_user, 'permissions', []):
            if wh.branch_id and wh.branch_id not in allowed:
                raise HTTPException(status_code=403, detail="لا يمكنك استلام بضاعة في مستودع خارج فروعك")

        ref = movement.reference or f"REC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        txn_date = movement.date or datetime.now().strftime("%Y-%m-%d")

        # UOM Validation: Discrete units must have integer quantities
        from utils.quantity_validation import validate_quantity_for_product
        for item in movement.items:
            validate_quantity_for_product(db, item.product_id, item.quantity)

        for item in movement.items:
            # Update WAC before quantity change
            unit_cost = Decimal(str(getattr(item, 'unit_cost', 0) or 0))
            if unit_cost > 0:
                from services.costing_service import CostingService
                CostingService.update_cost(
                    db,
                    product_id=item.product_id,
                    warehouse_id=movement.warehouse_id,
                    new_qty=item.quantity,
                    new_price=unit_cost,
                )

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

        # INV-007: Audit log
        log_activity(
            db, user_id=current_user.id, username=current_user.username,
            action="stock.receipt", resource_type="stock_movement",
            resource_id=ref, details={"warehouse_id": movement.warehouse_id, "items_count": len(movement.items)},
            request=request, branch_id=wh.branch_id
        )

        return {"message": "تم استلام البضاعة بنجاح", "reference": ref}
    except Exception as e:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@stock_movements_router.post("/delivery", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("stock.manage"))])
def create_stock_delivery(
    movement: StockMovementCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """صرف مخزون (تسليم بضاعة)"""
    db = get_db_connection(current_user.company_id)
    try:
        # Validate warehouse
        wh = db.execute(text("SELECT warehouse_name, branch_id FROM warehouses WHERE id = :id"), {"id": movement.warehouse_id}).fetchone()
        if not wh:
            raise HTTPException(**http_error(404, "warehouse_not_found"))

        # INV-007: Branch access check
        allowed = getattr(current_user, 'allowed_branches', []) or []
        if allowed and "*" not in getattr(current_user, 'permissions', []):
            if wh.branch_id and wh.branch_id not in allowed:
                raise HTTPException(status_code=403, detail="لا يمكنك صرف بضاعة من مستودع خارج فروعك")

        ref = movement.reference or f"DEL-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        txn_date = movement.date or datetime.now().strftime("%Y-%m-%d")

        # UOM Validation: Discrete units must have integer quantities
        from utils.quantity_validation import validate_quantity_for_product
        for item in movement.items:
            validate_quantity_for_product(db, item.product_id, item.quantity)

        for item in movement.items:
            # CONC-FIX: Lock row and check availability atomically
            inv_row = db.execute(text("""
                SELECT quantity FROM inventory
                WHERE product_id = :pid AND warehouse_id = :wh
                FOR UPDATE
            """), {"pid": item.product_id, "wh": movement.warehouse_id}).fetchone()

            current_qty = inv_row.quantity if inv_row else 0
            if current_qty < item.quantity:
                prod_name = db.execute(text("SELECT product_name FROM products WHERE id = :pid"), {"pid": item.product_id}).scalar()
                raise HTTPException(status_code=400, detail=f"الكمية غير متوفرة للمنتج: {prod_name}. المتوفر: {current_qty}, المطلوب: {item.quantity}")

            # Deduct inventory (row is locked by FOR UPDATE above)
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

        # INV-007: Audit log
        log_activity(
            db, user_id=current_user.id, username=current_user.username,
            action="stock.delivery", resource_type="stock_movement",
            resource_id=ref, details={"warehouse_id": movement.warehouse_id, "items_count": len(movement.items)},
            request=request, branch_id=wh.branch_id
        )

        return {"message": "تم تسليم البضاعة بنجاح", "reference": ref}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
