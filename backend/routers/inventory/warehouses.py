"""
Inventory Module - Warehouses CRUD + Current Stock
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from typing import List, Optional
import logging

from database import get_db_connection
from routers.auth import get_current_user
from utils.permissions import require_permission
from schemas import WarehouseCreate, WarehouseResponse

warehouses_router = APIRouter()
logger = logging.getLogger(__name__)


@warehouses_router.get("/warehouses", response_model=List[WarehouseResponse], dependencies=[Depends(require_permission(["stock.view", "stock.reports"]))])
def list_warehouses(branch_id: Optional[int] = None, current_user: dict = Depends(get_current_user)):
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="Company ID missing")

    db = get_db_connection(current_user.company_id)
    try:
        query = """
            SELECT w.id, w.warehouse_name as name, w.warehouse_code as code, 
                   w.branch_id, COALESCE(b.branch_name, '') as branch_name
            FROM warehouses w
            LEFT JOIN branches b ON w.branch_id = b.id
            WHERE 1=1
        """
        params = {}
        if branch_id:
            query += " AND w.branch_id = :bid"
            params["bid"] = branch_id

        query += " ORDER BY w.id"
        result = db.execute(text(query), params).fetchall()
        return [{
            "id": r.id,
            "name": r.name,
            "code": r.code,
            "branch_id": r.branch_id,
            "branch_name": r.branch_name
        } for r in result]
    except Exception as e:
        logger.error(f"Error fetching warehouses: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching warehouses: {str(e)}")
    finally:
        db.close()


@warehouses_router.post("/warehouses", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("stock.adjustment"))])
def create_warehouse(warehouse: WarehouseCreate, current_user: dict = Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        # Check duplicate code
        exists = db.execute(text("SELECT 1 FROM warehouses WHERE warehouse_code = :code"), {"code": warehouse.code}).scalar()
        if exists:
            raise HTTPException(status_code=400, detail="كود المستودع موجود مسبقاً")

        result = db.execute(text("""
            INSERT INTO warehouses (warehouse_name, warehouse_code, branch_id) 
            VALUES (:name, :code, :branch_id) RETURNING id
        """), {"name": warehouse.name, "code": warehouse.code, "branch_id": warehouse.branch_id}).fetchone()
        db.commit()

        # Get branch name if branch_id is set
        branch_name = None
        if warehouse.branch_id:
            branch_name = db.execute(text("SELECT branch_name FROM branches WHERE id = :id"), {"id": warehouse.branch_id}).scalar()

        return {**warehouse.model_dump(), "id": result[0], "branch_name": branch_name}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@warehouses_router.put("/warehouses/{id}", response_model=WarehouseResponse, dependencies=[Depends(require_permission("stock.adjustment"))])
def update_warehouse(id: int, warehouse: WarehouseCreate, current_user: dict = Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        exists = db.execute(text("SELECT id FROM warehouses WHERE id = :id"), {"id": id}).scalar()
        if not exists:
            raise HTTPException(status_code=404, detail="المستودع غير موجود")

        db.execute(text("""
            UPDATE warehouses SET warehouse_name = :name, warehouse_code = :code, branch_id = :branch_id
            WHERE id = :id
        """), {"name": warehouse.name, "code": warehouse.code, "branch_id": warehouse.branch_id, "id": id})
        db.commit()

        # Get branch name if branch_id is set
        branch_name = None
        if warehouse.branch_id:
            branch_name = db.execute(text("SELECT branch_name FROM branches WHERE id = :id"), {"id": warehouse.branch_id}).scalar()

        return {**warehouse.model_dump(), "id": id, "branch_name": branch_name}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@warehouses_router.delete("/warehouses/{id}", dependencies=[Depends(require_permission("stock.adjustment"))])
def delete_warehouse(id: int, current_user: dict = Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(text("DELETE FROM warehouses WHERE id = :id"), {"id": id})
        db.commit()
        return {"message": "deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@warehouses_router.get("/warehouses/{id}", response_model=WarehouseResponse, dependencies=[Depends(require_permission("stock.view"))])
def get_warehouse(id: int, current_user: dict = Depends(get_current_user)):
    """تفاصيل مستودع"""
    db = get_db_connection(current_user.company_id)
    try:
        warehouse = db.execute(text("""
            SELECT w.id, w.warehouse_name as name, w.warehouse_code as code, 
                   w.branch_id, b.branch_name
            FROM warehouses w
            LEFT JOIN branches b ON w.branch_id = b.id
            WHERE w.id = :id
        """), {"id": id}).fetchone()
        if not warehouse:
            raise HTTPException(status_code=404, detail="المستودع غير موجود")

        return {"id": warehouse.id, "name": warehouse.name, "code": warehouse.code, "branch_id": warehouse.branch_id, "branch_name": warehouse.branch_name}
    finally:
        db.close()


@warehouses_router.get("/warehouses/{id}/current-stock", dependencies=[Depends(require_permission(["stock.view", "stock.reports"]))])
def get_warehouse_current_stock(id: int, current_user: dict = Depends(get_current_user)):
    """جرد المستودع: المنتجات والكميات (مخصص للمستودع المحدد)"""
    db = get_db_connection(current_user.company_id)
    try:
        # Check if warehouse exists
        exists = db.execute(text("SELECT 1 FROM warehouses WHERE id = :id"), {"id": id}).scalar()
        if not exists:
            raise HTTPException(status_code=404, detail="المستودع غير موجود")

        result = db.execute(text("""
            SELECT p.id, p.product_name, p.product_code, i.quantity, u.unit_name
            FROM inventory i
            JOIN products p ON i.product_id = p.id
            LEFT JOIN product_units u ON p.unit_id = u.id
            WHERE i.warehouse_id = :id AND i.quantity != 0
            ORDER BY p.product_name
        """), {"id": id}).fetchall()

        return [
            {
                "id": row.id,
                "product_name": row.product_name,
                "product_code": row.product_code,
                "quantity": float(row.quantity),
                "unit_name": row.unit_name or "قطعة"
            }
            for row in result
        ]
    finally:
        db.close()
