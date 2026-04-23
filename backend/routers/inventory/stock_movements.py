"""
Inventory Module - Stock Receipt & Delivery

Note: ``/receipt`` and ``/delivery`` mutate inventory quantities WITHOUT
posting a journal entry. They are kept for backward compatibility with
legacy integrations only. New code MUST use ``/adjustment`` (which posts
a balanced JE through ``gl_service.create_journal_entry`` and is gated
by ``stock.adjust`` permission + fiscal-lock check).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
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
    response: Response,
    current_user: dict = Depends(get_current_user)
):
    """Legacy receipt endpoint (no GL posting).

    DEPRECATED: prefer POST /stock-movements/adjustment which posts a
    balanced JE and runs the fiscal-lock check.
    """
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = '</api/inventory/stock-movements/adjustment>; rel="successor-version"'
    logger.warning(
        "deprecated stock_movements/receipt called by user_id=%s company=%s",
        getattr(current_user, "id", None), getattr(current_user, "company_id", None),
    )
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
    except Exception:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@stock_movements_router.post("/delivery", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("stock.manage"))])
def create_stock_delivery(
    movement: StockMovementCreate,
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user)
):
    """Legacy delivery endpoint (no GL posting).

    DEPRECATED: prefer POST /stock-movements/adjustment which posts a
    balanced JE and runs the fiscal-lock check.
    """
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = '</api/inventory/stock-movements/adjustment>; rel="successor-version"'
    logger.warning(
        "deprecated stock_movements/delivery called by user_id=%s company=%s",
        getattr(current_user, "id", None), getattr(current_user, "company_id", None),
    )
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
    except Exception:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


# ==========================================================================
# INV-F1: Stock adjustment with mandatory GL posting (Phase-11 Sprint-5)
# ==========================================================================

from pydantic import BaseModel, Field
from typing import List as _List, Optional as _Optional


class StockAdjustmentItem(BaseModel):
    product_id: int
    warehouse_id: int
    quantity_delta: float  # positive = stock_in, negative = stock_out
    unit_cost: float = Field(..., gt=0)
    reason: _Optional[str] = None


class StockAdjustmentCreate(BaseModel):
    adjustment_account_id: int  # P&L account (gain/loss on inventory)
    inventory_account_id: _Optional[int] = None  # Override; else from company_settings
    reference: _Optional[str] = None
    notes: _Optional[str] = None
    date: _Optional[str] = None
    items: _List[StockAdjustmentItem]


@stock_movements_router.post(
    "/adjustment",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("stock.adjust"))],
)
def create_stock_adjustment(
    adjustment: StockAdjustmentCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """تسوية مخزون مع ترحيل محاسبي إلزامي (INV-F1).

    Unlike the legacy /receipt and /delivery endpoints, every adjustment here
    MUST post a balanced journal entry through ``gl_service.create_journal_entry``
    so inventory value and ledger balances stay reconciled.
    """
    from utils.accounting import get_mapped_account_id
    from services import gl_service
    from utils.fiscal_lock import check_fiscal_period_open

    if not adjustment.items:
        raise HTTPException(**http_error(400, "no_items"))

    db = get_db_connection(current_user.company_id)
    try:
        # Resolve inventory control account
        inv_account_id = adjustment.inventory_account_id
        if inv_account_id is None:
            inv_account_id = get_mapped_account_id(db, "acc_map_inventory")
        if not inv_account_id:
            raise HTTPException(**http_error(400, "inventory_account_not_mapped"))

        # Validate adjustment account exists
        acc_check = db.execute(
            text("SELECT id FROM accounts WHERE id = :id"),
            {"id": adjustment.adjustment_account_id},
        ).fetchone()
        if not acc_check:
            raise HTTPException(**http_error(404, "adjustment_account_not_found"))

        txn_date = adjustment.date or datetime.now().strftime("%Y-%m-%d")
        check_fiscal_period_open(db, txn_date)

        ref = adjustment.reference or f"ADJ-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

        # UOM guard
        from utils.quantity_validation import validate_quantity_for_product
        net_value_delta = Decimal("0")
        for item in adjustment.items:
            validate_quantity_for_product(db, item.product_id, abs(item.quantity_delta))
            # Resolve warehouse
            wh = db.execute(
                text("SELECT branch_id FROM warehouses WHERE id = :id"),
                {"id": item.warehouse_id},
            ).fetchone()
            if not wh:
                raise HTTPException(**http_error(404, "warehouse_not_found"))

            # Enforce non-negative stock on decreases
            if item.quantity_delta < 0:
                current_qty = db.execute(
                    text(
                        "SELECT COALESCE(quantity, 0) FROM inventory "
                        "WHERE product_id = :pid AND warehouse_id = :wh"
                    ),
                    {"pid": item.product_id, "wh": item.warehouse_id},
                ).scalar() or 0
                if float(current_qty) + item.quantity_delta < 0:
                    raise HTTPException(**http_error(400, "insufficient_stock"))

            # Upsert inventory quantity
            exists = db.execute(
                text(
                    "SELECT 1 FROM inventory WHERE product_id = :pid AND warehouse_id = :wh"
                ),
                {"pid": item.product_id, "wh": item.warehouse_id},
            ).scalar()
            if exists:
                db.execute(
                    text(
                        "UPDATE inventory SET quantity = quantity + :qty "
                        "WHERE product_id = :pid AND warehouse_id = :wh"
                    ),
                    {"qty": item.quantity_delta, "pid": item.product_id, "wh": item.warehouse_id},
                )
            else:
                db.execute(
                    text(
                        "INSERT INTO inventory (product_id, warehouse_id, quantity) "
                        "VALUES (:pid, :wh, :qty)"
                    ),
                    {"pid": item.product_id, "wh": item.warehouse_id, "qty": item.quantity_delta},
                )

            # Log transaction
            db.execute(
                text(
                    """
                    INSERT INTO inventory_transactions
                        (product_id, warehouse_id, transaction_type, reference_type,
                         quantity, notes, created_by, created_at)
                    VALUES (:pid, :wh, :tt, 'adjustment', :qty, :notes, :user, :date)
                    """
                ),
                {
                    "pid": item.product_id,
                    "wh": item.warehouse_id,
                    "tt": "stock_in" if item.quantity_delta >= 0 else "stock_out",
                    "qty": abs(item.quantity_delta),
                    "notes": f"Stock Adjustment {ref} - {item.reason or adjustment.notes or ''}",
                    "user": current_user.id,
                    "date": txn_date,
                },
            )

            net_value_delta += Decimal(str(item.quantity_delta)) * Decimal(str(item.unit_cost))

        # Post balanced JE
        net_value = net_value_delta.quantize(Decimal("0.01"))
        if abs(net_value) > Decimal("0.005"):
            if net_value > 0:
                # Stock increased → DR Inventory / CR Adjustment (gain)
                lines = [
                    {"account_id": inv_account_id, "debit": float(net_value), "credit": 0, "description": f"Stock adjustment gain {ref}"},
                    {"account_id": adjustment.adjustment_account_id, "debit": 0, "credit": float(net_value), "description": f"Stock adjustment gain {ref}"},
                ]
            else:
                # Stock decreased → DR Adjustment (loss) / CR Inventory
                abs_val = float(-net_value)
                lines = [
                    {"account_id": adjustment.adjustment_account_id, "debit": abs_val, "credit": 0, "description": f"Stock adjustment loss {ref}"},
                    {"account_id": inv_account_id, "debit": 0, "credit": abs_val, "description": f"Stock adjustment loss {ref}"},
                ]
            gl_service.create_journal_entry(
                db,
                company_id=current_user.company_id,
                date=txn_date,
                description=f"Stock Adjustment {ref}",
                lines=lines,
                user_id=current_user.id,
                reference=ref,
                source="StockAdjustment",
                source_id=None,
                username=getattr(current_user, "username", None),
                idempotency_key=f"stock_adj:{ref}",
            )

        db.commit()
        log_activity(
            db, user_id=current_user.id, username=current_user.username,
            action="stock.adjust", resource_type="stock_movement",
            resource_id=ref,
            details={
                "items_count": len(adjustment.items),
                "net_value_delta": float(net_value_delta),
                "adjustment_account_id": adjustment.adjustment_account_id,
            },
            request=request,
        )
        return {"message": "تمت تسوية المخزون مع ترحيل القيد بنجاح", "reference": ref, "net_value_delta": float(net_value_delta)}
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("Stock adjustment failed")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
