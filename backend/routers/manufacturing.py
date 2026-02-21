from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from routers.auth import get_current_user
from utils.permissions import require_permission
from database import get_db_connection
from utils.accounting import update_account_balance, get_base_currency
from schemas import UserResponse
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
    tags=["Manufacturing (Phase 5)"]
)

# ==========================================
# 1. WORK CENTERS
# ==========================================

@router.get("/work-centers", response_model=List[WorkCenterResponse], dependencies=[Depends(require_permission("manufacturing.view"))])
def list_work_centers(current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        rows = conn.execute(text("SELECT * FROM work_centers ORDER BY name")).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()

@router.post("/work-centers", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.create"]))])
def create_work_center(wc: WorkCenterCreate, current_user: UserResponse = Depends(get_current_user)):
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
        return dict(new_wc._mapping)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@router.put("/work-centers/{wc_id}", response_model=WorkCenterResponse, dependencies=[Depends(require_permission("manufacturing.manage"))])
def update_work_center(wc_id: int, wc: WorkCenterCreate, current_user: UserResponse = Depends(get_current_user)):
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
        return dict(updated._mapping)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

# ==========================================
# 2. ROUTINGS
# ==========================================

@router.get("/routes", response_model=List[RouteResponse], dependencies=[Depends(require_permission("manufacturing.view"))])
def list_routes(current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        routes_db = conn.execute(text("""
            SELECT r.*, p.product_name as product_name
            FROM manufacturing_routes r
            LEFT JOIN products p ON r.product_id = p.id
            ORDER BY r.name
        """)).fetchall()
        
        result = []
        for r in routes_db:
            route_dict = dict(r._mapping)
            # Fetch operations
            ops = conn.execute(text("""
                SELECT mo.*, wc.name as work_center_name 
                FROM manufacturing_operations mo
                LEFT JOIN work_centers wc ON mo.work_center_id = wc.id
                WHERE mo.route_id = :rid
                ORDER BY mo.sequence
            """), {"rid": r.id}).fetchall()
            route_dict['operations'] = [dict(op._mapping) for op in ops]
            result.append(route_dict)
            
        return result
    finally:
        conn.close()

@router.post("/routes", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.create"]))])
def create_route(route: RouteCreate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        # Create Header
        new_route = conn.execute(text("""
            INSERT INTO manufacturing_routes (name, product_id, is_active, description)
            VALUES (:name, :pid, :active, :desc)
            RETURNING *
        """), {
            "name": route.name, "pid": route.product_id, 
            "active": route.is_active, "desc": route.description
        }).fetchone()
        
        # Create Operations
        for op in route.operations:
            conn.execute(text("""
                INSERT INTO manufacturing_operations (route_id, sequence, work_center_id, description, setup_time, cycle_time)
                VALUES (:rid, :seq, :wcid, :desc, :setup, :cycle)
            """), {
                "rid": new_route.id, "seq": op.sequence, "wcid": op.work_center_id,
                "desc": op.description, "setup": op.setup_time, "cycle": op.cycle_time
            })
            
        trans.commit()
        
        # Re-fetch the newly created route with operations
        route_dict = dict(new_route._mapping)
        ops = conn.execute(text("""
            SELECT mo.*, wc.name as work_center_name 
            FROM manufacturing_operations mo
            LEFT JOIN work_centers wc ON mo.work_center_id = wc.id
            WHERE mo.route_id = :rid
            ORDER BY mo.sequence
        """), {"rid": new_route.id}).fetchall()
        route_dict['operations'] = [dict(op._mapping) for op in ops]
        # Add product_name from join
        if route.product_id:
            prod = conn.execute(text("SELECT product_name FROM products WHERE id = :pid"), {"pid": route.product_id}).fetchone()
            route_dict['product_name'] = prod.product_name if prod else None
        else:
            route_dict['product_name'] = None
        return route_dict
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

# ==========================================
# 3. BILL OF MATERIALS (BOM)
# ==========================================

@router.get("/boms", response_model=List[BOMResponse], dependencies=[Depends(require_permission("manufacturing.view"))])
def list_boms(current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        boms_db = conn.execute(text("""
            SELECT b.*, p.product_name as product_name, r.name as route_name
            FROM bill_of_materials b
            LEFT JOIN products p ON b.product_id = p.id
            LEFT JOIN manufacturing_routes r ON b.route_id = r.id
            ORDER BY b.id DESC
        """)).fetchall()
        
        result = []
        for b in boms_db:
            bom_dict = dict(b._mapping)
            # Fetch components
            comps = conn.execute(text("""
                SELECT bc.*, p.product_name as component_name, u.unit_name as component_uom
                FROM bom_components bc
                LEFT JOIN products p ON bc.component_product_id = p.id
                LEFT JOIN product_units u ON p.unit_id = u.id
                WHERE bc.bom_id = :bid
            """), {"bid": b.id}).fetchall()
            bom_dict['components'] = [dict(c._mapping) for c in comps]
            
            # Fetch outputs (by-products)
            outputs = conn.execute(text("""
                SELECT bo.*, p.product_name 
                FROM bom_outputs bo
                LEFT JOIN products p ON bo.product_id = p.id
                WHERE bo.bom_id = :bid
            """), {"bid": b.id}).fetchall()
            bom_dict['outputs'] = [dict(o._mapping) for o in outputs]
            
            result.append(bom_dict)
            
        return result
    finally:
        conn.close()

@router.post("/boms", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.create"]))])
def create_bom(bom: BOMCreate, current_user: UserResponse = Depends(get_current_user)):
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
            WHERE b.id = :bid
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
            WHERE bc.bom_id = :bid
        """), {"bid": new_bom.id}).fetchall()
        bom_dict['components'] = [dict(c._mapping) for c in comps]
        
        # Fetch outputs
        outputs = conn.execute(text("""
            SELECT bo.*, p.product_name 
            FROM bom_outputs bo
            LEFT JOIN products p ON bo.product_id = p.id
            WHERE bo.bom_id = :bid
        """), {"bid": new_bom.id}).fetchall()
        bom_dict['outputs'] = [dict(o._mapping) for o in outputs]
        
        return bom_dict
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=400, detail=str(e))
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
    total_material_cost = 0.0
    component_details = []
    
    if bom_id:
        components = conn.execute(text("""
            SELECT bc.*, p.cost_price, p.product_name
            FROM bom_components bc
            JOIN products p ON bc.component_product_id = p.id
            WHERE bc.bom_id = :bid
        """), {"bid": bom_id}).fetchall()
        
        for comp in components:
            waste_factor = 1 + (comp.waste_percentage or 0) / 100.0
            required_qty = comp.quantity * order_quantity * waste_factor
            unit_cost = comp.cost_price or 0
            line_cost = required_qty * unit_cost
            total_material_cost += line_cost
            component_details.append({
                "product_name": comp.product_name,
                "product_id": comp.component_product_id,
                "base_qty": comp.quantity * order_quantity,
                "waste_qty": required_qty - (comp.quantity * order_quantity),
                "total_qty": required_qty,
                "unit_cost": unit_cost,
                "total_cost": line_cost,
            })
    
    # B. Labor Cost (from production_order_operations × work_center cost_per_hour)
    total_labor_cost = 0.0
    total_overhead_cost = 0.0
    
    if order_id:
        ops_data = conn.execute(text("""
            SELECT poo.actual_run_time, wc.cost_per_hour
            FROM production_order_operations poo
            LEFT JOIN work_centers wc ON poo.work_center_id = wc.id
            WHERE poo.production_order_id = :oid
        """), {"oid": order_id}).fetchall()
        
        for op in ops_data:
            duration_hours = (op.actual_run_time or 0) / 60.0
            rate = op.cost_per_hour or 0
            total_labor_cost += duration_hours * rate
        
        # C. Overhead = configurable percentage of labor cost (default 30%)
        # Read from company_settings if available
        overhead_rate_row = conn.execute(text(
            "SELECT setting_value FROM company_settings WHERE setting_key = 'mfg_overhead_rate'"
        )).fetchone()
        overhead_rate = float(overhead_rate_row.setting_value) if overhead_rate_row else 0.30
        total_overhead_cost = total_labor_cost * overhead_rate
    
    total_cost = total_material_cost + total_labor_cost + total_overhead_cost
    unit_cost = total_cost / order_quantity if order_quantity else 0
    
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
        WHERE bc.bom_id = :bid
    """), {"bid": bom_id}).fetchall()
    
    shortages = []
    for comp in components:
        waste_factor = 1 + (comp.waste_percentage or 0) / 100.0
        # Variable BOM: quantity is a percentage of the order quantity
        base_qty = (comp.quantity / 100.0 * order_quantity) if comp.is_percentage else comp.quantity
        required_qty = base_qty * order_quantity * waste_factor if not comp.is_percentage else base_qty * waste_factor
        
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
        
        available = float(inv.qty) if inv else 0
        
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
        bom = conn.execute(text("SELECT * FROM bill_of_materials WHERE id = :bid"), {"bid": bom_id}).fetchone()
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
def list_production_orders(current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        orders_db = conn.execute(text("""
            SELECT po.*, p.product_name as product_name, b.name as bom_name,
                   po.order_number, po.status, po.produced_quantity, po.scrapped_quantity, po.created_at
            FROM production_orders po
            LEFT JOIN products p ON po.product_id = p.id
            LEFT JOIN bill_of_materials b ON po.bom_id = b.id
            ORDER BY po.id DESC
        """)).fetchall()

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
                WHERE bc.bom_id = :bid
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
    current_user: UserResponse = Depends(get_current_user)
):
    conn = get_db_connection(current_user.company_id)
    try:
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
def create_production_order(order: ProductionOrderCreate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        # Generate Order Number if not provided
        if not order.order_number:
            order.order_number = f"PO-{datetime.now().strftime('%y%m%d%H%M%S')}"

        # 1. Create Order Header
        new_order = conn.execute(text("""
            INSERT INTO production_orders (order_number, product_id, bom_id, route_id, quantity, 
                                         status, start_date, due_date, warehouse_id, destination_warehouse_id, notes, created_by)
            VALUES (:num, :pid, :bid, :rid, :qty, :status, :start, :due, :whid, :dwhid, :notes, :uid)
            RETURNING *
        """), {
            "num": order.order_number, "pid": order.product_id, "bid": order.bom_id,
            "rid": order.route_id, "qty": order.quantity, "status": order.status or 'draft',
            "start": order.start_date, "due": order.due_date, 
            "whid": order.warehouse_id, "dwhid": order.destination_warehouse_id,
            "notes": order.notes, "uid": current_user.id
        }).fetchone()
        new_order_id = new_order.id

        # 2. Create Order Operations (Copy from Route)
        if order.route_id:
            route_ops = conn.execute(text("""
                SELECT * FROM manufacturing_operations WHERE route_id = :rid ORDER BY sequence
            """), {"rid": order.route_id}).fetchall()

            for op in route_ops:
                conn.execute(text("""
                    INSERT INTO production_order_operations (production_order_id, operation_id, work_center_id, status)
                    VALUES (:poid, :opid, :wcid, 'pending')
                """), {
                    "poid": new_order_id, "opid": op.id, "wcid": op.work_center_id
                })

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
        
        return order_dict

    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@router.post("/orders/{order_id}/start", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.create"]))])
def start_production_order(order_id: int, current_user: UserResponse = Depends(get_current_user)):
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
        
        if order.status not in ['draft', 'confirmed']:
            raise HTTPException(status_code=400, detail=f"Cannot start order with status {order.status}")

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
                raise HTTPException(
                    status_code=400, 
                    detail=f"Insufficient raw materials: {shortage_details}"
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
                WHERE bc.bom_id = :bid
            """), {"bid": order.bom_id}).fetchall()
            
            total_material_cost = 0
            
            for comp in components:
                waste_factor = 1 + (comp.waste_percentage or 0) / 100.0
                # Variable BOM: quantity is % of order quantity
                if comp.is_percentage:
                    required_qty = (comp.quantity / 100.0 * order.quantity) * waste_factor
                else:
                    required_qty = comp.quantity * order.quantity * waste_factor
                cost = required_qty * (comp.cost_price or 0)
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
                # Create Journal Header
                journal = conn.execute(text("""
                    INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, created_by)
                    VALUES (:enum, CURRENT_DATE, :ref, :desc, 'posted', :currency, 1.0, :uid)
                    RETURNING id
                """), {
                    "enum": f"MFG-START-{order.order_number}",
                    "ref": order.order_number, 
                    "desc": f"Material Consumption for Production Order {order.order_number}",
                    "uid": current_user.id,
                    "currency": get_base_currency(conn)
                }).fetchone()
                
                # Debit WIP
                conn.execute(text("""
                    INSERT INTO journal_lines (journal_entry_id, account_id, description, debit, credit)
                    VALUES (:jid, :aid, :desc, :amt, 0)
                """), {"jid": journal.id, "aid": int(wip_acc_id), "desc": "WIP - Material Consumption", "amt": total_material_cost})
                
                # Credit Inventory
                conn.execute(text("""
                    INSERT INTO journal_lines (journal_entry_id, account_id, description, debit, credit)
                    VALUES (:jid, :aid, :desc, 0, :amt)
                """), {"jid": journal.id, "aid": int(rm_acc_id), "desc": "Raw Material Inventory", "amt": total_material_cost})

                # Update Account Balances
                update_account_balance(conn, account_id=int(wip_acc_id), debit_base=total_material_cost, credit_base=0)
                update_account_balance(conn, account_id=int(rm_acc_id), debit_base=0, credit_base=total_material_cost)

        trans.commit()
        
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
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@router.post("/orders/{order_id}/complete", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.create"]))])
def complete_production_order(order_id: int, current_user: UserResponse = Depends(get_current_user)):
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
        
        if order.status != 'in_progress':
            raise HTTPException(status_code=400, detail=f"Cannot complete order with status {order.status}")

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
                by_products = conn.execute(text("SELECT * FROM bom_outputs WHERE bom_id = :bid"), {"bid": order.bom_id}).fetchall()
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
        total_material_cost = 0
        if order.bom_id:
            components = conn.execute(text("""
                SELECT bc.*, p.cost_price 
                FROM bom_components bc
                JOIN products p ON bc.component_product_id = p.id
                WHERE bc.bom_id = :bid
            """), {"bid": order.bom_id}).fetchall()
            
            for comp in components:
                waste_factor = 1 + (comp.waste_percentage or 0) / 100.0
                total_material_cost += (comp.quantity * order.quantity * waste_factor * (comp.cost_price or 0))

        # B. Labor & Overhead Cost
        # Calculate actual run time from operations
        # Calculate actual run time from operations joined with work centers for cost
        ops_costs = conn.execute(text("""
            SELECT SUM((poo.actual_run_time / 60.0) * COALESCE(wc.cost_per_hour, 0)) as total_cost
            FROM production_order_operations poo
            LEFT JOIN work_centers wc ON poo.work_center_id = wc.id
            WHERE poo.production_order_id = :oid
        """), {"oid": order_id}).fetchone()
        
        total_labor_overhead_cost = ops_costs.total_cost or 0
        
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
             # Create Journal Header
            journal = conn.execute(text("""
                INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, created_by)
                VALUES (:enum, CURRENT_DATE, :ref, :desc, 'posted', :currency, 1.0, :uid)
                RETURNING id
            """), {
                "enum": f"MFG-COMP-{order.order_number}",
                "ref": order.order_number, 
                "desc": f"Production Completion (Mat: {total_material_cost}, Lab/OH: {total_labor_overhead_cost})",
                "uid": current_user.id,
                "currency": get_base_currency(conn)
            }).fetchone()
            
            # 1. Absorb Labor/Overhead into WIP (Debit WIP, Credit Absorption/Expense)
            if total_labor_overhead_cost > 0 and (labor_absorption_acc_id or overhead_absorption_acc_id):
                 absorb_acc = labor_absorption_acc_id or overhead_absorption_acc_id # Fallback
                 if absorb_acc:
                    # Debit WIP (Adding value)
                    conn.execute(text("""
                        INSERT INTO journal_lines (journal_entry_id, account_id, description, debit, credit)
                        VALUES (:jid, :aid, :desc, :amt, 0)
                    """), {"jid": journal.id, "aid": int(wip_acc_id), "desc": "WIP - Labor & Overhead Absorption", "amt": total_labor_overhead_cost})
                    
                    # Credit Absorption Account
                    conn.execute(text("""
                        INSERT INTO journal_lines (journal_entry_id, account_id, description, debit, credit)
                        VALUES (:jid, :aid, :desc, 0, :amt)
                    """), {"jid": journal.id, "aid": int(absorb_acc), "desc": "Absorbed Manufacturing Costs", "amt": total_labor_overhead_cost})

            # 2. Transfer Total Cost from WIP to FG (Debit FG, Credit WIP)
            # Debit Inventory (FG)
            conn.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, description, debit, credit)
                VALUES (:jid, :aid, :desc, :amt, 0)
            """), {"jid": journal.id, "aid": int(fg_acc_id), "desc": "Finished Goods Inventory", "amt": total_production_cost})
            
            # Credit WIP (Total Value Transfer)
            conn.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, description, debit, credit)
                VALUES (:jid, :aid, :desc, 0, :amt)
            """), {"jid": journal.id, "aid": int(wip_acc_id), "desc": "WIP - FG Transfer", "amt": total_production_cost})

            # Update Account Balances for all lines
            # Labor/Overhead absorption
            if total_labor_overhead_cost > 0 and (labor_absorption_acc_id or overhead_absorption_acc_id):
                absorb_acc_bal = labor_absorption_acc_id or overhead_absorption_acc_id
                if absorb_acc_bal:
                    update_account_balance(conn, account_id=int(wip_acc_id), debit_base=total_labor_overhead_cost, credit_base=0)
                    update_account_balance(conn, account_id=int(absorb_acc_bal), debit_base=0, credit_base=total_labor_overhead_cost)
            # FG transfer
            update_account_balance(conn, account_id=int(fg_acc_id), debit_base=total_production_cost, credit_base=0)
            update_account_balance(conn, account_id=int(wip_acc_id), debit_base=0, credit_base=total_production_cost)

        # 3. Update product cost_price using Weighted Average Cost (WAC)
        if order.quantity and total_production_cost > 0:
            new_unit_cost = total_production_cost / order.quantity
            # WAC: (existing_qty × old_cost + new_qty × new_cost) / (existing_qty + new_qty)
            existing = conn.execute(text("""
                SELECT COALESCE(SUM(quantity), 0) as qty FROM inventory 
                WHERE product_id = :pid
            """), {"pid": order.product_id}).fetchone()
            existing_qty = float(existing.qty) - order.quantity  # subtract newly added qty
            old_cost_row = conn.execute(text(
                "SELECT cost_price FROM products WHERE id = :pid"
            ), {"pid": order.product_id}).fetchone()
            old_cost = float(old_cost_row.cost_price or 0) if old_cost_row else 0
            
            if existing_qty + order.quantity > 0:
                wac = (existing_qty * old_cost + order.quantity * new_unit_cost) / (existing_qty + order.quantity)
            else:
                wac = new_unit_cost
            
            conn.execute(text("""
                UPDATE products SET cost_price = :cost, updated_at = NOW() WHERE id = :pid
            """), {"cost": round(wac, 4), "pid": order.product_id})

        trans.commit()
        
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
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


# ---- Cancel / Delete / Update Production Orders ----

@router.post("/orders/{order_id}/cancel", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.create"]))])
def cancel_production_order(order_id: int, current_user: UserResponse = Depends(get_current_user)):
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
        
        if order.status not in ['draft', 'confirmed']:
            raise HTTPException(status_code=400, detail=f"Cannot cancel order with status '{order.status}'. Only draft/confirmed orders can be cancelled.")
        
        conn.execute(text("""
            UPDATE production_orders SET status = 'cancelled', updated_at = NOW() WHERE id = :id
        """), {"id": order_id})
        
        trans.commit()
        
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
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.delete("/orders/{order_id}", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.delete"]))])
def delete_production_order(order_id: int, current_user: UserResponse = Depends(get_current_user)):
    """Delete a production order. Only draft orders can be deleted."""
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        order = conn.execute(text("SELECT * FROM production_orders WHERE id = :id"), {"id": order_id}).fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.status != 'draft':
            raise HTTPException(status_code=400, detail="Only draft orders can be deleted")
        
        # Delete operations first (cascade should handle, but be explicit)
        conn.execute(text("DELETE FROM production_order_operations WHERE production_order_id = :id"), {"id": order_id})
        conn.execute(text("DELETE FROM production_orders WHERE id = :id"), {"id": order_id})
        
        trans.commit()
        return {"message": "Production order deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.put("/orders/{order_id}", response_model=ProductionOrderResponse, dependencies=[Depends(require_permission("manufacturing.manage"))])
def update_production_order(order_id: int, order: ProductionOrderCreate, current_user: UserResponse = Depends(get_current_user)):
    """Update a production order. Only draft orders can be updated."""
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        existing = conn.execute(text("SELECT * FROM production_orders WHERE id = :id"), {"id": order_id}).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Order not found")
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
                SELECT * FROM manufacturing_operations WHERE route_id = :rid ORDER BY sequence
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
        
        return order_dict
    except HTTPException:
        raise
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


# ---- Delete Work Center / Route / BOM ----

@router.delete("/work-centers/{wc_id}", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.delete"]))])
def delete_work_center(wc_id: int, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        # Check if in use by any operations
        in_use = conn.execute(text("""
            SELECT COUNT(*) FROM manufacturing_operations WHERE work_center_id = :id
        """), {"id": wc_id}).scalar()
        if in_use > 0:
            raise HTTPException(status_code=400, detail=f"Work center is used in {in_use} operation(s). Remove them first.")
        
        result = conn.execute(text("DELETE FROM work_centers WHERE id = :id"), {"id": wc_id})
        conn.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Work center not found")
        return {"message": "Work center deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.delete("/routes/{route_id}", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.delete"]))])
def delete_route(route_id: int, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        # Check if in use by any production orders
        in_use = conn.execute(text("""
            SELECT COUNT(*) FROM production_orders WHERE route_id = :id AND status NOT IN ('cancelled', 'completed')
        """), {"id": route_id}).scalar()
        if in_use > 0:
            raise HTTPException(status_code=400, detail=f"Route is used in {in_use} active production order(s).")
        
        conn.execute(text("DELETE FROM manufacturing_operations WHERE route_id = :id"), {"id": route_id})
        result = conn.execute(text("DELETE FROM manufacturing_routes WHERE id = :id"), {"id": route_id})
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Route not found")
        
        trans.commit()
        return {"message": "Route and its operations deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.delete("/boms/{bom_id}", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.delete"]))])
def delete_bom(bom_id: int, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    trans = conn.begin()
    try:
        # Check if in use
        in_use = conn.execute(text("""
            SELECT COUNT(*) FROM production_orders WHERE bom_id = :id AND status NOT IN ('cancelled', 'completed')
        """), {"id": bom_id}).scalar()
        if in_use > 0:
            raise HTTPException(status_code=400, detail=f"BOM is used in {in_use} active production order(s).")
        
        conn.execute(text("DELETE FROM bom_outputs WHERE bom_id = :id"), {"id": bom_id})
        conn.execute(text("DELETE FROM bom_components WHERE bom_id = :id"), {"id": bom_id})
        result = conn.execute(text("DELETE FROM bill_of_materials WHERE id = :id"), {"id": bom_id})
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="BOM not found")
        
        trans.commit()
        return {"message": "BOM deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


# --- JOB CARDS (MFG-007) ---

@router.post("/operations/{op_id}/start", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.create"]))])
def start_operation(op_id: int, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        # Check if operation is already in progress
        op = conn.execute(text("SELECT * FROM production_order_operations WHERE id = :id"), {"id": op_id}).fetchone()
        if not op:
            raise HTTPException(status_code=404, detail="Operation not found")
        
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
        
        # Re-fetch
        updated = conn.execute(text("SELECT * FROM production_order_operations WHERE id = :id"), {"id": op_id}).fetchone()
        return updated
    finally:
        conn.close()

@router.post("/operations/{op_id}/pause", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.create"]))])
def pause_operation(op_id: int, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        op = conn.execute(text("SELECT * FROM production_order_operations WHERE id = :id"), {"id": op_id}).fetchone()
        if not op or op.status != 'in_progress':
            raise HTTPException(status_code=400, detail="Only in-progress operations can be paused")

        # Update status
        conn.execute(text("""
            UPDATE production_order_operations 
            SET status = 'paused', updated_at = NOW()
            WHERE id = :id
        """), {"id": op_id})
        conn.commit()
        return conn.execute(text("SELECT * FROM production_order_operations WHERE id = :id"), {"id": op_id}).fetchone()
    finally:
        conn.close()

@router.post("/operations/{op_id}/complete", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.create"]))])
def complete_operation(op_id: int, completed_qty: float, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        op = conn.execute(text("SELECT * FROM production_order_operations WHERE id = :id"), {"id": op_id}).fetchone()
        if not op:
            raise HTTPException(status_code=404, detail="Operation not found")

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
                   mo.description as operation_description, po.quantity as planned_quantity
            FROM production_order_operations poo
            JOIN production_orders po ON poo.production_order_id = po.id
            JOIN work_centers wc ON poo.work_center_id = wc.id
            LEFT JOIN manufacturing_operations mo ON poo.operation_id = mo.id
            WHERE poo.status IN ('pending', 'in_progress', 'paused')
            ORDER BY poo.sequence ASC, poo.created_at DESC
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

        # Fetch BOM components
        components = conn.execute(text("""
            SELECT bc.*, p.product_name, p.reorder_level,
                   (SELECT SUM(quantity) FROM inventory WHERE product_id = p.id) as on_hand
            FROM bom_components bc
            JOIN products p ON bc.component_product_id = p.id
            WHERE bc.bom_id = :bid
        """), {"bid": order.bom_id}).fetchall()

        mrp_items = []
        for comp in components:
            required = float(comp.quantity) * float(order.quantity)
            on_hand = float(comp.on_hand or 0)
            shortage = max(0.0, required - on_hand)
            
            action = "none"
            if shortage > 0:
                action = "purchase_order" # Simplified: Always suggest PO for now

            mrp_items.append({
                "product_id": comp.component_product_id,
                "product_name": comp.product_name,
                "required_quantity": required,
                "available_quantity": on_hand,
                "on_hand_quantity": on_hand,
                "on_order_quantity": 0, # To be improved with PO link
                "shortage_quantity": shortage,
                "lead_time_days": 1, # Default
                "suggested_action": action,
                "status": "pending"
            })

        # Save Plan? For now just return as response
        from datetime import datetime
        plan = {
            "id": 0,
            "plan_name": f"MRP for {order.order_number}",
            "production_order_id": order_id,
            "status": "draft",
            "calculated_at": datetime.now(),
            "items": mrp_items
        }
        return plan
    finally:
        conn.close()

# ==========================================
# 6. EQUIPMENT & MAINTENANCE
# ==========================================

@router.get("/equipment", response_model=List[EquipmentResponse], dependencies=[Depends(require_permission("manufacturing.view"))])
def list_equipment(current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        equip = conn.execute(text("""
            SELECT e.*, wc.name as work_center_name
            FROM manufacturing_equipment e
            LEFT JOIN work_centers wc ON e.work_center_id = wc.id
            ORDER BY e.id DESC
        """)).fetchall()
        return [dict(e._mapping) for e in equip]
    finally:
        conn.close()

@router.post("/equipment", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.create"]))])
def create_equipment(equip: EquipmentCreate, current_user: UserResponse = Depends(get_current_user)):
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
        return dict(new_equip._mapping)
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@router.get("/maintenance-logs", response_model=List[MaintenanceLogResponse], dependencies=[Depends(require_permission("manufacturing.view"))])
def list_maintenance_logs(equipment_id: Optional[int] = None, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        query = """
            SELECT ml.*, e.name as equipment_name, u.full_name as performed_by_name
            FROM maintenance_logs ml
            LEFT JOIN manufacturing_equipment e ON ml.equipment_id = e.id
            LEFT JOIN company_users u ON ml.performed_by = u.id
        """
        params = {}
        if equipment_id:
            query += " WHERE ml.equipment_id = :eid"
            params["eid"] = equipment_id
            
        query += " ORDER BY ml.maintenance_date DESC"
        
        logs = conn.execute(text(query), params).fetchall()
        return [dict(l._mapping) for l in logs]
    finally:
        conn.close()

@router.post("/maintenance-logs", dependencies=[Depends(require_permission(["manufacturing.manage", "manufacturing.create"]))])
def create_maintenance_log(log: MaintenanceLogCreate, current_user: UserResponse = Depends(get_current_user)):
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
        # Fetch updated log with joins
        log_res = conn.execute(text("""
            SELECT ml.*, e.name as equipment_name, u.full_name as performed_by_name
            FROM maintenance_logs ml
            LEFT JOIN manufacturing_equipment e ON ml.equipment_id = e.id
            LEFT JOIN company_users u ON ml.performed_by = u.id
            WHERE ml.id = :lid
        """), {"lid": new_log.id}).fetchone()
        
        return dict(log_res._mapping)
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


# ==========================================
# 7. MANUFACTURING REPORTS
# ==========================================

@router.get("/reports/production-cost", dependencies=[Depends(require_permission("manufacturing.view"))])
def report_production_cost(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Production Cost Report: Actual vs Estimated costs for completed production orders.
    """
    conn = get_db_connection(current_user.company_id)
    try:
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
                    "SELECT id FROM bill_of_materials WHERE product_id = :pid AND is_active = true LIMIT 1"
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
        wcs = conn.execute(text("SELECT * FROM work_centers ORDER BY name")).fetchall()
        
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
                "cost_per_hour": float(wc.cost_per_hour or 0),
                "total_operations": stats.total_operations,
                "completed_operations": stats.completed_operations,
                "total_run_time_hours": round(used_hours, 2),
                "total_output": float(stats.total_output or 0),
                "avg_cycle_time_min": round(float(stats.avg_run_time_min or 0), 2),
                "utilization_percent": round(utilization, 2),
                "total_cost": round(used_hours * float(wc.cost_per_hour or 0), 2),
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
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Material Consumption Report: Raw materials consumed by production orders.
    """
    conn = get_db_connection(current_user.company_id)
    try:
        date_filter = ""
        params = {}
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
                "total_consumed": round(float(r.total_consumed or 0), 4),
                "order_count": r.order_count,
                "avg_unit_cost": round(float(r.avg_unit_cost or 0), 4),
                "total_cost": round(float(r.total_cost or 0), 2),
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
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Production Summary Dashboard: Overview of all production activities.
    """
    conn = get_db_connection(current_user.company_id)
    try:
        date_filter = ""
        params = {}
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
        
        by_status = {row.status: {"count": row.count, "total_qty": float(row.total_qty)} for row in status_counts}
        
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
            WHERE next_maintenance_date <= CURRENT_DATE + INTERVAL '7 days' AND status != 'decommissioned'
        """)).scalar()
        
        return {
            "report_name": "Production Summary",
            "period": {"start": str(start_date) if start_date else "All", "end": str(end_date) if end_date else "All"},
            "orders_by_status": by_status,
            "total_orders": sum(s["count"] for s in by_status.values()),
            "top_produced_products": [
                {"product_name": r.product_name, "total_produced": float(r.total_produced or 0), "order_count": r.order_count}
                for r in top_products
            ],
            "equipment_maintenance_due": maint_due or 0,
        }
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
        bom = conn.execute(text("SELECT * FROM bill_of_materials WHERE id = :id"), {"id": bom_id}).fetchone()
        if not bom:
            raise HTTPException(status_code=404, detail="BOM غير موجود")

        components = conn.execute(text("""
            SELECT bc.*, p.product_name, p.cost_price, u.unit_name
            FROM bom_components bc
            JOIN products p ON bc.component_product_id = p.id
            LEFT JOIN product_units u ON p.unit_id = u.id
            WHERE bc.bom_id = :bid
        """), {"bid": bom_id}).fetchall()

        result_components = []
        total_material_cost = 0.0

        for c in components:
            waste_factor = 1 + (c.waste_percentage or 0) / 100.0
            if c.is_percentage:
                # Variable BOM: base qty = quantity% of order
                computed_qty = round((c.quantity / 100.0 * quantity) * waste_factor, 4)
            else:
                # Fixed BOM: qty per unit × order qty
                computed_qty = round(c.quantity * quantity * waste_factor, 4)

            unit_cost = float(c.cost_price or 0)
            line_cost = computed_qty * unit_cost
            total_material_cost += line_cost

            # Check available inventory
            inv = conn.execute(text(
                "SELECT COALESCE(SUM(quantity), 0) as qty FROM inventory WHERE product_id = :pid"
            ), {"pid": c.component_product_id}).scalar()
            available = float(inv)

            result_components.append({
                "component_product_id": c.component_product_id,
                "product_name": c.product_name,
                "unit": c.unit_name,
                "is_percentage": bool(c.is_percentage),
                "bom_quantity": float(c.quantity),
                "computed_quantity": computed_qty,
                "waste_percentage": float(c.waste_percentage or 0),
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
        raise HTTPException(status_code=500, detail=str(e))
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
        rows = conn.execute(text("""
            SELECT q.*, u.full_name as checked_by_name,
                   op.name as operation_name
            FROM mfg_qc_checks q
            LEFT JOIN company_users u ON q.checked_by = u.id
            LEFT JOIN manufacturing_operations op ON q.operation_id = op.id
            WHERE q.production_order_id = :oid
            ORDER BY q.created_at
        """), {"oid": order_id}).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()


@router.post("/orders/{order_id}/qc-checks", status_code=201, dependencies=[Depends(require_permission("manufacturing.manage"))])
def create_qc_check(
    order_id: int,
    qc: QCCheckCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """إضافة فحص جودة لأمر إنتاج"""
    conn = get_db_connection(current_user.company_id)
    try:
        order = conn.execute(text("SELECT id, status FROM production_orders WHERE id=:id"), {"id": order_id}).fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="أمر الإنتاج غير موجود")
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
        return {"success": True, "id": qc_id}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/qc-checks/{qc_id}/record-result", dependencies=[Depends(require_permission("manufacturing.manage"))])
def record_qc_result(
    qc_id: int,
    res: QCResultRecord,
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

        qc = conn.execute(text("SELECT * FROM mfg_qc_checks WHERE id=:id"), {"id": qc_id}).fetchone()
        if not qc:
            raise HTTPException(status_code=404, detail="فحص الجودة غير موجود")

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
        raise HTTPException(status_code=500, detail=str(e))
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
            WHERE q.result IN ('fail', 'pending')
            ORDER BY q.created_at DESC
        """)).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()
