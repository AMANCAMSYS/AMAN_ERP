from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Union, Any
from routers.roles import DEFAULT_ROLES
from pydantic import BaseModel
from datetime import date, datetime
from database import get_company_db, get_db_connection, get_company_db as get_db, hash_password
from routers.auth import oauth2_scheme, decode_token, get_current_user, UserResponse
from utils.permissions import require_permission, validate_branch_access, check_permission
from utils.accounting import get_mapped_account_id, get_base_currency
from utils.audit import log_activity
from schemas.hr import LoanCreate, LoanResponse, EmployeeCreate, EmployeeUpdate, EmployeeResponse, DepartmentCreate, DepartmentResponse, PositionCreate, PositionResponse, PayrollPeriodCreate, PayrollGenerate, PayrollEntryResponse, PayrollPeriodResponse, AttendanceResponse, LeaveRequestCreate, LeaveRequestResponse, EndOfServiceRequest

router = APIRouter(prefix="/hr", tags=["HR & Employees"])

# --- Helpers ---

def has_permission(user: UserResponse, permission: str) -> bool:
    """Helper to check permissions for a user object"""
    user_perms = getattr(user, 'permissions', []) or []
    return check_permission(user_perms, permission)

def get_current_user_company(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if not payload or not payload.get("company_id"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return payload["company_id"]

# --- Endpoints ---

@router.get("/employees", dependencies=[Depends(require_permission("hr.view"))])
def get_employees(
    branch_id: Optional[int] = None, 
    current_user: UserResponse = Depends(get_current_user)
):
    company_id = current_user.company_id
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
            GROUP BY e.id, e.employee_code, e.first_name, e.last_name, e.email, e.phone, e.status, e.user_id, e.account_id, e.created_at, p.position_name, d.department_name, e.branch_id, e.salary, e.housing_allowance, e.transport_allowance, e.other_allowances, e.hourly_cost, u.role
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
                "allowed_branches": row.allowed_branches or [],
                "role": row.role or 'user'
            })
            
        return employees
    finally:
        conn.close()

@router.post("/employees", dependencies=[Depends(require_permission("hr.manage"))])
def create_employee(request: Request, employee: EmployeeCreate, current_user: UserResponse = Depends(get_current_user)):
    company_id = current_user.company_id
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
            role_key = employee.role or 'user'
            
            # Get default permissions for the role
            import json
            perms = DEFAULT_ROLES.get(role_key, [])
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

        # 4. Create Employee Record
        conn.execute(text("""
            INSERT INTO employees (
                employee_code, first_name, last_name, first_name_en, last_name_en,
                email, phone, department_id, position_id, 
                salary, housing_allowance, transport_allowance, other_allowances, hourly_cost,
                hire_date, user_id, account_id, branch_id
            ) VALUES (
                :code, :fn, :ln, :fne, :lne,
                :email, :phone, :did, :pid,
                :salary, :housing, :transport, :other, :hc,
                :hire, :uid, :aid, :bid
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
            "bid": employee.branch_id
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

        return {"message": "Success"}
        
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@router.put("/employees/{employee_id}", dependencies=[Depends(require_permission("hr.manage"))])
def update_employee(
    request: Request,
    employee_id: int, 
    employee: EmployeeUpdate, 
    current_user: UserResponse = Depends(get_current_user)
):
    company_id = current_user.company_id
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

        # Update Role if provided
        if user_id and employee.role:
            conn.execute(text("UPDATE company_users SET role = :r WHERE id = :uid"), {"r": employee.role, "uid": user_id})

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
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=400, detail=str(e))
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
def create_payroll_period(period: PayrollPeriodCreate, company_id: str = Depends(get_current_user_company)):
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
        return {"message": "Created successfully"}
    finally:
        conn.close()

@router.get("/payroll-periods/{period_id}/entries", response_model=List[PayrollEntryResponse], dependencies=[Depends(require_permission(["hr.view", "hr.payroll.view"]))])
def get_payroll_entries(period_id: int, branch_id: Optional[int] = None, company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        query = """
            SELECT pe.id, 
                   e.first_name || ' ' || e.last_name as employee_name,
                   p.position_name as position,
                   pe.basic_salary, pe.housing_allowance, pe.transport_allowance, pe.other_allowances, 
                   pe.deductions, pe.net_salary
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
                "net_salary": row.net_salary or 0
            })
        return entries
    finally:
        conn.close()

# --- LOAN ENDPOINTS ---

@router.post("/loans", response_model=LoanResponse, dependencies=[Depends(require_permission("hr.loans.manage"))])
def create_loan_request(loan: LoanCreate, current_user: UserResponse = Depends(get_current_user)):
    # Standard restriction: only those with loan management permission can create
    if not has_permission(current_user, "hr.loans.manage"):
         raise HTTPException(status_code=403, detail="Not authorized")
         
    company_id = current_user.company_id
    conn = get_db_connection(company_id)
    try:
        monthly_installment = loan.amount / loan.total_installments
        
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
        return {**loan.model_dump(), "id": result.id, "monthly_installment": result.monthly_installment, 
                "paid_amount": result.paid_amount, "status": result.status, "created_at": result.created_at}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/loans", dependencies=[Depends(require_permission("hr.loans.view"))])
def list_loans(branch_id: Optional[int] = None, current_user: UserResponse = Depends(get_current_user)):
    if not has_permission(current_user, "hr.loans.view"):
        raise HTTPException(status_code=403, detail="Not authorized")
    company_id = current_user.company_id
    conn = get_db_connection(company_id)
    try:
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
        print(f"ERROR list_loans: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.put("/loans/{loan_id}/approve", dependencies=[Depends(require_permission("hr.loans.manage"))])
def approve_loan(loan_id: int, current_user: UserResponse = Depends(get_current_user)):
    if not has_permission(current_user, "hr.loans.manage"): # Manager only
         raise HTTPException(status_code=403, detail="Not authorized")
         
    company_id = current_user.company_id
    conn = get_db_connection(company_id)
    trans = conn.begin()
    try:
        loan = conn.execute(text("SELECT * FROM employee_loans WHERE id=:id FOR UPDATE"), {"id": loan_id}).fetchone()
        if not loan or loan.status != 'pending':
            raise HTTPException(status_code=400, detail="Invalid loan status")
            
        # Update Status
        conn.execute(text("UPDATE employee_loans SET status='active', approved_by=:uid WHERE id=:id"), 
                     {"uid": current_user.get("id") if isinstance(current_user, dict) else current_user.id, "id": loan_id})
        
        # Create Journal Entry for Loan Disbursement (Automated)
        acc_loan = get_mapped_account_id(conn, "acc_map_loans_adv")
        acc_cash = get_mapped_account_id(conn, "acc_map_cash_main")
        
        if acc_loan and acc_cash:
            import random
            je_num = f"JE-LOAN-{loan_id}-{random.randint(100, 999)}"
            base_currency = get_base_currency(conn)
            je_id = conn.execute(text("""
                INSERT INTO journal_entries (
                    entry_number, entry_date, reference, description, status, created_by,
                    currency, exchange_rate
                )
                VALUES (:num, CURRENT_DATE, :ref, :desc, 'posted', :uid, :currency, 1.0) RETURNING id
            """), {
                "num": je_num, "ref": f"LOAN-{loan_id}", 
                "desc": f"صرف سلفة لموظف - رقم {loan_id}", "uid": current_user.get("id") if isinstance(current_user, dict) else current_user.id,
                "currency": base_currency
            }).scalar()
            
            # Debit: Employee Loans (Asset)
            conn.execute(text("INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES (:jid, :acc, :amt, 0, 'مدين سلفة موظف')"),
                         {"jid": je_id, "acc": acc_loan, "amt": loan.amount})
            # Credit: Cash (Asset)
            conn.execute(text("INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES (:jid, :acc, 0, :amt, 'دائن نقدية/صرف سلفة')"),
                         {"jid": je_id, "acc": acc_cash, "amt": loan.amount})
            
            # Update Account Balances
            from utils.accounting import update_account_balance
            update_account_balance(conn, account_id=acc_loan, debit_base=float(loan.amount), credit_base=0)
            update_account_balance(conn, account_id=acc_cash, debit_base=0, credit_base=float(loan.amount))
        
        trans.commit()
        return {"status": "active"}
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.post("/payroll-periods/{period_id}/generate", dependencies=[Depends(require_permission(["hr.manage", "hr.payroll.manage"]))])
def generate_payroll(period_id: int, current_user: UserResponse = Depends(get_current_user)):
    company_id = current_user.company_id
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
        
        # Fetch Active Employees
        employees = conn.execute(text("""
            SELECT id, salary, housing_allowance, transport_allowance, other_allowances 
            FROM employees WHERE status = 'active'
        """)).fetchall()

        # Fetch GOSI settings (active)
        gosi = conn.execute(text("SELECT * FROM gosi_settings WHERE is_active = TRUE ORDER BY id DESC LIMIT 1")).fetchone()
        gosi_emp_pct = float(gosi.employee_share_percentage) if gosi else 9.75
        gosi_empr_pct = float(gosi.employer_share_percentage) if gosi else 11.75
        gosi_max_sal = float(gosi.max_contributable_salary) if gosi else 45000
        
        count = 0
        for emp in employees:
            basic = float(emp.salary or 0)
            housing = float(emp.housing_allowance or 0)
            transport = float(emp.transport_allowance or 0)
            other = float(emp.other_allowances or 0)

            # === 1. Salary Components (earnings & deductions) ===
            comp_earning = 0
            comp_deduction = 0
            try:
                components = conn.execute(text("""
                    SELECT esc.amount, sc.component_type, sc.calculation_type, sc.percentage_of, sc.percentage_value
                    FROM employee_salary_components esc
                    JOIN salary_components sc ON esc.component_id = sc.id
                    WHERE esc.employee_id = :eid AND esc.is_active = TRUE AND sc.is_active = TRUE
                """), {"eid": emp.id}).fetchall()

                for comp in components:
                    if comp.calculation_type == 'percentage':
                        base_val = basic if (comp.percentage_of or 'basic') == 'basic' else (basic + housing)
                        amt = round(base_val * float(comp.percentage_value or 0) / 100, 2)
                    else:
                        amt = float(comp.amount or 0)
                    
                    if comp.component_type == 'earning':
                        comp_earning += amt
                    else:
                        comp_deduction += amt
            except Exception:
                pass  # Table may not exist in older DBs

            # === 2. Approved Overtime (not yet processed) ===
            overtime_amount = 0
            try:
                ot_rows = conn.execute(text("""
                    SELECT COALESCE(SUM(calculated_amount), 0) as total
                    FROM overtime_requests
                    WHERE employee_id = :eid AND status = 'approved'
                """), {"eid": emp.id}).fetchone()
                overtime_amount = float(ot_rows.total) if ot_rows else 0
            except Exception:
                pass

            # === 3. GOSI Deductions ===
            contributable = min(basic + housing, gosi_max_sal)
            gosi_emp_share = round(contributable * gosi_emp_pct / 100, 2)
            gosi_empr_share = round(contributable * gosi_empr_pct / 100, 2)

            # === 4. Violation Deductions (open, deduct_from_salary, not yet deducted) ===
            violation_deduction = 0
            try:
                viol = conn.execute(text("""
                    SELECT COALESCE(SUM(penalty_amount), 0) as total
                    FROM employee_violations
                    WHERE employee_id = :eid AND deduct_from_salary = TRUE 
                    AND status = 'open' AND (payroll_period_id IS NULL)
                """), {"eid": emp.id}).fetchone()
                violation_deduction = float(viol.total) if viol else 0
            except Exception:
                pass

            # === 5. Loan Deductions ===
            active_loan = conn.execute(text("SELECT * FROM employee_loans WHERE employee_id=:eid AND status='active' AND paid_amount < amount"), {"eid": emp.id}).fetchone()
            loan_deduction = 0
            if active_loan:
                loan_deduction = float(min(active_loan.monthly_installment, active_loan.amount - active_loan.paid_amount))

            # === Calculate totals ===
            total_earnings = basic + housing + transport + other + comp_earning + overtime_amount
            total_deductions = comp_deduction + gosi_emp_share + violation_deduction + loan_deduction
            net = round(total_earnings - total_deductions, 2)
            
            conn.execute(text("""
                INSERT INTO payroll_entries (
                    period_id, employee_id, basic_salary, housing_allowance, transport_allowance, 
                    other_allowances, salary_components_earning, salary_components_deduction,
                    overtime_amount, gosi_employee_share, gosi_employer_share,
                    violation_deduction, loan_deduction, deductions, net_salary
                )
                VALUES (:pid, :eid, :basic, :housing, :transport, :other, :comp_earn, :comp_ded,
                        :overtime, :gosi_emp, :gosi_empr, :viol_ded, :loan_ded, :total_ded, :net)
            """), {
                "pid": period_id, "eid": emp.id,
                "basic": basic, "housing": housing, "transport": transport, "other": other,
                "comp_earn": comp_earning, "comp_ded": comp_deduction,
                "overtime": overtime_amount, "gosi_emp": gosi_emp_share, "gosi_empr": gosi_empr_share,
                "viol_ded": violation_deduction, "loan_ded": loan_deduction,
                "total_ded": total_deductions, "net": net
            })
            count += 1
            
        trans.commit()
        return {"message": f"Generated payroll for {count} employees"}
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.post("/payroll-periods/{period_id}/post", dependencies=[Depends(require_permission(["hr.manage", "hr.payroll.manage"]))])
def post_payroll(period_id: int, current_user: UserResponse = Depends(get_current_user)):
    company_id = current_user.company_id
    conn = get_db_connection(company_id)
    trans = conn.begin()
    try:
        # 1. Check Status
        period = conn.execute(text("SELECT * FROM payroll_periods WHERE id = :id"), {"id": period_id}).fetchone()
        if not period or period.status != 'draft':
            raise HTTPException(status_code=400, detail="Invalid period status")

        # 2. Calculate Totals (enhanced with new columns)
        totals = conn.execute(text("""
            SELECT 
                SUM(net_salary) as total_net,
                SUM(basic_salary + housing_allowance + transport_allowance + other_allowances + salary_components_earning + overtime_amount) as total_gross,
                SUM(gosi_employee_share) as total_gosi_emp,
                SUM(gosi_employer_share) as total_gosi_empr,
                SUM(overtime_amount) as total_overtime,
                SUM(violation_deduction) as total_violations,
                SUM(loan_deduction) as total_loans,
                SUM(salary_components_deduction) as total_comp_ded
            FROM payroll_entries WHERE period_id = :id
        """), {"id": period_id}).fetchone()
        
        total_net = float(totals.total_net or 0)
        totals_gross = float(totals.total_gross or 0)
        total_gosi_emp = float(totals.total_gosi_emp or 0)
        total_gosi_empr = float(totals.total_gosi_empr or 0)
        total_violations = float(totals.total_violations or 0)
        total_loans = float(totals.total_loans or 0)
        
        if total_net == 0:
            raise HTTPException(status_code=400, detail="No payroll calculated to post")

        # 3. Handle Loan Deductions & Balances
        if total_loans > 0:
            entries_with_loans = conn.execute(text("SELECT employee_id, loan_deduction FROM payroll_entries WHERE period_id = :id AND loan_deduction > 0"), {"id": period_id}).fetchall()
            for entry in entries_with_loans:
                loan = conn.execute(text("SELECT * FROM employee_loans WHERE employee_id=:eid AND status='active' AND paid_amount < amount"), {"eid": entry.employee_id}).fetchone()
                if loan:
                    new_paid = float(loan.paid_amount) + float(entry.loan_deduction)
                    new_status = 'completed' if new_paid >= float(loan.amount) else 'active'
                    conn.execute(text("UPDATE employee_loans SET paid_amount = :paid, status = :status WHERE id=:id"), 
                                 {"paid": new_paid, "status": new_status, "id": loan.id})

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
        
        je_num = f"PAY-{period_id}-{datetime.now().strftime('%Y%m%d')}"
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        branch_id = current_user.get("branch_id") if isinstance(current_user, dict) else (current_user.allowed_branches[0] if current_user.allowed_branches else None)
        
        base_currency = get_base_currency(conn)
        je_id = conn.execute(text("""
            INSERT INTO journal_entries (
                entry_number, entry_date, description, status, branch_id, created_by,
                currency, exchange_rate
            )
            VALUES (:num, :date, :desc, 'posted', :bid, :uid, :currency, 1.0) RETURNING id
        """), {
            "num": je_num, "date": datetime.now().date(),
            "desc": f"Payroll for period {period.name}",
            "bid": branch_id, "uid": user_id,
            "currency": base_currency
        }).fetchone()[0]
        
        from utils.accounting import update_account_balance

        # Line 1: Dr Salaries Expense (Gross)
        acc_salaries_exp = get_mapped_account_id(conn, "acc_map_salaries_exp")
        if acc_salaries_exp:
            conn.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description, amount_currency, currency)
                VALUES (:je, :acc, :amount, 0, 'مصروف رواتب وأجور - Salaries Expense', :amount, :currency)
            """), {"je": je_id, "acc": acc_salaries_exp, "amount": totals_gross, "currency": base_currency})
            update_account_balance(conn, account_id=acc_salaries_exp, debit_base=totals_gross, credit_base=0)

        # Line 2: Dr GOSI Employer Expense
        if total_gosi_empr > 0:
            acc_gosi_exp = get_mapped_account_id(conn, "acc_map_gosi_expense")
            if acc_gosi_exp:
                conn.execute(text("""
                    INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description, amount_currency, currency)
                    VALUES (:je, :acc, :amount, 0, 'مصروف تأمينات اجتماعية (حصة صاحب العمل) - GOSI Employer', :amount, :currency)
                """), {"je": je_id, "acc": acc_gosi_exp, "amount": total_gosi_empr, "currency": base_currency})
                update_account_balance(conn, account_id=acc_gosi_exp, debit_base=total_gosi_empr, credit_base=0)

        # Line 3: Cr GOSI Payable (employee + employer shares)
        total_gosi = total_gosi_emp + total_gosi_empr
        if total_gosi > 0:
            acc_gosi_payable = get_mapped_account_id(conn, "acc_map_gosi_payable")
            if acc_gosi_payable:
                conn.execute(text("""
                    INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description, amount_currency, currency)
                    VALUES (:je, :acc, 0, :amount, 'التأمينات المستحقة (حصة موظف + صاحب عمل) - GOSI Payable', :amount, :currency)
                """), {"je": je_id, "acc": acc_gosi_payable, "amount": total_gosi, "currency": base_currency})
                update_account_balance(conn, account_id=acc_gosi_payable, debit_base=0, credit_base=total_gosi)

        # Line 4: Cr Employee Loans (Deductions)
        if total_loans > 0:
            acc_loans_adv = get_mapped_account_id(conn, "acc_map_loans_adv")
            if acc_loans_adv:
                conn.execute(text("""
                    INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description, amount_currency, currency)
                    VALUES (:je, :acc, 0, :amount, 'استقطاع سلف موظفين - Loan Repayment', :amount, :currency)
                """), {"je": je_id, "acc": acc_loans_adv, "amount": total_loans, "currency": base_currency})
                update_account_balance(conn, account_id=acc_loans_adv, debit_base=0, credit_base=total_loans)
            
        # Line 5: Cr Bank (Net Payout)
        acc_bank = get_mapped_account_id(conn, "acc_map_bank")
        if acc_bank:
            conn.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description, amount_currency, currency)
                VALUES (:je, :acc, 0, :amount, 'صافي الرواتب المحولة - Net Salary Payment', :amount, :currency)
            """), {"je": je_id, "acc": acc_bank, "amount": total_net, "currency": base_currency})
            update_account_balance(conn, account_id=acc_bank, debit_base=0, credit_base=total_net)

        # 7. Update Period Status
        conn.execute(text("UPDATE payroll_periods SET status='posted' WHERE id=:id"), {"id": period_id})
        
        trans.commit()
        return {"message": "Payroll posted successfully", "journal_entry": je_num}

    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=500, detail=str(e))
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
def create_department(dept: DepartmentCreate, company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    trans = conn.begin()
    try:
        conn.execute(text("INSERT INTO departments (department_name) VALUES (:name)"), {"name": dept.department_name})
        trans.commit()
        return {"message": "Department created"}
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.delete("/departments/{dept_id}", dependencies=[Depends(require_permission("hr.manage"))])
def delete_department(dept_id: int, company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    trans = conn.begin()
    try:
        # Check usage
        count = conn.execute(text("SELECT COUNT(*) FROM employees WHERE department_id = :id"), {"id": dept_id}).scalar()
        if count > 0:
            raise HTTPException(status_code=400, detail="Cannot delete department. It is assigned to employees.")

        conn.execute(text("DELETE FROM departments WHERE id = :id"), {"id": dept_id})
        trans.commit()
        return {"message": "Department deleted"}
    except HTTPException:
        raise
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=500, detail=str(e))
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
def create_position(pos: PositionCreate, company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    trans = conn.begin()
    try:
        conn.execute(text("INSERT INTO employee_positions (position_name, department_id) VALUES (:name, :did)"), 
                     {"name": pos.position_name, "did": pos.department_id})
        trans.commit()
        return {"message": "Position created"}
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.delete("/positions/{pos_id}", dependencies=[Depends(require_permission("hr.manage"))])
def delete_position(pos_id: int, company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    trans = conn.begin()
    try:
        # Check usage
        count = conn.execute(text("SELECT COUNT(*) FROM employees WHERE position_id = :id"), {"id": pos_id}).scalar()
        if count > 0:
            raise HTTPException(status_code=400, detail="Cannot delete position. It is assigned to employees.")

        conn.execute(text("DELETE FROM employee_positions WHERE id = :id"), {"id": pos_id})
        trans.commit()
        return {"message": "Position deleted"}
    except HTTPException:
        raise
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=500, detail=str(e))
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
def check_in(
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
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=500, detail=str(e))
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
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=500, detail=str(e))
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
def create_leave_request(request: LeaveRequestCreate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
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
            from datetime import datetime as dt
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
                amount=float(leave_days),
                submitted_by=user_id,
                description=f"طلب إجازة {request.leave_type} - {leave_days} يوم",
                link=f"/hr/leaves"
            )
            if approval_info:
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
        print(f"Error creating leave: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/leaves", response_model=List[LeaveRequestResponse], dependencies=[Depends(require_permission("hr.view"))])
def list_leave_requests(branch_id: Optional[int] = None, current_user: UserResponse = Depends(get_current_user)):
    # Basic view permission required
    if not has_permission(current_user, "hr.leaves.view"):
        pass 
        # Actually, let's enforce view permission to be safe, but typically all employees should have "hr.leaves.view" or "hr.view".
        # If strict: raise HTTPException(status_code=403, detail="Not authorized")
    
    conn = get_db_connection(current_user.company_id)
    try:
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
def update_leave_status(leave_id: int, status_in: str, current_user: UserResponse = Depends(get_current_user)):
    if not has_permission(current_user, "hr.leaves.manage"):
        raise HTTPException(status_code=403, detail="Not authorized")
        
    if status_in not in ['approved', 'rejected']:
         raise HTTPException(status_code=400, detail="Invalid status")
         
    conn = get_db_connection(current_user.company_id)
    try:
        conn.execute(text("""
            UPDATE leave_requests 
            SET status = :status, approved_by = :uid, updated_at = NOW()
            WHERE id = :id
        """), {"status": status_in, "uid": current_user.get("id") if isinstance(current_user, dict) else current_user.id, "id": leave_id})
        conn.commit()
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
            SELECT id, employee_name, join_date, basic_salary, 
                   COALESCE(housing_allowance, 0) as housing_allowance,
                   COALESCE(transport_allowance, 0) as transport_allowance
            FROM employees WHERE id = :eid
        """), {"eid": data.employee_id}).fetchone()
        
        if not emp:
            raise HTTPException(status_code=404, detail="الموظف غير موجود")
        
        termination_date = data.termination_date or date.today()
        join_date = emp.join_date
        
        if not join_date:
            raise HTTPException(status_code=400, detail="تاريخ التعيين غير محدد للموظف")
        
        # Calculate service years
        from dateutil.relativedelta import relativedelta
        delta = relativedelta(termination_date, join_date)
        total_years = delta.years + (delta.months / 12) + (delta.days / 365.25)
        
        if total_years < 0:
            raise HTTPException(status_code=400, detail="تاريخ الإنهاء قبل تاريخ التعيين")
        
        # Total salary (basic + housing + transport) used as base
        base_salary = float(emp.basic_salary or 0)
        total_salary = base_salary + float(emp.housing_allowance) + float(emp.transport_allowance)
        
        # Saudi Labor Law End of Service Rules:
        # First 5 years: half month salary per year
        # After 5 years: full month salary per year
        # Resignation adjustments:
        #   < 2 years: nothing
        #   2-5 years: 1/3 of total
        #   5-10 years: 2/3 of total
        #   > 10 years: full amount
        
        gratuity = 0
        if total_years <= 5:
            gratuity = (total_salary / 2) * total_years
        else:
            first_five = (total_salary / 2) * 5
            remaining = total_salary * (total_years - 5)
            gratuity = first_five + remaining
        
        # Apply resignation factor
        resignation_factor = 1.0
        if data.termination_reason == "resignation":
            if total_years < 2:
                resignation_factor = 0
            elif total_years < 5:
                resignation_factor = 1/3
            elif total_years < 10:
                resignation_factor = 2/3
            else:
                resignation_factor = 1.0
        
        final_gratuity = round(gratuity * resignation_factor, 2)
        
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
            "service_years": round(total_years, 2),
            "service_years_display": f"{delta.years} سنة و {delta.months} شهر و {delta.days} يوم",
            "base_salary": base_salary,
            "total_salary_used": total_salary,
            "full_gratuity": round(gratuity, 2),
            "resignation_factor": resignation_factor,
            "final_gratuity": final_gratuity,
            "unpaid_leave_days": int(unpaid_days),
            "notes": "الحساب وفقاً لنظام العمل السعودي - المادة 84 و 85"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# =====================================================
# 8.15 HR IMPROVEMENTS
# =====================================================

# ---------- HR-005: Payslip View / Print ----------

@router.get("/payslips/{entry_id}", dependencies=[Depends(require_permission("hr.view"))])
def get_payslip(entry_id: int, current_user=Depends(get_current_user)):
    """Get a single payslip entry with full details for printing."""
    conn = get_db_connection(current_user.company_id)
    try:
        entry = conn.execute(text("""
            SELECT pe.*, e.employee_name, e.employee_code, e.national_id,
                   d.name as department_name, p.name as position_name,
                   pp.name as period_name, pp.start_date, pp.end_date
            FROM payroll_entries pe
            JOIN employees e ON pe.employee_id = e.id
            LEFT JOIN departments d ON e.department_id = d.id
            LEFT JOIN positions p ON e.position_id = p.id
            JOIN payroll_periods pp ON pe.period_id = pp.id
            WHERE pe.id = :id
        """), {"id": entry_id}).fetchone()
        if not entry:
            raise HTTPException(status_code=404, detail="Payslip not found")
        return dict(entry._mapping)
    finally:
        conn.close()


@router.get("/employees/{emp_id}/payslips", dependencies=[Depends(require_permission("hr.view"))])
def employee_payslip_history(emp_id: int, current_user=Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        rows = conn.execute(text("""
            SELECT pe.*, pp.name as period_name, pp.start_date, pp.end_date
            FROM payroll_entries pe
            JOIN payroll_periods pp ON pe.period_id = pp.id
            WHERE pe.employee_id = :eid
            ORDER BY pp.end_date DESC
        """), {"eid": emp_id}).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()


# ---------- HR-006: Leave Carryover ----------

@router.get("/leave-balance/{emp_id}", dependencies=[Depends(require_permission("hr.view"))])
def get_leave_balance(emp_id: int, year: Optional[int] = None, current_user=Depends(get_current_user)):
    """Get detailed leave balance for an employee."""
    conn = get_db_connection(current_user.company_id)
    try:
        from datetime import datetime as dt
        yr = year or dt.now().year
        emp = conn.execute(text(
            "SELECT annual_leave_entitlement, leave_carryover_max FROM employees WHERE id = :id"
        ), {"id": emp_id}).fetchone()
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")

        entitlement = float(emp.annual_leave_entitlement or 30)
        max_carry = float(emp.leave_carryover_max or 5)

        # Used days this year
        used = conn.execute(text("""
            SELECT COALESCE(SUM(end_date - start_date + 1), 0) as days
            FROM leave_requests
            WHERE employee_id = :eid AND status = 'approved'
              AND EXTRACT(YEAR FROM start_date) = :yr AND leave_type = 'annual'
        """), {"eid": emp_id, "yr": yr}).scalar() or 0

        # Carryover from previous year
        carry = conn.execute(text("""
            SELECT COALESCE(carried_days, 0) FROM leave_carryover
            WHERE employee_id = :eid AND year = :yr AND leave_type = 'annual'
        """), {"eid": emp_id, "yr": yr}).scalar() or 0

        total = entitlement + float(carry)
        remaining = total - float(used)

        return {
            "employee_id": emp_id, "year": yr,
            "entitlement": entitlement, "carryover": float(carry),
            "total_available": total, "used": float(used),
            "remaining": remaining, "max_carryover_next": max_carry,
        }
    finally:
        conn.close()


@router.post("/leave-carryover/calculate", dependencies=[Depends(require_permission("hr.manage"))])
def calculate_leave_carryover(data: dict, current_user=Depends(get_current_user)):
    """Calculate and record leave carryover at year end."""
    conn = get_db_connection(current_user.company_id)
    try:
        from_year = data.get("from_year")
        to_year = from_year + 1
        employees = conn.execute(text(
            "SELECT id, annual_leave_entitlement, leave_carryover_max FROM employees WHERE status = 'active'"
        )).fetchall()

        results = []
        for emp in employees:
            entitlement = float(emp.annual_leave_entitlement or 30)
            max_carry = float(emp.leave_carryover_max or 5)
            used = conn.execute(text("""
                SELECT COALESCE(SUM(end_date - start_date + 1),0) FROM leave_requests
                WHERE employee_id = :eid AND status = 'approved'
                  AND EXTRACT(YEAR FROM start_date) = :yr AND leave_type = 'annual'
            """), {"eid": emp.id, "yr": from_year}).scalar() or 0
            remaining = entitlement - float(used)
            carried = min(remaining, max_carry) if remaining > 0 else 0
            expired = remaining - carried if remaining > carried else 0

            conn.execute(text("""
                INSERT INTO leave_carryover (employee_id, leave_type, year, entitled_days, used_days,
                    carried_days, expired_days, max_carryover)
                VALUES (:eid, 'annual', :yr, :ent, :used, :carry, :exp, :max)
                ON CONFLICT (employee_id, leave_type, year) DO UPDATE
                SET carried_days = :carry, expired_days = :exp, used_days = :used, calculated_at = NOW()
            """), {
                "eid": emp.id, "yr": to_year, "ent": entitlement,
                "used": float(used), "carry": carried, "exp": expired, "max": max_carry,
            })
            results.append({"employee_id": emp.id, "carried": carried, "expired": expired})

        conn.commit()
        return {"year": to_year, "employees_processed": len(results), "details": results}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ---------- HR-012: Recruitment ----------

@router.get("/recruitment/openings", dependencies=[Depends(require_permission("hr.view"))])
def list_job_openings(status: Optional[str] = None, current_user=Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        q = """SELECT jo.*,
                      (SELECT COUNT(*) FROM job_applications ja WHERE ja.opening_id = jo.id) AS applications_count
               FROM job_openings jo WHERE 1=1"""
        params = {}
        if status:
            q += " AND jo.status = :status"
            params["status"] = status
        q += " ORDER BY jo.created_at DESC"
        rows = conn.execute(text(q), params).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/recruitment/openings", dependencies=[Depends(require_permission("hr.manage"))])
def create_job_opening(data: dict, current_user=Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        result = conn.execute(text("""
            INSERT INTO job_openings (title, department_id, position_id, description, requirements,
                employment_type, vacancies, status, branch_id, closing_date, created_by)
            VALUES (:title, :dept, :pos, :desc, :req, :etype, :vac, 'open', :branch, :close, :uid)
            RETURNING *
        """), {
            "title": data["title"], "dept": data.get("department_id"),
            "pos": data.get("position_id"), "desc": data.get("description"),
            "req": data.get("requirements"), "etype": data.get("employment_type", "full_time"),
            "vac": data.get("vacancies", 1), "branch": data.get("branch_id"),
            "close": data.get("closing_date"), "uid": current_user.id,
        }).fetchone()
        conn.commit()
        return dict(result._mapping)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.put("/recruitment/openings/{opening_id}", dependencies=[Depends(require_permission("hr.manage"))])
def update_opening_status(opening_id: int, data: dict, current_user=Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        conn.execute(text("UPDATE job_openings SET status = :s WHERE id = :id"),
                     {"s": data["status"], "id": opening_id})
        conn.commit()
        return {"message": "Opening updated"}
    finally:
        conn.close()


@router.get("/recruitment/openings/{opening_id}/applications", dependencies=[Depends(require_permission("hr.view"))])
def list_applications(opening_id: int, current_user=Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        rows = conn.execute(text(
            "SELECT * FROM job_applications WHERE opening_id = :oid ORDER BY created_at DESC"
        ), {"oid": opening_id}).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        conn.close()


@router.post("/recruitment/applications", dependencies=[Depends(require_permission("hr.manage"))])
def create_application(data: dict, current_user=Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        result = conn.execute(text("""
            INSERT INTO job_applications (opening_id, applicant_name, email, phone,
                resume_url, cover_letter, stage, status)
            VALUES (:oid, :name, :email, :phone, :resume, :cover, 'applied', 'pending')
            RETURNING *
        """), {
            "oid": data["opening_id"], "name": data["applicant_name"],
            "email": data.get("email"), "phone": data.get("phone"),
            "resume": data.get("resume_url"), "cover": data.get("cover_letter"),
        }).fetchone()
        conn.commit()
        return dict(result._mapping)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.put("/recruitment/applications/{app_id}/stage", dependencies=[Depends(require_permission("hr.manage"))])
def update_application_stage(app_id: int, data: dict, current_user=Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        sets = ["stage = :stage", "updated_at = NOW()"]
        params = {"stage": data["stage"], "id": app_id}
        if "rating" in data:
            sets.append("rating = :rating")
            params["rating"] = data["rating"]
        if "notes" in data:
            sets.append("notes = :notes")
            params["notes"] = data["notes"]
        if "interview_date" in data:
            sets.append("interview_date = :idate")
            params["idate"] = data["interview_date"]
        if "interviewer_id" in data:
            sets.append("interviewer_id = :iid")
            params["iid"] = data["interviewer_id"]
        if data["stage"] in ("hired", "rejected"):
            sets.append("status = :status")
            params["status"] = data["stage"]
        conn.execute(text(f"UPDATE job_applications SET {', '.join(sets)} WHERE id = :id"), params)
        conn.commit()
        return {"message": f"Application moved to {data['stage']}"}
    finally:
        conn.close()


# ============================================================
# Phase 8.15 - Payslips, Recruitment, Leave Balance
# ============================================================
import calendar as cal_module

# --- Payslips ---

@router.get("/payslips", dependencies=[Depends(require_permission("hr.view"))])
def list_all_payslips(company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        result = conn.execute(text("""
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
            ORDER BY pp.start_date DESC, e.first_name
        """)).fetchall()
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
def generate_single_payslip(data: PayslipGenerateRequest, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
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

        basic = float(emp.basic_salary or 0)
        housing = float(emp.housing_allowance or 0)
        transport = float(emp.transport_allowance or 0)
        other = float(emp.other_allowances or 0)
        net = basic + housing + transport + other

        conn.execute(text("""
            INSERT INTO payroll_entries
            (period_id,employee_id,basic_salary,housing_allowance,transport_allowance,other_allowances,
             salary_components_earning,salary_components_deduction,overtime_amount,
             gosi_employee_share,gosi_employer_share,violation_deduction,loan_deduction,deductions,net_salary)
            VALUES (:pid,:eid,:basic,:housing,:transport,:other,0,0,0,0,0,0,0,0,:net)
        """), {"pid": period_id, "eid": data.employee_id, "basic": basic,
               "housing": housing, "transport": transport, "other": other, "net": net})
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
    deadline: Optional[str] = None
    description: Optional[str] = None
    employment_type: str = "full_time"


class JobOpeningUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    positions: Optional[int] = None
    requirements: Optional[str] = None
    deadline: Optional[str] = None


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
def list_job_openings(company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        result = conn.execute(text("""
            SELECT jo.*,
                   (SELECT COUNT(*) FROM job_applications ja WHERE ja.opening_id = jo.id) as applications_count
            FROM job_openings jo ORDER BY jo.created_at DESC
        """)).fetchall()
        return [dict(row._mapping) for row in result]
    finally:
        conn.close()


@router.post("/recruitment/openings", dependencies=[Depends(require_permission("hr.manage"))])
def create_job_opening(data: JobOpeningCreate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
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
def update_job_opening(opening_id: int, data: JobOpeningUpdate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
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
def list_opening_applications(opening_id: int, company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        result = conn.execute(text("""
            SELECT ja.*, jo.title as opening_title
            FROM job_applications ja
            LEFT JOIN job_openings jo ON ja.opening_id = jo.id
            WHERE ja.opening_id = :oid ORDER BY ja.created_at DESC
        """), {"oid": opening_id}).fetchall()
        return [dict(row._mapping) for row in result]
    finally:
        conn.close()


@router.get("/recruitment/applications", dependencies=[Depends(require_permission("hr.view"))])
def list_all_applications(company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        result = conn.execute(text("""
            SELECT ja.*, jo.title as opening_title
            FROM job_applications ja
            LEFT JOIN job_openings jo ON ja.opening_id = jo.id
            ORDER BY ja.created_at DESC
        """)).fetchall()
        return [dict(row._mapping) for row in result]
    finally:
        conn.close()


@router.post("/recruitment/applications", dependencies=[Depends(require_permission("hr.manage"))])
def create_application(data: ApplicationCreate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
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
def update_application_stage(app_id: int, data: ApplicationStageUpdate, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        conn.execute(text("UPDATE job_applications SET stage=:stage, updated_at=NOW() WHERE id=:id"),
                     {"stage": data.stage, "id": app_id})
        conn.commit()
        return {"message": "Stage updated"}
    finally:
        conn.close()


# --- Leave Balance & Carryover ---

@router.get("/leave-balance/{emp_id}", dependencies=[Depends(require_permission("hr.view"))])
def get_leave_balance(emp_id: int, company_id: str = Depends(get_current_user_company)):
    conn = get_db_connection(company_id)
    try:
        from datetime import datetime as dt
        emp = conn.execute(text("""
            SELECT id, first_name||' '||last_name as name, annual_leave_entitlement
            FROM employees WHERE id=:id
        """), {"id": emp_id}).fetchone()
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
        entitled = float(emp.annual_leave_entitlement or 30)
        used_d = float(used.used or 0)
        carried_d = float(carryover.carried or 0)
        return {
            "employee_id": emp_id, "employee_name": emp.name, "year": year,
            "balances": [{"leave_type": "annual", "entitled_days": entitled,
                          "used_days": used_d, "carried_days": carried_d,
                          "remaining_days": max(0, entitled + carried_d - used_d)}]
        }
    finally:
        conn.close()


class LeaveCarryoverRequest(BaseModel):
    employee_id: int
    year: Optional[int] = None


@router.post("/leave-carryover/calculate", dependencies=[Depends(require_permission("hr.manage"))])
def calculate_leave_carryover(data: LeaveCarryoverRequest, current_user: UserResponse = Depends(get_current_user)):
    conn = get_db_connection(current_user.company_id)
    try:
        from datetime import datetime as dt
        year = data.year or (dt.now().year - 1)
        emp = conn.execute(text("""
            SELECT id, first_name||' '||last_name as name,
                   annual_leave_entitlement, leave_carryover_max
            FROM employees WHERE id=:id
        """), {"id": data.employee_id}).fetchone()
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        used = conn.execute(text("""
            SELECT COALESCE(SUM(days_requested),0) as used FROM leave_requests
            WHERE employee_id=:id AND status='approved' AND EXTRACT(YEAR FROM start_date)=:y
        """), {"id": data.employee_id, "y": year}).fetchone()
        entitled = float(emp.annual_leave_entitlement or 30)
        used_d = float(used.used or 0)
        max_carry = float(emp.leave_carryover_max or 5)
        remaining = entitled - used_d
        carried = min(max(0, remaining), max_carry)
        expired = max(0, remaining - carried)
        conn.execute(text("""
            INSERT INTO leave_carryover (employee_id,leave_type,year,entitled_days,used_days,carried_days,expired_days,max_carryover)
            VALUES (:eid,'annual',:year,:entitled,:used,:carried,:expired,:max_carry)
            ON CONFLICT (employee_id,leave_type,year) DO UPDATE SET
            entitled_days=EXCLUDED.entitled_days, used_days=EXCLUDED.used_days,
            carried_days=EXCLUDED.carried_days, expired_days=EXCLUDED.expired_days, calculated_at=NOW()
        """), {"eid": data.employee_id, "year": year, "entitled": entitled, "used": used_d,
               "carried": carried, "expired": expired, "max_carry": max_carry})
        conn.commit()
        return {"employee_id": data.employee_id, "employee_name": emp.name, "year": year,
                "entitled_days": entitled, "used_days": used_d, "carried_days": carried, "expired_days": expired}
    finally:
        conn.close()
