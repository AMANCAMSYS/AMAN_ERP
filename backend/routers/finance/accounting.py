from fastapi import APIRouter, Depends, HTTPException, status, Body
from utils.i18n import http_error
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import text
from database import get_db_connection
from routers.auth import get_current_user
import logging
from datetime import date
from dateutil.relativedelta import relativedelta
from utils.cache import invalidate_company_cache
from decimal import Decimal, ROUND_HALF_UP

from utils.permissions import require_permission, validate_branch_access
from utils.audit import log_activity
from utils.accounting import get_base_currency
from fastapi import Request
from services.gl_service import create_journal_entry as gl_create_journal_entry

from schemas.accounting import AccountCreate, AccountUpdate, FiscalYearCreate, FiscalYearClose, FiscalYearReopen
from utils.cache import cache
from utils.limiter import limiter

router = APIRouter(prefix="/accounting", tags=["المحاسبة"])
logger = logging.getLogger(__name__)

_D2 = Decimal("0.01")
_D4 = Decimal("0.0001")
def _dec(v) -> Decimal:
    return Decimal(str(v)) if v is not None else Decimal("0")

@router.get("/summary", dependencies=[Depends(require_permission("accounting.view"))])
@limiter.limit("200/minute")
def get_accounting_summary(
    request: Request,
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
                 cash_balance = db.execute(text("""
                    SELECT COALESCE(SUM(jl.debit - jl.credit), 0)
                    FROM journal_lines jl
                    JOIN journal_entries je ON jl.journal_entry_id = je.id
                    JOIN accounts a ON jl.account_id = a.id
                    WHERE a.id = ANY(:cash_ids)
                    AND je.branch_id = :branch_id
                """), {"cash_ids": all_cash_ids, "branch_id": branch_id}).scalar() or 0
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
                cash_balance = db.execute(text("""
                    SELECT COALESCE(SUM(balance), 0) FROM accounts 
                    WHERE id = ANY(:cash_ids)
                """), {"cash_ids": all_cash_ids}).scalar() or 0
        
        return {
            "total_income": float(total_income),
            "total_expenses": float(total_expenses),
            "net_profit": float(total_income - total_expenses),
            "cash_balance": float(cash_balance)
        }
    finally:
        db.close()
# ── MODULE-001: Map account_code to the module it belongs to ──
# Used to show module tags in COA and for module-based filtering
_ACCOUNT_MODULE_MAP = {
    # Manufacturing (legacy codes)
    "RM-INV":   "manufacturing",
    "FG-INV":   "manufacturing",
    "WIP":      "manufacturing",
    "CGS-MFG":  "manufacturing",
    "LABOR":    "manufacturing",
    "MFG-OH":   "manufacturing",
    # Inventory / Stock (legacy codes)
    "INV":      "stock",
    "INV-ADJ":  "stock",
    # POS (legacy codes)
    "CASH-OS":  "pos",
    # Services (legacy codes)
    "SALE-S":   "services",
    # HR (legacy codes)
    "SAL":      "hr",
    "GOSI-EXP": "hr",
    "ADV":      "hr",
}

# Numeric code prefix → module mapping (for SOCPA/IFRS-coded accounts)
# يغطي كل الحسابات المُزروعة من industry_coa_templates
_NUMERIC_CODE_MODULE_MAP = {
    "13":    "stock",           # مخزون — كل حسابات المخزون
    "130":   "stock",           # فرعيات المخزون
    "1301":  "stock",           # بضاعة بالطريق / WIP
    "1302":  "stock",           # مخزون إنتاج تام / بضاعة لدى وكلاء
    "1303":  "stock",           # قطع غيار / أصول بيولوجية
    "1304":  "stock",           # أصول بيولوجية فرعية
    "1305":  "stock",           # أصول بيولوجية أشجار
    "510":   "stock",           # تكلفة بضاعة فرعية
    "51010": "stock",           # COGS variants
    "51020": "stock",           # فروقات جرد / عمولات
    "51030": "manufacturing",   # تكاليف غير مباشرة
    "51040": "manufacturing",   # هدر إنتاج
    "51050": "manufacturing",   # فروقات تكلفة معيارية
    "16030": "manufacturing",   # معدات صناعية / ثقيلة
    "16040": "manufacturing",   # خطوط إنتاج / سقالات
    "18004": "manufacturing",   # إهلاك متراكم — آلات
    "18005": "manufacturing",   # إهلاك متراكم — خطوط إنتاج
    "41010": "sales",           # إيرادات فرعية
    "41020": "sales",           # مردودات / مبيعات فرعية
    "41030": "sales",           # خصم / إيرادات فرعية
    "41040": "sales",           # مردودات أدوية / أعلاف
    "61030": "hr",              # أجور عمال مباشرة
    "61040": "hr",              # أجور خدمة
    "15020": "projects",        # تكاليف مشاريع مؤجلة / WIP خدمات
    "21090": "projects",        # محتجزات موردين
    "21100": "projects",        # مقاولين من الباطن
}

def _account_code_to_module(code: str) -> str | None:
    """Return the module key this account belongs to, or None for core/shared accounts."""
    if not code:
        return None
    # 1) Check exact match (legacy codes)
    m = _ACCOUNT_MODULE_MAP.get(code)
    if m:
        return m
    # 2) Check numeric prefix (longest prefix first)
    for prefix_len in (5, 4, 3, 2):
        if len(code) >= prefix_len:
            prefix = code[:prefix_len]
            m = _NUMERIC_CODE_MODULE_MAP.get(prefix)
            if m:
                return m
    return None
@router.get("/accounts", dependencies=[Depends(require_permission("accounting.view"))])
@limiter.limit("200/minute")
async def get_chart_of_accounts(
    request: Request,
    search: Optional[str] = None,
    account_type: Optional[str] = None,
    page: Optional[int] = None,
    page_size: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Fetch all accounts for the current company, optionally filtered by branch balance"""
    branch_id = validate_branch_access(current_user, None)
    db = get_db_connection(current_user.company_id)
    
    # Balances are computed live from journal_lines — no caching
    # (accounts/treasury/journal entries can change at any time)
    use_cache = False

    try:

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
                    a.id, a.account_number, a.account_code, a.name, a.name_en, a.account_type, a.parent_id, a.currency, a.is_active, a.is_header,
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
                GROUP BY a.id, a.account_number, a.account_code, a.name, a.name_en, a.account_type, a.parent_id, a.currency, a.is_active, a.is_header, a.balance_currency
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
            # Compute balance from journal_lines aggregation (all branches)
            # Consistent with branch-specific view — always live from journal_lines
            query = f"""
                SELECT 
                    a.id, a.account_number, a.account_code, a.name, a.name_en, a.account_type,
                    a.parent_id, a.currency, a.is_active, a.is_header,
                    a.balance_currency as total_balance_currency,
                    CASE 
                        WHEN a.account_type IN ('asset', 'expense') THEN 
                            COALESCE(SUM(jl.debit - jl.credit), 0)
                        ELSE 
                            COALESCE(SUM(jl.credit - jl.debit), 0)
                    END as balance,
                    CASE 
                        WHEN a.currency IS NOT NULL AND a.currency != '' THEN
                            CASE 
                                WHEN a.account_type IN ('asset', 'expense') THEN 
                                    COALESCE(SUM(CASE WHEN jl.currency = a.currency AND jl.debit > 0 THEN jl.amount_currency ELSE 0 END), 0)
                                  - COALESCE(SUM(CASE WHEN jl.currency = a.currency AND jl.credit > 0 THEN jl.amount_currency ELSE 0 END), 0)
                                ELSE 
                                    COALESCE(SUM(CASE WHEN jl.currency = a.currency AND jl.credit > 0 THEN jl.amount_currency ELSE 0 END), 0)
                                  - COALESCE(SUM(CASE WHEN jl.currency = a.currency AND jl.debit > 0 THEN jl.amount_currency ELSE 0 END), 0)
                            END
                        ELSE 0
                    END as balance_currency
                FROM accounts a
                LEFT JOIN journal_lines jl ON jl.account_id = a.id
                LEFT JOIN journal_entries je ON jl.journal_entry_id = je.id
                WHERE 1=1 {where_extra}
                GROUP BY a.id, a.account_number, a.account_code, a.name, a.name_en, a.account_type,
                         a.parent_id, a.currency, a.is_active, a.is_header, a.balance_currency
                ORDER BY a.account_number ASC
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

        # ── MODULE-001: Add module_tag to each account based on account_code ──
        for acc in accounts:
            acc["module_tag"] = _account_code_to_module(acc.get("account_code", ""))
        
        # Pagination result structure
        if page is not None and page >= 1:
            return {
                "data": accounts,
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size
            }
        
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
@limiter.limit("100/minute")
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
            INSERT INTO accounts (account_number, account_code, name, name_en, account_type, parent_id, currency, is_header, balance, is_active)
            VALUES (:num, :code, :name, :name_en, :type, :parent, :curr, :is_header, 0, true)
        """), {
            "num": account.account_number,
            "code": account.account_code,
            "name": account.name,
            "name_en": account.name_en,
            "type": account.account_type,
            "parent": account.parent_id,
            "curr": account.currency,
            "is_header": account.is_header
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
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        # Invalidate cache
        try:
            cache.delete(f"chart_of_accounts:{current_user.company_id}")
        except Exception:
            pass
        db.close()

@router.delete("/accounts/{account_id}", dependencies=[Depends(require_permission("accounting.manage"))])
@limiter.limit("100/minute")
async def delete_account(
    request: Request,
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
        if balance_row and _dec(balance_row[0]).copy_abs() > _D2:
            raise HTTPException(status_code=400, detail="لا يمكن حذف الحساب لأن رصيده غير صفري")

        # Capture account info before delete
        acct = db.execute(text("SELECT account_code, name FROM accounts WHERE id = :id"), {"id": account_id}).fetchone()
        
        db.execute(text("DELETE FROM accounts WHERE id = :id"), {"id": account_id})
        db.commit()
        
        log_activity(db, user_id=current_user.id, username=current_user.username,
                     action="accounting.account.delete",
                     resource_type="account", resource_id=str(account_id),
                     details={"account_code": acct[0] if acct else None, "name": acct[1] if acct else None},
                     request=request)
        
        # Invalidate cache
        try:
            cache.delete(f"chart_of_accounts:{current_user.company_id}")
        except Exception:
            pass
            
        return {"success": True, "message": "تم حذف الحساب بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting account: {str(e)}")
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()

@router.put("/accounts/{account_id}", dependencies=[Depends(require_permission("accounting.edit"))])
@limiter.limit("100/minute")
async def update_account(
    request: Request,
    account_id: int,
    account_data: AccountUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update account details"""
    db = get_db_connection(current_user.company_id)
    try:
        # Check if account exists
        existing = db.execute(text("SELECT 1 FROM accounts WHERE id = :id"), {"id": account_id}).fetchone()
        if not existing:
             raise HTTPException(**http_error(404, "account_not_found"))

        payload = account_data.dict(exclude_unset=True)

        # Check for duplicate account_code
        new_code = payload.get("account_code")
        if new_code:
            dup = db.execute(text("SELECT 1 FROM accounts WHERE account_code = :code AND id != :id"), {"code": new_code, "id": account_id}).fetchone()
            if dup:
                raise HTTPException(status_code=400, detail=f"رمز الحساب '{new_code}' مستخدم بالفعل")
             
        db.execute(text("""
            UPDATE accounts 
            SET name = :name, name_en = :name_en, account_code = :code,
                account_type = COALESCE(:account_type, account_type),
                parent_id = :parent_id,
                currency = COALESCE(:currency, currency),
                is_header = COALESCE(:is_header, is_header),
                is_active = COALESCE(:is_active, is_active),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """), {
            "name": payload.get("name"),
            "name_en": payload.get("name_en"),
            "code": new_code,
            "account_type": payload.get("account_type"),
            "parent_id": payload.get("parent_id"),
            "currency": payload.get("currency"),
            "is_header": payload.get("is_header"),
            "is_active": payload.get("is_active"),
            "id": account_id
        })
        db.commit()
        
        log_activity(db, user_id=current_user.id, username=current_user.username,
                     action="accounting.account.update",
                     resource_type="account", resource_id=str(account_id),
                     details={"fields": list(payload.keys())},
                     request=request)
        
        # Invalidate cache
        try:
            cache.delete(f"chart_of_accounts:{current_user.company_id}")
        except Exception:
            pass
            
        return {"success": True, "message": "تم تحديث الحساب بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating account: {str(e)}")
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()

@router.post("/journal-entries", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("accounting.edit"))])
@limiter.limit("100/minute")
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
    Supports Idempotency-Key header to prevent duplicate entries on retries.
    """
    db = get_db_connection(current_user.company_id)
    try:
        # Idempotency check (Constitution XXIII)
        idempotency_key = request.headers.get("Idempotency-Key")
        if idempotency_key:
            existing = db.execute(text("""
                SELECT id, entry_number, status FROM journal_entries
                WHERE idempotency_key = :key
                LIMIT 1
            """), {"key": idempotency_key}).fetchone()
            if existing:
                return {"success": True, "message": "قيد موجود مسبقاً (مفتاح تكرار)", "entry_number": existing.entry_number, "entry_id": existing.id, "status": existing.status, "idempotent": True}

        from services.gl_service import create_journal_entry as gl_create_journal_entry
        
        entry_status = entry_data.get("status", "posted")
        
        journal_id, entry_number = gl_create_journal_entry(
            db=db,
            company_id=current_user.company_id,
            date=entry_data.get("date"),
            description=entry_data.get("description", ""),
            lines=entry_data.get("lines", []),
            user_id=current_user.id,
            branch_id=entry_data.get("branch_id"),
            reference=entry_data.get("reference"),
            status=entry_status,
            currency=entry_data.get("currency"),
            exchange_rate=_dec(entry_data.get("exchange_rate", 1)),
            source="Manual",
            source_id=None,
            username=current_user.username,
            idempotency_key=idempotency_key,
        )

        db.commit()
        invalidate_company_cache(str(current_user.company_id))
        

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

        # Notify admins on posted entries
        if entry_status == "posted":
            try:
                db.execute(text("""
                    INSERT INTO notifications (user_id, type, title, message, link, is_read, created_at)
                    SELECT DISTINCT u.id, 'journal_entry', :title, :message, :link, FALSE, NOW()
                    FROM company_users u
                    WHERE u.is_active = TRUE AND u.role IN ('admin', 'superuser')
                    AND u.id != :current_uid
                """), {
                    "title": "📝 تم ترحيل قيد يومية",
                    "message": f"تم ترحيل القيد {entry_number} — {entry_data.get('description', '')[:80]}",
                    "link": f"/accounting/journal/{journal_id}",
                    "current_uid": current_user.id
                })
                db.commit()
            except Exception:
                pass

        return {"success": True, "message": msg, "entry_number": entry_number, "entry_id": journal_id, "status": entry_status}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating journal: {str(e)}")
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()

# ============================================================
# Journal Entries Listing & Draft Workflow (ACC-002)
# ============================================================

@router.get("/journal-entries", dependencies=[Depends(require_permission("accounting.view"))])
@limiter.limit("200/minute")
def list_journal_entries(
    request: Request,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
    branch_id: Optional[int] = None,
    page: int = 1,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """قائمة القيود اليومية مع فلترة"""
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    try:
        conditions = []
        params = {}

        # Branch filtering
        if branch_id:
            conditions.append("je.branch_id = :branch_id")
            params["branch_id"] = branch_id
        else:
            allowed_branches = getattr(current_user, 'allowed_branches', [])
            if allowed_branches and "*" not in getattr(current_user, 'permissions', []):
                conditions.append("je.branch_id = ANY(:allowed_branches)")
                params["allowed_branches"] = allowed_branches

        if search and search.strip() in ('draft', 'posted', 'voided'):
            conditions.append("je.status = :status_val")
            params["status_val"] = search.strip()

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
@limiter.limit("200/minute")
def get_journal_entry(
    request: Request,
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

        # Branch access check
        if entry.branch_id:
            validate_branch_access(current_user, entry.branch_id)

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
@limiter.limit("100/minute")
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
        je_rate = _dec(entry.exchange_rate or 1)

        from utils.accounting import update_account_balance
        for line in lines:
            debit_base = _dec(line.debit)
            credit_base = _dec(line.credit)
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
        invalidate_company_cache(str(current_user.company_id))
        

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

        # Notify admins about posted journal entry
        try:
            db.execute(text("""
                INSERT INTO notifications (user_id, type, title, message, link, is_read, created_at)
                SELECT DISTINCT u.id, 'journal_entry', :title, :message, :link, FALSE, NOW()
                FROM company_users u
                WHERE u.is_active = TRUE AND u.role IN ('admin', 'superuser')
                AND u.id != :current_uid
            """), {
                "title": "📝 تم ترحيل قيد يومية",
                "message": f"تم ترحيل القيد {entry.entry_number} — {entry.description[:80] if entry.description else ''}",
                "link": f"/accounting/journal/{entry_id}",
                "current_uid": current_user.id
            })
            db.commit()
        except Exception:
            pass

        return {"success": True, "message": "تم ترحيل القيد بنجاح", "entry_number": entry.entry_number}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error posting journal entry: {e}")
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
@router.post("/journal-entries/{entry_id}/void", dependencies=[Depends(require_permission("accounting.manage"))])
@limiter.limit("100/minute")
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
        
        # 3. Create reversal entry via centralized GL service
        rev_lines = []
        for line in lines:
            rev_lines.append({
                "account_id": line.account_id,
                "debit": _dec(line.credit or 0),
                "credit": _dec(line.debit or 0),
                "description": f"عكس: {line.description or ''}",
                "amount_currency": _dec(line.amount_currency or 0),
                "currency": line.currency,
                "cost_center_id": line.cost_center_id,
            })

        rev_id, rev_entry_number = gl_create_journal_entry(
            db=db,
            company_id=current_user.company_id,
            date=str(date.today()),
            description=f"عكس قيد: {original.description}",
            lines=rev_lines,
            user_id=current_user.id,
            branch_id=original.branch_id,
            reference=original.entry_number,
            currency=original.currency,
            exchange_rate=_dec(original.exchange_rate or 1),
            source="journal_void",
            source_id=entry_id,
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
            details={"original_entry": original.entry_number, "reversal_entry": rev_entry_number},
            request=request,
            branch_id=original.branch_id
        )
        
        return {
            "success": True, 
            "message": "تم إلغاء القيد بنجاح وإنشاء قيد عكسي",
            "reversal_entry_id": rev_id,
            "reversal_entry_number": rev_entry_number
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error voiding journal entry: {str(e)}")
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
# ============================================================
# Fiscal Year Management & Year-End Closing (ACC-001)
# ============================================================

@router.get("/fiscal-years", dependencies=[Depends(require_permission("accounting.view"))])
@limiter.limit("200/minute")
def list_fiscal_years(request: Request, current_user: dict = Depends(get_current_user)):
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
@limiter.limit("100/minute")
def create_fiscal_year(
    request: Request,
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
                        INSERT INTO fiscal_periods (name, start_date, end_date, fiscal_year, is_closed)
                        VALUES (:name, :start, :end, :year, false)
                    """), {
                        "name": f"{months_ar[m-1]} {data.year}",
                        "start": start_d,
                        "end": end_d,
                        "year": data.year
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
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
@router.get("/fiscal-years/{year}/preview-closing", dependencies=[Depends(require_permission("accounting.manage"))])
@limiter.limit("200/minute")
def preview_year_end_closing(
    request: Request,
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

        total_revenue = sum(_dec(r.balance) for r in revenue_accounts)
        total_expenses = sum(_dec(r.balance) for r in expense_accounts)
        net_income = (total_revenue - total_expenses).quantize(_D4, ROUND_HALF_UP)

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
                 "name_en": r.name_en, "balance": float(_dec(r.balance).quantize(_D4, ROUND_HALF_UP))}
                for r in revenue_accounts
            ],
            "expense_accounts": [
                {"id": r.id, "account_number": r.account_number, "name": r.name,
                 "name_en": r.name_en, "balance": float(_dec(r.balance).quantize(_D4, ROUND_HALF_UP))}
                for r in expense_accounts
            ],
            "total_revenue": float(total_revenue.quantize(_D4, ROUND_HALF_UP)),
            "total_expenses": float(total_expenses.quantize(_D4, ROUND_HALF_UP)),
            "net_income": float(net_income.quantize(_D4, ROUND_HALF_UP)),
            "retained_earnings_account": {
                "id": re_acc.id, "account_number": re_acc.account_number,
                "name": re_acc.name, "name_en": re_acc.name_en
            } if re_acc else None,
            "result_type": "profit" if net_income >= 0 else "loss"
        }
    finally:
        db.close()
@router.post("/fiscal-years/{year}/close", dependencies=[Depends(require_permission("accounting.manage"))])
@limiter.limit("100/minute")
def close_fiscal_year(
    request: Request,
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

        total_revenue = sum(_dec(r.balance) for r in revenue_data)
        total_expenses = sum(_dec(r.balance) for r in expense_data)
        net_income = (total_revenue - total_expenses).quantize(_D4, ROUND_HALF_UP)

        if not revenue_data and not expense_data:
            raise HTTPException(status_code=400,
                detail="لا توجد حركات إيرادات أو مصاريف لهذه السنة المالية")

        # 4. Build and create the closing journal entry via centralized GL service
        closing_lines = []

        # A) Close revenue accounts (debit revenue to zero it out)
        for rev in revenue_data:
            balance = _dec(rev.balance).quantize(_D4, ROUND_HALF_UP)
            closing_lines.append({
                "account_id": rev.id,
                "debit": abs(balance),
                "credit": 0,
                "description": f"إقفال حساب إيرادات - {year}",
            })

        # B) Close expense accounts (credit expense to zero it out)
        for exp in expense_data:
            balance = _dec(exp.balance).quantize(_D4, ROUND_HALF_UP)
            closing_lines.append({
                "account_id": exp.id,
                "debit": 0,
                "credit": abs(balance),
                "description": f"إقفال حساب مصاريف - {year}",
            })

        # C) Transfer net income to retained earnings
        if net_income >= 0:
            closing_lines.append({
                "account_id": re_account_id,
                "debit": 0,
                "credit": abs(net_income),
                "description": f"ترحيل صافي ربح {year} إلى الأرباح المبقاة",
            })
        else:
            closing_lines.append({
                "account_id": re_account_id,
                "debit": abs(net_income),
                "credit": 0,
                "description": f"ترحيل صافي خسارة {year} إلى الأرباح المبقاة",
            })

        entry_id, entry_num = gl_create_journal_entry(
            db=db,
            company_id=current_user.company_id,
            date=str(fy.end_date),
            description=f"قيد إقفال السنة المالية {year} - ترحيل صافي {'الربح' if net_income >= 0 else 'الخسارة'} إلى الأرباح المبقاة",
            lines=closing_lines,
            user_id=current_user.id,
            reference=f"Year-End Closing {year}",
            source="fiscal_year_closing",
            source_id=fy.id,
        )

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
                     details={"year": year, "net_income": float(net_income.quantize(_D4, ROUND_HALF_UP))})

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
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
@router.post("/fiscal-years/{year}/reopen", dependencies=[Depends(require_permission("accounting.manage"))])
@limiter.limit("100/minute")
def reopen_fiscal_year(
    request: Request,
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
            closing_entry = db.execute(text("""
                SELECT entry_number, branch_id, currency, exchange_rate
                FROM journal_entries
                WHERE id = :id
            """), {"id": fy.closing_entry_id}).fetchone()

            closing_lines = db.execute(text("""
                SELECT account_id, debit, credit FROM journal_lines
                WHERE journal_entry_id = :id
            """), {"id": fy.closing_entry_id}).fetchall()

            rev_lines = []
            for line in closing_lines:
                rev_lines.append({
                    "account_id": line.account_id,
                    "debit": _dec(line.credit or 0),
                    "credit": _dec(line.debit or 0),
                    "description": f"عكس إقفال {year}",
                })

            rev_id, _ = gl_create_journal_entry(
                db=db,
                company_id=current_user.company_id,
                date=str(fy.end_date),
                description=f"عكس قيد إقفال السنة المالية {year}" + (f" - {data.reason}" if data.reason else ""),
                lines=rev_lines,
                user_id=current_user.id,
                branch_id=closing_entry.branch_id if closing_entry else None,
                reference=f"Reversal of Year-End Closing {year}",
                currency=closing_entry.currency if closing_entry else None,
                exchange_rate=_dec(closing_entry.exchange_rate or 1) if closing_entry else Decimal("1"),
                source="fiscal_year_reopen",
                source_id=fy.id,
            )

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
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
@router.get("/fiscal-years/{year}/periods", dependencies=[Depends(require_permission("accounting.view"))])
@limiter.limit("200/minute")
def list_fiscal_periods(
    request: Request,
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
@limiter.limit("100/minute")
def toggle_fiscal_period(
    request: Request,
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

        # Audit log for fiscal period lock/unlock (FR-024)
        log_activity(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action=f"fiscal_period.{'lock' if new_status else 'unlock'}",
            resource_type="fiscal_period",
            resource_id=str(period_id),
            details={"period_name": period.name, "new_status": "locked" if new_status else "unlocked"},
        )

        return {"success": True, "message": f"تم {action} الفترة {period.name}", "is_closed": new_status}
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
# ==================== ACC-003: Recurring Journal Templates ====================

@router.get("/recurring-templates", dependencies=[Depends(require_permission("accounting.view"))])
@limiter.limit("200/minute")
def list_recurring_templates(
    request: Request,
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
@limiter.limit("200/minute")
def get_recurring_template(request: Request, template_id: int, current_user: dict = Depends(get_current_user)):
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
            raise HTTPException(**http_error(404, "template_not_found"))

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
@limiter.limit("100/minute")
def create_recurring_template(request: Request, data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """إنشاء قالب قيد متكرر جديد"""
    db = get_db_connection(current_user.company_id)
    try:
        lines = data.pop("lines", [])
        if not lines or len(lines) < 2:
            raise HTTPException(status_code=400, detail="يجب إضافة سطرين على الأقل")

        total_debit = sum(_dec(l.get("debit", 0)) for l in lines)
        total_credit = sum(_dec(l.get("credit", 0)) for l in lines)
        if (total_debit - total_credit).copy_abs() > _D4:
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
            "exchange_rate": _dec(data.get("exchange_rate", 1)),
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
                "debit": _dec(line.get("debit", 0)),
                "credit": _dec(line.get("credit", 0)),
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
    except Exception:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
@router.put("/recurring-templates/{template_id}", dependencies=[Depends(require_permission("accounting.edit"))])
@limiter.limit("100/minute")
def update_recurring_template(request: Request, template_id: int, data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """تعديل قالب قيد متكرر"""
    db = get_db_connection(current_user.company_id)
    try:
        existing = db.execute(text("SELECT id FROM recurring_journal_templates WHERE id = :id"), {"id": template_id}).fetchone()
        if not existing:
            raise HTTPException(**http_error(404, "template_not_found"))

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
            total_debit = sum(_dec(l.get("debit", 0)) for l in lines)
            total_credit = sum(_dec(l.get("credit", 0)) for l in lines)
            if (total_debit - total_credit).copy_abs() > _D4:
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
                    "debit": _dec(line.get("debit", 0)),
                    "credit": _dec(line.get("credit", 0)),
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
    except Exception:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
@router.delete("/recurring-templates/{template_id}", dependencies=[Depends(require_permission("accounting.manage"))])
@limiter.limit("100/minute")
def delete_recurring_template(request: Request, template_id: int, current_user: dict = Depends(get_current_user)):
    """حذف قالب قيد متكرر"""
    db = get_db_connection(current_user.company_id)
    try:
        existing = db.execute(text(
            "SELECT id, name FROM recurring_journal_templates WHERE id = :id"
        ), {"id": template_id}).fetchone()
        if not existing:
            raise HTTPException(**http_error(404, "template_not_found"))

        db.execute(text("DELETE FROM recurring_journal_templates WHERE id = :id"), {"id": template_id})
        db.commit()
        log_activity(db, user_id=current_user.id, username=current_user.username,
                     action="accounting.recurring_template.delete",
                     resource_type="recurring_template", resource_id=str(template_id),
                     details={"name": existing.name})
        return {"success": True, "message": "تم حذف القالب بنجاح"}
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
@router.post("/recurring-templates/{template_id}/generate", dependencies=[Depends(require_permission("accounting.edit"))])
@limiter.limit("100/minute")
def generate_from_template(request: Request, template_id: int, current_user: dict = Depends(get_current_user)):
    """توليد قيد يومي من قالب متكرر يدوياً"""
    db = get_db_connection(current_user.company_id)
    try:
        tmpl = db.execute(text(
            "SELECT * FROM recurring_journal_templates WHERE id = :id"
        ), {"id": template_id}).fetchone()
        if not tmpl:
            raise HTTPException(**http_error(404, "template_not_found"))

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
    except Exception:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
@router.post("/recurring-templates/generate-due", dependencies=[Depends(require_permission("accounting.manage"))])
@limiter.limit("100/minute")
def generate_all_due_templates(request: Request, current_user: dict = Depends(get_current_user)):
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
    except Exception:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
def _create_entry_from_template(db, tmpl, lines, current_user):
    """Helper: إنشاء قيد يومي من قالب متكرر"""

    today = date.today()
    entry_status = "posted" if tmpl.auto_post else "draft"
    description = f"{tmpl.name} - {today.strftime('%Y-%m-%d')}"
    if tmpl.description:
        description = f"{tmpl.description} ({today.strftime('%Y-%m-%d')})"

    je_lines = []
    for line in lines:
        je_lines.append({
            "account_id": line.account_id,
            "debit": _dec(line.debit or 0),
            "credit": _dec(line.credit or 0),
            "description": line.description or "",
            "cost_center_id": line.cost_center_id,
        })

    entry_id, _ = gl_create_journal_entry(
        db=db,
        company_id=current_user.company_id,
        date=str(today),
        description=description,
        lines=je_lines,
        user_id=current_user.id,
        branch_id=tmpl.branch_id or getattr(current_user, "branch_id", None),
        reference=tmpl.reference or f"REC-{tmpl.id}",
        status=entry_status,
        currency=tmpl.currency or get_base_currency(db),
        exchange_rate=_dec(tmpl.exchange_rate or 1),
        source="recurring_template",
        source_id=tmpl.id,
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
@limiter.limit("200/minute")
def get_opening_balances(
    request: Request,
    current_user: dict = Depends(get_current_user),
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

        ob_map = {l.account_id: {"debit": _dec(l.debit or 0), "credit": _dec(l.credit or 0)} for l in ob_lines}

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
@limiter.limit("100/minute")
def save_opening_balances(
    request: Request,
    data: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """حفظ الأرصدة الافتتاحية (ينشئ أو يحدث قيد الأرصدة الافتتاحية)"""
    db = get_db_connection(current_user.company_id)
    try:
        lines = data.get("lines", [])
        entry_date = data.get("date", str(date.today()))

        # Filter to only lines with actual values
        valid_lines = [l for l in lines if _dec(l.get("debit", 0)) != 0 or _dec(l.get("credit", 0)) != 0]
        if not valid_lines:
            raise HTTPException(status_code=400, detail="لا توجد أرصدة لحفظها")

        total_debit = sum(_dec(l.get("debit", 0)) for l in valid_lines)
        total_credit = sum(_dec(l.get("credit", 0)) for l in valid_lines)

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
                        debit_base=_dec(ol.credit or 0),
                        credit_base=_dec(ol.debit or 0))

            # Replace old opening balance entry with a fresh centralized one
            db.execute(text("DELETE FROM journal_entries WHERE id = :eid"), {"eid": existing.id})

        # Default behavior is strict: reject imbalanced opening balances.
        # Admin can explicitly allow suspense adjustment by passing allow_auto_balance=true.
        diff = (total_debit - total_credit).quantize(_D4, ROUND_HALF_UP)
        if diff.copy_abs() > _D4:
            allow_auto_balance = bool(data.get("allow_auto_balance", False))
            if not allow_auto_balance:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "الأرصدة الافتتاحية غير متوازنة. "
                        f"الفرق الحالي: {diff}. "
                        "صحّح الأرصدة أو أعد الطلب مع allow_auto_balance=true للموازنة الاستثنائية."
                    ),
                )

            suspense = db.execute(text(
                "SELECT id FROM accounts WHERE account_number = '3100' OR (account_type = 'equity' AND name LIKE '%افتتا%') LIMIT 1"
            )).fetchone()
            if not suspense:
                suspense = db.execute(text(
                    "SELECT id FROM accounts WHERE account_type = 'equity' ORDER BY account_number LIMIT 1"
                )).fetchone()
            if not suspense:
                raise HTTPException(status_code=400, detail="لا يوجد حساب حقوق ملكية لتعويض فرق الأرصدة الافتتاحية")

            valid_lines.append({
                "account_id": suspense.id,
                "debit": max(-diff, Decimal("0")).quantize(_D4, ROUND_HALF_UP),
                "credit": max(diff, Decimal("0")).quantize(_D4, ROUND_HALF_UP),
                "description": "فرق الأرصدة الافتتاحية / Opening Balance Difference"
            })

        gl_lines = []
        for line in valid_lines:
            gl_lines.append({
                "account_id": int(line["account_id"]),
                "debit": _dec(line.get("debit", 0)),
                "credit": _dec(line.get("credit", 0)),
                "description": line.get("description", "رصيد افتتاحي"),
            })

        entry_id, _ = gl_create_journal_entry(
            db=db,
            company_id=current_user.company_id,
            date=entry_date,
            description="أرصدة افتتاحية / Opening Balances",
            lines=gl_lines,
            user_id=current_user.id,
            branch_id=getattr(current_user, "branch_id", None),
            reference="OPENING-BALANCE",
            source="opening_balances",
        )

        db.commit()
        log_activity(db, user_id=current_user.id, username=current_user.username,
                     action="accounting.opening_balances.save",
                     resource_type="opening_balances", resource_id=str(entry_id),
                     details={"lines_count": len(valid_lines)})
        return {"success": True, "entry_id": entry_id, "lines_count": len(valid_lines),
                "message": "تم حفظ الأرصدة الافتتاحية بنجاح"}
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
# ==================== ACC-006: Automatic Closing Entries ====================

@router.get("/closing-entries/preview", dependencies=[Depends(require_permission("accounting.manage"))])
@limiter.limit("200/minute")
def preview_closing_entries(
    request: Request,
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

        total_revenue = sum(_dec(r.balance) for r in revenues)
        total_expense = sum(_dec(r.balance) for r in expenses)
        net_income = (total_revenue - total_expense).quantize(_D4, ROUND_HALF_UP)

        return {
            "period": {"start": str(start_date), "end": str(end_date)},
            "revenues": [dict(r._mapping) for r in revenues],
            "expenses": [dict(r._mapping) for r in expenses],
            "total_revenue": float(total_revenue.quantize(_D4, ROUND_HALF_UP)),
            "total_expense": float(total_expense.quantize(_D4, ROUND_HALF_UP)),
            "net_income": float(net_income.quantize(_D4, ROUND_HALF_UP)),
            "income_summary_account": dict(income_summary._mapping) if income_summary else None,
            "retained_earnings_account": dict(retained_earnings._mapping) if retained_earnings else None,
        }
    finally:
        db.close()
@router.post("/closing-entries/generate", dependencies=[Depends(require_permission("accounting.manage"))])
@limiter.limit("100/minute")
def generate_closing_entries(
    request: Request,
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

        total_revenue = sum(_dec(r.balance) for r in revenues)
        total_expense = sum(_dec(r.balance) for r in expenses)
        net_income = (total_revenue - total_expense).quantize(_D4, ROUND_HALF_UP)

        created_entries = []
        target_account_id = income_summary_id if use_income_summary else retained_earnings_id

        # Entry 1: Close Revenue accounts
        if revenues:
            lines1 = []

            for rev in revenues:
                bal = _dec(rev.balance).quantize(_D4, ROUND_HALF_UP)
                lines1.append({
                    "account_id": rev.id,
                    "debit": bal,
                    "credit": 0,
                    "description": f"إقفال {rev.name}",
                })

            lines1.append({
                "account_id": target_account_id,
                "debit": 0,
                "credit": total_revenue,
                "description": "إجمالي الإيرادات المقفلة",
            })

            eid1, num1 = gl_create_journal_entry(
                db=db,
                company_id=current_user.company_id,
                date=entry_date_str,
                description=f"إقفال حسابات الإيرادات - {start_date_str} إلى {end_date_str}",
                lines=lines1,
                user_id=current_user.id,
                branch_id=branch_id or getattr(current_user, "branch_id", None),
                reference="CLOSING-REVENUE",
                source="closing_entries_revenue",
            )

            created_entries.append({"id": eid1, "type": "close_revenue", "number": num1})

        # Entry 2: Close Expense accounts
        if expenses:
            lines2 = []

            for exp in expenses:
                bal = _dec(exp.balance).quantize(_D4, ROUND_HALF_UP)
                lines2.append({
                    "account_id": exp.id,
                    "debit": 0,
                    "credit": bal,
                    "description": f"إقفال {exp.name}",
                })

            lines2.append({
                "account_id": target_account_id,
                "debit": total_expense,
                "credit": 0,
                "description": "إجمالي المصاريف المقفلة",
            })

            eid2, num2 = gl_create_journal_entry(
                db=db,
                company_id=current_user.company_id,
                date=entry_date_str,
                description=f"إقفال حسابات المصاريف - {start_date_str} إلى {end_date_str}",
                lines=lines2,
                user_id=current_user.id,
                branch_id=branch_id or getattr(current_user, "branch_id", None),
                reference="CLOSING-EXPENSE",
                source="closing_entries_expense",
            )

            created_entries.append({"id": eid2, "type": "close_expense", "number": num2})

        # Entry 3: Transfer Income Summary → Retained Earnings
        if use_income_summary and net_income != 0:
            lines3 = []

            if net_income > 0:
                # Profit: Debit Income Summary, Credit Retained Earnings
                lines3.append({
                    "account_id": income_summary_id,
                    "debit": net_income,
                    "credit": 0,
                    "description": "إقفال ملخص الدخل",
                })
                lines3.append({
                    "account_id": retained_earnings_id,
                    "debit": 0,
                    "credit": net_income,
                    "description": "صافي أرباح الفترة",
                })
            else:
                loss = abs(net_income)
                # Loss: Credit Income Summary, Debit Retained Earnings
                lines3.append({
                    "account_id": income_summary_id,
                    "debit": 0,
                    "credit": loss,
                    "description": "إقفال ملخص الدخل",
                })
                lines3.append({
                    "account_id": retained_earnings_id,
                    "debit": loss,
                    "credit": 0,
                    "description": "صافي خسائر الفترة",
                })

            eid3, num3 = gl_create_journal_entry(
                db=db,
                company_id=current_user.company_id,
                date=entry_date_str,
                description=f"ترحيل ملخص الدخل إلى الأرباح المبقاة - صافي: {net_income}",
                lines=lines3,
                user_id=current_user.id,
                branch_id=branch_id or getattr(current_user, "branch_id", None),
                reference="CLOSING-TRANSFER",
                source="closing_entries_transfer",
            )

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
    except Exception:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
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
@limiter.limit("100/minute")
def create_bad_debt_provision(request: Request, req: ProvisionRequest, current_user: dict = Depends(get_current_user)):
    """إنشاء قيد مخصص ديون معدومة — Dr مصروف ديون معدومة / Cr مخصص الديون المعدومة"""
    from utils.accounting import get_mapped_account_id, get_base_currency
    branch_id = validate_branch_access(current_user, req.branch_id)
    db = get_db_connection(current_user.company_id)
    trans = db.begin()
    try:
        base_currency = get_base_currency(db)
        acc_bad_debt_exp = get_mapped_account_id(db, "acc_map_bad_debt_expense")
        acc_prov_doubtful = get_mapped_account_id(db, "acc_map_provision_doubtful")
        if not acc_bad_debt_exp or not acc_prov_doubtful:
            raise HTTPException(status_code=400, detail="لم يتم تعيين حسابات الديون المعدومة في الإعدادات")

        desc = req.description or "مخصص ديون معدومة"
        _, je_num = gl_create_journal_entry(
            db=db,
            company_id=current_user.company_id,
            date=str(date.today()),
            description=desc,
            lines=[
                {
                    "account_id": acc_bad_debt_exp,
                    "debit": _dec(req.amount),
                    "credit": 0,
                    "description": "مصروف ديون معدومة",
                    "amount_currency": _dec(req.amount),
                    "currency": base_currency,
                },
                {
                    "account_id": acc_prov_doubtful,
                    "debit": 0,
                    "credit": _dec(req.amount),
                    "description": "مخصص الديون المعدومة",
                    "amount_currency": _dec(req.amount),
                    "currency": base_currency,
                },
            ],
            user_id=current_user.id,
            branch_id=branch_id,
            reference="BAD-DEBT-PROV",
            currency=base_currency,
            exchange_rate=1,
            source="bad_debt_provision",
        )

        trans.commit()
        return {"success": True, "journal_entry": je_num, "amount": req.amount}
    except HTTPException:
        trans.rollback()
        raise
    except Exception:
        trans.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
# ═══════════════════════════════════════════════════════════
# GL-005: Leave Provision (مخصص إجازات)
# ═══════════════════════════════════════════════════════════

@router.post("/provisions/leave", dependencies=[Depends(require_permission("accounting.manage"))])
@limiter.limit("100/minute")
def create_leave_provision(request: Request, req: ProvisionRequest, current_user: dict = Depends(get_current_user)):
    """إنشاء قيد مخصص إجازات — Dr مصروف إجازات / Cr مخصص الإجازات"""
    from utils.accounting import get_mapped_account_id, get_base_currency
    branch_id = validate_branch_access(current_user, req.branch_id)
    db = get_db_connection(current_user.company_id)
    trans = db.begin()
    try:
        base_currency = get_base_currency(db)
        acc_leave_exp = get_mapped_account_id(db, "acc_map_leave_expense")
        acc_leave_prov = get_mapped_account_id(db, "acc_map_provision_holiday")
        if not acc_leave_exp or not acc_leave_prov:
            raise HTTPException(status_code=400, detail="لم يتم تعيين حسابات الإجازات في الإعدادات")

        desc = req.description or "مخصص إجازات الموظفين"
        _, je_num = gl_create_journal_entry(
            db=db,
            company_id=current_user.company_id,
            date=str(date.today()),
            description=desc,
            lines=[
                {
                    "account_id": acc_leave_exp,
                    "debit": _dec(req.amount),
                    "credit": 0,
                    "description": "مصروف الإجازات",
                    "amount_currency": _dec(req.amount),
                    "currency": base_currency,
                },
                {
                    "account_id": acc_leave_prov,
                    "debit": 0,
                    "credit": _dec(req.amount),
                    "description": "مخصص الإجازات",
                    "amount_currency": _dec(req.amount),
                    "currency": base_currency,
                },
            ],
            user_id=current_user.id,
            branch_id=branch_id,
            reference="LEAVE-PROV",
            currency=base_currency,
            exchange_rate=1,
            source="leave_provision",
        )

        trans.commit()
        return {"success": True, "journal_entry": je_num, "amount": req.amount}
    except HTTPException:
        trans.rollback()
        raise
    except Exception:
        trans.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
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
@limiter.limit("100/minute")
def fx_revaluation(request: Request, req: FXRevaluationRequest, current_user: dict = Depends(get_current_user)):
    """إعادة تقييم أرصدة العملات الأجنبية — الفروقات تسجل كربح/خسارة غير محققة"""
    from utils.accounting import get_base_currency
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
        total_diff = Decimal("0")
        je_lines = []

        new_rate = _dec(req.new_rate)

        for bal in balances:
            m = bal._mapping
            fc = _dec(m["fc_balance"])
            old_base = _dec(m["base_balance"])
            new_base = (fc * new_rate).quantize(_D2, ROUND_HALF_UP)
            diff = (new_base - old_base).quantize(_D2, ROUND_HALF_UP)
            if diff.copy_abs() < _D2:
                continue

            total_diff += diff
            if diff > 0:
                je_lines.append({
                    "account_id": m["account_id"],
                    "debit": abs(diff),
                    "credit": 0,
                    "description": f"تعديل سعر {req.currency_code}",
                    "amount_currency": 0,
                    "currency": base_currency,
                })
            else:
                je_lines.append({
                    "account_id": m["account_id"],
                    "debit": 0,
                    "credit": abs(diff),
                    "description": f"تعديل سعر {req.currency_code}",
                    "amount_currency": 0,
                    "currency": base_currency,
                })

            adjustments.append({
                "account_id": m["account_id"], "account_number": m["account_number"], "name": m["name"],
                "fc_balance": float(fc.quantize(_D2, ROUND_HALF_UP)),
                "old_base": float(old_base.quantize(_D2, ROUND_HALF_UP)),
                "new_base": float(new_base.quantize(_D2, ROUND_HALF_UP)),
                "difference": float(diff.quantize(_D2, ROUND_HALF_UP)),
            })

        # Post the offsetting FX gain/loss
        if total_diff > 0 and ufx_gain:
            je_lines.append({
                "account_id": ufx_gain,
                "debit": 0,
                "credit": abs(total_diff),
                "description": "أرباح فروقات عملة (غير محققة)",
                "amount_currency": 0,
                "currency": base_currency,
            })
        elif total_diff < 0 and ufx_loss:
            je_lines.append({
                "account_id": ufx_loss,
                "debit": abs(total_diff),
                "credit": 0,
                "description": "خسائر فروقات عملة (غير محققة)",
                "amount_currency": 0,
                "currency": base_currency,
            })

        je_num = None
        if je_lines:
            _, je_num = gl_create_journal_entry(
                db=db,
                company_id=current_user.company_id,
                date=str(date.today()),
                description=f"إعادة تقييم عملة {req.currency_code} بسعر {req.new_rate}",
                lines=je_lines,
                user_id=current_user.id,
                branch_id=branch_id,
                reference=f"FX-REVAL-{req.currency_code}",
                currency=base_currency,
                exchange_rate=1,
                source="fx_revaluation",
            )

        trans.commit()
        return {
            "success": True, "journal_entry": je_num,
            "currency": req.currency_code, "new_rate": req.new_rate,
            "total_adjustment": float(total_diff.quantize(_D2, ROUND_HALF_UP)),
            "adjustments": adjustments,
        }
    except HTTPException:
        trans.rollback()
        raise
    except Exception:
        trans.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()