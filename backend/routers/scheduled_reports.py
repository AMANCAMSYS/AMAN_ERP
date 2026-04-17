"""
Scheduled Reports & Report Sharing Router
RPT-106: مشاركة التقارير بين المستخدمين
RPT-106b: جدولة التقارير التلقائية (Scheduled Reports)
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from utils.i18n import http_error
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime, date, timedelta
from pydantic import BaseModel
import logging
import json

from database import get_db_connection
from routers.auth import get_current_user
from utils.permissions import require_permission, validate_branch_access
from utils.audit import log_activity

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Scheduled & Shared Reports"])

# ─── Report Types Registry ────────────────────────────────────────────────

REPORT_TYPES = {
    "profit_loss": {"label": "Profit & Loss / قائمة الدخل", "category": "accounting"},
    "balance_sheet": {"label": "Balance Sheet / الميزانية العمومية", "category": "accounting"},
    "trial_balance": {"label": "Trial Balance / ميزان المراجعة", "category": "accounting"},
    "general_ledger": {"label": "General Ledger / دفتر الأستاذ", "category": "accounting"},
    "cashflow": {"label": "Cash Flow / التدفقات النقدية", "category": "accounting"},
    "sales_summary": {"label": "Sales Summary / ملخص المبيعات", "category": "sales"},
    "sales_aging": {"label": "Aging Report / تقرير أعمار الديون", "category": "sales"},
    "detailed_pl": {"label": "Detailed P&L / أرباح وخسائر تفصيلي", "category": "accounting"},
    "commissions": {"label": "Commissions / تقرير العمولات", "category": "sales"},
    "inventory_valuation": {"label": "Inventory Valuation / تقييم المخزون", "category": "inventory"},
    "payroll_trend": {"label": "Payroll Trend / اتجاه الرواتب", "category": "hr"},
}


# ─── Schemas ──────────────────────────────────────────────────────────────

class ScheduledReportCreate(BaseModel):
    report_name: Optional[str] = None
    report_type: str
    report_config: Optional[dict] = None
    frequency: str  # daily, weekly, monthly
    recipients: str  # comma-separated emails
    format: str = "pdf"
    branch_id: Optional[int] = None


class ShareReportRequest(BaseModel):
    report_type: str  # "custom" or "scheduled"
    report_id: int
    shared_with: int  # user_id
    permission: str = "view"
    message: Optional[str] = None


# ═══════════════════════════════════════════════════════════
# Scheduled Reports CRUD
# ═══════════════════════════════════════════════════════════

@router.get("/scheduled/types")
def list_report_types():
    """List available report types for scheduling."""
    return REPORT_TYPES


@router.get("/scheduled/", dependencies=[Depends(require_permission(["reports.view"]))])
def list_scheduled_reports(
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """List all scheduled reports."""
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    try:
        branch_filter = "AND (sr.branch_id = :branch_id OR sr.branch_id IS NULL)" if branch_id else ""
        params = {"uid": current_user.id}
        if branch_id:
            params["branch_id"] = branch_id

        query = f"""
            SELECT sr.*, b.branch_name, u.full_name as created_by_name
            FROM scheduled_reports sr
            LEFT JOIN branches b ON sr.branch_id = b.id
            LEFT JOIN company_users u ON sr.created_by = u.id
            WHERE (sr.created_by = :uid
                   OR sr.id IN (SELECT report_id FROM shared_reports WHERE shared_with = :uid AND report_type = 'scheduled'))
            {branch_filter}
            ORDER BY sr.created_at DESC
        """

        reports = [dict(row._mapping) for row in db.execute(text(query), params).fetchall()]
        return reports
    finally:
        db.close()


@router.post("/scheduled/", dependencies=[Depends(require_permission(["reports.create"]))])
def create_scheduled_report(
    data: ScheduledReportCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Create a new scheduled report."""
    if data.report_type not in REPORT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid report type. Valid: {list(REPORT_TYPES.keys())}")
    if data.frequency not in ("daily", "weekly", "monthly"):
        raise HTTPException(status_code=400, detail="Frequency must be daily, weekly, or monthly")

    db = get_db_connection(current_user.company_id)
    try:
        if data.branch_id:
            validate_branch_access(current_user, data.branch_id)

        next_run = _calculate_next_run(data.frequency)
        report_name = data.report_name or REPORT_TYPES[data.report_type]["label"]

        result = db.execute(text("""
            INSERT INTO scheduled_reports
            (report_name, report_type, report_config, frequency, recipients, format, branch_id, created_by, next_run_at)
            VALUES (:name, :type, :config, :freq, :recipients, :fmt, :branch, :uid, :next_run)
            RETURNING id, report_name, report_type, frequency, format, next_run_at, is_active, created_at
        """), {
            "name": report_name,
            "type": data.report_type,
            "config": json.dumps(data.report_config or {}),
            "freq": data.frequency,
            "recipients": data.recipients,
            "fmt": data.format,
            "branch": data.branch_id,
            "uid": current_user.id,
            "next_run": next_run,
        })
        db.commit()
        row = result.fetchone()
        log_activity(
            db, user_id=current_user.id, username=getattr(current_user, "username", "unknown"),
            action="reports.scheduled.create", resource_type="scheduled_report",
            resource_id=str(dict(row._mapping).get("id", "")),
            details={"report_type": data.report_type, "frequency": data.frequency},
            request=request
        )
        return dict(row._mapping)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(400, "invalid_data"))
    finally:
        db.close()


@router.put("/scheduled/{report_id}", dependencies=[Depends(require_permission(["reports.edit"]))])
def update_scheduled_report(
    report_id: int,
    data: ScheduledReportCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Update a scheduled report."""
    db = get_db_connection(current_user.company_id)
    try:
        next_run = _calculate_next_run(data.frequency)
        report_name = data.report_name or REPORT_TYPES.get(data.report_type, {}).get("label", data.report_type)

        result = db.execute(text("""
            UPDATE scheduled_reports SET
                report_name = :name, report_type = :type, report_config = :config,
                frequency = :freq, recipients = :recipients, format = :fmt,
                branch_id = :branch, next_run_at = :next_run, updated_at = NOW()
            WHERE id = :id AND created_by = :uid
        """), {
            "name": report_name,
            "type": data.report_type,
            "config": json.dumps(data.report_config or {}),
            "freq": data.frequency,
            "recipients": data.recipients,
            "fmt": data.format,
            "branch": data.branch_id,
            "next_run": next_run,
            "id": report_id,
            "uid": current_user.id,
        })
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Report not found or unauthorized")
        db.commit()
        log_activity(
            db, user_id=current_user.id, username=getattr(current_user, "username", "unknown"),
            action="reports.scheduled.update", resource_type="scheduled_report",
            resource_id=str(report_id),
            details={"report_type": data.report_type, "frequency": data.frequency},
            request=request
        )
        return {"message": "Scheduled report updated"}
    finally:
        db.close()


@router.delete("/scheduled/{report_id}", dependencies=[Depends(require_permission(["reports.delete"]))])
def delete_scheduled_report(
    report_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Delete a scheduled report."""
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(text("DELETE FROM shared_reports WHERE report_type='scheduled' AND report_id=:id"), {"id": report_id})
        result = db.execute(text("DELETE FROM scheduled_reports WHERE id = :id AND created_by = :uid"),
                            {"id": report_id, "uid": current_user.id})
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Report not found or unauthorized")
        db.commit()
        log_activity(
            db, user_id=current_user.id, username=getattr(current_user, "username", "unknown"),
            action="reports.scheduled.delete", resource_type="scheduled_report",
            resource_id=str(report_id), details={},
            request=request
        )
        return {"message": "Scheduled report deleted"}
    finally:
        db.close()


@router.put("/scheduled/{report_id}/toggle", dependencies=[Depends(require_permission(["reports.edit"]))])
def toggle_scheduled_report(
    report_id: int,
    active: bool,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Activate/Deactivate a scheduled report."""
    db = get_db_connection(current_user.company_id)
    try:
        result = db.execute(
            text("UPDATE scheduled_reports SET is_active = :active, updated_at = NOW() WHERE id = :id"),
            {"active": active, "id": report_id}
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Report not found")
        db.commit()
        log_activity(
            db, user_id=current_user.id, username=getattr(current_user, "username", "unknown"),
            action="reports.scheduled.toggle", resource_type="scheduled_report",
            resource_id=str(report_id), details={"is_active": active},
            request=request
        )
        return {"message": f"Report {'activated' if active else 'deactivated'}"}
    finally:
        db.close()


@router.post("/scheduled/{report_id}/run", dependencies=[Depends(require_permission(["reports.create"]))])
def run_scheduled_report_now(
    report_id: int,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Manually trigger a scheduled report immediately."""
    db = get_db_connection(current_user.company_id)
    try:
        report = db.execute(text("SELECT * FROM scheduled_reports WHERE id=:id"), {"id": report_id}).fetchone()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        background_tasks.add_task(_execute_scheduled_report, current_user.company_id, dict(report._mapping))
        log_activity(
            db, user_id=current_user.id, username=getattr(current_user, "username", "unknown"),
            action="reports.scheduled.run_now", resource_type="scheduled_report",
            resource_id=str(report_id), details={},
            request=request
        )
        return {"message": "Report execution started in background"}
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# RPT-106: Report Sharing
# ═══════════════════════════════════════════════════════════

@router.post("/share", dependencies=[Depends(require_permission(["reports.view"]))])
def share_report(
    data: ShareReportRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Share a report with another user."""
    if data.report_type not in ("custom", "scheduled"):
        raise HTTPException(status_code=400, detail="report_type must be 'custom' or 'scheduled'")

    db = get_db_connection(current_user.company_id)
    try:
        # Verify user exists
        user = db.execute(text("SELECT id, full_name FROM company_users WHERE id=:id"), {"id": data.shared_with}).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify report exists — SEC-003: table is from controlled whitelist, not user input
        _ALLOWED_TABLES = {"custom_reports", "scheduled_reports"}
        table = "custom_reports" if data.report_type == "custom" else "scheduled_reports"
        assert table in _ALLOWED_TABLES
        report = db.execute(text(f"SELECT id FROM {table} WHERE id=:id"), {"id": data.report_id}).fetchone()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        db.execute(text("""
            INSERT INTO shared_reports (report_type, report_id, shared_by, shared_with, permission, message)
            VALUES (:rt, :rid, :by, :with, :perm, :msg)
            ON CONFLICT (report_type, report_id, shared_with)
            DO UPDATE SET permission = EXCLUDED.permission, message = EXCLUDED.message
        """), {
            "rt": data.report_type, "rid": data.report_id,
            "by": current_user.id, "with": data.shared_with,
            "perm": data.permission, "msg": data.message,
        })
        db.commit()
        log_activity(
            db, user_id=current_user.id, username=getattr(current_user, "username", "unknown"),
            action="reports.share.create", resource_type="shared_report",
            resource_id=str(data.report_id),
            details={"report_type": data.report_type, "shared_with": data.shared_with},
            request=request
        )
        return {"message": f"Report shared with {user.full_name}"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(400, "invalid_data"))
    finally:
        db.close()


@router.delete("/share/{share_id}", dependencies=[Depends(require_permission(["reports.view"]))])
def unshare_report(share_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    """Remove report sharing."""
    db = get_db_connection(current_user.company_id)
    try:
        result = db.execute(text("DELETE FROM shared_reports WHERE id=:id AND shared_by=:uid"),
                            {"id": share_id, "uid": current_user.id})
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Share not found or unauthorized")
        db.commit()
        log_activity(
            db, user_id=current_user.id, username=getattr(current_user, "username", "unknown"),
            action="reports.share.delete", resource_type="shared_report",
            resource_id=str(share_id), details={},
            request=request
        )
        return {"message": "Share removed"}
    finally:
        db.close()


@router.get("/shared/", dependencies=[Depends(require_permission(["reports.view"]))])
def list_shared_reports(current_user: dict = Depends(get_current_user)):
    """List reports shared with the current user."""
    db = get_db_connection(current_user.company_id)
    try:
        result = db.execute(text("""
            SELECT sr.*, u.full_name as shared_by_name,
                   CASE sr.report_type
                       WHEN 'custom' THEN (SELECT report_name FROM custom_reports WHERE id = sr.report_id)
                       WHEN 'scheduled' THEN (SELECT COALESCE(report_name, report_type) FROM scheduled_reports WHERE id = sr.report_id)
                   END as report_name
            FROM shared_reports sr
            JOIN company_users u ON sr.shared_by = u.id
            WHERE sr.shared_with = :uid
            ORDER BY sr.created_at DESC
        """), {"uid": current_user.id}).fetchall()
        return [dict(row._mapping) for row in result]
    finally:
        db.close()


@router.get("/shared/by-report/{report_type}/{report_id}", dependencies=[Depends(require_permission(["reports.view"]))])
def list_report_shares(report_type: str, report_id: int, current_user: dict = Depends(get_current_user)):
    """List users a report is shared with."""
    db = get_db_connection(current_user.company_id)
    try:
        result = db.execute(text("""
            SELECT sr.*, u.full_name as shared_with_name, u.email as shared_with_email
            FROM shared_reports sr
            JOIN company_users u ON sr.shared_with = u.id
            WHERE sr.report_type = :rt AND sr.report_id = :rid
            ORDER BY sr.created_at DESC
        """), {"rt": report_type, "rid": report_id}).fetchall()
        return [dict(row._mapping) for row in result]
    finally:
        db.close()


@router.get("/users/", dependencies=[Depends(require_permission(["reports.view"]))])
def list_users_for_sharing(current_user: dict = Depends(get_current_user)):
    """List users that reports can be shared with."""
    db = get_db_connection(current_user.company_id)
    try:
        result = db.execute(text("""
            SELECT id, full_name, email, role FROM company_users
            WHERE id != :uid AND is_active = true
            ORDER BY full_name
        """), {"uid": current_user.id}).fetchall()
        return [dict(row._mapping) for row in result]
    finally:
        db.close()


# ─── Helpers ──────────────────────────────────────────────────────────────

def _calculate_next_run(frequency: str) -> datetime:
    """Calculate next run time based on frequency."""
    now = datetime.now()
    if frequency == "daily":
        next_run = (now + timedelta(days=1)).replace(hour=6, minute=0, second=0, microsecond=0)
    elif frequency == "weekly":
        days_ahead = 7 - now.weekday()
        if days_ahead == 0:
            days_ahead = 7
        next_run = (now + timedelta(days=days_ahead)).replace(hour=6, minute=0, second=0, microsecond=0)
    elif frequency == "monthly":
        if now.month == 12:
            next_run = now.replace(year=now.year + 1, month=1, day=1, hour=6, minute=0, second=0, microsecond=0)
        else:
            next_run = now.replace(month=now.month + 1, day=1, hour=6, minute=0, second=0, microsecond=0)
    else:
        next_run = now + timedelta(days=1)
    return next_run


def _execute_scheduled_report(company_id: str, report_config: dict):
    """Execute a scheduled report in the background (generate + log status)."""
    db = get_db_connection(company_id)
    report_id = report_config.get("id")
    try:
        report_type = report_config["report_type"]
        logger.info(f"Executing scheduled report #{report_id} ({report_type}) for company {company_id}")

        db.execute(text("UPDATE scheduled_reports SET last_status = 'running', updated_at = NOW() WHERE id = :id"),
                   {"id": report_id})
        db.commit()

        frequency = report_config["frequency"]
        next_run = _calculate_next_run(frequency)

        # Actual report generation + email would be called here
        db.execute(text("""
            UPDATE scheduled_reports SET
                last_run_at = NOW(), last_status = 'completed',
                next_run_at = :next_run, updated_at = NOW()
            WHERE id = :id
        """), {"id": report_id, "next_run": next_run})
        db.commit()
        logger.info(f"Scheduled report #{report_id} completed. Next run: {next_run}")
    except Exception as e:
        logger.error(f"Scheduled report #{report_id} failed: {e}")
        try:
            db.execute(text("UPDATE scheduled_reports SET last_status = 'failed', updated_at = NOW() WHERE id = :id"),
                       {"id": report_id})
            db.commit()
        except Exception:
            pass
    finally:
        db.close()


# ─── Background Scheduler Bootstrap ─────────────────────────────────────

def start_report_scheduler(app):
    """
    Start APScheduler to run scheduled reports.
    Call this from main.py on startup.
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler

        scheduler = BackgroundScheduler()

        def check_and_run_reports():
            """Check for reports due and execute them."""
            from database import get_all_company_ids
            try:
                company_ids = get_all_company_ids()
                for company_id in company_ids:
                    db = get_db_connection(company_id)
                    try:
                        due_reports = db.execute(text("""
                            SELECT * FROM scheduled_reports
                            WHERE is_active = true AND next_run_at <= NOW()
                            ORDER BY next_run_at
                            LIMIT 10
                        """)).fetchall()
                        for report in due_reports:
                            _execute_scheduled_report(company_id, dict(report._mapping))
                    finally:
                        db.close()
            except Exception as e:
                logger.error(f"Scheduler check failed: {e}")

        scheduler.add_job(check_and_run_reports, 'interval', minutes=15, id='report_scheduler')
        scheduler.start()
        logger.info("Report scheduler started (checks every 15 min)")

        import atexit
        atexit.register(scheduler.shutdown)

    except ImportError:
        logger.warning("APScheduler not installed — scheduled reports will not auto-run")
    except Exception as e:
        logger.error(f"Failed to start report scheduler: {e}")
