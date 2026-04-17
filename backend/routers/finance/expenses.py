"""
AMAN ERP - Expenses Module
وحدة إدارة المصاريف - مع نظام اعتماد وربط محاسبي كامل
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from utils.i18n import http_error
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
from database import get_db_connection
from routers.auth import get_current_user
from sqlalchemy import text
from utils.permissions import require_permission, validate_branch_access, require_module
from utils.accounting import (
    generate_sequential_number, get_mapped_account_id,
    get_base_currency, update_account_balance, validate_je_lines
)
from utils.audit import log_activity
from utils.fiscal_lock import check_fiscal_period_open
import logging

logger = logging.getLogger(__name__)

from schemas.expenses import ExpenseCreate, ExpenseUpdate, ExpenseApproval

router = APIRouter(prefix="/expenses", tags=["المصاريف"], dependencies=[Depends(require_module("expenses"))])


# ═══════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════

def get_expense_account_by_type(db, expense_type: str) -> Optional[int]:
    """تحديد حساب المصروف بناءً على النوع"""
    type_map = {
        "rent": "acc_map_rent_expense",
        "utilities": "acc_map_utilities_expense",
        "salaries": "acc_map_salaries",
        "materials": "acc_map_inventory",
        "travel": "acc_map_travel_expense",
    }
    
    mapped_key = type_map.get(expense_type)
    if mapped_key:
        acc_id = get_mapped_account_id(db, mapped_key)
        if acc_id:
            return acc_id
    
    # Fallback: general expense
    acc_id = get_mapped_account_id(db, "acc_map_general_expense")
    if acc_id:
        return acc_id
    
    # Last resort: any expense account
    return db.execute(text(
        "SELECT id FROM accounts WHERE account_type = 'expense' AND is_active = true LIMIT 1"
    )).scalar()


def create_expense_journal_entry(db, expense_data: dict, user_id: int, base_currency: str):
    """إنشاء قيد محاسبي للمصروف"""
    from services.gl_service import create_journal_entry as gl_create_journal_entry
    
    je_number = generate_sequential_number(db, "EXP", "journal_entries", "entry_number")
    
    je_lines = [
        {
            "account_id": expense_data["expense_account_id"], 
            "debit": float(expense_data["amount"]), 
            "credit": 0,
            "cost_center_id": expense_data.get("cost_center_id"),
            "description": expense_data.get("description")
        },
        {
            "account_id": expense_data["cash_account_id"], 
            "debit": 0, 
            "credit": float(expense_data["amount"]),
            "description": expense_data.get("description")
        },
    ]

    je_id, _ = gl_create_journal_entry(
        db=db,
        company_id=expense_data.get("company_id", 1), # Fallback to 1 if not provided
        date=expense_data["expense_date"],
        description=f"مصروف {expense_data['expense_type']}: {expense_data.get('description', '')}",
        lines=je_lines,
        user_id=user_id,
        branch_id=expense_data.get("branch_id"),
        reference=je_number,
        currency=base_currency,
        exchange_rate=1.0,
        source="expense",
        source_id=expense_data.get("expense_id")
    )
    
    # Update journal entry number to keep the EXP- prefix (since gl_service generates JV-)
    db.execute(text("UPDATE journal_entries SET entry_number = :num WHERE id = :id"), {"num": je_number, "id": je_id})
    
    return je_id, je_number


# ═══════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/", dependencies=[Depends(require_permission("expenses.view"))])
async def list_expenses(
    branch_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    expense_type: Optional[str] = None,
    approval_status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """قائمة المصاريف مع الفلاتر"""
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    
    try:
        params = {"company_id": current_user.company_id}
        filters = ["1=1"]
        
        if branch_id:
            filters.append("e.branch_id = :branch_id")
            params["branch_id"] = branch_id
        if start_date:
            filters.append("e.expense_date >= :start_date")
            params["start_date"] = start_date
        if end_date:
            filters.append("e.expense_date <= :end_date")
            params["end_date"] = end_date
        if expense_type:
            filters.append("e.expense_type = :expense_type")
            params["expense_type"] = expense_type
        if approval_status:
            filters.append("e.approval_status = :approval_status")
            params["approval_status"] = approval_status
        if search:
            filters.append("(e.description ILIKE :search OR e.expense_number ILIKE :search)")
            params["search"] = f"%{search}%"
        
        where_clause = " AND ".join(filters)
        
        result = db.execute(text(f"""
            SELECT 
                e.id, e.expense_number, e.expense_date, e.expense_type,
                e.amount, e.description, e.category, e.payment_method,
                e.approval_status, e.receipt_number, e.vendor_name,
                e.created_at, e.branch_id,
                u.username as created_by_name,
                cc.center_name as cost_center_name,
                p.project_name,
                ta.name as treasury_name,
                approver.username as approved_by_name,
                e.approved_at
            FROM expenses e
            LEFT JOIN company_users u ON e.created_by = u.id
            LEFT JOIN cost_centers cc ON e.cost_center_id = cc.id
            LEFT JOIN projects p ON e.project_id = p.id
            LEFT JOIN treasury_accounts ta ON e.treasury_id = ta.id
            LEFT JOIN company_users approver ON e.approved_by = approver.id
            WHERE {where_clause}
            ORDER BY e.expense_date DESC, e.id DESC
            LIMIT 100
        """), params).fetchall()
        
        return [dict(r._mapping) for r in result]
    finally:
        db.close()


@router.get("/summary", dependencies=[Depends(require_permission("expenses.view"))])
async def get_expenses_summary(
    branch_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user)
):
    """إحصائيات المصاريف"""
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    
    try:
        params = {}
        filters = ["1=1"]
        
        if branch_id:
            filters.append("branch_id = :branch_id")
            params["branch_id"] = branch_id
        if start_date:
            filters.append("expense_date >= :start_date")
            params["start_date"] = start_date
        if end_date:
            filters.append("expense_date <= :end_date")
            params["end_date"] = end_date
        
        where_clause = " AND ".join(filters)
        
        result = db.execute(text(f"""
            SELECT
                COUNT(*) as total_expenses,
                SUM(CASE WHEN approval_status = 'pending' THEN 1 ELSE 0 END) as pending_approval,
                SUM(CASE WHEN approval_status = 'approved' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN approval_status = 'rejected' THEN 1 ELSE 0 END) as rejected,
                SUM(amount) as total_amount,
                SUM(CASE WHEN approval_status = 'approved' THEN amount ELSE 0 END) as approved_amount,
                SUM(CASE WHEN approval_status = 'pending' THEN amount ELSE 0 END) as pending_amount
            FROM expenses
            WHERE {where_clause}
        """), params).fetchone()
        
        return dict(result._mapping) if result else {
            "total_expenses": 0, "pending_approval": 0, "approved": 0, "rejected": 0,
            "total_amount": 0, "approved_amount": 0, "pending_amount": 0
        }
    finally:
        db.close()



# ===================== C1: Expense Policies =====================

@router.get("/policies", dependencies=[Depends(require_permission("expenses.view"))])
def list_expense_policies(current_user=Depends(get_current_user)):
    """سياسات المصروفات"""
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(text("""
            SELECT ep.*, d.department_name as department_name
            FROM expense_policies ep
            LEFT JOIN departments d ON d.id = ep.department_id
            ORDER BY ep.name
        """)).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.post("/policies", dependencies=[Depends(require_permission("expenses.manage"))])
def create_expense_policy(policy: dict, current_user=Depends(get_current_user)):
    """إنشاء سياسة مصروفات"""
    db = get_db_connection(current_user.company_id)
    try:
        result = db.execute(text("""
            INSERT INTO expense_policies (name, expense_type, department_id,
                daily_limit, monthly_limit, annual_limit, requires_receipt,
                requires_approval, auto_approve_below, is_active)
            VALUES (:n, :et, :did, :dl, :ml, :al, :rr, :ra, :aab, :ia)
            RETURNING id
        """), {
            "n": policy["name"], "et": policy.get("expense_type"),
            "did": policy.get("department_id"), "dl": policy.get("daily_limit"),
            "ml": policy.get("monthly_limit"), "al": policy.get("annual_limit"),
            "rr": policy.get("requires_receipt", True),
            "ra": policy.get("requires_approval", True),
            "aab": policy.get("auto_approve_below"), "ia": policy.get("is_active", True)
        })
        pid = result.fetchone()[0]
        db.commit()
        return {"id": pid, "message": "تم إنشاء سياسة المصروفات بنجاح"}
    except Exception as e:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@router.put("/policies/{policy_id}", dependencies=[Depends(require_permission("expenses.manage"))])
def update_expense_policy(policy_id: int, policy: dict, current_user=Depends(get_current_user)):
    """تحديث سياسة مصروفات"""
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(text("""
            UPDATE expense_policies SET name = :n, expense_type = :et,
                department_id = :did, daily_limit = :dl, monthly_limit = :ml,
                annual_limit = :al, requires_receipt = :rr, requires_approval = :ra,
                auto_approve_below = :aab, is_active = :ia
            WHERE id = :id
        """), {
            "n": policy["name"], "et": policy.get("expense_type"),
            "did": policy.get("department_id"), "dl": policy.get("daily_limit"),
            "ml": policy.get("monthly_limit"), "al": policy.get("annual_limit"),
            "rr": policy.get("requires_receipt", True),
            "ra": policy.get("requires_approval", True),
            "aab": policy.get("auto_approve_below"), "ia": policy.get("is_active", True),
            "id": policy_id
        })
        db.commit()
        return {"message": "تم تحديث السياسة بنجاح"}
    except Exception as e:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@router.delete("/policies/{policy_id}", dependencies=[Depends(require_permission("expenses.manage"))])
def delete_expense_policy(policy_id: int, current_user=Depends(get_current_user)):
    """حذف سياسة مصروفات"""
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(text("DELETE FROM expense_policies WHERE id = :id"), {"id": policy_id})
        db.commit()
        return {"message": "تم حذف السياسة"}
    except Exception as e:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@router.post("/validate-policy")
def validate_expense_against_policy(expense: dict, current_user=Depends(get_current_user)):
    """التحقق من المصروف ضد السياسات"""
    db = get_db_connection(current_user.company_id)
    try:
        amount = float(expense.get("amount", 0))
        exp_type = expense.get("expense_type")
        dept_id = expense.get("department_id")

        policies = db.execute(text("""
            SELECT * FROM expense_policies
            WHERE is_active = TRUE
              AND (expense_type IS NULL OR expense_type = :et)
              AND (department_id IS NULL OR department_id = :did)
        """), {"et": exp_type, "did": dept_id}).fetchall()

        violations = []
        auto_approve = True
        for p in policies:
            pol = dict(p._mapping)
            if pol.get("daily_limit") and amount > float(pol["daily_limit"]):
                violations.append(f"يتجاوز الحد اليومي ({pol['daily_limit']})")
            if pol.get("auto_approve_below") and amount >= float(pol["auto_approve_below"]):
                auto_approve = False
            if pol.get("requires_receipt"):
                if not expense.get("has_receipt"):
                    violations.append("يتطلب إيصال")

        return {
            "valid": len(violations) == 0,
            "auto_approve": auto_approve and len(violations) == 0,
            "violations": violations,
            "policies_checked": len(policies)
        }
    finally:
        db.close()


@router.get("/{expense_id}", dependencies=[Depends(require_permission("expenses.view"))])
async def get_expense_details(expense_id: int, current_user: dict = Depends(get_current_user)):
    """تفاصيل مصروف محدد"""
    db = get_db_connection(current_user.company_id)
    
    try:
        result = db.execute(text("""
            SELECT 
                e.*,
                u.username as created_by_name,
                cc.center_name as cost_center_name,
                p.project_name, p.project_code,
                ta.name as treasury_name,
                approver.username as approved_by_name,
                a.name as expense_account_name,
                a.account_number as expense_account_number
            FROM expenses e
            LEFT JOIN company_users u ON e.created_by = u.id
            LEFT JOIN cost_centers cc ON e.cost_center_id = cc.id
            LEFT JOIN projects p ON e.project_id = p.id
            LEFT JOIN treasury_accounts ta ON e.treasury_id = ta.id
            LEFT JOIN company_users approver ON e.approved_by = approver.id
            LEFT JOIN accounts a ON e.expense_account_id = a.id
            WHERE e.id = :id
        """), {"id": expense_id}).fetchone()
        
        if not result:
            raise HTTPException(**http_error(404, "expense_not_found"))
        
        expense = dict(result._mapping)
        
        # Get journal entry if exists
        je = db.execute(text("""
            SELECT id, entry_number, entry_date, description, status
            FROM journal_entries
            WHERE entry_number LIKE :pattern
            ORDER BY created_at DESC
            LIMIT 1
        """), {"pattern": f"%{expense['expense_number']}%"}).fetchone()
        
        expense["journal_entry"] = dict(je._mapping) if je else None
        
        return expense
    finally:
        db.close()


@router.post("/", status_code=status.HTTP_201_CREATED, 
             dependencies=[Depends(require_permission("expenses.create"))])
async def create_expense(
    request: Request, 
    expense: ExpenseCreate, 
    current_user: dict = Depends(get_current_user)
):
    """إنشاء مصروف جديد"""
    expense.branch_id = validate_branch_access(current_user, expense.branch_id)
    db = get_db_connection(current_user.company_id)
    
    try:
        base_currency = get_base_currency(db)
        
        # Determine expense account
        expense_account_id = expense.expense_account_id
        if not expense_account_id:
            expense_account_id = get_expense_account_by_type(db, expense.expense_type)
        
        if not expense_account_id:
            raise HTTPException(status_code=400, detail="يجب تحديد حساب المصروف")
        
        # Determine cash/bank account
        cash_account_id = None
        if expense.treasury_id:
            cash_account_id = db.execute(text(
                "SELECT gl_account_id FROM treasury_accounts WHERE id = :id"
            ), {"id": expense.treasury_id}).scalar()
        
        if not cash_account_id:
            cash_account_id = get_mapped_account_id(db, "acc_map_cash_main")
        
        if not cash_account_id:
            raise HTTPException(status_code=400, detail="يجب تحديد حساب النقدية")
        
        # Generate expense number
        expense_number = generate_sequential_number(db, "EXP", "expenses", "expense_number")
        
        # Initial approval status
        approval_status = "pending" if expense.requires_approval else "approved"
        
        # Insert expense record
        expense_id = db.execute(text("""
            INSERT INTO expenses (
                expense_number, expense_date, expense_type, amount, description,
                category, payment_method, treasury_id, expense_account_id,
                cost_center_id, project_id, branch_id, approval_status,
                receipt_number, vendor_name, created_by
            ) VALUES (
                :num, :date, :type, :amt, :desc,
                :cat, :pm, :tid, :eaid,
                :ccid, :pid, :bid, :status,
                :receipt, :vendor, :uid
            ) RETURNING id
        """), {
            "num": expense_number, "date": expense.expense_date, "type": expense.expense_type,
            "amt": float(expense.amount), "desc": expense.description,
            "cat": expense.category, "pm": expense.payment_method, "tid": expense.treasury_id,
            "eaid": expense_account_id,
            "ccid": expense.cost_center_id, "pid": expense.project_id, "bid": expense.branch_id,
            "status": approval_status,
            "receipt": expense.receipt_number, "vendor": expense.vendor_name, "uid": current_user.id
        }).scalar()
        
        # If auto-approved, create journal entry immediately
        if approval_status == "approved":
            expense_data = {
                "expense_date": expense.expense_date,
                "expense_type": expense.expense_type,
                "amount": float(expense.amount),
                "description": expense.description,
                "expense_account_id": expense_account_id,
                "cash_account_id": cash_account_id,
                "cost_center_id": expense.cost_center_id,
                "branch_id": expense.branch_id,
                "company_id": current_user.company_id,
                "expense_id": expense_id
            }
            je_id, je_number = create_expense_journal_entry(db, expense_data, current_user.id, base_currency)
            
            # Update expense with journal entry reference
            db.execute(text("""
                UPDATE expenses SET journal_entry_id = :jid WHERE id = :id
            """), {"jid": je_id, "id": expense_id})
            
            # Update treasury balance (with sufficiency check)
            if expense.treasury_id:
                treasury_balance = db.execute(text(
                    "SELECT current_balance FROM treasury_accounts WHERE id = :id"
                ), {"id": expense.treasury_id}).scalar() or 0
                if float(treasury_balance) < float(expense.amount):
                    raise HTTPException(status_code=400, detail=f"رصيد الخزينة غير كافٍ. المتوفر: {float(treasury_balance):.2f}, المطلوب: {float(expense.amount):.2f}")
                db.execute(text("""
                    UPDATE treasury_accounts 
                    SET current_balance = current_balance - :amt 
                    WHERE id = :id
                """), {"amt": float(expense.amount), "id": expense.treasury_id})
            
            # Update project actual_cost if linked
            if expense.project_id:
                db.execute(text("""
                    UPDATE projects 
                    SET actual_cost = actual_cost + :amt
                    WHERE id = :id
                """), {"amt": float(expense.amount), "id": expense.project_id})
        
        db.commit()
        
        log_activity(
            db, user_id=current_user.id, username=current_user.username,
            action="expense.create", resource_type="expense", resource_id=str(expense_id),
            details={"expense_number": expense_number, "amount": float(expense.amount)},
            request=request, branch_id=expense.branch_id
        )
        
        # Submit for approval workflow if pending
        approval_info = None
        if approval_status == "pending":
            try:
                from utils.approval_utils import try_submit_for_approval
                approval_info = try_submit_for_approval(
                    db,
                    document_type="expense",
                    document_id=expense_id,
                    document_number=expense_number,
                    amount=float(expense.amount),
                    submitted_by=current_user.id,
                    description=f"مصروف {expense.expense_type}: {expense.description or ''} - {float(expense.amount):,.2f}",
                    link=f"/expenses/{expense_id}"
                )
                if approval_info:
                    db.commit()
            except Exception:
                pass  # Non-blocking
        
        response = {
            "success": True,
            "id": expense_id,
            "expense_number": expense_number,
            "approval_status": approval_status,
            "message": "تم إنشاء المصروف بنجاح" if approval_status == "approved" else "تم إنشاء المصروف - في انتظار الاعتماد"
        }

        # Notify about expense submission
        if approval_status == "pending":
            try:
                db.execute(text("""
                    INSERT INTO notifications (user_id, type, title, message, link, is_read, created_at)
                    SELECT DISTINCT u.id, 'expense', :title, :message, :link, FALSE, NOW()
                    FROM company_users u
                    WHERE u.is_active = TRUE AND u.role IN ('admin', 'superuser')
                    AND u.id != :current_uid
                """), {
                    "title": "🧳 طلب مصروف جديد",
                    "message": f"مصروف {expense_number} — {float(expense.amount):,.2f} — {expense.description or expense.expense_type}",
                    "link": f"/expenses/{expense_id}",
                    "current_uid": current_user.id
                })
                db.commit()
            except Exception:
                pass

        if approval_info:
            response["approval"] = approval_info
        return response
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating expense: {e}")
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@router.put("/{expense_id}", dependencies=[Depends(require_permission("expenses.edit"))])
async def update_expense(
    request: Request,
    expense_id: int,
    expense: ExpenseUpdate,
    current_user: dict = Depends(get_current_user)
):
    """تعديل مصروف"""
    db = get_db_connection(current_user.company_id)
    
    try:
        # Check if expense exists and is pending
        existing = db.execute(text(
            "SELECT id, approval_status FROM expenses WHERE id = :id"
        ), {"id": expense_id}).fetchone()
        
        if not existing:
            raise HTTPException(**http_error(404, "expense_not_found"))
        
        if existing.approval_status != "pending":
            raise HTTPException(status_code=400, detail="لا يمكن تعديل مصروف معتمد أو مرفوض")
        
        # Build update fields
        update_fields = []
        params = {"id": expense_id}
        
        for field in ["expense_date", "expense_type", "amount", "description", "category",
                     "payment_method", "treasury_id", "expense_account_id", "cost_center_id",
                     "project_id", "receipt_number", "vendor_name"]:
            value = getattr(expense, field)
            if value is not None:
                update_fields.append(f"{field} = :{field}")
                params[field] = value
        
        if not update_fields:
            raise HTTPException(**http_error(400, "no_data_to_update"))
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        db.execute(text(f"""
            UPDATE expenses SET {', '.join(update_fields)}
            WHERE id = :id
        """), params)
        
        db.commit()
        
        log_activity(
            db, user_id=current_user.id, username=current_user.username,
            action="expense.update", resource_type="expense", resource_id=str(expense_id),
            details={"updates": update_fields}, request=request
        )
        
        return {"success": True, "message": "تم تحديث المصروف بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@router.post("/{expense_id}/approve", dependencies=[Depends(require_permission("expenses.approve"))])
async def approve_expense(
    request: Request,
    expense_id: int,
    approval: ExpenseApproval,
    current_user: dict = Depends(get_current_user)
):
    """اعتماد أو رفض مصروف"""
    db = get_db_connection(current_user.company_id)
    
    try:
        # Get expense details
        expense_row = db.execute(text("""
            SELECT e.*, a.id as expense_account_id, ta.gl_account_id as cash_account_id
            FROM expenses e
            LEFT JOIN accounts a ON e.expense_account_id = a.id
            LEFT JOIN treasury_accounts ta ON e.treasury_id = ta.id
            WHERE e.id = :id
        """), {"id": expense_id}).fetchone()
        
        if not expense_row:
            raise HTTPException(**http_error(404, "expense_not_found"))
        
        expense = dict(expense_row._mapping)
        
        if expense["approval_status"] != "pending":
            raise HTTPException(status_code=400, detail="المصروف تم اعتماده أو رفضه مسبقاً")
        
        # Update approval status
        db.execute(text("""
            UPDATE expenses 
            SET approval_status = :status, 
                approved_by = :uid, 
                approved_at = CURRENT_TIMESTAMP,
                approval_notes = :notes
            WHERE id = :id
        """), {
            "status": approval.approval_status, 
            "uid": current_user.id, 
            "notes": approval.approval_notes,
            "id": expense_id
        })
        
        # If approved, create journal entry
        if approval.approval_status == "approved":
            base_currency = get_base_currency(db)
            
            # Determine cash account
            cash_account_id = expense["cash_account_id"]
            if not cash_account_id:
                cash_account_id = get_mapped_account_id(db, "acc_map_cash_main")
            
            if not cash_account_id:
                raise HTTPException(status_code=400, detail="حساب النقدية غير محدد")
            
            expense_data = {
                "expense_date": expense["expense_date"],
                "expense_type": expense["expense_type"],
                "amount": float(expense["amount"]),
                "description": expense["description"],
                "expense_account_id": expense["expense_account_id"],
                "cash_account_id": cash_account_id,
                "cost_center_id": expense["cost_center_id"],
                "branch_id": expense["branch_id"],
                "company_id": current_user.company_id,
                "expense_id": expense_id
            }
            je_id, je_number = create_expense_journal_entry(db, expense_data, current_user.id, base_currency)
            
            # Link journal entry to expense
            db.execute(text("""
                UPDATE expenses SET journal_entry_id = :jid WHERE id = :id
            """), {"jid": je_id, "id": expense_id})
            
            # Update treasury balance (with sufficiency check)
            if expense["treasury_id"]:
                treasury_balance = db.execute(text(
                    "SELECT current_balance FROM treasury_accounts WHERE id = :id"
                ), {"id": expense["treasury_id"]}).scalar() or 0
                if float(treasury_balance) < float(expense["amount"]):
                    raise HTTPException(status_code=400, detail=f"رصيد الخزينة غير كافٍ. المتوفر: {float(treasury_balance):.2f}, المطلوب: {float(expense['amount']):.2f}")
                db.execute(text("""
                    UPDATE treasury_accounts 
                    SET current_balance = current_balance - :amt 
                    WHERE id = :id
                """), {"amt": float(expense["amount"]), "id": expense["treasury_id"]})
            
            # Update project actual_cost if linked
            if expense["project_id"]:
                db.execute(text("""
                    UPDATE projects 
                    SET actual_cost = actual_cost + :amt
                    WHERE id = :id
                """), {"amt": float(expense["amount"]), "id": expense["project_id"]})
        
        db.commit()
        
        log_activity(
            db, user_id=current_user.id, username=current_user.username,
            action=f"expense.{approval.approval_status}", resource_type="expense",
            resource_id=str(expense_id),
            details={"approval_status": approval.approval_status, "notes": approval.approval_notes},
            request=request
        )
        
        message = "تم اعتماد المصروف بنجاح" if approval.approval_status == "approved" else "تم رفض المصروف"

        # Notify the expense submitter
        try:
            submitted_by = db.execute(text("SELECT created_by FROM expenses WHERE id = :id"), {"id": expense_id}).scalar()
            if submitted_by:
                icon = "✅" if approval.approval_status == "approved" else "❌"
                status_ar = "اعتُمد" if approval.approval_status == "approved" else "رُفض"
                exp_num = expense.get('expense_number', '') if isinstance(expense, dict) else ''
                db.execute(text("""
                    INSERT INTO notifications (user_id, type, title, message, link, is_read, created_at)
                    VALUES (:uid, 'expense_status', :title, :message, :link, FALSE, NOW())
                """), {
                    "uid": submitted_by,
                    "title": f"{icon} مصروفك {status_ar}",
                    "message": f"تم {status_ar} المصروف {exp_num} بمبلغ {float(expense.get('amount', 0)):,.2f}" if isinstance(expense, dict) else f"تم {status_ar} طلب المصروف",
                    "link": f"/expenses/{expense_id}"
                })
                db.commit()
        except Exception:
            pass

        return {"success": True, "message": message}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error approving expense: {e}")
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@router.delete("/{expense_id}", dependencies=[Depends(require_permission("expenses.delete"))])
async def delete_expense(
    request: Request,
    expense_id: int,
    current_user: dict = Depends(get_current_user)
):
    """حذف مصروف (فقط إذا كان معلق)"""
    db = get_db_connection(current_user.company_id)
    
    try:
        expense = db.execute(text(
            "SELECT approval_status FROM expenses WHERE id = :id"
        ), {"id": expense_id}).fetchone()
        
        if not expense:
            raise HTTPException(**http_error(404, "expense_not_found"))
        
        if expense.approval_status != "pending":
            raise HTTPException(status_code=400, detail="لا يمكن حذف مصروف معتمد - يجب إنشاء قيد عكسي")
        
        db.execute(text("DELETE FROM expenses WHERE id = :id"), {"id": expense_id})
        db.commit()
        
        log_activity(
            db, user_id=current_user.id, username=current_user.username,
            action="expense.delete", resource_type="expense", resource_id=str(expense_id),
            request=request
        )
        
        return {"success": True, "message": "تم حذف المصروف بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@router.get("/reports/by-type", dependencies=[Depends(require_permission("expenses.view"))])
async def get_expenses_by_type(
    branch_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user)
):
    """تقرير المصاريف حسب النوع"""
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    
    try:
        params = {}
        filters = ["approval_status = 'approved'"]
        
        if branch_id:
            filters.append("branch_id = :branch_id")
            params["branch_id"] = branch_id
        if start_date:
            filters.append("expense_date >= :start_date")
            params["start_date"] = start_date
        if end_date:
            filters.append("expense_date <= :end_date")
            params["end_date"] = end_date
        
        where_clause = " AND ".join(filters)
        
        result = db.execute(text(f"""
            SELECT 
                expense_type,
                COUNT(*) as count,
                SUM(amount) as total_amount,
                AVG(amount) as avg_amount,
                MIN(amount) as min_amount,
                MAX(amount) as max_amount
            FROM expenses
            WHERE {where_clause}
            GROUP BY expense_type
            ORDER BY total_amount DESC
        """), params).fetchall()
        
        return [dict(r._mapping) for r in result]
    finally:
        db.close()


@router.get("/reports/by-cost-center", dependencies=[Depends(require_permission("expenses.view"))])
async def get_expenses_by_cost_center(
    branch_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user)
):
    """تقرير المصاريف حسب مركز التكلفة"""
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    
    try:
        params = {}
        filters = ["e.approval_status = 'approved'"]
        
        if branch_id:
            filters.append("e.branch_id = :branch_id")
            params["branch_id"] = branch_id
        if start_date:
            filters.append("e.expense_date >= :start_date")
            params["start_date"] = start_date
        if end_date:
            filters.append("e.expense_date <= :end_date")
            params["end_date"] = end_date
        
        where_clause = " AND ".join(filters)
        
        result = db.execute(text(f"""
            SELECT 
                COALESCE(cc.center_name, 'غير محدد') as cost_center_name,
                COUNT(*) as count,
                SUM(e.amount) as total_amount
            FROM expenses e
            LEFT JOIN cost_centers cc ON e.cost_center_id = cc.id
            WHERE {where_clause}
            GROUP BY cc.center_name
            ORDER BY total_amount DESC
        """), params).fetchall()
        
        return [dict(r._mapping) for r in result]
    finally:
        db.close()


@router.get("/reports/monthly", dependencies=[Depends(require_permission("expenses.view"))])
async def get_monthly_expenses(
    branch_id: Optional[int] = None,
    year: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """تقرير المصاريف الشهري"""
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    
    try:
        from datetime import datetime
        current_year = year or datetime.now().year
        
        params = {"year": current_year}
        filters = ["approval_status = 'approved'", "EXTRACT(YEAR FROM expense_date) = :year"]
        
        if branch_id:
            filters.append("branch_id = :branch_id")
            params["branch_id"] = branch_id
        
        where_clause = " AND ".join(filters)
        
        result = db.execute(text(f"""
            SELECT 
                EXTRACT(MONTH FROM expense_date) as month,
                COUNT(*) as count,
                SUM(amount) as total_amount
            FROM expenses
            WHERE {where_clause}
            GROUP BY EXTRACT(MONTH FROM expense_date)
            ORDER BY month
        """), params).fetchall()
        
        return [dict(r._mapping) for r in result]
    finally:
        db.close()

