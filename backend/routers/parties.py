from fastapi import APIRouter, Depends, HTTPException, status, Query
from utils.i18n import http_error
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

from database import get_db_connection
from routers.auth import get_current_user
from utils.permissions import require_permission
from schemas.parties import PartyResponse
import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/parties", tags=["الجهات (العملاء والموردين)"])

@router.get("/customers", response_model=dict, dependencies=[Depends(require_permission(["parties.view", "sales.view"]))])
async def get_customers(
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """جلب قائمة العملاء"""
    db = get_db_connection(current_user.company_id)
    try:
        query = """
            SELECT 
                id, name, name_en, email, phone, tax_number, address,
                current_balance as balance, credit_limit,
                CASE WHEN status = 'active' THEN true ELSE false END as is_active,
                'customer' as party_type
            FROM parties 
            WHERE is_customer = true
        """
        params = {"limit": limit, "offset": offset}
        
        if search:
            query += " AND (name ILIKE :search OR phone LIKE :search)"
            params["search"] = f"%{search}%"

        # PTY-007: Enforce branch filtering
        allowed = getattr(current_user, 'allowed_branches', []) or []
        if allowed and "*" not in getattr(current_user, 'permissions', []):
            branch_placeholders = ", ".join(f":_ab_{i}" for i in range(len(allowed)))
            query += f" AND branch_id IN ({branch_placeholders})"
            for i, bid in enumerate(allowed):
                params[f"_ab_{i}"] = bid
            
        query += " ORDER BY name ASC LIMIT :limit OFFSET :offset"
        
        result = db.execute(text(query), params)
        parties = []
        for row in result:
             parties.append(dict(row._mapping))
             
        return {"items": parties}
    except Exception as e:
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()

@router.get("/suppliers", response_model=dict, dependencies=[Depends(require_permission(["parties.view", "buying.view"]))])
async def get_suppliers(
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """جلب قائمة الموردين"""
    db = get_db_connection(current_user.company_id)
    try:
        query = """
            SELECT 
                id, name, name_en, email, phone, tax_number, address,
                current_balance as balance, credit_limit,
                CASE WHEN status = 'active' THEN true ELSE false END as is_active,
                'supplier' as party_type
            FROM parties 
            WHERE is_supplier = true
        """
        params = {"limit": limit, "offset": offset}
        
        if search:
            query += " AND (name ILIKE :search OR phone LIKE :search)"
            params["search"] = f"%{search}%"

        # PTY-007: Enforce branch filtering
        allowed = getattr(current_user, 'allowed_branches', []) or []
        if allowed and "*" not in getattr(current_user, 'permissions', []):
            branch_placeholders = ", ".join(f":_ab_{i}" for i in range(len(allowed)))
            query += f" AND branch_id IN ({branch_placeholders})"
            for i, bid in enumerate(allowed):
                params[f"_ab_{i}"] = bid
            
        query += " ORDER BY name ASC LIMIT :limit OFFSET :offset"
        
        result = db.execute(text(query), params)
        parties = []
        for row in result:
             parties.append(dict(row._mapping))
             
        return {"items": parties}
    except Exception as e:
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
