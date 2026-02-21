"""
Inventory Module - Shipments Lifecycle
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from typing import Optional
from datetime import datetime
import logging

from database import get_db_connection
from routers.auth import get_current_user
from utils.permissions import require_permission
from .schemas import ShipmentCreate

shipments_router = APIRouter()
logger = logging.getLogger(__name__)


@shipments_router.post("/shipments", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("stock.transfer"))])
def create_shipment(
    shipment: ShipmentCreate,
    current_user: dict = Depends(get_current_user)
):
    """إنشاء شحنة جديدة بين المستودعات"""
    company_id = current_user.get("company_id") if isinstance(current_user, dict) else current_user.company_id
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    db = get_db_connection(company_id)
    try:
        if shipment.source_warehouse_id == shipment.destination_warehouse_id:
            raise HTTPException(status_code=400, detail="لا يمكن الشحن لنفس المستودع")

        # Validate warehouses
        src = db.execute(text("SELECT warehouse_name FROM warehouses WHERE id = :id"),
                        {"id": shipment.source_warehouse_id}).fetchone()
        dst = db.execute(text("SELECT warehouse_name FROM warehouses WHERE id = :id"),
                        {"id": shipment.destination_warehouse_id}).fetchone()

        if not src or not dst:
            raise HTTPException(status_code=404, detail="المستودع غير موجود")

        import random
        shipment_ref = f"SHP-{datetime.now().year}-{random.randint(10000, 99999)}"

        # Create shipment
        result = db.execute(text("""
            INSERT INTO stock_shipments (shipment_ref, source_warehouse_id, destination_warehouse_id, 
                                        status, notes, created_by, created_at)
            VALUES (:ref, :src, :dst, 'pending', :notes, :user, NOW())
            RETURNING id
        """), {
            "ref": shipment_ref,
            "src": shipment.source_warehouse_id,
            "dst": shipment.destination_warehouse_id,
            "notes": shipment.notes,
            "user": user_id
        })
        shipment_id = result.fetchone()[0]

        # Add items
        for item in shipment.items:
            # Validate stock availability
            current_qty = db.execute(text("""
                SELECT quantity FROM inventory 
                WHERE product_id = :pid AND warehouse_id = :wh
            """), {"pid": item.product_id, "wh": shipment.source_warehouse_id}).scalar() or 0

            if current_qty < item.quantity:
                prod_name = db.execute(text("SELECT product_name FROM products WHERE id = :pid"),
                                      {"pid": item.product_id}).scalar()
                db.rollback()
                raise HTTPException(status_code=400, detail=f"الكمية غير متوفرة للمنتج: {prod_name}")

            db.execute(text("""
                INSERT INTO stock_shipment_items (shipment_id, product_id, quantity)
                VALUES (:sid, :pid, :qty)
            """), {"sid": shipment_id, "pid": item.product_id, "qty": item.quantity})

        # Create targeted notifications for destination branch
        dest_branch_info = db.execute(text("""
            SELECT branch_id, manager_id FROM warehouses WHERE id = :id
        """), {"id": shipment.destination_warehouse_id}).fetchone()

        if dest_branch_info:
            d_branch_id = dest_branch_info.branch_id
            d_manager_id = dest_branch_info.manager_id

            db.execute(text("""
                INSERT INTO notifications (user_id, type, title, message, link, created_at)
                SELECT DISTINCT u.id, 'shipment_incoming', :title, :message, :link, NOW()
                FROM company_users u
                LEFT JOIN user_branches ub ON u.id = ub.user_id
                WHERE u.is_active = TRUE 
                AND (ub.branch_id = :bid OR u.id = :mid OR u.role = 'superuser' OR u.role = 'admin')
            """), {
                "title": f"📦 شحنة واردة جديدة",
                "message": f"شحنة {shipment_ref} من {src.warehouse_name} إلى {dst.warehouse_name} في انتظار التأكيد",
                "link": f"/stock/shipments/incoming",
                "bid": d_branch_id,
                "mid": d_manager_id
            })

        db.commit()
        return {"message": "تم إنشاء الشحنة بنجاح", "reference": shipment_ref, "id": shipment_id}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@shipments_router.get("/shipments", dependencies=[Depends(require_permission("stock.view"))])
def list_shipments(
    status_filter: Optional[str] = None,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """عرض جميع الشحنات"""
    db = get_db_connection(current_user.company_id)
    try:
        query = """
            SELECT s.id, s.shipment_ref, s.status, s.notes, s.created_at, s.shipped_at, s.received_at,
                   sw.warehouse_name as source_warehouse,
                   dw.warehouse_name as destination_warehouse,
                   u.full_name as created_by_name,
                   (SELECT COUNT(*) FROM stock_shipment_items WHERE shipment_id = s.id) as item_count
            FROM stock_shipments s
            JOIN warehouses sw ON s.source_warehouse_id = sw.id
            JOIN warehouses dw ON s.destination_warehouse_id = dw.id
            LEFT JOIN company_users u ON s.created_by = u.id
            WHERE 1=1
        """
        params = {}
        if branch_id:
            query += " AND (sw.branch_id = :branch_id OR dw.branch_id = :branch_id)"
            params["branch_id"] = branch_id

        if status_filter:
            query += " AND s.status = :status"
            params["status"] = status_filter
        query += " ORDER BY s.created_at DESC"

        result = db.execute(text(query), params).fetchall()
        return [dict(r._mapping) for r in result]
    finally:
        db.close()


@shipments_router.get("/shipments/incoming", dependencies=[Depends(require_permission("stock.view"))])
def list_incoming_shipments(
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """عرض الشحنات الواردة المعلقة"""
    company_id = current_user.get("company_id") if isinstance(current_user, dict) else current_user.company_id
    db = get_db_connection(company_id)
    try:
        query = """
            SELECT s.id, s.shipment_ref, s.status, s.notes, s.created_at,
                   sw.warehouse_name as source_warehouse,
                   dw.warehouse_name as destination_warehouse,
                   u.full_name as created_by_name,
                   (SELECT json_agg(json_build_object(
                       'product_id', i.product_id,
                       'product_name', p.product_name,
                       'quantity', i.quantity
                   )) FROM stock_shipment_items i 
                   JOIN products p ON i.product_id = p.id 
                   WHERE i.shipment_id = s.id) as items
            FROM stock_shipments s
            JOIN warehouses sw ON s.source_warehouse_id = sw.id
            JOIN warehouses dw ON s.destination_warehouse_id = dw.id
            LEFT JOIN company_users u ON s.created_by = u.id
            WHERE s.status = 'pending'
        """
        params = {}
        if branch_id:
            query += " AND dw.branch_id = :bid"
            params["bid"] = branch_id

        query += " ORDER BY s.created_at DESC"
        result = db.execute(text(query), params).fetchall()
        return [dict(r._mapping) for r in result]
    finally:
        db.close()


@shipments_router.get("/shipments/{id}", dependencies=[Depends(require_permission("stock.view"))])
def get_shipment_details(
    id: int,
    current_user: dict = Depends(get_current_user)
):
    """عرض تفاصيل شحنة"""
    db = get_db_connection(current_user.company_id)
    try:
        shipment = db.execute(text("""
            SELECT s.*, sw.warehouse_name as source_warehouse, dw.warehouse_name as destination_warehouse,
                   u.full_name as created_by_name, r.full_name as received_by_name
            FROM stock_shipments s
            JOIN warehouses sw ON s.source_warehouse_id = sw.id
            JOIN warehouses dw ON s.destination_warehouse_id = dw.id
            LEFT JOIN company_users u ON s.created_by = u.id
            LEFT JOIN company_users r ON s.received_by = r.id
            WHERE s.id = :id
        """), {"id": id}).fetchone()

        if not shipment:
            raise HTTPException(status_code=404, detail="الشحنة غير موجودة")

        items = db.execute(text("""
            SELECT i.*, p.product_name, p.product_code
            FROM stock_shipment_items i
            JOIN products p ON i.product_id = p.id
            WHERE i.shipment_id = :id
        """), {"id": id}).fetchall()

        return {
            **dict(shipment._mapping),
            "items": [dict(i._mapping) for i in items]
        }
    finally:
        db.close()


@shipments_router.post("/shipments/{id}/confirm", dependencies=[Depends(require_permission("stock.transfer"))])
def confirm_shipment(
    id: int,
    current_user: dict = Depends(get_current_user)
):
    """تأكيد استلام الشحنة"""
    company_id = current_user.get("company_id") if isinstance(current_user, dict) else current_user.company_id
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    db = get_db_connection(company_id)
    try:
        # Get shipment
        shipment = db.execute(text("""
            SELECT s.*, sw.warehouse_name as source_name, dw.warehouse_name as dest_name
            FROM stock_shipments s
            JOIN warehouses sw ON s.source_warehouse_id = sw.id
            JOIN warehouses dw ON s.destination_warehouse_id = dw.id
            WHERE s.id = :id
        """), {"id": id}).fetchone()

        if not shipment:
            raise HTTPException(status_code=404, detail="الشحنة غير موجودة")

        if shipment.status != 'pending':
            raise HTTPException(status_code=400, detail="لا يمكن تأكيد هذه الشحنة")

        # Get items
        items = db.execute(text("""
            SELECT * FROM stock_shipment_items WHERE shipment_id = :id
        """), {"id": id}).fetchall()

        from services.costing_service import CostingService

        # Process each item
        for item in items:
            # 1. Deduct from source
            db.execute(text("""
                UPDATE inventory SET quantity = quantity - :qty
                WHERE product_id = :pid AND warehouse_id = :wh
            """), {"qty": item.quantity, "pid": item.product_id, "wh": shipment.source_warehouse_id})

            # 2. Get Source Cost for Valuation
            source_cost = CostingService.get_cogs_cost(db, item.product_id, shipment.source_warehouse_id)

            # 3. Update Destination Cost (WAC Calculation)
            CostingService.update_cost(
                db,
                product_id=item.product_id,
                warehouse_id=shipment.destination_warehouse_id,
                new_qty=float(item.quantity),
                new_price=float(source_cost)
            )

            # 4. Add to destination Qty
            exists = db.execute(text("""
                SELECT 1 FROM inventory WHERE product_id = :pid AND warehouse_id = :wh
            """), {"pid": item.product_id, "wh": shipment.destination_warehouse_id}).scalar()

            if exists:
                db.execute(text("""
                    UPDATE inventory SET quantity = quantity + :qty
                    WHERE product_id = :pid AND warehouse_id = :wh
                """), {"qty": item.quantity, "pid": item.product_id, "wh": shipment.destination_warehouse_id})
            else:
                exists_now = db.execute(text("""
                    SELECT 1 FROM inventory WHERE product_id = :pid AND warehouse_id = :wh
                """), {"pid": item.product_id, "wh": shipment.destination_warehouse_id}).scalar()

                if exists_now:
                    db.execute(text("UPDATE inventory SET quantity = quantity + :qty WHERE product_id = :pid AND warehouse_id = :wh"),
                               {"qty": item.quantity, "pid": item.product_id, "wh": shipment.destination_warehouse_id})
                else:
                    db.execute(text("""
                        INSERT INTO inventory (product_id, warehouse_id, quantity)
                        VALUES (:pid, :wh, :qty)
                    """), {"pid": item.product_id, "wh": shipment.destination_warehouse_id, "qty": item.quantity})

            # 5. Log transactions
            db.execute(text("""
                INSERT INTO inventory_transactions (product_id, warehouse_id, transaction_type, 
                                                   reference_type, quantity, notes, created_by)
                VALUES (:pid, :wh, 'shipment_out', 'shipment', :qty, :notes, :user)
            """), {
                "pid": item.product_id,
                "wh": shipment.source_warehouse_id,
                "qty": -item.quantity,
                "notes": f"Shipment {shipment.shipment_ref} to {shipment.dest_name}",
                "user": user_id
            })

            db.execute(text("""
                INSERT INTO inventory_transactions (product_id, warehouse_id, transaction_type, 
                                                   reference_type, quantity, notes, created_by)
                VALUES (:pid, :wh, 'shipment_in', 'shipment', :qty, :notes, :user)
            """), {
                "pid": item.product_id,
                "wh": shipment.destination_warehouse_id,
                "qty": item.quantity,
                "notes": f"Shipment {shipment.shipment_ref} from {shipment.source_name}",
                "user": user_id
            })

            # 5b. Log in stock_transfer_log (V2 Upgrade)
            dest_stats_after = db.execute(text("""
                SELECT average_cost FROM inventory 
                WHERE product_id = :pid AND warehouse_id = :wh
            """), {"pid": item.product_id, "wh": shipment.destination_warehouse_id}).fetchone()

            db.execute(text("""
                INSERT INTO stock_transfer_log 
                (shipment_id, product_id, from_warehouse_id, to_warehouse_id, quantity, transfer_cost, 
                 from_avg_cost_before, to_avg_cost_before, to_avg_cost_after)
                VALUES (:sid, :pid, :fwh, :twh, :qty, :tcost, :fcast, :tcast_b, :tcast_a)
            """), {
                "sid": id,
                "pid": item.product_id,
                "fwh": shipment.source_warehouse_id,
                "twh": shipment.destination_warehouse_id,
                "qty": item.quantity,
                "tcost": source_cost,
                "fcast": source_cost,
                "tcast_b": 0,
                "tcast_a": float(dest_stats_after.average_cost if dest_stats_after else 0)
            })

        # Update shipment status
        db.execute(text("""
            UPDATE stock_shipments 
            SET status = 'received', received_at = NOW(), received_by = :user
            WHERE id = :id
        """), {"id": id, "user": user_id})

        # Notify sender
        db.execute(text("""
            INSERT INTO notifications (user_id, type, title, message, link, created_at)
            VALUES (:user, 'shipment_confirmed', :title, :message, :link, NOW())
        """), {
            "user": shipment.created_by,
            "title": "✅ تم تأكيد استلام الشحنة",
            "message": f"تم تأكيد استلام الشحنة {shipment.shipment_ref} في {shipment.dest_name}",
            "link": f"/stock/shipments/{id}"
        })

        db.commit()
        return {"message": "تم تأكيد استلام الشحنة بنجاح"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@shipments_router.post("/shipments/{id}/cancel", dependencies=[Depends(require_permission("stock.manage"))])
def cancel_shipment(
    id: int,
    current_user: dict = Depends(get_current_user)
):
    """إلغاء الشحنة"""
    company_id = current_user.get("company_id") if isinstance(current_user, dict) else current_user.company_id
    db = get_db_connection(company_id)
    try:
        shipment = db.execute(text("""
            SELECT * FROM stock_shipments WHERE id = :id
        """), {"id": id}).fetchone()

        if not shipment:
            raise HTTPException(status_code=404, detail="الشحنة غير موجودة")

        if shipment.status != 'pending':
            raise HTTPException(status_code=400, detail="لا يمكن إلغاء هذه الشحنة")

        db.execute(text("""
            UPDATE stock_shipments SET status = 'cancelled' WHERE id = :id
        """), {"id": id})

        db.commit()
        return {"message": "تم إلغاء الشحنة"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
