"""
AMAN ERP – Subscription Billing
إدارة الاشتراكات والفوترة المتكررة
"""

import logging
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from utils.i18n import http_error
from sqlalchemy import text

from database import get_db_connection
from routers.auth import get_current_user
from utils.fiscal_lock import check_fiscal_period_open
from schemas.subscription import (
    CancelRequest,
    EnrollmentCreate,
    EnrollmentDetailRead,
    EnrollmentListResponse,
    EnrollmentRead,
    PlanChangeRequest,
    PlanCreate,
    PlanListResponse,
    PlanRead,
    PlanUpdate,
    SubscriptionInvoiceRead,
)
from services.subscription_service import (
    cancel_enrollment,
    enroll_customer,
    pause_enrollment,
    prorate_plan_change,
    resume_enrollment,
)
from utils.permissions import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/finance/subscriptions", tags=["إدارة الاشتراكات"])


# ── Plans ──

@router.get(
    "/plans",
    response_model=PlanListResponse,
    dependencies=[Depends(require_permission("finance.subscription_view"))],
)
def list_plans(
    skip: int = 0,
    limit: int = 50,
    is_active: Optional[bool] = Query(None),
    current_user=Depends(get_current_user),
):
    db = get_db_connection(current_user.company_id)
    try:
        where = "is_deleted = false"
        params: dict = {"lim": limit, "off": skip}
        if is_active is not None:
            where += " AND is_active = :active"
            params["active"] = is_active
        total = db.execute(
            text(f"SELECT COUNT(*) FROM subscription_plans WHERE {where}"), params
        ).scalar()
        rows = db.execute(
            text(
                f"SELECT * FROM subscription_plans WHERE {where} "
                "ORDER BY created_at DESC LIMIT :lim OFFSET :off"
            ),
            params,
        ).fetchall()
        return PlanListResponse(
            items=[PlanRead.model_validate(r) for r in rows],
            total=total,
        )
    finally:
        db.close()


@router.post(
    "/plans",
    response_model=PlanRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("finance.subscription_manage"))],
)
def create_plan(body: PlanCreate, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        row = db.execute(
            text(
                "INSERT INTO subscription_plans "
                "(name, description, billing_frequency, base_amount, currency, "
                " trial_period_days, auto_renewal, created_by, updated_by) "
                "VALUES (:name, :desc, :freq, :amt, :cur, :trial, :auto, :usr, :usr) "
                "RETURNING *"
            ),
            {
                "name": body.name,
                "desc": body.description,
                "freq": body.billing_frequency,
                "amt": str(body.base_amount),
                "cur": body.currency,
                "trial": body.trial_period_days,
                "auto": body.auto_renewal,
                "usr": str(current_user.id),
            },
        ).fetchone()
        db.commit()
        return PlanRead.model_validate(row)
    except Exception:
        db.rollback()
        logger.exception("Failed to create subscription plan")
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@router.put(
    "/plans/{plan_id}",
    response_model=PlanRead,
    dependencies=[Depends(require_permission("finance.subscription_manage"))],
)
def update_plan(plan_id: int, body: PlanUpdate, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        # Build dynamic SET clause from provided fields
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(**http_error(400, "no_data_to_update"))

        set_clauses = []
        params: dict = {"pid": plan_id}
        for key, value in updates.items():
            set_clauses.append(f"{key} = :{key}")
            params[key] = str(value) if key == "base_amount" and value is not None else value
        set_clauses.append("updated_at = NOW()")
        set_clauses.append("updated_by = :usr")
        params["usr"] = str(current_user.id)

        row = db.execute(
            text(
                f"UPDATE subscription_plans SET {', '.join(set_clauses)} "
                "WHERE id = :pid AND is_deleted = false RETURNING *"
            ),
            params,
        ).fetchone()
        if not row:
            raise HTTPException(**http_error(404, "plan_not_found"))
        db.commit()
        return PlanRead.model_validate(row)
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("Failed to update subscription plan")
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


# ── Enrollments ──

@router.post(
    "/enroll",
    response_model=EnrollmentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("finance.subscription_manage"))],
)
def enroll(body: EnrollmentCreate, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        # Check fiscal period is open for the enrollment start date
        start_date = body.enrollment_date or __import__('datetime').date.today()
        check_fiscal_period_open(db, start_date)

        result = enroll_customer(
            db,
            customer_id=body.customer_id,
            plan_id=body.plan_id,
            enrollment_date=body.enrollment_date,
            user=str(current_user.id),
        )
        enrollment_id = result["enrollment_id"]

        # Submit for approval workflow
        try:
            from utils.approval_utils import try_submit_for_approval
            plan_row = db.execute(
                text("SELECT base_amount FROM subscription_plans WHERE id = :pid"),
                {"pid": body.plan_id},
            ).fetchone()
            plan_amount = plan_row.base_amount if plan_row else 0
            try_submit_for_approval(
                db,
                document_type="subscription",
                document_id=enrollment_id,
                document_number=f"SUB-{enrollment_id}",
                amount=Decimal(str(plan_amount)),
                submitted_by=current_user.id,
                description=f"اشتراك جديد - خطة {body.plan_id} للعميل {body.customer_id}",
                link=f"/subscriptions/enrollments/{enrollment_id}",
            )
            db.commit()
        except Exception:
            pass  # Non-blocking

        row = db.execute(
            text("SELECT * FROM subscription_enrollments WHERE id = :eid"),
            {"eid": enrollment_id},
        ).fetchone()
        return EnrollmentRead.model_validate(row)
    except ValueError:
        logger.exception("Internal error")
        raise HTTPException(**http_error(400, "invalid_data"))
    except Exception:
        db.rollback()
        logger.exception("Failed to enroll customer")
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@router.get(
    "/enrollments",
    response_model=EnrollmentListResponse,
    dependencies=[Depends(require_permission("finance.subscription_view"))],
)
def list_enrollments(
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = Query(None, alias="status"),
    customer_id: Optional[int] = Query(None),
    current_user=Depends(get_current_user),
):
    db = get_db_connection(current_user.company_id)
    try:
        where = "e.is_deleted = false"
        params: dict = {"lim": limit, "off": skip}
        if status_filter:
            where += " AND e.status = :st"
            params["st"] = status_filter
        if customer_id:
            where += " AND e.customer_id = :cid"
            params["cid"] = customer_id

        total = db.execute(
            text(f"SELECT COUNT(*) FROM subscription_enrollments e WHERE {where}"), params
        ).scalar()
        rows = db.execute(
            text(
                f"SELECT e.* FROM subscription_enrollments e WHERE {where} "
                "ORDER BY e.created_at DESC LIMIT :lim OFFSET :off"
            ),
            params,
        ).fetchall()
        return EnrollmentListResponse(
            items=[EnrollmentRead.model_validate(r) for r in rows],
            total=total,
        )
    finally:
        db.close()


@router.get(
    "/enrollments/{enrollment_id}",
    response_model=EnrollmentDetailRead,
    dependencies=[Depends(require_permission("finance.subscription_view"))],
)
def get_enrollment(enrollment_id: int, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        row = db.execute(
            text(
                "SELECT e.*, p.name AS plan_name, pa.name AS customer_name "
                "FROM subscription_enrollments e "
                "JOIN subscription_plans p ON p.id = e.plan_id "
                "LEFT JOIN parties pa ON pa.id = e.customer_id "
                "WHERE e.id = :eid AND e.is_deleted = false"
            ),
            {"eid": enrollment_id},
        ).fetchone()
        if not row:
            raise HTTPException(**http_error(404, "enrollment_not_found"))

        invoices = db.execute(
            text(
                "SELECT * FROM subscription_invoices "
                "WHERE enrollment_id = :eid AND is_deleted = false "
                "ORDER BY billing_period_start DESC"
            ),
            {"eid": enrollment_id},
        ).fetchall()

        detail = EnrollmentDetailRead.model_validate(row)
        detail.invoices = [SubscriptionInvoiceRead.model_validate(i) for i in invoices]
        return detail
    finally:
        db.close()


@router.post(
    "/enrollments/{enrollment_id}/pause",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("finance.subscription_manage"))],
)
def pause(enrollment_id: int, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        pause_enrollment(db, enrollment_id=enrollment_id, user=str(current_user.id))
    except ValueError:
        logger.exception("Internal error")
        raise HTTPException(**http_error(400, "invalid_data"))
    except Exception:
        db.rollback()
        logger.exception("Failed to pause enrollment")
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@router.post(
    "/enrollments/{enrollment_id}/resume",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("finance.subscription_manage"))],
)
def resume(enrollment_id: int, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        resume_enrollment(db, enrollment_id=enrollment_id, user=str(current_user.id))
    except ValueError:
        logger.exception("Internal error")
        raise HTTPException(**http_error(400, "invalid_data"))
    except Exception:
        db.rollback()
        logger.exception("Failed to resume enrollment")
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@router.post(
    "/enrollments/{enrollment_id}/cancel",
    response_model=EnrollmentRead,
    dependencies=[Depends(require_permission("finance.subscription_manage"))],
)
def cancel(enrollment_id: int, body: CancelRequest, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        cancel_enrollment(
            db,
            enrollment_id=enrollment_id,
            reason=body.reason,
            user=str(current_user.id),
        )
        row = db.execute(
            text("SELECT * FROM subscription_enrollments WHERE id = :eid"),
            {"eid": enrollment_id},
        ).fetchone()
        return EnrollmentRead.model_validate(row)
    except ValueError:
        logger.exception("Internal error")
        raise HTTPException(**http_error(400, "invalid_data"))
    except Exception:
        db.rollback()
        logger.exception("Failed to cancel enrollment")
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@router.post(
    "/enrollments/{enrollment_id}/change-plan",
    dependencies=[Depends(require_permission("finance.subscription_manage"))],
)
def change_plan(enrollment_id: int, body: PlanChangeRequest, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        # Check fiscal period is open for today (plan change date)
        from datetime import date as _date
        check_fiscal_period_open(db, _date.today())

        result = prorate_plan_change(
            db,
            enrollment_id=enrollment_id,
            new_plan_id=body.new_plan_id,
            user=str(current_user.id),
        )
        return {"success": True, "data": result}
    except ValueError:
        logger.exception("Internal error")
        raise HTTPException(**http_error(400, "invalid_data"))
    except Exception:
        db.rollback()
        logger.exception("Failed to change plan")
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
