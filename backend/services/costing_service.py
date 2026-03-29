
from sqlalchemy import text
from typing import Optional
from decimal import Decimal, ROUND_HALF_UP

# FIN-FIX: Precision constants for costing calculations
_D4 = Decimal('0.0001')
_dec = lambda v: Decimal(str(v or 0))

class CostingService:
    @staticmethod
    def get_active_policy(db):
        """Get the active costing policy for the current company context."""
        policy = db.execute(text("SELECT policy_type FROM costing_policies WHERE is_active = TRUE LIMIT 1")).scalar()
        return policy or 'global_wac'

    @staticmethod
    def calculate_new_cost(
        current_qty: float,
        current_cost: float,
        new_qty: float,
        new_price: float
    ) -> float:
        """Standard WAC Formula using Decimal for precision."""
        d_curr_qty = _dec(current_qty)
        d_curr_cost = _dec(current_cost)
        d_new_qty = _dec(new_qty)
        d_new_price = _dec(new_price)

        # Guard: reset if current qty is negative (corrupted state)
        if d_curr_qty < 0:
            d_curr_qty = Decimal('0')
            d_curr_cost = Decimal('0')

        total_qty = d_curr_qty + d_new_qty
        if total_qty <= 0:
            return float(d_new_price)

        total_value = (d_curr_qty * d_curr_cost) + (d_new_qty * d_new_price)
        result = (total_value / total_qty).quantize(_D4, ROUND_HALF_UP)
        return float(result)


    @staticmethod
    def update_cost(
        db,
        product_id: int,
        warehouse_id: int,
        new_qty: float,
        new_price: float
    ):
        """
        Updates product cost based on the active policy.
        CALLED BEFORE INVENTORY QUANTITY UPDATE (to use current stock stats).
        """
        policy_type = CostingService.get_active_policy(db)
        
        # 1. Global WAC Strategy
        if policy_type == 'global_wac':
            # Calculate Global Stock
            current_stats = db.execute(text("""
                SELECT cost_price, 
                       (SELECT COALESCE(SUM(quantity), 0) FROM inventory WHERE product_id = :pid) as total_qty
                FROM products WHERE id = :pid
            """), {"pid": product_id}).fetchone()
            
            curr_qty = float(current_stats.total_qty or 0)
            curr_cost = float(current_stats.cost_price or 0)
            
            new_wac = CostingService.calculate_new_cost(curr_qty, curr_cost, new_qty, new_price)
            
            # Update Product Master (Global Cost)
            db.execute(text("UPDATE products SET cost_price = :cost, last_purchase_price = :last WHERE id = :pid"), 
                       {"cost": new_wac, "last": new_price, "pid": product_id})
            
            # Sync with inventory rows if they exist (for future per-wh compatibility)
            db.execute(text("UPDATE inventory SET average_cost = :cost WHERE product_id = :pid"),
                       {"cost": new_wac, "pid": product_id})
            
        # 2. Per-Warehouse WAC Strategy
        elif policy_type == 'per_warehouse_wac':
            # Calculate Warehouse Stock
            current_stats = db.execute(text("""
                SELECT average_cost, quantity 
                FROM inventory WHERE product_id = :pid AND warehouse_id = :wh
            """), {"pid": product_id, "wh": warehouse_id}).fetchone()
            
            curr_cost = float(current_stats.average_cost or 0) if current_stats else 0
            curr_qty = float(current_stats.quantity or 0) if current_stats else 0
            
            new_wac = CostingService.calculate_new_cost(curr_qty, curr_cost, new_qty, new_price)
            
            # Update Inventory Cost (Warehouse Specific)
            exists = db.execute(text("SELECT 1 FROM inventory WHERE product_id=:pid AND warehouse_id=:wh"), 
                                     {"pid": product_id, "wh": warehouse_id}).scalar()
            
            if exists:
                db.execute(text("""
                    UPDATE inventory SET average_cost = :cost, last_costing_update = CURRENT_TIMESTAMP
                    WHERE product_id = :pid AND warehouse_id = :wh
                """), {"cost": new_wac, "pid": product_id, "wh": warehouse_id})
            else:
                db.execute(text("""
                    INSERT INTO inventory (product_id, warehouse_id, quantity, average_cost, last_costing_update)
                    VALUES (:pid, :wh, 0, :cost, CURRENT_TIMESTAMP)
                """), {"pid": product_id, "wh": warehouse_id, "cost": new_wac})
                
            # Update Product Master for reporting (simple weighted average of all warehouse costs)
            # The warehouse row was ALREADY updated above, so just compute from existing inventory rows
            all_inventory = db.execute(text("""
                SELECT SUM(quantity * average_cost) as total_val, SUM(quantity) as total_qty
                FROM inventory WHERE product_id = :pid AND quantity > 0
            """), {"pid": product_id}).fetchone()
            
            cur_total_val = float(all_inventory.total_val or 0)
            cur_total_qty = float(all_inventory.total_qty or 0)
            
            # The inventory table already reflects the new cost; just compute the weighted average
            global_wac = cur_total_val / cur_total_qty if cur_total_qty > 0 else new_price
            
            db.execute(text("UPDATE products SET cost_price = :cost, last_purchase_price = :last WHERE id = :pid"),
                       {"cost": global_wac, "last": new_price, "pid": product_id})

        # Create Snapshot after update
        CostingService.create_snapshot(db, warehouse_id, product_id)

    @staticmethod
    def get_cogs_cost(db, product_id: int, warehouse_id: Optional[int] = None) -> float:
        """Get the unit cost for COGS based on current policy."""
        policy_type = CostingService.get_active_policy(db)
        
        if policy_type == 'per_warehouse_wac' and warehouse_id:
            cost = db.execute(text("""
                SELECT average_cost FROM inventory 
                WHERE product_id = :pid AND warehouse_id = :wh
            """), {"pid": product_id, "wh": warehouse_id}).scalar()
            if cost is not None:
                return float(cost)
        
        # Default to Global Product Cost
        cost = db.execute(text("SELECT cost_price FROM products WHERE id = :id"), {"id": product_id}).scalar()
        return float(cost or 0)

    @staticmethod
    def create_snapshot(db, warehouse_id=None, product_id=None):
        """Creates a snapshot of current costs for audit/history."""
        policy_type = CostingService.get_active_policy(db)
        query = """
            INSERT INTO inventory_cost_snapshots (warehouse_id, product_id, average_cost, quantity, policy_type)
            SELECT i.warehouse_id, i.product_id, i.average_cost, i.quantity, :policy
            FROM inventory i
            WHERE 1=1
        """
        params = {"policy": policy_type}
        if warehouse_id:
            query += " AND i.warehouse_id = :wh"
            params["wh"] = warehouse_id
        if product_id:
            query += " AND i.product_id = :pid"
            params["pid"] = product_id
            
        db.execute(text(query), params)

    @staticmethod
    def validate_policy_switch(db, new_policy_type):
        """Analyzes impact before switching policy."""
        # This is a simplified analysis for the MVP refinement
        # affected_products: products where costs differ between warehouses
        impact = db.execute(text("""
            SELECT 
                COUNT(DISTINCT product_id) as affected_products,
                SUM(ABS(average_cost - (SELECT cost_price FROM products p WHERE p.id = product_id))) as total_deviation
            FROM inventory
            WHERE quantity > 0
        """)).fetchone()
        
        return {
            "affected_products_count": impact.affected_products or 0,
            "total_cost_impact": float(impact.total_deviation or 0)
        }
