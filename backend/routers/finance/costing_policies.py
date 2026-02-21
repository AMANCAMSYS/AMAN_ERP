
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from database import get_db_connection
from routers.auth import get_current_user
from utils.permissions import require_permission


from services.costing_service import CostingService
import json

from schemas.costing_policies import CostingPolicySet, CostingPolicyHistoryResponse

router = APIRouter(prefix="/costing-policies", tags=["Costing Policies"])

@router.get("/current", dependencies=[Depends(require_permission("settings.view"))])
def get_current_policy(current_user: dict = Depends(get_current_user)):
    """Get the currently active costing policy"""
    db = get_db_connection(current_user.company_id)
    try:
        policy = db.execute(text("""
            SELECT policy_type, policy_name, is_active, created_at, description 
            FROM costing_policies 
            WHERE is_active = TRUE 
            LIMIT 1
        """)).fetchone()
        
        if not policy:
            return {
                "policy_type": "global_wac", 
                "policy_name": "Global WAC (Default)", 
                "is_active": True,
                "description": "Default system policy"
            }
            
        return dict(policy._mapping)
    finally:
        db.close()

@router.post("/set", dependencies=[Depends(require_permission("settings.edit"))])
def set_costing_policy(policy_data: CostingPolicySet, current_user: dict = Depends(get_current_user)):
    """Change the costing policy with impact analysis"""
    if policy_data.policy_type not in ['global_wac', 'per_warehouse_wac', 'hybrid', 'smart']:
        raise HTTPException(status_code=400, detail="Invalid policy type")
        
    db = get_db_connection(current_user.company_id)
    try:
        # 1. Get current active policy
        current_policy = db.execute(text("SELECT policy_type FROM costing_policies WHERE is_active = TRUE LIMIT 1")).scalar()
        
        if current_policy == policy_data.policy_type:
             return {"message": "Policy is already set to this type", "status": "no_change"}
             
        # 2. PERFORM IMPACT ANALYSIS (V2)
        impact = CostingService.validate_policy_switch(db, policy_data.policy_type)
        
        # 3. Deactivate old
        db.execute(text("UPDATE costing_policies SET is_active = FALSE WHERE is_active = TRUE"))
        
        # 4. Insert New
        new_name = {
            'global_wac': 'Global WAC',
            'per_warehouse_wac': 'Per-Warehouse WAC',
            'hybrid': 'Hybrid Costing',
            'smart': 'Smart Costing'
        }.get(policy_data.policy_type, 'Unknown Policy')
        
        db.execute(text("""
            INSERT INTO costing_policies (policy_name, policy_type, description, is_active, created_by)
            VALUES (:name, :type, :desc, TRUE, :user)
        """), {
            "name": new_name,
            "type": policy_data.policy_type,
            "desc": f"Policy changed to {new_name}",
            "user": current_user.id
        })
        
        # 5. Log History with Impact (V2)
        db.execute(text("""
            INSERT INTO costing_policy_history 
            (old_policy_type, new_policy_type, changed_by, reason, affected_products_count, total_cost_impact, status)
            VALUES (:old, :new, :user, :reason, :count, :impact, 'completed')
        """), {
            "old": current_policy,
            "new": policy_data.policy_type,
            "user": current_user.id,
            "reason": policy_data.reason,
            "count": impact["affected_products_count"],
            "impact": impact["total_cost_impact"]
        })
        
        # 6. MIGRATION LOGIC
        if current_policy == 'global_wac' and policy_data.policy_type == 'per_warehouse_wac':
             db.execute(text("""
                UPDATE inventory 
                SET average_cost = p.cost_price, 
                    policy_version = 2,
                    last_costing_update = CURRENT_TIMESTAMP
                FROM products p 
                WHERE inventory.product_id = p.id AND (inventory.average_cost = 0 OR inventory.average_cost IS NULL)
             """))
        
        # 7. Create Full System Snapshot (V2)
        CostingService.create_snapshot(db)
             
        db.commit()
        return {"message": f"Policy updated to {new_name}", "status": "success", "impact": impact}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/history", response_model=List[CostingPolicyHistoryResponse], dependencies=[Depends(require_permission("settings.view"))])
def get_policy_history(current_user: dict = Depends(get_current_user)):
    """Get history of policy changes with impact metrics"""
    db = get_db_connection(current_user.company_id)
    try:
        result = db.execute(text("""
            SELECT h.*, u.full_name as changed_by_name
            FROM costing_policy_history h
            LEFT JOIN company_users u ON h.changed_by = u.id
            ORDER BY h.change_date DESC
        """)).fetchall()
        return [dict(r._mapping) for r in result]
    finally:
        db.close()
