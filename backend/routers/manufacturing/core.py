import logging
from decimal import Decimal
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from utils.i18n import http_error
from pydantic import BaseModel
from sqlalchemy import text
from routers.auth import get_current_user
from utils.permissions import require_permission, require_module
from database import get_db_connection
from utils.accounting import update_account_balance, get_base_currency
from utils.fiscal_lock import check_fiscal_period_open
from utils.exports import generate_excel, generate_pdf, create_export_response
from utils.audit import log_activity
from services.gl_service import create_journal_entry  # TASK-015: centralized GL posting
from schemas import UserResponse

logger = logging.getLogger(__name__)
from schemas.manufacturing_advanced import (
    WorkCenterCreate, WorkCenterResponse,
    RouteCreate, RouteResponse,
    BOMCreate, BOMResponse,
    ProductionOrderCreate, ProductionOrderResponse,
    ProductionOrderOperationResponse, MRPPlanResponse,
    EquipmentCreate, EquipmentResponse,
    MaintenanceLogCreate, MaintenanceLogResponse
)

router = APIRouter(
    prefix="/manufacturing",
    tags=["Manufacturing (Phase 5)"],
    dependencies=[Depends(require_module("manufacturing"))]
)

# ==========================================
# 1. WORK CENTERS
# ==========================================

@router.get("/work-centers", response_model=List[WorkCenterResponse], dependencies=[Depends(require_permission("manufacturing.view"))])
def list_work_centers(
    branch_id: Optional[int] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    from utils.permissions import validate_branch_access
    validated_branch = validate_branch_access(current_user, branch_id)
    conn = get_db_connection(current_user.company_id)
    try:
        query = "SELECT * FROM work_centers WHERE is_deleted = false"
        params = {}
        if validated_branch:
            query += " AND branch_id = :branch_id"
            params["branch_id"] = validated_branch
        query += " ORDER BY name"
        rows = conn.execute(text(query), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()

@router.post("/work-centers", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.create"]))])
def create_work_center(wc: WorkCenterCreate, request: Request, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        new_wc = conn.execute(text("""
            INSERT INTO work_centers (name, code, capacity_per_day, cost_per_hour, location, status, cost_center_id, default_expense_account_id)
            VALUES (:name, :code, :cap, :cost, :loc, :status, :ccid, :accid)
            RETURNING *
        """), {
            "name": wc.name, "code": wc.code, "cap": wc.capacity_per_day, 
            "cost": wc.cost_per_hour, "loc": wc.location, "status": wc.status,
            "ccid": wc.cost_center_id, "accid": wc.default_expense_account_id
        }).fetchone()
        conn.commit()
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="create_work_center", resource_type="work_centers",
                     resource_id=str(new_wc.id), details={"name": wc.name, "code": wc.code},
                     request=request)
        return dict(new_wc._mapping)
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating work center: {e}")
        raise HTTPException(status_code=400, detail="فشل في إنشاء مركز العمل")
    finally:
        conn.close()

@router.put("/work-centers/{wc_id}", response_model=WorkCenterResponse, dependencies=[Depends(require_permission("manufacturing.manage"))])
def update_work_center(wc_id: int, wc: WorkCenterCreate, request: Request, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        updated = conn.execute(text("""
            UPDATE work_centers 
            SET name=:name, code=:code, capacity_per_day=:cap, cost_per_hour=:cost, location=:loc, status=:status, 
                cost_center_id=:ccid, default_expense_account_id=:accid, updated_at=NOW()
            WHERE id=:id
            RETURNING *
        """), {
            "name": wc.name, "code": wc.code, "cap": wc.capacity_per_day, 
            "cost": wc.cost_per_hour, "loc": wc.location, "status": wc.status, 
            "ccid": wc.cost_center_id, "accid": wc.default_expense_account_id, "id": wc_id
        }).fetchone()
        if not updated:
            raise HTTPException(status_code=404, detail="Work center not found")
        conn.commit()
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="update_work_center", resource_type="work_centers",
                     resource_id=str(wc_id), details={"name": wc.name},
                     request=request)
        return dict(updated._mapping)
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating work center {wc_id}: {e}")
        raise HTTPException(status_code=400, detail="فشل في تحديث مركز العمل")
    finally:
        conn.close()

# ==========================================
# 2. ROUTINGS
# ==========================================

@router.get("/routes", response_model=List[RouteResponse], dependencies=[Depends(require_permission("manufacturing.view"))])
def list_routes(
    branch_id: Optional[int] = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user),
):
    conn = get_db_connection(current_user.company_id)
    try:
        from utils.permissions import validate_branch_access
        validated_branch = validate_branch_access(current_user, branch_id)

        query = """
            SELECT r.*, p.product_name as product_name
            FROM manufacturing_routes r
            LEFT JOIN products p ON r.product_id = p.id
            WHERE r.is_deleted = false
        """
        params = {}
        if validated_branch:
            query += """
                AND r.product_id IN (
                    SELECT DISTINCT product_id FROM inventory WHERE branch_id = :branch_id
                )
            """
            params["branch_id"] = validated_branch
        query += " ORDER BY r.name LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset
        routes_db = conn.execute(text(query), params).fetchall()
        
        result = []
        for r in routes_db:
            route_dict = dict(r._mapping)
            # Fetch operations
            ops = conn.execute(text("""
                SELECT mo.*, wc.name as work_center_name 
                FROM manufacturing_operations mo
                LEFT JOIN work_centers wc ON mo.work_center_id = wc.id
                WHERE mo.route_id = :rid AND mo.is_deleted = false
                ORDER BY mo.sequence
            """), {"rid": r.id}).fetchall()
            route_dict['operations'] = [dict(op._mapping) for op in ops]
            result.append(route_dict)
            
        return result
    finally:
        conn.close()

@router.post("/routes", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.create"]))])
def create_route(route: RouteCreate, request: Request, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        # Create Header
        new_route = conn.execute(text("""
            INSERT INTO manufacturing_routes (name, product_id, bom_id, is_default, is_active, description)
            VALUES (:name, :pid, :bid, :default, :active, :desc)
            RETURNING *
        """), {
            "name": route.name, "pid": route.product_id,
            "bid": route.bom_id, "default": route.is_default,
            "active": route.is_active, "desc": route.description
        }).fetchone()
        
        # Create Operations
        for op in route.operations:
            conn.execute(text("""
                INSERT INTO manufacturing_operations (route_id, sequence, name, work_center_id, description, setup_time, cycle_time, labor_rate_per_hour)
                VALUES (:rid, :seq, :name, :wcid, :desc, :setup, :cycle, :labor)
            """), {
                "rid": new_route.id, "seq": op.sequence, "name": op.name, "wcid": op.work_center_id,
                "desc": op.description, "setup": op.setup_time, "cycle": op.cycle_time,
                "labor": op.labor_rate_per_hour
            })
            
        trans.commit()
        
        # Re-fetch the newly created route with operations
        route_dict = dict(new_route._mapping)
        ops = conn.execute(text("""
            SELECT mo.*, wc.name as work_center_name 
            FROM manufacturing_operations mo
            LEFT JOIN work_centers wc ON mo.work_center_id = wc.id
            WHERE mo.route_id = :rid AND mo.is_deleted = false
            ORDER BY mo.sequence
        """), {"rid": new_route.id}).fetchall()
        route_dict['operations'] = [dict(op._mapping) for op in ops]
        # Add product_name from join
        if route.product_id:
            prod = conn.execute(text("SELECT product_name FROM products WHERE id = :pid"), {"pid": route.product_id}).fetchone()
            route_dict['product_name'] = prod.product_name if prod else None
        else:
            route_dict['product_name'] = None
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="create_route", resource_type="manufacturing_routes",
                     resource_id=str(new_route.id), details={"name": route.name},
                     request=request)
        return route_dict
    except HTTPException:
        raise
    except Exception as e:
        trans.rollback()
        logger.error(f"Error creating route: {e}")
        raise HTTPException(status_code=400, detail="فشل في إنشاء المسار")
    finally:
        conn.close()

@router.put("/routes/{route_id}", response_model=RouteResponse, dependencies=[Depends(require_permission("manufacturing.manage"))])
def update_route(route_id: int, route: RouteCreate, request: Request, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        existing = conn.execute(text("SELECT * FROM manufacturing_routes WHERE id = :id AND is_deleted = false"), {"id": route_id}).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Route not found")

        conn.execute(text("""
            UPDATE manufacturing_routes SET name=:name, product_id=:pid, bom_id=:bid, is_default=:default, is_active=:active, description=:desc, updated_at=NOW()
            WHERE id=:id
        """), {"name": route.name, "pid": route.product_id, "bid": route.bom_id, "default": route.is_default, "active": route.is_active, "desc": route.description, "id": route_id})

        # Replace operations: delete old ones & insert new
        conn.execute(text("DELETE FROM manufacturing_operations WHERE route_id = :rid"), {"rid": route_id})
        for op in route.operations:
            conn.execute(text("""
                INSERT INTO manufacturing_operations (route_id, sequence, name, work_center_id, description, setup_time, cycle_time, labor_rate_per_hour)
                VALUES (:rid, :seq, :name, :wcid, :desc, :setup, :cycle, :labor)
            """), {"rid": route_id, "seq": op.sequence, "name": op.name, "wcid": op.work_center_id, "desc": op.description, "setup": op.setup_time, "cycle": op.cycle_time, "labor": op.labor_rate_per_hour})

        trans.commit()

        route_row = conn.execute(text("""
            SELECT r.*, p.product_name FROM manufacturing_routes r LEFT JOIN products p ON r.product_id = p.id WHERE r.id = :id AND r.is_deleted = false
        """), {"id": route_id}).fetchone()
        route_dict = dict(route_row._mapping)
        ops = conn.execute(text("""
            SELECT mo.*, wc.name as work_center_name FROM manufacturing_operations mo
            LEFT JOIN work_centers wc ON mo.work_center_id = wc.id WHERE mo.route_id = :rid AND mo.is_deleted = false ORDER BY mo.sequence
        """), {"rid": route_id}).fetchall()
        route_dict['operations'] = [dict(op._mapping) for op in ops]
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="update_route", resource_type="manufacturing_routes",
                     resource_id=str(route_id), details={"name": route.name},
                     request=request)
        return route_dict
    except HTTPException:
        raise
    except Exception as e:
        trans.rollback()
        logger.error(f"Error updating route {route_id}: {e}")
        raise HTTPException(status_code=400, detail="فشل في تحديث المسار")
    finally:
        conn.close()

# ==========================================
# 3. BILL OF MATERIALS (BOM)
# ==========================================

@router.get("/boms", response_model=List[BOMResponse], dependencies=[Depends(require_permission("manufacturing.view"))])
def list_boms(
    branch_id: Optional[int] = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user),
):
    conn = get_db_connection(current_user.company_id)
    try:
        from utils.permissions import validate_branch_access
        validated_branch = validate_branch_access(current_user, branch_id)

        query = """
            SELECT b.*, p.product_name as product_name, r.name as route_name
            FROM bill_of_materials b
            LEFT JOIN products p ON b.product_id = p.id
            LEFT JOIN manufacturing_routes r ON b.route_id = r.id
            WHERE b.is_deleted = false
        """
        params = {}
        if validated_branch:
            query += """
                AND b.product_id IN (
                    SELECT DISTINCT product_id FROM inventory WHERE branch_id = :branch_id
                )
            """
            params["branch_id"] = validated_branch
        query += " ORDER BY b.id DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset
        boms_db = conn.execute(text(query), params).fetchall()
        
        result = []
        for b in boms_db:
            bom_dict = dict(b._mapping)
            # Fetch components
            comps = conn.execute(text("""
                SELECT bc.*, p.product_name as component_name, u.unit_name as component_uom
                FROM bom_components bc
                LEFT JOIN products p ON bc.component_product_id = p.id
                LEFT JOIN product_units u ON p.unit_id = u.id
                WHERE bc.bom_id = :bid AND bc.is_deleted = false
            """), {"bid": b.id}).fetchall()
            bom_dict['components'] = [dict(c._mapping) for c in comps]
            
            # Fetch outputs (by-products)
            outputs = conn.execute(text("""
                SELECT bo.*, p.product_name 
                FROM bom_outputs bo
                LEFT JOIN products p ON bo.product_id = p.id
                WHERE bo.bom_id = :bid AND bo.is_deleted = false
            """), {"bid": b.id}).fetchall()
            bom_dict['outputs'] = [dict(o._mapping) for o in outputs]
            
            result.append(bom_dict)
            
        return result
    finally:
        conn.close()

@router.post("/boms", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.create"]))])
def create_bom(bom: BOMCreate, request: Request, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        new_bom = conn.execute(text("""
            INSERT INTO bill_of_materials (product_id, code, name, yield_quantity, route_id, is_active, notes)
            VALUES (:pid, :code, :name, :yield_q, :rid, :active, :notes)
            RETURNING *
        """), {
            "pid": bom.product_id, "code": bom.code, "name": bom.name,
            "yield_q": bom.yield_quantity, "rid": bom.route_id, 
            "active": bom.is_active, "notes": bom.notes
        }).fetchone()
        
        for comp in bom.components:
            conn.execute(text("""
                INSERT INTO bom_components (bom_id, component_product_id, quantity, waste_percentage, cost_share_percentage, is_percentage, notes)
                VALUES (:bid, :cpid, :qty, :waste, :share, :is_pct, :notes)
            """), {
                "bid": new_bom.id, "cpid": comp.component_product_id,
                "qty": comp.quantity, "waste": comp.waste_percentage,
                "share": comp.cost_share_percentage,
                "is_pct": comp.is_percentage,
                "notes": comp.notes
            })

        for out in bom.outputs:
            conn.execute(text("""
                INSERT INTO bom_outputs (bom_id, product_id, quantity, cost_allocation_percentage, notes)
                VALUES (:bid, :pid, :qty, :share, :notes)
            """), {
                "bid": new_bom.id, "pid": out.product_id,
                "qty": out.quantity, "share": out.cost_allocation_percentage,
                "notes": out.notes
            })
            
        trans.commit()
        # Re-fetch the newly created BOM with its components and outputs
        bom_dict = dict(new_bom._mapping)
        # Add product_name and route_name from joins
        prod_route = conn.execute(text("""
            SELECT p.product_name, r.name as route_name
            FROM bill_of_materials b
            LEFT JOIN products p ON b.product_id = p.id
            LEFT JOIN manufacturing_routes r ON b.route_id = r.id
            WHERE b.id = :bid AND b.is_deleted = false
        """), {"bid": new_bom.id}).fetchone()
        if prod_route:
            bom_dict['product_name'] = prod_route.product_name
            bom_dict['route_name'] = prod_route.route_name
        
        # Fetch components
        comps = conn.execute(text("""
            SELECT bc.*, p.product_name as component_name, u.unit_name as component_uom
            FROM bom_components bc
            LEFT JOIN products p ON bc.component_product_id = p.id
            LEFT JOIN product_units u ON p.unit_id = u.id
            WHERE bc.bom_id = :bid AND bc.is_deleted = false
        """), {"bid": new_bom.id}).fetchall()
        bom_dict['components'] = [dict(c._mapping) for c in comps]
        
        # Fetch outputs
        outputs = conn.execute(text("""
            SELECT bo.*, p.product_name 
            FROM bom_outputs bo
            LEFT JOIN products p ON bo.product_id = p.id
            WHERE bo.bom_id = :bid AND bo.is_deleted = false
        """), {"bid": new_bom.id}).fetchall()
        bom_dict['outputs'] = [dict(o._mapping) for o in outputs]
        
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="create_bom", resource_type="bill_of_materials",
                     resource_id=str(new_bom.id), details={"name": bom.name, "code": bom.code},
                     request=request)
        return bom_dict
    except HTTPException:
        raise
    except Exception as e:
        trans.rollback()
        logger.error(f"Error creating BOM: {e}")
        raise HTTPException(status_code=400, detail="فشل في إنشاء قائمة المواد")
    finally:
        conn.close()

@router.get("/boms/{bom_id}", response_model=BOMResponse, dependencies=[Depends(require_permission("manufacturing.view"))])
def get_bom(bom_id: int, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        b = conn.execute(text("""
            SELECT b.*, p.product_name as product_name, r.name as route_name
            FROM bill_of_materials b
            LEFT JOIN products p ON b.product_id = p.id
            LEFT JOIN manufacturing_routes r ON b.route_id = r.id
            WHERE b.id = :bid AND b.is_deleted = false
        """), {"bid": bom_id}).fetchone()
        if not b:
            raise HTTPException(status_code=404, detail="BOM not found")
        bom_dict = dict(b._mapping)
        comps = conn.execute(text("""
            SELECT bc.*, p.product_name as component_name, u.unit_name as component_uom
            FROM bom_components bc
            LEFT JOIN products p ON bc.component_product_id = p.id
            LEFT JOIN product_units u ON p.unit_id = u.id
            WHERE bc.bom_id = :bid AND bc.is_deleted = false
        """), {"bid": bom_id}).fetchall()
        bom_dict['components'] = [dict(c._mapping) for c in comps]
        outputs = conn.execute(text("""
            SELECT bo.*, p.product_name FROM bom_outputs bo
            LEFT JOIN products p ON bo.product_id = p.id WHERE bo.bom_id = :bid AND bo.is_deleted = false
        """), {"bid": bom_id}).fetchall()
        bom_dict['outputs'] = [dict(o._mapping) for o in outputs]
        return bom_dict
    finally:
        conn.close()

@router.put("/boms/{bom_id}", response_model=BOMResponse, dependencies=[Depends(require_permission("manufacturing.manage"))])
def update_bom(bom_id: int, bom: BOMCreate, request: Request, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        existing = conn.execute(text("SELECT * FROM bill_of_materials WHERE id = :id AND is_deleted = false"), {"id": bom_id}).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="BOM not found")

        conn.execute(text("""
            UPDATE bill_of_materials SET product_id=:pid, code=:code, name=:name, yield_quantity=:yield_q,
                route_id=:rid, is_active=:active, notes=:notes, updated_at=NOW()
            WHERE id=:id
        """), {
            "pid": bom.product_id, "code": bom.code, "name": bom.name,
            "yield_q": bom.yield_quantity, "rid": bom.route_id,
            "active": bom.is_active, "notes": bom.notes, "id": bom_id
        })

        # Replace components
        conn.execute(text("DELETE FROM bom_components WHERE bom_id = :bid"), {"bid": bom_id})
        for comp in bom.components:
            conn.execute(text("""
                INSERT INTO bom_components (bom_id, component_product_id, quantity, waste_percentage, cost_share_percentage, is_percentage, notes)
                VALUES (:bid, :cpid, :qty, :waste, :share, :is_pct, :notes)
            """), {
                "bid": bom_id, "cpid": comp.component_product_id,
                "qty": comp.quantity, "waste": comp.waste_percentage,
                "share": comp.cost_share_percentage, "is_pct": comp.is_percentage, "notes": comp.notes
            })

        # Replace outputs
        conn.execute(text("DELETE FROM bom_outputs WHERE bom_id = :bid"), {"bid": bom_id})
        for out in bom.outputs:
            conn.execute(text("""
                INSERT INTO bom_outputs (bom_id, product_id, quantity, cost_allocation_percentage, notes)
                VALUES (:bid, :pid, :qty, :share, :notes)
            """), {"bid": bom_id, "pid": out.product_id, "qty": out.quantity, "share": out.cost_allocation_percentage, "notes": out.notes})

        trans.commit()

        # Re-fetch with joins
        b = conn.execute(text("""
            SELECT b.*, p.product_name as product_name, r.name as route_name
            FROM bill_of_materials b LEFT JOIN products p ON b.product_id = p.id
            LEFT JOIN manufacturing_routes r ON b.route_id = r.id WHERE b.id = :bid AND b.is_deleted = false
        """), {"bid": bom_id}).fetchone()
        bom_dict = dict(b._mapping)
        comps = conn.execute(text("""
            SELECT bc.*, p.product_name as component_name, u.unit_name as component_uom
            FROM bom_components bc LEFT JOIN products p ON bc.component_product_id = p.id
            LEFT JOIN product_units u ON p.unit_id = u.id WHERE bc.bom_id = :bid AND bc.is_deleted = false
        """), {"bid": bom_id}).fetchall()
        bom_dict['components'] = [dict(c._mapping) for c in comps]
        outputs = conn.execute(text("""
            SELECT bo.*, p.product_name FROM bom_outputs bo
            LEFT JOIN products p ON bo.product_id = p.id WHERE bo.bom_id = :bid AND bo.is_deleted = false
        """), {"bid": bom_id}).fetchall()
        bom_dict['outputs'] = [dict(o._mapping) for o in outputs]
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="update_bom", resource_type="bill_of_materials",
                     resource_id=str(bom_id), details={"name": bom.name},
                     request=request)
        return bom_dict
    except HTTPException:
        raise
    except Exception as e:
        trans.rollback()
        logger.error(f"Error updating BOM {bom_id}: {e}")
        raise HTTPException(status_code=400, detail="فشل في تحديث قائمة المواد")
    finally:
        conn.close()


# ==========================================
# 4. PRODUCTION ORDERS
# ==========================================

# ---- Helper: Calculate Production Cost ----
def calculate_production_cost(conn, bom_id: int, order_quantity: float, order_id: int = None):
    """
    Calculate total production cost breakdown for a production order.
    Returns dict with material_cost, labor_cost, overhead_cost, total_cost, and unit_cost.
    """
    # A. Material Cost (from BOM components × quantity × cost_price)
    total_material_cost = Decimal("0")
    component_details = []
    
    if bom_id:
        components = conn.execute(text("""
            SELECT bc.*, p.cost_price, p.product_name
            FROM bom_components bc
            JOIN products p ON bc.component_product_id = p.id
            WHERE bc.bom_id = :bid AND bc.is_deleted = false
        """), {"bid": bom_id}).fetchall()
        
        for comp in components:
            waste_factor = 1 + Decimal(str(comp.waste_percentage or 0)) / Decimal("100")
            # Handle percentage-based BOM components
            if comp.is_percentage:
                base_qty = Decimal(str(comp.quantity)) / Decimal("100") * Decimal(str(order_quantity))
                required_qty = base_qty * waste_factor
            else:
                required_qty = Decimal(str(comp.quantity)) * Decimal(str(order_quantity)) * waste_factor
            unit_cost = Decimal(str(comp.cost_price or 0))
            line_cost = required_qty * unit_cost
            total_material_cost += line_cost
            component_details.append({
                "product_name": comp.product_name,
                "product_id": comp.component_product_id,
                "base_qty": (Decimal(str(comp.quantity)) / Decimal("100") * Decimal(str(order_quantity))) if comp.is_percentage else Decimal(str(comp.quantity)) * Decimal(str(order_quantity)),
                "waste_qty": required_qty - ((Decimal(str(comp.quantity)) / Decimal("100") * Decimal(str(order_quantity))) if comp.is_percentage else Decimal(str(comp.quantity)) * Decimal(str(order_quantity))),
                "total_qty": required_qty,
                "unit_cost": unit_cost,
                "total_cost": line_cost,
            })
    
    # B. Labor Cost (from production_order_operations × work_center cost_per_hour)
    total_labor_cost = Decimal("0")
    total_overhead_cost = Decimal("0")
    
    if order_id:
        ops_data = conn.execute(text("""
            SELECT poo.actual_run_time, wc.cost_per_hour
            FROM production_order_operations poo
            LEFT JOIN work_centers wc ON poo.work_center_id = wc.id
            WHERE poo.production_order_id = :oid
        """), {"oid": order_id}).fetchall()
        
        for op in ops_data:
            duration_hours = Decimal(str(op.actual_run_time or 0)) / Decimal("60")
            rate = Decimal(str(op.cost_per_hour or 0))
            total_labor_cost += duration_hours * rate
        
        # C. Overhead = configurable percentage of labor cost (default 30%)
        # Read from company_settings if available
        overhead_rate_row = conn.execute(text(
            "SELECT setting_value FROM company_settings WHERE setting_key = 'mfg_overhead_rate'"
        )).fetchone()
        overhead_rate = Decimal(str(overhead_rate_row.setting_value)) if overhead_rate_row else Decimal("0.30")
        total_overhead_cost = total_labor_cost * overhead_rate
    
    total_cost = total_material_cost + total_labor_cost + total_overhead_cost
    unit_cost = total_cost / Decimal(str(order_quantity)) if order_quantity else Decimal("0")
    
    return {
        "material_cost": round(total_material_cost, 2),
        "labor_cost": round(total_labor_cost, 2),
        "overhead_cost": round(total_overhead_cost, 2),
        "total_cost": round(total_cost, 2),
        "unit_cost": round(unit_cost, 4),
        "components": component_details,
    }


# ---- Helper: Check Inventory Sufficiency ----
def check_inventory_sufficiency(conn, bom_id: int, order_quantity: float, warehouse_id: int = None):
    """
    Check if enough raw materials are available in inventory for a production order.
    Returns (is_sufficient: bool, shortages: list).
    """
    if not bom_id:
        return True, []
    
    components = conn.execute(text("""
        SELECT bc.*, p.product_name
        FROM bom_components bc
        JOIN products p ON bc.component_product_id = p.id
        WHERE bc.bom_id = :bid AND bc.is_deleted = false
    """), {"bid": bom_id}).fetchall()
    
    shortages = []
    for comp in components:
        waste_factor = 1 + Decimal(str(comp.waste_percentage or 0)) / Decimal("100")
        # Variable BOM: quantity is a percentage of the order quantity
        base_qty = (Decimal(str(comp.quantity)) / Decimal("100") * Decimal(str(order_quantity))) if comp.is_percentage else Decimal(str(comp.quantity))
        required_qty = base_qty * Decimal(str(order_quantity)) * waste_factor if not comp.is_percentage else base_qty * waste_factor
        
        # Check available quantity
        if warehouse_id:
            inv = conn.execute(text("""
                SELECT COALESCE(quantity, 0) as qty FROM inventory 
                WHERE product_id = :pid AND warehouse_id = :whid
            """), {"pid": comp.component_product_id, "whid": warehouse_id}).fetchone()
        else:
            inv = conn.execute(text("""
                SELECT COALESCE(SUM(quantity), 0) as qty FROM inventory 
                WHERE product_id = :pid
            """), {"pid": comp.component_product_id}).fetchone()
        
        available = Decimal(str(inv.qty)) if inv else Decimal("0")
        
        if available < required_qty:
            shortages.append({
                "product_id": comp.component_product_id,
                "product_name": comp.product_name,
                "required": round(required_qty, 4),
                "available": round(available, 4),
                "shortage": round(required_qty - available, 4),
            })
    
    return len(shortages) == 0, shortages


@router.get("/orders/cost-estimate", dependencies=[Depends(require_permission("manufacturing.view"))])
def estimate_production_cost(
    bom_id: int = Query(..., description="BOM ID"),
    quantity: float = Query(..., description="Production quantity"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Estimate production cost before creating an order."""
    conn = get_db_connection(current_user.company_id)
    try:
        bom = conn.execute(text("SELECT * FROM bill_of_materials WHERE id = :bid AND is_deleted = false"), {"bid": bom_id}).fetchone()
        if not bom:
            raise HTTPException(status_code=404, detail="BOM not found")
        cost = calculate_production_cost(conn, bom_id, quantity)
        return cost
    finally:
        conn.close()


@router.get("/orders/check-materials", dependencies=[Depends(require_permission("manufacturing.view"))])
def check_materials_availability(
    bom_id: int = Query(..., description="BOM ID"),
    quantity: float = Query(..., description="Production quantity"),
    warehouse_id: Optional[int] = Query(None, description="Source warehouse ID"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Check if enough raw materials are available for production."""
    conn = get_db_connection(current_user.company_id)
    try:
        is_sufficient, shortages = check_inventory_sufficiency(conn, bom_id, quantity, warehouse_id)
        return {"is_sufficient": is_sufficient, "shortages": shortages}
    finally:
        conn.close()

@router.get("/orders", response_model=List[ProductionOrderResponse], dependencies=[Depends(require_permission("manufacturing.view"))])
def list_production_orders(
    branch_id: Optional[int] = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user)
):
    from utils.permissions import validate_branch_access
    validated_branch = validate_branch_access(current_user, branch_id)
    conn = get_db_connection(current_user.company_id)
    try:
        query = """
            SELECT po.*, p.product_name as product_name, b.name as bom_name,
                   po.order_number, po.status, po.produced_quantity, po.scrapped_quantity, po.created_at
            FROM production_orders po
            LEFT JOIN products p ON po.product_id = p.id
            LEFT JOIN bill_of_materials b ON po.bom_id = b.id
        """
        params = {"limit": limit, "offset": offset}
        if validated_branch:
            query += " WHERE po.branch_id = :branch_id"
            params["branch_id"] = validated_branch
        query += " ORDER BY po.id DESC LIMIT :limit OFFSET :offset"
        orders_db = conn.execute(text(query), params).fetchall()

        result = []
        for o in orders_db:
            order_dict = dict(o._mapping)
            # Fetch operations status
            ops = conn.execute(text("""
                SELECT poo.*, mo.description as operation_description
                FROM production_order_operations poo
                LEFT JOIN manufacturing_operations mo ON poo.operation_id = mo.id
                WHERE poo.production_order_id = :poid
                ORDER BY mo.sequence
            """), {"poid": o.id}).fetchall()
            order_dict['operations'] = [dict(op._mapping) for op in ops]
            result.append(order_dict)

        return result
    finally:
        conn.close()
 
@router.get("/orders/{order_id}", response_model=ProductionOrderResponse, dependencies=[Depends(require_permission("manufacturing.view"))])
def get_production_order(order_id: int, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        o = conn.execute(text("""
            SELECT po.*, p.product_name as product_name, b.name as bom_name
            FROM production_orders po
            LEFT JOIN products p ON po.product_id = p.id
            LEFT JOIN bill_of_materials b ON po.bom_id = b.id
            WHERE po.id = :oid
        """), {"oid": order_id}).fetchone()
        
        if not o:
            raise HTTPException(status_code=404, detail="Order not found")
        from utils.permissions import validate_branch_access
        if o.branch_id:
            validate_branch_access(current_user, o.branch_id)
            
        order_dict = dict(o._mapping)
        
        # Fetch operations
        ops = conn.execute(text("""
            SELECT poo.*, mo.description as operation_description, wc.name as work_center_name, wc.cost_per_hour
            FROM production_order_operations poo
            LEFT JOIN manufacturing_operations mo ON poo.operation_id = mo.id
            LEFT JOIN work_centers wc ON poo.work_center_id = wc.id
            WHERE poo.production_order_id = :poid
            ORDER BY mo.sequence
        """), {"poid": order_id}).fetchall()
        order_dict['operations'] = [dict(op._mapping) for op in ops]
        
        # Calculate Labor & Overhead Cost
        total_labor_cost = 0
        for op in ops:
            duration_hours = (op.actual_run_time or 0) / 60.0
            rate = op.cost_per_hour or 0
            total_labor_cost += (duration_hours * rate)
            
        order_dict['total_labor_overhead_cost'] = total_labor_cost
        
        # Calculate Material Cost (from transactions if exists, else estimate from BOM)
        mat_cost_query = conn.execute(text("""
            SELECT SUM(ABS(quantity) * unit_cost) 
            FROM inventory_transactions 
            WHERE reference_type = 'production_order' AND reference_id = :oid AND transaction_type = 'production_out'
        """), {"oid": order_id}).scalar()
        
        current_material_cost = mat_cost_query or 0
        
        # If 0 (maybe draft), estimate from BOM
        if current_material_cost == 0 and o.status == 'draft':
             bom_cost = conn.execute(text("""
                SELECT SUM(bc.quantity * p.cost_price)
                FROM bom_components bc
                JOIN products p ON bc.component_product_id = p.id
                WHERE bc.bom_id = :bid AND bc.is_deleted = false
             """), {"bid": o.bom_id}).scalar()
             current_material_cost = (bom_cost or 0) * o.quantity

        order_dict['total_material_cost'] = current_material_cost
        order_dict['unit_production_cost'] = (current_material_cost + total_labor_cost) / (o.quantity or 1)
        
        return order_dict
    finally:
        conn.close()

@router.get("/operations", response_model=List[ProductionOrderOperationResponse], dependencies=[Depends(require_permission("manufacturing.view"))])
def list_all_operations(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    work_center_id: Optional[int] = None,
    status: Optional[str] = None,
    branch_id: Optional[int] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    conn = get_db_connection(current_user.company_id)
    try:
        from utils.permissions import validate_branch_access
        validated_branch = validate_branch_access(current_user, branch_id)

        query = """
            SELECT poo.*, mo.description as operation_description, wc.name as work_center_name,
                   po.order_number, p.product_name
            FROM production_order_operations poo
            JOIN production_orders po ON poo.production_order_id = po.id
            LEFT JOIN manufacturing_operations mo ON poo.operation_id = mo.id
            LEFT JOIN work_centers wc ON poo.work_center_id = wc.id
            LEFT JOIN products p ON po.product_id = p.id
            WHERE 1=1
        """
        params = {}
        
        if validated_branch:
            query += " AND po.branch_id = :branch_id"
            params["branch_id"] = validated_branch
        
        if work_center_id:
            query += " AND poo.work_center_id = :wcid"
            params["wcid"] = work_center_id
            
        if status:
            query += " AND poo.status = :status"
            params["status"] = status
            
        # Filter by Planned Date (using planned_start_date if available, or just filtering logic)
        # Note: We assume planned_start_date exists in production_order_operations table.
        if start_date:
            query += " AND (poo.planned_start_time >= :start_date OR po.start_date >= :start_date)"
            params["start_date"] = start_date
            
        if end_date:
            query += " AND (poo.planned_end_time <= :end_date OR po.due_date <= :end_date)"
            params["end_date"] = end_date

        query += " ORDER BY poo.planned_start_time ASC, po.id ASC"
        
        ops = conn.execute(text(query), params).fetchall()
        return [dict(op._mapping) for op in ops]
    finally:
        conn.close()

@router.post("/orders", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.create"]))])
def create_production_order(order: ProductionOrderCreate, request: Request, current_user: UserResponse = Depends(get_current_user)):
    from utils.permissions import validate_branch_access
    if order.warehouse_id:
        conn_pre = get_db_connection(current_user.company_id)
        try:
            wh = conn_pre.execute(text("SELECT branch_id FROM warehouses WHERE id = :wid"), {"wid": order.warehouse_id}).fetchone()
            if wh and wh.branch_id:
                validate_branch_access(current_user, wh.branch_id)
        finally:
            conn_pre.close()
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        # Generate Order Number if not provided
        if not order.order_number:
            order.order_number = f"PO-{datetime.now().strftime('%y%m%d%H%M%S')}"

        # Auto-detect default routing if route_id not provided
        route_id = order.route_id
        if not route_id and order.product_id:
            default_route = conn.execute(text("""
                SELECT id FROM manufacturing_routes
                WHERE product_id = :pid AND is_active = true AND is_deleted = false
                ORDER BY is_default DESC, id ASC
                LIMIT 1
            """), {"pid": order.product_id}).fetchone()
            if default_route:
                route_id = default_route.id

        # 1. Create Order Header
        new_order = conn.execute(text("""
            INSERT INTO production_orders (order_number, product_id, bom_id, route_id, quantity, 
                                         status, start_date, due_date, warehouse_id, destination_warehouse_id, notes, created_by)
            VALUES (:num, :pid, :bid, :rid, :qty, :status, :start, :due, :whid, :dwhid, :notes, :uid)
            RETURNING *
        """), {
            "num": order.order_number, "pid": order.product_id, "bid": order.bom_id,
            "rid": route_id, "qty": order.quantity, "status": order.status or 'draft',
            "start": order.start_date, "due": order.due_date, 
            "whid": order.warehouse_id, "dwhid": order.destination_warehouse_id,
            "notes": order.notes, "uid": current_user.id
        }).fetchone()
        new_order_id = new_order.id

        # 2. Create Order Operations (Copy from Route) & calculate labor cost
        total_labor_cost = Decimal("0")
        if route_id:
            route_ops = conn.execute(text("""
                SELECT * FROM manufacturing_operations WHERE route_id = :rid AND is_deleted = false ORDER BY sequence
            """), {"rid": route_id}).fetchall()

            for op in route_ops:
                conn.execute(text("""
                    INSERT INTO production_order_operations (production_order_id, operation_id, work_center_id, status, sequence)
                    VALUES (:poid, :opid, :wcid, 'pending', :seq)
                """), {
                    "poid": new_order_id, "opid": op.id, "wcid": op.work_center_id, "seq": op.sequence
                })
                # Calculate labor cost: (setup_time + cycle_time * qty) / 60 * labor_rate
                setup = Decimal(str(op.setup_time or 0))
                run = Decimal(str(op.cycle_time or 0)) * Decimal(str(order.quantity))
                rate = Decimal(str(getattr(op, 'labor_rate_per_hour', 0) or 0))
                total_labor_cost += ((setup + run) / Decimal("60")) * rate

            # Update standard labor cost on the order
            if total_labor_cost > 0:
                conn.execute(text("""
                    UPDATE production_orders
                    SET actual_labor_cost = :lc
                    WHERE id = :oid
                """), {"lc": round(total_labor_cost, 4), "oid": new_order_id})

        trans.commit()
        
        # Re-fetch for response
        # Using the same logic as list_production_orders but for single ID
        # ... or just calling list structure. 
        # For simplicity, returning the created object with empty operations if correct, 
        # but better to re-query to match response model fields like product_name which are joins.
        
        # Re-query
        o = conn.execute(text("""
            SELECT po.*, p.product_name as product_name, b.name as bom_name
            FROM production_orders po
            LEFT JOIN products p ON po.product_id = p.id
            LEFT JOIN bill_of_materials b ON po.bom_id = b.id
            WHERE po.id = :oid
        """), {"oid": new_order_id}).fetchone()
        
        order_dict = dict(o._mapping)
        
        ops = conn.execute(text("""
            SELECT poo.*, mo.description as operation_description
            FROM production_order_operations poo
            LEFT JOIN manufacturing_operations mo ON poo.operation_id = mo.id
            WHERE poo.production_order_id = :poid
            ORDER BY mo.sequence
        """), {"poid": new_order_id}).fetchall()
        order_dict['operations'] = [dict(op._mapping) for op in ops]
        
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="create_production_order", resource_type="production_orders",
                     resource_id=str(new_order_id),
                     details={"order_number": order.order_number, "product_id": order.product_id, "quantity": float(order.quantity)},
                     request=request)
        return order_dict

    except HTTPException:
        raise
    except Exception as e:
        trans.rollback()
        logger.error(f"Error creating production order: {e}")
        raise HTTPException(status_code=400, detail="فشل في إنشاء أمر الإنتاج")
    finally:
        conn.close()

@router.post("/orders/{order_id}/start", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.create"]))])
def start_production_order(order_id: int, request: Request, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        # Check current status
        order = conn.execute(text("""
            SELECT po.*, p.cost_price as product_cost 
            FROM production_orders po
            LEFT JOIN products p ON po.product_id = p.id
            WHERE po.id=:id
        """), {"id": order_id}).fetchone()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        from utils.permissions import validate_branch_access
        if order.branch_id:
            validate_branch_access(current_user, order.branch_id)
        
        if order.status not in ['draft', 'confirmed']:
            logger.warning(f"Cannot start order {order_id} with status {order.status}")
            raise HTTPException(status_code=400, detail="لا يمكن بدء الأمر في حالته الحالية")

        # Check inventory sufficiency before starting
        if order.bom_id:
            is_sufficient, shortages = check_inventory_sufficiency(
                conn, order.bom_id, order.quantity, order.warehouse_id
            )
            if not is_sufficient:
                shortage_details = "; ".join(
                    f"{s['product_name']}: need {s['required']}, have {s['available']} (short {s['shortage']})"
                    for s in shortages
                )
                logger.warning(f"Insufficient raw materials for order {order_id}: {shortage_details}")
                raise HTTPException(
                    status_code=400, 
                    detail="المواد الخام غير كافية لبدء أمر الإنتاج"
                )

        # Update status to in_progress
        updated = conn.execute(text("""
            UPDATE production_orders 
            SET status='in_progress', start_date=CURRENT_DATE
            WHERE id=:id
            RETURNING *
        """), {"id": order_id}).fetchone()
        
        # 1. Consume Raw Materials
        # Get BOM components
        if order.bom_id:
            components = conn.execute(text("""
                SELECT bc.*, p.cost_price, p.product_name, p.id as product_id
                FROM bom_components bc
                JOIN products p ON bc.component_product_id = p.id
                WHERE bc.bom_id = :bid AND bc.is_deleted = false
            """), {"bid": order.bom_id}).fetchall()
            
            total_material_cost = Decimal("0")
            
            for comp in components:
                waste_factor = 1 + Decimal(str(comp.waste_percentage or 0)) / Decimal("100")
                # Variable BOM: quantity is % of order quantity
                if comp.is_percentage:
                    required_qty = (Decimal(str(comp.quantity)) / Decimal("100") * Decimal(str(order.quantity))) * waste_factor
                else:
                    required_qty = Decimal(str(comp.quantity)) * Decimal(str(order.quantity)) * waste_factor
                cost = required_qty * Decimal(str(comp.cost_price or 0))
                total_material_cost += cost
                
                # Deduct from Source Warehouse
                if order.warehouse_id:
                    # Update Inventory Level
                    conn.execute(text("""
                        INSERT INTO inventory (warehouse_id, product_id, quantity, updated_at)
                        VALUES (:whid, :pid, -:qty, NOW())
                        ON CONFLICT (warehouse_id, product_id) 
                        DO UPDATE SET quantity = inventory.quantity - :qty, updated_at = NOW()
                    """), {"whid": order.warehouse_id, "pid": comp.product_id, "qty": required_qty})
                    
                    # Create Transaction
                    conn.execute(text("""
                        INSERT INTO inventory_transactions 
                        (product_id, warehouse_id, transaction_type, quantity, reference_id, reference_type, notes, created_by)
                        VALUES (:pid, :whid, 'production_out', :qty, :ref, 'production_order', :notes, :uid)
                    """), {
                        "pid": comp.product_id, "whid": order.warehouse_id, "qty": -required_qty,
                        "ref": order_id, "notes": f"Consumed for Order {order.order_number}", "uid": current_user.id
                    })

            # 2. Journal Entry (WIP)
            # Find accounts from mappings
            settings_res = conn.execute(text("SELECT setting_key, setting_value FROM company_settings WHERE setting_key IN ('acc_map_wip', 'acc_map_raw_materials', 'acc_map_inventory')")).fetchall()
            settings = {s.setting_key: s.setting_value for s in settings_res}
            
            wip_acc_id = settings.get('acc_map_wip')
            rm_acc_id = settings.get('acc_map_raw_materials') or settings.get('acc_map_inventory')
            
            if wip_acc_id and rm_acc_id and total_material_cost > 0:
                # Validate fiscal period is open before creating GL entry
                check_fiscal_period_open(conn, date.today())

                # TASK-015: route through centralized GL service
                create_journal_entry(
                    db=conn,
                    company_id=current_user.company_id,
                    date=date.today().isoformat(),
                    description=f"Material Consumption for Production Order {order.order_number}",
                    lines=[
                        {"account_id": int(wip_acc_id), "debit": total_material_cost, "credit": 0,
                         "description": "WIP - Material Consumption"},
                        {"account_id": int(rm_acc_id), "debit": 0, "credit": total_material_cost,
                         "description": "Raw Material Inventory"},
                    ],
                    user_id=current_user.id,
                    reference=order.order_number,
                    status="posted",
                    currency=get_base_currency(conn),
                    source="ProductionStart",
                    source_id=order_id,
                    username=getattr(current_user, "username", None),
                    idempotency_key=f"mfg-start-{order_id}",
                )

        trans.commit()

        # Audit log
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="start_production", resource_type="production_orders",
                     resource_id=str(order_id),
                     details={"material_cost": total_material_cost},
                     request=request)

        # Re-fetch full object
        o = conn.execute(text("""
            SELECT po.*, p.product_name as product_name, b.name as bom_name
            FROM production_orders po
            LEFT JOIN products p ON po.product_id = p.id
            LEFT JOIN bill_of_materials b ON po.bom_id = b.id
            WHERE po.id = :oid
        """), {"oid": order_id}).fetchone()
        
        order_dict = dict(o._mapping)
        order_dict['operations'] = [] 
        return order_dict
        
    except HTTPException:
        raise
    except Exception as e:
        trans.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(400, "invalid_data"))
    finally:
        conn.close()

@router.post("/orders/{order_id}/complete", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.create"]))])
def complete_production_order(order_id: int, request: Request, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        # Check current status
        order = conn.execute(text("""
            SELECT po.*, p.cost_price as product_cost, b.yield_quantity,
                   wc.cost_per_hour, wc.default_expense_account_id as overhead_account_id
            FROM production_orders po
            LEFT JOIN products p ON po.product_id = p.id
            LEFT JOIN bill_of_materials b ON po.bom_id = b.id
            LEFT JOIN manufacturing_routes mr ON po.route_id = mr.id 
            -- Assuming primary WC for overhead/labor rate simplification, 
            -- ideally should sum from operations. For now getting rate from first op's WC or Order's WC if exists
            LEFT JOIN manufacturing_operations mo ON mr.id = mo.route_id AND mo.sequence = 1
            LEFT JOIN work_centers wc ON mo.work_center_id = wc.id
            WHERE po.id=:id
        """), {"id": order_id}).fetchone()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        from utils.permissions import validate_branch_access
        if order.branch_id:
            validate_branch_access(current_user, order.branch_id)
        
        if order.status != 'in_progress':
            logger.warning(f"Cannot complete order {order_id} with status {order.status}")
            raise HTTPException(status_code=400, detail="لا يمكن إكمال الأمر في حالته الحالية")

        # Update status to completed
        updated = conn.execute(text("""
            UPDATE production_orders 
            SET status='completed', produced_quantity=quantity, updated_at=NOW()
            WHERE id=:id
            RETURNING *
        """), {"id": order_id}).fetchone()
        
        # 1. Add Finished Goods to Destination Warehouse
        if order.destination_warehouse_id:
            # Update Inventory Level (Main Product)
            conn.execute(text("""
                INSERT INTO inventory (warehouse_id, product_id, quantity, updated_at)
                VALUES (:whid, :pid, :qty, NOW())
                ON CONFLICT (warehouse_id, product_id) 
                DO UPDATE SET quantity = inventory.quantity + :qty, updated_at = NOW()
            """), {"whid": order.destination_warehouse_id, "pid": order.product_id, "qty": order.quantity})
            
            # Create Transaction (Main Product)
            conn.execute(text("""
                INSERT INTO inventory_transactions 
                (product_id, warehouse_id, transaction_type, quantity, reference_id, reference_type, notes, created_by)
                VALUES (:pid, :whid, 'production_in', :qty, :ref, 'production_order', :notes, :uid)
            """), {
                "pid": order.product_id, "whid": order.destination_warehouse_id, "qty": order.quantity,
                "ref": order_id, "notes": f"Production Receipt for Order {order.order_number}", "uid": current_user.id
            })

            # 1.b Handle By-products (BOM Outputs)
            if order.bom_id:
                by_products = conn.execute(text("SELECT * FROM bom_outputs WHERE bom_id = :bid AND is_deleted = false"), {"bid": order.bom_id}).fetchall()
                for bp in by_products:
                    bp_qty = bp.quantity * order.quantity
                    # Add to stock
                    conn.execute(text("""
                        INSERT INTO inventory (warehouse_id, product_id, quantity, updated_at)
                        VALUES (:whid, :pid, :qty, NOW())
                        ON CONFLICT (warehouse_id, product_id) 
                        DO UPDATE SET quantity = inventory.quantity + :qty, updated_at = NOW()
                    """), {"whid": order.destination_warehouse_id, "pid": bp.product_id, "qty": bp_qty})
                    
                    # Transaction
                    conn.execute(text("""
                        INSERT INTO inventory_transactions 
                        (product_id, warehouse_id, transaction_type, quantity, reference_id, reference_type, notes, created_by)
                        VALUES (:pid, :whid, 'production_in', :qty, :ref, 'production_order', :notes, :uid)
                    """), {
                        "pid": bp.product_id, "whid": order.destination_warehouse_id, "qty": bp_qty,
                        "ref": order_id, "notes": f"By-product Receipt for Order {order.order_number}", "uid": current_user.id
                    })

        # 2. Journal Entry (FG Capitalization)
        # Calculate Costs
        
        # A. Material Cost
        total_material_cost = Decimal("0")
        if order.bom_id:
            components = conn.execute(text("""
                SELECT bc.*, p.cost_price 
                FROM bom_components bc
                JOIN products p ON bc.component_product_id = p.id
                WHERE bc.bom_id = :bid AND bc.is_deleted = false
            """), {"bid": order.bom_id}).fetchall()
            
            for comp in components:
                waste_factor = 1 + Decimal(str(comp.waste_percentage or 0)) / Decimal("100")
                # Handle percentage-based BOM components
                if comp.is_percentage:
                    base_qty = Decimal(str(comp.quantity)) / Decimal("100") * Decimal(str(order.quantity))
                    required_qty = base_qty * waste_factor
                else:
                    required_qty = Decimal(str(comp.quantity)) * Decimal(str(order.quantity)) * waste_factor
                total_material_cost += (required_qty * Decimal(str(comp.cost_price or 0)))

        # B. Labor & Overhead Cost
        # Calculate actual run time from operations
        # Calculate actual run time from operations joined with work centers for cost
        ops_costs = conn.execute(text("""
            SELECT SUM((poo.actual_run_time / 60.0) * COALESCE(wc.cost_per_hour, 0)) as total_cost
            FROM production_order_operations poo
            LEFT JOIN work_centers wc ON poo.work_center_id = wc.id
            WHERE poo.production_order_id = :oid
        """), {"oid": order_id}).fetchone()
        
        total_labor_overhead_cost = Decimal(str(ops_costs.total_cost or 0))
        
        total_production_cost = total_material_cost + total_labor_overhead_cost
        
        # Debit: Inventory (FG)
        # Credit: WIP
        settings_res = conn.execute(text("SELECT setting_key, setting_value FROM company_settings WHERE setting_key IN ('acc_map_wip', 'acc_map_finished_goods', 'acc_map_inventory', 'acc_map_labor_cost', 'acc_map_mfg_overhead')")).fetchall()
        settings = {s.setting_key: s.setting_value for s in settings_res}
        
        wip_acc_id = settings.get('acc_map_wip')
        fg_acc_id = settings.get('acc_map_finished_goods') or settings.get('acc_map_inventory')
        
        # Credit Accounts for Labor/Overhead absorption (Contra-expense or Liability)
        # Using a simplistic approach: Credit a "Manufacturing Absorbed Costs" account or Payroll
        # For this phase, we credit WIP for the total transfer to FG, 
        # BUT we also need to Debit WIP and Credit Labor/Overhead for the added value FIRST.
        
        labor_absorption_acc_id = settings.get('acc_map_labor_cost') # e.g., Payroll Payable or Absorbed Labor
        overhead_absorption_acc_id = settings.get('acc_map_mfg_overhead') # e.g., Factory Overhead Absorption

        if wip_acc_id and fg_acc_id and total_production_cost > 0:
            # Validate fiscal period is open before creating GL entry
            check_fiscal_period_open(conn, date.today())

            # TASK-015: centralized GL posting — build single balanced JE
            je_lines = []
            absorb_acc = None
            if total_labor_overhead_cost > 0 and (labor_absorption_acc_id or overhead_absorption_acc_id):
                absorb_acc = labor_absorption_acc_id or overhead_absorption_acc_id
                if absorb_acc:
                    je_lines.append({"account_id": int(wip_acc_id),
                                     "debit": total_labor_overhead_cost, "credit": 0,
                                     "description": "WIP - Labor & Overhead Absorption"})
                    je_lines.append({"account_id": int(absorb_acc),
                                     "debit": 0, "credit": total_labor_overhead_cost,
                                     "description": "Absorbed Manufacturing Costs"})

            je_lines.append({"account_id": int(fg_acc_id),
                             "debit": total_production_cost, "credit": 0,
                             "description": "Finished Goods Inventory"})
            je_lines.append({"account_id": int(wip_acc_id),
                             "debit": 0, "credit": total_production_cost,
                             "description": "WIP - FG Transfer"})

            create_journal_entry(
                db=conn,
                company_id=current_user.company_id,
                date=date.today().isoformat(),
                description=(
                    f"Production Completion (Mat: {total_material_cost}, "
                    f"Lab/OH: {total_labor_overhead_cost})"
                ),
                lines=je_lines,
                user_id=current_user.id,
                reference=order.order_number,
                status="posted",
                currency=get_base_currency(conn),
                source="ProductionComplete",
                source_id=order_id,
                username=getattr(current_user, "username", None),
                idempotency_key=f"mfg-complete-{order_id}",
            )

        # 3. Update product cost_price using Weighted Average Cost (WAC)
        if order.quantity and total_production_cost > 0:
            new_unit_cost = total_production_cost / order.quantity
            # WAC: (existing_qty × old_cost + new_qty × new_cost) / (existing_qty + new_qty)
            existing = conn.execute(text("""
                SELECT COALESCE(SUM(quantity), 0) as qty FROM inventory 
                WHERE product_id = :pid
            """), {"pid": order.product_id}).fetchone()
            existing_qty = Decimal(str(existing.qty)) - Decimal(str(order.quantity))  # subtract newly added qty
            old_cost_row = conn.execute(text(
                "SELECT cost_price FROM products WHERE id = :pid"
            ), {"pid": order.product_id}).fetchone()
            old_cost = Decimal(str(old_cost_row.cost_price or 0)) if old_cost_row else Decimal("0")
            
            if existing_qty + Decimal(str(order.quantity)) > 0:
                wac = (existing_qty * old_cost + Decimal(str(order.quantity)) * new_unit_cost) / (existing_qty + Decimal(str(order.quantity)))
            else:
                wac = new_unit_cost
            
            conn.execute(text("""
                UPDATE products SET cost_price = :cost, updated_at = NOW() WHERE id = :pid
            """), {"cost": round(wac, 4), "pid": order.product_id})

        trans.commit()

        # Audit log
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="complete_production", resource_type="production_orders",
                     resource_id=str(order_id),
                     details={"quantity": float(order.quantity), "total_cost": total_production_cost},
                     request=request)

        # Re-fetch full object
        o = conn.execute(text("""
            SELECT po.*, p.product_name as product_name, b.name as bom_name
            FROM production_orders po
            LEFT JOIN products p ON po.product_id = p.id
            LEFT JOIN bill_of_materials b ON po.bom_id = b.id
            WHERE po.id = :oid
        """), {"oid": order_id}).fetchone()
        
        order_dict = dict(o._mapping)
        order_dict['operations'] = [] 
        return order_dict
        
    except HTTPException:
        raise
    except Exception as e:
        trans.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(400, "invalid_data"))
    finally:
        conn.close()


# ---- Cancel / Delete / Update Production Orders ----

@router.post("/orders/{order_id}/cancel", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.create"]))])
def cancel_production_order(order_id: int, request: Request, current_user: UserResponse = Depends(get_current_user)):
    """Cancel a production order. Only draft/confirmed orders can be cancelled."""
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        order = conn.execute(text("""
            SELECT po.*, p.product_name as product_name, b.name as bom_name
            FROM production_orders po
            LEFT JOIN products p ON po.product_id = p.id
            LEFT JOIN bill_of_materials b ON po.bom_id = b.id
            WHERE po.id = :id
        """), {"id": order_id}).fetchone()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        from utils.permissions import validate_branch_access
        if order.branch_id:
            validate_branch_access(current_user, order.branch_id)
        
        if order.status not in ['draft', 'confirmed']:
            logger.warning(f"Cannot cancel order {order_id} with status {order.status}")
            raise HTTPException(status_code=400, detail="لا يمكن إلغاء الأمر في حالته الحالية")
        
        conn.execute(text("""
            UPDATE production_orders SET status = 'cancelled', updated_at = NOW() WHERE id = :id
        """), {"id": order_id})
        
        trans.commit()
        
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="cancel_production_order", resource_type="production_orders",
                     resource_id=str(order_id), details={"order_number": order.order_number},
                     request=request)
        updated = conn.execute(text("""
            SELECT po.*, p.product_name as product_name, b.name as bom_name
            FROM production_orders po
            LEFT JOIN products p ON po.product_id = p.id
            LEFT JOIN bill_of_materials b ON po.bom_id = b.id
            WHERE po.id = :id
        """), {"id": order_id}).fetchone()
        order_dict = dict(updated._mapping)
        order_dict['operations'] = []
        return order_dict
    except HTTPException:
        raise
    except Exception as e:
        trans.rollback()
        logger.error(f"Error cancelling production order {order_id}: {e}")
        raise HTTPException(status_code=400, detail="فشل في إلغاء أمر الإنتاج")
    finally:
        conn.close()


@router.delete("/orders/{order_id}", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.delete"]))])
def delete_production_order(order_id: int, request: Request, current_user: UserResponse = Depends(get_current_user)):
    """Delete a production order. Only draft orders can be deleted."""
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        order = conn.execute(text("SELECT * FROM production_orders WHERE id = :id"), {"id": order_id}).fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        from utils.permissions import validate_branch_access
        if order.branch_id:
            validate_branch_access(current_user, order.branch_id)
        if order.status != 'draft':
            raise HTTPException(status_code=400, detail="Only draft orders can be deleted")
        
        # Delete operations first (cascade should handle, but be explicit)
        conn.execute(text("DELETE FROM production_order_operations WHERE production_order_id = :id"), {"id": order_id})
        conn.execute(text("DELETE FROM production_orders WHERE id = :id"), {"id": order_id})
        
        trans.commit()
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="delete_production_order", resource_type="production_orders",
                     resource_id=str(order_id), request=request)
        return {"message": "Production order deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        trans.rollback()
        logger.error(f"Error deleting production order {order_id}: {e}")
        raise HTTPException(status_code=400, detail="فشل في حذف أمر الإنتاج")
    finally:
        conn.close()


@router.put("/orders/{order_id}", response_model=ProductionOrderResponse, dependencies=[Depends(require_permission("manufacturing.manage"))])
def update_production_order(order_id: int, order: ProductionOrderCreate, request: Request, current_user: UserResponse = Depends(get_current_user)):
    """Update a production order. Only draft orders can be updated."""
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        existing = conn.execute(text("SELECT * FROM production_orders WHERE id = :id"), {"id": order_id}).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Order not found")
        from utils.permissions import validate_branch_access
        if existing.branch_id:
            validate_branch_access(current_user, existing.branch_id)
        if existing.status != 'draft':
            raise HTTPException(status_code=400, detail="Only draft orders can be updated")
        
        updated = conn.execute(text("""
            UPDATE production_orders 
            SET product_id = :pid, bom_id = :bid, route_id = :rid, quantity = :qty,
                start_date = :start, due_date = :due, warehouse_id = :whid, 
                destination_warehouse_id = :dwhid, notes = :notes, updated_at = NOW()
            WHERE id = :id
            RETURNING *
        """), {
            "pid": order.product_id, "bid": order.bom_id, "rid": order.route_id,
            "qty": order.quantity, "start": order.start_date, "due": order.due_date,
            "whid": order.warehouse_id, "dwhid": order.destination_warehouse_id,
            "notes": order.notes, "id": order_id
        }).fetchone()
        
        if not updated:
            raise HTTPException(status_code=500, detail="Update failed")
        
        # Re-create operations from new route if route changed
        if order.route_id and order.route_id != existing.route_id:
            conn.execute(text("DELETE FROM production_order_operations WHERE production_order_id = :id"), {"id": order_id})
            route_ops = conn.execute(text("""
                SELECT * FROM manufacturing_operations WHERE route_id = :rid AND is_deleted = false ORDER BY sequence
            """), {"rid": order.route_id}).fetchall()
            for op in route_ops:
                conn.execute(text("""
                    INSERT INTO production_order_operations (production_order_id, operation_id, work_center_id, status)
                    VALUES (:poid, :opid, :wcid, 'pending')
                """), {"poid": order_id, "opid": op.id, "wcid": op.work_center_id})
        
        trans.commit()
        
        # Re-fetch with joins
        o = conn.execute(text("""
            SELECT po.*, p.product_name as product_name, b.name as bom_name
            FROM production_orders po
            LEFT JOIN products p ON po.product_id = p.id
            LEFT JOIN bill_of_materials b ON po.bom_id = b.id
            WHERE po.id = :oid
        """), {"oid": order_id}).fetchone()
        order_dict = dict(o._mapping)
        
        ops = conn.execute(text("""
            SELECT poo.*, mo.description as operation_description
            FROM production_order_operations poo
            LEFT JOIN manufacturing_operations mo ON poo.operation_id = mo.id
            WHERE poo.production_order_id = :poid
            ORDER BY mo.sequence
        """), {"poid": order_id}).fetchall()
        order_dict['operations'] = [dict(op._mapping) for op in ops]
        
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="update_production_order", resource_type="production_orders",
                     resource_id=str(order_id), details={"quantity": float(order.quantity)},
                     request=request)
        return order_dict
    except HTTPException:
        raise
    except Exception as e:
        trans.rollback()
        logger.error(f"Error updating production order {order_id}: {e}")
        raise HTTPException(status_code=400, detail="فشل في تحديث أمر الإنتاج")
    finally:
        conn.close()


# ---- Delete Work Center / Route / BOM ----

@router.delete("/work-centers/{wc_id}", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.delete"]))])
def delete_work_center(wc_id: int, request: Request, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        # Check if in use by any operations
        in_use = conn.execute(text("""
            SELECT COUNT(*) FROM manufacturing_operations WHERE work_center_id = :id AND is_deleted = false
        """), {"id": wc_id}).scalar()
        if in_use > 0:
            logger.warning(f"Cannot delete work center {wc_id}: used in {in_use} operation(s)")
            raise HTTPException(status_code=400, detail="لا يمكن حذف مركز العمل لارتباطه بعمليات قائمة")
        
        result = conn.execute(text("UPDATE work_centers SET is_deleted = true, deleted_at = NOW(), updated_at = NOW() WHERE id = :id AND is_deleted = false"), {"id": wc_id})
        conn.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Work center not found")
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="delete_work_center", resource_type="work_centers",
                     resource_id=str(wc_id), request=request)
        return {"message": "Work center deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting work center {wc_id}: {e}")
        raise HTTPException(status_code=400, detail="فشل في حذف مركز العمل")
    finally:
        conn.close()


@router.delete("/routes/{route_id}", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.delete"]))])
def delete_route(route_id: int, request: Request, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        # Check if in use by any production orders
        in_use = conn.execute(text("""
            SELECT COUNT(*) FROM production_orders WHERE route_id = :id AND status NOT IN ('cancelled', 'completed')
        """), {"id": route_id}).scalar()
        if in_use > 0:
            logger.warning(f"Cannot delete route {route_id}: used in {in_use} active order(s)")
            raise HTTPException(status_code=400, detail="لا يمكن حذف المسار لارتباطه بأوامر إنتاج نشطة")
        
        conn.execute(text("UPDATE manufacturing_operations SET is_deleted = true, deleted_at = NOW(), updated_at = NOW() WHERE route_id = :id"), {"id": route_id})
        result = conn.execute(text("UPDATE manufacturing_routes SET is_deleted = true, deleted_at = NOW(), updated_at = NOW() WHERE id = :id AND is_deleted = false"), {"id": route_id})
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Route not found")
        
        trans.commit()
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="delete_route", resource_type="manufacturing_routes",
                     resource_id=str(route_id), request=request)
        return {"message": "Route and its operations deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        trans.rollback()
        logger.error(f"Error deleting route {route_id}: {e}")
        raise HTTPException(status_code=400, detail="فشل في حذف المسار")
    finally:
        conn.close()


@router.delete("/boms/{bom_id}", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.delete"]))])
def delete_bom(bom_id: int, request: Request, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        # Check if in use
        in_use = conn.execute(text("""
            SELECT COUNT(*) FROM production_orders WHERE bom_id = :id AND status NOT IN ('cancelled', 'completed')
        """), {"id": bom_id}).scalar()
        if in_use > 0:
            logger.warning(f"Cannot delete BOM {bom_id}: used in {in_use} active order(s)")
            raise HTTPException(status_code=400, detail="لا يمكن حذف قائمة المواد لارتباطها بأوامر إنتاج نشطة")
        
        conn.execute(text("UPDATE bom_outputs SET is_deleted = true, deleted_at = NOW() WHERE bom_id = :id"), {"id": bom_id})
        conn.execute(text("UPDATE bom_components SET is_deleted = true, deleted_at = NOW() WHERE bom_id = :id"), {"id": bom_id})
        result = conn.execute(text("UPDATE bill_of_materials SET is_deleted = true, deleted_at = NOW(), updated_at = NOW() WHERE id = :id AND is_deleted = false"), {"id": bom_id})
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="BOM not found")
        
        trans.commit()
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="delete_bom", resource_type="bill_of_materials",
                     resource_id=str(bom_id), request=request)
        return {"message": "BOM deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        trans.rollback()
        logger.error(f"Error deleting BOM {bom_id}: {e}")
        raise HTTPException(status_code=400, detail="فشل في حذف قائمة المواد")
    finally:
        conn.close()


# --- JOB CARDS (MFG-007) ---

@router.post("/operations/{op_id}/start", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.create"]))])
def start_operation(op_id: int, request: Request, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        op = conn.execute(text("SELECT * FROM production_order_operations WHERE id = :id"), {"id": op_id}).fetchone()
        if not op:
            raise HTTPException(status_code=404, detail="Operation not found")
        
        # Branch validation via production order
        from utils.permissions import validate_branch_access
        po = conn.execute(text("SELECT branch_id FROM production_orders WHERE id = :id"), {"id": op.production_order_id}).fetchone()
        if po and po.branch_id:
            validate_branch_access(current_user, po.branch_id)
        
        if op.status == 'in_progress':
            raise HTTPException(status_code=400, detail="Operation already in progress")

        # Update status to in_progress
        conn.execute(text("""
            UPDATE production_order_operations 
            SET status = 'in_progress', 
                start_time = COALESCE(start_time, NOW()), 
                worker_id = :uid,
                updated_at = NOW()
            WHERE id = :id
        """), {"id": op_id, "uid": current_user.id})
        
        conn.commit()
        
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="start_operation", resource_type="production_order_operations",
                     resource_id=str(op_id), request=request)
        # Re-fetch
        updated = conn.execute(text("SELECT * FROM production_order_operations WHERE id = :id"), {"id": op_id}).fetchone()
        return updated
    finally:
        conn.close()

@router.post("/operations/{op_id}/pause", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.create"]))])
def pause_operation(op_id: int, request: Request, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        op = conn.execute(text("SELECT * FROM production_order_operations WHERE id = :id"), {"id": op_id}).fetchone()
        if not op or op.status != 'in_progress':
            raise HTTPException(status_code=400, detail="Only in-progress operations can be paused")

        # Branch validation via production order
        from utils.permissions import validate_branch_access
        po = conn.execute(text("SELECT branch_id FROM production_orders WHERE id = :id"), {"id": op.production_order_id}).fetchone()
        if po and po.branch_id:
            validate_branch_access(current_user, po.branch_id)

        # Update status
        conn.execute(text("""
            UPDATE production_order_operations 
            SET status = 'paused', updated_at = NOW()
            WHERE id = :id
        """), {"id": op_id})
        conn.commit()
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="pause_operation", resource_type="production_order_operations",
                     resource_id=str(op_id), request=request)
        return conn.execute(text("SELECT * FROM production_order_operations WHERE id = :id"), {"id": op_id}).fetchone()
    finally:
        conn.close()

@router.post("/operations/{op_id}/complete", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.create"]))])
def complete_operation(op_id: int, completed_qty: float, request: Request, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        op = conn.execute(text("SELECT * FROM production_order_operations WHERE id = :id"), {"id": op_id}).fetchone()
        if not op:
            raise HTTPException(status_code=404, detail="Operation not found")

        # Branch validation via production order
        from utils.permissions import validate_branch_access
        po = conn.execute(text("SELECT branch_id FROM production_orders WHERE id = :id"), {"id": op.production_order_id}).fetchone()
        if po and po.branch_id:
            validate_branch_access(current_user, po.branch_id)

        # Calculate duration if we have start_time
        duration = 0
        if op.start_time:
            # Simple duration calculation (minutes)
            res = conn.execute(text("SELECT EXTRACT(EPOCH FROM (NOW() - :start))/60"), {"start": op.start_time}).fetchone()
            duration = res[0] if res else 0

        conn.execute(text("""
            UPDATE production_order_operations 
            SET status = 'completed', 
                end_time = NOW(), 
                completed_quantity = :qty,
                actual_run_time = :duration,
                updated_at = NOW()
            WHERE id = :id
        """), {"id": op_id, "qty": completed_qty, "duration": duration})
        
        conn.commit()
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="complete_operation", resource_type="production_order_operations",
                     resource_id=str(op_id), details={"completed_qty": completed_qty},
                     request=request)
        return conn.execute(text("SELECT * FROM production_order_operations WHERE id = :id"), {"id": op_id}).fetchone()
    finally:
        conn.close()

@router.get("/orders/operations/active", response_model=List[ProductionOrderOperationResponse], dependencies=[Depends(require_permission("manufacturing.view"))])
def get_active_operations(current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        # Fetch active or pending operations with order details
        res = conn.execute(text("""
            SELECT poo.*, po.order_number, wc.name as work_center_name, 
                   mo.description as operation_description, po.quantity as planned_quantity,
                   mo.cycle_time, mo.setup_time, p.product_name
            FROM production_order_operations poo
            JOIN production_orders po ON poo.production_order_id = po.id
            JOIN products p ON po.product_id = p.id
            JOIN work_centers wc ON poo.work_center_id = wc.id
            LEFT JOIN manufacturing_operations mo ON poo.operation_id = mo.id
            WHERE poo.status IN ('pending', 'in_progress', 'paused')
            ORDER BY poo.start_time ASC NULLS LAST, poo.created_at ASC
        """)).fetchall()
        return res
    finally:
        conn.close()

# --- MRP (MFG-005) ---

@router.get("/mrp/calculate/{order_id}", response_model=MRPPlanResponse, dependencies=[Depends(require_permission("manufacturing.manage"))])
def calculate_mrp_for_order(order_id: int, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        order = conn.execute(text("SELECT * FROM production_orders WHERE id = :id"), {"id": order_id}).fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Branch validation
        from utils.permissions import validate_branch_access
        if order.branch_id:
            validate_branch_access(current_user, order.branch_id)
        
        if not order.bom_id:
            raise HTTPException(status_code=400, detail="Order has no BOM assigned")

        # Fetch BOM components
        components = conn.execute(text("""
            SELECT bc.*, p.product_name, p.reorder_level, p.lead_time_days,
                   COALESCE((SELECT SUM(quantity) FROM inventory WHERE product_id = p.id), 0) as on_hand
            FROM bom_components bc
            JOIN products p ON bc.component_product_id = p.id
            WHERE bc.bom_id = :bid AND bc.is_deleted = false
        """), {"bid": order.bom_id}).fetchall()

        # Check pending purchase orders for on_order_quantity
        mrp_items = []
        for comp in components:
            # Handle waste percentage & variable BOM (is_percentage)
            waste_factor = 1 + Decimal(str(comp.waste_percentage or 0)) / Decimal("100")
            if comp.is_percentage:
                required = (Decimal(str(comp.quantity)) / Decimal("100") * Decimal(str(order.quantity))) * waste_factor
            else:
                required = Decimal(str(comp.quantity)) * Decimal(str(order.quantity)) * waste_factor
            required = round(required, 4)

            on_hand = Decimal(str(comp.on_hand or 0))

            # Check pending POs for this product
            on_order = conn.execute(text("""
                SELECT COALESCE(SUM(pi.quantity - COALESCE(pi.received_quantity, 0)), 0)
                FROM purchase_invoice_items pi
                JOIN purchase_invoices p ON pi.invoice_id = p.id
                WHERE pi.product_id = :pid AND p.status IN ('draft', 'approved', 'sent', 'partially_received')
            """), {"pid": comp.component_product_id}).scalar() or 0
            on_order = Decimal(str(on_order))

            available = on_hand + on_order
            shortage = max(0.0, round(required - available, 4))

            if shortage > 0:
                action = "purchase_order"
            elif required > on_hand and on_order > 0:
                action = "wait_for_po"
            else:
                action = "none"

            mrp_items.append({
                "product_id": comp.component_product_id,
                "product_name": comp.product_name,
                "required_quantity": required,
                "available_quantity": available,
                "on_hand_quantity": on_hand,
                "on_order_quantity": on_order,
                "shortage_quantity": shortage,
                "lead_time_days": int(comp.lead_time_days or 1),
                "suggested_action": action,
                "status": "pending"
            })

        # Save MRP Plan to database
        plan_row = conn.execute(text("""
            INSERT INTO mrp_plans (plan_name, production_order_id, status, calculated_at)
            VALUES (:name, :oid, 'draft', NOW())
            RETURNING *
        """), {"name": f"MRP for {order.order_number}", "oid": order_id}).fetchone()

        for item in mrp_items:
            conn.execute(text("""
                INSERT INTO mrp_items (mrp_plan_id, product_id, required_quantity, available_quantity, shortage_quantity, suggested_action, status)
                VALUES (:pid, :prod, :req, :avail, :short, :action, :status)
            """), {
                "pid": plan_row.id, "prod": item["product_id"],
                "req": item["required_quantity"], "avail": item["available_quantity"],
                "short": item["shortage_quantity"], "action": item["suggested_action"],
                "status": item["status"]
            })

        conn.commit()

        return {
            "id": plan_row.id,
            "plan_name": plan_row.plan_name,
            "production_order_id": order_id,
            "status": "draft",
            "calculated_at": plan_row.calculated_at,
            "items": mrp_items
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Error calculating MRP for order {order_id}: {e}")
        raise HTTPException(status_code=500, detail="فشل في حساب تخطيط الاحتياجات")
    finally:
        conn.close()

@router.get("/mrp/plans", dependencies=[Depends(require_permission("manufacturing.view"))])
def list_mrp_plans(
    branch_id: Optional[int] = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user),
):
    conn = get_db_connection(current_user.company_id)
    try:
        from utils.permissions import validate_branch_access
        validated_branch = validate_branch_access(current_user, branch_id)

        query = """
            SELECT mp.*, po.order_number 
            FROM mrp_plans mp
            LEFT JOIN production_orders po ON mp.production_order_id = po.id
            WHERE 1=1
        """
        params = {}
        if validated_branch:
            query += " AND po.branch_id = :branch_id"
            params["branch_id"] = validated_branch
        query += " ORDER BY mp.calculated_at DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset
        plans = conn.execute(text(query), params).fetchall()
        result = []
        for p in plans:
            pd = dict(p._mapping)
            items = conn.execute(text("""
                SELECT mi.*, pr.product_name 
                FROM mrp_items mi
                JOIN products pr ON mi.product_id = pr.id
                WHERE mi.mrp_plan_id = :pid
            """), {"pid": p.id}).fetchall()
            pd['items'] = [dict(i._mapping) for i in items]
            result.append(pd)
        return result
    finally:
        conn.close()

# ==========================================
# 6. EQUIPMENT & MAINTENANCE
# ==========================================

@router.get("/equipment", response_model=List[EquipmentResponse], dependencies=[Depends(require_permission("manufacturing.view"))])
def list_equipment(
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user),
):
    conn = get_db_connection(current_user.company_id)
    try:
        equip = conn.execute(text("""
            SELECT e.*, wc.name as work_center_name
            FROM manufacturing_equipment e
            LEFT JOIN work_centers wc ON e.work_center_id = wc.id
            WHERE e.is_deleted = false
            ORDER BY e.id DESC
            LIMIT :limit OFFSET :offset
        """), {"limit": limit, "offset": offset}).fetchall()
        return [dict(e._mapping) for e in equip]
    finally:
        conn.close()

@router.post("/equipment", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.create"]))])
def create_equipment(equip: EquipmentCreate, request: Request, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        new_equip = conn.execute(text("""
            INSERT INTO manufacturing_equipment (name, code, work_center_id, status, purchase_date, last_maintenance_date, next_maintenance_date, notes)
            VALUES (:name, :code, :wcid, :status, :pdate, :lmdate, :nmdate, :notes)
            RETURNING *
        """), {
            "name": equip.name, "code": equip.code, "wcid": equip.work_center_id,
            "status": equip.status, "pdate": equip.purchase_date,
            "lmdate": equip.last_maintenance_date, "nmdate": equip.next_maintenance_date,
            "notes": equip.notes
        }).fetchone()
        
        trans.commit()
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="create_equipment", resource_type="manufacturing_equipment",
                     resource_id=str(new_equip.id), details={"name": equip.name},
                     request=request)
        return dict(new_equip._mapping)
    except HTTPException:
        raise
    except Exception as e:
        trans.rollback()
        logger.error(f"Error creating equipment: {e}")
        raise HTTPException(status_code=400, detail="فشل في إنشاء المعدات")
    finally:
        conn.close()

@router.put("/equipment/{equip_id}", response_model=EquipmentResponse, dependencies=[Depends(require_permission("manufacturing.manage"))])
def update_equipment(equip_id: int, equip: EquipmentCreate, request: Request, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        updated = conn.execute(text("""
            UPDATE manufacturing_equipment SET name=:name, code=:code, work_center_id=:wcid, status=:status,
                purchase_date=:pdate, last_maintenance_date=:lmdate, next_maintenance_date=:nmdate, notes=:notes
            WHERE id=:id RETURNING *
        """), {
            "name": equip.name, "code": equip.code, "wcid": equip.work_center_id,
            "status": equip.status, "pdate": equip.purchase_date,
            "lmdate": equip.last_maintenance_date, "nmdate": equip.next_maintenance_date,
            "notes": equip.notes, "id": equip_id
        }).fetchone()
        if not updated:
            raise HTTPException(status_code=404, detail="Equipment not found")
        conn.commit()
        result = dict(updated._mapping)
        wc = conn.execute(text("SELECT name FROM work_centers WHERE id = :wid"), {"wid": equip.work_center_id}).fetchone() if equip.work_center_id else None
        result['work_center_name'] = wc.name if wc else None
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="update_equipment", resource_type="manufacturing_equipment",
                     resource_id=str(equip_id), details={"name": equip.name},
                     request=request)
        return result
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating equipment {equip_id}: {e}")
        raise HTTPException(status_code=400, detail="فشل في تحديث المعدات")
    finally:
        conn.close()

@router.delete("/equipment/{equip_id}", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.delete"]))])
def delete_equipment(equip_id: int, request: Request, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        # Check for maintenance logs
        logs = conn.execute(text("SELECT COUNT(*) FROM maintenance_logs WHERE equipment_id = :id"), {"id": equip_id}).scalar()
        if logs > 0:
            logger.warning(f"Cannot delete equipment {equip_id}: has {logs} maintenance log(s)")
            raise HTTPException(status_code=400, detail="لا يمكن حذف المعدة لوجود سجلات صيانة مرتبطة")
        deleted = conn.execute(text("UPDATE manufacturing_equipment SET is_deleted = true, deleted_at = NOW() WHERE id = :id AND is_deleted = false RETURNING id"), {"id": equip_id}).fetchone()
        if not deleted:
            raise HTTPException(status_code=404, detail="Equipment not found")
        conn.commit()
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="delete_equipment", resource_type="manufacturing_equipment",
                     resource_id=str(equip_id), request=request)
        return {"detail": "Equipment deleted"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting equipment {equip_id}: {e}")
        raise HTTPException(status_code=400, detail="فشل في حذف المعدات")
    finally:
        conn.close()

@router.get("/maintenance-logs", response_model=List[MaintenanceLogResponse], dependencies=[Depends(require_permission("manufacturing.view"))])
def list_maintenance_logs(
    equipment_id: Optional[int] = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user),
):
    conn = get_db_connection(current_user.company_id)
    try:
        query = """
            SELECT ml.*, e.name as equipment_name, u.full_name as performed_by_name
            FROM maintenance_logs ml
            LEFT JOIN manufacturing_equipment e ON ml.equipment_id = e.id
            LEFT JOIN company_users u ON ml.performed_by = u.id
            WHERE 1=1
        """
        params = {}
        if equipment_id:
            query += " AND ml.equipment_id = :eid"
            params["eid"] = equipment_id
            
        query += " ORDER BY ml.maintenance_date DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset
        
        logs = conn.execute(text(query), params).fetchall()
        return [dict(l._mapping) for l in logs]
    finally:
        conn.close()

@router.post("/maintenance-logs", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.create"]))])
def create_maintenance_log(log: MaintenanceLogCreate, request: Request, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        new_log = conn.execute(text("""
            INSERT INTO maintenance_logs (equipment_id, maintenance_type, description, cost, performed_by, 
                                        external_service_provider, maintenance_date, next_due_date, status, notes)
            VALUES (:eid, :mtype, :desc, :cost, :uid, :ext, :mdate, :ndate, :status, :notes)
            RETURNING *
        """), {
            "eid": log.equipment_id, "mtype": log.maintenance_type, "desc": log.description,
            "cost": log.cost, "uid": log.performed_by, "ext": log.external_service_provider,
            "mdate": log.maintenance_date, "ndate": log.next_due_date,
            "status": log.status, "notes": log.notes
        }).fetchone()
        
        # Update Equipment dates if necessary
        if log.maintenance_date:
            conn.execute(text("UPDATE manufacturing_equipment SET last_maintenance_date = :date WHERE id = :id"), 
                         {"date": log.maintenance_date, "id": log.equipment_id})
        
        if log.next_due_date:
             conn.execute(text("UPDATE manufacturing_equipment SET next_maintenance_date = :date WHERE id = :id"), 
                         {"date": log.next_due_date, "id": log.equipment_id})

        trans.commit()
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="create_maintenance_log", resource_type="maintenance_logs",
                     resource_id=str(new_log.id), details={"equipment_id": log.equipment_id, "type": log.maintenance_type},
                     request=request)
        # Fetch updated log with joins
        log_res = conn.execute(text("""
            SELECT ml.*, e.name as equipment_name, u.full_name as performed_by_name
            FROM maintenance_logs ml
            LEFT JOIN manufacturing_equipment e ON ml.equipment_id = e.id
            LEFT JOIN company_users u ON ml.performed_by = u.id
            WHERE ml.id = :lid
        """), {"lid": new_log.id}).fetchone()
        
        return dict(log_res._mapping)
    except HTTPException:
        raise
    except Exception as e:
        trans.rollback()
        logger.error(f"Error creating maintenance log: {e}")
        raise HTTPException(status_code=400, detail="فشل في إنشاء سجل الصيانة")
    finally:
        conn.close()


# ==========================================
# 7. MANUFACTURING REPORTS
# ==========================================

@router.get("/reports/production-cost", dependencies=[Depends(require_permission("manufacturing.view"))])
def report_production_cost(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    branch_id: Optional[int] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Production Cost Report: Actual vs Estimated costs for completed production orders.
    """
    conn = get_db_connection(current_user.company_id)
    try:
        from utils.permissions import validate_branch_access
        validated_branch = validate_branch_access(current_user, branch_id)

        query = """
            SELECT po.id, po.order_number, po.product_id, p.product_name, po.quantity,
                   po.status, po.start_date, po.updated_at as completion_date,
                   b.name as bom_name
            FROM production_orders po
            LEFT JOIN products p ON po.product_id = p.id
            LEFT JOIN bill_of_materials b ON po.bom_id = b.id
            WHERE po.status = 'completed'
        """
        params = {}
        if validated_branch:
            query += " AND po.branch_id = :branch_id"
            params["branch_id"] = validated_branch
        if start_date:
            query += " AND po.start_date >= :start"
            params["start"] = start_date
        if end_date:
            query += " AND po.updated_at <= :end"
            params["end"] = end_date
        query += " ORDER BY po.updated_at DESC"
        
        orders = conn.execute(text(query), params).fetchall()
        
        report_rows = []
        total_material = 0
        total_labor = 0
        total_overhead = 0
        total_production = 0
        
        for o in orders:
            cost = calculate_production_cost(conn, o.product_id if not o.bom_name else None, o.quantity, o.id)
            # Re-calculate with actual BOM
            if o.product_id:
                bom_row = conn.execute(text(
                    "SELECT id FROM bill_of_materials WHERE product_id = :pid AND is_active = true AND is_deleted = false LIMIT 1"
                ), {"pid": o.product_id}).fetchone()
                if bom_row:
                    cost = calculate_production_cost(conn, bom_row.id, o.quantity, o.id)
            
            row = {
                "order_id": o.id,
                "order_number": o.order_number,
                "product_name": o.product_name,
                "quantity": o.quantity,
                "start_date": str(o.start_date) if o.start_date else None,
                "completion_date": str(o.completion_date) if o.completion_date else None,
                "material_cost": cost["material_cost"],
                "labor_cost": cost["labor_cost"],
                "overhead_cost": cost["overhead_cost"],
                "total_cost": cost["total_cost"],
                "unit_cost": cost["unit_cost"],
            }
            report_rows.append(row)
            total_material += cost["material_cost"]
            total_labor += cost["labor_cost"]
            total_overhead += cost["overhead_cost"]
            total_production += cost["total_cost"]
        
        return {
            "report_name": "Production Cost Report",
            "period": {"start": str(start_date) if start_date else "All", "end": str(end_date) if end_date else "All"},
            "orders": report_rows,
            "totals": {
                "total_material_cost": round(total_material, 2),
                "total_labor_cost": round(total_labor, 2),
                "total_overhead_cost": round(total_overhead, 2),
                "total_production_cost": round(total_production, 2),
                "order_count": len(report_rows),
            }
        }
    finally:
        conn.close()


@router.get("/reports/work-center-efficiency", dependencies=[Depends(require_permission("manufacturing.view"))])
def report_work_center_efficiency(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Work Center Efficiency Report: Utilization and performance of each work center.
    """
    conn = get_db_connection(current_user.company_id)
    try:
        wcs = conn.execute(text("SELECT * FROM work_centers WHERE is_deleted = false ORDER BY name")).fetchall()
        
        date_filter = ""
        params = {}
        if start_date:
            date_filter += " AND poo.start_time >= :start"
            params["start"] = start_date
        if end_date:
            date_filter += " AND poo.end_time <= :end"
            params["end"] = end_date
        
        report_rows = []
        for wc in wcs:
            stats = conn.execute(text(f"""
                SELECT 
                    COUNT(*) as total_operations,
                    COUNT(CASE WHEN poo.status = 'completed' THEN 1 END) as completed_operations,
                    COALESCE(SUM(poo.actual_run_time), 0) as total_run_time_min,
                    COALESCE(SUM(poo.completed_quantity), 0) as total_output,
                    COALESCE(AVG(poo.actual_run_time), 0) as avg_run_time_min
                FROM production_order_operations poo
                WHERE poo.work_center_id = :wcid {date_filter}
            """), {**params, "wcid": wc.id}).fetchone()
            
            capacity_hours = (wc.capacity_per_day or 8) * 22  # Approx monthly capacity
            used_hours = (stats.total_run_time_min or 0) / 60.0
            utilization = (used_hours / capacity_hours * 100) if capacity_hours > 0 else 0
            
            report_rows.append({
                "work_center_id": wc.id,
                "work_center_name": wc.name,
                "code": wc.code,
                "cost_per_hour": Decimal(str(wc.cost_per_hour or 0)),
                "total_operations": stats.total_operations,
                "completed_operations": stats.completed_operations,
                "total_run_time_hours": round(used_hours, 2),
                "total_output": Decimal(str(stats.total_output or 0)),
                "avg_cycle_time_min": round(Decimal(str(stats.avg_run_time_min or 0)), 2),
                "utilization_percent": round(utilization, 2),
                "total_cost": round(used_hours * Decimal(str(wc.cost_per_hour or 0)), 2),
            })
        
        return {
            "report_name": "Work Center Efficiency Report",
            "period": {"start": str(start_date) if start_date else "All", "end": str(end_date) if end_date else "All"},
            "work_centers": report_rows,
        }
    finally:
        conn.close()


@router.get("/reports/material-consumption", dependencies=[Depends(require_permission("manufacturing.view"))])
def report_material_consumption(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    branch_id: Optional[int] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Material Consumption Report: Raw materials consumed by production orders.
    """
    conn = get_db_connection(current_user.company_id)
    try:
        from utils.permissions import validate_branch_access
        validated_branch = validate_branch_access(current_user, branch_id)

        date_filter = ""
        params = {}
        if validated_branch:
            date_filter += " AND it.branch_id = :branch_id"
            params["branch_id"] = validated_branch
        if start_date:
            date_filter += " AND it.created_at >= :start"
            params["start"] = start_date
        if end_date:
            date_filter += " AND it.created_at <= :end"
            params["end"] = end_date
        
        rows = conn.execute(text(f"""
            SELECT p.id as product_id, p.product_name, p.product_code,
                   SUM(ABS(it.quantity)) as total_consumed,
                   COUNT(DISTINCT it.reference_id) as order_count,
                   AVG(p.cost_price) as avg_unit_cost,
                   SUM(ABS(it.quantity) * COALESCE(p.cost_price, 0)) as total_cost
            FROM inventory_transactions it
            JOIN products p ON it.product_id = p.id
            WHERE it.transaction_type = 'production_out' 
              AND it.reference_type = 'production_order'
              {date_filter}
            GROUP BY p.id, p.product_name, p.product_code
            ORDER BY total_cost DESC
        """), params).fetchall()
        
        materials = []
        grand_total = 0
        for r in rows:
            mat = {
                "product_id": r.product_id,
                "product_name": r.product_name,
                "product_code": r.product_code,
                "total_consumed": round(Decimal(str(r.total_consumed or 0)), 4),
                "order_count": r.order_count,
                "avg_unit_cost": round(Decimal(str(r.avg_unit_cost or 0)), 4),
                "total_cost": round(Decimal(str(r.total_cost or 0)), 2),
            }
            materials.append(mat)
            grand_total += mat["total_cost"]
        
        return {
            "report_name": "Material Consumption Report",
            "period": {"start": str(start_date) if start_date else "All", "end": str(end_date) if end_date else "All"},
            "materials": materials,
            "grand_total_cost": round(grand_total, 2),
        }
    finally:
        conn.close()


@router.get("/reports/production-summary", dependencies=[Depends(require_permission("manufacturing.view"))])
def report_production_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    branch_id: Optional[int] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Production Summary Dashboard: Overview of all production activities.
    """
    conn = get_db_connection(current_user.company_id)
    try:
        from utils.permissions import validate_branch_access
        validated_branch = validate_branch_access(current_user, branch_id)

        date_filter = ""
        params = {}
        if validated_branch:
            date_filter += " AND po.branch_id = :branch_id"
            params["branch_id"] = validated_branch
        if start_date:
            date_filter += " AND po.created_at >= :start"
            params["start"] = start_date
        if end_date:
            date_filter += " AND po.created_at <= :end"
            params["end"] = end_date
        
        # Order counts by status
        status_counts = conn.execute(text(f"""
            SELECT status, COUNT(*) as count, COALESCE(SUM(quantity), 0) as total_qty
            FROM production_orders po
            WHERE 1=1 {date_filter}
            GROUP BY status
        """), params).fetchall()
        
        by_status = {row.status: {"count": row.count, "total_qty": Decimal(str(row.total_qty))} for row in status_counts}
        
        # Top produced products
        top_products = conn.execute(text(f"""
            SELECT p.product_name, SUM(po.produced_quantity) as total_produced, COUNT(*) as order_count
            FROM production_orders po
            JOIN products p ON po.product_id = p.id
            WHERE po.status = 'completed' {date_filter}
            GROUP BY p.product_name
            ORDER BY total_produced DESC
            LIMIT 10
        """), params).fetchall()
        
        # Equipment maintenance due
        maint_due = conn.execute(text("""
            SELECT COUNT(*) FROM manufacturing_equipment 
            WHERE next_maintenance_date <= CURRENT_DATE + INTERVAL '7 days' AND status != 'decommissioned' AND is_deleted = false
        """)).scalar()
        
        return {
            "report_name": "Production Summary",
            "period": {"start": str(start_date) if start_date else "All", "end": str(end_date) if end_date else "All"},
            "orders_by_status": by_status,
            "total_orders": sum(s["count"] for s in by_status.values()),
            "top_produced_products": [
                {"product_name": r.product_name, "total_produced": Decimal(str(r.total_produced or 0)), "order_count": r.order_count}
                for r in top_products
            ],
            "equipment_maintenance_due": maint_due or 0,
        }
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════
# MFG-109: Direct Labor Report (تقرير العمالة المباشرة)
# ═══════════════════════════════════════════════════════════

@router.get("/reports/direct-labor", dependencies=[Depends(require_permission("manufacturing.view"))])
def report_direct_labor(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    work_center_id: Optional[int] = None,
    branch_id: Optional[int] = None,
    format: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    تقرير العمالة المباشرة: ساعات العمل الفعلية، التكلفة، الكفاءة لكل عامل/مركز عمل/أمر إنتاج.
    Direct Labor Report: Actual hours, cost, efficiency per worker/work center/production order.
    """
    conn = get_db_connection(current_user.company_id)
    try:
        from utils.permissions import validate_branch_access
        validated_branch = validate_branch_access(current_user, branch_id)

        date_filter = ""
        params = {}
        if validated_branch:
            date_filter += " AND po.branch_id = :branch_id"
            params["branch_id"] = validated_branch
        if start_date:
            date_filter += " AND poo.start_time >= :start"
            params["start"] = start_date
        if end_date:
            date_filter += " AND poo.end_time <= :end"
            params["end"] = end_date
        if work_center_id:
            date_filter += " AND poo.work_center_id = :wcid"
            params["wcid"] = work_center_id

        # Per work center labor breakdown
        rows = conn.execute(text(f"""
            SELECT 
                wc.id as work_center_id,
                wc.name as work_center_name,
                wc.code as work_center_code,
                wc.cost_per_hour,
                po.id as order_id,
                po.order_number,
                p.product_name,
                po.quantity as order_quantity,
                COALESCE(mo.description, '') as operation_name,
                poo.status as operation_status,
                COALESCE(poo.actual_run_time, 0) as actual_run_time_min,
                COALESCE(
                    EXTRACT(EPOCH FROM (poo.planned_end_time - poo.planned_start_time)) / 60.0,
                    mo.cycle_time * po.quantity,
                    0
                ) as planned_run_time_min,
                COALESCE(poo.completed_quantity, 0) as completed_quantity,
                poo.start_time,
                poo.end_time
            FROM production_order_operations poo
            JOIN production_orders po ON poo.production_order_id = po.id
            JOIN products p ON po.product_id = p.id
            LEFT JOIN work_centers wc ON poo.work_center_id = wc.id
            LEFT JOIN manufacturing_operations mo ON poo.operation_id = mo.id
            WHERE poo.status IN ('completed', 'in_progress')
            {date_filter}
            ORDER BY wc.name, po.order_number, mo.sequence
        """), params).fetchall()

        # Build detailed report
        report_rows = []
        total_actual_hours = 0
        total_planned_hours = 0
        total_labor_cost = 0

        for r in rows:
            actual_hours = round(Decimal(str(r.actual_run_time_min or 0)) / Decimal("60"), 2)
            planned_hours = round(Decimal(str(r.planned_run_time_min or 0)) / Decimal("60"), 2)
            cost_per_hour = Decimal(str(r.cost_per_hour or 0))
            labor_cost = round(actual_hours * cost_per_hour, 2)
            efficiency = round((planned_hours / actual_hours * 100), 1) if actual_hours > 0 else 0

            total_actual_hours += actual_hours
            total_planned_hours += planned_hours
            total_labor_cost += labor_cost

            report_rows.append({
                "work_center": r.work_center_name or "غير محدد",
                "work_center_code": r.work_center_code or "",
                "order_number": r.order_number,
                "product_name": r.product_name,
                "operation": r.operation_name or "",
                "planned_hours": planned_hours,
                "actual_hours": actual_hours,
                "efficiency_pct": efficiency,
                "cost_per_hour": cost_per_hour,
                "labor_cost": labor_cost,
                "completed_qty": Decimal(str(r.completed_quantity or 0)),
                "cost_per_unit": round(labor_cost / Decimal(str(r.completed_quantity)), 2) if r.completed_quantity else 0,
            })

        # Summary by work center
        wc_summary = {}
        for r in report_rows:
            wc = r["work_center"]
            if wc not in wc_summary:
                wc_summary[wc] = {"hours": 0, "cost": 0, "operations": 0}
            wc_summary[wc]["hours"] += r["actual_hours"]
            wc_summary[wc]["cost"] += r["labor_cost"]
            wc_summary[wc]["operations"] += 1

        overall_efficiency = round((total_planned_hours / total_actual_hours * 100), 1) if total_actual_hours > 0 else 0

        result = {
            "report_name": "Direct Labor Report - تقرير العمالة المباشرة",
            "period": {"start": str(start_date) if start_date else "All", "end": str(end_date) if end_date else "All"},
            "details": report_rows,
            "work_center_summary": [
                {"work_center": k, "total_hours": round(v["hours"], 2), "total_cost": round(v["cost"], 2), "operations_count": v["operations"]}
                for k, v in wc_summary.items()
            ],
            "totals": {
                "total_actual_hours": round(total_actual_hours, 2),
                "total_planned_hours": round(total_planned_hours, 2),
                "overall_efficiency_pct": overall_efficiency,
                "total_labor_cost": round(total_labor_cost, 2),
                "total_operations": len(report_rows),
            }
        }

        # Export if format specified
        if format in ("excel", "pdf"):
            export_data = []
            for r in report_rows:
                export_data.append({
                    "مركز العمل / Work Center": r["work_center"],
                    "أمر الإنتاج / Order #": r["order_number"],
                    "المنتج / Product": r["product_name"],
                    "العملية / Operation": r["operation"],
                    "ساعات مخططة / Planned Hrs": r["planned_hours"],
                    "ساعات فعلية / Actual Hrs": r["actual_hours"],
                    "الكفاءة % / Efficiency": f"{r['efficiency_pct']}%",
                    "تكلفة الساعة / Cost/Hr": r["cost_per_hour"],
                    "تكلفة العمالة / Labor Cost": r["labor_cost"],
                })
            columns = list(export_data[0].keys()) if export_data else []
            period_str = f"{start_date or 'all'}_{end_date or 'all'}"
            if format == "excel":
                buffer = generate_excel(export_data, columns, sheet_name="Direct Labor")
                return create_export_response(buffer, f"direct_labor_{period_str}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                pdf_data = [columns] + [[str(row.get(c, '')) for c in columns] for row in export_data]
                buffer = generate_pdf(pdf_data, f"Direct Labor Report ({period_str})")
                return create_export_response(buffer, f"direct_labor_{period_str}.pdf", "application/pdf")

        return result
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════
# MFG-107: Variable BOM — Compute Material Quantities
# ═══════════════════════════════════════════════════════════

@router.get("/boms/{bom_id}/compute-materials", dependencies=[Depends(require_permission("manufacturing.view"))])
def compute_bom_materials(
    bom_id: int,
    quantity: float = Query(..., description="Production order quantity"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    احسب الكميات الفعلية للمكونات بناءً على كمية الإنتاج المطلوبة.
    يدعم BOMs النسبية (Variable BOM) والثابتة.
    """
    conn = get_db_connection(current_user.company_id)
    try:
        bom = conn.execute(text("SELECT * FROM bill_of_materials WHERE id = :id AND is_deleted = false"), {"id": bom_id}).fetchone()
        if not bom:
            raise HTTPException(status_code=404, detail="BOM غير موجود")

        components = conn.execute(text("""
            SELECT bc.*, p.product_name, p.cost_price, u.unit_name
            FROM bom_components bc
            JOIN products p ON bc.component_product_id = p.id
            LEFT JOIN product_units u ON p.unit_id = u.id
            WHERE bc.bom_id = :bid AND bc.is_deleted = false
        """), {"bid": bom_id}).fetchall()

        result_components = []
        total_material_cost = Decimal("0")

        for c in components:
            waste_factor = 1 + (c.waste_percentage or 0) / 100.0
            if c.is_percentage:
                # Variable BOM: base qty = quantity% of order
                computed_qty = round((c.quantity / 100.0 * quantity) * waste_factor, 4)
            else:
                # Fixed BOM: qty per unit × order qty
                computed_qty = round(c.quantity * quantity * waste_factor, 4)

            unit_cost = Decimal(str(c.cost_price or 0))
            line_cost = computed_qty * unit_cost
            total_material_cost += line_cost

            # Check available inventory
            inv = conn.execute(text(
                "SELECT COALESCE(SUM(quantity), 0) as qty FROM inventory WHERE product_id = :pid"
            ), {"pid": c.component_product_id}).scalar()
            available = Decimal(str(inv))

            result_components.append({
                "component_product_id": c.component_product_id,
                "product_name": c.product_name,
                "unit": c.unit_name,
                "is_percentage": bool(c.is_percentage),
                "bom_quantity": Decimal(str(c.quantity)),
                "computed_quantity": computed_qty,
                "waste_percentage": Decimal(str(c.waste_percentage or 0)),
                "unit_cost": unit_cost,
                "line_cost": round(line_cost, 2),
                "available_inventory": round(available, 4),
                "sufficient": available >= computed_qty,
                "shortage": round(max(0.0, computed_qty - available), 4),
            })

        return {
            "bom_id": bom_id,
            "bom_name": bom.name,
            "production_quantity": quantity,
            "total_material_cost": round(total_material_cost, 2),
            "components": result_components,
            "all_sufficient": all(c["sufficient"] for c in result_components),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error computing BOM materials: {e}")
        raise HTTPException(status_code=500, detail="فشل في حساب المواد")
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════
# MFG-108: In-Process QC Checks (فحص الجودة أثناء الإنتاج)
# ═══════════════════════════════════════════════════════════

class QCCheckCreate(BaseModel):
    check_name: str
    check_type: Optional[str] = "visual"
    specification: Optional[str] = None
    failure_action: Optional[str] = "warn"
    operation_id: Optional[int] = None
    notes: Optional[str] = None


class QCResultRecord(BaseModel):
    actual_value: str
    result: str   # "pass" | "fail" | "warning"
    notes: Optional[str] = None


@router.get("/orders/{order_id}/qc-checks", dependencies=[Depends(require_permission("manufacturing.view"))])
def get_qc_checks(order_id: int, current_user: UserResponse = Depends(get_current_user)):
    """جلب فحوصات الجودة لأمر الإنتاج"""
    conn = get_db_connection(current_user.company_id)
    try:
        # Branch validation
        from utils.permissions import validate_branch_access
        po = conn.execute(text("SELECT branch_id FROM production_orders WHERE id = :id"), {"id": order_id}).fetchone()
        if po and po.branch_id:
            validate_branch_access(current_user, po.branch_id)

        rows = conn.execute(text("""
            SELECT q.*, u.full_name as checked_by_name,
                   op.name as operation_name
            FROM mfg_qc_checks q
            LEFT JOIN company_users u ON q.checked_by = u.id
            LEFT JOIN manufacturing_operations op ON q.operation_id = op.id
            WHERE q.production_order_id = :oid AND q.is_deleted = false
            ORDER BY q.created_at
        """), {"oid": order_id}).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()


@router.post("/orders/{order_id}/qc-checks", status_code=201, dependencies=[Depends(require_permission("manufacturing.manage"))])
def create_qc_check(
    order_id: int,
    qc: QCCheckCreate,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """إضافة فحص جودة لأمر إنتاج"""
    conn = get_db_connection(current_user.company_id)
    try:
        order = conn.execute(text("SELECT id, status, branch_id FROM production_orders WHERE id=:id"), {"id": order_id}).fetchone()
        if not order:
            raise HTTPException(**http_error(404, "production_order_not_found"))
        from utils.permissions import validate_branch_access
        if order.branch_id:
            validate_branch_access(current_user, order.branch_id)
        if order.status not in ("in_progress", "confirmed"):
            raise HTTPException(status_code=400, detail="فحص الجودة يُضاف فقط للأوامر قيد التنفيذ أو المؤكدة")

        qc_id = conn.execute(text("""
            INSERT INTO mfg_qc_checks (
                production_order_id, operation_id, check_name,
                check_type, specification, failure_action, notes,
                result, checked_by
            ) VALUES (:oid, :op, :name, :type, :spec, :action, :notes, 'pending', :uid)
            RETURNING id
        """), {
            "oid": order_id, "op": qc.operation_id, "name": qc.check_name,
            "type": qc.check_type, "spec": qc.specification,
            "action": qc.failure_action, "notes": qc.notes,
            "uid": current_user.id
        }).scalar()
        conn.commit()
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="create_qc_check", resource_type="mfg_qc_checks",
                     resource_id=str(qc_id), details={"order_id": order_id, "check_name": qc.check_name},
                     request=request)
        return {"success": True, "id": qc_id}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating QC check: {e}")
        raise HTTPException(status_code=500, detail="فشل في إنشاء فحص الجودة")
    finally:
        conn.close()


@router.post("/qc-checks/{qc_id}/record-result", dependencies=[Depends(require_permission("manufacturing.manage"))])
def record_qc_result(
    qc_id: int,
    res: QCResultRecord,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    تسجيل نتيجة فحص الجودة.
    إذا كانت النتيجة 'fail' وإجراء الفشل 'stop' → يُوقف أمر الإنتاج تلقائياً.
    """
    conn = get_db_connection(current_user.company_id)
    try:
        if res.result not in ("pass", "fail", "warning"):
            raise HTTPException(status_code=400, detail="النتيجة يجب أن تكون: pass / fail / warning")

        qc = conn.execute(text("SELECT * FROM mfg_qc_checks WHERE id=:id AND is_deleted = false"), {"id": qc_id}).fetchone()
        if not qc:
            raise HTTPException(**http_error(404, "quality_check_not_found"))

        # Branch validation via production order
        from utils.permissions import validate_branch_access
        po = conn.execute(text("SELECT branch_id FROM production_orders WHERE id = :id"), {"id": qc.production_order_id}).fetchone()
        if po and po.branch_id:
            validate_branch_access(current_user, po.branch_id)

        conn.execute(text("""
            UPDATE mfg_qc_checks
            SET actual_value = :val, result = :result, notes = COALESCE(:notes, notes),
                checked_by = :uid, checked_at = NOW(), updated_at = NOW()
            WHERE id = :id
        """), {
            "val": res.actual_value, "result": res.result,
            "notes": res.notes, "uid": current_user.id, "id": qc_id
        })

        action_taken = None

        # If failed with "stop" action → mark order as needing QC review in notes
        if res.result == "fail" and qc.failure_action == "stop":
            conn.execute(text("""
                UPDATE production_orders
                SET notes = COALESCE(notes,'') || ' | [QC-STOP] فشل فحص: ' || :check_name,
                    updated_at = NOW()
                WHERE id = :oid
            """), {"check_name": qc.check_name, "oid": qc.production_order_id})
            action_taken = "qc_stop_flagged"

        conn.commit()

        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="record_qc_result", resource_type="mfg_qc_checks",
                     resource_id=str(qc_id), details={"result": res.result},
                     request=request)
        return {
            "success": True,
            "result": res.result,
            "action_taken": action_taken,
            "message": (
                "تم تعليم أمر الإنتاج بفشل فحص الجودة — يستلزم مراجعة" if action_taken == "qc_stop_flagged"
                else f"تم تسجيل نتيجة الفحص: {res.result}"
            )
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Error recording QC result: {e}")
        raise HTTPException(status_code=500, detail="فشل في تسجيل نتيجة الفحص")
    finally:
        conn.close()


@router.get("/qc-checks/failures", dependencies=[Depends(require_permission("manufacturing.view"))])
def get_qc_failures(current_user: UserResponse = Depends(get_current_user)):
    """قائمة فحوصات الجودة الفاشلة والمعلقة"""
    conn = get_db_connection(current_user.company_id)
    try:
        rows = conn.execute(text("""
            SELECT q.*, po.order_number, p.product_name,
                   u.full_name as checked_by_name
            FROM mfg_qc_checks q
            JOIN production_orders po ON q.production_order_id = po.id
            JOIN products p ON po.product_id = p.id
            LEFT JOIN company_users u ON q.checked_by = u.id
            WHERE q.result IN ('fail', 'pending') AND q.is_deleted = false
            ORDER BY q.created_at DESC
        """)).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  ACTUAL MANUFACTURING COSTING & VARIANCE ANALYSIS
#  التكلفة الفعلية للتصنيع — تحليل الانحرافات
# ═══════════════════════════════════════════════════════════════════════════════

class ActualCostUpdate(BaseModel):
    actual_material_cost: Optional[float] = None
    actual_labor_cost: Optional[float] = None
    actual_overhead_cost: Optional[float] = None


@router.post("/orders/{order_id}/calculate-cost", dependencies=[Depends(require_permission("manufacturing.manage"))])
def calculate_actual_cost(order_id: int, body: Optional[ActualCostUpdate] = None,
                          current_user: UserResponse = Depends(get_current_user)):
    """
    حساب التكلفة الفعلية لأمر الإنتاج — المواد + العمالة + الأعباء
    ومقارنتها بالتكلفة المعيارية (من BOM) لإنتاج تقرير الانحرافات
    """
    conn = get_db_connection(current_user.company_id)
    try:
        order = conn.execute(text("""
            SELECT po.*, p.product_name, p.cost_price as standard_unit_cost
            FROM production_orders po
            JOIN products p ON po.product_id = p.id
            WHERE po.id = :id
        """), {"id": order_id}).fetchone()

        if not order:
            raise HTTPException(**http_error(404, "production_order_not_found"))
        from utils.permissions import validate_branch_access
        if order.branch_id:
            validate_branch_access(current_user, order.branch_id)

        qty = Decimal(str(order.quantity or 1))

        # ── 1. Actual Material Cost ──
        material_consumed = conn.execute(text("""
            SELECT COALESCE(SUM(ABS(it.quantity) * COALESCE(p.cost_price, 0)), 0)
            FROM inventory_transactions it
            JOIN products p ON p.id = it.product_id
            WHERE it.reference_type = 'production_order'
              AND it.reference_id = :oid
              AND it.quantity < 0
        """), {"oid": order_id}).scalar() or 0

        actual_material = Decimal(str(body.actual_material_cost)) if body and body.actual_material_cost is not None else Decimal(str(material_consumed))

        # ── 2. Actual Labor Cost ──
        labor_cost = conn.execute(text("""
            SELECT COALESCE(SUM(
                COALESCE(poo.actual_run_time, 0) / 60.0 * COALESCE(wc.cost_per_hour, 0)
            ), 0)
            FROM production_order_operations poo
            LEFT JOIN work_centers wc ON wc.id = poo.work_center_id
            WHERE poo.production_order_id = :oid
        """), {"oid": order_id}).scalar() or 0

        actual_labor = Decimal(str(body.actual_labor_cost)) if body and body.actual_labor_cost is not None else Decimal(str(labor_cost))

        # ── 3. Overhead ──
        settings = conn.execute(text("SELECT * FROM company_settings LIMIT 1")).fetchone()
        overhead_rate = Decimal(str(getattr(settings, 'mfg_overhead_rate', 0) or 0)) / Decimal("100")
        default_overhead = round(actual_labor * overhead_rate, 2) if overhead_rate > 0 else Decimal("0")
        actual_overhead = Decimal(str(body.actual_overhead_cost)) if body and body.actual_overhead_cost is not None else default_overhead

        actual_total = round(actual_material + actual_labor + actual_overhead, 2)

        # ── 4. Standard Cost (from BOM) ──
        standard_cost = Decimal("0")
        if order.bom_id:
            # BOM material cost from bom_components
            bom_material = conn.execute(text("""
                SELECT COALESCE(SUM(bc.quantity * COALESCE(p.cost_price, 0)), 0)
                FROM bom_components bc
                JOIN products p ON p.id = bc.component_product_id
                WHERE bc.bom_id = :boid AND bc.is_deleted = false
            """), {"boid": order.bom_id}).scalar() or 0

            # BOM operation cost from manufacturing_operations via route
            bom_ops = conn.execute(text("""
                SELECT COALESCE(SUM(
                    COALESCE(mo.cycle_time, 0) / 60.0 * COALESCE(wc.cost_per_hour, 0)
                ), 0)
                FROM manufacturing_operations mo
                LEFT JOIN work_centers wc ON wc.id = mo.work_center_id
                WHERE mo.route_id = (SELECT route_id FROM bill_of_materials WHERE id = :boid) AND mo.is_deleted = false
            """), {"boid": order.bom_id}).scalar() or 0

            standard_cost = (Decimal(str(bom_material)) + Decimal(str(bom_ops))) * qty
        else:
            standard_cost = Decimal(str(order.standard_unit_cost or 0)) * qty

        standard_cost = round(standard_cost, 2)

        # ── 5. Variance ──
        variance = round(actual_total - standard_cost, 2)
        variance_pct = round((variance / standard_cost * 100), 2) if standard_cost > 0 else Decimal("0")

        if variance > 0:
            variance_type = "unfavorable"
            variance_type_ar = "غير مواتٍ (تجاوز)"
        elif variance < 0:
            variance_type = "favorable"
            variance_type_ar = "مواتٍ (وفر)"
        else:
            variance_type = "none"
            variance_type_ar = "لا انحراف"

        # ── 6. Per-unit cost ──
        actual_qty = Decimal(str(order.produced_quantity or order.quantity or 1))
        actual_unit_cost = round(actual_total / actual_qty, 4) if actual_qty > 0 else Decimal("0")

        # ── Update production order with costs ──
        conn.execute(text("""
            UPDATE production_orders SET
                actual_material_cost = :mc, actual_labor_cost = :lc,
                actual_overhead_cost = :oc, actual_total_cost = :tc,
                standard_cost = :sc, variance_amount = :va,
                variance_percentage = :vp, costing_status = 'calculated',
                updated_at = NOW()
            WHERE id = :id
        """), {
            "mc": actual_material, "lc": actual_labor, "oc": actual_overhead,
            "tc": actual_total, "sc": standard_cost, "va": variance,
            "vp": variance_pct, "id": order_id
        })

        # ── Update product cost_price with actual cost ──
        conn.execute(text("""
            UPDATE products SET cost_price = :cost, updated_at = NOW()
            WHERE id = :pid
        """), {"cost": actual_unit_cost, "pid": order.product_id})

        conn.commit()

        return {
            "order_id": order_id,
            "product_name": order.product_name,
            "planned_quantity": qty,
            "produced_quantity": actual_qty,
            "cost_breakdown": {
                "material_cost": actual_material,
                "labor_cost": actual_labor,
                "overhead_cost": actual_overhead,
                "total_actual_cost": actual_total,
                "unit_actual_cost": actual_unit_cost
            },
            "standard_cost": standard_cost,
            "variance": {
                "amount": variance,
                "percentage": variance_pct,
                "type": variance_type,
                "type_ar": variance_type_ar
            },
            "costing_status": "calculated",
            "message": f"تم حساب التكلفة الفعلية — الانحراف: {variance:+.2f} ({variance_pct:+.1f}%)"
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Error calculating actual cost for order {order_id}: {e}")
        raise HTTPException(500, "فشل في حساب التكلفة الفعلية")
    finally:
        conn.close()


@router.get("/cost-variance-report", dependencies=[Depends(require_permission("manufacturing.view"))])
def cost_variance_report(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    branch_id: Optional[int] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """تقرير الانحرافات — مقارنة التكلفة المعيارية بالفعلية لكل أوامر الإنتاج"""
    conn = get_db_connection(current_user.company_id)
    try:
        from utils.permissions import validate_branch_access
        validated_branch = validate_branch_access(current_user, branch_id)

        query = """
            SELECT po.id, po.order_number, po.product_id,
                   p.product_name, p.sku,
                   po.quantity, po.produced_quantity,
                   po.actual_material_cost, po.actual_labor_cost,
                   po.actual_overhead_cost, po.actual_total_cost,
                   po.standard_cost, po.variance_amount, po.variance_percentage,
                   po.costing_status, po.status, po.created_at
            FROM production_orders po
            JOIN products p ON p.id = po.product_id
            WHERE po.costing_status = 'calculated'
        """
        params = {}
        if validated_branch:
            query += " AND po.branch_id = :branch_id"
            params["branch_id"] = validated_branch
        if from_date:
            query += " AND po.created_at >= :fd"
            params["fd"] = from_date
        if to_date:
            query += " AND po.created_at <= :td"
            params["td"] = to_date

        query += " ORDER BY ABS(COALESCE(po.variance_percentage, 0)) DESC"

        rows = conn.execute(text(query), params).fetchall()
        results = [dict(r._mapping) for r in rows]

        total_actual = sum(Decimal(str(r.get('actual_total_cost', 0) or 0)) for r in results)
        total_standard = sum(Decimal(str(r.get('standard_cost', 0) or 0)) for r in results)
        total_variance = round(total_actual - total_standard, 2)

        return {
            "orders": results,
            "summary": {
                "total_orders": len(results),
                "total_actual_cost": total_actual,
                "total_standard_cost": total_standard,
                "total_variance": total_variance,
                "overall_variance_pct": round((total_variance / total_standard * 100), 2) if total_standard else 0,
                "favorable_count": sum(1 for r in results if Decimal(str(r.get('variance_amount', 0) or 0)) < 0),
                "unfavorable_count": sum(1 for r in results if Decimal(str(r.get('variance_amount', 0) or 0)) > 0)
            }
        }
    finally:
        conn.close()


# ===================== B4: OEE + Capacity Planning =====================

@router.get("/oee", dependencies=[Depends(require_permission("manufacturing.view"))])
def calculate_oee(
    work_center_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    """حساب الفعالية الشاملة للمعدات OEE"""
    conn = get_db_connection(current_user.company_id)
    try:
        q = """
            SELECT cp.work_center_id, wc.name as work_center_name,
                   AVG(cp.efficiency_pct) as avg_efficiency,
                   SUM(cp.available_hours) as total_available,
                   SUM(cp.planned_hours) as total_planned,
                   SUM(cp.actual_hours) as total_actual
            FROM capacity_plans cp
            LEFT JOIN work_centers wc ON wc.id = cp.work_center_id
            WHERE 1=1 AND cp.is_deleted = false AND (wc.is_deleted = false OR wc.id IS NULL)
        """
        params = {}
        if work_center_id:
            q += " AND cp.work_center_id = :wc"
            params["wc"] = work_center_id
        if date_from:
            q += " AND cp.plan_date >= :df"
            params["df"] = date_from
        if date_to:
            q += " AND cp.plan_date <= :dt"
            params["dt"] = date_to
        q += " GROUP BY cp.work_center_id, wc.name ORDER BY wc.name"

        rows = conn.execute(text(q), params).fetchall()
        results = []
        for r in rows:
            d = dict(r._mapping)
            avail = Decimal(str(d.get("total_available") or 1))
            planned = Decimal(str(d.get("total_planned") or 0))
            actual = Decimal(str(d.get("total_actual") or 0))
            availability = min(actual / avail * 100, 100) if avail > 0 else 0
            performance = min(planned / actual * 100, 100) if actual > 0 else 0
            quality = 98.5  # placeholder - would come from QC data
            oee = round(availability * performance * quality / 10000, 2)
            d["availability"] = round(availability, 2)
            d["performance"] = round(performance, 2)
            d["quality"] = round(quality, 2)
            d["oee"] = oee
            results.append(d)
        return results
    except Exception as e:
        logger.error(f"Error calculating OEE: {e}")
        raise HTTPException(500, "فشل في حساب الفعالية الشاملة")
    finally:
        conn.close()


@router.get("/capacity-plans", dependencies=[Depends(require_permission("manufacturing.view"))])
def list_capacity_plans(
    work_center_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    """خطط الطاقة الإنتاجية"""
    conn = get_db_connection(current_user.company_id)
    try:
        q = """
            SELECT cp.*, wc.name as work_center_name
            FROM capacity_plans cp
            LEFT JOIN work_centers wc ON wc.id = cp.work_center_id
            WHERE 1=1 AND cp.is_deleted = false
        """
        params = {}
        if work_center_id:
            q += " AND cp.work_center_id = :wc"
            params["wc"] = work_center_id
        if date_from:
            q += " AND cp.plan_date >= :df"
            params["df"] = date_from
        if date_to:
            q += " AND cp.plan_date <= :dt"
            params["dt"] = date_to
        q += " ORDER BY cp.plan_date DESC"
        rows = conn.execute(text(q), params).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception as e:
        logger.error(f"Error listing capacity plans: {e}")
        raise HTTPException(500, "فشل في جلب خطط الطاقة")
    finally:
        conn.close()


@router.post("/capacity-plans", dependencies=[Depends(require_permission("manufacturing.manage"))])
def create_capacity_plan(plan: dict, request: Request, current_user=Depends(get_current_user)):
    """إنشاء خطة طاقة إنتاجية"""
    conn = get_db_connection(current_user.company_id)
    try:
        eff = 0
        if plan.get("available_hours") and plan.get("actual_hours"):
            eff = round(Decimal(str(plan["actual_hours"])) / Decimal(str(plan["available_hours"])) * 100, 2)
        result = conn.execute(text("""
            INSERT INTO capacity_plans (work_center_id, plan_date, available_hours,
                planned_hours, actual_hours, efficiency_pct, notes)
            VALUES (:wc, :pd, :ah, :ph, :ach, :eff, :n)
            RETURNING id
        """), {
            "wc": plan["work_center_id"], "pd": plan["plan_date"],
            "ah": plan.get("available_hours", 8), "ph": plan.get("planned_hours", 0),
            "ach": plan.get("actual_hours", 0), "eff": eff, "n": plan.get("notes")
        })
        plan_id = result.fetchone()[0]
        conn.commit()
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="create_capacity_plan", resource_type="capacity_plans",
                     resource_id=str(plan_id), request=request)
        return {"id": plan_id, "message": "تم إنشاء خطة الطاقة بنجاح"}
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating capacity plan: {e}")
        raise HTTPException(500, "فشل في إنشاء خطة الطاقة")
    finally:
        conn.close()


@router.put("/capacity-plans/{plan_id}", dependencies=[Depends(require_permission("manufacturing.manage"))])
def update_capacity_plan(plan_id: int, plan: dict, request: Request, current_user=Depends(get_current_user)):
    """تحديث خطة طاقة إنتاجية"""
    conn = get_db_connection(current_user.company_id)
    try:
        eff = 0
        if plan.get("available_hours") and plan.get("actual_hours"):
            eff = round(Decimal(str(plan["actual_hours"])) / Decimal(str(plan["available_hours"])) * 100, 2)
        conn.execute(text("""
            UPDATE capacity_plans SET available_hours = :ah, planned_hours = :ph,
                actual_hours = :ach, efficiency_pct = :eff, notes = :n
            WHERE id = :id
        """), {
            "ah": plan.get("available_hours"), "ph": plan.get("planned_hours"),
            "ach": plan.get("actual_hours"), "eff": eff, "n": plan.get("notes"), "id": plan_id
        })
        conn.commit()
        log_activity(conn, user_id=current_user.id, username=current_user.username,
                     action="update_capacity_plan", resource_type="capacity_plans",
                     resource_id=str(plan_id), request=request)
        return {"message": "تم تحديث خطة الطاقة بنجاح"}
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating capacity plan {plan_id}: {e}")
        raise HTTPException(500, "فشل في تحديث خطة الطاقة")
    finally:
        conn.close()
