"""
Inventory Module - Stock Transfers (Single-item with GL + Multi-item)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import text
from typing import Optional
from datetime import datetime
import logging

from database import get_db_connection
from routers.auth import get_current_user
from utils.audit import log_activity
from utils.permissions import require_permission
from .schemas import StockTransferSingleCreate, StockTransferCreate

transfers_router = APIRouter()
logger = logging.getLogger(__name__)


@transfers_router.post("/transfers", dependencies=[Depends(require_permission("stock.adjustment"))])
def create_stock_transfer(
    transfer: StockTransferSingleCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """تحويل مخزني مباشر بين المستودعات مع تطبيق سياسة التكلفة"""
    from services.costing_service import CostingService

    db = get_db_connection(current_user.company_id)
    try:
        from utils.accounting import get_base_currency
        base_currency = get_base_currency(db)
        user_id = current_user.id

        # 1. Validate source and destination are different
        if transfer.source_warehouse_id == transfer.destination_warehouse_id:
            raise HTTPException(status_code=400, detail="لا يمكن التحويل لنفس المستودع")

        # 2. Check warehouses exist
        src_wh = db.execute(text("SELECT warehouse_name FROM warehouses WHERE id = :id"),
                           {"id": transfer.source_warehouse_id}).fetchone()
        dst_wh = db.execute(text("SELECT warehouse_name FROM warehouses WHERE id = :id"),
                           {"id": transfer.destination_warehouse_id}).fetchone()

        if not src_wh:
            raise HTTPException(status_code=404, detail="المستودع المصدر غير موجود")
        if not dst_wh:
            raise HTTPException(status_code=404, detail="المستودع الوجهة غير موجود")

        # 3. Check product exists
        product = db.execute(text("SELECT product_name FROM products WHERE id = :id"),
                            {"id": transfer.product_id}).fetchone()
        if not product:
            raise HTTPException(status_code=404, detail="المنتج غير موجود")

        # 4. Check available stock in source — lock row to prevent phantom stock
        source_inv = db.execute(text("""
            SELECT quantity, average_cost FROM inventory 
            WHERE product_id = :pid AND warehouse_id = :wh
            FOR UPDATE
        """), {"pid": transfer.product_id, "wh": transfer.source_warehouse_id}).fetchone()

        source_qty = float(source_inv.quantity) if source_inv else 0
        source_cost = float(source_inv.average_cost) if source_inv else 0

        if source_qty < transfer.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"الكمية المتوفرة ({source_qty}) أقل من المطلوب ({transfer.quantity})"
            )

        # 5. Get destination current state — lock row to ensure consistent WAC
        dest_inv = db.execute(text("""
            SELECT quantity, average_cost FROM inventory 
            WHERE product_id = :pid AND warehouse_id = :wh
            FOR UPDATE
        """), {"pid": transfer.product_id, "wh": transfer.destination_warehouse_id}).fetchone()

        dest_qty_before = float(dest_inv.quantity) if dest_inv else 0
        dest_cost_before = float(dest_inv.average_cost) if dest_inv else 0

        # 6. Update source inventory (decrease)
        db.execute(text("""
            UPDATE inventory SET quantity = quantity - :qty, updated_at = NOW()
            WHERE product_id = :pid AND warehouse_id = :wh
        """), {"qty": transfer.quantity, "pid": transfer.product_id, "wh": transfer.source_warehouse_id})

        # 7. Update destination inventory (increase with WAC calculation)
        if dest_inv:
            # Calculate new weighted average cost
            new_total_qty = dest_qty_before + transfer.quantity
            if new_total_qty > 0:
                new_avg_cost = ((dest_qty_before * dest_cost_before) + (transfer.quantity * source_cost)) / new_total_qty
            else:
                new_avg_cost = source_cost

            db.execute(text("""
                UPDATE inventory 
                SET quantity = :qty, average_cost = :cost, updated_at = NOW()
                WHERE product_id = :pid AND warehouse_id = :wh
            """), {
                "qty": new_total_qty,
                "cost": new_avg_cost,
                "pid": transfer.product_id,
                "wh": transfer.destination_warehouse_id
            })
        else:
            # Insert new inventory record with source cost
            db.execute(text("""
                INSERT INTO inventory (product_id, warehouse_id, quantity, average_cost, updated_at)
                VALUES (:pid, :wh, :qty, :cost, NOW())
            """), {
                "pid": transfer.product_id,
                "wh": transfer.destination_warehouse_id,
                "qty": transfer.quantity,
                "cost": source_cost
            })
            new_avg_cost = source_cost

        # 8. Log transactions
        db.execute(text("""
            INSERT INTO inventory_transactions (product_id, warehouse_id, transaction_type, 
                                               reference_type, quantity, notes, created_by)
            VALUES (:pid, :wh, 'transfer_out', 'transfer', :qty, :notes, :user)
        """), {
            "pid": transfer.product_id,
            "wh": transfer.source_warehouse_id,
            "qty": -transfer.quantity,
            "notes": transfer.notes or f"تحويل إلى {dst_wh.warehouse_name}",
            "user": user_id
        })

        db.execute(text("""
            INSERT INTO inventory_transactions (product_id, warehouse_id, transaction_type, 
                                               reference_type, quantity, notes, created_by)
            VALUES (:pid, :wh, 'transfer_in', 'transfer', :qty, :notes, :user)
        """), {
            "pid": transfer.product_id,
            "wh": transfer.destination_warehouse_id,
            "qty": transfer.quantity,
            "notes": transfer.notes or f"تحويل من {src_wh.warehouse_name}",
            "user": user_id
        })

        # 9. Log in stock_transfer_log for V2 tracking
        db.execute(text("""
            INSERT INTO stock_transfer_log 
            (product_id, from_warehouse_id, to_warehouse_id, quantity, transfer_cost, 
             from_avg_cost_before, to_avg_cost_before, to_avg_cost_after)
            VALUES (:pid, :fwh, :twh, :qty, :tcost, :fcast, :tcast_b, :tcast_a)
        """), {
            "pid": transfer.product_id,
            "fwh": transfer.source_warehouse_id,
            "twh": transfer.destination_warehouse_id,
            "qty": transfer.quantity,
            "tcost": source_cost,
            "fcast": source_cost,
            "tcast_b": dest_cost_before,
            "tcast_a": new_avg_cost
        })

        # 9b. Create GL Journal Entry for warehouse transfer
        src_branch = db.execute(text("SELECT branch_id FROM warehouses WHERE id = :id"), {"id": transfer.source_warehouse_id}).scalar()
        dst_branch = db.execute(text("SELECT branch_id FROM warehouses WHERE id = :id"), {"id": transfer.destination_warehouse_id}).scalar()

        transfer_value = float(transfer.quantity) * float(source_cost)
        if transfer_value > 0.01:
            from utils.accounting import get_mapped_account_id, update_account_balance
            import uuid as uuid_mod

            # Get inventory accounts
            acc_inventory = get_mapped_account_id(db, "acc_map_inventory")

            if acc_inventory:
                if src_branch and dst_branch and src_branch != dst_branch:
                    # Inter-branch transfer needs GL entry via inter-branch clearing account
                    acc_interco = get_mapped_account_id(db, "acc_map_intercompany") or acc_inventory

                    je_num = f"JE-TRF-{uuid_mod.uuid4().hex[:6].upper()}"
                    je_id = db.execute(text("""
                        INSERT INTO journal_entries (
                            entry_number, entry_date, description, reference, status, 
                            created_by, branch_id, currency, exchange_rate
                        ) VALUES (:num, CURRENT_DATE, :desc, :ref, 'posted', :uid, :bid, :base_curr, 1.0)
                        RETURNING id
                    """), {
                        "num": je_num,
                        "desc": f"Stock Transfer {src_wh.warehouse_name} → {dst_wh.warehouse_name}",
                        "ref": je_num, "uid": user_id, "bid": src_branch,
                        "base_curr": base_currency
                    }).scalar()

                    # Dr Destination Inventory, Cr Source Inventory
                    db.execute(text("INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES (:jid, :aid, :amt, 0, :desc)"),
                              {"jid": je_id, "aid": acc_inventory, "amt": transfer_value, "desc": f"Transfer In - {dst_wh.warehouse_name}"})
                    db.execute(text("INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES (:jid, :aid, 0, :amt, :desc)"),
                              {"jid": je_id, "aid": acc_inventory, "amt": transfer_value, "desc": f"Transfer Out - {src_wh.warehouse_name}"})
                else:
                    # Same-branch transfer: still create GL memo entry for audit trail
                    je_num = f"JE-TRF-{uuid_mod.uuid4().hex[:6].upper()}"
                    je_id = db.execute(text("""
                        INSERT INTO journal_entries (
                            entry_number, entry_date, description, reference, status, 
                            created_by, branch_id, currency, exchange_rate
                        ) VALUES (:num, CURRENT_DATE, :desc, :ref, 'posted', :uid, :bid, :base_curr, 1.0)
                        RETURNING id
                    """), {
                        "num": je_num,
                        "desc": f"تحويل مخزني: {src_wh.warehouse_name} → {dst_wh.warehouse_name}",
                        "ref": je_num, "uid": user_id, "bid": src_branch or dst_branch,
                        "base_curr": base_currency
                    }).scalar()

                    db.execute(text("INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES (:jid, :aid, :amt, 0, :desc)"),
                              {"jid": je_id, "aid": acc_inventory, "amt": transfer_value, "desc": f"Transfer In - {dst_wh.warehouse_name}"})
                    db.execute(text("INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES (:jid, :aid, 0, :amt, :desc)"),
                              {"jid": je_id, "aid": acc_inventory, "amt": transfer_value, "desc": f"Transfer Out - {src_wh.warehouse_name}"})

        # 10. Log activity
        log_activity(
            db, user_id, "stock_transfer",
            f"تحويل {transfer.quantity} من {product.product_name} من {src_wh.warehouse_name} إلى {dst_wh.warehouse_name}",
            request
        )

        db.commit()

        return {
            "message": "تم التحويل بنجاح",
            "transfer_details": {
                "product_name": product.product_name,
                "quantity": transfer.quantity,
                "source_warehouse": src_wh.warehouse_name,
                "destination_warehouse": dst_wh.warehouse_name,
                "transfer_cost": source_cost,
                "new_destination_avg_cost": new_avg_cost
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Stock transfer error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@transfers_router.post("/transfer", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("stock.transfer"))])
def transfer_stock(
    transfer: StockTransferCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """نقل مخزون بين المستودعات (متعدد الأصناف)"""
    db = get_db_connection(current_user.company_id)
    try:
        if transfer.source_warehouse_id == transfer.destination_warehouse_id:
            raise HTTPException(status_code=400, detail="لا يمكن النقل لنفس المستودع")

        # Validate warehouses exist
        src = db.execute(text("SELECT warehouse_name FROM warehouses WHERE id = :id"), {"id": transfer.source_warehouse_id}).fetchone()
        dst = db.execute(text("SELECT warehouse_name FROM warehouses WHERE id = :id"), {"id": transfer.destination_warehouse_id}).fetchone()

        if not src or not dst:
            raise HTTPException(status_code=404, detail="المستودع غير موجود")

        import random
        transfer_ref = f"TRF-{datetime.now().year}-{random.randint(10000, 99999)}"

        for item in transfer.items:
            # Check source stock
            current_qty = db.execute(text("""
                SELECT quantity FROM inventory 
                WHERE product_id = :pid AND warehouse_id = :wh
            """), {"pid": item.product_id, "wh": transfer.source_warehouse_id}).scalar() or 0

            if current_qty < item.quantity:
                prod_name = db.execute(text("SELECT product_name FROM products WHERE id = :pid"), {"pid": item.product_id}).scalar()
                raise HTTPException(status_code=400, detail=f"الكمية غير متوفرة للمنتج: {prod_name}")

            # 1. Get source cost for WAC calculation
            source_inv = db.execute(text("""
                SELECT average_cost FROM inventory 
                WHERE product_id = :pid AND warehouse_id = :wh
            """), {"pid": item.product_id, "wh": transfer.source_warehouse_id}).fetchone()
            source_cost = float(source_inv.average_cost or 0) if source_inv else 0

            # 2. Deduct from Source
            db.execute(text("""
                UPDATE inventory SET quantity = quantity - :qty 
                WHERE product_id = :pid AND warehouse_id = :wh
            """), {"qty": item.quantity, "pid": item.product_id, "wh": transfer.source_warehouse_id})

            # 3. Add to Destination with WAC recalculation
            exists_dest = db.execute(text("""
                SELECT quantity, average_cost FROM inventory WHERE product_id = :pid AND warehouse_id = :wh
            """), {"pid": item.product_id, "wh": transfer.destination_warehouse_id}).fetchone()

            if exists_dest:
                dest_qty = float(exists_dest.quantity or 0)
                dest_cost = float(exists_dest.average_cost or 0)
                new_total_qty = dest_qty + item.quantity
                if new_total_qty > 0:
                    new_avg_cost = ((dest_qty * dest_cost) + (item.quantity * source_cost)) / new_total_qty
                else:
                    new_avg_cost = source_cost
                db.execute(text("""
                    UPDATE inventory SET quantity = :qty, average_cost = :cost
                    WHERE product_id = :pid AND warehouse_id = :wh
                """), {"qty": new_total_qty, "cost": new_avg_cost, "pid": item.product_id, "wh": transfer.destination_warehouse_id})
            else:
                db.execute(text("""
                    INSERT INTO inventory (product_id, warehouse_id, quantity, average_cost)
                    VALUES (:pid, :wh, :qty, :cost)
                """), {"pid": item.product_id, "wh": transfer.destination_warehouse_id, "qty": item.quantity, "cost": source_cost})

            # 3. Log Transactions
            db.execute(text("""
                INSERT INTO inventory_transactions (
                    product_id, warehouse_id, transaction_type, reference_type, 
                    quantity, notes, created_by
                ) VALUES (
                    :pid, :wh, 'transfer_out', 'transfer', 
                    :qty, :notes, :user
                )
            """), {
                "pid": item.product_id,
                "wh": transfer.source_warehouse_id,
                "qty": -item.quantity,
                "notes": f"Transfer to {dst.warehouse_name} ({transfer_ref})",
                "user": current_user.id
            })

            db.execute(text("""
                INSERT INTO inventory_transactions (
                    product_id, warehouse_id, transaction_type, reference_type, 
                    quantity, notes, created_by
                ) VALUES (
                    :pid, :wh, 'transfer_in', 'transfer', 
                    :qty, :notes, :user
                )
            """), {
                "pid": item.product_id,
                "wh": transfer.destination_warehouse_id,
                "qty": item.quantity,
                "notes": f"Transfer from {src.warehouse_name} ({transfer_ref})",
                "user": current_user.id
            })

        db.commit()

        # AUDIT LOG
        log_activity(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="stock.transfer",
            resource_type="stock_transfer",
            resource_id=transfer_ref,
            details={"from": transfer.source_warehouse_id, "to": transfer.destination_warehouse_id, "items_count": len(transfer.items)},
            request=request,
            branch_id=db.execute(text("SELECT branch_id FROM warehouses WHERE id = :id"), {"id": transfer.source_warehouse_id}).scalar()
        )

        return {"message": "تم نقل المخزون بنجاح", "reference": transfer_ref}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
