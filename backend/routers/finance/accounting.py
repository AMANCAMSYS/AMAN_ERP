from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db_connection
from routers.auth import get_current_user
import logging
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from utils.permissions import require_permission, validate_branch_access
from utils.audit import log_activity
from utils.accounting import get_base_currency
from fastapi import Request

from schemas.accounting import AccountCreate, FiscalYearCreate, FiscalYearClose, FiscalYearReopen
from utils.cache import cache

router = APIRouter(prefix="/accounting", tags=["المحاسبة"])
logger = logging.getLogger(__name__)

@router.get("/summary", dependencies=[Depends(require_permission("accounting.view"))])
def get_accounting_summary(
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """جلب ملخص إحصائيات المحاسبة"""
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    try:
        if branch_id:
            # Calculate branch-specific summary
            # Standard: Asset/Expense balance = Debit - Credit, Others = Credit - Debit
            # Revenue summary
            total_income = db.execute(text("""
                SELECT COALESCE(SUM(jl.credit - jl.debit), 0)
                FROM journal_lines jl
                JOIN journal_entries je ON jl.journal_entry_id = je.id
                JOIN accounts a ON jl.account_id = a.id
                WHERE a.account_type = 'revenue' AND je.branch_id = :branch_id
            """), {"branch_id": branch_id}).scalar() or 0
            
            # Expense summary
            total_expenses = db.execute(text("""
                SELECT COALESCE(SUM(jl.debit - jl.credit), 0)
                FROM journal_lines jl
                JOIN journal_entries je ON jl.journal_entry_id = je.id
                JOIN accounts a ON jl.account_id = a.id
                WHERE a.account_type = 'expense' AND je.branch_id = :branch_id
            """), {"branch_id": branch_id}).scalar() or 0
            
            # Cash/Bank summary
            # Cash/Bank summary
            # Dynamic Treasury Lookup
            treasury_ids = [row[0] for row in db.execute(text("SELECT gl_account_id FROM treasury_accounts WHERE is_active = true")).fetchall() if row[0]]
            legacy_ids = [row[0] for row in db.execute(text("SELECT id FROM accounts WHERE account_code LIKE 'BOX%' OR account_code LIKE 'BNK%'")).fetchall()]
            all_cash_ids = list(set(treasury_ids + legacy_ids))
            
            cash_balance = 0
            if all_cash_ids:
                 cash_balance = db.execute(text(f"""
                    SELECT COALESCE(SUM(jl.debit - jl.credit), 0)
                    FROM journal_lines jl
                    JOIN journal_entries je ON jl.journal_entry_id = je.id
                    JOIN accounts a ON jl.account_id = a.id
                    WHERE a.id IN ({','.join(map(str, all_cash_ids))})
                    AND je.branch_id = :branch_id
                """), {"branch_id": branch_id}).scalar() or 0
        else:
            # 1. Total Income (Revenue accounts balance)
            total_income = db.execute(text("SELECT COALESCE(SUM(balance), 0) FROM accounts WHERE account_type = 'revenue'")).scalar() or 0
            
            # 2. Total Expenses (Expense accounts balance)
            total_expenses = db.execute(text("SELECT COALESCE(SUM(balance), 0) FROM accounts WHERE account_type = 'expense'")).scalar() or 0
            
            # 3. Cash/Bank Balance (Asset accounts with BOX or BNK codes OR linked to treasury)
            # Dynamic Treasury Lookup
            treasury_ids = [row[0] for row in db.execute(text("SELECT gl_account_id FROM treasury_accounts WHERE is_active = true")).fetchall() if row[0]]
            legacy_ids = [row[0] for row in db.execute(text("SELECT id FROM accounts WHERE account_code LIKE 'BOX%' OR account_code LIKE 'BNK%'")).fetchall()]
            all_cash_ids = list(set(treasury_ids + legacy_ids))
            
            cash_balance = 0
            if all_cash_ids:
                cash_balance = db.execute(text(f"""
                    SELECT COALESCE(SUM(balance), 0) FROM accounts 
                    WHERE id IN ({','.join(map(str, all_cash_ids))})
                """)).scalar() or 0
        
        return {
            "total_income": float(total_income),
            "total_expenses": float(total_expenses),
            "net_profit": float(total_income - total_expenses),
            "cash_balance": float(cash_balance)
        }
    finally:
        db.close()

@router.get("/accounts", dependencies=[Depends(require_permission("accounting.view"))])
async def get_chart_of_accounts(
    branch_id: Optional[int] = None,
    search: Optional[str] = None,
    account_type: Optional[str] = None,
    page: Optional[int] = None,
    page_size: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Fetch all accounts for the current company, optionally filtered by branch balance"""
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    
    # Cache key for full COA structure (no filters)
    cache_key = f"chart_of_accounts:{current_user.company_id}"
    use_cache = not branch_id and not search and not account_type and page is None

    try:
        if use_cache:
            cached_coa = cache.get(cache_key)
            if cached_coa:
                return cached_coa

        # Build WHERE clauses for search and type filter
        where_extra = ""
        extra_params = {}
        
        if search:
            where_extra += " AND (a.name ILIKE :search OR a.name_en ILIKE :search OR a.account_number ILIKE :search OR a.account_code ILIKE :search)"
            extra_params["search"] = f"%{search}%"
        if account_type:
            where_extra += " AND a.account_type = :acct_type"
            extra_params["acct_type"] = account_type

        if branch_id:
            # Calculate balances specifically for the branch
            # We calculate both base balance and currency balance if it matches the account currency
            query = f"""
                SELECT 
                    a.id, a.account_number, a.account_code, a.name, a.name_en, a.account_type, a.parent_id, a.currency, a.is_active,
                    a.balance_currency as total_balance_currency,
                    CASE 
                        WHEN a.account_type IN ('asset', 'expense') THEN 
                            COALESCE(SUM(CASE WHEN je.branch_id = :branch_id THEN jl.debit - jl.credit ELSE 0 END), 0)
                        ELSE 
                            COALESCE(SUM(CASE WHEN je.branch_id = :branch_id THEN jl.credit - jl.debit ELSE 0 END), 0)
                    END as balance,
                    CASE 
                        WHEN a.currency IS NOT NULL AND a.currency != '' THEN
                            CASE 
                                WHEN a.account_type IN ('asset', 'expense') THEN 
                                    COALESCE(SUM(CASE WHEN je.branch_id = :branch_id AND jl.currency = a.currency AND jl.debit > 0 THEN jl.amount_currency ELSE 0 END), 0)
                                  - COALESCE(SUM(CASE WHEN je.branch_id = :branch_id AND jl.currency = a.currency AND jl.credit > 0 THEN jl.amount_currency ELSE 0 END), 0)
                                ELSE 
                                    COALESCE(SUM(CASE WHEN je.branch_id = :branch_id AND jl.currency = a.currency AND jl.credit > 0 THEN jl.amount_currency ELSE 0 END), 0)
                                  - COALESCE(SUM(CASE WHEN je.branch_id = :branch_id AND jl.currency = a.currency AND jl.debit > 0 THEN jl.amount_currency ELSE 0 END), 0)
                            END
                        ELSE 0
                    END as balance_currency
                FROM accounts a
                LEFT JOIN journal_lines jl ON jl.account_id = a.id
                LEFT JOIN journal_entries je ON jl.journal_entry_id = je.id
                WHERE 1=1 {where_extra}
                GROUP BY a.id, a.account_number, a.account_code, a.name, a.name_en, a.account_type, a.parent_id, a.currency, a.is_active, a.balance_currency
                ORDER BY a.account_number ASC
            """
            all_params = {"branch_id": branch_id, **extra_params}
            
            # Count total (branch case)
            count_query = f"""
                SELECT COUNT(DISTINCT a.id)
                FROM accounts a
                LEFT JOIN journal_lines jl ON jl.account_id = a.id
                LEFT JOIN journal_entries je ON jl.journal_entry_id = je.id
                WHERE 1=1 {where_extra}
            """
            total_count = db.execute(text(count_query), all_params).scalar() or 0
            
            # Add pagination
            if page is not None and page >= 1:
                query += " LIMIT :limit OFFSET :offset"
                all_params["limit"] = page_size
                all_params["offset"] = (page - 1) * page_size
                
            result = db.execute(text(query), all_params)
        else:
            query = f"""
                SELECT id, account_number, account_code, name, name_en, account_type, parent_id, balance, balance_currency, currency, is_active
                FROM accounts a
                WHERE 1=1 {where_extra}
                ORDER BY account_number ASC
            """
            
            # Count total (standard case)
            count_query = f"SELECT COUNT(*) FROM accounts a WHERE 1=1 {where_extra}"
            total_count = db.execute(text(count_query), extra_params).scalar() or 0
            
            # Add pagination
            if page is not None and page >= 1:
                query += " LIMIT :limit OFFSET :offset"
                extra_params["limit"] = page_size
                extra_params["offset"] = (page - 1) * page_size
                
            result = db.execute(text(query), extra_params)
            
        accounts = [dict(row._mapping) for row in result]
        
        # Pagination result structure
        if page is not None and page >= 1:
            return {
                "data": accounts,
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size
            }
        
        if use_cache:
            cache.set(cache_key, accounts, expire=3600)
            
        return accounts
    except Exception as e:
        logger.error(f"Error fetching accounts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="حدث خطأ أثناء جلب شجرة الحسابات"
        )
    finally:
        db.close()

@router.post("/accounts", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("accounting.edit"))])
async def create_account(
    request: Request,
    account: AccountCreate,
    current_user: dict = Depends(get_current_user)
):
    """إنشاء حساب جديد في شجرة الحسابات"""
    db = get_db_connection(current_user.company_id)
    try:
        # Check if account number already exists
        exists = db.execute(text("SELECT 1 FROM accounts WHERE account_number = :num"), {"num": account.account_number}).fetchone()
        if exists:
            raise HTTPException(status_code=400, detail="رقم الحساب موجود مسبقاً")

        # Check if account code already exists
        if account.account_code:
            code_exists = db.execute(text("SELECT 1 FROM accounts WHERE account_code = :code"), {"code": account.account_code}).fetchone()
            if code_exists:
                raise HTTPException(status_code=400, detail="كود الحساب موجود مسبقاً")

        db.execute(text("""
            INSERT INTO accounts (account_number, account_code, name, name_en, account_type, parent_id, currency, balance, is_active)
            VALUES (:num, :code, :name, :name_en, :type, :parent, :curr, 0, true)
        """), {
            "num": account.account_number,
            "code": account.account_code,
            "name": account.name,
            "name_en": account.name_en,
            "type": account.account_type,
            "parent": account.parent_id,
            "curr": account.currency
        })
        db.commit()

        # AUDIT LOG
        log_activity(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="accounting.account.create",
            resource_type="account",
            resource_id=account.account_number,
            details={"name": account.name, "type": account.account_type},
            request=request
        )

        return {"success": True, "message": "تم إنشاء الحساب بنجاح"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating account: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Invalidate cache
        try:
            cache.delete(f"chart_of_accounts:{current_user.company_id}")
        except:
            pass
        db.close()

@router.delete("/accounts/{account_id}", dependencies=[Depends(require_permission("accounting.manage"))])
async def delete_account(
    account_id: int,
    current_user: dict = Depends(get_current_user)
):
    """حذف حساب من شجرة الحسابات (بشرط عدم وجود حركات أو أبناء)"""
    db = get_db_connection(current_user.company_id)
    try:
        # 1. Check if has children
        has_children = db.execute(text("SELECT 1 FROM accounts WHERE parent_id = :id"), {"id": account_id}).fetchone()
        if has_children:
            raise HTTPException(status_code=400, detail="لا يمكن حذف الحساب لأنه يحتوي على حسابات فرعية")

        # 2. Check if has transactions (journal lines)
        has_tx = db.execute(text("SELECT 1 FROM journal_lines WHERE account_id = :id"), {"id": account_id}).fetchone()
        if has_tx:
            raise HTTPException(status_code=400, detail="لا يمكن حذف الحساب لأنه يحتوي على قيود محاسبية مسجلة")

        # 2b. Check if linked to treasury accounts
        has_treasury = db.execute(text("SELECT 1 FROM treasury_accounts WHERE gl_account_id = :id"), {"id": account_id}).fetchone()
        if has_treasury:
            raise HTTPException(status_code=400, detail="لا يمكن حذف الحساب لأنه مرتبط بحساب خزينة")

        # 2c. Check if used in budget items
        has_budget = db.execute(text("SELECT 1 FROM budget_items WHERE account_id = :id LIMIT 1"), {"id": account_id}).fetchone()
        if has_budget:
            raise HTTPException(status_code=400, detail="لا يمكن حذف الحساب لأنه مستخدم في الميزانيات")

        # 2d. Check if used in company_settings as mapped account
        has_mapping = db.execute(text("SELECT 1 FROM company_settings WHERE setting_value = :id_str AND setting_key LIKE 'acc_map_%' LIMIT 1"), {"id_str": str(account_id)}).fetchone()
        if has_mapping:
            raise HTTPException(status_code=400, detail="لا يمكن حذف الحساب لأنه معين كحساب افتراضي في الإعدادات")

        # 3. Check for balance
        balance_row = db.execute(text("SELECT balance FROM accounts WHERE id = :id"), {"id": account_id}).fetchone()
        if balance_row and abs(float(balance_row[0])) > 0.01:
            raise HTTPException(status_code=400, detail="لا يمكن حذف الحساب لأن رصيده غير صفري")

        db.execute(text("DELETE FROM accounts WHERE id = :id"), {"id": account_id})
        db.commit()
        
        # Invalidate cache
        try:
            cache.delete(f"chart_of_accounts:{current_user.company_id}")
        except:
            pass
            
        return {"success": True, "message": "تم حذف الحساب بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting account: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.put("/accounts/{account_id}", dependencies=[Depends(require_permission("accounting.edit"))])
async def update_account(
    account_id: int,
    account_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update account details"""
    db = get_db_connection(current_user.company_id)
    try:
        # Check if account exists
        existing = db.execute(text("SELECT 1 FROM accounts WHERE id = :id"), {"id": account_id}).fetchone()
        if not existing:
             raise HTTPException(status_code=404, detail="الحساب غير موجود")
        
        # Check for duplicate account_code
        new_code = account_data.get("account_code")
        if new_code:
            dup = db.execute(text("SELECT 1 FROM accounts WHERE account_code = :code AND id != :id"), {"code": new_code, "id": account_id}).fetchone()
            if dup:
                raise HTTPException(status_code=400, detail=f"رمز الحساب '{new_code}' مستخدم بالفعل")
             
        db.execute(text("""
            UPDATE accounts 
            SET name = :name, name_en = :name_en, account_code = :code
            WHERE id = :id
        """), {
            "name": account_data.get("name"),
            "name_en": account_data.get("name_en"),
            "code": new_code,
            "id": account_id
        })
        db.commit()
        
        # Invalidate cache
        try:
            cache.delete(f"chart_of_accounts:{current_user.company_id}")
        except:
            pass
            
        return {"success": True, "message": "تم تحديث الحساب بنجاح"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating account: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.post("/journal-entries", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("accounting.edit"))])
async def create_journal_entry(
    request: Request,
    entry_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new journal entry (Manual Entry)
    entry_data format:
    {
        "date": "2023-10-01",
        "description": "Opening Balance / Expense Payment",
        "reference": "REF123",
        "status": "posted" or "draft",   <-- NEW: defaults to "posted"
        "lines": [
            {"account_id": 1, "debit": 100, "credit": 0, "description": "Line desc", "cost_center_id": 5},
            {"account_id": 2, "debit": 0, "credit": 100, "description": "Line desc"}
        ]
    }
    """
    db = get_db_connection(current_user.company_id)
    try:
        # 1. Validation
        if "lines" not in entry_data or not entry_data["lines"]:
            raise HTTPException(status_code=400, detail="يجب إضافة سطر واحد على الأقل في القيد")

        for i, line in enumerate(entry_data["lines"]):
            d = float(line.get("debit", 0))
            c = float(line.get("credit", 0))
            if d < 0 or c < 0:
                raise HTTPException(status_code=400, detail=f"السطر {i+1}: لا يمكن إدخال مبالغ سالبة")
            if d > 0 and c > 0:
                raise HTTPException(status_code=400, detail=f"السطر {i+1}: لا يمكن أن يكون مدين ودائن معاً في نفس السطر")

        total_debit = sum(float(line.get("debit", 0)) for line in entry_data["lines"])
        total_credit = sum(float(line.get("credit", 0)) for line in entry_data["lines"])
        
        if total_debit == 0 and total_credit == 0:
            raise HTTPException(status_code=400, detail="لا يمكن إنشاء قيد بمبالغ صفرية")

        if abs(total_debit - total_credit) > 0.01:
             raise HTTPException(status_code=400, detail="القيود غير موزونة (المدين لا يساوي الدائن)")

        # Determine entry status (draft or posted)
        entry_status = entry_data.get("status", "posted")
        if entry_status not in ("draft", "posted"):
            entry_status = "posted"

        # 1b. Closed Period Check (only for posted entries)
        entry_date = entry_data.get("date")
        if entry_date and entry_status == "posted":
            closed_period = db.execute(text("""
                SELECT 1 FROM fiscal_periods 
                WHERE :entry_date BETWEEN start_date AND end_date 
                AND is_closed = TRUE
                LIMIT 1
            """), {"entry_date": entry_date}).fetchone()
            if closed_period:
                raise HTTPException(status_code=400, detail="لا يمكن ترحيل قيود في فترة محاسبية مغلقة")

        # 2. Create Header
        from utils.accounting import generate_sequential_number
        entry_number = generate_sequential_number(db, "JE", "journal_entries", "entry_number")
        
        # Get Company Base Currency
        base_currency_row = db.execute(text("SELECT code FROM currencies WHERE is_base = TRUE LIMIT 1")).fetchone()
        if not base_currency_row:
             base_currency_row = db.execute(text("SELECT setting_value as code FROM company_settings WHERE setting_key = 'default_currency'")).fetchone()
        base_currency = base_currency_row[0] if base_currency_row else "SYP"

        currency = entry_data.get("currency", base_currency)
        exchange_rate = float(entry_data.get("exchange_rate", 1.0))
        
        journal_res = db.execute(text("""
            INSERT INTO journal_entries (entry_number, entry_date, description, reference, status, branch_id, created_by, currency, exchange_rate, posted_at)
            VALUES (:num, :date, :desc, :ref, :status, :branch_id, :user, :curr, :rate, :posted_at)
            RETURNING id
        """), {
            "num": entry_number,
            "date": entry_data["date"],
            "desc": entry_data["description"],
            "ref": entry_data.get("reference"),
            "status": entry_status,
            "branch_id": entry_data.get("branch_id"),
            "user": current_user.id,
            "curr": currency,
            "rate": exchange_rate,
            "posted_at": datetime.now() if entry_status == "posted" else None
        }).fetchone()
        
        journal_id = journal_res.id

        # 3. Create Lines and Update Balances (only if posted)
        for line in entry_data["lines"]:
            input_debit = float(line.get("debit", 0))
            input_credit = float(line.get("credit", 0))
            
            debit_base = input_debit * exchange_rate
            credit_base = input_credit * exchange_rate
            
            account_id = line["account_id"]
            
            line_currency = line.get("currency") or currency
            
            if line.get("amount_currency"):
                line_amount_currency = float(line["amount_currency"])
            else:
                line_amount_currency = input_debit + input_credit

            db.execute(text("""
                INSERT INTO journal_lines (
                    journal_entry_id, account_id, debit, credit, description, 
                    cost_center_id, amount_currency, currency
                )
                VALUES (:jid, :aid, :deb, :cred, :desc, :cc_id, :amt_curr, :curr)
            """), {
                "jid": journal_id,
                "aid": account_id,
                "deb": debit_base,
                "cred": credit_base,
                "desc": line.get("description", entry_data["description"]),
                "cc_id": line.get("cost_center_id"),
                "amt_curr": line_amount_currency,
                "curr": line_currency
            })
            
            # Update Account Balances ONLY if posting immediately
            if entry_status == "posted":
                from utils.accounting import update_account_balance
                update_account_balance(
                    db, 
                    account_id=account_id, 
                    debit_base=debit_base, 
                    credit_base=credit_base, 
                    debit_curr=input_debit, 
                    credit_curr=input_credit, 
                    currency=line_currency
                )

        db.commit()

        # AUDIT LOG
        log_activity(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action=f"accounting.journal.{'create' if entry_status == 'posted' else 'draft'}",
            resource_type="journal_entry",
            resource_id=entry_number,
            details={"description": entry_data["description"], "reference": entry_data.get("reference"), "status": entry_status},
            request=request,
            branch_id=entry_data.get("branch_id")
        )

        msg = "تم ترحيل القيد بنجاح" if entry_status == "posted" else "تم حفظ القيد كمسودة"
        return {"success": True, "message": msg, "entry_number": entry_number, "entry_id": journal_id, "status": entry_status}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating journal: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()



# ============================================================
# Journal Entries Listing & Draft Workflow (ACC-002)
# ============================================================

@router.get("/journal-entries", dependencies=[Depends(require_permission("accounting.view"))])
def list_journal_entries(
    status_filter: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """قائمة القيود اليومية مع فلترة"""
    db = get_db_connection(current_user.company_id)
    try:
        conditions = []
        params = {}

        if status_filter and status_filter in ('draft', 'posted', 'voided'):
            conditions.append("je.status = :status")
            params["status"] = status_filter

        if date_from:
            conditions.append("je.entry_date >= :date_from")
            params["date_from"] = date_from
        if date_to:
            conditions.append("je.entry_date <= :date_to")
            params["date_to"] = date_to

        if search:
            conditions.append("(je.entry_number ILIKE :search OR je.description ILIKE :search OR je.reference ILIKE :search)")
            params["search"] = f"%{search}%"

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Count
        total = db.execute(text(f"""
            SELECT COUNT(*) FROM journal_entries je WHERE {where_clause}
        """), params).scalar()

        # Fetch
        offset = (page - 1) * limit
        params["limit"] = limit
        params["offset"] = offset

        rows = db.execute(text(f"""
            SELECT je.*,
                   cu.username AS created_by_name,
                   COALESCE(SUM(jl.debit), 0) AS total_debit,
                   COALESCE(SUM(jl.credit), 0) AS total_credit,
                   COUNT(jl.id) AS line_count
            FROM journal_entries je
            LEFT JOIN company_users cu ON je.created_by = cu.id
            LEFT JOIN journal_lines jl ON jl.journal_entry_id = je.id
            WHERE {where_clause}
            GROUP BY je.id, cu.username
            ORDER BY je.entry_date DESC, je.id DESC
            LIMIT :limit OFFSET :offset
        """), params).fetchall()

        entries = []
        for r in rows:
            entries.append({
                "id": r.id,
                "entry_number": r.entry_number,
                "entry_date": str(r.entry_date),
                "description": r.description,
                "reference": r.reference,
                "status": r.status,
                "currency": r.currency,
                "exchange_rate": float(r.exchange_rate) if r.exchange_rate else 1.0,
                "total_debit": float(r.total_debit),
                "total_credit": float(r.total_credit),
                "line_count": r.line_count,
                "created_by": r.created_by,
                "created_by_name": r.created_by_name,
                "created_at": str(r.created_at) if r.created_at else None,
                "posted_at": str(r.posted_at) if r.posted_at else None,
            })

        return {
            "items": entries,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    finally:
        db.close()


@router.get("/journal-entries/{entry_id}", dependencies=[Depends(require_permission("accounting.view"))])
def get_journal_entry(
    entry_id: int,
    current_user: dict = Depends(get_current_user)
):
    """جلب تفاصيل قيد يومي"""
    db = get_db_connection(current_user.company_id)
    try:
        entry = db.execute(text("""
            SELECT je.*, cu.username AS created_by_name
            FROM journal_entries je
            LEFT JOIN company_users cu ON je.created_by = cu.id
            WHERE je.id = :id
        """), {"id": entry_id}).fetchone()
        if not entry:
            raise HTTPException(status_code=404, detail="القيد غير موجود")

        lines = db.execute(text("""
            SELECT jl.*, a.account_number, a.name AS account_name, a.name_en AS account_name_en
            FROM journal_lines jl
            JOIN accounts a ON jl.account_id = a.id
            WHERE jl.journal_entry_id = :id
            ORDER BY jl.id
        """), {"id": entry_id}).fetchall()

        return {
            "id": entry.id,
            "entry_number": entry.entry_number,
            "entry_date": str(entry.entry_date),
            "description": entry.description,
            "reference": entry.reference,
            "status": entry.status,
            "currency": entry.currency,
            "exchange_rate": float(entry.exchange_rate) if entry.exchange_rate else 1.0,
            "branch_id": entry.branch_id,
            "created_by": entry.created_by,
            "created_by_name": entry.created_by_name,
            "created_at": str(entry.created_at) if entry.created_at else None,
            "posted_at": str(entry.posted_at) if entry.posted_at else None,
            "lines": [{
                "id": l.id,
                "account_id": l.account_id,
                "account_number": l.account_number,
                "account_name": l.account_name,
                "account_name_en": l.account_name_en,
                "debit": float(l.debit),
                "credit": float(l.credit),
                "description": l.description,
                "currency": l.currency,
                "amount_currency": float(l.amount_currency) if l.amount_currency else 0,
                "cost_center_id": l.cost_center_id,
            } for l in lines]
        }
    finally:
        db.close()


@router.post("/journal-entries/{entry_id}/post", dependencies=[Depends(require_permission("accounting.manage"))])
async def post_journal_entry(
    entry_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """اعتماد وترحيل قيد مسودة"""
    db = get_db_connection(current_user.company_id)
    try:
        entry = db.execute(text("SELECT * FROM journal_entries WHERE id = :id"), {"id": entry_id}).fetchone()
        if not entry:
            raise HTTPException(status_code=404, detail="القيد غير موجود")
        if entry.status != 'draft':
            raise HTTPException(status_code=400, detail=f"القيد بحالة '{entry.status}' ولا يمكن ترحيله")

        # Closed period check
        if entry.entry_date:
            closed_period = db.execute(text("""
                SELECT 1 FROM fiscal_periods
                WHERE :entry_date BETWEEN start_date AND end_date
                AND is_closed = TRUE LIMIT 1
            """), {"entry_date": entry.entry_date}).fetchone()
            if closed_period:
                raise HTTPException(status_code=400, detail="لا يمكن ترحيل قيود في فترة محاسبية مغلقة")

        # Get lines and update account balances
        lines = db.execute(text("""
            SELECT account_id, debit, credit, currency, amount_currency FROM journal_lines
            WHERE journal_entry_id = :id
        """), {"id": entry_id}).fetchall()

        # Get the exchange rate from the journal entry
        je_rate = float(entry.exchange_rate or 1.0)

        from utils.accounting import update_account_balance
        for line in lines:
            debit_base = float(line.debit)
            credit_base = float(line.credit)
            # Reverse the base amounts to get original currency amounts
            if je_rate != 0:
                debit_curr = debit_base / je_rate
                credit_curr = credit_base / je_rate
            else:
                debit_curr = debit_base
                credit_curr = credit_base
            update_account_balance(
                db,
                account_id=line.account_id,
                debit_base=debit_base,
                credit_base=credit_base,
                debit_curr=debit_curr,
                credit_curr=credit_curr,
                currency=line.currency
            )

        # Update status to posted
        db.execute(text("""
            UPDATE journal_entries SET status = 'posted', posted_at = NOW()
            WHERE id = :id
        """), {"id": entry_id})

        db.commit()

        log_activity(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="accounting.journal.post",
            resource_type="journal_entry",
            resource_id=entry.entry_number,
            details={"description": entry.description},
            request=request,
            branch_id=entry.branch_id
        )

        return {"success": True, "message": "تم ترحيل القيد بنجاح", "entry_number": entry.entry_number}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error posting journal entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/journal-entries/{entry_id}/void", dependencies=[Depends(require_permission("accounting.manage"))])
async def void_journal_entry(
    entry_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    إلغاء (عكس) قيد يومي منشور.
    ينشئ قيد عكسي بنفس المبالغ لإلغاء الأثر المحاسبي.
    """
    db = get_db_connection(current_user.company_id)
    try:
        # 1. Get original entry
        original = db.execute(text("""
            SELECT * FROM journal_entries WHERE id = :id
        """), {"id": entry_id}).fetchone()
        
        if not original:
            raise HTTPException(status_code=404, detail="القيد غير موجود")
        
        if original.status == 'voided':
            raise HTTPException(status_code=400, detail="القيد ملغى بالفعل")
        
        # 2. Get original lines
        lines = db.execute(text("""
            SELECT account_id, debit, credit, description, amount_currency, currency, cost_center_id
            FROM journal_lines WHERE journal_entry_id = :id
        """), {"id": entry_id}).fetchall()
        
        if not lines:
            raise HTTPException(status_code=400, detail="القيد لا يحتوي على أسطر")
        
        # 3. Create reversal entry
        from utils.accounting import generate_sequential_number
        rev_num = f"REV-{original.entry_number}"
        
        rev_id = db.execute(text("""
            INSERT INTO journal_entries (
                entry_number, entry_date, description, reference, status, 
                branch_id, created_by, currency, exchange_rate
            ) VALUES (
                :num, CURRENT_DATE, :desc, :ref, 'posted', 
                :bid, :uid, :curr, :rate
            ) RETURNING id
        """), {
            "num": rev_num,
            "desc": f"عكس قيد: {original.description}",
            "ref": original.entry_number,
            "bid": original.branch_id,
            "uid": current_user.id,
            "curr": original.currency,
            "rate": original.exchange_rate
        }).scalar()
        
        # 4. Create reversed lines (swap debit/credit) and reverse balances
        from utils.accounting import update_account_balance
        
        for line in lines:
            # Insert reversed line
            db.execute(text("""
                INSERT INTO journal_lines (
                    journal_entry_id, account_id, debit, credit, description,
                    amount_currency, currency, cost_center_id
                ) VALUES (:jid, :aid, :deb, :cred, :desc, :amt_curr, :curr, :cc)
            """), {
                "jid": rev_id,
                "aid": line.account_id,
                "deb": float(line.credit),   # Swap: original credit becomes debit
                "cred": float(line.debit),   # Swap: original debit becomes credit
                "desc": f"عكس: {line.description or ''}",
                "amt_curr": float(line.amount_currency or 0),
                "curr": line.currency,
                "cc": line.cost_center_id
            })
            
            # Reverse balance: original was (debit, credit), reversal is (credit, debit)
            je_rate = float(original.exchange_rate or 1.0)
            debit_base = float(line.credit)
            credit_base = float(line.debit)
            if je_rate != 0:
                debit_curr = debit_base / je_rate
                credit_curr = credit_base / je_rate
            else:
                debit_curr = debit_base
                credit_curr = credit_base
            update_account_balance(
                db, 
                account_id=line.account_id,
                debit_base=debit_base,
                credit_base=credit_base,
                debit_curr=debit_curr,
                credit_curr=credit_curr,
                currency=line.currency
            )
        
        # 5. Mark original as voided
        db.execute(text("""
            UPDATE journal_entries SET status = 'voided' WHERE id = :id
        """), {"id": entry_id})
        
        db.commit()
        
        log_activity(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="accounting.journal.void",
            resource_type="journal_entry",
            resource_id=str(entry_id),
            details={"original_entry": original.entry_number, "reversal_entry": rev_num},
            request=request,
            branch_id=original.branch_id
        )
        
        return {
            "success": True, 
            "message": "تم إلغاء القيد بنجاح وإنشاء قيد عكسي",
            "reversal_entry_id": rev_id,
            "reversal_entry_number": rev_num
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error voiding journal entry: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ============================================================
# Fiscal Year Management & Year-End Closing (ACC-001)
# ============================================================

def _generate_sequential_number(db, prefix: str, table: str, column: str) -> str:
    """Generate sequential number like JE-2025-00001."""
    last = db.execute(text(f"""
        SELECT {column} FROM {table}
        WHERE {column} LIKE :prefix
        ORDER BY {column} DESC LIMIT 1
    """), {"prefix": f"{prefix}%"}).scalar()
    if last:
        try:
            num = int(last.split('-')[-1]) + 1
        except (ValueError, IndexError):
            num = 1
    else:
        num = 1
    return f"{prefix}-{num:05d}"


@router.get("/fiscal-years", dependencies=[Depends(require_permission("accounting.view"))])
def list_fiscal_years(current_user: dict = Depends(get_current_user)):
    """قائمة السنوات المالية"""
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(text("""
            SELECT fy.*,
                   cu_closed.username AS closed_by_name,
                   cu_reopened.username AS reopened_by_name,
                   a.name AS retained_earnings_account_name,
                   a.account_number AS retained_earnings_account_number,
                   (SELECT COUNT(*) FROM fiscal_periods fp WHERE fp.fiscal_year = fy.year) AS period_count,
                   (SELECT COUNT(*) FROM fiscal_periods fp WHERE fp.fiscal_year = fy.year AND fp.is_closed = TRUE) AS closed_period_count
            FROM fiscal_years fy
            LEFT JOIN company_users cu_closed ON fy.closed_by = cu_closed.id
            LEFT JOIN company_users cu_reopened ON fy.reopened_by = cu_reopened.id
            LEFT JOIN accounts a ON fy.retained_earnings_account_id = a.id
            ORDER BY fy.year DESC
        """)).fetchall()

        result = []
        for r in rows:
            result.append({
                "id": r.id,
                "year": r.year,
                "start_date": str(r.start_date),
                "end_date": str(r.end_date),
                "status": r.status,
                "retained_earnings_account_id": r.retained_earnings_account_id,
                "retained_earnings_account_name": r.retained_earnings_account_name,
                "retained_earnings_account_number": r.retained_earnings_account_number,
                "closing_entry_id": r.closing_entry_id,
                "closed_by": r.closed_by,
                "closed_by_name": r.closed_by_name,
                "closed_at": str(r.closed_at) if r.closed_at else None,
                "reopened_by": r.reopened_by,
                "reopened_by_name": r.reopened_by_name,
                "reopened_at": str(r.reopened_at) if r.reopened_at else None,
                "period_count": r.period_count,
                "closed_period_count": r.closed_period_count,
            })
        return result
    finally:
        db.close()


@router.post("/fiscal-years", dependencies=[Depends(require_permission("accounting.manage"))])
def create_fiscal_year(
    data: FiscalYearCreate,
    current_user: dict = Depends(get_current_user)
):
    """إنشاء سنة مالية جديدة"""
    db = get_db_connection(current_user.company_id)
    try:
        # Check duplicate
        existing = db.execute(text("SELECT 1 FROM fiscal_years WHERE year = :y"), {"y": data.year}).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail=f"السنة المالية {data.year} موجودة بالفعل")

        # Find retained earnings account if not specified
        re_account_id = data.retained_earnings_account_id
        if not re_account_id:
            re_acc = db.execute(text("""
                SELECT id FROM accounts
                WHERE account_type = 'equity'
                  AND (account_code = 'RET' OR account_number = '32'
                       OR LOWER(name_en) LIKE '%retained%earnings%')
                LIMIT 1
            """)).fetchone()
            if re_acc:
                re_account_id = re_acc.id

        result = db.execute(text("""
            INSERT INTO fiscal_years (year, start_date, end_date, retained_earnings_account_id)
            VALUES (:year, :start, :end, :re_acc)
            RETURNING id
        """), {
            "year": data.year,
            "start": data.start_date,
            "end": data.end_date,
            "re_acc": re_account_id
        })
        fy_id = result.scalar()

        # Auto-create 12 monthly fiscal periods if none exist for this year
        period_count = db.execute(text(
            "SELECT COUNT(*) FROM fiscal_periods WHERE fiscal_year = :y"
        ), {"y": data.year}).scalar()

        if period_count == 0:
            months_ar = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
                         "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
            for m in range(1, 13):
                import calendar
                start_d = date(data.year, m, 1)
                last_day = calendar.monthrange(data.year, m)[1]
                end_d = date(data.year, m, last_day)
                # Only create if within fiscal year range
                if end_d >= data.start_date and start_d <= data.end_date:
                    db.execute(text("""
                        INSERT INTO fiscal_periods (name, start_date, end_date, fiscal_year, fiscal_year_id, is_closed)
                        VALUES (:name, :start, :end, :year, :fy_id, false)
                    """), {
                        "name": f"{months_ar[m-1]} {data.year}",
                        "start": start_d,
                        "end": end_d,
                        "year": data.year,
                        "fy_id": fy_id
                    })

        db.commit()

        log_activity(db, user_id=current_user.id, username=current_user.username,
                     action="accounting.fiscal_year.create",
                     resource_type="fiscal_year", resource_id=str(fy_id),
                     details={"year": data.year})

        return {"success": True, "id": fy_id, "message": f"تم إنشاء السنة المالية {data.year}"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating fiscal year: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/fiscal-years/{year}/preview-closing", dependencies=[Depends(require_permission("accounting.manage"))])
def preview_year_end_closing(
    year: int,
    current_user: dict = Depends(get_current_user)
):
    """معاينة قيد الإقفال قبل التنفيذ - عرض الإيرادات والمصاريف"""
    db = get_db_connection(current_user.company_id)
    try:
        # Get fiscal year
        fy = db.execute(text("SELECT * FROM fiscal_years WHERE year = :y"), {"y": year}).fetchone()
        if not fy:
            raise HTTPException(status_code=404, detail=f"السنة المالية {year} غير موجودة")
        if fy.status == 'closed':
            raise HTTPException(status_code=400, detail=f"السنة المالية {year} مقفلة بالفعل")

        # Get all revenue accounts with their balances for this year
        revenue_accounts = db.execute(text("""
            SELECT a.id, a.account_number, a.name, a.name_en,
                   COALESCE(SUM(jl.credit - jl.debit), 0) AS balance
            FROM accounts a
            JOIN journal_lines jl ON jl.account_id = a.id
            JOIN journal_entries je ON jl.journal_entry_id = je.id
            WHERE a.account_type = 'revenue'
            AND je.entry_date BETWEEN :start AND :end
            AND je.status = 'posted'
            GROUP BY a.id, a.account_number, a.name, a.name_en
            HAVING COALESCE(SUM(jl.credit - jl.debit), 0) != 0
            ORDER BY a.account_number
        """), {"start": fy.start_date, "end": fy.end_date}).fetchall()

        # Get all expense accounts with their balances for this year
        expense_accounts = db.execute(text("""
            SELECT a.id, a.account_number, a.name, a.name_en,
                   COALESCE(SUM(jl.debit - jl.credit), 0) AS balance
            FROM accounts a
            JOIN journal_lines jl ON jl.account_id = a.id
            JOIN journal_entries je ON jl.journal_entry_id = je.id
            WHERE a.account_type = 'expense'
            AND je.entry_date BETWEEN :start AND :end
            AND je.status = 'posted'
            GROUP BY a.id, a.account_number, a.name, a.name_en
            HAVING COALESCE(SUM(jl.debit - jl.credit), 0) != 0
            ORDER BY a.account_number
        """), {"start": fy.start_date, "end": fy.end_date}).fetchall()

        total_revenue = sum(float(r.balance) for r in revenue_accounts)
        total_expenses = sum(float(r.balance) for r in expense_accounts)
        net_income = total_revenue - total_expenses

        # Get retained earnings account
        re_acc = None
        if fy.retained_earnings_account_id:
            re_acc = db.execute(text(
                "SELECT id, account_number, name, name_en FROM accounts WHERE id = :id"
            ), {"id": fy.retained_earnings_account_id}).fetchone()

        return {
            "year": year,
            "start_date": str(fy.start_date),
            "end_date": str(fy.end_date),
            "revenue_accounts": [
                {"id": r.id, "account_number": r.account_number, "name": r.name,
                 "name_en": r.name_en, "balance": float(r.balance)}
                for r in revenue_accounts
            ],
            "expense_accounts": [
                {"id": r.id, "account_number": r.account_number, "name": r.name,
                 "name_en": r.name_en, "balance": float(r.balance)}
                for r in expense_accounts
            ],
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "net_income": net_income,
            "retained_earnings_account": {
                "id": re_acc.id, "account_number": re_acc.account_number,
                "name": re_acc.name, "name_en": re_acc.name_en
            } if re_acc else None,
            "result_type": "profit" if net_income >= 0 else "loss"
        }
    finally:
        db.close()


@router.post("/fiscal-years/{year}/close", dependencies=[Depends(require_permission("accounting.manage"))])
def close_fiscal_year(
    year: int,
    data: FiscalYearClose = FiscalYearClose(),
    current_user: dict = Depends(get_current_user)
):
    """إقفال السنة المالية - ترحيل الأرباح/الخسائر إلى حقوق الملكية"""
    db = get_db_connection(current_user.company_id)
    try:
        # 1. Validate fiscal year exists and is open
        fy = db.execute(text("SELECT * FROM fiscal_years WHERE year = :y"), {"y": year}).fetchone()
        if not fy:
            raise HTTPException(status_code=404, detail=f"السنة المالية {year} غير موجودة")
        if fy.status == 'closed':
            raise HTTPException(status_code=400, detail=f"السنة المالية {year} مقفلة بالفعل")

        # 2. Determine retained earnings account
        re_account_id = data.retained_earnings_account_id or fy.retained_earnings_account_id
        if not re_account_id:
            re_acc = db.execute(text("""
                SELECT id FROM accounts
                WHERE account_type = 'equity'
                  AND (account_code = 'RET' OR account_number = '32'
                       OR LOWER(name_en) LIKE '%retained%earnings%')
                LIMIT 1
            """)).fetchone()
            if re_acc:
                re_account_id = re_acc.id
            else:
                raise HTTPException(status_code=400,
                    detail="لم يتم العثور على حساب الأرباح المبقاة. يرجى تحديده يدوياً")

        # 3. Calculate total revenue and expenses for the year
        revenue_data = db.execute(text("""
            SELECT a.id, COALESCE(SUM(jl.credit - jl.debit), 0) AS balance
            FROM accounts a
            JOIN journal_lines jl ON jl.account_id = a.id
            JOIN journal_entries je ON jl.journal_entry_id = je.id
            WHERE a.account_type = 'revenue'
              AND je.entry_date BETWEEN :start AND :end
              AND je.status = 'posted'
            GROUP BY a.id
            HAVING COALESCE(SUM(jl.credit - jl.debit), 0) != 0
        """), {"start": fy.start_date, "end": fy.end_date}).fetchall()

        expense_data = db.execute(text("""
            SELECT a.id, COALESCE(SUM(jl.debit - jl.credit), 0) AS balance
            FROM accounts a
            JOIN journal_lines jl ON jl.account_id = a.id
            JOIN journal_entries je ON jl.journal_entry_id = je.id
            WHERE a.account_type = 'expense'
              AND je.entry_date BETWEEN :start AND :end
              AND je.status = 'posted'
            GROUP BY a.id
            HAVING COALESCE(SUM(jl.debit - jl.credit), 0) != 0
        """), {"start": fy.start_date, "end": fy.end_date}).fetchall()

        total_revenue = sum(float(r.balance) for r in revenue_data)
        total_expenses = sum(float(r.balance) for r in expense_data)
        net_income = round(total_revenue - total_expenses, 4)

        if not revenue_data and not expense_data:
            raise HTTPException(status_code=400,
                detail="لا توجد حركات إيرادات أو مصاريف لهذه السنة المالية")

        # 4. Create the closing journal entry
        entry_num = _generate_sequential_number(db, f"CLS-{year}", "journal_entries", "entry_number")

        entry_id = db.execute(text("""
            INSERT INTO journal_entries (
                entry_number, entry_date, reference, description,
                status, created_by, posted_at
            ) VALUES (
                :num, :edate, :ref, :desc,
                'posted', :user, NOW()
            ) RETURNING id
        """), {
            "num": entry_num,
            "edate": fy.end_date,
            "ref": f"Year-End Closing {year}",
            "desc": f"قيد إقفال السنة المالية {year} - ترحيل صافي {'الربح' if net_income >= 0 else 'الخسارة'} إلى الأرباح المبقاة",
            "user": current_user.id
        }).scalar()

        # 5. Create closing lines - use update_account_balance for proper sign handling
        from utils.accounting import update_account_balance as _uab_fy

        # A) Close revenue accounts (debit revenue to zero it out)
        for rev in revenue_data:
            balance = float(rev.balance)
            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                VALUES (:je, :acc, :debit, :credit, :desc)
            """), {
                "je": entry_id, "acc": rev.id,
                "debit": abs(balance), "credit": 0,
                "desc": f"إقفال حساب إيرادات - {year}"
            })
            _uab_fy(db, account_id=rev.id, debit_base=abs(balance), credit_base=0)

        # B) Close expense accounts (credit expense to zero it out)
        for exp in expense_data:
            balance = float(exp.balance)
            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                VALUES (:je, :acc, :debit, :credit, :desc)
            """), {
                "je": entry_id, "acc": exp.id,
                "debit": 0, "credit": abs(balance),
                "desc": f"إقفال حساب مصاريف - {year}"
            })
            _uab_fy(db, account_id=exp.id, debit_base=0, credit_base=abs(balance))

        # C) Transfer net income to retained earnings
        if net_income >= 0:
            # Profit → Credit retained earnings
            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                VALUES (:je, :acc, 0, :amt, :desc)
            """), {
                "je": entry_id, "acc": re_account_id,
                "amt": abs(net_income),
                "desc": f"ترحيل صافي ربح {year} إلى الأرباح المبقاة"
            })
            _uab_fy(db, account_id=re_account_id, debit_base=0, credit_base=abs(net_income))
        else:
            # Loss → Debit retained earnings
            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                VALUES (:je, :acc, :amt, 0, :desc)
            """), {
                "je": entry_id, "acc": re_account_id,
                "amt": abs(net_income),
                "desc": f"ترحيل صافي خسارة {year} إلى الأرباح المبقاة"
            })
            _uab_fy(db, account_id=re_account_id, debit_base=abs(net_income), credit_base=0)

        # 6. Close fiscal periods for this year (if requested)
        closed_periods = 0
        if data.close_periods:
            closed_periods = db.execute(text("""
                UPDATE fiscal_periods
                SET is_closed = TRUE, closed_by = :user, closed_at = NOW()
                WHERE fiscal_year = :year AND is_closed = FALSE
            """), {"year": year, "user": current_user.id}).rowcount

        # 7. Mark fiscal year as closed
        db.execute(text("""
            UPDATE fiscal_years
            SET status = 'closed',
                closing_entry_id = :entry_id,
                retained_earnings_account_id = :re_acc,
                closed_by = :user,
                closed_at = NOW()
            WHERE year = :year
        """), {
            "entry_id": entry_id,
            "re_acc": re_account_id,
            "user": current_user.id,
            "year": year
        })

        db.commit()

        log_activity(db, user_id=current_user.id, username=current_user.username,
                     action="accounting.fiscal_year.close",
                     resource_type="fiscal_year", resource_id=str(fy.id),
                     details={"year": year, "net_income": float(net_income)})

        return {
            "success": True,
            "message": f"تم إقفال السنة المالية {year} بنجاح",
            "closing_entry_id": entry_id,
            "closing_entry_number": entry_num,
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "net_income": net_income,
            "result_type": "profit" if net_income >= 0 else "loss",
            "closed_periods": closed_periods
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error closing fiscal year {year}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/fiscal-years/{year}/reopen", dependencies=[Depends(require_permission("accounting.manage"))])
def reopen_fiscal_year(
    year: int,
    data: FiscalYearReopen = FiscalYearReopen(),
    current_user: dict = Depends(get_current_user)
):
    """إعادة فتح سنة مالية مقفلة - عكس قيد الإقفال"""
    db = get_db_connection(current_user.company_id)
    try:
        # 1. Validate
        fy = db.execute(text("SELECT * FROM fiscal_years WHERE year = :y"), {"y": year}).fetchone()
        if not fy:
            raise HTTPException(status_code=404, detail=f"السنة المالية {year} غير موجودة")
        if fy.status != 'closed':
            raise HTTPException(status_code=400, detail=f"السنة المالية {year} ليست مقفلة")

        # 2. Reverse the closing journal entry
        if fy.closing_entry_id:
            closing_lines = db.execute(text("""
                SELECT account_id, debit, credit FROM journal_lines
                WHERE journal_entry_id = :id
            """), {"id": fy.closing_entry_id}).fetchall()

            # Create reversal entry
            rev_num = _generate_sequential_number(db, f"RCLS-{year}", "journal_entries", "entry_number")
            rev_id = db.execute(text("""
                INSERT INTO journal_entries (
                    entry_number, entry_date, reference, description,
                    status, created_by, posted_at
                ) VALUES (
                    :num, :edate, :ref, :desc,
                    'posted', :user, NOW()
                ) RETURNING id
            """), {
                "num": rev_num,
                "edate": fy.end_date,
                "ref": f"Reversal of Year-End Closing {year}",
                "desc": f"عكس قيد إقفال السنة المالية {year}" + (f" - {data.reason}" if data.reason else ""),
                "user": current_user.id
            }).scalar()

            # Reverse each line (swap debit/credit) and reverse balance impact
            from utils.accounting import update_account_balance as _uab_rev
            for line in closing_lines:
                rev_debit = float(line.credit)
                rev_credit = float(line.debit)
                db.execute(text("""
                    INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                    VALUES (:je, :acc, :debit, :credit, :desc)
                """), {
                    "je": rev_id, "acc": line.account_id,
                    "debit": rev_debit, "credit": rev_credit,
                    "desc": f"عكس إقفال {year}"
                })

                # Reverse account balance using proper helper
                _uab_rev(db, account_id=line.account_id,
                         debit_base=rev_debit, credit_base=rev_credit)

            # Mark original closing entry as voided
            db.execute(text("""
                UPDATE journal_entries SET status = 'voided' WHERE id = :id
            """), {"id": fy.closing_entry_id})

        # 3. Reopen fiscal periods
        db.execute(text("""
            UPDATE fiscal_periods
            SET is_closed = FALSE, closed_by = NULL, closed_at = NULL
            WHERE fiscal_year = :year
        """), {"year": year})

        # 4. Update fiscal year status
        db.execute(text("""
            UPDATE fiscal_years
            SET status = 'open',
                closing_entry_id = NULL,
                reopened_by = :user,
                reopened_at = NOW()
            WHERE year = :year
        """), {"user": current_user.id, "year": year})

        db.commit()

        log_activity(db, user_id=current_user.id, username=current_user.username,
                     action="accounting.fiscal_year.reopen",
                     resource_type="fiscal_year", resource_id=str(fy.id),
                     details={"year": year, "reason": data.reason})

        return {
            "success": True,
            "message": f"تم إعادة فتح السنة المالية {year}",
            "reversal_entry_id": rev_id if fy.closing_entry_id else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error reopening fiscal year {year}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/fiscal-years/{year}/periods", dependencies=[Depends(require_permission("accounting.view"))])
def list_fiscal_periods(
    year: int,
    current_user: dict = Depends(get_current_user)
):
    """جلب الفترات المحاسبية لسنة مالية"""
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(text("""
            SELECT fp.*,
                   cu.username AS closed_by_name,
                   (SELECT COUNT(*) FROM journal_entries je
                    WHERE je.entry_date BETWEEN fp.start_date AND fp.end_date
                    AND je.status = 'posted') AS entry_count
            FROM fiscal_periods fp
            LEFT JOIN company_users cu ON fp.closed_by = cu.id
            WHERE fp.fiscal_year = :year
            ORDER BY fp.start_date
        """), {"year": year}).fetchall()

        return [{
            "id": r.id,
            "name": r.name,
            "start_date": str(r.start_date),
            "end_date": str(r.end_date),
            "is_closed": r.is_closed,
            "closed_by": r.closed_by,
            "closed_by_name": r.closed_by_name,
            "closed_at": str(r.closed_at) if r.closed_at else None,
            "entry_count": r.entry_count,
        } for r in rows]
    finally:
        db.close()


@router.post("/fiscal-periods/{period_id}/toggle-close", dependencies=[Depends(require_permission("accounting.manage"))])
def toggle_fiscal_period(
    period_id: int,
    current_user: dict = Depends(get_current_user)
):
    """فتح/إغلاق فترة محاسبية"""
    db = get_db_connection(current_user.company_id)
    try:
        period = db.execute(text("SELECT * FROM fiscal_periods WHERE id = :id"), {"id": period_id}).fetchone()
        if not period:
            raise HTTPException(status_code=404, detail="الفترة المحاسبية غير موجودة")

        # Check if the parent fiscal year is closed
        if period.fiscal_year:
            fy = db.execute(text(
                "SELECT status FROM fiscal_years WHERE year = :y"
            ), {"y": period.fiscal_year}).fetchone()
            if fy and fy.status == 'closed' and period.is_closed:
                raise HTTPException(status_code=400,
                    detail="لا يمكن فتح فترة في سنة مالية مقفلة. افتح السنة أولاً")

        new_status = not period.is_closed
        db.execute(text("""
            UPDATE fiscal_periods
            SET is_closed = :closed,
                closed_by = CASE WHEN :closed THEN :user ELSE NULL END,
                closed_at = CASE WHEN :closed THEN NOW() ELSE NULL END
            WHERE id = :id
        """), {"closed": new_status, "user": current_user.id, "id": period_id})

        db.commit()
        action = "إغلاق" if new_status else "فتح"
        return {"success": True, "message": f"تم {action} الفترة {period.name}", "is_closed": new_status}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ==================== ACC-003: Recurring Journal Templates ====================

@router.get("/recurring-templates", dependencies=[Depends(require_permission("accounting.view"))])
def list_recurring_templates(
    is_active: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    """قائمة قوالب القيود المتكررة"""
    db = get_db_connection(current_user.company_id)
    try:
        query = """
            SELECT t.*,
                   u.full_name as created_by_name,
                   (SELECT COUNT(*) FROM recurring_journal_lines WHERE template_id = t.id) as line_count
            FROM recurring_journal_templates t
            LEFT JOIN company_users u ON t.created_by = u.id
        """
        params = {}
        if is_active is not None:
            query += " WHERE t.is_active = :active"
            params["active"] = is_active
        query += " ORDER BY t.created_at DESC"
        rows = db.execute(text(query), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.get("/recurring-templates/{template_id}", dependencies=[Depends(require_permission("accounting.view"))])
def get_recurring_template(template_id: int, current_user: dict = Depends(get_current_user)):
    """تفاصيل قالب قيد متكرر مع بنوده"""
    db = get_db_connection(current_user.company_id)
    try:
        tmpl = db.execute(text("""
            SELECT t.*, u.full_name as created_by_name
            FROM recurring_journal_templates t
            LEFT JOIN company_users u ON t.created_by = u.id
            WHERE t.id = :id
        """), {"id": template_id}).fetchone()
        if not tmpl:
            raise HTTPException(status_code=404, detail="القالب غير موجود")

        lines = db.execute(text("""
            SELECT l.*, a.name as account_name, a.account_code as account_code
            FROM recurring_journal_lines l
            JOIN accounts a ON l.account_id = a.id
            WHERE l.template_id = :tid
            ORDER BY l.id
        """), {"tid": template_id}).fetchall()

        result = dict(tmpl._mapping)
        result["lines"] = [dict(l._mapping) for l in lines]
        return result
    finally:
        db.close()


@router.post("/recurring-templates", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("accounting.edit"))])
def create_recurring_template(data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """إنشاء قالب قيد متكرر جديد"""
    db = get_db_connection(current_user.company_id)
    try:
        lines = data.pop("lines", [])
        if not lines or len(lines) < 2:
            raise HTTPException(status_code=400, detail="يجب إضافة سطرين على الأقل")

        total_debit = sum(float(l.get("debit", 0)) for l in lines)
        total_credit = sum(float(l.get("credit", 0)) for l in lines)
        if round(total_debit, 4) != round(total_credit, 4):
            raise HTTPException(status_code=400, detail=f"القيد غير متوازن: مدين={total_debit} دائن={total_credit}")

        result = db.execute(text("""
            INSERT INTO recurring_journal_templates
                (name, description, reference, frequency, start_date, end_date,
                 next_run_date, is_active, auto_post, branch_id, currency,
                 exchange_rate, max_runs, created_by)
            VALUES
                (:name, :description, :reference, :frequency, :start_date, :end_date,
                 :next_run_date, :is_active, :auto_post, :branch_id, :currency,
                 :exchange_rate, :max_runs, :created_by)
            RETURNING id
        """), {
            "name": data.get("name"),
            "description": data.get("description"),
            "reference": data.get("reference"),
            "frequency": data.get("frequency", "monthly"),
            "start_date": data.get("start_date"),
            "end_date": data.get("end_date"),
            "next_run_date": data.get("next_run_date") or data.get("start_date"),
            "is_active": data.get("is_active", True),
            "auto_post": data.get("auto_post", False),
            "branch_id": data.get("branch_id") or getattr(current_user, "branch_id", None),
            "currency": data.get("currency", get_base_currency(db)),
            "exchange_rate": data.get("exchange_rate", 1.0),
            "max_runs": data.get("max_runs"),
            "created_by": current_user.id,
        })
        template_id = result.fetchone()[0]

        for line in lines:
            db.execute(text("""
                INSERT INTO recurring_journal_lines
                    (template_id, account_id, debit, credit, description, cost_center_id)
                VALUES (:tid, :account_id, :debit, :credit, :desc, :cc)
            """), {
                "tid": template_id,
                "account_id": line["account_id"],
                "debit": float(line.get("debit", 0)),
                "credit": float(line.get("credit", 0)),
                "desc": line.get("description", ""),
                "cc": line.get("cost_center_id"),
            })

        db.commit()
        log_activity(db, user_id=current_user.id, username=current_user.username,
                     action="accounting.recurring_template.create",
                     resource_type="recurring_template", resource_id=str(template_id),
                     details={"name": data.get('name')})
        return {"id": template_id, "message": "تم إنشاء القالب بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.put("/recurring-templates/{template_id}", dependencies=[Depends(require_permission("accounting.edit"))])
def update_recurring_template(template_id: int, data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """تعديل قالب قيد متكرر"""
    db = get_db_connection(current_user.company_id)
    try:
        existing = db.execute(text("SELECT id FROM recurring_journal_templates WHERE id = :id"), {"id": template_id}).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="القالب غير موجود")

        lines = data.pop("lines", None)

        db.execute(text("""
            UPDATE recurring_journal_templates SET
                name = COALESCE(:name, name),
                description = COALESCE(:description, description),
                reference = COALESCE(:reference, reference),
                frequency = COALESCE(:frequency, frequency),
                start_date = COALESCE(:start_date, start_date),
                end_date = :end_date,
                next_run_date = COALESCE(:next_run_date, next_run_date),
                is_active = COALESCE(:is_active, is_active),
                auto_post = COALESCE(:auto_post, auto_post),
                currency = COALESCE(:currency, currency),
                exchange_rate = COALESCE(:exchange_rate, exchange_rate),
                max_runs = :max_runs,
                updated_at = NOW()
            WHERE id = :id
        """), {
            "id": template_id,
            "name": data.get("name"),
            "description": data.get("description"),
            "reference": data.get("reference"),
            "frequency": data.get("frequency"),
            "start_date": data.get("start_date"),
            "end_date": data.get("end_date"),
            "next_run_date": data.get("next_run_date"),
            "is_active": data.get("is_active"),
            "auto_post": data.get("auto_post"),
            "currency": data.get("currency"),
            "exchange_rate": data.get("exchange_rate"),
            "max_runs": data.get("max_runs"),
        })

        if lines is not None:
            if len(lines) < 2:
                raise HTTPException(status_code=400, detail="يجب إضافة سطرين على الأقل")
            total_debit = sum(float(l.get("debit", 0)) for l in lines)
            total_credit = sum(float(l.get("credit", 0)) for l in lines)
            if round(total_debit, 4) != round(total_credit, 4):
                raise HTTPException(status_code=400, detail=f"القيد غير متوازن: مدين={total_debit} دائن={total_credit}")

            db.execute(text("DELETE FROM recurring_journal_lines WHERE template_id = :tid"), {"tid": template_id})
            for line in lines:
                db.execute(text("""
                    INSERT INTO recurring_journal_lines
                        (template_id, account_id, debit, credit, description, cost_center_id)
                    VALUES (:tid, :account_id, :debit, :credit, :desc, :cc)
                """), {
                    "tid": template_id,
                    "account_id": line["account_id"],
                    "debit": float(line.get("debit", 0)),
                    "credit": float(line.get("credit", 0)),
                    "desc": line.get("description", ""),
                    "cc": line.get("cost_center_id"),
                })

        db.commit()
        log_activity(db, user_id=current_user.id, username=current_user.username,
                     action="accounting.recurring_template.update",
                     resource_type="recurring_template", resource_id=str(template_id),
                     details={"template_id": template_id})
        return {"success": True, "message": "تم تعديل القالب بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.delete("/recurring-templates/{template_id}", dependencies=[Depends(require_permission("accounting.manage"))])
def delete_recurring_template(template_id: int, current_user: dict = Depends(get_current_user)):
    """حذف قالب قيد متكرر"""
    db = get_db_connection(current_user.company_id)
    try:
        existing = db.execute(text(
            "SELECT id, name FROM recurring_journal_templates WHERE id = :id"
        ), {"id": template_id}).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="القالب غير موجود")

        db.execute(text("DELETE FROM recurring_journal_templates WHERE id = :id"), {"id": template_id})
        db.commit()
        log_activity(db, user_id=current_user.id, username=current_user.username,
                     action="accounting.recurring_template.delete",
                     resource_type="recurring_template", resource_id=str(template_id),
                     details={"name": existing.name})
        return {"success": True, "message": "تم حذف القالب بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/recurring-templates/{template_id}/generate", dependencies=[Depends(require_permission("accounting.edit"))])
def generate_from_template(template_id: int, current_user: dict = Depends(get_current_user)):
    """توليد قيد يومي من قالب متكرر يدوياً"""
    db = get_db_connection(current_user.company_id)
    try:
        tmpl = db.execute(text(
            "SELECT * FROM recurring_journal_templates WHERE id = :id"
        ), {"id": template_id}).fetchone()
        if not tmpl:
            raise HTTPException(status_code=404, detail="القالب غير موجود")

        lines = db.execute(text(
            "SELECT * FROM recurring_journal_lines WHERE template_id = :tid ORDER BY id"
        ), {"tid": template_id}).fetchall()
        if not lines:
            raise HTTPException(status_code=400, detail="القالب لا يحتوي على بنود")

        entry_id = _create_entry_from_template(db, tmpl, lines, current_user)

        db.commit()
        return {"success": True, "message": "تم توليد القيد بنجاح", "entry_id": entry_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/recurring-templates/generate-due", dependencies=[Depends(require_permission("accounting.manage"))])
def generate_all_due_templates(current_user: dict = Depends(get_current_user)):
    """توليد القيود المستحقة لجميع القوالب النشطة (يُستخدم بالجدولة)"""
    db = get_db_connection(current_user.company_id)
    try:
        today = date.today()
        templates = db.execute(text("""
            SELECT * FROM recurring_journal_templates
            WHERE is_active = TRUE
              AND next_run_date <= :today
              AND (end_date IS NULL OR end_date >= :today)
              AND (max_runs IS NULL OR run_count < max_runs)
            ORDER BY next_run_date
        """), {"today": today}).fetchall()

        generated = []
        errors = []
        for tmpl in templates:
            try:
                lines = db.execute(text(
                    "SELECT * FROM recurring_journal_lines WHERE template_id = :tid ORDER BY id"
                ), {"tid": tmpl.id}).fetchall()
                if not lines:
                    continue

                entry_id = _create_entry_from_template(db, tmpl, lines, current_user)
                generated.append({"template_id": tmpl.id, "template_name": tmpl.name, "entry_id": entry_id})
            except Exception as ex:
                errors.append({"template_id": tmpl.id, "template_name": tmpl.name, "error": str(ex)})

        db.commit()
        return {
            "success": True,
            "generated_count": len(generated),
            "error_count": len(errors),
            "generated": generated,
            "errors": errors,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


def _create_entry_from_template(db, tmpl, lines, current_user):
    """Helper: إنشاء قيد يومي من قالب متكرر"""
    from dateutil.relativedelta import relativedelta

    today = date.today()
    entry_status = "posted" if tmpl.auto_post else "draft"

    number = _generate_sequential_number(db, "JE", "journal_entries", "entry_number")
    description = f"{tmpl.name} - {today.strftime('%Y-%m-%d')}"
    if tmpl.description:
        description = f"{tmpl.description} ({today.strftime('%Y-%m-%d')})"

    result = db.execute(text("""
        INSERT INTO journal_entries
            (entry_number, entry_date, description, reference, status,
             branch_id, currency, exchange_rate, created_by, posted_at)
        VALUES
            (:number, :entry_date, :desc, :ref, :status,
             :branch, :currency, :rate, :user,
             CASE WHEN :status = 'posted' THEN NOW() ELSE NULL END)
        RETURNING id
    """), {
        "number": number,
        "entry_date": today,
        "desc": description,
        "ref": tmpl.reference or f"REC-{tmpl.id}",
        "status": entry_status,
        "branch": tmpl.branch_id or getattr(current_user, "branch_id", None),
        "currency": tmpl.currency or get_base_currency(db),
        "rate": float(tmpl.exchange_rate or 1),
        "user": current_user.id,
    })
    entry_id = result.fetchone()[0]

    from utils.accounting import update_account_balance
    for line in lines:
        debit_val = float(line.debit or 0)
        credit_val = float(line.credit or 0)
        db.execute(text("""
            INSERT INTO journal_lines
                (journal_entry_id, account_id, debit, credit, description, cost_center_id)
            VALUES (:eid, :acc, :debit, :credit, :desc, :cc)
        """), {
            "eid": entry_id,
            "acc": line.account_id,
            "debit": debit_val,
            "credit": credit_val,
            "desc": line.description or "",
            "cc": line.cost_center_id,
        })

        if entry_status == "posted":
            update_account_balance(
                db, account_id=line.account_id,
                debit_base=debit_val, credit_base=credit_val
            )

    # Update template tracking
    freq_map = {
        "daily": relativedelta(days=1),
        "weekly": relativedelta(weeks=1),
        "monthly": relativedelta(months=1),
        "quarterly": relativedelta(months=3),
        "yearly": relativedelta(years=1),
    }
    next_date = today + freq_map.get(tmpl.frequency, relativedelta(months=1))

    new_run_count = (tmpl.run_count or 0) + 1
    should_deactivate = tmpl.max_runs and new_run_count >= tmpl.max_runs

    db.execute(text("""
        UPDATE recurring_journal_templates SET
            last_run_date = :today,
            next_run_date = :next,
            run_count = :count,
            is_active = :active,
            updated_at = NOW()
        WHERE id = :id
    """), {
        "today": today,
        "next": next_date,
        "count": new_run_count,
        "active": not should_deactivate,
        "id": tmpl.id,
    })

    return entry_id


# ==================== ACC-005: Opening Balances ====================

@router.get("/opening-balances", dependencies=[Depends(require_permission("accounting.view"))])
def get_opening_balances(
    current_user: dict = Depends(get_current_user)
):
    """جلب الأرصدة الافتتاحية - آخر قيد أرصدة افتتاحية مع أرصدة جميع الحسابات"""
    db = get_db_connection(current_user.company_id)
    try:
        # Find existing opening balance entry
        ob_entry = db.execute(text("""
            SELECT je.id, je.entry_number, je.entry_date, je.status, je.description
            FROM journal_entries je
            WHERE je.reference = 'OPENING-BALANCE'
            ORDER BY je.entry_date DESC, je.id DESC
            LIMIT 1
        """)).fetchone()

        # Get all accounts with their current balance
        accounts = db.execute(text("""
            SELECT id, account_number, name, name_en, account_type, parent_id
            FROM accounts
            ORDER BY account_number
        """)).fetchall()

        ob_lines = []
        if ob_entry:
            ob_lines = db.execute(text("""
                SELECT account_id, debit, credit, description
                FROM journal_lines
                WHERE journal_entry_id = :eid
            """), {"eid": ob_entry.id}).fetchall()

        ob_map = {l.account_id: {"debit": float(l.debit or 0), "credit": float(l.credit or 0)} for l in ob_lines}

        result = []
        for a in accounts:
            am = dict(a._mapping)
            ob = ob_map.get(a.id, {"debit": 0, "credit": 0})
            am["opening_debit"] = ob["debit"]
            am["opening_credit"] = ob["credit"]
            result.append(am)

        return {
            "entry": dict(ob_entry._mapping) if ob_entry else None,
            "accounts": result,
        }
    finally:
        db.close()


@router.post("/opening-balances", dependencies=[Depends(require_permission("accounting.manage"))])
def save_opening_balances(
    data: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """حفظ الأرصدة الافتتاحية (ينشئ أو يحدث قيد الأرصدة الافتتاحية)"""
    db = get_db_connection(current_user.company_id)
    try:
        lines = data.get("lines", [])
        entry_date = data.get("date", str(date.today()))

        # Filter to only lines with actual values
        valid_lines = [l for l in lines if float(l.get("debit", 0)) != 0 or float(l.get("credit", 0)) != 0]
        if not valid_lines:
            raise HTTPException(status_code=400, detail="لا توجد أرصدة لحفظها")

        total_debit = sum(float(l.get("debit", 0)) for l in valid_lines)
        total_credit = sum(float(l.get("credit", 0)) for l in valid_lines)

        # Find existing opening balance entry
        existing = db.execute(text("""
            SELECT id, status FROM journal_entries
            WHERE reference = 'OPENING-BALANCE'
            ORDER BY entry_date DESC, id DESC
            LIMIT 1
        """)).fetchone()

        if existing:
            # Reverse old balances if it was posted
            if existing.status == 'posted':
                from utils.accounting import update_account_balance as _uab
                old_lines = db.execute(text(
                    "SELECT account_id, debit, credit FROM journal_lines WHERE journal_entry_id = :eid"
                ), {"eid": existing.id}).fetchall()
                for ol in old_lines:
                    # Reverse: swap debit/credit to undo original effect
                    _uab(db, account_id=ol.account_id,
                         debit_base=float(ol.credit or 0),
                         credit_base=float(ol.debit or 0))

            # Delete old lines and update entry
            db.execute(text("DELETE FROM journal_lines WHERE journal_entry_id = :eid"), {"eid": existing.id})
            db.execute(text("""
                UPDATE journal_entries SET
                    entry_date = :dt, status = 'posted', posted_at = NOW(),
                    description = :desc, updated_at = NOW()
                WHERE id = :id
            """), {"dt": entry_date, "desc": "أرصدة افتتاحية / Opening Balances", "id": existing.id})
            entry_id = existing.id
        else:
            # Create new entry
            number = _generate_sequential_number(db, "JE", "journal_entries", "entry_number")
            result = db.execute(text("""
                INSERT INTO journal_entries
                    (entry_number, entry_date, description, reference, status, branch_id, created_by, posted_at)
                VALUES
                    (:num, :dt, :desc, 'OPENING-BALANCE', 'posted', :branch, :user, NOW())
                RETURNING id
            """), {
                "num": number,
                "dt": entry_date,
                "desc": "أرصدة افتتاحية / Opening Balances",
                "branch": getattr(current_user, "branch_id", None),
                "user": current_user.id,
            })
            entry_id = result.fetchone()[0]

        # If not balanced, add a suspense line (difference to equity - opening balance equity)
        if round(total_debit, 4) != round(total_credit, 4):
            diff = total_debit - total_credit
            # Find or use a suspense/equity account
            suspense = db.execute(text(
                "SELECT id FROM accounts WHERE account_number = '3100' OR (account_type = 'equity' AND name LIKE '%افتتا%') LIMIT 1"
            )).fetchone()
            if not suspense:
                suspense = db.execute(text(
                    "SELECT id FROM accounts WHERE account_type = 'equity' ORDER BY account_number LIMIT 1"
                )).fetchone()
            if suspense:
                valid_lines.append({
                    "account_id": suspense.id,
                    "debit": max(-diff, 0),
                    "credit": max(diff, 0),
                    "description": "فرق الأرصدة الافتتاحية / Opening Balance Difference"
                })

        # Insert new lines
        from utils.accounting import update_account_balance as _uab2
        for line in valid_lines:
            d_val = float(line.get("debit", 0))
            c_val = float(line.get("credit", 0))
            db.execute(text("""
                INSERT INTO journal_lines
                    (journal_entry_id, account_id, debit, credit, description)
                VALUES (:eid, :acc, :debit, :credit, :desc)
            """), {
                "eid": entry_id,
                "acc": int(line["account_id"]),
                "debit": d_val,
                "credit": c_val,
                "desc": line.get("description", "رصيد افتتاحي"),
            })

            # Update account balance using proper helper (respects account type)
            _uab2(db, account_id=int(line["account_id"]),
                  debit_base=d_val, credit_base=c_val)

        db.commit()
        log_activity(db, user_id=current_user.id, username=current_user.username,
                     action="accounting.opening_balances.save",
                     resource_type="opening_balances", resource_id=str(entry_id),
                     details={"lines_count": len(valid_lines)})
        return {"success": True, "entry_id": entry_id, "lines_count": len(valid_lines),
                "message": "تم حفظ الأرصدة الافتتاحية بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ==================== ACC-006: Automatic Closing Entries ====================

@router.get("/closing-entries/preview", dependencies=[Depends(require_permission("accounting.manage"))])
def preview_closing_entries(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """معاينة قيود الإقفال التلقائي للإيرادات والمصاريف"""
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    try:
        if not start_date:
            start_date = date.today().replace(month=1, day=1)
        if not end_date:
            end_date = date.today()

        params = {"start": start_date, "end": end_date}
        branch_filter = "AND je.branch_id = :branch_id" if branch_id else ""
        if branch_id:
            params["branch_id"] = branch_id

        revenues = db.execute(text(f"""
            SELECT a.id, a.account_number, a.name, a.name_en,
                   COALESCE(SUM(jl.credit - jl.debit), 0) as balance
            FROM accounts a
            JOIN journal_lines jl ON a.id = jl.account_id
            JOIN journal_entries je ON jl.journal_entry_id = je.id
            WHERE a.account_type = 'revenue'
            AND je.entry_date BETWEEN :start AND :end
            AND je.status = 'posted' {branch_filter}
            GROUP BY a.id, a.account_number, a.name, a.name_en
            HAVING COALESCE(SUM(jl.credit - jl.debit), 0) != 0
            ORDER BY a.account_number
        """), params).fetchall()

        expenses = db.execute(text(f"""
            SELECT a.id, a.account_number, a.name, a.name_en,
                   COALESCE(SUM(jl.debit - jl.credit), 0) as balance
            FROM accounts a
            JOIN journal_lines jl ON a.id = jl.account_id
            JOIN journal_entries je ON jl.journal_entry_id = je.id
            WHERE a.account_type = 'expense'
            AND je.entry_date BETWEEN :start AND :end
            AND je.status = 'posted' {branch_filter}
            GROUP BY a.id, a.account_number, a.name, a.name_en
            HAVING COALESCE(SUM(jl.debit - jl.credit), 0) != 0
            ORDER BY a.account_number
        """), params).fetchall()

        income_summary = db.execute(text(
            "SELECT id, account_number, name FROM accounts WHERE account_number = '3200' OR name LIKE '%ملخص الدخل%' LIMIT 1"
        )).fetchone()
        retained_earnings = db.execute(text(
            "SELECT id, account_number, name FROM accounts WHERE account_number IN ('RET', '3100') OR name LIKE '%أرباح مبقاة%' OR name LIKE '%Retained%' ORDER BY account_number LIMIT 1"
        )).fetchone()

        total_revenue = sum(float(r.balance) for r in revenues)
        total_expense = sum(float(r.balance) for r in expenses)
        net_income = total_revenue - total_expense

        return {
            "period": {"start": str(start_date), "end": str(end_date)},
            "revenues": [dict(r._mapping) for r in revenues],
            "expenses": [dict(r._mapping) for r in expenses],
            "total_revenue": total_revenue,
            "total_expense": total_expense,
            "net_income": net_income,
            "income_summary_account": dict(income_summary._mapping) if income_summary else None,
            "retained_earnings_account": dict(retained_earnings._mapping) if retained_earnings else None,
        }
    finally:
        db.close()


@router.post("/closing-entries/generate", dependencies=[Depends(require_permission("accounting.manage"))])
def generate_closing_entries(
    data: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """توليد قيود الإقفال التلقائي: إقفال الإيرادات والمصاريف → ملخص الدخل → أرباح مبقاة"""
    db = get_db_connection(current_user.company_id)
    try:
        start_date_str = data.get("start_date", str(date.today().replace(month=1, day=1)))
        end_date_str = data.get("end_date", str(date.today()))
        retained_earnings_id = data.get("retained_earnings_account_id")
        income_summary_id = data.get("income_summary_account_id")
        use_income_summary = data.get("use_income_summary", False) and income_summary_id
        entry_date_str = data.get("entry_date", end_date_str)

        branch_id = validate_branch_access(current_user, data.get("branch_id"))
        params = {"start": start_date_str, "end": end_date_str}
        branch_filter = "AND je.branch_id = :branch_id" if branch_id else ""
        if branch_id:
            params["branch_id"] = branch_id

        if not retained_earnings_id:
            ret = db.execute(text(
                "SELECT id FROM accounts WHERE account_number IN ('RET', '3100') OR name LIKE '%أرباح مبقاة%' OR name LIKE '%Retained%' ORDER BY account_number LIMIT 1"
            )).fetchone()
            if not ret:
                raise HTTPException(status_code=400, detail="لم يتم العثور على حساب الأرباح المبقاة")
            retained_earnings_id = ret.id

        revenues = db.execute(text(f"""
            SELECT a.id, a.account_number, a.name,
                   COALESCE(SUM(jl.credit - jl.debit), 0) as balance
            FROM accounts a
            JOIN journal_lines jl ON a.id = jl.account_id
            JOIN journal_entries je ON jl.journal_entry_id = je.id
                AND je.entry_date BETWEEN :start AND :end
                AND je.status = 'posted' {branch_filter}
            WHERE a.account_type = 'revenue'
            GROUP BY a.id, a.account_number, a.name
            HAVING COALESCE(SUM(jl.credit - jl.debit), 0) != 0
        """), params).fetchall()

        expenses = db.execute(text(f"""
            SELECT a.id, a.account_number, a.name,
                   COALESCE(SUM(jl.debit - jl.credit), 0) as balance
            FROM accounts a
            JOIN journal_lines jl ON a.id = jl.account_id
            JOIN journal_entries je ON jl.journal_entry_id = je.id
                AND je.entry_date BETWEEN :start AND :end
                AND je.status = 'posted' {branch_filter}
            WHERE a.account_type = 'expense'
            GROUP BY a.id, a.account_number, a.name
            HAVING COALESCE(SUM(jl.debit - jl.credit), 0) != 0
        """), params).fetchall()

        total_revenue = sum(float(r.balance) for r in revenues)
        total_expense = sum(float(r.balance) for r in expenses)
        net_income = total_revenue - total_expense

        created_entries = []
        target_account_id = income_summary_id if use_income_summary else retained_earnings_id

        from utils.accounting import update_account_balance as _uab_closing

        # Entry 1: Close Revenue accounts
        if revenues:
            num1 = _generate_sequential_number(db, "JE", "journal_entries", "entry_number")
            r1 = db.execute(text("""
                INSERT INTO journal_entries
                    (entry_number, entry_date, description, reference, status, branch_id, created_by, posted_at)
                VALUES (:num, :dt, :desc, 'CLOSING-REVENUE', 'posted', :branch, :user, NOW())
                RETURNING id
            """), {
                "num": num1, "dt": entry_date_str,
                "desc": f"إقفال حسابات الإيرادات - {start_date_str} إلى {end_date_str}",
                "branch": branch_id or getattr(current_user, "branch_id", None), "user": current_user.id,
            })
            eid1 = r1.fetchone()[0]

            for rev in revenues:
                bal = float(rev.balance)
                db.execute(text("""
                    INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                    VALUES (:eid, :acc, :debit, 0, :desc)
                """), {"eid": eid1, "acc": rev.id, "debit": bal, "desc": f"إقفال {rev.name}"})
                # Debit revenue → zeroes it out (revenue normal balance is credit)
                _uab_closing(db, account_id=rev.id, debit_base=bal, credit_base=0)

            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                VALUES (:eid, :acc, 0, :credit, :desc)
            """), {"eid": eid1, "acc": target_account_id, "credit": total_revenue,
                   "desc": "إجمالي الإيرادات المقفلة"})
            _uab_closing(db, account_id=target_account_id, debit_base=0, credit_base=total_revenue)

            created_entries.append({"id": eid1, "type": "close_revenue", "number": num1})

        # Entry 2: Close Expense accounts
        if expenses:
            num2 = _generate_sequential_number(db, "JE", "journal_entries", "entry_number")
            r2 = db.execute(text("""
                INSERT INTO journal_entries
                    (entry_number, entry_date, description, reference, status, branch_id, created_by, posted_at)
                VALUES (:num, :dt, :desc, 'CLOSING-EXPENSE', 'posted', :branch, :user, NOW())
                RETURNING id
            """), {
                "num": num2, "dt": entry_date_str,
                "desc": f"إقفال حسابات المصاريف - {start_date_str} إلى {end_date_str}",
                "branch": branch_id or getattr(current_user, "branch_id", None), "user": current_user.id,
            })
            eid2 = r2.fetchone()[0]

            for exp in expenses:
                bal = float(exp.balance)
                db.execute(text("""
                    INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                    VALUES (:eid, :acc, 0, :credit, :desc)
                """), {"eid": eid2, "acc": exp.id, "credit": bal, "desc": f"إقفال {exp.name}"})
                # Credit expense → zeroes it out (expense normal balance is debit)
                _uab_closing(db, account_id=exp.id, debit_base=0, credit_base=bal)

            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                VALUES (:eid, :acc, :debit, 0, :desc)
            """), {"eid": eid2, "acc": target_account_id, "debit": total_expense,
                   "desc": "إجمالي المصاريف المقفلة"})
            _uab_closing(db, account_id=target_account_id, debit_base=total_expense, credit_base=0)

            created_entries.append({"id": eid2, "type": "close_expense", "number": num2})

        # Entry 3: Transfer Income Summary → Retained Earnings
        if use_income_summary and net_income != 0:
            num3 = _generate_sequential_number(db, "JE", "journal_entries", "entry_number")
            r3 = db.execute(text("""
                INSERT INTO journal_entries
                    (entry_number, entry_date, description, reference, status, branch_id, created_by, posted_at)
                VALUES (:num, :dt, :desc, 'CLOSING-TRANSFER', 'posted', :branch, :user, NOW())
                RETURNING id
            """), {
                "num": num3, "dt": entry_date_str,
                "desc": f"ترحيل ملخص الدخل إلى الأرباح المبقاة - صافي: {net_income}",
                "branch": branch_id or getattr(current_user, "branch_id", None), "user": current_user.id,
            })
            eid3 = r3.fetchone()[0]

            if net_income > 0:
                # Profit: Debit Income Summary, Credit Retained Earnings
                db.execute(text("""
                    INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                    VALUES (:eid, :acc, :amt, 0, 'إقفال ملخص الدخل')
                """), {"eid": eid3, "acc": income_summary_id, "amt": net_income})
                db.execute(text("""
                    INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                    VALUES (:eid, :acc, 0, :amt, 'صافي أرباح الفترة')
                """), {"eid": eid3, "acc": retained_earnings_id, "amt": net_income})
                _uab_closing(db, account_id=income_summary_id, debit_base=net_income, credit_base=0)
                _uab_closing(db, account_id=retained_earnings_id, debit_base=0, credit_base=net_income)
            else:
                loss = abs(net_income)
                # Loss: Credit Income Summary, Debit Retained Earnings
                db.execute(text("""
                    INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                    VALUES (:eid, :acc, 0, :amt, 'إقفال ملخص الدخل')
                """), {"eid": eid3, "acc": income_summary_id, "amt": loss})
                db.execute(text("""
                    INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                    VALUES (:eid, :acc, :amt, 0, 'صافي خسائر الفترة')
                """), {"eid": eid3, "acc": retained_earnings_id, "amt": loss})
                _uab_closing(db, account_id=income_summary_id, debit_base=0, credit_base=loss)
                _uab_closing(db, account_id=retained_earnings_id, debit_base=loss, credit_base=0)

            created_entries.append({"id": eid3, "type": "transfer_to_retained", "number": num3})

        db.commit()
        log_activity(db, user_id=current_user.id, username=current_user.username,
                     action="accounting.closing_entries.generate",
                     resource_type="closing_entries", resource_id=str(len(created_entries)),
                     details={"entries_count": len(created_entries), "net_income": net_income})

        return {
            "success": True,
            "entries": created_entries,
            "total_revenue": total_revenue,
            "total_expense": total_expense,
            "net_income": net_income,
            "message": f"تم توليد {len(created_entries)} قيد إقفال بنجاح",
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# GL-004: Bad Debt Provision (مخصص ديون معدومة)
# ═══════════════════════════════════════════════════════════

class ProvisionRequest(BaseModel):
    amount: float
    description: Optional[str] = None
    branch_id: Optional[int] = None

@router.post("/provisions/bad-debt", dependencies=[Depends(require_permission("accounting.manage"))])
def create_bad_debt_provision(req: ProvisionRequest, current_user: dict = Depends(get_current_user)):
    """إنشاء قيد مخصص ديون معدومة — Dr مصروف ديون معدومة / Cr مخصص الديون المعدومة"""
    from utils.accounting import get_mapped_account_id, get_base_currency, update_account_balance
    branch_id = validate_branch_access(current_user, req.branch_id)
    db = get_db_connection(current_user.company_id)
    trans = db.begin()
    try:
        base_currency = get_base_currency(db)
        acc_bad_debt_exp = get_mapped_account_id(db, "acc_map_bad_debt_expense")
        acc_prov_doubtful = get_mapped_account_id(db, "acc_map_provision_doubtful")
        if not acc_bad_debt_exp or not acc_prov_doubtful:
            raise HTTPException(status_code=400, detail="لم يتم تعيين حسابات الديون المعدومة في الإعدادات")

        je_num = f"JE-BD-PROV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        desc = req.description or "مخصص ديون معدومة"
        je_id = db.execute(text("""
            INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, created_by, branch_id, currency, exchange_rate, posted_at)
            VALUES (:num, CURRENT_DATE, 'BAD-DEBT-PROV', :desc, 'posted', :uid, :br, :curr, 1, NOW()) RETURNING id
        """), {"num": je_num, "desc": desc, "uid": current_user.id, "br": branch_id, "curr": base_currency}).scalar()

        for acc_id, debit, credit, line_desc in [
            (acc_bad_debt_exp, req.amount, 0, "مصروف ديون معدومة"),
            (acc_prov_doubtful, 0, req.amount, "مخصص الديون المعدومة"),
        ]:
            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description, amount_currency, currency)
                VALUES (:jid, :acc, :d, :c, :desc, :amt, :curr)
            """), {"jid": je_id, "acc": acc_id, "d": debit, "c": credit, "desc": line_desc, "amt": req.amount, "curr": base_currency})
            update_account_balance(db, account_id=acc_id, debit_base=debit, credit_base=credit)

        trans.commit()
        return {"success": True, "journal_entry": je_num, "amount": req.amount}
    except HTTPException:
        trans.rollback()
        raise
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# GL-005: Leave Provision (مخصص إجازات)
# ═══════════════════════════════════════════════════════════

@router.post("/provisions/leave", dependencies=[Depends(require_permission("accounting.manage"))])
def create_leave_provision(req: ProvisionRequest, current_user: dict = Depends(get_current_user)):
    """إنشاء قيد مخصص إجازات — Dr مصروف إجازات / Cr مخصص الإجازات"""
    from utils.accounting import get_mapped_account_id, get_base_currency, update_account_balance
    branch_id = validate_branch_access(current_user, req.branch_id)
    db = get_db_connection(current_user.company_id)
    trans = db.begin()
    try:
        base_currency = get_base_currency(db)
        acc_leave_exp = get_mapped_account_id(db, "acc_map_leave_expense")
        acc_leave_prov = get_mapped_account_id(db, "acc_map_provision_holiday")
        if not acc_leave_exp or not acc_leave_prov:
            raise HTTPException(status_code=400, detail="لم يتم تعيين حسابات الإجازات في الإعدادات")

        je_num = f"JE-LV-PROV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        desc = req.description or "مخصص إجازات الموظفين"
        je_id = db.execute(text("""
            INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, created_by, branch_id, currency, exchange_rate, posted_at)
            VALUES (:num, CURRENT_DATE, 'LEAVE-PROV', :desc, 'posted', :uid, :br, :curr, 1, NOW()) RETURNING id
        """), {"num": je_num, "desc": desc, "uid": current_user.id, "br": branch_id, "curr": base_currency}).scalar()

        for acc_id, debit, credit, line_desc in [
            (acc_leave_exp, req.amount, 0, "مصروف الإجازات"),
            (acc_leave_prov, 0, req.amount, "مخصص الإجازات"),
        ]:
            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description, amount_currency, currency)
                VALUES (:jid, :acc, :d, :c, :desc, :amt, :curr)
            """), {"jid": je_id, "acc": acc_id, "d": debit, "c": credit, "desc": line_desc, "amt": req.amount, "curr": base_currency})
            update_account_balance(db, account_id=acc_id, debit_base=debit, credit_base=credit)

        trans.commit()
        return {"success": True, "journal_entry": je_num, "amount": req.amount}
    except HTTPException:
        trans.rollback()
        raise
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# GL-006: FX Revaluation (تسوية العملات الأجنبية)
# ═══════════════════════════════════════════════════════════

class FXRevaluationRequest(BaseModel):
    currency_code: str
    new_rate: float
    branch_id: Optional[int] = None

@router.post("/fx-revaluation", dependencies=[Depends(require_permission("accounting.manage"))])
def fx_revaluation(req: FXRevaluationRequest, current_user: dict = Depends(get_current_user)):
    """إعادة تقييم أرصدة العملات الأجنبية — الفروقات تسجل كربح/خسارة غير محققة"""
    from utils.accounting import get_mapped_account_id, get_base_currency, update_account_balance
    branch_id = validate_branch_access(current_user, req.branch_id)
    db = get_db_connection(current_user.company_id)
    trans = db.begin()
    try:
        base_currency = get_base_currency(db)

        # Find unrealized FX gain/loss accounts
        gain_acc = db.execute(text("SELECT id FROM accounts WHERE account_number = '4202'")).fetchone()
        loss_acc = db.execute(text("SELECT id FROM accounts WHERE account_number = '5403'")).fetchone()
        ufx_gain = gain_acc.id if gain_acc else None
        ufx_loss = loss_acc.id if loss_acc else None
        if not ufx_gain and not ufx_loss:
            raise HTTPException(status_code=400, detail="لم يتم العثور على حسابات فروقات العملة غير المحققة")

        # Find all accounts with balances in this currency
        balances = db.execute(text("""
            SELECT jl.account_id, a.account_number, a.name,
                   SUM(CASE WHEN jl.debit > 0 THEN jl.amount_currency
                            ELSE -jl.amount_currency END) as fc_balance,
                   SUM(jl.debit - jl.credit) as base_balance
            FROM journal_lines jl
            JOIN journal_entries je ON jl.journal_entry_id = je.id
            JOIN accounts a ON jl.account_id = a.id
            WHERE jl.currency = :curr AND je.status = 'posted'
                  AND a.account_type IN ('asset', 'liability')
            GROUP BY jl.account_id, a.account_number, a.name
            HAVING SUM(CASE WHEN jl.debit > 0 THEN jl.amount_currency
                            ELSE -jl.amount_currency END) != 0
        """), {"curr": req.currency_code}).fetchall()

        if not balances:
            return {"success": True, "message": "لا توجد أرصدة بهذه العملة", "adjustments": []}

        adjustments = []
        total_diff = 0.0

        je_num = f"JE-FX-REVAL-{req.currency_code}-{datetime.now().strftime('%Y%m%d')}"
        je_id = db.execute(text("""
            INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, created_by, branch_id, currency, exchange_rate)
            VALUES (:num, CURRENT_DATE, :ref, :desc, 'posted', :uid, :br, :curr, 1) RETURNING id
        """), {
            "num": je_num, "ref": f"FX-REVAL-{req.currency_code}",
            "desc": f"إعادة تقييم عملة {req.currency_code} بسعر {req.new_rate}",
            "uid": current_user.id, "br": branch_id, "curr": base_currency
        }).scalar()

        for bal in balances:
            m = bal._mapping
            fc = float(m["fc_balance"])
            old_base = float(m["base_balance"])
            new_base = fc * req.new_rate
            diff = new_base - old_base
            if abs(diff) < 0.01:
                continue

            total_diff += diff
            if diff > 0:
                db.execute(text("""
                    INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description, amount_currency, currency)
                    VALUES (:jid, :acc, :d, 0, :desc, 0, :curr)
                """), {"jid": je_id, "acc": m["account_id"], "d": abs(diff), "desc": f"تعديل سعر {req.currency_code}", "curr": base_currency})
                update_account_balance(db, account_id=m["account_id"], debit_base=abs(diff), credit_base=0)
            else:
                db.execute(text("""
                    INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description, amount_currency, currency)
                    VALUES (:jid, :acc, 0, :c, :desc, 0, :curr)
                """), {"jid": je_id, "acc": m["account_id"], "c": abs(diff), "desc": f"تعديل سعر {req.currency_code}", "curr": base_currency})
                update_account_balance(db, account_id=m["account_id"], debit_base=0, credit_base=abs(diff))

            adjustments.append({
                "account_id": m["account_id"], "account_number": m["account_number"], "name": m["name"],
                "fc_balance": round(fc, 2), "old_base": round(old_base, 2), "new_base": round(new_base, 2),
                "difference": round(diff, 2),
            })

        # Post the offsetting FX gain/loss
        if total_diff > 0 and ufx_gain:
            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description, amount_currency, currency)
                VALUES (:jid, :acc, 0, :amt, 'أرباح فروقات عملة (غير محققة)', 0, :curr)
            """), {"jid": je_id, "acc": ufx_gain, "amt": abs(total_diff), "curr": base_currency})
            update_account_balance(db, account_id=ufx_gain, debit_base=0, credit_base=abs(total_diff))
        elif total_diff < 0 and ufx_loss:
            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description, amount_currency, currency)
                VALUES (:jid, :acc, :amt, 0, 'خسائر فروقات عملة (غير محققة)', 0, :curr)
            """), {"jid": je_id, "acc": ufx_loss, "amt": abs(total_diff), "curr": base_currency})
            update_account_balance(db, account_id=ufx_loss, debit_base=abs(total_diff), credit_base=0)

        trans.commit()
        return {
            "success": True, "journal_entry": je_num,
            "currency": req.currency_code, "new_rate": req.new_rate,
            "total_adjustment": round(total_diff, 2),
            "adjustments": adjustments,
        }
    except HTTPException:
        trans.rollback()
        raise
    except Exception as e:
        trans.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()