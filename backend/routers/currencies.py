from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Any
from datetime import date, datetime
from pydantic import BaseModel
from database import get_db, get_company_db
from utils.permissions import require_permission
from schemas import CurrencyCreate, CurrencyResponse, ExchangeRateCreate, ExchangeRateResponse
from schemas.currencies import RevaluationRequest

router = APIRouter(
    prefix="/accounting/currencies",
    tags=["accounting"]
)

@router.get("/", response_model=List[CurrencyResponse])
def list_currencies(
    current_user: Any = Depends(require_permission(["accounting.view", "currencies.view"]))
):
    """List all configured currencies"""
    from database import get_db_connection, get_currency_tables_sql
    db = get_db_connection(current_user.company_id)
    try:
        try:
            result = db.execute(text("SELECT * FROM currencies ORDER BY is_base DESC, code ASC"))
            return result.mappings().all()
        except Exception as e:
            db.rollback()
            if "currencies" in str(e).lower() and "does not exist" in str(e).lower():
                # Auto-create missing currency tables
                db.execute(text(get_currency_tables_sql()))
                db.commit()

                # Fetch TRUE company currency from system database
                from database import get_system_db
                sys_db = get_system_db()
                try:
                    true_currency = sys_db.execute(
                        text("SELECT currency FROM system_companies WHERE id = :id"),
                        {"id": current_user.company_id}
                    ).scalar()
                    default_currency = true_currency if true_currency else "SAR"
                except Exception:
                    default_currency = "SAR"
                finally:
                    sys_db.close()

                # Initialize with company default currency
                db.execute(text(f"""
                    INSERT INTO currencies (code, name, symbol, is_base, current_rate)
                    VALUES ('{default_currency}', '{default_currency}', '{default_currency}', TRUE, 1.0)
                    ON CONFLICT (code) DO UPDATE SET is_base = TRUE
                """))
                
                # Correction Logic: If 'SAR' exists but it's NOT the company currency, remove it or demote it.
                # If we just inserted the correct one, and SAR was there from before (if table wasn't empty but we thought it was? unlikely in this block)
                # But to be safe, let's clean up if there are multiple bases.
                if default_currency != 'SAR':
                     # Remove SAR if it was wrongly added as base
                     db.execute(text("DELETE FROM currencies WHERE code = 'SAR' AND is_base = TRUE"))
                     
                db.commit()
                result = db.execute(text("SELECT * FROM currencies ORDER BY is_base DESC, code ASC"))
                return result.mappings().all()
            raise e
    finally:
        db.close()

@router.post("/", response_model=CurrencyResponse)
def create_currency(
    currency: CurrencyCreate,
    current_user: Any = Depends(require_permission(["accounting.manage", "currencies.manage"]))
):
    """Add a new currency"""
    from database import get_db_connection
    db = get_db_connection(current_user.company_id)
    try:
        # Validate currency code format (ISO 4217: 3 uppercase letters)
        import re
        if not re.match(r'^[A-Z]{3}$', currency.code):
            raise HTTPException(status_code=400, detail="كود العملة يجب أن يكون 3 أحرف إنجليزية كبيرة (مثال: USD, EUR, SAR)")

        # Check if exists
        existing = db.execute(text("SELECT 1 FROM currencies WHERE code = :code"), {"code": currency.code}).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Currency code already exists")

        # If is_base is True, unset other base currencies
        if currency.is_base:
            db.execute(text("UPDATE currencies SET is_base = FALSE"))

        query = text("""
            INSERT INTO currencies (code, name, name_en, symbol, is_base, current_rate, is_active)
            VALUES (:code, :name, :name_en, :symbol, :is_base, :current_rate, :is_active)
            RETURNING *
        """)
        result = db.execute(query, currency.model_dump()).mappings().fetchone()
        db.commit()
        return result
    finally:
        db.close()

@router.put("/{currency_id}", response_model=CurrencyResponse)
def update_currency(
    currency_id: int,
    currency: CurrencyCreate,
    current_user: Any = Depends(require_permission(["accounting.manage", "currencies.manage"]))
):
    """Update currency details"""
    from database import get_db_connection
    db = get_db_connection(current_user.company_id)
    try:
        # If setting as base, unset others
        if currency.is_base:
            db.execute(text("UPDATE currencies SET is_base = FALSE WHERE id != :id"), {"id": currency_id})
            # Base currency rate must be 1
            currency.current_rate = 1.0
        
        query = text("""
            UPDATE currencies 
            SET code=:code, name=:name, name_en=:name_en, symbol=:symbol, 
                is_base=:is_base, current_rate=:current_rate, is_active=:is_active,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=:id
            RETURNING *
        """)
        params = currency.model_dump()
        params["id"] = currency_id
        
        result = db.execute(query, params).mappings().fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Currency not found")
            
        db.commit()
        return result
    finally:
        db.close()

@router.delete("/{currency_id}")
def delete_currency(
    currency_id: int,
    current_user: Any = Depends(require_permission(["accounting.manage", "currencies.manage"]))
):
    """Delete a currency"""
    from database import get_db_connection
    db = get_db_connection(current_user.company_id)
    try:
        # Don't delete base currency
        check = db.execute(text("SELECT is_base, code FROM currencies WHERE id = :id"), {"id": currency_id}).fetchone()
        if not check:
            raise HTTPException(status_code=404, detail="العملة غير موجودة")
        if check.is_base:
            raise HTTPException(status_code=400, detail="Cannot delete base currency")

        # Check if currency is used in any transactions
        code = check.code
        usage_checks = [
            ("journal_entries", "SELECT 1 FROM journal_entries WHERE currency = :code LIMIT 1"),
            ("invoices", "SELECT 1 FROM invoices WHERE currency = :code LIMIT 1"),
            ("payment_vouchers", "SELECT 1 FROM payment_vouchers WHERE currency = :code LIMIT 1"),
            ("treasury_accounts", "SELECT 1 FROM treasury_accounts WHERE currency = :code LIMIT 1"),
            ("accounts", "SELECT 1 FROM accounts WHERE currency = :code LIMIT 1"),
        ]
        for table_name, check_query in usage_checks:
            try:
                used = db.execute(text(check_query), {"code": code}).fetchone()
                if used:
                    raise HTTPException(status_code=400, detail=f"لا يمكن حذف العملة لأنها مستخدمة في {table_name}")
            except HTTPException:
                raise
            except Exception:
                pass  # Table may not exist yet

        db.execute(text("DELETE FROM currencies WHERE id = :id"), {"id": currency_id})
        db.commit()
        return {"message": "Currency deleted"}
    finally:
        db.close()

@router.post("/rates", response_model=ExchangeRateResponse)
def add_exchange_rate(
    rate_data: ExchangeRateCreate,
    current_user: Any = Depends(require_permission(["accounting.manage", "currencies.manage"]))
):
    """Record a historical exchange rate"""
    from database import get_db_connection
    db = get_db_connection(current_user.company_id)
    try:
        # Validate exchange rate
        if rate_data.rate is None or rate_data.rate <= 0:
            raise HTTPException(status_code=400, detail="سعر الصرف يجب أن يكون أكبر من صفر")

        # Check currency exists
        curr = db.execute(text("SELECT code FROM currencies WHERE id = :id"), {"id": rate_data.currency_id}).fetchone()
        if not curr:
            raise HTTPException(status_code=404, detail="Currency not found")

        # Insert or Update (Upsert)
        query = text("""
            INSERT INTO exchange_rates (currency_id, rate_date, rate, source, created_by)
            VALUES (:currency_id, :rate_date, :rate, :source, :user_id)
            ON CONFLICT (currency_id, rate_date) 
            DO UPDATE SET rate = :rate, source = :source, created_at = CURRENT_TIMESTAMP
            RETURNING *
        """)
        params = rate_data.model_dump()
        params["user_id"] = current_user.id
        
        result = db.execute(query, params).mappings().fetchone()
        
        # Also update current rate in currencies table
        db.execute(text("UPDATE currencies SET current_rate = :rate WHERE id = :id"), 
                {"rate": rate_data.rate, "id": rate_data.currency_id})
        
        db.commit()
        return result
    finally:
        db.close()

@router.get("/{currency_id}/rates", response_model=List[ExchangeRateResponse])
def get_rate_history(
    currency_id: int,
    limit: int = 30,
    current_user: Any = Depends(require_permission(["accounting.view", "currencies.view"]))
):
    """Get exchange rate history"""
    from database import get_db_connection
    db = get_db_connection(current_user.company_id)
    try:
        query = text("""
            SELECT * FROM exchange_rates 
            WHERE currency_id = :id 
            ORDER BY rate_date DESC 
            LIMIT :limit
        """)
        result = db.execute(query, {"id": currency_id, "limit": limit})
        return result.mappings().all()
    finally:
        db.close()


@router.post("/revaluate")
def create_revaluation(
    req: RevaluationRequest,
    current_user: Any = Depends(require_permission(["accounting.manage", "currencies.manage"]))
):
    """
    Calculate and book Unrealized FX Gains/Losses for a specific currency.
    Compares (Account Balance in FC * New Rate) vs (Account Balance in BC from GL).
    """
    from database import get_db_connection
    db = get_db_connection(current_user.company_id)
    try:
        # Validate new rate
        if req.new_rate is None or req.new_rate <= 0:
            raise HTTPException(status_code=400, detail="سعر الصرف الجديد يجب أن يكون أكبر من صفر")

        # 1. Get Currency Info
        currency = db.execute(text("SELECT * FROM currencies WHERE id = :id"), {"id": req.currency_id}).fetchone()
        if not currency:
            raise HTTPException(status_code=404, detail="Currency not found")
        
        code = currency.code

        # Check for duplicate revaluation on same date and currency
        existing_reval = db.execute(text("""
            SELECT id FROM journal_entries 
            WHERE entry_number LIKE :prefix 
            AND entry_date = :rate_date
            AND status = 'posted'
        """), {"prefix": f"REV-{code}-%", "rate_date": req.rate_date}).fetchone()
        if existing_reval:
            raise HTTPException(status_code=400, detail=f"تم إجراء إعادة تقييم لهذه العملة ({code}) بنفس التاريخ. يرجى إلغاء السابقة أولاً.")

        # 2. Get all accounts with this currency
        accounts = db.execute(text("SELECT id, name, balance FROM accounts WHERE currency = :code"), {"code": code}).fetchall()
        
        if not accounts:
            return {"message": "No accounts found with this currency", "entries_created": 0}

        # 3. Get GL Account IDs for Unrealized Gain/Loss
        acc_gain = db.execute(text("SELECT id FROM accounts WHERE account_code = 'UFX-GAIN'")).fetchone()
        acc_loss = db.execute(text("SELECT id FROM accounts WHERE account_code = 'UFX-LOSS'")).fetchone()
        
        if not acc_gain or not acc_loss:
            raise HTTPException(status_code=500, detail="Unrealized Gain/Loss accounts not found in Chart of Accounts")
        
        gain_id = acc_gain.id
        loss_id = acc_loss.id

        # 4. Prepare Journal Entry
        journal_entry_lines = []

        for acc in accounts:
            # Get account type to determine balance direction
            acc_type_row = db.execute(text("SELECT account_type FROM accounts WHERE id = :aid"), {"aid": acc.id}).fetchone()
            acc_type = acc_type_row.account_type if acc_type_row else 'asset'
            
            # Calculate Foreign Currency Balance from Journal Lines
            # FC amount_currency is always positive, so use debit/credit to determine direction
            fc_balance_row = db.execute(text("""
                SELECT COALESCE(SUM(
                    CASE WHEN debit > 0 THEN COALESCE(amount_currency, 0)
                         WHEN credit > 0 THEN -COALESCE(amount_currency, 0)
                         ELSE 0 END
                ), 0) as fc_balance 
                FROM journal_lines 
                WHERE account_id = :aid
            """), {"aid": acc.id}).fetchone()
            fc_balance = float(fc_balance_row.fc_balance)

            if abs(fc_balance) < 0.01:
                continue

            # Calculate Current Base Currency Balance (Book Value)
            bc_balance_row = db.execute(text("""
                SELECT COALESCE(SUM(debit - credit), 0) as balance 
                FROM journal_lines 
                WHERE account_id = :aid
            """), {"aid": acc.id}).fetchone()
            
            bc_balance = float(bc_balance_row.balance)
            target_bc_value = fc_balance * req.new_rate
            diff = target_bc_value - bc_balance
            diff = round(diff, 4)
            
            if abs(diff) < 0.01:
                continue

            if diff > 0:
                journal_entry_lines.append({"account_id": acc.id, "debit": diff, "credit": 0, "desc": f"Revaluation {code} @ {req.new_rate}"})
                journal_entry_lines.append({"account_id": gain_id, "debit": 0, "credit": diff, "desc": f"Unrealized Gain - {acc.name}"})
            else:
                abs_diff = abs(diff)
                journal_entry_lines.append({"account_id": acc.id, "debit": 0, "credit": abs_diff, "desc": f"Revaluation {code} @ {req.new_rate}"})
                journal_entry_lines.append({"account_id": loss_id, "debit": abs_diff, "credit": 0, "desc": f"Unrealized Loss - {acc.name}"})

        if not journal_entry_lines:
            return {"message": "No revaluation needed", "entries_created": 0}

        # 5. Create Journal Entry (wrapped in try/except for rollback on partial failure)
        try:
            entry_num = f"REV-{code}-{datetime.now().strftime('%Y%m%d%H%M')}"
            
            je_query = text("""
                INSERT INTO journal_entries (entry_number, entry_date, description, status, created_by, branch_id)
                VALUES (:entry_num, :date, :desc, 'posted', :uid, 1)
                RETURNING id
            """)
            je_result = db.execute(je_query, {
                "entry_num": entry_num,
                "date": req.rate_date,
                "desc": req.description or f"Currency Revaluation {code} to {req.new_rate}",
                "uid": current_user.id
            }).fetchone()
            
            je_id = je_result.id

            # Insert Lines
            line_query = text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                VALUES (:jid, :aid, :debit, :credit, :desc)
            """)
            
            from utils.accounting import update_account_balance
            for line in journal_entry_lines:
                db.execute(line_query, {
                    "jid": je_id,
                    "aid": line["account_id"],
                    "debit": line["debit"],
                    "credit": line["credit"],
                    "desc": line["desc"]
                })
                update_account_balance(db, account_id=line["account_id"], debit_base=line["debit"], credit_base=line["credit"])
            
            # Update currency current_rate
            db.execute(text("UPDATE currencies SET current_rate = :rate WHERE id = :id"),
                       {"rate": req.new_rate, "id": req.currency_id})
                
            db.commit()
            
            return {
                "message": "Revaluation completed successfully",
                "journal_entry_id": je_id,
                "lines_count": len(journal_entry_lines),
                "total_impact": sum(l['debit'] for l in journal_entry_lines) / 2
            }
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"خطأ أثناء إعادة التقييم: {str(e)}")
    finally:
        db.close()
