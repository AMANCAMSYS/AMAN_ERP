from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime, date

from database import get_db_connection, get_db
from routers.auth import get_current_user
from utils.permissions import require_permission, validate_branch_access

router = APIRouter(prefix="/reports/scheduled", tags=["Scheduled Reports"])

@router.get("/", dependencies=[Depends(require_permission(["reports.view"]))])
def list_scheduled_reports(
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """List all scheduled reports"""
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    try:
        branch_filter = "AND (branch_id = :branch_id OR branch_id IS NULL)" if branch_id else ""
        params = {"branch_id": branch_id} if branch_id else {}
        
        query = f"""
            SELECT sr.*, b.branch_name, u.full_name as created_by_name
            FROM scheduled_reports sr
            LEFT JOIN branches b ON sr.branch_id = b.id
            LEFT JOIN company_users u ON sr.created_by = u.id
            WHERE 1=1 {branch_filter}
            ORDER BY sr.created_at DESC
        """
        
        reports = [dict(row._mapping) for row in db.execute(text(query), params).fetchall()]
        return reports
    finally:
        db.close()

@router.post("/", dependencies=[Depends(require_permission(["reports.create"]))])
def create_scheduled_report(
    report_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Create a new scheduled report"""
    db = get_db_connection(current_user.company_id)
    try:
        # Validate data
        required = ["report_type", "frequency", "recipients"]
        for field in required:
            if field not in report_data:
                raise HTTPException(status_code=400, detail=f"Missing field: {field}")
        
        branch_id = report_data.get("branch_id")
        if branch_id:
             validate_branch_access(current_user, branch_id)
        
        # Insert
        query = """
            INSERT INTO scheduled_reports 
            (report_type, frequency, recipients, format, branch_id, created_by, next_run_at)
            VALUES 
            (:report_type, :frequency, :recipients, :format, :branch_id, :created_by, :next_run_at)
            RETURNING id
        """
        
        # Calculate next run
        from datetime import timedelta
        next_run = datetime.now() + timedelta(minutes=5) # First run in 5 mins for testing, or standard logic
        # Ideally calculate based on frequency. For now simple.
        
        params = {
            "report_type": report_data["report_type"],
            "frequency": report_data["frequency"],
            "recipients": report_data["recipients"],
            "format": report_data.get("format", "pdf"),
            "branch_id": branch_id,
            "created_by": current_user.id,
            "next_run_at": next_run
        }
        
        result = db.execute(text(query), params)
        new_id = result.fetchone()[0]
        db.commit()
        
        return {"id": new_id, "message": "Scheduled report created"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@router.delete("/{report_id}", dependencies=[Depends(require_permission(["reports.delete"]))])
def delete_scheduled_report(
    report_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete a scheduled report"""
    db = get_db_connection(current_user.company_id)
    try:
        result = db.execute(text("DELETE FROM scheduled_reports WHERE id = :id"), {"id": report_id})
        if result.rowcount == 0:
             raise HTTPException(status_code=404, detail="Report not found")
        db.commit()
        return {"message": "Scheduled report deleted"}
    finally:
        db.close()

@router.put("/{report_id}/toggle", dependencies=[Depends(require_permission(["reports.edit"]))])
def toggle_scheduled_report(
    report_id: int,
    active: bool,
    current_user: dict = Depends(get_current_user)
):
    """Activate/Deactivate a scheduled report"""
    db = get_db_connection(current_user.company_id)
    try:
        result = db.execute(
            text("UPDATE scheduled_reports SET is_active = :active WHERE id = :id"), 
            {"active": active, "id": report_id}
        )
        if result.rowcount == 0:
             raise HTTPException(status_code=404, detail="Report not found")
        db.commit()
        return {"message": f"Report {'activated' if active else 'deactivated'}"}
    finally:
        db.close()
