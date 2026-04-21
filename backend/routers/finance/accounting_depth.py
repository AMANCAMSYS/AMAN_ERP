"""
Phase 5 accounting-depth REST surface.

Thin HTTP layer over the scaffolded services:
  * IFRS 9 ECL provision compute.
  * IAS 2 NRV write-down test.
  * IAS 36 CGU impairment test.
  * IFRS 15 revenue contracts + recognition.
  * E-invoicing submissions (EG ETA / UAE FTA adapters).

All routes are guarded by `finance.*` permissions so integrations cannot
spin up provisions or submit invoices without explicit grants.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text

from database import get_db_connection
from integrations.einvoicing import get_adapter
from routers.auth import get_current_user
from services import ecl_service, ifrs15_revenue_service, impairment_service, nrv_service
from utils.permissions import require_permission

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/finance/accounting-depth", tags=["accounting-depth"])


def _close(db):
    try:
        db.close()
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════
# IFRS 9 — Expected Credit Loss
# ═══════════════════════════════════════════════════════════════════════════

class ECLComputeRequest(BaseModel):
    as_of_date: Optional[date] = None
    post_journal: bool = False
    provision_account_id: Optional[int] = None
    expense_account_id: Optional[int] = None


@router.post(
    "/ecl/compute",
    dependencies=[Depends(require_permission("finance.accounting_post"))],
)
def ecl_compute(body: ECLComputeRequest, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        return ecl_service.compute_ecl_provision(
            db,
            company_id=current_user.company_id,
            as_of_date=body.as_of_date,
            post_journal=body.post_journal,
            provision_account_id=body.provision_account_id,
            expense_account_id=body.expense_account_id,
            user_id=current_user.id,
            username=getattr(current_user, "username", None),
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except RuntimeError as e:
        db.rollback()
        raise HTTPException(status.HTTP_412_PRECONDITION_FAILED, str(e))
    except Exception:
        db.rollback()
        logger.exception("ECL compute failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error")
    finally:
        _close(db)


@router.get(
    "/ecl/provisions",
    dependencies=[Depends(require_permission("finance.accounting_view"))],
)
def ecl_list(current_user=Depends(get_current_user), limit: int = 50):
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(text("""
            SELECT id, as_of_date, total_exposure, provision_amount,
                   journal_entry_id, created_at
            FROM ecl_provisions ORDER BY as_of_date DESC, id DESC LIMIT :lim
        """), {"lim": limit}).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        _close(db)


# ═══════════════════════════════════════════════════════════════════════════
# IAS 2 — NRV
# ═══════════════════════════════════════════════════════════════════════════

class NRVRunRequest(BaseModel):
    as_of_date: Optional[date] = None
    selling_cost_rate: Decimal = Decimal("0.05")
    post_journal: bool = False
    inventory_account_id: Optional[int] = None
    writedown_expense_account_id: Optional[int] = None


@router.post(
    "/nrv/run",
    dependencies=[Depends(require_permission("finance.accounting_post"))],
)
def nrv_run(body: NRVRunRequest, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        return nrv_service.run_nrv_test(
            db,
            company_id=current_user.company_id,
            as_of_date=body.as_of_date,
            selling_cost_rate=body.selling_cost_rate,
            post_journal=body.post_journal,
            inventory_account_id=body.inventory_account_id,
            writedown_expense_account_id=body.writedown_expense_account_id,
            user_id=current_user.id,
            username=getattr(current_user, "username", None),
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except Exception:
        db.rollback()
        logger.exception("NRV run failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error")
    finally:
        _close(db)


@router.get(
    "/nrv/tests",
    dependencies=[Depends(require_permission("finance.accounting_view"))],
)
def nrv_list(current_user=Depends(get_current_user), limit: int = 100):
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(text("""
            SELECT id, as_of_date, product_id, warehouse_id,
                   cost_value, nrv_value, writedown_amount, journal_entry_id
            FROM inventory_nrv_tests ORDER BY as_of_date DESC, id DESC LIMIT :lim
        """), {"lim": limit}).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        _close(db)


# ═══════════════════════════════════════════════════════════════════════════
# IAS 36 — Impairment
# ═══════════════════════════════════════════════════════════════════════════

class CGUCreateRequest(BaseModel):
    code: str
    name: str


class ImpairmentTestRequest(BaseModel):
    cgu_id: int
    carrying_amount: Decimal
    value_in_use: Optional[Decimal] = None
    fair_value_less_costs: Optional[Decimal] = None
    as_of_date: Optional[date] = None
    post_journal: bool = False
    impairment_expense_account_id: Optional[int] = None
    accumulated_impairment_account_id: Optional[int] = None
    details: Optional[dict] = None


@router.post(
    "/cgu",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("finance.accounting_post"))],
)
def cgu_create(body: CGUCreateRequest, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        row = db.execute(text("""
            INSERT INTO cash_generating_units (code, name)
            VALUES (:c, :n)
            ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name
            RETURNING id, code, name, is_active
        """), {"c": body.code, "n": body.name}).fetchone()
        db.commit()
        return dict(row._mapping)
    finally:
        _close(db)


@router.get(
    "/cgu",
    dependencies=[Depends(require_permission("finance.accounting_view"))],
)
def cgu_list(current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(text(
            "SELECT id, code, name, is_active FROM cash_generating_units ORDER BY code"
        )).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        _close(db)


@router.post(
    "/impairment/test",
    dependencies=[Depends(require_permission("finance.accounting_post"))],
)
def impairment_test(body: ImpairmentTestRequest,
                    current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        return impairment_service.record_impairment_test(
            db,
            cgu_id=body.cgu_id,
            carrying_amount=body.carrying_amount,
            company_id=current_user.company_id,
            value_in_use=body.value_in_use,
            fair_value_less_costs=body.fair_value_less_costs,
            as_of_date=body.as_of_date,
            post_journal=body.post_journal,
            impairment_expense_account_id=body.impairment_expense_account_id,
            accumulated_impairment_account_id=body.accumulated_impairment_account_id,
            user_id=current_user.id,
            username=getattr(current_user, "username", None),
            details=body.details,
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except Exception:
        db.rollback()
        logger.exception("Impairment test failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error")
    finally:
        _close(db)


# ═══════════════════════════════════════════════════════════════════════════
# IFRS 15 — Revenue contracts & recognition
# ═══════════════════════════════════════════════════════════════════════════

class POPayload(BaseModel):
    description: str
    standalone_selling_price: Decimal
    recognition_method: str = "point_in_time"  # | over_time


class ContractCreateRequest(BaseModel):
    contract_number: str
    customer_id: Optional[int] = None
    total_transaction_price: Decimal
    currency: str = "SAR"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    obligations: list[POPayload] = []


class RevenueRecogniseRequest(BaseModel):
    po_id: int
    as_of_date: Optional[date] = None
    new_satisfied_pct: Optional[Decimal] = None
    post_journal: bool = False
    debit_account_id: Optional[int] = None
    credit_account_id: Optional[int] = None


@router.post(
    "/ifrs15/contracts",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("finance.accounting_post"))],
)
def ifrs15_create_contract(body: ContractCreateRequest,
                           current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        contract_id = ifrs15_revenue_service.create_contract(
            db,
            contract_number=body.contract_number,
            customer_id=body.customer_id,
            total_transaction_price=body.total_transaction_price,
            currency=body.currency,
            start_date=body.start_date,
            end_date=body.end_date,
            obligations=[ob.model_dump() for ob in body.obligations],
        )
        return {"contract_id": contract_id}
    except ValueError as e:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except Exception:
        db.rollback()
        logger.exception("IFRS15 contract create failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error")
    finally:
        _close(db)


@router.get(
    "/ifrs15/contracts/{contract_id}",
    dependencies=[Depends(require_permission("finance.accounting_view"))],
)
def ifrs15_get_contract(contract_id: int, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        c = db.execute(text(
            "SELECT * FROM revenue_contracts WHERE id = :id"
        ), {"id": contract_id}).fetchone()
        if not c:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "contract not found")
        pos = db.execute(text("""
            SELECT * FROM performance_obligations WHERE contract_id = :id ORDER BY id
        """), {"id": contract_id}).fetchall()
        return {
            "contract": dict(c._mapping),
            "performance_obligations": [dict(p._mapping) for p in pos],
        }
    finally:
        _close(db)


@router.post(
    "/ifrs15/recognise",
    dependencies=[Depends(require_permission("finance.accounting_post"))],
)
def ifrs15_recognise(body: RevenueRecogniseRequest,
                     current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        return ifrs15_revenue_service.recognise_revenue(
            db,
            po_id=body.po_id,
            company_id=current_user.company_id,
            as_of_date=body.as_of_date,
            new_satisfied_pct=body.new_satisfied_pct,
            post_journal=body.post_journal,
            debit_account_id=body.debit_account_id,
            credit_account_id=body.credit_account_id,
            user_id=current_user.id,
            username=getattr(current_user, "username", None),
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except Exception:
        db.rollback()
        logger.exception("IFRS15 recognise failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error")
    finally:
        _close(db)


# ═══════════════════════════════════════════════════════════════════════════
# E-Invoicing submissions
# ═══════════════════════════════════════════════════════════════════════════

class EInvoiceSubmitRequest(BaseModel):
    jurisdiction: str   # EG | AE | SA
    invoice_type: str   # sales | credit_note
    invoice_id: int
    invoice_payload: dict = {}


@router.post(
    "/einvoice/submit",
    dependencies=[Depends(require_permission("finance.accounting_post"))],
)
def einvoice_submit(body: EInvoiceSubmitRequest,
                    current_user=Depends(get_current_user)):
    try:
        adapter = get_adapter(body.jurisdiction)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))

    db = get_db_connection(current_user.company_id)
    try:
        payload = {"id": body.invoice_id, **(body.invoice_payload or {})}
        result = adapter.submit(payload)
        row = db.execute(text("""
            INSERT INTO e_invoice_submissions (jurisdiction, invoice_type, invoice_id,
                document_uuid, submission_status, submitted_at, response_payload, error_message)
            VALUES (:j, :t, :iid, :u, :s, CURRENT_TIMESTAMP, CAST(:r AS JSONB), :err)
            RETURNING id
        """), {
            "j": body.jurisdiction.upper(),
            "t": body.invoice_type,
            "iid": body.invoice_id,
            "u": result.document_uuid,
            "s": result.status,
            "r": json.dumps(result.response or {}, default=str, ensure_ascii=False),
            "err": result.error_message,
        }).fetchone()
        db.commit()
        return {
            "submission_id": row.id,
            "status": result.status,
            "document_uuid": result.document_uuid,
            "error_message": result.error_message,
        }
    except Exception:
        db.rollback()
        logger.exception("einvoice submit failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error")
    finally:
        _close(db)


@router.get(
    "/einvoice/submissions",
    dependencies=[Depends(require_permission("finance.accounting_view"))],
)
def einvoice_list(current_user=Depends(get_current_user), limit: int = 50,
                  jurisdiction: Optional[str] = None):
    db = get_db_connection(current_user.company_id)
    try:
        if jurisdiction:
            rows = db.execute(text("""
                SELECT id, jurisdiction, invoice_type, invoice_id, document_uuid,
                       submission_status, submitted_at, error_message
                FROM e_invoice_submissions
                WHERE jurisdiction = :j
                ORDER BY id DESC LIMIT :lim
            """), {"j": jurisdiction.upper(), "lim": limit}).fetchall()
        else:
            rows = db.execute(text("""
                SELECT id, jurisdiction, invoice_type, invoice_id, document_uuid,
                       submission_status, submitted_at, error_message
                FROM e_invoice_submissions
                ORDER BY id DESC LIMIT :lim
            """), {"lim": limit}).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        _close(db)


@router.post(
    "/einvoice/{submission_id}/refresh",
    dependencies=[Depends(require_permission("finance.accounting_post"))],
)
def einvoice_refresh(submission_id: int, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        sub = db.execute(text("""
            SELECT id, jurisdiction, document_uuid
            FROM e_invoice_submissions WHERE id = :id
        """), {"id": submission_id}).fetchone()
        if not sub:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "submission not found")
        if not sub.document_uuid:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "submission has no document_uuid")
        adapter = get_adapter(sub.jurisdiction)
        result = adapter.fetch_status(sub.document_uuid)
        db.execute(text("""
            UPDATE e_invoice_submissions
               SET submission_status = :s,
                   response_payload = CAST(:r AS JSONB),
                   error_message = :err
             WHERE id = :id
        """), {
            "s": result.status,
            "r": json.dumps(result.response or {}, default=str, ensure_ascii=False),
            "err": result.error_message,
            "id": submission_id,
        })
        db.commit()
        return {"submission_id": submission_id, "status": result.status,
                "error_message": result.error_message}
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("einvoice refresh failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error")
    finally:
        _close(db)
