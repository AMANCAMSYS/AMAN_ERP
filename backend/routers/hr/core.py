from fastapi import APIRouter, Depends, HTTPException, Request
from utils.i18n import http_error
from sqlalchemy import text
from typing import List, Optional, Any, Dict
from routers.roles import DEFAULT_ROLES
from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
import logging
from database import get_db_connection, hash_password
from routers.auth import get_current_user, UserResponse, get_current_user_company
from utils.permissions import require_permission, validate_branch_access, check_permission, require_module
from utils.accounting import get_mapped_account_id, get_base_currency
from utils.fiscal_lock import check_fiscal_period_open
from utils.audit import log_activity
from schemas.hr import LoanCreate, LoanResponse, EmployeeCreate, EmployeeUpdate, DepartmentCreate, DepartmentResponse, PositionCreate, PositionResponse, PayrollPeriodCreate, PayrollEntryResponse, PayrollPeriodResponse, AttendanceResponse, LeaveRequestCreate, LeaveRequestResponse, EndOfServiceRequest
from services.gl_service import create_journal_entry as gl_create_journal_entry

logger = logging.getLogger(__name__)

_D2 = Decimal('0.01')

def _dec(v: Any) -> Decimal:
    return Decimal(str(v or 0))

router = APIRouter(prefix="/hr", tags=["HR & Employees"], dependencies=[Depends(require_module("hr"))])

# --- Helpers ---

def has_permission(user: UserResponse, permission: str) -> bool:
    """Helper to check permissions for a user object"""
    user_perms = getattr(user, 'permissions', []) or []
    return check_permission(user_perms, permission)

# get_current_user_company moved to routers.auth

# --- Endpoints ---

@router.get("/employees", dependencies=[Depends(require_permission("hr.view"))])
def get_employees(
    branch_id: Optional[int] = None, 
    current_user: UserResponse = Depends(get_current_user),
    company_id: str = Depends(get_current_user_company)
):
    conn = get_db_connection(company_id)
    try:
        query = """
            SELECT 
                e.id, 
                e.employee_code,
                e.first_name, 
                e.last_name, 
                e.email,
                e.phone,
                e.status,
                p.position_name as position,
                d.department_name as department,
                e.user_id,
                e.account_id,
                e.branch_id,
                e.salary,
                e.housing_allowance,
                e.transport_allowance,
                e.other_allowances,
                e.hourly_cost,
                e.currency,
                e.nationality,
                u.role,
                array_agg(ub.branch_id) filter (where ub.branch_id is not null) as allowed_branches
            FROM employees e
            LEFT JOIN employee_positions p ON e.position_id = p.id
            LEFT JOIN departments d ON e.department_id = d.id
            LEFT JOIN company_users u ON e.user_id = u.id
            LEFT JOIN user_branches ub ON e.user_id = ub.user_id
            WHERE 1=1
        """
        params = {}
        
        # Access Control Logic
        if current_user.role not in ['admin', 'system_admin', 'manager', 'gm']:
            # For regular users, restrict to allowed branches
            if not current_user.allowed_branches:
                # If no branches assigned, they see nothing (or maybe just themselves? strict for now)
                return []
            
            if branch_id:
                # If requesting specific branch, verify access
                if branch_id not in current_user.allowed_branches:
                    raise HTTPException(status_code=403, detail="Unauthorized access to this branch")
                query += " AND e.branch_id = :bid"
                params["bid"] = branch_id
            else:
                # If no specific branch, show employees in ALL allowed branches
                # safe string formatting for int list
                branches_str = ",".join(map(str, current_user.allowed_branches))
                query += f" AND e.branch_id IN ({branches_str})"
        else:
            # Admins/Managers can see all or filter by any branch
            if branch_id:
                query += " AND e.branch_id = :bid"
                params["bid"] = branch_id

        query += """
            GROUP BY e.id, e.employee_code, e.first_name, e.last_name, e.email, e.phone, e.status, e.user_id, e.account_id, e.created_at, p.position_name, d.department_name, e.branch_id, e.salary, e.housing_allowance, e.transport_allowance, e.other_allowances, e.hourly_cost, e.currency, e.nationality, u.role
            ORDER BY e.created_at DESC
        """
        
        result = conn.execute(text(query), params).fetchall()
        
        employees = []
        for row in result:
            employees.append({
                "id": row.id,
                "employee_code": row.employee_code,
                "first_name": row.first_name,
                "last_name": row.last_name,
                "email": row.email,
                "phone": row.phone,
                "status": row.status,
                "position": row.position or "غير محدد",
                "department": row.department or "غير محدد",
                "user_id": row.user_id,
                "account_id": row.account_id,
                "branch_id": row.branch_id,
                "salary": row.salary or 0,
                "housing_allowance": row.housing_allowance or 0,
                "transport_allowance": row.transport_allowance or 0,
                "other_allowances": row.other_allowances or 0,
                "hourly_cost": row.hourly_cost or 0,
                "currency": row.currency,
                "nationality": row.nationality,
                "allowed_branches": row.allowed_branches or [],
                "role": row.role or 'user'
            })
            
        return employees
    finally:
        conn.close()

@router.post("/employees", dependencies=[Depends(require_permission("hr.manage"))])
def create_employee(request: Request, employee: EmployeeCreate, current_user: UserResponse = Depends(get_current_user), company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    trans = conn.begin()
    try:
        # 1. Handle Department & Position (Simple Implementation: Get first or create dummy)
        # For simplicity in this iteration, we might check if they exist or just insert
        dept_id = None
        if employee.department_name:
            # Try find
            res = conn.execute(text("SELECT id FROM departments WHERE department_name = :n"), {"n": employee.department_name}).fetchone()
            if res:
                dept_id = res[0]
            else:
                # Create
                res = conn.execute(text("INSERT INTO departments (department_name) VALUES (:n) RETURNING id"), {"n": employee.department_name}).fetchone()
                dept_id = res[0]

        pos_id = None
        if employee.position_title:
             res = conn.execute(text("SELECT id FROM employee_positions WHERE position_name = :n"), {"n": employee.position_title}).fetchone()
             if res:
                 pos_id = res[0]
             else:
                 res = conn.execute(text("INSERT INTO employee_positions (position_name, department_id) VALUES (:n, :d) RETURNING id"), {"n": employee.position_title, "d": dept_id}).fetchone()
                 pos_id = res[0]


        # 2. Create User (Optional)
        new_user_id = None
        if employee.create_user and employee.username and employee.password:
            # Check if username exists
            exists = conn.execute(text("SELECT 1 FROM company_users WHERE username = :u"), {"u": employee.username}).fetchone()
            if exists:
                raise HTTPException(status_code=400, detail="Username already exists")
            
            hashed = hash_password(employee.password)
            role_key = (employee.role or 'employee').strip().lower()

            # SEC-C2: Whitelist role against DEFAULT_ROLES. Block privileged
            # roles (admin / system_admin / superuser) — those can only be
            # granted from /api/roles (admin.roles) with rank check.
            if role_key not in DEFAULT_ROLES:
                raise HTTPException(
                    status_code=400,
                    detail=f"الدور '{role_key}' غير معروف — استخدم دوراً معرَّفاً في DEFAULT_ROLES",
                )
            privileged = {"admin", "system_admin", "superuser"}
            if role_key in privileged:
                raise HTTPException(
                    status_code=403,
                    detail=(
                        "لا يمكن إسناد دور إداري من واجهة الموارد البشرية — "
                        "استخدم /api/roles المحمي بصلاحية admin.roles."
                    ),
                )

            # Get default permissions for the role
            import json
            perms_def = DEFAULT_ROLES.get(role_key, {})
            perms = perms_def.get("permissions", []) if isinstance(perms_def, dict) else perms_def
            perms_json = json.dumps(perms)
            
            res = conn.execute(text("""
                INSERT INTO company_users (username, password, email, full_name, role, permissions)
                VALUES (:u, :p, :e, :f, :r, :perms) RETURNING id
            """), {
                "u": employee.username,
                "p": hashed,
                "e": employee.email if employee.email else None,
                "f": f"{employee.first_name} {employee.last_name}",
                "r": role_key,
                "perms": perms_json
            }).fetchone()
            new_user_id = res[0]

            # DB-015: Update central user index for fast login
            try:
                from database import get_system_db
                sys_db = get_system_db()
                sys_db.execute(text("""
                    INSERT INTO system_user_index (username, company_id, is_active)
                    VALUES (:username, :company_id, true)
                    ON CONFLICT (username, company_id) DO UPDATE SET is_active = true, updated_at = CURRENT_TIMESTAMP
                """), {"username": employee.username, "company_id": company_id})
                sys_db.commit()
                sys_db.close()
            except Exception:
                pass  # Non-critical

        # 3. Create Ledger Account (Optional)
        new_account_id = None
        if employee.create_ledger:
            # Find "Salaries Payable" or "Employee Payables" parent.
            # For now, we put it under "Current Liabilities" (21) -> Accounts Payable (2101) or create new parent
            # Let's put under "Accounts Payable" (2101) for simplicity or look for a better parent.
            # Better: Create specific parent "Employee Payables" if not exists.
            
            # 1. Find or create parent "Employee Payables" under 21 (Current Liabilities)
            parent_acc = conn.execute(text("SELECT id FROM accounts WHERE name = 'ذمم الموظفين'")).fetchone()
            if not parent_acc:
                # Find ID of 21
                liab_root = conn.execute(text("SELECT id FROM accounts WHERE account_number = '21'")).fetchone()
                if liab_root:
                    parent_acc_res = conn.execute(text("""
                        INSERT INTO accounts (account_number, name, name_en, account_type, parent_id)
                        VALUES ('2105', 'ذمم الموظفين', 'Employees Payable', 'liability', :pid) RETURNING id
                    """), {"pid": liab_root[0]}).fetchone()
                    parent_acc_id = parent_acc_res[0]
                else:
                    parent_acc_id = None # Fallback?
            else:
                parent_acc_id = parent_acc[0]

            if parent_acc_id:
                # Generate unique number
                count = conn.execute(text("SELECT COUNT(*) FROM accounts WHERE parent_id = :pid"), {"pid": parent_acc_id}).scalar()
                acc_num = f"2105{str(count+1).zfill(3)}"
                
                acc_name = f"{employee.first_name} {employee.last_name}"
                res = conn.execute(text("""
                    INSERT INTO accounts (account_number, name, name_en, account_type, parent_id)
                    VALUES (:num, :name, :name, 'liability', :pid) RETURNING id
                """), {
                    "num": acc_num,
                    "name": acc_name,
                    "pid": parent_acc_id
                }).fetchone()
                new_account_id = res[0]

        # 4. Auto-detect currency from branch if not provided
        emp_currency = employee.currency
        if not emp_currency and employee.branch_id:
            branch_row = conn.execute(text("SELECT default_currency FROM branches WHERE id = :bid"), {"bid": employee.branch_id}).fetchone()
            if branch_row and branch_row.default_currency:
                emp_currency = branch_row.default_currency
        if not emp_currency:
            emp_currency = get_base_currency(conn)

        # 5. Create Employee Record
        conn.execute(text("""
            INSERT INTO employees (
                employee_code, first_name, last_name, first_name_en, last_name_en,
                email, phone, department_id, position_id, 
                salary, housing_allowance, transport_allowance, other_allowances, hourly_cost,
                hire_date, user_id, account_id, branch_id, currency, nationality
            ) VALUES (
                :code, :fn, :ln, :fne, :lne,
                :email, :phone, :did, :pid,
                :salary, :housing, :transport, :other, :hc,
                :hire, :uid, :aid, :bid, :currency, :nationality
            )
        """), {
            "code": employee.employee_code if employee.employee_code else None,
            "fn": employee.first_name,
            "ln": employee.last_name,
            "fne": employee.first_name_en,
            "lne": employee.last_name_en,
            "email": employee.email,
            "phone": employee.phone,
            "did": dept_id,
            "pid": pos_id,
            "salary": employee.salary,
            "housing": employee.housing_allowance,
            "transport": employee.transport_allowance,
            "other": employee.other_allowances,
            "hc": employee.hourly_cost,
            "hire": employee.hire_date or date.today(),
            "uid": new_user_id,
            "aid": new_account_id,
            "bid": employee.branch_id,
            "currency": emp_currency,
            "nationality": employee.nationality
        })
        
        # 5. Assign Branches
        if new_user_id and employee.allowed_branch_ids:
             for bid in employee.allowed_branch_ids:
                 conn.execute(text("INSERT INTO user_branches (user_id, branch_id) VALUES (:uid, :bid)"), {"uid": new_user_id, "bid": bid})
        
        trans.commit()

        # AUDIT LOG
        log_activity(
            conn,
            user_id=current_user.get("id") if isinstance(current_user, dict) else current_user.id,
            username=current_user.get("username") if isinstance(current_user, dict) else current_user.username,
            action="hr.employee.create",
            resource_type="employee",
            resource_id=f"{employee.first_name} {employee.last_name}",
            details={"position": employee.position_title, "branch_id": employee.branch_id},
            request=request,
            branch_id=employee.branch_id
        )

        # Notify HR admins about new employee
        try:
            conn.execute(text("""
                INSERT INTO notifications (user_id, type, title, message, link, is_read, created_at)
                SELECT DISTINCT u.id, 'employee', :title, :message, :link, FALSE, NOW()
                FROM company_users u
                WHERE u.is_active = TRUE AND u.role IN ('admin', 'superuser')
                AND u.id != :current_uid
            """), {
                "title": "👤 موظف جديد",
                "message": f"تم إضافة الموظف {employee.first_name} {employee.last_name} — {employee.position_title or ''}",
                "link": "/hr/employees",
                "current_uid": current_user.get('id') if isinstance(current_user, dict) else current_user.id
            })
            conn.commit()
        except Exception:
            pass

        return {"message": "Success"}
        
    except Exception:
        trans.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(400, "invalid_data"))
    finally:
        conn.close()

@router.put("/employees/{employee_id}", dependencies=[Depends(require_permission("hr.manage"))])
def update_employee(
    request: Request,
    employee_id: int, 
    employee: EmployeeUpdate, 
    current_user: UserResponse = Depends(get_current_user),
    company_id: str = Depends(get_current_user_company)
):
    conn = get_db_connection(company_id)
    trans = conn.begin()
    try:
        # Check existence
        existing = conn.execute(text("SELECT user_id FROM employees WHERE id = :id"), {"id": employee_id}).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        user_id = existing[0]

        # Update basic info
        update_fields = []
        params = {"id": employee_id}
        
        if employee.employee_code is not None:
            update_fields.append("employee_code = :code")
            params["code"] = employee.employee_code if employee.employee_code else None
        if employee.first_name:
            update_fields.append("first_name = :fn")
            params["fn"] = employee.first_name
        if employee.last_name:
            update_fields.append("last_name = :ln")
            params["ln"] = employee.last_name
        if employee.email:
            update_fields.append("email = :email")
            params["email"] = employee.email
        if employee.phone:
            update_fields.append("phone = :phone")
            params["phone"] = employee.phone
        if employee.salary:
            update_fields.append("salary = :salary")
            params["salary"] = employee.salary
        if employee.branch_id:
            update_fields.append("branch_id = :bid")
            params["bid"] = employee.branch_id

        # Allowances
        if employee.housing_allowance is not None:
             update_fields.append("housing_allowance = :housing")
             params["housing"] = employee.housing_allowance
        if employee.transport_allowance is not None:
             update_fields.append("transport_allowance = :transport")
             params["transport"] = employee.transport_allowance
        if employee.other_allowances is not None:
             update_fields.append("other_allowances = :other")
             params["other"] = employee.other_allowances
        if employee.hourly_cost is not None:
             update_fields.append("hourly_cost = :hc")
             params["hc"] = employee.hourly_cost

        if employee.currency is not None:
             update_fields.append("currency = :currency")
             params["currency"] = employee.currency
        if employee.nationality is not None:
             update_fields.append("nationality = :nationality")
             params["nationality"] = employee.nationality

        # Update Dept/Pos if changed
        if employee.department_name:
             # Find or create
             res = conn.execute(text("SELECT id FROM departments WHERE department_name = :n"), {"n": employee.department_name}).fetchone()
             if res:
                 dept_id = res[0]
             else:
                 res = conn.execute(text("INSERT INTO departments (department_name) VALUES (:n) RETURNING id"), {"n": employee.department_name}).fetchone()
                 dept_id = res[0]
             update_fields.append("department_id = :did")
             params["did"] = dept_id

        if employee.position_title:
             # We need dept_id (either updated or existing)
             # Simplification: if position exists, use it. If not, create (needs dept).
             # Fetch current dept if not updated
             if "did" not in params:
                 curr_dept = conn.execute(text("SELECT department_id FROM employees WHERE id = :id"), {"id": employee_id}).scalar()
                 dept = curr_dept
             else:
                 dept = params["did"]
                 
             res = conn.execute(text("SELECT id FROM employee_positions WHERE position_name = :n"), {"n": employee.position_title}).fetchone()
             if res:
                 pos_id = res[0]
             else:
                 res = conn.execute(text("INSERT INTO employee_positions (position_name, department_id) VALUES (:n, :d) RETURNING id"), {"n": employee.position_title, "d": dept}).fetchone()
                 pos_id = res[0]
             update_fields.append("position_id = :pid")
             params["pid"] = pos_id

        if update_fields:
            stmt = f"UPDATE employees SET {', '.join(update_fields)} WHERE id = :id"
            conn.execute(text(stmt), params)

        # Update Branches if provided and user exists
        if user_id and employee.allowed_branch_ids is not None:
            # Clear existing
            conn.execute(text("DELETE FROM user_branches WHERE user_id = :uid"), {"uid": user_id})
            # Add new
            for bid in employee.allowed_branch_ids:
                 conn.execute(text("INSERT INTO user_branches (user_id, branch_id) VALUES (:uid, :bid)"), {"uid": user_id, "bid": bid})

        # SEC-C2: Role writes are forbidden from the HR endpoint.
        # Role management lives under /api/roles and is gated by the
        # `admin.roles` permission with a rank check. Any attempt to send
        # `role` via the HR employee update is rejected hard.
        if user_id and getattr(employee, "role", None):
            raise HTTPException(
                status_code=403,
                detail=(
                    "لا يمكن تعديل الدور من خلال واجهة الموارد البشرية — "
                    "استخدم /api/roles المحمي بصلاحية admin.roles."
                ),
            )

        trans.commit()

        # AUDIT LOG
        log_activity(
            conn,
            user_id=current_user.get("id") if isinstance(current_user, dict) else current_user.id,
            username=current_user.get("username") if isinstance(current_user, dict) else current_user.username,
            action="hr.employee.update",
            resource_type="employee",
            resource_id=str(employee_id),
            details={"fields_updated": update_fields},
            request=request,
            branch_id=employee.branch_id
        )

        return {"message": "Updated successfully"}
    except Exception:
        trans.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(400, "invalid_data"))
    finally:
        conn.close()

# --- Payroll Endpoints ---

@router.get("/payroll-periods", response_model=List[PayrollPeriodResponse], dependencies=[Depends(require_permission(["hr.view", "hr.payroll.view"]))])
def list_payroll_periods(company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        query = """
            SELECT p.id, p.name, p.start_date, p.end_date, p.status, p.created_at,
                   COALESCE(SUM(e.net_salary), 0) as total_net
            FROM payroll_periods p
            LEFT JOIN payroll_entries e ON p.id = e.period_id
            GROUP BY p.id
            ORDER BY p.start_date DESC
        """
        result = conn.execute(text(query)).fetchall()
        
        periods = []
        for row in result:
            periods.append({
                "id": row.id,
                "name": row.name,
                "start_date": row.start_date,
                "end_date": row.end_date,
                "status": row.status,
                "total_net": row.total_net,
                "created_at": row.created_at
            })
        return periods
    finally:
        conn.close()

@router.get("/payroll-periods/{period_id}", response_model=PayrollPeriodResponse, dependencies=[Depends(require_permission(["hr.view", "hr.payroll.view"]))])
def get_payroll_period(period_id: int, company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        query = """
            SELECT p.id, p.name, p.start_date, p.end_date, p.status, p.created_at,
                   COALESCE(SUM(e.net_salary), 0) as total_net
            FROM payroll_periods p
            LEFT JOIN payroll_entries e ON p.id = e.period_id
            WHERE p.id = :id
            GROUP BY p.id
        """
        row = conn.execute(text(query), {"id": period_id}).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Payroll period not found")
            
        return {
            "id": row.id,
            "name": row.name,
            "start_date": row.start_date,
            "end_date": row.end_date,
            "status": row.status,
            "total_net": row.total_net,
            "created_at": row.created_at
        }
    finally:
        conn.close()

@router.post("/payroll-periods", dependencies=[Depends(require_permission(["hr.manage", "hr.payroll.manage"]))])
def create_payroll_period(period: PayrollPeriodCreate, current_user: UserResponse = Depends(get_current_user), company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        # Check overlap? For now skip complex validation
        
        conn.execute(text("""
            INSERT INTO payroll_periods (name, start_date, end_date, payment_date, status)
            VALUES (:name, :start, :end, :pay, 'draft')
        """), {
            "name": period.name,
            "start": period.start_date,
            "end": period.end_date,
            "pay": period.payment_date
        })
        conn.commit()
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        username = current_user.get("username", "") if isinstance(current_user, dict) else getattr(current_user, "username", "")
        log_activity(conn, user_id=user_id, username=username, action="payroll_period.create",
                     resource_type="payroll_period", resource_id=0, details={"name": period.name})
        return {"message": "Created successfully"}
    finally:
        conn.close()

@router.get("/payroll-periods/{period_id}/entries", response_model=List[PayrollEntryResponse], dependencies=[Depends(require_permission(["hr.view", "hr.payroll.view"]))])
def get_payroll_entries(period_id: int, branch_id: Optional[int] = None, current_user: UserResponse = Depends(get_current_user), company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        if branch_id:
            branch_id = validate_branch_access(current_user, branch_id)
        query = """
            SELECT pe.id, 
                   e.first_name || ' ' || e.last_name as employee_name,
                   p.position_name as position,
                   pe.basic_salary, pe.housing_allowance, pe.transport_allowance, pe.other_allowances, 
                   pe.deductions, pe.net_salary,
                   pe.currency, pe.exchange_rate, pe.net_salary_base,
                   pe.gosi_employee_share, pe.gosi_employer_share,
                   pe.overtime_amount, pe.violation_deduction, pe.loan_deduction,
                   pe.salary_components_earning, pe.salary_components_deduction
            FROM payroll_entries pe
            JOIN employees e ON pe.employee_id = e.id
            LEFT JOIN employee_positions p ON e.position_id = p.id
            WHERE pe.period_id = :pid
        """
        params = {"pid": period_id}
        
        if branch_id:
            query += " AND e.branch_id = :bid"
            params["bid"] = branch_id
            
        query += " ORDER BY e.first_name"
        
        result = conn.execute(text(query), params).fetchall()
        
        entries = []
        for row in result:
            entries.append({
                "id": row.id,
                "employee_name": row.employee_name,
                "position": row.position,
                "basic_salary": row.basic_salary or 0,
                "housing_allowance": row.housing_allowance or 0,
                "transport_allowance": row.transport_allowance or 0,
                "other_allowances": row.other_allowances or 0,
                "deductions": row.deductions or 0,
                "net_salary": row.net_salary or 0,
                "currency": row.currency,
                "exchange_rate": str(row.exchange_rate) if row.exchange_rate else "1",
                "net_salary_base": str(row.net_salary_base) if row.net_salary_base else None,
                "gosi_employee_share": str(row.gosi_employee_share or 0),
                "gosi_employer_share": str(row.gosi_employer_share or 0),
                "overtime_amount": str(row.overtime_amount or 0),
                "violation_deduction": str(row.violation_deduction or 0),
                "loan_deduction": str(row.loan_deduction or 0),
                "salary_components_earning": str(row.salary_components_earning or 0),
                "salary_components_deduction": str(row.salary_components_deduction or 0)
            })
        return entries
    finally:
        conn.close()

# --- LOAN ENDPOINTS ---

@router.post("/loans", response_model=LoanResponse, dependencies=[Depends(require_permission("hr.loans.manage"))])
def create_loan_request(loan: LoanCreate, current_user: UserResponse = Depends(get_current_user), company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        monthly_installment = str((_dec(loan.amount) / Decimal(str(loan.total_installments))).quantize(_D2, ROUND_HALF_UP))
        
        # Check if employee exists
        emp = conn.execute(text("SELECT id FROM employees WHERE id=:id"), {"id": loan.employee_id}).fetchone()
        if not emp:
             raise HTTPException(status_code=404, detail="Employee not found")

        result = conn.execute(text("""
            INSERT INTO employee_loans (employee_id, amount, total_installments, monthly_installment, start_date, reason, status, branch_id)
            VALUES (:eid, :amt, :inst, :month_inst, :start, :reason, 'pending', :bid)
            RETURNING id, created_at, monthly_installment, paid_amount, status
        """), {
            "eid": loan.employee_id, "amt": loan.amount, "inst": loan.total_installments,
            "month_inst": monthly_installment, "start": loan.start_date, "reason": loan.reason,
            "bid": current_user.get("branch_id") if isinstance(current_user, dict) else (current_user.allowed_branches[0] if current_user.allowed_branches else None)
        }).fetchone()
        
        conn.commit()
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        username = current_user.get("username", "") if isinstance(current_user, dict) else getattr(current_user, "username", "")
        log_activity(conn, user_id=user_id, username=username, action="loan.create",
                     resource_type="employee_loan", resource_id=result.id,
                     details={"employee_id": loan.employee_id, "amount": loan.amount})
        return {**loan.model_dump(), "id": result.id, "monthly_installment": result.monthly_installment, 
                "paid_amount": result.paid_amount, "status": result.status, "created_at": result.created_at}
    except Exception:
        conn.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        conn.close()

@router.get("/loans", dependencies=[Depends(require_permission("hr.loans.view"))])
def list_loans(branch_id: Optional[int] = None, current_user: UserResponse = Depends(get_current_user), company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        if branch_id:
            branch_id = validate_branch_access(current_user, branch_id)
        query = """
            SELECT l.*, e.first_name || ' ' || e.last_name as employee_name 
            FROM employee_loans l
            JOIN employees e ON l.employee_id = e.id
            WHERE 1=1
        """
        params = {}
        if branch_id:
            query += " AND l.branch_id = :bid"
            params["bid"] = branch_id

        query += " ORDER BY l.created_at DESC"
        
        loans = conn.execute(text(query), params).fetchall()
        return [dict(row._mapping) for row in loans]
    except Exception as e:
        logger.error("list_loans error: %s", e)
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        conn.close()

@router.put("/loans/{loan_id}/approve", dependencies=[Depends(require_permission("hr.loans.manage"))])
def approve_loan(loan_id: int, current_user: UserResponse = Depends(get_current_user), company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    trans = conn.begin()
    try:
        loan = conn.execute(text("SELECT * FROM employee_loans WHERE id=:id FOR UPDATE"), {"id": loan_id}).fetchone()
        if not loan or loan.status != 'pending':
            raise HTTPException(status_code=400, detail="Invalid loan status")

        # Enforce fiscal period lock before any GL posting on approval
        check_fiscal_period_open(conn, datetime.now().date())

        # Update Status
        conn.execute(text("UPDATE employee_loans SET status='active', approved_by=:uid WHERE id=:id"), 
                     {"uid": current_user.get("id") if isinstance(current_user, dict) else current_user.id, "id": loan_id})
        
        # Create Journal Entry for Loan Disbursement (Automated)
        acc_loan = get_mapped_account_id(conn, "acc_map_loans_adv")
        acc_cash = get_mapped_account_id(conn, "acc_map_cash_main")
        
        if acc_loan and acc_cash:
            from utils.accounting import generate_sequential_number
            je_num = generate_sequential_number(conn, f"LOAN-{datetime.now().year}", "journal_entries", "entry_number")
            base_currency = get_base_currency(conn)
            user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
            
            gl_create_journal_entry(
                db=conn,
                company_id=company_id,
                date=datetime.now().date(),
                reference=f"LOAN-{loan_id}",
                description=f"صرف سلفة لموظف - رقم {loan_id}",
                status="posted",
                currency=base_currency,
                exchange_rate=1.0,
                lines=[
                    {
                        "account_id": acc_loan, "debit": loan.amount, "credit": 0,
                        "description": "مدين سلفة موظف"
                    },
                    {
                        "account_id": acc_cash, "debit": 0, "credit": loan.amount,
                        "description": "دائن نقدية/صرف سلفة"
                    }
                ],
                user_id=user_id
            )
        
        trans.commit()
        user_id_val = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        username_val = current_user.get("username", "") if isinstance(current_user, dict) else getattr(current_user, "username", "")
        log_activity(conn, user_id=user_id_val, username=username_val, action="loan.approve",
                     resource_type="employee_loan", resource_id=loan_id,
                     details={"amount": str(loan.amount), "employee_id": loan.employee_id})
        return {"status": "active"}
    except Exception:
        trans.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        conn.close()

@router.post("/payroll-periods/{period_id}/generate", dependencies=[Depends(require_permission(["hr.manage", "hr.payroll.manage"]))])
def generate_payroll(period_id: int, current_user: UserResponse = Depends(get_current_user), company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    trans = conn.begin()
    try:
        # Check status
        period = conn.execute(text("SELECT * FROM payroll_periods WHERE id = :id"), {"id": period_id}).fetchone()
        if not period:
            raise HTTPException(status_code=404, detail="Period not found")
        if period.status != 'draft':
             raise HTTPException(status_code=400, detail="Cannot generate payroll for non-draft period")

        # Clear existing
        conn.execute(text("DELETE FROM payroll_entries WHERE period_id = :id"), {"id": period_id})
        
        # Fetch Active Employees (include currency & branch)
        employees = conn.execute(text("""
            SELECT e.id, e.salary, e.housing_allowance, e.transport_allowance, e.other_allowances,
                   e.currency, e.branch_id, COALESCE(b.default_currency, 'SAR') as branch_currency
            FROM employees e
            LEFT JOIN branches b ON e.branch_id = b.id
            WHERE e.status = 'active'
        """)).fetchall()

        # Fetch GOSI settings (active)
        gosi = conn.execute(text("SELECT * FROM gosi_settings WHERE is_active = TRUE ORDER BY id DESC LIMIT 1")).fetchone()
        gosi_emp_pct = _dec(gosi.employee_share_percentage) if gosi else Decimal('9.75')
        gosi_empr_pct = _dec(gosi.employer_share_percentage) if gosi else Decimal('12.00')
        gosi_max_sal = _dec(gosi.max_contributable_salary) if gosi else Decimal('45000')

        base_currency = get_base_currency(conn)

        count = 0
        for emp in employees:
            basic: Decimal = _dec(emp.salary)
            housing: Decimal = _dec(emp.housing_allowance)
            transport: Decimal = _dec(emp.transport_allowance)
            other: Decimal = _dec(emp.other_allowances)

            # === 1. Salary Components (earnings & deductions) ===
            comp_earning = Decimal('0')
            comp_deduction = Decimal('0')
            try:
                components = conn.execute(text("""
                    SELECT esc.amount, sc.component_type, sc.calculation_type, sc.percentage_of, sc.percentage_value
                    FROM employee_salary_components esc
                    JOIN salary_components sc ON esc.component_id = sc.id
                    WHERE esc.employee_id = :eid AND esc.is_active = TRUE AND sc.is_active = TRUE
                """), {"eid": emp.id}).fetchall()

                for comp in components:
                    if comp.calculation_type == 'percentage':
                        base_val = basic if (comp.percentage_of or 'basic') == 'basic' else (basic + housing)  # pyre-ignore
                        amt = (_dec(comp.percentage_value) / Decimal('100') * base_val).quantize(_D2, ROUND_HALF_UP)
                    else:
                        amt = _dec(comp.amount)
                    
                    if comp.component_type == 'earning':
                        comp_earning += amt  # pyre-ignore
                    else:
                        comp_deduction += amt  # pyre-ignore
            except Exception:
                pass  # Table may not exist in older DBs

            # === 2. Approved Overtime (not yet processed) ===
            overtime_amount = Decimal('0')
            try:
                ot_rows = conn.execute(text("""
                    SELECT COALESCE(SUM(calculated_amount), 0) as total
                    FROM overtime_requests
                    WHERE employee_id = :eid AND status = 'approved'
                """), {"eid": emp.id}).fetchone()
                overtime_amount = _dec(ot_rows.total) if ot_rows else Decimal('0')
            except Exception:
                pass

            # === 3. GOSI Deductions ===
            contributable = min(basic + housing, gosi_max_sal)
            gosi_emp_share = (contributable * gosi_emp_pct / Decimal('100')).quantize(_D2, ROUND_HALF_UP)
            gosi_empr_share = (contributable * gosi_empr_pct / Decimal('100')).quantize(_D2, ROUND_HALF_UP)

            # === 4. Violation Deductions (open, deduct_from_salary, not yet deducted) ===
            violation_deduction = Decimal('0')
            try:
                viol = conn.execute(text("""
                    SELECT COALESCE(SUM(penalty_amount), 0) as total
                    FROM employee_violations
                    WHERE employee_id = :eid AND deduct_from_salary = TRUE
                    AND status = 'open' AND (payroll_period_id IS NULL)
                """), {"eid": emp.id}).fetchone()
                violation_deduction = _dec(viol.total) if viol else Decimal('0')
            except Exception:
                pass

            # === 5. Loan Deductions ===
            active_loan = conn.execute(text("SELECT * FROM employee_loans WHERE employee_id=:eid AND status='active' AND paid_amount < amount"), {"eid": emp.id}).fetchone()
            loan_deduction = Decimal('0')
            if active_loan:
                loan_deduction = min(_dec(active_loan.monthly_installment), _dec(active_loan.amount) - _dec(active_loan.paid_amount))

            # === Calculate totals ===
            total_earnings = basic + housing + transport + other + comp_earning + overtime_amount
            total_deductions = comp_deduction + gosi_emp_share + violation_deduction + loan_deduction
            net = (total_earnings - total_deductions).quantize(_D2, ROUND_HALF_UP)
            
            # === Currency & Exchange Rate ===
            emp_currency = getattr(emp, 'currency', None) or getattr(emp, 'branch_currency', None) or base_currency
            # Get exchange rate for this currency
            if emp_currency and emp_currency != base_currency:
                rate_row = conn.execute(text("""
                    SELECT current_rate FROM currencies WHERE code = :code AND is_active = TRUE
                """), {"code": emp_currency}).fetchone()
                exchange_rate = _dec(rate_row.current_rate) if rate_row and rate_row.current_rate else Decimal('1')
            else:
                exchange_rate = Decimal('1')

            net_base = (net * exchange_rate).quantize(_D2, ROUND_HALF_UP)
            
            conn.execute(text("""
                INSERT INTO payroll_entries (
                    period_id, employee_id, basic_salary, housing_allowance, transport_allowance, 
                    other_allowances, salary_components_earning, salary_components_deduction,
                    overtime_amount, gosi_employee_share, gosi_employer_share,
                    violation_deduction, loan_deduction, deductions, net_salary,
                    currency, exchange_rate, net_salary_base
                )
                VALUES (:pid, :eid, :basic, :housing, :transport, :other, :comp_earn, :comp_ded,
                        :overtime, :gosi_emp, :gosi_empr, :viol_ded, :loan_ded, :total_ded, :net,
                        :currency, :exchange_rate, :net_base)
            """), {
                "pid": period_id, "eid": emp.id,
                "basic": str(basic), "housing": str(housing), "transport": str(transport), "other": str(other),
                "comp_earn": str(comp_earning), "comp_ded": str(comp_deduction),
                "overtime": str(overtime_amount), "gosi_emp": str(gosi_emp_share), "gosi_empr": str(gosi_empr_share),
                "viol_ded": str(violation_deduction), "loan_ded": str(loan_deduction),
                "total_ded": str(total_deductions), "net": str(net),
                "currency": emp_currency, "exchange_rate": str(exchange_rate), "net_base": str(net_base)
            })
            count += 1
            
        trans.commit()
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        username = current_user.get("username", "") if isinstance(current_user, dict) else getattr(current_user, "username", "")
        log_activity(conn, user_id=user_id, username=username, action="payroll.generate",
                     resource_type="payroll_period", resource_id=period_id,
                     details={"employee_count": count})
        return {"message": f"Generated payroll for {count} employees"}
    except Exception:
        trans.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        conn.close()

@router.post("/payroll-periods/{period_id}/post", dependencies=[Depends(require_permission(["hr.manage", "hr.payroll.manage"]))])
def post_payroll(period_id: int, current_user: UserResponse = Depends(get_current_user), company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    trans = conn.begin()
    try:
        # 1. Check Status
        period = conn.execute(text("SELECT * FROM payroll_periods WHERE id = :id"), {"id": period_id}).fetchone()
        if not period or period.status != 'draft':
            raise HTTPException(status_code=400, detail="Invalid period status")

        # FISCAL-LOCK: Prevent posting payroll into a closed accounting period
        check_fiscal_period_open(conn, period.end_date)

        base_currency = get_base_currency(conn)

        # 2. Calculate Totals in BASE currency (convert foreign currency amounts)
        totals = conn.execute(text("""
            SELECT 
                SUM(COALESCE(net_salary_base, net_salary * COALESCE(exchange_rate, 1))) as total_net_base,
                SUM((basic_salary + housing_allowance + transport_allowance + other_allowances + salary_components_earning + overtime_amount) * COALESCE(exchange_rate, 1)) as total_gross_base,
                SUM(gosi_employee_share * COALESCE(exchange_rate, 1)) as total_gosi_emp_base,
                SUM(gosi_employer_share * COALESCE(exchange_rate, 1)) as total_gosi_empr_base,
                SUM(overtime_amount * COALESCE(exchange_rate, 1)) as total_overtime_base,
                SUM(violation_deduction * COALESCE(exchange_rate, 1)) as total_violations_base,
                SUM(loan_deduction * COALESCE(exchange_rate, 1)) as total_loans_base,
                SUM(salary_components_deduction * COALESCE(exchange_rate, 1)) as total_comp_ded_base
            FROM payroll_entries WHERE period_id = :id
        """), {"id": period_id}).fetchone()
        
        total_net = _dec(totals.total_net_base)
        totals_gross = _dec(totals.total_gross_base)
        total_gosi_emp = _dec(totals.total_gosi_emp_base)
        total_gosi_empr = _dec(totals.total_gosi_empr_base)
        total_violations = _dec(totals.total_violations_base)
        total_loans = _dec(totals.total_loans_base)
        total_comp_ded = _dec(totals.total_comp_ded_base)
        
        # Get net salary grouped by currency for bank payout lines
        net_by_currency = conn.execute(text("""
            SELECT COALESCE(currency, :base) as pay_currency,
                   SUM(net_salary) as total_net_local,
                   SUM(COALESCE(net_salary_base, net_salary * COALESCE(exchange_rate, 1))) as total_net_base,
                   MAX(COALESCE(exchange_rate, 1)) as rate
            FROM payroll_entries WHERE period_id = :id
            GROUP BY COALESCE(currency, :base)
        """), {"id": period_id, "base": base_currency}).fetchall()
        
        if total_net == Decimal('0'):
            raise HTTPException(status_code=400, detail="No payroll calculated to post")

        # 3. Handle Loan Deductions & Balances
        if total_loans > 0:
            entries_with_loans = conn.execute(text("SELECT employee_id, loan_deduction FROM payroll_entries WHERE period_id = :id AND loan_deduction > 0"), {"id": period_id}).fetchall()
            for entry in entries_with_loans:
                loan = conn.execute(text("SELECT * FROM employee_loans WHERE employee_id=:eid AND status='active' AND paid_amount < amount"), {"eid": entry.employee_id}).fetchone()
                if loan:
                    new_paid = _dec(loan.paid_amount) + _dec(entry.loan_deduction)
                    new_status = 'completed' if new_paid >= _dec(loan.amount) else 'active'
                    conn.execute(text("UPDATE employee_loans SET paid_amount = :paid, status = :status WHERE id=:id"),
                                 {"paid": str(new_paid.quantize(_D2, ROUND_HALF_UP)), "status": new_status, "id": loan.id})

        # 4. Mark processed overtime requests (so they're not counted again)
        try:
            entries_with_overtime = conn.execute(text("SELECT employee_id FROM payroll_entries WHERE period_id = :id AND overtime_amount > 0"), {"id": period_id}).fetchall()
            for entry in entries_with_overtime:
                conn.execute(text("""
                    UPDATE overtime_requests SET status = 'processed'
                    WHERE employee_id = :eid AND status = 'approved'
                """), {"eid": entry.employee_id})
        except Exception:
            pass  # 'processed' status may not exist, safe to skip

        # 5. Mark violations as deducted (link to payroll period)
        try:
            entries_with_violations = conn.execute(text("SELECT employee_id FROM payroll_entries WHERE period_id = :id AND violation_deduction > 0"), {"id": period_id}).fetchall()
            for entry in entries_with_violations:
                conn.execute(text("""
                    UPDATE employee_violations SET payroll_period_id = :pid, status = 'resolved'
                    WHERE employee_id = :eid AND deduct_from_salary = TRUE 
                    AND status = 'open' AND payroll_period_id IS NULL
                """), {"pid": period_id, "eid": entry.employee_id})
        except Exception:
            pass

        # 6. Create Journal Entry
        # Dr Salaries & Wages Expense (Gross: basic + housing + transport + other + components + overtime)
        # Dr GOSI Employer Expense (employer's share)
        #   Cr GOSI Payable (employee share + employer share)
        #   Cr Employee Loans (loan deductions)
        #   Cr Bank/Cash (net salary payout)
        
        from utils.accounting import generate_sequential_number
        je_num = generate_sequential_number(conn, f"PAY-{datetime.now().year}", "journal_entries", "entry_number")
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        branch_id = current_user.get("branch_id") if isinstance(current_user, dict) else (current_user.allowed_branches[0] if current_user.allowed_branches else None)
        
        lines = []

        # Line 1: Dr Salaries Expense (Gross)
        acc_salaries_exp = get_mapped_account_id(conn, "acc_map_salaries_exp")
        if acc_salaries_exp:
            lines.append({
                "account_id": acc_salaries_exp, "debit": totals_gross, "credit": 0,
                "description": 'مصروف رواتب وأجور - Salaries Expense',
                "currency": base_currency, "exchange_rate": 1.0
            })

        # Line 2: Dr GOSI Employer Expense
        if total_gosi_empr > Decimal('0'):
            acc_gosi_exp = get_mapped_account_id(conn, "acc_map_gosi_expense")
            if acc_gosi_exp:
                lines.append({
                    "account_id": acc_gosi_exp, "debit": total_gosi_empr, "credit": 0,
                    "description": 'مصروف تأمينات اجتماعية (حصة صاحب العمل) - GOSI Employer',
                    "currency": base_currency, "exchange_rate": 1.0
                })

        # Line 3: Cr GOSI Payable (employee + employer shares)
        total_gosi = total_gosi_emp + total_gosi_empr
        if total_gosi > Decimal('0'):
            acc_gosi_payable = get_mapped_account_id(conn, "acc_map_gosi_payable")
            if acc_gosi_payable:
                lines.append({
                    "account_id": acc_gosi_payable, "debit": 0, "credit": total_gosi,
                    "description": 'التأمينات المستحقة (حصة موظف + صاحب عمل) - GOSI Payable',
                    "currency": base_currency, "exchange_rate": 1.0
                })

        # Line 4: Cr Employee Loans (Deductions)
        if total_loans > Decimal('0'):
            acc_loans_adv = get_mapped_account_id(conn, "acc_map_loans_adv")
            if acc_loans_adv:
                lines.append({
                    "account_id": acc_loans_adv, "debit": 0, "credit": total_loans,
                    "description": 'استقطاع سلف موظفين - Loan Repayment',
                    "currency": base_currency, "exchange_rate": 1.0
                })

        # Line 5: Cr Violation Deductions
        if total_violations > Decimal('0'):
            acc_violations = get_mapped_account_id(conn, "acc_map_violations") or get_mapped_account_id(conn, "acc_map_other_payable")
            if acc_violations:
                lines.append({
                    "account_id": acc_violations, "debit": 0, "credit": total_violations,
                    "description": 'استقطاع مخالفات موظفين - Violation Deductions',
                    "currency": base_currency, "exchange_rate": 1.0
                })

        # Line 6: Cr Salary Component Deductions (other deductions)
        if total_comp_ded > Decimal('0'):
            acc_comp_ded = get_mapped_account_id(conn, "acc_map_other_deductions") or get_mapped_account_id(conn, "acc_map_other_payable")
            if acc_comp_ded:
                lines.append({
                    "account_id": acc_comp_ded, "debit": 0, "credit": total_comp_ded,
                    "description": 'استقطاعات عناصر الراتب - Salary Component Deductions',
                    "currency": base_currency, "exchange_rate": 1.0
                })

        # Line 7: Cr Bank (Net Payout) — one line per currency for proper tracking
        total_net_all = Decimal('0')
        acc_bank = get_mapped_account_id(conn, "acc_map_bank")
        if acc_bank:
            for cur_row in net_by_currency:
                pay_currency = cur_row.pay_currency
                local_amount = _dec(cur_row.total_net_local)
                base_amount = _dec(cur_row.total_net_base)
                rate = _dec(cur_row.rate)

                if pay_currency == base_currency:
                    desc_text = f'صافي الرواتب المحولة - Net Salary Payment ({pay_currency})'
                else:
                    desc_text = f'صافي الرواتب المحولة - Net Salary Payment ({str(local_amount)} {pay_currency} × {str(rate)})'

                lines.append({
                    "account_id": acc_bank, "debit": 0, "credit": base_amount,
                    "description": desc_text,
                    "currency": pay_currency, "exchange_rate": rate
                })
                total_net_all += base_amount

        if lines:
            gl_create_journal_entry(
                db=conn,
                company_id=company_id,
                date=datetime.now().date(),
                description=f"Payroll for period {period.name}",
                status="posted",
                currency=base_currency,
                exchange_rate=1.0,
                branch_id=branch_id,
                source="payroll",
                source_id=period_id,
                lines=lines,
                user_id=user_id
            )

        # 7a. Update Treasury (bank) balance to keep treasury in sync with GL
        if total_net_all > Decimal('0'):
            try:
                # Find treasury account linked to the GL bank account
                treasury = conn.execute(text("""
                    SELECT id FROM treasury_accounts
                    WHERE gl_account_id = :gl_id AND is_active = TRUE
                    LIMIT 1
                """), {"gl_id": acc_bank}).fetchone() if acc_bank else None
                if treasury:
                    conn.execute(text("""
                        UPDATE treasury_accounts
                        SET current_balance = current_balance - :amt, updated_at = CURRENT_TIMESTAMP
                        WHERE id = :tid
                    """), {"amt": str(total_net_all), "tid": treasury.id})
            except Exception as tres_err:
                logger.warning(f"Treasury balance update for payroll skipped: {tres_err}")

        # 7. Update Period Status
        conn.execute(text("UPDATE payroll_periods SET status='posted' WHERE id=:id"), {"id": period_id})

        # 8. Notify HR admins about payroll posting
        try:
            emp_count = conn.execute(text("SELECT COUNT(*) FROM payroll_entries WHERE period_id = :id"), {"id": period_id}).scalar() or 0
            conn.execute(text("""
                INSERT INTO notifications (user_id, type, title, message, link, is_read, created_at)
                SELECT DISTINCT u.id, 'payroll', :title, :message, :link, FALSE, NOW()
                FROM company_users u
                WHERE u.is_active = TRUE
                AND u.role IN ('admin', 'superuser')
            """), {
                "title": "💰 تم ترحيل الرواتب",
                "message": f"تم ترحيل مسير الرواتب {period.name} بنجاح — {emp_count} موظف — إجمالي {str(total_net)} {base_currency}",
                "link": "/hr/payroll"
            })
        except Exception:
            pass  # Non-blocking

        trans.commit()
        log_activity(conn, user_id=user_id, username=current_user.get("username", "") if isinstance(current_user, dict) else getattr(current_user, "username", ""),
                     action="payroll.post", resource_type="payroll_period", resource_id=period_id,
                     details={"journal_entry": je_num, "total_net": str(total_net)})
        return {"message": "Payroll posted successfully", "journal_entry": je_num}

    except Exception:
        trans.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        conn.close()

# --- Departments ---
@router.get("/departments", response_model=List[DepartmentResponse], dependencies=[Depends(require_permission("hr.view"))])
def list_departments(company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        rows = conn.execute(text("SELECT id, department_name FROM departments ORDER BY department_name")).fetchall()
        return [{"id": r.id, "department_name": r.department_name} for r in rows]
    finally:
        conn.close()

@router.post("/departments", dependencies=[Depends(require_permission("hr.manage"))])
def create_department(dept: DepartmentCreate, current_user: UserResponse = Depends(get_current_user), company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    trans = conn.begin()
    try:
        conn.execute(text("INSERT INTO departments (department_name) VALUES (:name)"), {"name": dept.department_name})
        trans.commit()
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        username = current_user.get("username", "") if isinstance(current_user, dict) else getattr(current_user, "username", "")
        log_activity(conn, user_id=user_id, username=username, action="department.create",
                     resource_type="department", resource_id=0, details={"name": dept.department_name})
        return {"message": "Department created"}
    except Exception:
        trans.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        conn.close()

@router.delete("/departments/{dept_id}", dependencies=[Depends(require_permission("hr.manage"))])
def delete_department(dept_id: int, current_user: UserResponse = Depends(get_current_user), company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    trans = conn.begin()
    try:
        # Check usage
        count = conn.execute(text("SELECT COUNT(*) FROM employees WHERE department_id = :id"), {"id": dept_id}).scalar()
        if count > 0:
            raise HTTPException(status_code=400, detail="Cannot delete department. It is assigned to employees.")

        conn.execute(text("DELETE FROM departments WHERE id = :id"), {"id": dept_id})
        trans.commit()
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        username = current_user.get("username", "") if isinstance(current_user, dict) else getattr(current_user, "username", "")
        log_activity(conn, user_id=user_id, username=username, action="department.delete",
                     resource_type="department", resource_id=dept_id, details={})
        return {"message": "Department deleted"}
    except HTTPException:
        raise
    except Exception:
        trans.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        conn.close()

# --- Positions ---
@router.get("/positions", response_model=List[PositionResponse], dependencies=[Depends(require_permission("hr.view"))])
def list_positions(company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        query = """
            SELECT p.id, p.position_name, p.department_id, d.department_name
            FROM employee_positions p
            LEFT JOIN departments d ON p.department_id = d.id
            ORDER BY p.position_name
        """
        rows = conn.execute(text(query)).fetchall()
        return [
            {
                "id": r.id, 
                "position_name": r.position_name, 
                "department_id": r.department_id,
                "department_name": r.department_name
            } 
            for r in rows
        ]
    finally:
        conn.close()

@router.post("/positions", dependencies=[Depends(require_permission("hr.manage"))])
def create_position(pos: PositionCreate, current_user: UserResponse = Depends(get_current_user), company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    trans = conn.begin()
    try:
        conn.execute(text("INSERT INTO employee_positions (position_name, department_id) VALUES (:name, :did)"), 
                     {"name": pos.position_name, "did": pos.department_id})
        trans.commit()
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        username = current_user.get("username", "") if isinstance(current_user, dict) else getattr(current_user, "username", "")
        log_activity(conn, user_id=user_id, username=username, action="position.create",
                     resource_type="position", resource_id=0, details={"name": pos.position_name})
        return {"message": "Position created"}
    except Exception:
        trans.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        conn.close()

@router.delete("/positions/{pos_id}", dependencies=[Depends(require_permission("hr.manage"))])
def delete_position(pos_id: int, current_user: UserResponse = Depends(get_current_user), company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    trans = conn.begin()
    try:
        # Check usage
        count = conn.execute(text("SELECT COUNT(*) FROM employees WHERE position_id = :id"), {"id": pos_id}).scalar()
        if count > 0:
            raise HTTPException(status_code=400, detail="Cannot delete position. It is assigned to employees.")

        conn.execute(text("DELETE FROM employee_positions WHERE id = :id"), {"id": pos_id})
        trans.commit()
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        username = current_user.get("username", "") if isinstance(current_user, dict) else getattr(current_user, "username", "")
        log_activity(conn, user_id=user_id, username=username, action="position.delete",
                     resource_type="position", resource_id=pos_id, details={})
        return {"message": "Position deleted"}
    except HTTPException:
        raise
    except Exception:
        trans.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        conn.close()

# --- ATTENDANCE ENDPOINTS ---

def get_current_employee(
    current_user: UserResponse = Depends(get_current_user),
    company_id: str = Depends(get_current_user_company)
):
    conn = get_db_connection(company_id)
    try:
        emp = conn.execute(
            text("SELECT id, first_name, last_name, status FROM employees WHERE user_id = :uid"), 
            {"uid": current_user.get("id") if isinstance(current_user, dict) else current_user.id}
        ).fetchone()
        
        if not emp:
            raise HTTPException(status_code=404, detail="السجلات الوظيفية غير مرتبطة بهذا المستخدم")
        
        # Access by index since it's a Row object/tuple
        if emp[3] != 'active': # status
             raise HTTPException(status_code=400, detail="الموظف غير نشط")
             
        return emp
    finally:
        conn.close()

@router.post("/attendance/check-in", response_model=AttendanceResponse, dependencies=[Depends(require_permission(["hr.attendance.view", "hr.attendance.manage"]))])
def check_in(current_user: UserResponse = Depends(get_current_user), company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    trans = conn.begin()
    try:
        # Get Employee ID
        emp_res = conn.execute(
            text("SELECT id FROM employees WHERE user_id = :uid"), 
            {"uid": current_user.get("id") if isinstance(current_user, dict) else current_user.id}
        ).fetchone()
        
        if not emp_res:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        employee_id = emp_res[0]
        today = date.today()
        
        # Check if already checked in today (open session without checkout)
        existing = conn.execute(
            text("SELECT id, check_in, check_out FROM attendance WHERE employee_id = :eid AND date = :date ORDER BY id DESC LIMIT 1"),
            {"eid": employee_id, "date": today}
        ).fetchone()
        
        if existing and existing[1] and not existing[2]:
            raise HTTPException(status_code=400, detail="You are already checked in")
        
        # Prevent excessive check-ins on same day (max 3 sessions)
        day_count = conn.execute(
            text("SELECT COUNT(*) FROM attendance WHERE employee_id = :eid AND date = :date"),
            {"eid": employee_id, "date": today}
        ).scalar() or 0
        
        if day_count >= 3:
            raise HTTPException(status_code=400, detail="تم تجاوز الحد الأقصى لتسجيلات الحضور لهذا اليوم (3 مرات)")
            
        # Create new check-in
        new_record = conn.execute(
            text("""
                INSERT INTO attendance (employee_id, date, check_in, status)
                VALUES (:eid, :date, CURRENT_TIMESTAMP, 'present')
                RETURNING id, employee_id, date, check_in, check_out, status, notes
            """),
            {"eid": employee_id, "date": today}
        ).fetchone()
        
        trans.commit()
        
        return AttendanceResponse(
            id=new_record[0],
            employee_id=new_record[1],
            date=new_record[2],
            check_in=new_record[3],
            check_out=new_record[4],
            status=new_record[5],
            notes=new_record[6]
        )
        
    except HTTPException:
        raise
    except Exception:
        trans.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        conn.close()

@router.post("/attendance/check-out", response_model=AttendanceResponse, dependencies=[Depends(require_permission(["hr.attendance.view", "hr.attendance.manage"]))])
def check_out(
    current_user: UserResponse = Depends(get_current_user),
    company_id: str = Depends(get_current_user_company)
):
    conn = get_db_connection(company_id)
    trans = conn.begin()
    try:
        # Get Employee ID
        emp_res = conn.execute(
            text("SELECT id FROM employees WHERE user_id = :uid"), 
            {"uid": current_user.get("id") if isinstance(current_user, dict) else current_user.id}
        ).fetchone()
        
        if not emp_res:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        employee_id = emp_res[0]
        today = date.today()
        
        # Find active check-in
        existing = conn.execute(
            text("SELECT id FROM attendance WHERE employee_id = :eid AND date = :date AND check_out IS NULL ORDER BY id DESC LIMIT 1"),
            {"eid": employee_id, "date": today}
        ).fetchone()
        
        if not existing:
            raise HTTPException(status_code=400, detail="No active check-in found for today")
            
        # Update check-out
        updated_record = conn.execute(
            text("""
                UPDATE attendance 
                SET check_out = CURRENT_TIMESTAMP 
                WHERE id = :id
                RETURNING id, employee_id, date, check_in, check_out, status, notes
            """),
            {"id": existing[0]}
        ).fetchone()
        
        trans.commit()
        
        return AttendanceResponse(
            id=updated_record[0],
            employee_id=updated_record[1],
            date=updated_record[2],
            check_in=updated_record[3],
            check_out=updated_record[4],
            status=updated_record[5],
            notes=updated_record[6]
        )
        
    except HTTPException:
        raise
    except Exception:
        trans.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        conn.close()

@router.get("/attendance/status", dependencies=[Depends(require_permission("hr.attendance.view"))])
def get_attendance_status(
    current_user: UserResponse = Depends(get_current_user),
    company_id: str = Depends(get_current_user_company)
):
    conn = get_db_connection(company_id)
    try:
        emp_res = conn.execute(
            text("SELECT id FROM employees WHERE user_id = :uid"), 
            {"uid": current_user.get("id") if isinstance(current_user, dict) else current_user.id}
        ).fetchone()
        
        if not emp_res:
            return {"status": "not_linked", "message": "User not linked to employee"}
            
        employee_id = emp_res[0]
        today = date.today()
        
        # Check today's records
        record = conn.execute(
            text("""
                SELECT id, check_in, check_out 
                FROM attendance 
                WHERE employee_id = :eid AND date = :date 
                ORDER BY id DESC LIMIT 1
            """),
            {"eid": employee_id, "date": today}
        ).fetchone()
        
        if not record:
            return {"status": "checked_out", "last_action": None} # Never checked in today
            
        if record[1] and not record[2]:
            return {
                "status": "checked_in", 
                "check_in_time": record[1],
                "record_id": record[0]
            }
        else:
            return {
                "status": "checked_out", 
                "check_in_time": record[1],
                "check_out_time": record[2],
                "record_id": record[0]
            }

    finally:
        conn.close()

@router.get("/attendance/history", dependencies=[Depends(require_permission("hr.attendance.view"))])
def get_attendance_history(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: UserResponse = Depends(get_current_user),
    company_id: str = Depends(get_current_user_company)
):
    conn = get_db_connection(company_id)
    try:
        emp_res = conn.execute(
            text("SELECT id FROM employees WHERE user_id = :uid"), 
            {"uid": current_user.get("id") if isinstance(current_user, dict) else current_user.id}
        ).fetchone()
        
        if not emp_res:
            return []
            
        employee_id = emp_res[0]
        
        query = "SELECT id, employee_id, date, check_in, check_out, status, notes FROM attendance WHERE employee_id = :eid"
        params = {"eid": employee_id}
        
        if start_date:
            query += " AND date >= :start"
            params["start"] = start_date
        if end_date:
            query += " AND date <= :end"
            params["end"] = end_date
            
        query += " ORDER BY date DESC, check_in DESC"
        
        records = conn.execute(text(query), params).fetchall()
        
        return [
            AttendanceResponse(
                id=r[0], employee_id=r[1], date=r[2], 
                check_in=r[3], check_out=r[4], status=r[5], notes=r[6]
            ) for r in records
        ]
        
    finally:
        conn.close()

# --- LEAVE REQUESTS ---

@router.post("/leaves", response_model=LeaveRequestResponse, dependencies=[Depends(require_permission("hr.leaves.manage"))])
def create_leave_request(request: LeaveRequestCreate, current_user: UserResponse = Depends(get_current_user), company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        # Determine employee ID
        employee_id = request.employee_id
        if not employee_id:
            # Try to find employee linked to this user
            emp_res = conn.execute(text("SELECT id FROM employees WHERE user_id = :uid"), {"uid": current_user.get("id") if isinstance(current_user, dict) else current_user.id}).fetchone()
            if not emp_res:
                raise HTTPException(status_code=400, detail="User is not linked to an employee")
            employee_id = emp_res[0]
        else:
            # If sending explicit employee_id, must have manage permission
            if not has_permission(current_user, "hr.leaves.manage"):
                 # Check if the employee_id matches self
                 emp_res = conn.execute(text("SELECT id FROM employees WHERE user_id = :uid"), {"uid": current_user.get("id") if isinstance(current_user, dict) else current_user.id}).fetchone()
                 if not emp_res or emp_res[0] != employee_id:
                     raise HTTPException(status_code=403, detail="Not authorized to request leave for others")

        # Validate dates
        if request.start_date > request.end_date:
            raise HTTPException(status_code=400, detail="تاريخ البداية لا يمكن أن يكون بعد تاريخ النهاية")
        
        leave_days = (request.end_date - request.start_date).days + 1
        
        # Check for overlapping leave requests
        overlap = conn.execute(text("""
            SELECT id FROM leave_requests 
            WHERE employee_id = :eid 
            AND status IN ('pending', 'approved')
            AND (
                (start_date <= :end AND end_date >= :start)
            )
        """), {"eid": employee_id, "start": request.start_date, "end": request.end_date}).fetchone()
        
        if overlap:
            raise HTTPException(status_code=400, detail="يوجد طلب إجازة متداخل مع هذه الفترة")
        
        # Check leave balance for annual leave type
        if request.leave_type in ('annual', 'سنوية'):
            # Get total approved leave days in current year
            year_start = date(date.today().year, 1, 1)
            used_days = conn.execute(text("""
                SELECT COALESCE(SUM(end_date - start_date + 1), 0) 
                FROM leave_requests 
                WHERE employee_id = :eid 
                AND status = 'approved'
                AND leave_type IN ('annual', 'سنوية')
                AND start_date >= :year_start
            """), {"eid": employee_id, "year_start": year_start}).scalar() or 0
            
            # Get annual leave allowance (default 21 days per Saudi labor law)
            leave_allowance = conn.execute(text("""
                SELECT COALESCE(annual_leave_days, 21) FROM employees WHERE id = :eid
            """), {"eid": employee_id}).scalar() or 21
            
            remaining_balance = int(leave_allowance) - int(used_days)
            if leave_days > remaining_balance:
                raise HTTPException(
                    status_code=400, 
                    detail=f"رصيد الإجازات السنوية غير كافٍ. المتبقي: {remaining_balance} يوم، المطلوب: {leave_days} يوم"
                )

        # Create - CORRECT TABLE NAME 'leave_requests'
        result = conn.execute(text("""
            INSERT INTO leave_requests (employee_id, leave_type, start_date, end_date, reason, status)
            VALUES (:eid, :type, :start, :end, :reason, 'pending')
            RETURNING id, created_at, status
        """), {
            "eid": employee_id,
            "type": request.leave_type,
            "start": request.start_date,
            "end": request.end_date,
            "reason": request.reason
        }).fetchone()
        
        conn.commit()
        
        # Submit for approval workflow if exists
        approval_info = None
        try:
            from utils.approval_utils import try_submit_for_approval
            user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
            approval_info = try_submit_for_approval(
                conn,
                document_type="leave_request",
                document_id=result.id,
                document_number=f"LR-{result.id}",
                amount=str(leave_days),
                submitted_by=user_id,
                description=f"طلب إجازة {request.leave_type} - {leave_days} يوم",
                link="/hr/leaves"
            )
            if approval_info:
                conn.commit()
        except Exception:
            pass  # Non-blocking
        
        # Notify HR admins/superusers about new leave request
        try:
            emp_name_row = conn.execute(text("""
                SELECT CONCAT(first_name, ' ', last_name) as name FROM employees WHERE id = :eid
            """), {"eid": employee_id}).fetchone()
            emp_name = emp_name_row.name if emp_name_row else f"موظف #{employee_id}"
            conn.execute(text("""
                INSERT INTO notifications (user_id, type, title, message, link, is_read, created_at)
                SELECT DISTINCT u.id, 'leave_request', :title, :message, :link, FALSE, NOW()
                FROM company_users u
                WHERE u.is_active = TRUE
                AND u.role IN ('admin', 'superuser')
            """), {
                "title": "🌴 طلب إجازة جديد",
                "message": f"{emp_name} طلب إجازة {request.leave_type} من {request.start_date} إلى {request.end_date} ({leave_days} يوم)",
                "link": "/hr/leaves"
            })
            conn.commit()
        except Exception:
            pass  # Non-blocking

        response = {
            "id": result.id,
            "employee_id": employee_id,
            "leave_type": request.leave_type,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "reason": request.reason,
            "status": result.status,
            "created_at": result.created_at
        }
        if approval_info:
            response["approval"] = approval_info
        return response
    except Exception as e:
        conn.rollback()
        logger.error("Error creating leave: %s", e)
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        conn.close()

@router.get("/leaves", response_model=List[LeaveRequestResponse], dependencies=[Depends(require_permission("hr.view"))])
def list_leave_requests(branch_id: Optional[int] = None, current_user: UserResponse = Depends(get_current_user), company_id: str = Depends(get_current_user_company)):
    # Basic view permission required
    if not has_permission(current_user, "hr.leaves.view"):
        pass 
        # Actually, let's enforce view permission to be safe, but typically all employees should have "hr.leaves.view" or "hr.view".
        # If strict: raise HTTPException(status_code=403, detail="Not authorized")
    
    conn = get_db_connection(company_id)
    try:
        if branch_id:
            branch_id = validate_branch_access(current_user, branch_id)
        # Check if manager
        is_manager = has_permission(current_user, "hr.leaves.manage")
        
        query = """
            SELECT l.*, e.first_name || ' ' || e.last_name as employee_name 
            FROM leave_requests l
            JOIN employees e ON l.employee_id = e.id
        """
        params = {}
        
        if not is_manager:
            # Filter by self
            emp_res = conn.execute(text("SELECT id FROM employees WHERE user_id = :uid"), {"uid": current_user.get("id") if isinstance(current_user, dict) else current_user.id}).fetchone()
            if not emp_res:
                return [] # No employee record
            query += " WHERE l.employee_id = :eid"
            params["eid"] = emp_res[0]
        else:
             # Manager view - filter by branch if provided
             where_clauses = []
             if branch_id:
                 where_clauses.append("e.branch_id = :bid")
                 params["bid"] = branch_id
             
             if where_clauses:
                 query += " WHERE " + " AND ".join(where_clauses)
            
        query += " ORDER BY l.created_at DESC"
        
        records = conn.execute(text(query), params).fetchall()
        return [dict(row._mapping) for row in records]
    finally:
        conn.close()

@router.put("/leaves/{leave_id}/status", dependencies=[Depends(require_permission("hr.leaves.manage"))])
def update_leave_status(leave_id: int, status_in: str, current_user: UserResponse = Depends(get_current_user), company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        conn.execute(text("""
            UPDATE leave_requests 
            SET status = :status, approved_by = :uid, updated_at = NOW()
            WHERE id = :id
        """), {"status": status_in, "uid": current_user.get("id") if isinstance(current_user, dict) else current_user.id, "id": leave_id})
        conn.commit()

        # Notify the employee about their leave update
        try:
            emp_info = conn.execute(text("""
                SELECT e.user_id, CONCAT(e.first_name, ' ', e.last_name) as name,
                       l.leave_type, l.start_date, l.end_date
                FROM employees e
                JOIN leave_requests l ON l.employee_id = e.id
                WHERE l.id = :lid
            """), {"lid": leave_id}).fetchone()
            if emp_info and emp_info.user_id:
                icon = "✅" if status_in == 'approved' else "❌"
                status_ar = "اعتُمد" if status_in == 'approved' else "رُفض"
                conn.execute(text("""
                    INSERT INTO notifications (user_id, type, title, message, link, is_read, created_at)
                    VALUES (:uid, 'leave_status', :title, :message, '/hr/leaves', FALSE, NOW())
                """), {
                    "uid": emp_info.user_id,
                    "title": f"{icon} طلب إجازتك {status_ar}",
                    "message": f"تم {status_ar} طلب إجازتك ({emp_info.leave_type}) من {emp_info.start_date} إلى {emp_info.end_date}"
                })
                conn.commit()
        except Exception:
            pass  # Non-blocking

        # Audit log
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        username = current_user.get("username", "") if isinstance(current_user, dict) else getattr(current_user, "username", "")
        log_activity(conn, user_id=user_id, username=username, action="leave.status_update",
                     resource_type="leave_request", resource_id=leave_id,
                     details={"new_status": status_in})

        return {"message": "Status updated"}
    finally:
        conn.close()


# --- End of Service Calculation ---

@router.post("/end-of-service/calculate", dependencies=[Depends(require_permission("hr.manage"))])
def calculate_end_of_service(
    data: EndOfServiceRequest,
    current_user: UserResponse = Depends(get_current_user),
    company_id: str = Depends(get_current_user_company)
):
    """حساب مكافأة نهاية الخدمة وفقاً لنظام العمل السعودي"""
    conn = get_db_connection(company_id)
    try:
        # Get employee details
        emp = conn.execute(text("""
            SELECT id, CONCAT(first_name, ' ', last_name) as employee_name, 
                   hire_date, salary as basic_salary, 
                   COALESCE(housing_allowance, 0) as housing_allowance,
                   COALESCE(transport_allowance, 0) as transport_allowance
            FROM employees WHERE id = :eid
        """), {"eid": data.employee_id}).fetchone()
        
        if not emp:
            raise HTTPException(**http_error(404, "employee_not_found"))
        
        termination_date = data.termination_date or date.today()
        join_date = emp.hire_date
        
        if not join_date:
            raise HTTPException(status_code=400, detail="تاريخ التعيين غير محدد للموظف")
        
        # Calculate service years
        from dateutil.relativedelta import relativedelta
        delta = relativedelta(termination_date, join_date)
        total_years = _dec(delta.years) + (_dec(delta.months) / Decimal('12')) + (_dec(delta.days) / Decimal('365.25'))
        
        if total_years < Decimal('0'):
            raise HTTPException(status_code=400, detail="تاريخ الإنهاء قبل تاريخ التعيين")
        
        # Total salary (basic + housing + transport) used as base
        base_salary = _dec(emp.basic_salary)
        total_salary = base_salary + _dec(emp.housing_allowance) + _dec(emp.transport_allowance)
        
        # Calculate EOS using shared helper (Saudi Labor Law Art. 84/85)
        from utils.hr_helpers import calculate_eos_gratuity
        eos = calculate_eos_gratuity(total_salary, total_years, data.termination_reason)
        
        gratuity = eos["full_gratuity"]
        resignation_factor = eos["resignation_factor"]
        final_gratuity = eos["final_gratuity"]
        
        # Calculate unpaid leave deduction days (if any)
        unpaid_days = conn.execute(text("""
            SELECT COALESCE(SUM(
                CASE WHEN leave_type = 'unpaid' AND status = 'approved'
                THEN (end_date - start_date + 1) ELSE 0 END
            ), 0) FROM leave_requests WHERE employee_id = :eid
        """), {"eid": data.employee_id}).scalar() or 0
        
        return {
            "employee_id": data.employee_id,
            "employee_name": emp.employee_name,
            "join_date": str(join_date),
            "termination_date": str(termination_date),
            "termination_reason": data.termination_reason,
            "service_years": str(total_years.quantize(_D2, ROUND_HALF_UP)),
            "service_years_display": f"{delta.years} سنة و {delta.months} شهر و {delta.days} يوم",
            "base_salary": str(base_salary),
            "total_salary_used": str(total_salary),
            "full_gratuity": str(gratuity),
            "resignation_factor": str(resignation_factor),
            "final_gratuity": str(final_gratuity),
            "unpaid_leave_days": int(unpaid_days),
            "notes": "الحساب وفقاً لنظام العمل السعودي - المادة 84 و 85"
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        conn.close()


# =====================================================
# 8.15 HR IMPROVEMENTS
# =====================================================

# ---------- HR-005: Payslip View / Print ----------
# NOTE: Payslip endpoints consolidated below in "Phase 8.15" section


# ============================================================
# Phase 8.15 - Payslips, Recruitment, Leave Balance
# ============================================================
import calendar as cal_module

# --- Payslips ---

@router.get("/payslips", dependencies=[Depends(require_permission("hr.view"))])
def list_all_payslips(branch_id: Optional[int] = None, current_user: UserResponse = Depends(get_current_user), company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        q = """
            SELECT pe.id, pe.employee_id, pe.period_id,
                   e.first_name || ' ' || e.last_name as employee_name,
                   pe.basic_salary,
                   COALESCE(pe.housing_allowance,0)+COALESCE(pe.transport_allowance,0)+COALESCE(pe.other_allowances,0)+COALESCE(pe.salary_components_earning,0)+COALESCE(pe.overtime_amount,0) as total_allowances,
                   COALESCE(pe.deductions,0) as total_deductions,
                   pe.net_salary as net_pay,
                   pp.status,
                   EXTRACT(MONTH FROM pp.start_date)::int as month,
                   EXTRACT(YEAR FROM pp.start_date)::int as year
            FROM payroll_entries pe
            JOIN employees e ON pe.employee_id = e.id
            JOIN payroll_periods pp ON pe.period_id = pp.id
            WHERE 1=1
        """
        params = {}
        # Branch access control
        if current_user.role not in ['admin', 'system_admin', 'manager', 'gm']:
            if not current_user.allowed_branches:
                return []
            if branch_id:
                if branch_id not in current_user.allowed_branches:
                    raise HTTPException(status_code=403, detail="Unauthorized access to this branch")
                q += " AND e.branch_id = :bid"
                params["bid"] = branch_id
            else:
                branches_str = ",".join(map(str, current_user.allowed_branches))
                q += f" AND e.branch_id IN ({branches_str})"
        else:
            if branch_id:
                q += " AND e.branch_id = :bid"
                params["bid"] = branch_id
        q += " ORDER BY pp.start_date DESC, e.first_name"
        result = conn.execute(text(q), params).fetchall()
        return [dict(row._mapping) for row in result]
    finally:
        conn.close()


@router.get("/employees/{emp_id}/payslips", dependencies=[Depends(require_permission("hr.view"))])
def get_employee_payslips_route(emp_id: int, company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        result = conn.execute(text("""
            SELECT pe.id, pe.employee_id,
                   e.first_name || ' ' || e.last_name as employee_name,
                   pe.basic_salary,
                   COALESCE(pe.housing_allowance,0)+COALESCE(pe.transport_allowance,0)+COALESCE(pe.other_allowances,0) as total_allowances,
                   COALESCE(pe.deductions,0) as total_deductions,
                   pe.net_salary as net_pay,
                   pp.status,
                   EXTRACT(MONTH FROM pp.start_date)::int as month,
                   EXTRACT(YEAR FROM pp.start_date)::int as year
            FROM payroll_entries pe
            JOIN employees e ON pe.employee_id = e.id
            JOIN payroll_periods pp ON pe.period_id = pp.id
            WHERE pe.employee_id = :eid
            ORDER BY pp.start_date DESC
        """), {"eid": emp_id}).fetchall()
        return [dict(row._mapping) for row in result]
    finally:
        conn.close()


@router.get("/payslips/{entry_id}", dependencies=[Depends(require_permission("hr.view"))])
def get_payslip_detail(entry_id: int, company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        row = conn.execute(text("""
            SELECT pe.*, e.first_name || ' ' || e.last_name as employee_name,
                   pp.status, pp.name as period_name,
                   EXTRACT(MONTH FROM pp.start_date)::int as month,
                   EXTRACT(YEAR FROM pp.start_date)::int as year
            FROM payroll_entries pe
            JOIN employees e ON pe.employee_id = e.id
            JOIN payroll_periods pp ON pe.period_id = pp.id
            WHERE pe.id = :id
        """), {"id": entry_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Payslip not found")
        return dict(row._mapping)
    finally:
        conn.close()


class PayslipGenerateRequest(BaseModel):
    employee_id: int
    month: int
    year: int


@router.post("/payslips/generate", dependencies=[Depends(require_permission("hr.manage"))])
def generate_single_payslip(data: PayslipGenerateRequest, company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        last_day = cal_module.monthrange(data.year, data.month)[1]
        start_date = f"{data.year}-{data.month:02d}-01"
        end_date = f"{data.year}-{data.month:02d}-{last_day}"
        period_name = f"Payroll {data.month}/{data.year}"

        period = conn.execute(text("""
            SELECT id FROM payroll_periods
            WHERE EXTRACT(MONTH FROM start_date)=:m AND EXTRACT(YEAR FROM start_date)=:y
        """), {"m": data.month, "y": data.year}).fetchone()

        if not period:
            res = conn.execute(text("""
                INSERT INTO payroll_periods (name,start_date,end_date,payment_date,status)
                VALUES (:name,:start,:end,:end,'draft') RETURNING id
            """), {"name": period_name, "start": start_date, "end": end_date})
            period_id = res.fetchone()[0]
        else:
            period_id = period.id

        emp = conn.execute(text("""
            SELECT e.id, e.salary,
                   COALESCE(ss.basic_salary, e.salary, 0) as basic_salary,
                   COALESCE(ss.housing_allowance, 0) as housing_allowance,
                   COALESCE(ss.transport_allowance, 0) as transport_allowance,
                   COALESCE(ss.other_allowances, 0) as other_allowances
            FROM employees e
            LEFT JOIN salary_structures ss ON e.salary_structure_id = ss.id
            WHERE e.id = :id
        """), {"id": data.employee_id}).fetchone()

        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")

        existing = conn.execute(text(
            "SELECT id FROM payroll_entries WHERE period_id=:pid AND employee_id=:eid"
        ), {"pid": period_id, "eid": data.employee_id}).fetchone()

        if existing:
            raise HTTPException(status_code=400, detail="Payslip already exists for this period")

        basic = _dec(emp.basic_salary)
        housing = _dec(emp.housing_allowance)
        transport = _dec(emp.transport_allowance)
        other = _dec(emp.other_allowances)
        gross = basic + housing + transport + other

        # Calculate GOSI deductions
        gosi_settings = conn.execute(text("SELECT * FROM gosi_settings LIMIT 1")).fetchone()
        gosi_emp = Decimal('0')
        gosi_empr = Decimal('0')
        if gosi_settings:
            gosi_max_sal = _dec(gosi_settings.max_contributable_salary) if gosi_settings.max_contributable_salary else Decimal('45000')
            emp_rate = _dec(gosi_settings.employee_percentage) if gosi_settings.employee_percentage else Decimal('9.75')
            empr_rate = _dec(gosi_settings.employer_percentage) if gosi_settings.employer_percentage else Decimal('11.75')
            contributable = min(basic + housing, gosi_max_sal)
            gosi_emp = (contributable * emp_rate / Decimal('100')).quantize(_D2, ROUND_HALF_UP)
            gosi_empr = (contributable * empr_rate / Decimal('100')).quantize(_D2, ROUND_HALF_UP)

        # Calculate violation deductions for the month
        violation_total = conn.execute(text("""
            SELECT COALESCE(SUM(deduction_amount), 0) FROM employee_violations
            WHERE employee_id = :eid AND violation_date BETWEEN :start AND :end AND status = 'approved'
        """), {"eid": data.employee_id, "start": start_date, "end": end_date}).scalar() or 0
        violation_deduction = _dec(violation_total)

        # Calculate loan deductions
        loan_deduction = Decimal('0')
        active_loan = conn.execute(text("""
            SELECT monthly_deduction FROM employee_loans
            WHERE employee_id = :eid AND status = 'active' AND paid_amount < amount
            LIMIT 1
        """), {"eid": data.employee_id}).fetchone()
        if active_loan:
            loan_deduction = _dec(active_loan.monthly_deduction)

        # Calculate salary component earnings/deductions
        comp_earning = Decimal('0')
        comp_deduction = Decimal('0')
        components = conn.execute(text("""
            SELECT sc.amount, sc.component_type
            FROM salary_components sc
            WHERE sc.employee_id = :eid AND sc.is_active = TRUE
        """), {"eid": data.employee_id}).fetchall()
        for comp in components:
            if comp.component_type == 'earning':
                comp_earning += _dec(comp.amount)  # pyre-ignore
            elif comp.component_type == 'deduction':
                comp_deduction += _dec(comp.amount)  # pyre-ignore

        total_deductions = gosi_emp + violation_deduction + loan_deduction + comp_deduction  # pyre-ignore
        net = gross + comp_earning - total_deductions  # pyre-ignore

        conn.execute(text("""
            INSERT INTO payroll_entries
            (period_id,employee_id,basic_salary,housing_allowance,transport_allowance,other_allowances,
             salary_components_earning,salary_components_deduction,overtime_amount,
             gosi_employee_share,gosi_employer_share,violation_deduction,loan_deduction,deductions,net_salary)
            VALUES (:pid,:eid,:basic,:housing,:transport,:other,:comp_earn,:comp_ded,0,:gosi_emp,:gosi_empr,:violation,:loan,:deductions,:net)
        """), {"pid": period_id, "eid": data.employee_id, "basic": str(basic),
               "housing": str(housing), "transport": str(transport), "other": str(other),
               "comp_earn": str(comp_earning), "comp_ded": str(comp_deduction),
               "gosi_emp": str(gosi_emp), "gosi_empr": str(gosi_empr),
               "violation": str(violation_deduction), "loan": str(loan_deduction),
               "deductions": str(total_deductions), "net": str(net)})
        conn.commit()
        return {"message": "Payslip generated successfully"}
    finally:
        conn.close()


# --- Recruitment ---

class JobOpeningCreate(BaseModel):
    title: str
    department: Optional[str] = None
    positions: int = 1
    requirements: Optional[str] = None
    deadline: Optional[date] = None
    description: Optional[str] = None
    employment_type: str = "full_time"


class JobOpeningUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    positions: Optional[int] = None
    requirements: Optional[str] = None
    deadline: Optional[date] = None


class ApplicationCreate(BaseModel):
    job_opening_id: int
    applicant_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    resume_url: Optional[str] = None
    cover_letter: Optional[str] = None


class ApplicationStageUpdate(BaseModel):
    stage: str


@router.get("/recruitment/openings", dependencies=[Depends(require_permission("hr.view"))])
def list_job_openings(status: Optional[str] = None, branch_id: Optional[int] = None, current_user: UserResponse = Depends(get_current_user), company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        q = """SELECT jo.*,
                   (SELECT COUNT(*) FROM job_applications ja WHERE ja.opening_id = jo.id) as applications_count
            FROM job_openings jo WHERE 1=1"""
        params: Dict[str, Any] = {}
        if status:
            q += " AND jo.status = :status"
            params["status"] = status
        # Branch access control
        if current_user.role not in ['admin', 'system_admin', 'manager', 'gm']:
            if current_user.allowed_branches:
                if branch_id:
                    if branch_id not in current_user.allowed_branches:
                        raise HTTPException(status_code=403, detail="Unauthorized access to this branch")
                    q += " AND jo.branch_id = :bid"
                    params["bid"] = branch_id
                else:
                    branches_str = ",".join(map(str, current_user.allowed_branches))
                    q += f" AND (jo.branch_id IN ({branches_str}) OR jo.branch_id IS NULL)"
        else:
            if branch_id:
                q += " AND jo.branch_id = :bid"
                params["bid"] = branch_id
        q += " ORDER BY jo.created_at DESC"
        result = conn.execute(text(q), params).fetchall()
        return [dict(row._mapping) for row in result]
    finally:
        conn.close()


@router.post("/recruitment/openings", dependencies=[Depends(require_permission("hr.manage"))])
def create_job_opening(data: JobOpeningCreate, company_id: str = Depends(get_current_user_company), current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(company_id)
    try:
        res = conn.execute(text("""
            INSERT INTO job_openings (title,description,requirements,employment_type,vacancies,status,closing_date,created_by)
            VALUES (:title,:desc,:req,:emp_type,:vacancies,'open',:deadline,:created_by)
            RETURNING id,title,status,vacancies,created_at
        """), {"title": data.title, "desc": data.description or "", "req": data.requirements or "",
               "emp_type": data.employment_type, "vacancies": data.positions,
               "deadline": data.deadline, "created_by": current_user.id})
        conn.commit()
        return dict(res.fetchone()._mapping)
    finally:
        conn.close()


@router.put("/recruitment/openings/{opening_id}", dependencies=[Depends(require_permission("hr.manage"))])
def update_job_opening(opening_id: int, data: JobOpeningUpdate, company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        fields, params = [], {"id": opening_id}
        for f, col in [("title","title"),("status","status"),("positions","vacancies"),("requirements","requirements"),("deadline","closing_date")]:
            v = getattr(data, f, None)
            if v is not None:
                fields.append(f"{col} = :{f}"); params[f] = v
        if fields:
            conn.execute(text(f"UPDATE job_openings SET {', '.join(fields)} WHERE id = :id"), params)
            conn.commit()
        return {"message": "Updated"}
    finally:
        conn.close()


@router.get("/recruitment/openings/{opening_id}/applications", dependencies=[Depends(require_permission("hr.view"))])
def list_opening_applications(opening_id: int, current_user: UserResponse = Depends(get_current_user), company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        # Check branch access for this opening
        if current_user.role not in ['admin', 'system_admin', 'manager', 'gm']:
            opening = conn.execute(text("SELECT branch_id FROM job_openings WHERE id=:id"), {"id": opening_id}).fetchone()
            if opening and opening.branch_id and current_user.allowed_branches:
                if opening.branch_id not in current_user.allowed_branches:
                    raise HTTPException(status_code=403, detail="Unauthorized access to this branch")
        result = conn.execute(text("""
            SELECT ja.*, jo.title as opening_title
            FROM job_applications ja
            JOIN job_openings jo ON ja.opening_id = jo.id
            WHERE ja.opening_id = :id
            ORDER BY ja.created_at DESC
        """), {"id": opening_id}).fetchall()
        return [dict(row._mapping) for row in result]
    finally:
        conn.close()


@router.get("/recruitment/applications", dependencies=[Depends(require_permission("hr.view"))])
def list_all_applications(branch_id: Optional[int] = None, current_user: UserResponse = Depends(get_current_user), company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        q = """SELECT ja.*, jo.title as opening_title
            FROM job_applications ja
            LEFT JOIN job_openings jo ON ja.opening_id = jo.id
            WHERE 1=1"""
        params = {}
        if branch_id:
            q += " AND jo.branch_id = :bid"
            params["bid"] = branch_id
        q += " ORDER BY ja.created_at DESC"
        result = conn.execute(text(q), params).fetchall()
        return [dict(row._mapping) for row in result]
    finally:
        conn.close()


@router.post("/recruitment/applications", dependencies=[Depends(require_permission("hr.manage"))])
def create_application(data: ApplicationCreate, company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        res = conn.execute(text("""
            INSERT INTO job_applications (opening_id,applicant_name,email,phone,resume_url,cover_letter,stage,status)
            VALUES (:oid,:name,:email,:phone,:resume,:cover,'applied','pending')
            RETURNING id,applicant_name,email,stage,created_at
        """), {"oid": data.job_opening_id, "name": data.applicant_name, "email": data.email,
               "phone": data.phone, "resume": data.resume_url, "cover": data.cover_letter})
        conn.commit()
        return dict(res.fetchone()._mapping)
    finally:
        conn.close()


@router.put("/recruitment/applications/{app_id}/stage", dependencies=[Depends(require_permission("hr.manage"))])
def update_application_stage(app_id: int, data: ApplicationStageUpdate, company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        conn.execute(text("UPDATE job_applications SET stage=:stage, updated_at=NOW() WHERE id=:id"),
                     {"stage": data.stage, "id": app_id})
        conn.commit()
        return {"message": "Stage updated"}
    finally:
        conn.close()


# --- Leave Balance & Carryover (with branch access) ---

@router.get("/leave-balance/{emp_id}", dependencies=[Depends(require_permission("hr.view"))])
def get_leave_balance(emp_id: int, current_user: UserResponse = Depends(get_current_user), company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        from datetime import datetime as dt
        emp = conn.execute(text("""
            SELECT id, first_name||' '||last_name as name, annual_leave_entitlement, branch_id
            FROM employees WHERE id=:id
        """), {"id": emp_id}).fetchone()
        # Branch access check
        if emp and current_user.role not in ['admin', 'system_admin', 'manager', 'gm']:
            if current_user.allowed_branches and emp.branch_id not in current_user.allowed_branches:
                raise HTTPException(status_code=403, detail="Unauthorized access to this employee")
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        year = dt.now().year
        used = conn.execute(text("""
            SELECT COALESCE(SUM(days_requested),0) as used FROM leave_requests
            WHERE employee_id=:id AND status='approved' AND EXTRACT(YEAR FROM start_date)=:y
        """), {"id": emp_id, "y": year}).fetchone()
        carryover = conn.execute(text("""
            SELECT COALESCE(SUM(carried_days),0) as carried FROM leave_carryover
            WHERE employee_id=:id AND year=:y
        """), {"id": emp_id, "y": year}).fetchone()
        entitled = _dec(emp.annual_leave_entitlement) if emp.annual_leave_entitlement else Decimal('30')
        used_d = _dec(used.used)
        carried_d = _dec(carryover.carried)
        remaining = max(Decimal('0'), entitled + carried_d - used_d)
        return {
            "employee_id": emp_id, "employee_name": emp.name, "year": year,
            "balances": [{"leave_type": "annual", "entitled_days": str(entitled),
                          "used_days": str(used_d), "carried_days": str(carried_d),
                          "remaining_days": str(remaining)}]
        }
    finally:
        conn.close()


class LeaveCarryoverRequest(BaseModel):
    employee_id: int
    year: Optional[int] = None


@router.post("/leave-carryover/calculate", dependencies=[Depends(require_permission("hr.manage"))])
def calculate_leave_carryover(data: LeaveCarryoverRequest, current_user: UserResponse = Depends(get_current_user), company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        from datetime import datetime as dt
        year = data.year or (dt.now().year - 1)
        emp = conn.execute(text("""
            SELECT id, first_name||' '||last_name as name,
                   annual_leave_entitlement, leave_carryover_max, branch_id
            FROM employees WHERE id=:id
        """), {"id": data.employee_id}).fetchone()
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        # Branch access check
        if current_user.role not in ['admin', 'system_admin', 'manager', 'gm']:
            if current_user.allowed_branches and emp.branch_id not in current_user.allowed_branches:
                raise HTTPException(status_code=403, detail="Unauthorized access to this employee")
        used = conn.execute(text("""
            SELECT COALESCE(SUM(days_requested),0) as used FROM leave_requests
            WHERE employee_id=:id AND status='approved' AND EXTRACT(YEAR FROM start_date)=:y
        """), {"id": data.employee_id, "y": year}).fetchone()
        entitled = _dec(emp.annual_leave_entitlement) if emp.annual_leave_entitlement else Decimal('30')
        used_d = _dec(used.used)
        max_carry = _dec(emp.leave_carryover_max) if emp.leave_carryover_max else Decimal('5')
        remaining = entitled - used_d
        carried = min(max(Decimal('0'), remaining), max_carry)
        expired = max(Decimal('0'), remaining - carried)
        conn.execute(text("""
            INSERT INTO leave_carryover (employee_id,leave_type,year,entitled_days,used_days,carried_days,expired_days,max_carryover)
            VALUES (:eid,'annual',:year,:entitled,:used,:carried,:expired,:max_carry)
            ON CONFLICT (employee_id,leave_type,year) DO UPDATE SET
            entitled_days=EXCLUDED.entitled_days, used_days=EXCLUDED.used_days,
            carried_days=EXCLUDED.carried_days, expired_days=EXCLUDED.expired_days, calculated_at=NOW()
        """), {"eid": data.employee_id, "year": year, "entitled": str(entitled), "used": str(used_d),
               "carried": str(carried), "expired": str(expired), "max_carry": str(max_carry)})
        conn.commit()
        return {"employee_id": data.employee_id, "employee_name": emp.name, "year": year,
                "entitled_days": str(entitled), "used_days": str(used_d), "carried_days": str(carried), "expired_days": str(expired)}
    finally:
        conn.close()
