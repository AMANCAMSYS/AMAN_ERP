"""
AMAN ERP - Projects Module
وحدة إدارة المشاريع - مع ربط محاسبي كامل (مراكز تكلفة، مصاريف، إيرادات)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, File, UploadFile
import shutil
import os
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from database import get_db_connection
from routers.auth import get_current_user
from utils.permissions import require_permission, validate_branch_access, require_module
from utils.accounting import (
    generate_sequential_number, get_mapped_account_id,
    get_base_currency, update_account_balance
)
from utils.audit import log_activity
from sqlalchemy import text
from services.gl_service import create_journal_entry as gl_create_journal_entry
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["المشاريع"], dependencies=[Depends(require_module("projects"))])
from schemas.projects import (
    ProjectCreate, ProjectUpdate, TaskCreate, TaskUpdate,
    ProjectExpenseCreate, ProjectRevenueCreate,
    TimesheetCreate, TimesheetUpdate, TimesheetApprove,
    ProjectInvoiceCreate, ProjectDocumentCreate,
    ChangeOrderCreate, ChangeOrderUpdate, ProjectCloseRequest
)


# ═══════════════════════════════════════════════════════════
# Projects CRUD
# ═══════════════════════════════════════════════════════════

@router.get("/", dependencies=[Depends(require_permission("projects.view"))])
async def get_projects(
    status_filter: Optional[str] = None,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """جلب قائمة المشاريع مع ملخص مالي"""
    from utils.permissions import validate_branch_access
    validated_branch = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    try:
        params = {}
        filters = ["1=1"]

        if status_filter:
            filters.append("p.status = :status")
            params["status"] = status_filter

        if validated_branch:
            filters.append("p.branch_id = :branch_id")
            params["branch_id"] = validated_branch

        where = " AND ".join(filters)

        result = db.execute(text(f"""
            SELECT p.*,
                c.name as customer_name,
                CONCAT(e.first_name, ' ', e.last_name) as manager_name,
                COALESCE(exp.total_expenses, 0) as total_expenses,
                COALESCE(rev.total_revenues, 0) as total_revenues,
                COALESCE(tasks.total_tasks, 0) as total_tasks,
                COALESCE(tasks.completed_tasks, 0) as completed_tasks
            FROM projects p
            LEFT JOIN parties c ON p.customer_id = c.id
            LEFT JOIN employees e ON p.manager_id = e.id
            LEFT JOIN (
                SELECT project_id, SUM(amount) as total_expenses
                FROM project_expenses WHERE status != 'rejected'
                GROUP BY project_id
            ) exp ON exp.project_id = p.id
            LEFT JOIN (
                SELECT project_id, SUM(amount) as total_revenues
                FROM project_revenues WHERE status != 'rejected'
                GROUP BY project_id
            ) rev ON rev.project_id = p.id
            LEFT JOIN (
                SELECT project_id,
                       COUNT(*) as total_tasks,
                       COUNT(*) FILTER (WHERE status = 'completed') as completed_tasks
                FROM project_tasks
                GROUP BY project_id
            ) tasks ON tasks.project_id = p.id
            WHERE {where}
            ORDER BY p.created_at DESC
        """), params).fetchall()

        return [dict(r._mapping) for r in result]
    except Exception as e:
        logger.error(f"Error fetching projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/summary", dependencies=[Depends(require_permission("projects.view"))])
async def get_projects_summary(current_user: dict = Depends(get_current_user)):
    """ملخص إحصائي للمشاريع"""
    db = get_db_connection(current_user.company_id)
    try:
        stats = db.execute(text("""
            SELECT
                COUNT(*) as total_projects,
                COUNT(*) FILTER (WHERE status = 'planning') as planning,
                COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress,
                COUNT(*) FILTER (WHERE status = 'completed') as completed,
                COUNT(*) FILTER (WHERE status = 'on_hold') as on_hold,
                COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled,
                COALESCE(SUM(planned_budget), 0) as total_budget,
                COALESCE(SUM(actual_cost), 0) as total_actual_cost
            FROM projects
        """)).fetchone()

        return dict(stats._mapping)
    except Exception as e:
        logger.error(f"Error fetching project summary: {e}")
        return {
            "total_projects": 0, "planning": 0, "in_progress": 0,
            "completed": 0, "on_hold": 0, "cancelled": 0,
            "total_budget": 0, "total_actual_cost": 0
        }
    finally:
        db.close()


@router.get("/{project_id}", dependencies=[Depends(require_permission("projects.view"))])
async def get_project(project_id: int, current_user: dict = Depends(get_current_user)):
    """جلب تفاصيل مشروع مع المهام والمصاريف والإيرادات"""
    db = get_db_connection(current_user.company_id)
    try:
        project = db.execute(text("""
            SELECT p.*,
                c.name as customer_name, c.party_code as customer_code,
                CONCAT(e.first_name, ' ', e.last_name) as manager_name
            FROM projects p
            LEFT JOIN parties c ON p.customer_id = c.id
            LEFT JOIN employees e ON p.manager_id = e.id
            WHERE p.id = :id
        """), {"id": project_id}).fetchone()

        if not project:
            raise HTTPException(status_code=404, detail="المشروع غير موجود")

        project_data: Dict[str, Any] = dict(project._mapping)

        # Tasks
        tasks = db.execute(text("""
            SELECT pt.*,
                CONCAT(e.first_name, ' ', e.last_name) as assigned_to_name
            FROM project_tasks pt
            LEFT JOIN employees e ON pt.assigned_to = e.id
            WHERE pt.project_id = :id
            ORDER BY pt.id
        """), {"id": project_id}).fetchall()
        project_data["tasks"] = [dict(t._mapping) for t in tasks]

        # Expenses
        expenses = db.execute(text("""
            SELECT pe.*,
                COALESCE(u.full_name, '') as created_by_name
            FROM project_expenses pe
            LEFT JOIN company_users u ON pe.created_by = u.id
            WHERE pe.project_id = :id
            ORDER BY pe.expense_date DESC
        """), {"id": project_id}).fetchall()
        project_data["expenses"] = [dict(ex._mapping) for ex in expenses]

        # Revenues
        revenues = db.execute(text("""
            SELECT pr.*,
                COALESCE(u.full_name, '') as created_by_name
            FROM project_revenues pr
            LEFT JOIN company_users u ON pr.created_by = u.id
            WHERE pr.project_id = :id
            ORDER BY pr.revenue_date DESC
        """), {"id": project_id}).fetchall()
        project_data["revenues"] = [dict(rv._mapping) for rv in revenues]

        # Financial summary
        total_exp = sum(float(ex.get("amount", 0)) for ex in project_data["expenses"] if ex.get("status") != "rejected")
        total_rev = sum(float(rv.get("amount", 0)) for rv in project_data["revenues"] if rv.get("status") != "rejected")
        planned = float(project_data.get("planned_budget") or 0)

        project_data["financial_summary"] = {
            "planned_budget": planned,
            "total_expenses": total_exp,
            "total_revenues": total_rev,
            "profit_loss": total_rev - total_exp,
            "budget_consumed_pct": round(total_exp / planned * 100, 2) if planned > 0 else 0,
        }

        return project_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("projects.create"))])
async def create_project(
    request: Request,
    project: ProjectCreate,
    current_user: dict = Depends(get_current_user)
):
    """إنشاء مشروع جديد"""
    db = get_db_connection(current_user.company_id)
    try:
        code = project.project_code
        if not code:
            code = generate_sequential_number(db, f"PRJ-{datetime.now().year}", "projects", "project_code")

        result = db.execute(text("""
            INSERT INTO projects (
                project_code, project_name, project_name_en, description,
                project_type, customer_id, manager_id,
                start_date, end_date, planned_budget, status, created_by
            ) VALUES (
                :code, :name, :name_en, :desc,
                :type, :cid, :mid,
                :start, :end, :budget, :status, :uid
            ) RETURNING id
        """), {
            "code": code, "name": project.project_name,
            "name_en": project.project_name_en, "desc": project.description,
            "type": project.project_type, "cid": project.customer_id,
            "mid": project.manager_id,
            "start": project.start_date, "end": project.end_date,
            "budget": project.planned_budget, "status": project.status,
            "uid": current_user.id
        })
        project_id = result.scalar()
        db.commit()

        log_activity(
            db, user_id=current_user.id, username=current_user.username,
            action="project.create", resource_type="project",
            resource_id=str(project_id),
            details={"project_name": project.project_name, "budget": project.planned_budget},
            request=request, branch_id=project.branch_id
        )

        return {"success": True, "id": project_id, "project_code": code, "message": "تم إنشاء المشروع بنجاح"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.put("/{project_id}", dependencies=[Depends(require_permission("projects.edit"))])
async def update_project(
    project_id: int,
    data: ProjectUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """تحديث بيانات مشروع"""
    db = get_db_connection(current_user.company_id)
    try:
        existing = db.execute(text("SELECT * FROM projects WHERE id = :id"), {"id": project_id}).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="المشروع غير موجود")

        updates = []
        params = {"id": project_id}

        field_map = {
            "project_name": "name", "project_name_en": "name_en",
            "description": "desc", "project_type": "type",
            "customer_id": "cid", "manager_id": "mid",
            "start_date": "start", "end_date": "end",
            "planned_budget": "budget", "status": "status",
            "progress_percentage": "pct"
        }

        for field, param in field_map.items():
            value = getattr(data, field, None)
            if value is not None:
                if field == "status":
                    valid = ['planning', 'in_progress', 'on_hold', 'completed', 'cancelled']
                    if value not in valid:
                        raise HTTPException(status_code=400, detail=f"حالة غير صالحة. المتاح: {', '.join(valid)}")
                if field == "progress_percentage" and (value < 0 or value > 100):
                    raise HTTPException(status_code=400, detail="نسبة الإنجاز يجب أن تكون بين 0 و 100")
                updates.append(f"{field} = :{param}")
                params[param] = value

        if not updates:
            raise HTTPException(status_code=400, detail="لا توجد بيانات للتحديث")

        updates.append("updated_at = NOW()")
        query = f"UPDATE projects SET {', '.join(updates)} WHERE id = :id"
        db.execute(text(query), params)
        db.commit()

        log_activity(
            db, user_id=current_user.id, username=current_user.username,
            action="project.update", resource_type="project",
            resource_id=str(project_id), details={}, request=request
        )

        return {"success": True, "message": "تم تحديث المشروع بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.delete("/{project_id}", dependencies=[Depends(require_permission("projects.delete"))])
async def delete_project(project_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    """حذف مشروع (فقط إذا لم يكن له مصاريف أو إيرادات مرحّلة)"""
    db = get_db_connection(current_user.company_id)
    try:
        existing = db.execute(text("SELECT id FROM projects WHERE id = :id"), {"id": project_id}).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="المشروع غير موجود")

        has_posted = db.execute(text("""
            SELECT COUNT(*) FROM (
                SELECT id FROM project_expenses WHERE project_id = :id AND status = 'approved'
                UNION ALL
                SELECT id FROM project_revenues WHERE project_id = :id AND status = 'approved'
            ) x
        """), {"id": project_id}).scalar()

        if has_posted > 0:
            raise HTTPException(
                status_code=400,
                detail="لا يمكن حذف المشروع لوجود مصاريف أو إيرادات مرحّلة. يمكنك إلغاؤه بدلاً من حذفه."
            )

        db.execute(text("DELETE FROM project_revenues WHERE project_id = :id"), {"id": project_id})
        db.execute(text("DELETE FROM project_expenses WHERE project_id = :id"), {"id": project_id})
        db.execute(text("DELETE FROM project_budgets WHERE project_id = :id"), {"id": project_id})
        db.execute(text("DELETE FROM project_tasks WHERE project_id = :id"), {"id": project_id})
        db.execute(text("DELETE FROM projects WHERE id = :id"), {"id": project_id})
        db.commit()

        log_activity(
            db, user_id=current_user.id, username=current_user.username,
            action="project.delete", resource_type="project",
            resource_id=str(project_id), details={}, request=request
        )

        return {"success": True, "message": "تم حذف المشروع"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# Project Tasks
# ═══════════════════════════════════════════════════════════

@router.get("/{project_id}/tasks", dependencies=[Depends(require_permission("projects.view"))])
async def get_project_tasks(project_id: int, current_user: dict = Depends(get_current_user)):
    """جلب مهام المشروع"""
    db = get_db_connection(current_user.company_id)
    try:
        tasks = db.execute(text("""
            SELECT pt.*,
                CONCAT(e.first_name, ' ', e.last_name) as assigned_to_name
            FROM project_tasks pt
            LEFT JOIN employees e ON pt.assigned_to = e.id
            WHERE pt.project_id = :pid
            ORDER BY pt.id
        """), {"pid": project_id}).fetchall()
        return [dict(t._mapping) for t in tasks]
    finally:
        db.close()


@router.post("/{project_id}/tasks", status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission("projects.edit"))])
async def create_task(project_id: int, task: TaskCreate, current_user: dict = Depends(get_current_user)):
    """إضافة مهمة للمشروع"""
    db = get_db_connection(current_user.company_id)
    try:
        project = db.execute(text("SELECT id FROM projects WHERE id = :id"), {"id": project_id}).fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="المشروع غير موجود")

        result = db.execute(text("""
            INSERT INTO project_tasks (
                project_id, task_name, task_name_en, description,
                parent_task_id, assigned_to, start_date, end_date,
                planned_hours, status
            ) VALUES (
                :pid, :name, :name_en, :desc,
                :parent, :assigned, :start, :end,
                :hours, :status
            ) RETURNING id
        """), {
            "pid": project_id,
            "name": task.task_name, "name_en": task.task_name_en,
            "desc": task.description, "parent": task.parent_task_id,
            "assigned": task.assigned_to,
            "start": task.start_date, "end": task.end_date,
            "hours": task.planned_hours, "status": task.status
        })
        task_id = result.scalar()
        db.commit()
        return {"success": True, "id": task_id, "message": "تم إضافة المهمة"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.put("/{project_id}/tasks/{task_id}", dependencies=[Depends(require_permission("projects.edit"))])
async def update_task(project_id: int, task_id: int, data: TaskUpdate, current_user: dict = Depends(get_current_user)):
    """تحديث مهمة"""
    db = get_db_connection(current_user.company_id)
    try:
        existing = db.execute(
            text("SELECT id FROM project_tasks WHERE id = :tid AND project_id = :pid"),
            {"tid": task_id, "pid": project_id}
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="المهمة غير موجودة")

        updates = []
        params = {"tid": task_id}

        fields = {
            "task_name": "name", "description": "desc",
            "assigned_to": "assigned", "start_date": "start",
            "end_date": "end", "planned_hours": "ph",
            "actual_hours": "ah", "progress": "prog", "status": "st"
        }
        for field, param in fields.items():
            value = getattr(data, field, None)
            if value is not None:
                updates.append(f"{field} = :{param}")
                params[param] = value

        if not updates:
            raise HTTPException(status_code=400, detail="لا توجد بيانات للتحديث")

        query = f"UPDATE project_tasks SET {', '.join(updates)} WHERE id = :tid"
        db.execute(text(query), params)

        # Auto-update project progress
        db.execute(text("""
            UPDATE projects SET progress_percentage = (
                SELECT COALESCE(AVG(progress), 0) FROM project_tasks WHERE project_id = :pid
            ), updated_at = NOW()
            WHERE id = :pid
        """), {"pid": project_id})

        db.commit()
        return {"success": True, "message": "تم تحديث المهمة"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.delete("/{project_id}/tasks/{task_id}", dependencies=[Depends(require_permission("projects.edit"))])
async def delete_task(project_id: int, task_id: int, current_user: dict = Depends(get_current_user)):
    """حذف مهمة"""
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(
            text("DELETE FROM project_tasks WHERE id = :tid AND project_id = :pid"),
            {"tid": task_id, "pid": project_id}
        )
        db.commit()
        return {"success": True, "message": "تم حذف المهمة"}
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# Project Expenses (مع ربط محاسبي)
# ═══════════════════════════════════════════════════════════

@router.post("/{project_id}/expenses", status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission("projects.edit"))])
async def create_project_expense(
    project_id: int,
    expense: ProjectExpenseCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    تسجيل مصروف على المشروع مع قيد محاسبي تلقائي:
    مدين: حساب المصاريف | دائن: حساب النقدية/الخزينة
    """
    db = get_db_connection(current_user.company_id)
    try:
        project = db.execute(text("SELECT * FROM projects WHERE id = :id"), {"id": project_id}).fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="المشروع غير موجود")

        base_currency = get_base_currency(db)
        amount = float(expense.amount)

        # Determine expense account
        expense_acc = expense.expense_account_id
        if not expense_acc:
            type_map = {"materials": "acc_map_inventory", "labor": "acc_map_salaries_exp"}
            mapping_key = type_map.get(expense.expense_type)
            if mapping_key:
                expense_acc = get_mapped_account_id(db, mapping_key)
            if not expense_acc:
                expense_acc = db.execute(text(
                    "SELECT id FROM accounts WHERE account_code = 'OP-EXP' LIMIT 1"
                )).scalar()
            if not expense_acc:
                expense_acc = db.execute(text(
                    "SELECT id FROM accounts WHERE account_type = 'expense' LIMIT 1"
                )).scalar()

        if not expense_acc:
            raise HTTPException(status_code=400, detail="لم يتم العثور على حساب المصاريف")

        # Cash/treasury account
        cash_acc = None
        if expense.treasury_id:
            cash_acc = db.execute(text(
                "SELECT gl_account_id FROM treasury_accounts WHERE id = :id"
            ), {"id": expense.treasury_id}).scalar()
        if not cash_acc:
            cash_acc = get_mapped_account_id(db, "acc_map_cash_main")
        if not cash_acc:
            raise HTTPException(status_code=400, detail="لم يتم العثور على حساب النقدية")

        # 1. Record project expense
        exp_id = db.execute(text("""
            INSERT INTO project_expenses (
                project_id, expense_type, expense_date, amount,
                description, status, created_by
            ) VALUES (:pid, :type, :date, :amt, :desc, 'approved', :uid)
            RETURNING id
        """), {
            "pid": project_id, "type": expense.expense_type,
            "date": expense.expense_date, "amt": amount,
            "desc": expense.description, "uid": current_user.id
        }).scalar()

        # 2. Journal Entry
        cost_center_id = db.execute(text(
            "SELECT id FROM cost_centers WHERE center_name ILIKE :name LIMIT 1"
        ), {"name": f"%{project._mapping['project_name']}%"}).scalar()
        
        je_id, _ = gl_create_journal_entry(
            db=db,
            company_id=current_user.company_id,
            date=expense.expense_date.isoformat() if hasattr(expense.expense_date, 'isoformat') else str(expense.expense_date),
            description=f"مصروف مشروع: {project._mapping['project_name']} - {expense.description or expense.expense_type}",
            reference=None,
            status="posted",
            currency=base_currency,
            exchange_rate=1.0,
            lines=[
                {
                    "account_id": expense_acc,
                    "debit": amount,
                    "credit": 0,
                    "description": expense.description or expense.expense_type,
                    "cost_center_id": cost_center_id
                },
                {
                    "account_id": cash_acc,
                    "debit": 0,
                    "credit": amount,
                    "description": expense.description or expense.expense_type,
                    "cost_center_id": cost_center_id
                }
            ],
            user_id=current_user.id,
            branch_id=project._mapping.get('branch_id'),
            source="project_expense",
            source_id=exp_id
        )

        if expense.treasury_id:
            db.execute(text(
                "UPDATE treasury_accounts SET current_balance = current_balance - :amt WHERE id = :id"
            ), {"amt": amount, "id": expense.treasury_id})

        # 4. Update project actual cost
        db.execute(text("""
            UPDATE projects SET actual_cost = COALESCE(actual_cost, 0) + :amt, updated_at = NOW()
            WHERE id = :pid
        """), {"amt": amount, "pid": project_id})

        db.commit()

        log_activity(
            db, user_id=current_user.id, username=current_user.username,
            action="project.expense", resource_type="project_expense",
            resource_id=str(exp_id),
            details={"project_id": project_id, "amount": amount, "type": expense.expense_type},
            request=request
        )

        return {"success": True, "id": exp_id, "journal_entry_id": je_id,
                "message": "تم تسجيل المصروف وإنشاء القيد المحاسبي"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating project expense: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/{project_id}/expenses", dependencies=[Depends(require_permission("projects.view"))])
async def get_project_expenses(project_id: int, current_user: dict = Depends(get_current_user)):
    """جلب مصاريف المشروع"""
    db = get_db_connection(current_user.company_id)
    try:
        result = db.execute(text("""
            SELECT pe.*, COALESCE(u.full_name, '') as created_by_name
            FROM project_expenses pe
            LEFT JOIN company_users u ON pe.created_by = u.id
            WHERE pe.project_id = :pid
            ORDER BY pe.expense_date DESC
        """), {"pid": project_id}).fetchall()
        return [dict(r._mapping) for r in result]
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# Project Revenues (مع ربط محاسبي)
# ═══════════════════════════════════════════════════════════

@router.post("/{project_id}/revenues", status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission("projects.edit"))])
async def create_project_revenue(
    project_id: int,
    revenue: ProjectRevenueCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    تسجيل إيراد على المشروع مع قيد محاسبي:
    مدين: العملاء أو النقدية | دائن: الإيرادات
    """
    db = get_db_connection(current_user.company_id)
    try:
        project = db.execute(text("SELECT * FROM projects WHERE id = :id"), {"id": project_id}).fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="المشروع غير موجود")

        base_currency = get_base_currency(db)
        amount = float(revenue.amount)

        # Revenue account
        revenue_acc = get_mapped_account_id(db, "acc_map_sales_rev")
        if not revenue_acc:
            revenue_acc = db.execute(text(
                "SELECT id FROM accounts WHERE account_type = 'revenue' LIMIT 1"
            )).scalar()
        if not revenue_acc:
            raise HTTPException(status_code=400, detail="لم يتم العثور على حساب الإيرادات")

        # Debit account
        debit_acc = None
        if project._mapping.get("customer_id"):
            debit_acc = get_mapped_account_id(db, "acc_map_ar")
        if not debit_acc:
            debit_acc = get_mapped_account_id(db, "acc_map_cash_main")
        if not debit_acc:
            raise HTTPException(status_code=400, detail="لم يتم العثور على الحساب المدين")

        # 1. Record revenue
        rev_id = db.execute(text("""
            INSERT INTO project_revenues (
                project_id, revenue_type, revenue_date, amount,
                description, invoice_id, status, created_by
            ) VALUES (:pid, :type, :date, :amt, :desc, :inv, 'approved', :uid)
            RETURNING id
        """), {
            "pid": project_id, "type": revenue.revenue_type,
            "date": revenue.revenue_date, "amt": amount,
            "desc": revenue.description, "inv": revenue.invoice_id,
            "uid": current_user.id
        }).scalar()

        # 2. Journal Entry
        cost_center_id = db.execute(text(
            "SELECT id FROM cost_centers WHERE center_name ILIKE :name LIMIT 1"
        ), {"name": f"%{project._mapping['project_name']}%"}).scalar()

        je_id, _ = gl_create_journal_entry(
            db=db,
            company_id=current_user.company_id,
            date=revenue.revenue_date.isoformat() if hasattr(revenue.revenue_date, 'isoformat') else str(revenue.revenue_date),
            description=f"إيراد مشروع: {project._mapping['project_name']} - {revenue.description or revenue.revenue_type}",
            reference=None,
            status="posted",
            currency=base_currency,
            exchange_rate=1.0,
            lines=[
                {
                    "account_id": debit_acc,
                    "debit": amount,
                    "credit": 0,
                    "description": revenue.description or revenue.revenue_type,
                    "cost_center_id": cost_center_id
                },
                {
                    "account_id": revenue_acc,
                    "debit": 0,
                    "credit": amount,
                    "description": revenue.description or revenue.revenue_type,
                    "cost_center_id": cost_center_id
                }
            ],
            user_id=current_user.id,
            branch_id=project._mapping.get('branch_id'),
            source="project_revenue",
            source_id=rev_id
        )

        db.commit()

        log_activity(
            db, user_id=current_user.id, username=current_user.username,
            action="project.revenue", resource_type="project_revenue",
            resource_id=str(rev_id),
            details={"project_id": project_id, "amount": amount, "type": revenue.revenue_type},
            request=request
        )

        return {"success": True, "id": rev_id, "journal_entry_id": je_id,
                "message": "تم تسجيل الإيراد وإنشاء القيد المحاسبي"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating project revenue: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/{project_id}/revenues", dependencies=[Depends(require_permission("projects.view"))])
async def get_project_revenues(project_id: int, current_user: dict = Depends(get_current_user)):
    """جلب إيرادات المشروع"""
    db = get_db_connection(current_user.company_id)
    try:
        result = db.execute(text("""
            SELECT pr.*, COALESCE(u.full_name, '') as created_by_name
            FROM project_revenues pr
            LEFT JOIN company_users u ON pr.created_by = u.id
            WHERE pr.project_id = :pid
            ORDER BY pr.revenue_date DESC
        """), {"pid": project_id}).fetchall()
        return [dict(r._mapping) for r in result]
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# Project Financial Report
# ═══════════════════════════════════════════════════════════

@router.get("/{project_id}/financials", dependencies=[Depends(require_permission("projects.view"))])
async def get_project_financials(project_id: int, current_user: dict = Depends(get_current_user)):
    """تقرير مالي شامل للمشروع"""
    db = get_db_connection(current_user.company_id)
    try:
        project = db.execute(text("SELECT * FROM projects WHERE id = :id"), {"id": project_id}).fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="المشروع غير موجود")

        p = project._mapping

        expenses_by_type = db.execute(text("""
            SELECT expense_type, COUNT(*) as count, SUM(amount) as total
            FROM project_expenses
            WHERE project_id = :pid AND status != 'rejected'
            GROUP BY expense_type
        """), {"pid": project_id}).fetchall()

        revenues_by_type = db.execute(text("""
            SELECT revenue_type, COUNT(*) as count, SUM(amount) as total
            FROM project_revenues
            WHERE project_id = :pid AND status != 'rejected'
            GROUP BY revenue_type
        """), {"pid": project_id}).fetchall()

        monthly = db.execute(text("""
            SELECT
                TO_CHAR(d.month, 'YYYY-MM') as period,
                COALESCE(e.total, 0) as expenses,
                COALESCE(r.total, 0) as revenues
            FROM (
                SELECT DISTINCT DATE_TRUNC('month', expense_date) as month FROM project_expenses WHERE project_id = :pid
                UNION
                SELECT DISTINCT DATE_TRUNC('month', revenue_date) FROM project_revenues WHERE project_id = :pid
            ) d
            LEFT JOIN (
                SELECT DATE_TRUNC('month', expense_date) as month, SUM(amount) as total
                FROM project_expenses WHERE project_id = :pid AND status != 'rejected'
                GROUP BY DATE_TRUNC('month', expense_date)
            ) e ON e.month = d.month
            LEFT JOIN (
                SELECT DATE_TRUNC('month', revenue_date) as month, SUM(amount) as total
                FROM project_revenues WHERE project_id = :pid AND status != 'rejected'
                GROUP BY DATE_TRUNC('month', revenue_date)
            ) r ON r.month = d.month
            ORDER BY d.month
        """), {"pid": project_id}).fetchall()

        total_exp = sum(float(e._mapping["total"]) for e in expenses_by_type)
        total_rev = sum(float(r._mapping["total"]) for r in revenues_by_type)
        planned = float(p.get("planned_budget") or 0)
        
        # Calculate Indirect Costs (Overhead) - For now, assume a fixed 15% of Labor if not explicitly recorded
        # In a real scenario, this might come from a specific 'overhead' expense type
        labor_cost = next((float(e._mapping["total"]) for e in expenses_by_type if e._mapping["expense_type"] == 'labor'), 0)
        direct_materials = next((float(e._mapping["total"]) for e in expenses_by_type if e._mapping["expense_type"] == 'materials'), 0)
        
        # If no explicit 'overhead' expense type exists, we can estimate or just list what's there.
        # Let's just categorize existing expenses into Direct (Labor, Materials) and Indirect (Others)
        direct_types = ['labor', 'materials']
        indirect_cost = sum(float(e._mapping["total"]) for e in expenses_by_type if e._mapping["expense_type"] not in direct_types)

        net_profit = total_rev - total_exp
        margin = (net_profit / total_rev * 100) if total_rev > 0 else 0

        return {
            "project_id": project_id,
            "project_name": p["project_name"],
            "planned_budget": planned,
            "total_expenses": total_exp,
            "total_revenues": total_rev,
            "net_profit": net_profit,
            "margin_pct": round(margin, 2),
            "budget_remaining": planned - total_exp,
            "budget_consumed_pct": round(total_exp / planned * 100, 2) if planned > 0 else 0,
            "cost_breakdown": {
                "labor": labor_cost,
                "materials": direct_materials,
                "indirect_overhead": indirect_cost,
                "details": [dict(e._mapping) for e in expenses_by_type]
            },
            "revenues_by_type": [dict(r._mapping) for r in revenues_by_type],
            "monthly_breakdown": [dict(m._mapping) for m in monthly],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching financials: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/resources/allocation", dependencies=[Depends(require_permission("projects.view"))])
async def get_resource_allocation(
    start_date: date,
    end_date: date,
    current_user: dict = Depends(get_current_user)
):
    """
    تقرير تخصيص الموارد (Resource Allocation)
    يحسب ساعات العمل المخططة لكل موظف يومياً بناءً على المهام المسندة.
    """
    db = get_db_connection(current_user.company_id)
    try:
        # Fetch tasks that overlap with the requested period
        tasks = db.execute(text("""
            SELECT pt.id, pt.task_name, pt.start_date, pt.end_date, pt.planned_hours,
                   pt.assigned_to, CONCAT(e.first_name, ' ', e.last_name) as employee_name,
                   p.project_name
            FROM project_tasks pt
            JOIN projects p ON pt.project_id = p.id
            JOIN employees e ON pt.assigned_to = e.id
            WHERE pt.start_date <= :end AND pt.end_date >= :start
            AND pt.assigned_to IS NOT NULL
            AND p.status IN ('in_progress', 'planning')
        """), {"start": start_date, "end": end_date}).fetchall()

        # Fetch actual timesheets for verification (Optional, maybe for a different view)
        # For allocation, we mainly care about "Planned" load to avoid overloading.

        allocation: Dict[int, Dict[str, Any]] = {}

        # Helper to generate date range
        from datetime import timedelta
        def daterange(start_date, end_date):
            for n in range(int((end_date - start_date).days) + 1):
                yield start_date + timedelta(n)

        req_start = start_date
        req_end = end_date

        for task in tasks:
            emp_id = task.assigned_to
            emp_name = task.employee_name
            
            if emp_id not in allocation:
                allocation[emp_id] = {"id": emp_id, "name": emp_name, "projects": set(), "daily_load": {}}

            allocation[emp_id]["projects"].add(task.project_name)

            # Calculate daily load for this task
            # Intersection of Task Duration and Requested Period
            t_start = max(task.start_date.date() if isinstance(task.start_date, datetime) else task.start_date, req_start)
            t_end = min(task.end_date.date() if isinstance(task.end_date, datetime) else task.end_date, req_end)
            
            if t_start > t_end:
                 continue

            days_count = (task.end_date - task.start_date).days + 1
            if days_count <= 0: days_count = 1
            
            # Simple linear distribution: hours / days
            daily_hours = float(task.planned_hours or 0) / days_count

            for single_date in daterange(t_start, t_end):
                d_str = single_date.isoformat()
                allocation[emp_id]["daily_load"][d_str] = allocation[emp_id]["daily_load"].get(d_str, 0) + daily_hours

        # Format for frontend
        result = []
        for emp_id, data in allocation.items():
            result.append({
                "id": data["id"],
                "name": data["name"],
                "projects": list(data["projects"]),
                "daily_load": [{"date": d, "hours": float(f"{float(h):.2f}")} for d, h in data["daily_load"].items()]
            })

        return result

    except Exception as e:
        logger.error(f"Error fetching resource allocation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# Timesheets (PRJ-002)
# ═══════════════════════════════════════════════════════════

@router.get("/{project_id}/timesheets", dependencies=[Depends(require_permission("projects.view"))])
async def list_project_timesheets(project_id: int, current_user: dict = Depends(get_current_user)):
    """جلب سجلات الوقت لمشروع"""
    db = get_db_connection(current_user.company_id)
    try:
        timesheets = db.execute(text("""
            SELECT ts.*,
                CONCAT(u.first_name, ' ', u.last_name) as employee_name,
                pt.task_name
            FROM project_timesheets ts
            LEFT JOIN employees u ON ts.employee_id = u.id
            LEFT JOIN project_tasks pt ON ts.task_id = pt.id
            WHERE ts.project_id = :pid
            ORDER BY ts.date DESC, ts.created_at DESC
        """), {"pid": project_id}).fetchall()
        return [dict(t._mapping) for t in timesheets]
    finally:
        db.close()


@router.post("/{project_id}/timesheets", status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission("projects.edit"))])
async def create_timesheet(
    project_id: int,
    entry: TimesheetCreate,
    current_user: dict = Depends(get_current_user)
):
    """تسجيل وقت عمل"""
    db = get_db_connection(current_user.company_id)
    try:
        # Check if project exists
        project = db.execute(text("SELECT id FROM projects WHERE id = :id"), {"id": project_id}).fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="المشروع غير موجود")

        ts_id = db.execute(text("""
            INSERT INTO project_timesheets (
                employee_id, project_id, task_id, date, hours, description, status
            ) VALUES (
                :uid, :pid, :tid, :date, :hours, :desc, :status
            ) RETURNING id
        """), {
            "uid": current_user.id,
            "pid": project_id,
            "tid": entry.task_id,
            "date": entry.date,
            "hours": entry.hours,
            "desc": entry.description,
            "status": entry.status
        }).scalar()

        # Update task actual hours if task_id is present
        if entry.task_id:
            db.execute(text("""
                UPDATE project_tasks
                SET actual_hours = COALESCE(actual_hours, 0) + :hours,
                    updated_at = NOW()
                WHERE id = :tid
            """), {"hours": entry.hours, "tid": entry.task_id})

        db.commit()
        return {"success": True, "id": ts_id, "message": "تم تسجيل الوقت بنجاح"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating timesheet: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.put("/timesheets/{timesheet_id}", dependencies=[Depends(require_permission("projects.edit"))])
async def update_timesheet(
    timesheet_id: int,
    entry: TimesheetUpdate,
    current_user: dict = Depends(get_current_user)
):
    """تحديث سجل وقت"""
    db = get_db_connection(current_user.company_id)
    try:
        # Get existing
        existing = db.execute(text("SELECT * FROM project_timesheets WHERE id = :id"), {"id": timesheet_id}).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="السجل غير موجود")
        
        # Check permission (only owner or admin)
        # Note: existing.employee_id refers to company_users.id (based on my schema design)
        # so comparison with current_user.id is correct.
        if existing.employee_id != current_user.id and current_user.role != 'admin':
             raise HTTPException(status_code=403, detail="غير مصرح لك بتعديل هذا السجل")

        # Calculate difference in hours if updating hours/task
        old_hours = float(existing.hours)
        new_hours = entry.hours if entry.hours is not None else old_hours
        diff = new_hours - old_hours
        
        old_task = existing.task_id
        new_task = entry.task_id if entry.task_id is not None else old_task

        # Prepare updates
        updates = []
        params = {"id": timesheet_id}
        fields = {"task_id": "tid", "date": "date", "hours": "hrs", "description": "desc", "status": "st"}
        
        for field, param in fields.items():
            val = getattr(entry, field, None)
            if val is not None:
                updates.append(f"{field} = :{param}")
                params[param] = val
        
        if updates:
            updates.append("updated_at = NOW()")
            db.execute(text(f"UPDATE project_timesheets SET {', '.join(updates)} WHERE id = :id"), params)

            # Update actual hours on task(s)
            if old_task == new_task and diff != 0 and old_task:
                 db.execute(text("UPDATE project_tasks SET actual_hours = actual_hours + :diff WHERE id = :tid"), 
                            {"diff": diff, "tid": old_task})
            
            elif old_task != new_task:
                if old_task:
                    db.execute(text("UPDATE project_tasks SET actual_hours = actual_hours - :hrs WHERE id = :tid"),
                               {"hrs": old_hours, "tid": old_task})
                if new_task:
                    db.execute(text("UPDATE project_tasks SET actual_hours = COALESCE(actual_hours, 0) + :hrs WHERE id = :tid"),
                               {"hrs": new_hours, "tid": new_task})

        db.commit()
        return {"success": True, "message": "تم تحديث السجل"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.delete("/timesheets/{timesheet_id}", dependencies=[Depends(require_permission("projects.edit"))])
async def delete_timesheet(timesheet_id: int, current_user: dict = Depends(get_current_user)):
    """حذف سجل وقت"""
    db = get_db_connection(current_user.company_id)
    try:
        existing = db.execute(text("SELECT * FROM project_timesheets WHERE id = :id"), {"id": timesheet_id}).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="السجل غير موجود")

        if existing.employee_id != current_user.id and current_user.role != 'admin':
             raise HTTPException(status_code=403, detail="غير مصرح لك بحذف هذا السجل")

        # Revert task hours
        if existing.task_id:
            db.execute(text("UPDATE project_tasks SET actual_hours = actual_hours - :hrs WHERE id = :tid"),
                       {"hrs": existing.hours, "tid": existing.task_id})

        db.execute(text("DELETE FROM project_timesheets WHERE id = :id"), {"id": timesheet_id})
        db.commit()
        return {"success": True, "message": "تم حذف السجل"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/{project_id}/timesheets/approve", dependencies=[Depends(require_permission("projects.edit"))])
async def approve_timesheets(
    project_id: int,
    approval: TimesheetApprove,
    current_user: dict = Depends(get_current_user)
):
    """اعتماد سجلات الوقت وتوليد القيود المحاسبية"""
    db = get_db_connection(current_user.company_id)
    trans = db.begin()
    try:
        # 1. Fetch mapping accounts
        acc_labor_exp = get_mapped_account_id(db, "acc_map_salaries_exp")
        acc_payable = get_mapped_account_id(db, "acc_map_accrued_salaries")
        base_curr = get_base_currency(db)

        if not acc_labor_exp or not acc_payable:
            raise HTTPException(status_code=400, detail="حسابات تكلفة العمالة غير معرفة في إعدادات الشركة")

        # 2. Fetch Project Info
        project = db.execute(text("SELECT project_name FROM projects WHERE id = :id"), {"id": project_id}).fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="المشروع غير موجود")

        results = []
        for ts_id in approval.timesheet_ids:
            # Fetch timesheet with employee rates
            ts = db.execute(text("""
                SELECT ts.*, e.hourly_cost, e.salary, e.first_name || ' ' || e.last_name as emp_name
                FROM project_timesheets ts
                JOIN employees e ON ts.employee_id = e.user_id
                WHERE ts.id = :tid AND ts.project_id = :pid AND ts.status = 'draft'
            """), {"tid": ts_id, "pid": project_id}).fetchone()

            if not ts:
                continue

            # Calculate Rate
            rate = float(ts.hourly_cost or 0)
            if rate == 0:
                # Fallback: Monthly Salary / 176 hours
                rate = float(ts.salary or 0) / 176.0
            
            total_cost = round(rate * float(ts.hours), 2)

            if total_cost > 0:
                # A. Create Project Expense Record
                exp_id = db.execute(text("""
                    INSERT INTO project_expenses (
                        project_id, expense_type, expense_date, amount,
                        description, status, created_by
                    ) VALUES (:pid, 'labor', :date, :amt, :desc, 'approved', :uid)
                    RETURNING id
                """), {
                    "pid": project_id,
                    "date": ts.date,
                    "amt": total_cost,
                    "desc": f"تكلفة عمالة: {ts.emp_name} - {ts.description or ts.date}",
                    "uid": current_user.id
                }).scalar()

                # B. Create Journal Entry
                cost_center_id = db.execute(text(
                    "SELECT id FROM cost_centers WHERE center_name ILIKE :name LIMIT 1"
                ), {"name": f"%{project.project_name}%"}).scalar()

                je_id, _ = gl_create_journal_entry(
                    db=db,
                    company_id=current_user.company_id,
                    date=ts.date.isoformat() if hasattr(ts.date, 'isoformat') else str(ts.date),
                    description=f"قيد تكلفة عمالة مشروع: {project.project_name} - {ts.emp_name}",
                    reference=None,
                    status="posted",
                    currency=base_curr,
                    exchange_rate=1.0,
                    lines=[
                        {
                            "account_id": acc_labor_exp,
                            "debit": total_cost,
                            "credit": 0,
                            "description": f"تكلفة عمالة مشروع {project.project_name}",
                            "cost_center_id": cost_center_id
                        },
                        {
                            "account_id": acc_payable,
                            "debit": 0,
                            "credit": total_cost,
                            "description": f"استحقاق رواتب - مشروع {project.project_name}",
                            "cost_center_id": cost_center_id
                        }
                    ],
                    user_id=current_user.id,
                    branch_id=project.branch_id,
                    source="project_timesheet",
                    source_id=ts_id
                )

            # D. Update Timesheet Status
            db.execute(text("UPDATE project_timesheets SET status = 'approved' WHERE id = :id"), {"id": ts_id})
            results.append(ts_id)

        trans.commit()
        return {"success": True, "approved_count": len(results), "message": f"تم اعتماد {len(results)} سجل(ات) بنجاح"}
    except Exception as e:
        trans.rollback()
        logger.error(f"Error approving timesheets: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# ═══════════════════════════════════════════════════════════
# Project Documents
# ═══════════════════════════════════════════════════════════

@router.post("/{project_id}/documents", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("projects.edit"))])
async def create_project_document(
    project_id: int,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """رفع مستند للمشروع"""
    global uploads_dir # Assuming it's available or we find path relative to main
    # But main.py defined it. We should use absolute path or config.
    # We will use 'uploads/projects' relative to backend root or where we are running.
    
    upload_folder = "uploads/projects"
    os.makedirs(upload_folder, exist_ok=True)
    
    from utils.sql_safety import (
        validate_file_extension,
        validate_file_size,
        validate_file_mime_and_signature,
        MAX_DOCUMENT_SIZE,
        ALLOWED_DOCUMENT_EXTENSIONS,
    )

    content = await file.read()
    validate_file_extension(file.filename, ALLOWED_DOCUMENT_EXTENSIONS, "المستند")
    validate_file_size(content, MAX_DOCUMENT_SIZE, "المستند")
    file_ext = validate_file_mime_and_signature(file.filename, file.content_type, content, "المستند")

    unique_filename = f"{project_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_ext}"
    file_path = os.path.join(upload_folder, unique_filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(content)
        
    file_url = f"/uploads/projects/{unique_filename}"
    
    db = get_db_connection(current_user.company_id)
    try:
        doc_id = db.execute(text("""
            INSERT INTO project_documents (
                project_id, file_name, file_url, file_type, uploaded_by
            ) VALUES (:pid, :name, :url, :type, :uid)
            RETURNING id
        """), {
            "pid": project_id,
            "name": file.filename,
            "url": file_url,
            "type": file.content_type,
            "uid": current_user.id
        }).scalar()
        
        db.commit()
        return {"success": True, "id": doc_id, "file_url": file_url, "message": "تم رفع المستند بنجاح"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/{project_id}/documents", dependencies=[Depends(require_permission("projects.view"))])
async def get_project_documents(project_id: int, current_user: dict = Depends(get_current_user)):
    """جلب مستندات المشروع"""
    db = get_db_connection(current_user.company_id)
    try:
        docs = db.execute(text("""
            SELECT pd.*, u.full_name as uploaded_by_name
            FROM project_documents pd
            LEFT JOIN company_users u ON pd.uploaded_by = u.id
            WHERE pd.project_id = :pid
            ORDER BY pd.created_at DESC
        """), {"pid": project_id}).fetchall()
        return [dict(d._mapping) for d in docs]
    finally:
        db.close()

@router.delete("/{project_id}/documents/{doc_id}", dependencies=[Depends(require_permission("projects.edit"))])
async def delete_project_document(project_id: int, doc_id: int, current_user: dict = Depends(get_current_user)):
    """حذف مستند"""
    db = get_db_connection(current_user.company_id)
    try:
        # Get file path to delete from disk
        doc = db.execute(text("SELECT file_url FROM project_documents WHERE id = :id AND project_id = :pid"),
                         {"id": doc_id, "pid": project_id}).fetchone()
        
        if doc and doc.file_url:
            # Construct absolute path. stored as /uploads/...
            # We assume running from backend root, so remove leading /
            rel_path = doc.file_url.lstrip("/")
            if os.path.exists(rel_path):
                os.remove(rel_path)
                
        db.execute(text("DELETE FROM project_documents WHERE id = :id"), {"id": doc_id})
        db.commit()
        return {"success": True, "message": "تم حذف المستند"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# Project Invoicing
# ═══════════════════════════════════════════════════════════

@router.post("/{project_id}/create-invoice", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("projects.edit"))])
async def create_project_invoice(
    project_id: int,
    invoice_data: ProjectInvoiceCreate,
    current_user: dict = Depends(get_current_user)
):
    """إنشاء فاتورة مبيعات من المشروع"""
    db = get_db_connection(current_user.company_id)
    try:
        # Verify Project
        project = db.execute(text("SELECT * FROM projects WHERE id = :id"), {"id": project_id}).fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="المشروع غير موجود")
            
        # 1. Generate Invoice Number
        inv_num = generate_sequential_number(db, f"INV-{datetime.now().year}", "invoices", "invoice_number")
        
        # 2. Calculate Totals
        subtotal = 0
        total_tax = 0
        total_discount = 0
        
        line_items_data = []
        
        for item in invoice_data.items:
            line_sub = item.quantity * item.unit_price
            taxable = line_sub - item.discount
            tax = taxable * (item.tax_rate / 100)
            total = taxable + tax
            
            subtotal += line_sub
            total_tax += tax
            total_discount += item.discount
            
            line_items_data.append({
                "pid": item.product_id,
                "desc": item.description,
                "qty": item.quantity,
                "price": item.unit_price,
                "tax": item.tax_rate,
                "disc": item.discount,
                "total": total
            })
            
        grand_total = subtotal - total_discount + total_tax
        
        # 3. Create Invoice Header
        inv_currency = invoice_data.currency or get_base_currency(db)
        exchange_rate = invoice_data.exchange_rate or 1.0
        
        inv_id = db.execute(text("""
            INSERT INTO invoices (
                invoice_number, party_id, invoice_type, invoice_date, due_date,
                subtotal, tax_amount, discount, total, paid_amount, status, notes,
                payment_method, created_by, branch_id, warehouse_id,
                currency, exchange_rate
            ) VALUES (
                :num, :cust, 'sales', :inv_date, :due_date,
                :sub, :tax, :disc, :total, 0, 'unpaid', :notes,
                :pay_method, :user, :branch, :wh,
                :currency, :rate
            ) RETURNING id
        """), {
            "num": inv_num, "cust": invoice_data.customer_id,
            "inv_date": invoice_data.invoice_date, "due_date": invoice_data.due_date,
            "sub": subtotal, "tax": total_tax, "disc": total_discount, "total": grand_total,
            "notes": invoice_data.notes or f"Project Invoice: {project.project_name}",
            "pay_method": invoice_data.payment_method, "user": current_user.id,
            "branch": project.branch_id, "wh": invoice_data.warehouse_id,
            "currency": inv_currency, "rate": exchange_rate
        }).scalar()
        
        # 4. Create Invoice Lines
        for item in line_items_data:
            db.execute(text("""
                INSERT INTO invoice_lines (
                    invoice_id, product_id, description, quantity, unit_price, tax_rate, discount, total
                ) VALUES (
                    :inv_id, :pid, :desc, :qty, :price, :tax, :disc, :total
                )
            """), {
                "inv_id": inv_id, **item
            })
            
            # NOTE: Logic to deduct inventory is skipped here for simplicity as we assume service/milestone invoice often. 
            # If product_id is provided, we should ideally deduct stock, but recreating full sales logic here is risky.
            # Best practice: Call the Internal create_invoice service.
            
        # 5. Link to Project Revenues (Shadow Record)
        # We manually insert into project_revenues to show it in project financials
        # WE DO NOT CREATE GL ENTRIES HERE because the INVOICE will eventually create GL entries when posted/paid or if we implemented full logic.
        # Actually, since we just inserted 'unpaid' invoice above without GL logic, NO GL exists yet.
        # The user will go to Sales -> Invoices to Post/Pay it.
        # So we just link it.
        
        db.execute(text("""
            INSERT INTO project_revenues (
                project_id, revenue_type, revenue_date, amount,
                description, invoice_id, status, created_by
            ) VALUES (
                :pid, 'invoice', :date, :amt, :desc, :inv_id, 'approved', :uid
            )
        """), {
            "pid": project_id,
            "date": invoice_data.invoice_date,
            "amt": grand_total,
            "desc": f"Invoice #{inv_num}",
            "inv_id": inv_id,
            "uid": current_user.id
        })
        
        # 6. Create GL Journal Entry (PRJ-103)
        # Dr: Accounts Receivable (acc_map_ar)
        # Cr: Sales Revenue (acc_map_sales_rev) — subtotal
        # Cr: VAT Output (acc_map_vat_out) — tax_amount (if any)
        je_id = None
        ar_acc = get_mapped_account_id(db, "acc_map_ar")
        rev_acc = get_mapped_account_id(db, "acc_map_sales_rev") or get_mapped_account_id(db, "acc_map_project_revenue")
        base_currency = get_base_currency(db)
        
        if ar_acc and rev_acc and grand_total > 0:
            lines = []
            cost_center_id = db.execute(text(
                "SELECT id FROM cost_centers WHERE center_name ILIKE :name LIMIT 1"
            ), {"name": f"%{project.project_name}%"}).scalar()

            # Dr: Accounts Receivable = grand_total
            lines.append({
                "account_id": ar_acc,
                "debit": grand_total,
                "credit": 0,
                "description": f"ذمم مدينة — فاتورة مشروع {inv_num}",
                "cost_center_id": cost_center_id
            })
            
            # Cr: Revenue = subtotal (before tax)
            net_revenue = subtotal - total_discount
            if net_revenue > 0:
                lines.append({
                    "account_id": rev_acc,
                    "debit": 0,
                    "credit": net_revenue,
                    "description": f"إيراد مشروع {project.project_name}",
                    "cost_center_id": cost_center_id
                })
            
            # Cr: VAT Output = tax_amount (if applicable)
            if total_tax > 0:
                vat_acc = get_mapped_account_id(db, "acc_map_vat_out") or get_mapped_account_id(db, "acc_map_tax_payable")
                if vat_acc:
                    lines.append({
                        "account_id": vat_acc,
                        "debit": 0,
                        "credit": total_tax,
                        "description": f"ضريبة القيمة المضافة — فاتورة مشروع {inv_num}",
                        "cost_center_id": cost_center_id
                    })

            je_id, entry_num = gl_create_journal_entry(
                db=db,
                company_id=current_user.get("company_id") if isinstance(current_user, dict) else current_user.company_id,
                date=invoice_data.invoice_date,
                description=f"فاتورة مشروع: {project.project_name} — {inv_num}",
                status="posted",
                currency=inv_currency,
                exchange_rate=exchange_rate,
                lines=lines,
                user_id=current_user.get("id") if isinstance(current_user, dict) else current_user.id,
                source="project_invoice",
                source_id=inv_id
            )
            
            # Update invoice with journal entry reference
            db.execute(text("UPDATE invoices SET notes = notes || ' | JE: ' || :je_num WHERE id = :id"),
                       {"je_num": entry_num, "id": inv_id})
        
        db.commit()
        return {
            "success": True, "invoice_id": inv_id, "invoice_number": inv_num,
            "journal_entry_id": je_id,
            "message": "تم إنشاء الفاتورة والقيد المحاسبي بنجاح" if je_id else "تم إنشاء الفاتورة بنجاح (بدون قيد — تحقق من إعداد الحسابات)"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating project invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# Project Change Orders (أوامر التغيير)
# ═══════════════════════════════════════════════════════════

@router.get("/{project_id}/change-orders", dependencies=[Depends(require_permission("projects.view"))])
async def get_change_orders(project_id: int, current_user: dict = Depends(get_current_user)):
    """جلب أوامر التغيير للمشروع"""
    db = get_db_connection(current_user.company_id)
    try:
        result = db.execute(text("""
            SELECT co.*,
                   COALESCE(req.full_name, '') as requested_by_name,
                   COALESCE(app.full_name, '') as approved_by_name
            FROM project_change_orders co
            LEFT JOIN company_users req ON co.requested_by = req.id
            LEFT JOIN company_users app ON co.approved_by = app.id
            WHERE co.project_id = :pid
            ORDER BY co.created_at DESC
        """), {"pid": project_id}).fetchall()
        return [dict(r._mapping) for r in result]
    finally:
        db.close()


@router.post("/{project_id}/change-orders", status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission("projects.edit"))])
async def create_change_order(
    project_id: int,
    co: ChangeOrderCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """إنشاء أمر تغيير جديد"""
    db = get_db_connection(current_user.company_id)
    try:
        project = db.execute(text("SELECT * FROM projects WHERE id = :id"), {"id": project_id}).fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="المشروع غير موجود")

        co_num = generate_sequential_number(db, f"CO-{datetime.now().year}", "project_change_orders", "change_order_number")

        co_id = db.execute(text("""
            INSERT INTO project_change_orders (
                project_id, change_order_number, title, description,
                change_type, cost_impact, time_impact_days, status, requested_by
            ) VALUES (:pid, :num, :title, :desc, :type, :cost, :days, 'pending', :uid)
            RETURNING id
        """), {
            "pid": project_id, "num": co_num, "title": co.title,
            "desc": co.description, "type": co.change_type,
            "cost": co.cost_impact, "days": co.time_impact_days,
            "uid": current_user.id
        }).scalar()

        db.commit()

        log_activity(
            db, user_id=current_user.id, username=current_user.username,
            action="project.change_order.create", resource_type="project_change_order",
            resource_id=str(co_id),
            details={"project_id": project_id, "cost_impact": co.cost_impact, "title": co.title},
            request=request
        )

        return {"success": True, "id": co_id, "change_order_number": co_num}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.put("/change-orders/{co_id}", dependencies=[Depends(require_permission("projects.edit"))])
async def update_change_order(
    co_id: int,
    data: ChangeOrderUpdate,
    current_user: dict = Depends(get_current_user)
):
    """تحديث أمر تغيير"""
    db = get_db_connection(current_user.company_id)
    try:
        existing = db.execute(text("SELECT * FROM project_change_orders WHERE id = :id"), {"id": co_id}).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="أمر التغيير غير موجود")
        if existing.status == 'approved':
            raise HTTPException(status_code=400, detail="لا يمكن تعديل أمر تغيير تمت الموافقة عليه")

        updates = []
        params = {"id": co_id}
        for field in ["title", "description", "change_type", "cost_impact", "time_impact_days", "status"]:
            val = getattr(data, field, None)
            if val is not None:
                updates.append(f"{field} = :{field}")
                params[field] = val
        updates.append("updated_at = NOW()")

        if not updates:
            raise HTTPException(status_code=400, detail="لا توجد بيانات للتحديث")

        db.execute(text(f"UPDATE project_change_orders SET {', '.join(updates)} WHERE id = :id"), params)
        db.commit()
        return {"success": True, "message": "تم تحديث أمر التغيير"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/change-orders/{co_id}/approve", dependencies=[Depends(require_permission("projects.edit"))])
async def approve_change_order(
    co_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """الموافقة على أمر التغيير وتعديل ميزانية المشروع تلقائياً"""
    db = get_db_connection(current_user.company_id)
    try:
        co = db.execute(text("SELECT * FROM project_change_orders WHERE id = :id"), {"id": co_id}).fetchone()
        if not co:
            raise HTTPException(status_code=404, detail="أمر التغيير غير موجود")
        if co.status != 'pending':
            raise HTTPException(status_code=400, detail=f"Cannot approve change order with status '{co.status}'")

        db.execute(text("""
            UPDATE project_change_orders
            SET status = 'approved', approved_by = :uid, approved_at = NOW(), updated_at = NOW()
            WHERE id = :id
        """), {"id": co_id, "uid": current_user.id})

        if co.cost_impact:
            db.execute(text("""
                UPDATE projects
                SET planned_budget = COALESCE(planned_budget, 0) + :cost, updated_at = NOW()
                WHERE id = :pid
            """), {"cost": co.cost_impact, "pid": co.project_id})

        if co.time_impact_days and co.time_impact_days > 0:
            db.execute(text("""
                UPDATE projects
                SET end_date = COALESCE(end_date, CURRENT_DATE) + :days * INTERVAL '1 day', updated_at = NOW()
                WHERE id = :pid
            """), {"days": co.time_impact_days, "pid": co.project_id})

        db.commit()

        log_activity(
            db, user_id=current_user.id, username=current_user.username,
            action="project.change_order.approve", resource_type="project_change_order",
            resource_id=str(co_id),
            details={"project_id": co.project_id, "cost_impact": float(co.cost_impact or 0)},
            request=request
        )

        return {"success": True, "message": "تمت الموافقة على أمر التغيير وتحديث ميزانية المشروع"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# Project Closure with P&L Journal Entry
# ═══════════════════════════════════════════════════════════

@router.post("/{project_id}/close", dependencies=[Depends(require_permission("projects.edit"))])
async def close_project(
    project_id: int,
    close_data: ProjectCloseRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    إغلاق المشروع مع قيد محاسبي لربح/خسارة المشروع.
    يقارن إجمالي الإيرادات بإجمالي المصاريف ويسجل قيد إقفال.
    """
    db = get_db_connection(current_user.company_id)
    try:
        project = db.execute(text("SELECT * FROM projects WHERE id = :id"), {"id": project_id}).fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="المشروع غير موجود")

        p = project._mapping
        if p["status"] == "completed":
            raise HTTPException(status_code=400, detail="المشروع مغلق بالفعل")

        total_expenses = float(db.execute(text(
            "SELECT COALESCE(SUM(amount), 0) FROM project_expenses WHERE project_id = :pid AND status != 'rejected'"
        ), {"pid": project_id}).scalar())

        total_revenues = float(db.execute(text(
            "SELECT COALESCE(SUM(amount), 0) FROM project_revenues WHERE project_id = :pid AND status != 'rejected'"
        ), {"pid": project_id}).scalar())

        net_profit_loss = total_revenues - total_expenses
        base_currency = get_base_currency(db)
        close_date = close_data.close_date or date.today()

        je_id = None
        if abs(net_profit_loss) > 0.01:
            pl_acc = get_mapped_account_id(db, "acc_map_project_pl")
            if not pl_acc:
                pl_acc = db.execute(text(
                    "SELECT id FROM accounts WHERE account_number = '3300' OR account_number = '33' LIMIT 1"
                )).scalar()

            if pl_acc:
                lines = []
                cost_center_id = db.execute(text(
                    "SELECT id FROM cost_centers WHERE center_name ILIKE :name LIMIT 1"
                ), {"name": f"%{p['project_name']}%"}).scalar()

                if net_profit_loss > 0:
                    rev_acc = get_mapped_account_id(db, "acc_map_sales_rev")
                    if rev_acc:
                        lines.append({
                            "account_id": rev_acc, "debit": net_profit_loss, "credit": 0,
                            "description": f"إقفال إيرادات مشروع {p['project_name']}", "cost_center_id": cost_center_id
                        })
                        lines.append({
                            "account_id": pl_acc, "debit": 0, "credit": net_profit_loss,
                            "description": f"ربح مشروع {p['project_name']}", "cost_center_id": cost_center_id
                        })
                else:
                    loss_amount = abs(net_profit_loss)
                    exp_acc = db.execute(text(
                        "SELECT id FROM accounts WHERE account_number = '5200' OR account_number = '52' LIMIT 1"
                    )).scalar()
                    if exp_acc:
                        lines.append({
                            "account_id": pl_acc, "debit": loss_amount, "credit": 0,
                            "description": f"خسارة مشروع {p['project_name']}", "cost_center_id": cost_center_id
                        })
                        lines.append({
                            "account_id": exp_acc, "debit": 0, "credit": loss_amount,
                            "description": f"إقفال مصاريف مشروع {p['project_name']}", "cost_center_id": cost_center_id
                        })
                
                if lines:
                    je_id, entry_num = gl_create_journal_entry(
                        db=db,
                        company_id=current_user.get("company_id") if isinstance(current_user, dict) else current_user.company_id,
                        date=close_date,
                        description=f"إقفال مشروع: {p['project_name']} — صافي {'ربح' if net_profit_loss > 0 else 'خسارة'}: {abs(net_profit_loss):.2f}",
                        status="posted",
                        currency=base_currency,
                        exchange_rate=1.0,
                        lines=lines,
                        user_id=current_user.get("id") if isinstance(current_user, dict) else current_user.id,
                        source="project_closure",
                        source_id=project_id
                    )

        db.execute(text("""
            UPDATE projects
            SET status = 'completed', progress_percentage = 100,
                actual_cost = :cost, end_date = :date, updated_at = NOW()
            WHERE id = :id
        """), {"cost": total_expenses, "date": close_date, "id": project_id})

        db.commit()

        log_activity(
            db, user_id=current_user.id, username=current_user.username,
            action="project.close", resource_type="project",
            resource_id=str(project_id),
            details={"net_profit_loss": net_profit_loss,
                     "total_expenses": total_expenses,
                     "total_revenues": total_revenues},
            request=request
        )

        return {
            "success": True,
            "message": "تم إغلاق المشروع بنجاح",
            "summary": {
                "total_expenses": total_expenses,
                "total_revenues": total_revenues,
                "net_profit_loss": net_profit_loss,
                "journal_entry_id": je_id,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error closing project: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# PRJ-107: Retainer Auto-Billing (فوترة دورية تلقائية)
# ═══════════════════════════════════════════════════════════

class RetainerSetup(BaseModel):
    retainer_amount: float
    billing_cycle: str = "monthly"  # monthly, quarterly, yearly
    next_billing_date: Optional[date] = None

@router.put("/{project_id}/retainer-setup", dependencies=[Depends(require_permission("projects.edit"))])
async def setup_retainer(
    project_id: int,
    data: RetainerSetup,
    current_user: dict = Depends(get_current_user)
):
    """إعداد الفوترة الدورية لعقد Retainer"""
    db = get_db_connection(current_user.company_id)
    try:
        project = db.execute(text("SELECT * FROM projects WHERE id = :id"), {"id": project_id}).fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="المشروع غير موجود")
        
        next_date = data.next_billing_date or date.today()
        db.execute(text("""
            UPDATE projects SET 
                contract_type = 'retainer',
                retainer_amount = :amt,
                billing_cycle = :cycle,
                next_billing_date = :next_date,
                updated_at = NOW()
            WHERE id = :id
        """), {
            "amt": data.retainer_amount, "cycle": data.billing_cycle,
            "next_date": next_date, "id": project_id
        })
        db.commit()
        return {"success": True, "message": "تم إعداد الفوترة الدورية بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/retainer/generate-invoices", dependencies=[Depends(require_permission("projects.edit"))])
async def generate_retainer_invoices(
    request: Request,
    billing_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    توليد فواتير دورية تلقائية لعقود Retainer المستحقة.
    Generate automatic periodic invoices for due Retainer contracts.
    Creates invoice + GL entry (Dr AR / Cr Revenue) for each project.
    """
    db = get_db_connection(current_user.company_id)
    try:
        target_date = billing_date or date.today()
        
        # Find retainer projects due for billing
        projects = db.execute(text("""
            SELECT p.*, 
                   COALESCE(c.name, pa.name, '') as customer_name,
                   COALESCE(p.customer_id, p.party_id) as bill_to_id
            FROM projects p
            LEFT JOIN customers c ON p.customer_id = c.id
            LEFT JOIN parties pa ON p.party_id = pa.id
            WHERE p.contract_type = 'retainer'
              AND p.retainer_amount > 0
              AND p.status NOT IN ('completed', 'cancelled')
              AND (p.next_billing_date IS NULL OR p.next_billing_date <= :target)
        """), {"target": target_date}).fetchall()
        
        if not projects:
            return {"success": True, "generated": 0, "message": "لا توجد عقود مستحقة للفوترة"}
        
        base_currency = get_base_currency(db)
        ar_acc = get_mapped_account_id(db, "acc_map_ar")
        rev_acc = get_mapped_account_id(db, "acc_map_sales_rev") or get_mapped_account_id(db, "acc_map_project_revenue")
        
        generated = []
        
        for proj in projects:
            p = proj._mapping
            amount = float(p["retainer_amount"])
            if amount <= 0:
                continue
            
            # Generate invoice
            inv_num = generate_sequential_number(db, f"RET-{target_date.year}", "invoices", "invoice_number")
            bill_to = p.get("bill_to_id") or p.get("customer_id")
            
            inv_id = db.execute(text("""
                INSERT INTO invoices (
                    invoice_number, party_id, invoice_type, invoice_date, due_date,
                    subtotal, tax_amount, discount, total, paid_amount, status, notes,
                    payment_method, created_by, branch_id, currency, exchange_rate
                ) VALUES (
                    :num, :cust, 'sales', :inv_date, :due_date,
                    :amt, 0, 0, :amt, 0, 'unpaid',
                    :notes, 'credit', :uid, :branch, :curr, 1.0
                ) RETURNING id
            """), {
                "num": inv_num, "cust": bill_to,
                "inv_date": target_date,
                "due_date": target_date + timedelta(days=30),
                "amt": amount,
                "notes": f"فاتورة دورية (Retainer) — مشروع: {p['project_name']}",
                "uid": current_user.id, "branch": p.get("branch_id"),
                "curr": base_currency
            }).scalar()
            
            # Invoice line
            db.execute(text("""
                INSERT INTO invoice_lines (invoice_id, description, quantity, unit_price, tax_rate, discount, total)
                VALUES (:inv_id, :desc, 1, :price, 0, 0, :total)
            """), {
                "inv_id": inv_id, "desc": f"رسوم اشتراك — مشروع {p['project_name']}",
                "price": amount, "total": amount
            })
            
            # Link to project revenues
            db.execute(text("""
                INSERT INTO project_revenues (project_id, revenue_type, revenue_date, amount, description, invoice_id, status, created_by)
                VALUES (:pid, 'retainer', :date, :amt, :desc, :inv_id, 'approved', :uid)
            """), {
                "pid": p["id"], "date": target_date, "amt": amount,
                "desc": f"فاتورة Retainer #{inv_num}", "inv_id": inv_id, "uid": current_user.id
            })
            
            # GL Entry: Dr AR / Cr Revenue
            je_id = None
            if ar_acc and rev_acc:
                cost_center_id = db.execute(text(
                    "SELECT id FROM cost_centers WHERE center_name ILIKE :name LIMIT 1"
                ), {"name": f"%{p['project_name']}%"}).scalar()

                je_id, entry_num = gl_create_journal_entry(
                    db=db,
                    company_id=current_user.get("company_id") if isinstance(current_user, dict) else current_user.company_id,
                    date=target_date,
                    description=f"فاتورة Retainer — {p['project_name']} — {inv_num}",
                    status="posted",
                    currency=base_currency,
                    exchange_rate=1.0,
                    lines=[
                        {
                            "account_id": ar_acc, "debit": amount, "credit": 0,
                            "description": f"ذمم مدينة — Retainer {p['project_name']}", "cost_center_id": cost_center_id
                        },
                        {
                            "account_id": rev_acc, "debit": 0, "credit": amount,
                            "description": f"إيراد Retainer {p['project_name']}", "cost_center_id": cost_center_id
                        }
                    ],
                    user_id=current_user.get("id") if isinstance(current_user, dict) else current_user.id,
                    source="project_invoice",
                    source_id=inv_id
                )
            
            # Calculate next billing date
            cycle = p.get("billing_cycle", "monthly")
            if cycle == "monthly":
                next_date = target_date + timedelta(days=30)
            elif cycle == "quarterly":
                next_date = target_date + timedelta(days=90)
            elif cycle == "yearly":
                next_date = target_date + timedelta(days=365)
            else:
                next_date = target_date + timedelta(days=30)
            
            db.execute(text("""
                UPDATE projects SET last_billed_date = :billed, next_billing_date = :next, updated_at = NOW()
                WHERE id = :id
            """), {"billed": target_date, "next": next_date, "id": p["id"]})
            
            generated.append({
                "project_id": p["id"], "project_name": p["project_name"],
                "invoice_id": inv_id, "invoice_number": inv_num,
                "amount": amount, "journal_entry_id": je_id
            })
        
        db.commit()
        
        return {
            "success": True,
            "generated": len(generated),
            "invoices": generated,
            "message": f"تم إنشاء {len(generated)} فاتورة Retainer بنجاح"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating retainer invoices: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# Earned Value Management (EVM)
# ═══════════════════════════════════════════════════════════

@router.get("/{project_id}/evm", dependencies=[Depends(require_permission("projects.view"))])
async def get_earned_value_metrics(project_id: int, current_user: dict = Depends(get_current_user)):
    """
    حساب مقاييس القيمة المكتسبة (EVM):
    PV (Planned Value), EV (Earned Value), AC (Actual Cost)
    SPI, CPI, EAC, ETC, VAC, TCPI
    """
    db = get_db_connection(current_user.company_id)
    try:
        project = db.execute(text("SELECT * FROM projects WHERE id = :id"), {"id": project_id}).fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="المشروع غير موجود")

        p = project._mapping
        bac = float(p.get("planned_budget") or 0)
        progress = float(p.get("progress_percentage") or 0) / 100.0

        start_dt = p.get("start_date")
        end_dt = p.get("end_date")
        today = date.today()

        schedule_progress = 0.0
        if start_dt and end_dt and end_dt > start_dt:
            total_days = (end_dt - start_dt).days
            elapsed_days = min((today - start_dt).days, total_days)
            schedule_progress = max(0.0, elapsed_days / total_days) if total_days > 0 else 0.0

        pv = bac * schedule_progress          # Planned Value
        ev = bac * progress                    # Earned Value
        ac = float(db.execute(text(
            "SELECT COALESCE(SUM(amount), 0) FROM project_expenses WHERE project_id = :pid AND status != 'rejected'"
        ), {"pid": project_id}).scalar())

        spi = ev / pv if pv > 0 else 0.0
        cpi = ev / ac if ac > 0 else 0.0
        sv = ev - pv
        cv = ev - ac
        eac = bac / cpi if cpi > 0 else bac * 2
        etc = max(0.0, eac - ac)
        vac = bac - eac

        remaining_work = bac - ev
        remaining_budget = bac - ac
        tcpi = remaining_work / remaining_budget if remaining_budget > 0 else None

        return {
            "project_id": project_id,
            "project_name": p["project_name"],
            "metrics": {
                "BAC": round(bac, 2),
                "PV": round(pv, 2),
                "EV": round(ev, 2),
                "AC": round(ac, 2),
                "SV": round(sv, 2),
                "CV": round(cv, 2),
                "SPI": round(spi, 4),
                "CPI": round(cpi, 4),
                "EAC": round(eac, 2),
                "ETC": round(etc, 2),
                "VAC": round(vac, 2),
                "TCPI": round(tcpi, 4) if tcpi is not None else None,
            },
            "interpretation": {
                "schedule": "ahead" if spi > 1 else ("on_track" if spi == 1 else "behind"),
                "cost": "under_budget" if cpi > 1 else ("on_budget" if cpi == 1 else "over_budget"),
                "schedule_progress_pct": round(schedule_progress * 100, 2),
                "completion_pct": round(progress * 100, 2),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating EVM: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# Project Reports
# ═══════════════════════════════════════════════════════════

@router.get("/reports/profitability", dependencies=[Depends(require_permission("projects.view"))])
async def report_project_profitability(
    status_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """تقرير ربحية المشاريع"""
    db = get_db_connection(current_user.company_id)
    try:
        where = "WHERE 1=1"
        params = {}
        if status_filter:
            where += " AND p.status = :status"
            params["status"] = status_filter

        rows = db.execute(text(f"""
            SELECT p.id, p.project_code, p.project_name, p.status,
                   p.planned_budget, p.progress_percentage,
                   p.start_date, p.end_date,
                   COALESCE(exp.total, 0) as total_expenses,
                   COALESCE(rev.total, 0) as total_revenues
            FROM projects p
            LEFT JOIN (
                SELECT project_id, SUM(amount) as total
                FROM project_expenses WHERE status != 'rejected'
                GROUP BY project_id
            ) exp ON exp.project_id = p.id
            LEFT JOIN (
                SELECT project_id, SUM(amount) as total
                FROM project_revenues WHERE status != 'rejected'
                GROUP BY project_id
            ) rev ON rev.project_id = p.id
            {where}
            ORDER BY (COALESCE(rev.total, 0) - COALESCE(exp.total, 0)) DESC
        """), params).fetchall()

        projects_list = []
        total_revenue_sum = 0.0
        total_expense_sum = 0.0
        for r in rows:
            m = r._mapping
            rev = float(m["total_revenues"] or 0)
            exp = float(m["total_expenses"] or 0)
            net = rev - exp
            margin = (net / rev * 100) if rev > 0 else 0.0
            budget = float(m["planned_budget"] or 0)
            budget_var = budget - exp

            projects_list.append({
                "project_id": m["id"],
                "project_code": m["project_code"],
                "project_name": m["project_name"],
                "status": m["status"],
                "planned_budget": budget,
                "total_expenses": round(exp, 2),
                "total_revenues": round(rev, 2),
                "net_profit": round(net, 2),
                "margin_pct": round(margin, 2),
                "budget_variance": round(budget_var, 2),
                "progress": float(m["progress_percentage"] or 0),
            })
            total_revenue_sum += rev
            total_expense_sum += exp

        total_net = total_revenue_sum - total_expense_sum
        avg_margin = (total_net / total_revenue_sum * 100) if total_revenue_sum > 0 else 0.0

        return {
            "report_name": "تقرير ربحية المشاريع",
            "projects": projects_list,
            "totals": {
                "total_revenue": round(total_revenue_sum, 2),
                "total_expense": round(total_expense_sum, 2),
                "total_profit": round(total_net, 2),
                "avg_margin_pct": round(avg_margin, 2),
                "project_count": len(projects_list),
            }
        }
    finally:
        db.close()


@router.get("/reports/variance", dependencies=[Depends(require_permission("projects.view"))])
async def report_project_variance(current_user: dict = Depends(get_current_user)):
    """تقرير انحراف المشاريع (Budget vs Actual)"""
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(text("""
            SELECT p.id, p.project_code, p.project_name, p.status,
                   p.planned_budget, p.progress_percentage,
                   p.start_date, p.end_date,
                   COALESCE(exp.total, 0) as actual_expenses,
                   COALESCE(ts.total_hours, 0) as actual_hours,
                   COALESCE(tk.planned_hours, 0) as planned_hours
            FROM projects p
            LEFT JOIN (
                SELECT project_id, SUM(amount) as total
                FROM project_expenses WHERE status != 'rejected'
                GROUP BY project_id
            ) exp ON exp.project_id = p.id
            LEFT JOIN (
                SELECT project_id, SUM(hours) as total_hours
                FROM project_timesheets WHERE status = 'approved'
                GROUP BY project_id
            ) ts ON ts.project_id = p.id
            LEFT JOIN (
                SELECT project_id, SUM(planned_hours) as planned_hours
                FROM project_tasks
                GROUP BY project_id
            ) tk ON tk.project_id = p.id
            WHERE p.status != 'cancelled'
            ORDER BY p.id
        """)).fetchall()

        projects_list = []
        for r in rows:
            m = r._mapping
            budget = float(m["planned_budget"] or 0)
            actual = float(m["actual_expenses"] or 0)
            cost_var = budget - actual
            cost_var_pct = (cost_var / budget * 100) if budget > 0 else 0.0

            planned_h = float(m["planned_hours"] or 0)
            actual_h = float(m["actual_hours"] or 0)
            hour_var = planned_h - actual_h

            schedule_var_days = None
            if m["end_date"] and m["status"] not in ["completed", "cancelled"]:
                schedule_var_days = (m["end_date"] - date.today()).days

            projects_list.append({
                "project_id": m["id"],
                "project_code": m["project_code"],
                "project_name": m["project_name"],
                "status": m["status"],
                "planned_budget": budget,
                "actual_cost": round(actual, 2),
                "cost_variance": round(cost_var, 2),
                "cost_variance_pct": round(cost_var_pct, 2),
                "planned_hours": planned_h,
                "actual_hours": actual_h,
                "hours_variance": round(hour_var, 2),
                "progress": float(m["progress_percentage"] or 0),
                "schedule_days_remaining": schedule_var_days,
                "is_over_budget": actual > budget if budget > 0 else False,
                "is_behind_schedule": schedule_var_days is not None and schedule_var_days < 0,
            })

        overbudget = sum(1 for p in projects_list if p["is_over_budget"])
        behind = sum(1 for p in projects_list if p["is_behind_schedule"])

        return {
            "report_name": "تقرير انحراف المشاريع",
            "projects": projects_list,
            "summary": {
                "total_projects": len(projects_list),
                "over_budget_count": overbudget,
                "behind_schedule_count": behind,
                "on_track_count": len(projects_list) - overbudget - behind,
            }
        }
    finally:
        db.close()


@router.get("/reports/resource-utilization", dependencies=[Depends(require_permission("projects.view"))])
async def report_resource_utilization(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user)
):
    """تقرير استخدام الموارد عبر المشاريع"""
    db = get_db_connection(current_user.company_id)
    try:
        date_filter = ""
        params = {}
        if start_date:
            date_filter += " AND ts.date >= :start"
            params["start"] = start_date
        if end_date:
            date_filter += " AND ts.date <= :end"
            params["end"] = end_date

        rows = db.execute(text(f"""
            SELECT u.id as user_id, u.full_name,
                   COUNT(DISTINCT ts.project_id) as projects_count,
                   SUM(ts.hours) as total_hours,
                   AVG(ts.hours) as avg_daily_hours,
                   COUNT(DISTINCT ts.date) as working_days
            FROM project_timesheets ts
            JOIN company_users u ON ts.employee_id = u.id
            WHERE ts.status = 'approved' {date_filter}
            GROUP BY u.id, u.full_name
            ORDER BY total_hours DESC
        """), params).fetchall()

        resources = []
        for r in rows:
            m = r._mapping
            total_h = float(m["total_hours"] or 0)
            working_days = int(m["working_days"] or 1)
            standard_hours = working_days * 8
            utilization = (total_h / standard_hours * 100) if standard_hours > 0 else 0.0

            resources.append({
                "user_id": m["user_id"],
                "name": m["full_name"],
                "projects_count": m["projects_count"],
                "total_hours": round(total_h, 2),
                "avg_daily_hours": round(float(m["avg_daily_hours"] or 0), 2),
                "working_days": working_days,
                "utilization_pct": round(utilization, 2),
            })

        return {
            "report_name": "تقرير استخدام الموارد",
            "period": {
                "start": str(start_date) if start_date else "All",
                "end": str(end_date) if end_date else "All"
            },
            "resources": resources,
        }
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# PRJ-108: Schedule & Budget Alerts Dashboard
# ═══════════════════════════════════════════════════════════

@router.get("/alerts/overdue-tasks", dependencies=[Depends(require_permission("projects.view"))])
async def get_overdue_tasks(current_user: dict = Depends(get_current_user)):
    """
    المهام المتأخرة: المهام التي تجاوزت تاريخ الانتهاء ولم تكتمل بعد.
    """
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(text("""
            SELECT t.id, t.task_name, t.end_date, t.status,
                   t.progress,
                   p.id as project_id, p.project_code, p.project_name,
                   COALESCE(u.full_name, '') as assigned_to_name,
                   (CURRENT_DATE - t.end_date) as days_overdue
            FROM project_tasks t
            JOIN projects p ON t.project_id = p.id
            LEFT JOIN company_users u ON t.assigned_to = u.id
            WHERE t.end_date < CURRENT_DATE
              AND t.status NOT IN ('completed', 'cancelled')
              AND p.status NOT IN ('completed', 'cancelled')
            ORDER BY days_overdue DESC
        """)).fetchall()

        tasks_list = [dict(r._mapping) for r in rows]

        return {
            "alert_type": "overdue_tasks",
            "count": len(tasks_list),
            "tasks": tasks_list,
            "message": f"{len(tasks_list)} مهمة متأخرة تستلزم اهتماماً" if tasks_list else "لا توجد مهام متأخرة ✓",
        }
    finally:
        db.close()


@router.get("/alerts/over-budget", dependencies=[Depends(require_permission("projects.view"))])
async def get_over_budget_projects(current_user: dict = Depends(get_current_user)):
    """المشاريع التي تجاوزت ميزانيتها المخططة."""
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(text("""
            SELECT p.id, p.project_code, p.project_name, p.status,
                   p.planned_budget,
                   COALESCE(exp.total, 0) as actual_cost,
                   COALESCE(exp.total, 0) - p.planned_budget as overage,
                   CASE WHEN p.planned_budget > 0
                        THEN ROUND(((COALESCE(exp.total,0) - p.planned_budget) / p.planned_budget * 100)::numeric, 1)
                        ELSE 0 END as overage_pct,
                   p.progress_percentage
            FROM projects p
            LEFT JOIN (
                SELECT project_id, SUM(amount) as total
                FROM project_expenses WHERE status != 'rejected'
                GROUP BY project_id
            ) exp ON exp.project_id = p.id
            WHERE p.planned_budget > 0
              AND COALESCE(exp.total, 0) > p.planned_budget
              AND p.status NOT IN ('completed', 'cancelled')
            ORDER BY overage_pct DESC
        """)).fetchall()

        projects_list = [dict(r._mapping) for r in rows]

        return {
            "alert_type": "over_budget",
            "count": len(projects_list),
            "projects": projects_list,
            "message": f"{len(projects_list)} مشروع تجاوز الميزانية" if projects_list else "جميع المشاريع ضمن الميزانية ✓",
        }
    finally:
        db.close()


@router.get("/alerts/dashboard", dependencies=[Depends(require_permission("projects.view"))])
async def get_alerts_dashboard(current_user: dict = Depends(get_current_user)):
    """
    لوحة تنبيهات المشاريع الشاملة:
    - مهام متأخرة
    - مشاريع تجاوزت الميزانية
    - مشاريع قاربت على الموعد النهائي (<14 يوم)
    - مشاريع تجاوزت الموعد النهائي
    """
    db = get_db_connection(current_user.company_id)
    try:
        today = date.today()

        # Overdue tasks
        overdue_tasks_count = db.execute(text("""
            SELECT COUNT(*) FROM project_tasks t
            JOIN projects p ON t.project_id = p.id
            WHERE t.end_date < CURRENT_DATE
              AND t.status NOT IN ('completed', 'cancelled')
              AND p.status NOT IN ('completed', 'cancelled')
        """)).scalar()

        # Over-budget projects
        over_budget_count = db.execute(text("""
            SELECT COUNT(*) FROM projects p
            LEFT JOIN (
                SELECT project_id, SUM(amount) as total FROM project_expenses
                WHERE status != 'rejected' GROUP BY project_id
            ) exp ON exp.project_id = p.id
            WHERE p.planned_budget > 0
              AND COALESCE(exp.total,0) > p.planned_budget
              AND p.status NOT IN ('completed','cancelled')
        """)).scalar()

        # Projects ending within 14 days
        due_soon = db.execute(text("""
            SELECT id, project_code, project_name, end_date,
                   (end_date - CURRENT_DATE) as days_remaining,
                   progress_percentage
            FROM projects
            WHERE end_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '14 days'
              AND status NOT IN ('completed', 'cancelled')
            ORDER BY end_date
        """)).fetchall()

        # Projects past end_date
        overdue_projects = db.execute(text("""
            SELECT id, project_code, project_name, end_date,
                   (CURRENT_DATE - end_date) as days_overdue,
                   progress_percentage
            FROM projects
            WHERE end_date < CURRENT_DATE
              AND status NOT IN ('completed', 'cancelled')
            ORDER BY days_overdue DESC
        """)).fetchall()

        # Pending change orders
        pending_cos = db.execute(text("""
            SELECT COUNT(*) FROM project_change_orders
            WHERE status = 'pending'
        """)).scalar() or 0

        alerts = []
        if overdue_tasks_count:
            alerts.append({"type": "overdue_tasks", "severity": "high",
                           "message": f"{overdue_tasks_count} مهمة متأخرة", "count": overdue_tasks_count})
        if over_budget_count:
            alerts.append({"type": "over_budget", "severity": "high",
                           "message": f"{over_budget_count} مشروع تجاوز الميزانية", "count": over_budget_count})
        if overdue_projects:
            alerts.append({"type": "overdue_projects", "severity": "critical",
                           "message": f"{len(overdue_projects)} مشروع تجاوز الموعد النهائي", "count": len(overdue_projects)})
        if due_soon:
            alerts.append({"type": "due_soon", "severity": "medium",
                           "message": f"{len(due_soon)} مشروع ينتهي خلال 14 يوماً", "count": len(due_soon)})
        if pending_cos:
            alerts.append({"type": "pending_change_orders", "severity": "low",
                           "message": f"{pending_cos} أوامر تغيير في انتظار الموافقة", "count": pending_cos})

        return {
            "total_alerts": len(alerts),
            "alerts": alerts,
            "details": {
                "overdue_tasks_count": int(overdue_tasks_count or 0),
                "over_budget_count": int(over_budget_count or 0),
                "overdue_projects": [dict(r._mapping) for r in overdue_projects],
                "due_soon_projects": [dict(r._mapping) for r in due_soon],
                "pending_change_orders": int(pending_cos),
            }
        }
    finally:
        db.close()


# ===================== B5: Project Risks =====================

@router.get("/{project_id}/risks")
def list_project_risks(project_id: int, current_user=Depends(get_current_user)):
    """سجل المخاطر"""
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(text("""
            SELECT pr.*, u.full_name as owner_name
            FROM project_risks pr
            LEFT JOIN users u ON u.id = pr.owner_id
            WHERE pr.project_id = :pid
            ORDER BY pr.risk_score DESC NULLS LAST, pr.created_at DESC
        """), {"pid": project_id}).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.post("/{project_id}/risks")
def create_project_risk(project_id: int, risk: dict, current_user=Depends(get_current_user)):
    """إضافة خطر"""
    db = get_db_connection(current_user.company_id)
    try:
        prob = float(risk.get("probability", 0.5))
        impact = float(risk.get("impact", 0.5))
        score = round(prob * impact, 4)
        result = db.execute(text("""
            INSERT INTO project_risks (project_id, title, description, probability,
                impact, risk_score, status, mitigation_plan, owner_id, due_date)
            VALUES (:pid, :t, :d, :p, :i, :s, :st, :mp, :oid, :dd)
            RETURNING id
        """), {
            "pid": project_id, "t": risk["title"], "d": risk.get("description"),
            "p": prob, "i": impact, "s": score,
            "st": risk.get("status", "identified"), "mp": risk.get("mitigation_plan"),
            "oid": risk.get("owner_id"), "dd": risk.get("due_date")
        })
        risk_id = result.fetchone()[0]
        db.commit()
        return {"id": risk_id, "message": "تم إضافة الخطر بنجاح"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.put("/risks/{risk_id}")
def update_project_risk(risk_id: int, risk: dict, current_user=Depends(get_current_user)):
    """تحديث خطر"""
    db = get_db_connection(current_user.company_id)
    try:
        prob = float(risk.get("probability", 0.5))
        impact = float(risk.get("impact", 0.5))
        score = round(prob * impact, 4)
        db.execute(text("""
            UPDATE project_risks SET title = :t, description = :d, probability = :p,
                impact = :i, risk_score = :s, status = :st, mitigation_plan = :mp,
                owner_id = :oid, due_date = :dd
            WHERE id = :id
        """), {
            "t": risk["title"], "d": risk.get("description"),
            "p": prob, "i": impact, "s": score,
            "st": risk.get("status"), "mp": risk.get("mitigation_plan"),
            "oid": risk.get("owner_id"), "dd": risk.get("due_date"), "id": risk_id
        })
        db.commit()
        return {"message": "تم تحديث الخطر بنجاح"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.delete("/risks/{risk_id}")
def delete_project_risk(risk_id: int, current_user=Depends(get_current_user)):
    """حذف خطر"""
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(text("DELETE FROM project_risks WHERE id = :id"), {"id": risk_id})
        db.commit()
        return {"message": "تم حذف الخطر"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


# ===================== B5: Task Dependencies =====================

@router.get("/{project_id}/task-dependencies")
def list_task_dependencies(project_id: int, current_user=Depends(get_current_user)):
    """تبعيات المهام"""
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(text("""
            SELECT td.*, t1.name as task_name, t2.name as depends_on_name
            FROM task_dependencies td
            LEFT JOIN project_tasks t1 ON t1.id = td.task_id
            LEFT JOIN project_tasks t2 ON t2.id = td.depends_on_task_id
            WHERE td.project_id = :pid
            ORDER BY td.task_id
        """), {"pid": project_id}).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.post("/{project_id}/task-dependencies")
def create_task_dependency(project_id: int, dep: dict, current_user=Depends(get_current_user)):
    """إنشاء تبعية مهمة"""
    db = get_db_connection(current_user.company_id)
    try:
        result = db.execute(text("""
            INSERT INTO task_dependencies (project_id, task_id, depends_on_task_id,
                dependency_type, lag_days)
            VALUES (:pid, :tid, :did, :dt, :ld)
            RETURNING id
        """), {
            "pid": project_id, "tid": dep["task_id"], "did": dep["depends_on_task_id"],
            "dt": dep.get("dependency_type", "FS"), "ld": dep.get("lag_days", 0)
        })
        dep_id = result.fetchone()[0]
        db.commit()
        return {"id": dep_id, "message": "تم إنشاء التبعية بنجاح"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.delete("/task-dependencies/{dep_id}")
def delete_task_dependency(dep_id: int, current_user=Depends(get_current_user)):
    """حذف تبعية"""
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(text("DELETE FROM task_dependencies WHERE id = :id"), {"id": dep_id})
        db.commit()
        return {"message": "تم حذف التبعية"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()
