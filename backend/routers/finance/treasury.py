"""
AMAN ERP - Treasury Router
إدارة الخزينة والمصروفات
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import date
from pydantic import BaseModel
import logging

from decimal import Decimal, ROUND_HALF_UP

from database import get_db_connection
from routers.auth import get_current_user
from utils.permissions import require_permission, require_module
from utils.audit import log_activity
from utils.accounting import update_account_balance, validate_je_lines
from utils.fiscal_lock import check_fiscal_period_open
from utils.cache import cache
from fastapi import Request
from schemas.treasury import TreasuryAccountCreate, TreasuryAccountResponse, TransactionCreate, TransactionResponse

_D2 = Decimal('0.01')
def _dec(v) -> Decimal:
    """Convert any numeric value to Decimal safely."""
    return Decimal(str(v)) if v is not None else Decimal('0')

router = APIRouter(prefix="/treasury", tags=["الخزينة والمصروفات"], dependencies=[Depends(require_module("treasury"))])
logger = logging.getLogger(__name__)

# --- Endpoints ---

@router.get("/accounts", response_model=List[TreasuryAccountResponse], dependencies=[Depends(require_permission("treasury.view"))])
def list_treasury_accounts(branch_id: Optional[int] = None, current_user = Depends(get_current_user)):
    """عرض حسابات الخزينة والبنوك مع فلترة حسب الفرع"""
    if not current_user.company_id:
         raise HTTPException(status_code=400, detail="يجب تحديد الشركة أولاً")
         
    db = get_db_connection(current_user.company_id)
    try:
        query = """
            SELECT 
                ta.id, ta.name, ta.name_en, ta.account_type, ta.currency, 
                ta.gl_account_id, ta.branch_id, ta.bank_name, ta.account_number, 
                ta.iban, ta.is_active,
                COALESCE(a.balance, 0) as current_balance,
                COALESCE(ta.current_balance, 0) as balance_in_currency,
                b.branch_name as branch_name,
                COALESCE(c.current_rate, 1.0) as exchange_rate
            FROM treasury_accounts ta
            LEFT JOIN branches b ON ta.branch_id = b.id
            LEFT JOIN accounts a ON ta.gl_account_id = a.id
            LEFT JOIN currencies c ON ta.currency = c.code
            WHERE ta.is_active = TRUE
        """
        params = {}
        if branch_id:
            query += " AND ta.branch_id = :branch_id"
            params["branch_id"] = branch_id
        query += " ORDER BY ta.id"
        
        result = db.execute(text(query), params).fetchall()
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

@router.get("/transactions", response_model=List[TransactionResponse], dependencies=[Depends(require_permission("treasury.view"))])
def list_transactions(branch_id: Optional[int] = None, limit: int = 50, current_user = Depends(get_current_user)):
    """عرض سجل العمليات الأخيرة"""
    if not current_user.company_id:
         raise HTTPException(status_code=400, detail="يجب تحديد الشركة أولاً")
         
    db = get_db_connection(current_user.company_id)
    try:
        query_str = """
            SELECT 
                t.id, 
                t.transaction_number, 
                t.transaction_date, 
                t.transaction_type, 
                t.amount, 
                t.description, 
                to_char(t.created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at,
                ta.name as treasury_name,
                COALESCE(ta_target.name, gl.name) as target_name,
                'posted' as status
            FROM treasury_transactions t
            LEFT JOIN treasury_accounts ta ON t.treasury_id = ta.id
            LEFT JOIN treasury_accounts ta_target ON t.target_treasury_id = ta_target.id
            LEFT JOIN accounts gl ON t.target_account_id = gl.id
            WHERE 1=1
        """
        params = {"limit": limit}
        if branch_id:
            query_str += " AND (ta.branch_id = :bid OR t.branch_id = :bid)"
            params["bid"] = branch_id
            
        query_str += " ORDER BY t.transaction_date DESC, t.id DESC LIMIT :limit"
        
        result = db.execute(text(query_str), params).fetchall()
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

@router.post("/accounts", response_model=TreasuryAccountResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("treasury.create"))])
def create_treasury_account(request: Request, account: TreasuryAccountCreate, current_user: dict = Depends(get_current_user)):
    """
    إنشاء حساب خزينة جديد
    يقوم تلقائياً بإنشاء حساب في دليل الحسابات (GL Account) تحت الأصول المتداولة
    """
    db = get_db_connection(current_user.company_id)
    try:
        from utils.accounting import get_base_currency
        base_currency = get_base_currency(db)
        # Check for duplicate treasury account name
        existing = db.execute(text("SELECT id FROM treasury_accounts WHERE name = :name"), {"name": account.name}).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="يوجد حساب خزينة بنفس الاسم بالفعل")

        # Check for duplicate bank account number (if provided)
        if account.account_type == 'bank' and hasattr(account, 'bank_account_number') and account.bank_account_number:
            existing_bank = db.execute(text(
                "SELECT id FROM treasury_accounts WHERE bank_account_number = :ban"
            ), {"ban": account.bank_account_number}).fetchone()
            if existing_bank:
                raise HTTPException(status_code=400, detail="رقم الحساب البنكي مسجل بالفعل في حساب خزينة آخر")

        # 1. Determine Parent Account from Chart of Accounts
        # 1101 = Cash & Equivalents
        parent_account = db.execute(text("SELECT id FROM accounts WHERE account_number = '1101'")).fetchone()
        if not parent_account:
            # Fallback: Check code column
            parent_account = db.execute(text("SELECT id FROM accounts WHERE account_code = '1101'")).fetchone()
            
        if not parent_account:
            raise HTTPException(status_code=500, detail="حساب النقدية الرئيسي غير موجود في الدليل (1101)")
        
        parent_id = parent_account[0]
        
        # 2. Generate Account Code
        # Find max code under 1101
        last_acc = db.execute(text("SELECT account_code FROM accounts WHERE parent_id = :pid ORDER BY account_code DESC LIMIT 1"), {"pid": parent_id}).fetchone()
        
        new_code = "1101001"
        if last_acc and last_acc[0]:
            last_code = last_acc[0]
            if last_code.isdigit():
                 new_code = str(int(last_code) + 1)
            else:
                 # If alphanumeric, just append a random number or increment if suffix is numeric
                 # Simple fallback: use timestamp suffix to ensure uniqueness
                 import random
                 import time
                 new_code = f"1101{random.randint(100000, 999999)}"
        
        
        # 3. Create GL Account
        gl_query = text("""
            INSERT INTO accounts (account_number, account_code, name, name_en, account_type, parent_id, currency, balance, is_active)
            VALUES (:num, :code, :name, :name_en, 'asset', :pid, :curr, 0, TRUE)
            RETURNING id
        """)
        gl_id = db.execute(gl_query, {
            "num": new_code, # Use code as number for simplicity here or generate logic
            "code": new_code,
            "name": account.name,
            "name_en": account.name_en,
            "pid": parent_id,
            "curr": account.currency
        }).scalar()
        
        # Invalidate chart of accounts cache (new GL account added)
        try:
            cache.delete(f"chart_of_accounts:{current_user.company_id}")
        except Exception:
            pass

        # Invalidate chart of accounts cache (new GL account added)
        try:
            cache.delete(f"chart_of_accounts:{current_user.company_id}")
        except Exception:
            pass

        # 4. Create Treasury Account
        treasury_query = text("""
            INSERT INTO treasury_accounts (name, name_en, account_type, currency, bank_name, account_number, iban, gl_account_id, branch_id)
            VALUES (:name, :name_en, :type, :curr, :bank, :acc_num, :iban, :gl_id, :branch_id)
            RETURNING id, name, name_en, account_type, currency, bank_name, account_number, iban, gl_account_id, current_balance, is_active, branch_id
        """)
        
        new_treasury = db.execute(treasury_query, {
            "name": account.name,
            "name_en": account.name_en,
            "type": account.account_type,
            "curr": account.currency,
            "bank": account.bank_name,
            "acc_num": account.account_number,
            "iban": account.iban,
            "gl_id": gl_id,
            "branch_id": account.branch_id
        }).fetchone()
        
        # 5. Handle Opening Balance
        if account.opening_balance and account.opening_balance > 0:
            # Update Treasury Balance (Current Balance is always in account currency)
            db.execute(text("UPDATE treasury_accounts SET current_balance = :bal WHERE id = :id"), 
                       {"bal": account.opening_balance, "id": new_treasury[0]})
            
            # Credit Capital (3101 - Placeholder for Capital/Opening Balance)
            # Find Capital account or use 31 as root
            capital_acc = db.execute(text("SELECT id FROM accounts WHERE account_number = '31' OR account_code = 'CAP' LIMIT 1")).fetchone()
            capital_gl_id = capital_acc[0] if capital_acc else None
            
            if capital_gl_id:
                # Build and validate journal lines
                je_lines = [
                    {"account_id": gl_id, "debit": float(account.opening_balance), "credit": 0, "currency": account.currency, "exchange_rate": float(account.exchange_rate or 1)},
                    {"account_id": capital_gl_id, "debit": 0, "credit": float(account.opening_balance) * float(account.exchange_rate or 1), "currency": base_currency, "exchange_rate": 1.0},
                ]
                
                from services.gl_service import create_journal_entry as gl_create_journal_entry
                gl_create_journal_entry(
                    db=db,
                    company_id=current_user.company_id,
                    date=date.today().isoformat(),
                    description=f"Opening Balance - {account.name}",
                    lines=je_lines,
                    user_id=current_user.id,
                    branch_id=account.branch_id,
                    currency=base_currency,
                    exchange_rate=1.0,
                    source="treasury_account_opening",
                    source_id=new_treasury[0]
                )
        
        db.commit()

        # AUDIT LOG
        log_activity(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="treasury.account.create",
            resource_type="treasury_account",
            resource_id=str(new_treasury[0]),
            details={"name": account.name, "type": account.account_type, "opening_balance": account.opening_balance},
            request=request,
            branch_id=account.branch_id
        )

        # Refresh from DB to get updated balance from GL
        final_query = """
            SELECT ta.*, COALESCE(a.balance, 0) as current_balance
            FROM treasury_accounts ta
            LEFT JOIN accounts a ON ta.gl_account_id = a.id
            WHERE ta.id = :id
        """
        final_treasury = db.execute(text(final_query), {"id": new_treasury[0]}).fetchone()
        return dict(final_treasury._mapping)
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating treasury account: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.put("/accounts/{id}", dependencies=[Depends(require_permission("treasury.edit"))])
def update_treasury_account(
    id: int,
    account: TreasuryAccountCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """تحديث حساب خزينة"""
    db = get_db_connection(current_user.company_id)
    try:
        # Check existence
        existing = db.execute(text("SELECT id, gl_account_id FROM treasury_accounts WHERE id = :id"), {"id": id}).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="حساب الخزينة غير موجود")
        
        # Check for duplicate name (excluding current account)
        dup = db.execute(text("SELECT id FROM treasury_accounts WHERE name = :name AND id != :id"), 
                        {"name": account.name, "id": id}).fetchone()
        if dup:
            raise HTTPException(status_code=400, detail="يوجد حساب خزينة آخر بنفس الاسم")
        
        # Update treasury account
        db.execute(text("""
            UPDATE treasury_accounts SET
                name = :name,
                name_en = :name_en,
                account_type = :type,
                currency = :curr,
                bank_name = :bank,
                account_number = :acc_num,
                iban = :iban,
                branch_id = :branch_id,
                updated_at = NOW()
            WHERE id = :id
        """), {
            "id": id,
            "name": account.name,
            "name_en": account.name_en,
            "type": account.account_type,
            "curr": account.currency,
            "bank": account.bank_name,
            "acc_num": account.account_number,
            "iban": account.iban,
            "branch_id": account.branch_id
        })
        
        # Update linked GL account name
        if existing.gl_account_id:
            db.execute(text("""
                UPDATE accounts SET
                    name = :name,
                    name_en = :name_en,
                    currency = :curr
                WHERE id = :id
            """), {
                "id": existing.gl_account_id,
                "name": account.name,
                "name_en": account.name_en,
                "curr": account.currency
            })
        
        db.commit()
        
        # AUDIT LOG
        log_activity(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="treasury_account.update",
            resource_type="treasury_account",
            resource_id=str(id),
            details={"name": account.name},
            request=request,
            branch_id=account.branch_id
        )
        
        return {"id": id, "message": "تم تحديث حساب الخزينة بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating treasury account: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.delete("/accounts/{id}", dependencies=[Depends(require_permission("treasury.delete"))])
def delete_treasury_account(
    id: int,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """حذف حساب خزينة"""
    db = get_db_connection(current_user.company_id)
    try:
        # Check existence
        account = db.execute(text("SELECT id, name, current_balance, gl_account_id FROM treasury_accounts WHERE id = :id"), 
                           {"id": id}).fetchone()
        if not account:
            raise HTTPException(status_code=404, detail="حساب الخزينة غير موجود")
        
        # Check if account has balance
        if account.current_balance and abs(account.current_balance) > 0.01:
            raise HTTPException(status_code=400, detail="لا يمكن حذف حساب خزينة له رصيد")
        
        # Check if account has transactions
        usage = db.execute(text("""
            SELECT COUNT(*) FROM treasury_transactions WHERE treasury_id = :id OR target_treasury_id = :id
        """), {"id": id}).scalar()
        
        if usage and usage > 0:
            raise HTTPException(status_code=400, detail="لا يمكن حذف حساب خزينة له معاملات سابقة")
        
        # Delete treasury account (will be soft delete by setting is_active = FALSE)
        db.execute(text("UPDATE treasury_accounts SET is_active = FALSE WHERE id = :id"), {"id": id})
        
        # Optionally deactivate linked GL account
        if account.gl_account_id:
            db.execute(text("UPDATE accounts SET is_active = FALSE WHERE id = :id"), {"id": account.gl_account_id})
        
        db.commit()
        
        # AUDIT LOG
        log_activity(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="treasury_account.delete",
            resource_type="treasury_account",
            resource_id=str(id),
            details={"name": account.name},
            request=request,
            branch_id=None
        )
        
        return {"message": "تم حذف حساب الخزينة بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting treasury account: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.post("/transactions/expense", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("treasury.manage"))])
def create_expense(request: Request, data: TransactionCreate, current_user: dict = Depends(get_current_user)):
    """تسجيل مصروف جديد"""
    if data.transaction_type != 'expense':
        raise HTTPException(status_code=400, detail="Invalid transaction type")
    
    # Validate amount
    if data.amount is None or data.amount <= 0:
        raise HTTPException(status_code=400, detail="المبلغ يجب أن يكون أكبر من صفر")
        
    db = get_db_connection(current_user.company_id)
    try:
        # Validate expense account type
        if data.target_account_id:
            exp_acct = db.execute(text("SELECT account_type FROM accounts WHERE id = :id"), {"id": data.target_account_id}).fetchone()
            if not exp_acct:
                raise HTTPException(status_code=404, detail="حساب المصروفات غير موجود")
            if exp_acct.account_type not in ('expense', 'asset', 'liability'):
                raise HTTPException(status_code=400, detail=f"الحساب المحدد ليس حساب مصروفات (نوعه: {exp_acct.account_type})")
        else:
            raise HTTPException(status_code=400, detail="يجب تحديد حساب المصروفات")

        # Generate Transaction Number
        import uuid
        trans_num = f"EXP-{str(uuid.uuid4())[:8].upper()}"
        
        # 1. Get Treasury Account GL ID & Branch & Currency
        treasury = db.execute(text("SELECT gl_account_id, current_balance, branch_id, currency FROM treasury_accounts WHERE id = :id"), {"id": data.treasury_id}).fetchone()
        if not treasury:
            raise HTTPException(status_code=404, detail="الخزينة غير موجودة")
            
        treasury_gl_id, _, treasury_branch_id, treasury_currency = treasury
        exchange_rate = _dec(data.exchange_rate or 1)
        amount_base = (_dec(data.amount) * exchange_rate).quantize(_D2, ROUND_HALF_UP)
        
        # Determine the branch for this transaction (Allocation Branch)
        final_branch_id = data.branch_id if data.branch_id is not None else treasury_branch_id
        
        # Check Balance (Optional logic, maybe warn but allow?)
        # For now, allow negative balance for cash? No, let's just log it.

        # 2. Insert Treasury Transaction
        trans_id = db.execute(text("""
            INSERT INTO treasury_transactions (
                transaction_number, transaction_date, transaction_type, amount, 
                treasury_id, target_account_id, description, reference_number, created_by, branch_id
            ) VALUES (
                :num, :date, :type, :amount, :tid, :target, :desc, :ref, :uid, :bid
            ) RETURNING id
        """), {
            "num": trans_num,
            "date": data.transaction_date,
            "type": 'expense',
            "amount": data.amount,
            "tid": data.treasury_id,
            "target": data.target_account_id,
            "desc": data.description,
            "ref": data.reference_number,
            "uid": current_user.id,
            "bid": final_branch_id
        }).scalar()
        
        # 3. Update Treasury Balance
        db.execute(text("UPDATE treasury_accounts SET current_balance = current_balance - :amt WHERE id = :id"), 
                   {"amt": data.amount, "id": data.treasury_id})
        
        # 4. Create Journal Entry
        check_fiscal_period_open(db, data.transaction_date)
        
        je_lines = [
            {"account_id": data.target_account_id, "debit": float(data.amount), "credit": 0},
            {"account_id": treasury_gl_id, "debit": 0, "credit": float(data.amount)},
        ]

        from services.gl_service import create_journal_entry as gl_create_journal_entry
        je_id, _ = gl_create_journal_entry(
            db=db,
            company_id=current_user.company_id,
            date=data.transaction_date,
            description=f"Expense: {data.description} ({treasury_currency})",
            lines=je_lines,
            user_id=current_user.id,
            branch_id=final_branch_id,
            reference=trans_num,
            currency=treasury_currency,
            exchange_rate=float(exchange_rate),
            source="expense_transaction",
            source_id=trans_id
        )
        
        db.commit()

        # AUDIT LOG
        log_activity(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="treasury.expense.create",
            resource_type="treasury_transaction",
            resource_id=str(trans_id),
            details={"amount": data.amount, "description": data.description, "treasury_id": data.treasury_id},
            request=request,
            branch_id=final_branch_id
        )

        return {"success": True, "message": "تم تسجيل المصروف بنجاح", "transaction_id": trans_id}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Expense Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.post("/transactions/transfer", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("treasury.manage"))])
def create_transfer(request: Request, data: TransactionCreate, current_user: dict = Depends(get_current_user)):
    """تحويل بين الخزائن/البنوك"""
    if data.transaction_type != 'transfer':
        raise HTTPException(status_code=400, detail="Invalid transaction type")
    
    # Validate amount
    if data.amount is None or data.amount <= 0:
        raise HTTPException(status_code=400, detail="المبلغ يجب أن يكون أكبر من صفر")
    
    # Prevent self-transfer
    if data.treasury_id == data.target_treasury_id:
        raise HTTPException(status_code=400, detail="لا يمكن التحويل من وإلى نفس الحساب")
    
    if not data.target_treasury_id:
        raise HTTPException(status_code=400, detail="يجب تحديد حساب الخزينة المستلم")
        
    db = get_db_connection(current_user.company_id)
    try:
        import uuid
        trans_num = f"TRF-{str(uuid.uuid4())[:8].upper()}"
        
        # Get Source & Target Info
        source = db.execute(text("SELECT gl_account_id, name, branch_id, currency FROM treasury_accounts WHERE id = :id"), {"id": data.treasury_id}).fetchone()
        target = db.execute(text("SELECT gl_account_id, name, currency FROM treasury_accounts WHERE id = :id"), {"id": data.target_treasury_id}).fetchone()
        
        if not source or not target:
            raise HTTPException(status_code=404, detail="حساب المصدر أو المستلم غير موجود")
            
        source_gl, source_name, branch_id, source_currency = source
        target_gl, target_name, target_currency = target
        
        exchange_rate = _dec(data.exchange_rate or 1)
        amount_base = (_dec(data.amount) * exchange_rate).quantize(_D2, ROUND_HALF_UP)

        # 1. Insert Transaction Log
        trans_id = db.execute(text("""
            INSERT INTO treasury_transactions (
                transaction_number, transaction_date, transaction_type, amount, 
                treasury_id, target_treasury_id, description, reference_number, created_by
            ) VALUES (
                :num, :date, :type, :amount, :src, :dst, :desc, :ref, :uid
            ) RETURNING id
        """), {
            "num": trans_num,
            "date": data.transaction_date,
            "type": 'transfer',
            "amount": data.amount,
            "src": data.treasury_id,
            "dst": data.target_treasury_id,
            "desc": data.description or f"Transfer from {source_name} to {target_name}",
            "ref": data.reference_number,
            "uid": current_user.id
        }).scalar()
        
        # 2. Update Treasury Balances
        db.execute(text("UPDATE treasury_accounts SET current_balance = current_balance - :amt WHERE id = :id"), {"amt": data.amount, "id": data.treasury_id})
        
        # Cross-currency: convert amount to target currency before adding to target treasury
        if source_currency != target_currency and exchange_rate != Decimal('1'):
            # data.amount is in source currency, exchange_rate converts source->base
            # For target treasury, we need to convert: source_amount * source_rate / target_rate
            target_rate_row = db.execute(text("SELECT current_rate FROM currencies WHERE code = :code"), {"code": target_currency}).fetchone()
            target_rate = _dec(target_rate_row.current_rate) if target_rate_row else Decimal('1')
            target_amount = ((_dec(data.amount) * exchange_rate) / target_rate).quantize(_D2, ROUND_HALF_UP) if target_rate else _dec(data.amount)
        else:
            target_amount = data.amount
        
        db.execute(text("UPDATE treasury_accounts SET current_balance = current_balance + :amt WHERE id = :id"), {"amt": target_amount, "id": data.target_treasury_id})
        
        # 3. Create Journal Entry
        check_fiscal_period_open(db, data.transaction_date)
        
        target_rate = (_dec(amount_base) / _dec(target_amount)) if _dec(target_amount) else Decimal('1')
        
        je_lines = [
            {
                "account_id": target_gl, "debit": float(target_amount), "credit": 0, 
                "currency": target_currency, "exchange_rate": float(target_rate), "description": "Transfer In"
            },
            {
                "account_id": source_gl, "debit": 0, "credit": float(data.amount), 
                "currency": source_currency, "exchange_rate": float(exchange_rate), "description": "Transfer Out"
            },
        ]

        from services.gl_service import create_journal_entry as gl_create_journal_entry
        je_id, _ = gl_create_journal_entry(
            db=db,
            company_id=current_user.company_id,
            date=data.transaction_date,
            description=f"Transfer: {source_name} -> {target_name} ({source_currency})",
            lines=je_lines,
            user_id=current_user.id,
            branch_id=branch_id,
            reference=trans_num,
            currency=source_currency,
            exchange_rate=float(exchange_rate),
            source="treasury_transfer",
            source_id=trans_id
        )
        
        db.commit()

        # AUDIT LOG
        log_activity(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="treasury.transfer.create",
            resource_type="treasury_transaction",
            resource_id=str(trans_id),
            details={"amount": data.amount, "from": data.treasury_id, "to": data.target_treasury_id},
            request=request,
            branch_id=branch_id
        )

        return {"success": True, "message": "تم التحويل بنجاح", "transaction_id": trans_id}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Transfer Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ────────────────────────── Treasury Reports ──────────────────────────

@router.get("/reports/balances", dependencies=[Depends(require_permission("treasury.view"))])
def get_treasury_balances_report(
    branch_id: Optional[int] = None,
    as_of_date: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    """تقرير أرصدة الخزينة — كل الصناديق والبنوك مع أرصدتها"""
    db = get_db_connection(current_user.company_id)
    try:
        if branch_id:
            from utils.permissions import validate_branch_access
            validate_branch_access(current_user, branch_id)

        target_date = as_of_date or date.today().isoformat()

        # Get all treasury accounts with current balances
        q = text("""
            SELECT ta.id, ta.name, ta.name_en, ta.account_type, ta.currency,
                   ta.current_balance,
                   ta.gl_account_id, ta.branch_id,
                   COALESCE(b.branch_name, '') as branch_name
            FROM treasury_accounts ta
            LEFT JOIN branches b ON b.id = ta.branch_id
            WHERE ta.is_active = true
            """ + (" AND ta.branch_id = :branch_id" if branch_id else "") + """
            ORDER BY ta.account_type, ta.name
        """)
        params = {"branch_id": branch_id} if branch_id else {}
        rows = db.execute(q, params).fetchall()

        accounts = []
        total_cash = Decimal('0')
        total_bank = Decimal('0')
        total_all = Decimal('0')

        # Load base currency and exchange rates once
        base_currency = db.execute(text(
            "SELECT code FROM currencies WHERE is_base = TRUE LIMIT 1"
        )).scalar() or "SAR"

        fx_rates: dict = {}
        try:
            rate_rows = db.execute(text(
                "SELECT code, current_rate FROM currencies WHERE is_active = true"
            )).fetchall()
            for rr in rate_rows:
                fx_rates[rr.code] = _dec(rr.current_rate or 1)
        except Exception:
            pass

        for r in rows:
            bal = _dec(r.current_balance or 0)
            currency = r.currency or base_currency
            rate = fx_rates.get(currency, Decimal('1')) if currency != base_currency else Decimal('1')
            bal_base = (bal * rate).quantize(_D2, ROUND_HALF_UP)

            acc = {
                "id": r.id, "name": r.name, "name_en": r.name_en,
                "account_type": r.account_type, "currency": currency,
                "current_balance": float(bal),
                "balance_in_currency": float(bal),
                "balance_in_base": float(bal_base),
                "exchange_rate": float(rate),
                "base_currency": base_currency,
                "branch_name": r.branch_name
            }
            accounts.append(acc)
            if r.account_type == 'cash':
                total_cash += bal_base
            else:
                total_bank += bal_base
            total_all += bal_base

        # Recent transactions for context
        txn_q = text("""
            SELECT tt.id, tt.transaction_type, tt.amount, tt.description,
                   tt.created_at, ta.name as account_name
            FROM treasury_transactions tt
            JOIN treasury_accounts ta ON ta.id = tt.treasury_id
            WHERE 1=1
            """ + (" AND ta.branch_id = :branch_id" if branch_id else "") + """
            ORDER BY tt.created_at DESC LIMIT 10
        """)
        txns = db.execute(txn_q, params).fetchall()
        recent = [{
            "id": t.id, "type": t.transaction_type, "amount": float(t.amount),
            "description": t.description, "date": str(t.created_at)[:10],
            "account_name": t.account_name
        } for t in txns]

        return {
            "accounts": accounts,
            "summary": {
                "total_cash": float(total_cash),
                "total_bank": float(total_bank),
                "total_all": float(total_all),
                "cash_count": sum(1 for a in accounts if a["account_type"] == "cash"),
                "bank_count": sum(1 for a in accounts if a["account_type"] == "bank"),
            },
            "recent_transactions": recent,
            "as_of_date": target_date
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Treasury balances report error: {e}")
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.get("/reports/cashflow", dependencies=[Depends(require_permission("treasury.view"))])
def get_treasury_cashflow_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    branch_id: Optional[int] = None,
    current_user=Depends(get_current_user)
):
    """تقرير التدفقات النقدية للخزينة — التدفقات الداخلة والخارجة"""
    db = get_db_connection(current_user.company_id)
    try:
        if branch_id:
            from utils.permissions import validate_branch_access
            validate_branch_access(current_user, branch_id)

        from datetime import datetime, timedelta
        if not start_date:
            start_date = (datetime.now().replace(day=1)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        branch_filter = " AND ta.branch_id = :branch_id" if branch_id else ""
        params = {"start_date": start_date, "end_date": end_date}
        if branch_id:
            params["branch_id"] = branch_id

        # Inflows (receipts, deposits, transfers in)
        inflow_q = text(f"""
            SELECT COALESCE(SUM(tt.amount), 0) as total,
                   tt.transaction_type,
                   COUNT(*) as count
            FROM treasury_transactions tt
            JOIN treasury_accounts ta ON ta.id = tt.treasury_id
            WHERE tt.transaction_type IN ('receipt', 'deposit', 'transfer_in', 'pos_sale')
              AND tt.created_at::date BETWEEN :start_date AND :end_date
              {branch_filter}
            GROUP BY tt.transaction_type
        """)
        inflows = db.execute(inflow_q, params).fetchall()

        # Outflows (expense, withdrawal, transfer out)
        outflow_q = text(f"""
            SELECT COALESCE(SUM(tt.amount), 0) as total,
                   tt.transaction_type,
                   COUNT(*) as count
            FROM treasury_transactions tt
            JOIN treasury_accounts ta ON ta.id = tt.treasury_id
            WHERE tt.transaction_type IN ('expense', 'withdrawal', 'transfer_out', 'payment')
              AND tt.created_at::date BETWEEN :start_date AND :end_date
              {branch_filter}
            GROUP BY tt.transaction_type
        """)
        outflows = db.execute(outflow_q, params).fetchall()

        # Daily trend
        daily_q = text(f"""
            SELECT tt.created_at::date as day,
                   SUM(CASE WHEN tt.transaction_type IN ('receipt','deposit','transfer_in','pos_sale') THEN tt.amount ELSE 0 END) as inflow,
                   SUM(CASE WHEN tt.transaction_type IN ('expense','withdrawal','transfer_out','payment') THEN tt.amount ELSE 0 END) as outflow
            FROM treasury_transactions tt
            JOIN treasury_accounts ta ON ta.id = tt.treasury_id
            WHERE tt.created_at::date BETWEEN :start_date AND :end_date
              {branch_filter}
            GROUP BY tt.created_at::date
            ORDER BY day
        """)
        daily = db.execute(daily_q, params).fetchall()

        # By account breakdown
        by_account_q = text(f"""
            SELECT ta.id, ta.name, ta.account_type,
                   SUM(CASE WHEN tt.transaction_type IN ('receipt','deposit','transfer_in','pos_sale') THEN tt.amount ELSE 0 END) as inflow,
                   SUM(CASE WHEN tt.transaction_type IN ('expense','withdrawal','transfer_out','payment') THEN tt.amount ELSE 0 END) as outflow
            FROM treasury_transactions tt
            JOIN treasury_accounts ta ON ta.id = tt.treasury_id
            WHERE tt.created_at::date BETWEEN :start_date AND :end_date
              {branch_filter}
            GROUP BY ta.id, ta.name, ta.account_type
            ORDER BY ta.name
        """)
        by_account = db.execute(by_account_q, params).fetchall()

        total_in = sum(float(r.total) for r in inflows)
        total_out = sum(float(r.total) for r in outflows)

        return {
            "inflows": [{"type": r.transaction_type, "total": float(r.total), "count": r.count} for r in inflows],
            "outflows": [{"type": r.transaction_type, "total": float(r.total), "count": r.count} for r in outflows],
            "total_inflow": total_in,
            "total_outflow": total_out,
            "net_flow": total_in - total_out,
            "daily_trend": [{"date": str(d.day), "inflow": float(d.inflow), "outflow": float(d.outflow)} for d in daily],
            "by_account": [{"id": a.id, "name": a.name, "type": a.account_type, "inflow": float(a.inflow), "outflow": float(a.outflow), "net": float(a.inflow) - float(a.outflow)} for a in by_account],
            "start_date": start_date,
            "end_date": end_date
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Treasury cashflow report error: {e}")
        raise HTTPException(500, str(e))
    finally:
        db.close()
