"""
AMAN ERP — Intercompany Accounting v2 Router
Entity group management, intercompany transactions with reciprocal JEs,
consolidation elimination, account mappings, and balance reporting.

Uses intercompany_service.py (entity_groups, intercompany_transactions_v2, intercompany_account_mappings tables).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
import logging

from routers.auth import get_current_user
from utils.permissions import require_permission
from utils.limiter import limiter
from schemas.intercompany import (
    EntityGroupCreate, EntityGroupRead, IntercompanyTransactionCreate,
    IntercompanyTransactionRead, ConsolidationRequest, ConsolidationResult,
    AccountMappingCreate, AccountMappingRead,
)
from services import intercompany_service

router = APIRouter(prefix="/accounting/intercompany", tags=["المعاملات بين الشركات v2"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Entity Group CRUD
# ---------------------------------------------------------------------------

@router.get("/entities", dependencies=[Depends(require_permission("accounting.view"))])
@limiter.limit("200/minute")
def list_entities(request: Request, current_user=Depends(get_current_user)):
    """Return entity group tree."""
    company_id = current_user.get("company_id") if isinstance(current_user, dict) else current_user.company_id
    return intercompany_service.get_entity_tree(str(company_id))


@router.post("/entities", status_code=201, dependencies=[Depends(require_permission("accounting.edit"))])
@limiter.limit("100/minute")
def create_entity(request: Request, data: EntityGroupCreate, current_user=Depends(get_current_user)):
    """Create a new entity group node."""
    company_id = current_user.get("company_id") if isinstance(current_user, dict) else current_user.company_id
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    return intercompany_service.create_entity_group(data.model_dump(), str(company_id), user_id)


# ---------------------------------------------------------------------------
# Intercompany Transactions
# ---------------------------------------------------------------------------

@router.post("/transactions", status_code=201, dependencies=[Depends(require_permission("accounting.edit"))])
@limiter.limit("100/minute")
def create_transaction(request: Request, data: IntercompanyTransactionCreate, current_user=Depends(get_current_user)):
    """Create intercompany transaction with reciprocal JEs."""
    company_id = current_user.get("company_id") if isinstance(current_user, dict) else current_user.company_id
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    try:
        return intercompany_service.create_transaction(data.model_dump(), str(company_id), user_id)
    except ValueError as e:
        logger.exception("Internal error")
        raise HTTPException(status_code=400, detail="طلب غير صالح")


@router.get("/transactions", dependencies=[Depends(require_permission("accounting.view"))])
@limiter.limit("200/minute")
def list_transactions(
    request: Request,
    entity_id: Optional[int] = None,
    current_user=Depends(get_current_user),
):
    """List intercompany transactions (v2 tables)."""
    company_id = current_user.get("company_id") if isinstance(current_user, dict) else current_user.company_id
    return intercompany_service.get_transactions(str(company_id), status_filter, entity_id)


@router.get("/transactions/{txn_id}", dependencies=[Depends(require_permission("accounting.view"))])
@limiter.limit("200/minute")
def get_transaction(request: Request, txn_id: int, current_user=Depends(get_current_user)):
    """Get a single intercompany transaction."""
    company_id = current_user.get("company_id") if isinstance(current_user, dict) else current_user.company_id
    result = intercompany_service.get_transaction_by_id(txn_id, str(company_id))
    if not result:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return result


# ---------------------------------------------------------------------------
# Consolidation
# ---------------------------------------------------------------------------

@router.post("/consolidate", dependencies=[Depends(require_permission("accounting.edit"))])
@limiter.limit("100/minute")
def consolidate(request: Request, data: ConsolidationRequest, current_user=Depends(get_current_user)):
    """Run consolidation elimination for an entity group."""
    company_id = current_user.get("company_id") if isinstance(current_user, dict) else current_user.company_id
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    try:
        return intercompany_service.run_consolidation(
            entity_group_id=data.entity_group_id,
            company_id=str(company_id),
            user_id=user_id,
            as_of_date=data.as_of_date,
        )
    except ValueError as e:
        logger.exception("Internal error")
        raise HTTPException(status_code=400, detail="طلب غير صالح")


# ---------------------------------------------------------------------------
# Balances Report
# ---------------------------------------------------------------------------

@router.get("/balances", dependencies=[Depends(require_permission("accounting.view"))])
@limiter.limit("200/minute")
def get_balances(request: Request, current_user=Depends(get_current_user)):
    """Report outstanding intercompany balances."""
    company_id = current_user.get("company_id") if isinstance(current_user, dict) else current_user.company_id
    return intercompany_service.get_intercompany_balances(str(company_id))


# ---------------------------------------------------------------------------
# Account Mappings
# ---------------------------------------------------------------------------

@router.get("/mappings", dependencies=[Depends(require_permission("accounting.view"))])
@limiter.limit("200/minute")
def list_mappings(request: Request, current_user=Depends(get_current_user)):
    """List intercompany account mappings."""
    company_id = current_user.get("company_id") if isinstance(current_user, dict) else current_user.company_id
    return intercompany_service.get_account_mappings(str(company_id))


@router.post("/mappings", status_code=201, dependencies=[Depends(require_permission("accounting.edit"))])
@limiter.limit("100/minute")
def create_mapping(request: Request, data: AccountMappingCreate, current_user=Depends(get_current_user)):
    """Create a new intercompany account mapping."""
    company_id = current_user.get("company_id") if isinstance(current_user, dict) else current_user.company_id
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    return intercompany_service.create_account_mapping(data.model_dump(), str(company_id), user_id)
