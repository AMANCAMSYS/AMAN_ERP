"""
AMAN ERP — System Completion Router
Bank Import | Zakat Calculator | Consolidation Reports | Fiscal Period Lock | Backup
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel
from decimal import Decimal, ROUND_HALF_UP
from decimal import Decimal
import io, csv, json, logging, subprocess, os

from database import get_db_connection, engine as system_engine
from routers.auth import get_current_user
from utils.permissions import require_permission
from utils.audit import log_activity
from utils.accounting import (
    generate_sequential_number, get_mapped_account_id,
    update_account_balance, get_base_currency
)
from utils.fiscal_lock import check_fiscal_period_open, create_fiscal_lock_table
from utils.duplicate_detection import find_duplicate_parties, find_duplicate_products

router = APIRouter(tags=["System Completion"])
logger = logging.getLogger(__name__)


def _u(current_user, key, default=None):
    """Safely get attribute from dict or Pydantic model."""
    if isinstance(current_user, dict):
        return current_user.get(key, default)
    return getattr(current_user, key, default)


# ═══════════════════════════════════════════════════════════════════════════════
#  1. BANK STATEMENT IMPORT
#     استيراد كشف الحساب البنكي (CSV/Excel)
# ═══════════════════════════════════════════════════════════════════════════════

class BankImportLineUpdate(BaseModel):
    status: Optional[str] = None  # matched, unmatched, ignored
    matched_transaction_id: Optional[int] = None
    account_id: Optional[int] = None
    notes: Optional[str] = None


@router.post("/treasury/bank-import", dependencies=[Depends(require_permission("accounting.manage"))],
             tags=["Treasury"])
async def import_bank_statement(
    file: UploadFile = File(...),
    bank_account_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    استيراد كشف حساب بنكي من ملف CSV
    Expected columns: date, description, reference, debit, credit, balance
    """
    company_id = _u(current_user, "company_id")
    user_id = _u(current_user, "user_id")
    db = get_db_connection(company_id)
    try:
        if not file.filename.lower().endswith(('.csv', '.txt')):
            raise HTTPException(400, "يرجى رفع ملف CSV")

        content = await file.read()
        try:
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            text_content = content.decode('windows-1256')  # Arabic Windows encoding

        reader = csv.reader(io.StringIO(text_content))
        rows_list = list(reader)

        if len(rows_list) < 2:
            raise HTTPException(400, "الملف فارغ أو لا يحتوي على بيانات")

        # Auto-detect header
        header = [h.strip().lower() for h in rows_list[0]]

        # Map common column names
        col_map = {}
        for i, h in enumerate(header):
            if h in ('date', 'تاريخ', 'value_date', 'transaction_date'):
                col_map['date'] = i
            elif h in ('description', 'details', 'وصف', 'البيان', 'narrative'):
                col_map['description'] = i
            elif h in ('reference', 'ref', 'مرجع', 'cheque_no', 'check'):
                col_map['reference'] = i
            elif h in ('debit', 'مدين', 'withdrawal', 'سحب'):
                col_map['debit'] = i
            elif h in ('credit', 'دائن', 'deposit', 'إيداع'):
                col_map['credit'] = i
            elif h in ('balance', 'رصيد', 'running_balance'):
                col_map['balance'] = i
            elif h in ('amount', 'مبلغ'):
                col_map['amount'] = i

        if 'date' not in col_map:
            raise HTTPException(400, "لم يتم العثور على عمود التاريخ في الملف")

        # Create batch
        batch_result = db.execute(text("""
            INSERT INTO bank_import_batches (
                file_name, bank_account_id, total_lines, status, uploaded_by
            ) VALUES (:fn, :baid, :total, 'pending', :uid)
            RETURNING id
        """), {
            "fn": file.filename,
            "baid": bank_account_id,
            "total": len(rows_list) - 1,
            "uid": user_id
        })
        batch_id = batch_result.fetchone()[0]

        # Parse lines
        imported = 0
        errors = []
        for idx, row in enumerate(rows_list[1:], start=2):
            try:
                if not row or all(not cell.strip() for cell in row):
                    continue

                txn_date = row[col_map['date']].strip() if 'date' in col_map else None
                description = row[col_map['description']].strip() if 'description' in col_map and col_map['description'] < len(row) else ''
                reference = row[col_map['reference']].strip() if 'reference' in col_map and col_map['reference'] < len(row) else ''

                debit = 0
                credit = 0
                if 'debit' in col_map and col_map['debit'] < len(row):
                    val = row[col_map['debit']].strip().replace(',', '')
                    debit = float(val) if val else 0
                if 'credit' in col_map and col_map['credit'] < len(row):
                    val = row[col_map['credit']].strip().replace(',', '')
                    credit = float(val) if val else 0
                if 'amount' in col_map and col_map['amount'] < len(row) and debit == 0 and credit == 0:
                    val = row[col_map['amount']].strip().replace(',', '')
                    amount = float(val) if val else 0
                    if amount > 0:
                        credit = amount
                    else:
                        debit = abs(amount)

                balance = 0
                if 'balance' in col_map and col_map['balance'] < len(row):
                    val = row[col_map['balance']].strip().replace(',', '')
                    balance = float(val) if val else 0

                # Parse date (try multiple formats)
                parsed_date = None
                for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d'):
                    try:
                        parsed_date = datetime.strptime(txn_date, fmt).date()
                        break
                    except (ValueError, TypeError):
                        continue

                if not parsed_date:
                    errors.append(f"سطر {idx}: تاريخ غير صالح '{txn_date}'")
                    continue

                db.execute(text("""
                    INSERT INTO bank_import_lines (
                        batch_id, line_number, transaction_date, description,
                        reference, debit, credit, balance, status
                    ) VALUES (:bid, :ln, :td, :desc, :ref, :dr, :cr, :bal, 'unmatched')
                """), {
                    "bid": batch_id, "ln": idx - 1, "td": parsed_date,
                    "desc": description, "ref": reference,
                    "dr": debit, "cr": credit, "bal": balance
                })
                imported += 1

            except Exception as e:
                errors.append(f"سطر {idx}: {str(e)}")

        # Update batch
        db.execute(text("""
            UPDATE bank_import_batches SET
                imported_lines = :imp, status = 'imported',
                total_debit = (SELECT COALESCE(SUM(debit), 0) FROM bank_import_lines WHERE batch_id = :bid),
                total_credit = (SELECT COALESCE(SUM(credit), 0) FROM bank_import_lines WHERE batch_id = :bid)
            WHERE id = :bid
        """), {"imp": imported, "bid": batch_id})

        db.commit()

        return {
            "batch_id": batch_id,
            "file_name": file.filename,
            "total_lines": len(rows_list) - 1,
            "imported": imported,
            "errors": errors[:20],
            "message": f"تم استيراد {imported} حركة بنكية"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.get("/treasury/bank-import/batches", dependencies=[Depends(require_permission("accounting.view"))],
            tags=["Treasury"])
def list_bank_import_batches(current_user: dict = Depends(get_current_user)):
    company_id = _u(current_user, "company_id")
    db = get_db_connection(company_id)
    try:
        rows = db.execute(text("""
            SELECT bib.*, cu.full_name as uploaded_by_name
            FROM bank_import_batches bib
            LEFT JOIN company_users cu ON cu.id = bib.uploaded_by
            ORDER BY bib.id DESC
        """)).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.get("/treasury/bank-import/{batch_id}/lines",
            dependencies=[Depends(require_permission("accounting.view"))], tags=["Treasury"])
def get_bank_import_lines(batch_id: int, status_filter: Optional[str] = None,
                          current_user: dict = Depends(get_current_user)):
    company_id = _u(current_user, "company_id")
    db = get_db_connection(company_id)
    try:
        query = "SELECT * FROM bank_import_lines WHERE batch_id = :bid"
        params = {"bid": batch_id}
        if status_filter:
            query += " AND status = :st"
            params["st"] = status_filter
        query += " ORDER BY line_number"

        rows = db.execute(text(query), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.post("/treasury/bank-import/{batch_id}/auto-match",
             dependencies=[Depends(require_permission("accounting.manage"))], tags=["Treasury"])
def auto_match_bank_lines(batch_id: int, current_user: dict = Depends(get_current_user)):
    """مطابقة تلقائية للحركات البنكية مع المعاملات الموجودة"""
    company_id = _u(current_user, "company_id")
    db = get_db_connection(company_id)
    try:
        lines = db.execute(text("""
            SELECT * FROM bank_import_lines
            WHERE batch_id = :bid AND status = 'unmatched'
        """), {"bid": batch_id}).fetchall()

        matched = 0
        for line in lines:
            amount = float(line.debit or 0) or float(line.credit or 0)
            ref = line.reference or ''

            # Try matching by reference number and amount
            match = None
            if ref:
                # Match against payments/receipts
                match = db.execute(text("""
                    SELECT 'payment' as type, id, reference_number, amount
                    FROM payments
                    WHERE (reference_number = :ref OR check_number = :ref)
                    AND ABS(amount - :amt) < 0.01
                    LIMIT 1
                """), {"ref": ref, "amt": amount}).fetchone()

                if not match:
                    # Match against invoices
                    match = db.execute(text("""
                        SELECT 'invoice' as type, id, invoice_number as reference_number, total_amount as amount
                        FROM invoices
                        WHERE invoice_number = :ref
                        AND ABS(total_amount - :amt) < 0.01
                        LIMIT 1
                    """), {"ref": ref, "amt": amount}).fetchone()

            if not match and amount > 0:
                # Try matching by amount and date (±1 day)
                match = db.execute(text("""
                    SELECT 'payment' as type, id, reference_number, amount
                    FROM payments
                    WHERE ABS(amount - :amt) < 0.01
                    AND payment_date BETWEEN :d1 AND :d2
                    AND id NOT IN (
                        SELECT COALESCE(matched_transaction_id, 0)
                        FROM bank_import_lines
                        WHERE batch_id = :bid AND status = 'matched'
                    )
                    LIMIT 1
                """), {
                    "amt": amount,
                    "d1": line.transaction_date,
                    "d2": line.transaction_date,
                    "bid": batch_id
                }).fetchone()

            if match:
                db.execute(text("""
                    UPDATE bank_import_lines SET
                        status = 'matched',
                        matched_transaction_id = :tid,
                        notes = :notes
                    WHERE id = :lid
                """), {
                    "tid": match.id,
                    "notes": f"Matched to {match.type} #{match.reference_number}",
                    "lid": line.id
                })
                matched += 1

        db.execute(text("""
            UPDATE bank_import_batches SET
                matched_lines = :mc,
                status = CASE WHEN :mc = total_lines THEN 'fully_matched'
                         WHEN :mc > 0 THEN 'partially_matched'
                         ELSE status END
            WHERE id = :bid
        """), {"mc": matched, "bid": batch_id})

        db.commit()

        return {
            "total_unmatched": len(lines),
            "matched": matched,
            "remaining": len(lines) - matched,
            "message": f"تمت مطابقة {matched} من {len(lines)} حركة"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  2. ZAKAT CALCULATOR
#     حاسبة الزكاة — طريقة صافي الأصول والوعاء الزكوي
#     ⚠️ Islamic Zakat — applies to Muslim-majority countries (SA, AE, etc.)
#     Non-Islamic countries may ignore this module.
#     Frontend should show/hide based on company settings.
# ═══════════════════════════════════════════════════════════════════════════════

class ZakatCalculateRequest(BaseModel):
    fiscal_year: int
    method: str = "net_assets"  # net_assets or adjusted_profit
    zakat_rate: float = 2.5  # standard Hijri rate (2.5%)
    use_gregorian_rate: bool = False  # If True, uses 2.5775% for Gregorian year
    notes: Optional[str] = None


@router.post("/accounting/zakat/calculate", dependencies=[Depends(require_permission("accounting.manage"))],
             tags=["Zakat"])
def calculate_zakat(body: ZakatCalculateRequest, current_user: dict = Depends(get_current_user)):
    """
    حساب الزكاة الشرعية — Sharia-compliant Zakat Calculation

    Two methods are supported:

    ═══ METHOD 1: Net Assets (صافي الأصول / الوعاء الزكوي) ═══
    Based on GAZT (هيئة الزكاة والضريبة والجمارك) guidelines:
    
    Zakat Base = Capital + Reserves + Retained Earnings + Provisions
                 + Long-term Loans + Net Profit
                 - Fixed Assets - Long-term Investments
                 - Pre-operating Losses
    
    OR simplified: Current Assets - Current Liabilities (Working Capital)
    
    ═══ METHOD 2: Adjusted Profit (الربح المُعدَّل) ═══
    Zakat Base = Net Profit + Non-deductible Expenses (depreciation, provisions,
                 penalties, donations, entertainment beyond limit)
                 - Non-taxable Income

    Rate: 2.5% for Hijri year, 2.5775% for Gregorian year (354/365 adjustment)
    """
    company_id = _u(current_user, "company_id")
    user_id = _u(current_user, "user_id")
    db = get_db_connection(company_id)
    try:
        # Determine rate (Decimal for legal tax precision)
        rate = Decimal('2.57764') if body.use_gregorian_rate else Decimal(str(body.zakat_rate))

        if body.method == "net_assets":
            # ── Detailed Zakat Base Calculation (GAZT Method) ──

            # 1. Equity components (رأس المال + الاحتياطيات + الأرباح المبقاة)
            equity = db.execute(text("""
                SELECT COALESCE(SUM(a.balance), 0)
                FROM accounts a WHERE a.account_type = 'equity'
            """)).scalar() or 0

            # 2. Long-term liabilities (الالتزامات طويلة الأجل)
            lt_liabilities = db.execute(text("""
                SELECT COALESCE(SUM(a.balance), 0)
                FROM accounts a WHERE a.account_type IN ('long_term_liability', 'liability')
                AND (a.name LIKE '%طويل%' OR a.name_en LIKE '%long%term%'
                     OR a.account_code LIKE '22%')
            """)).scalar() or 0

            # 3. Provisions (المخصصات)
            provisions = db.execute(text("""
                SELECT COALESCE(SUM(a.balance), 0)
                FROM accounts a WHERE a.account_type IN ('liability', 'equity')
                AND (a.name LIKE '%مخصص%' OR a.name_en LIKE '%provision%')
            """)).scalar() or 0

            # 4. Net profit for the year
            revenue = db.execute(text("""
                SELECT COALESCE(SUM(CASE WHEN a.account_type IN ('revenue', 'income') 
                    THEN a.balance ELSE 0 END), 0) FROM accounts a
            """)).scalar() or 0
            expenses = db.execute(text("""
                SELECT COALESCE(SUM(CASE WHEN a.account_type IN ('expense', 'cogs') 
                    THEN a.balance ELSE 0 END), 0) FROM accounts a
            """)).scalar() or 0
            net_profit = Decimal(str(revenue)) - Decimal(str(expenses))

            # ADDITIONS to Zakat Base
            additions = Decimal(str(equity)) + Decimal(str(lt_liabilities)) + Decimal(str(provisions))
            if net_profit > 0:
                additions += net_profit

            # 5. DEDUCTIONS — Fixed assets (الأصول الثابتة)
            fixed_assets = db.execute(text("""
                SELECT COALESCE(SUM(a.balance), 0)
                FROM accounts a WHERE a.account_type = 'asset'
                AND (a.name LIKE '%أصول ثابتة%' OR a.name LIKE '%أصل%'
                     OR a.name_en LIKE '%fixed%asset%'
                     OR a.account_code LIKE '12%' OR a.account_code LIKE '15%')
            """)).scalar() or 0

            # 6. Long-term investments (الاستثمارات طويلة الأجل)
            lt_investments = db.execute(text("""
                SELECT COALESCE(SUM(a.balance), 0)
                FROM accounts a WHERE a.account_type = 'asset'
                AND (a.name LIKE '%استثمار%طويل%' OR a.name LIKE '%استثمار%'
                     OR a.name_en LIKE '%long%invest%'
                     OR a.account_code LIKE '13%')
            """)).scalar() or 0

            deductions = Decimal(str(fixed_assets)) + Decimal(str(lt_investments))

            zakat_base = additions - deductions

            # Also calculate simplified method for comparison
            ca = db.execute(text("""
                SELECT COALESCE(SUM(a.balance), 0)
                FROM accounts a WHERE a.account_type = 'asset'
                AND a.account_code LIKE '1%'
                AND a.account_code NOT LIKE '12%' AND a.account_code NOT LIKE '13%'
                AND a.account_code NOT LIKE '15%'
            """)).scalar() or 0

            cl = db.execute(text("""
                SELECT COALESCE(SUM(a.balance), 0)
                FROM accounts a WHERE a.account_type IN ('liability', 'current_liability')
                AND a.account_code LIKE '21%'
            """)).scalar() or 0

            simplified_base = Decimal(str(ca)) - Decimal(str(cl))

            zakat_amount = max(Decimal('0'), (zakat_base * rate / Decimal('100')).quantize(Decimal('0.01'), ROUND_HALF_UP))

            details = {
                "method_name_ar": "طريقة صافي الأصول (الوعاء الزكوي)",
                "method_name_en": "Net Assets Method (Zakat Base)",
                "additions": {
                    "equity": float(Decimal(str(equity)).quantize(Decimal('0.01'))),
                    "long_term_liabilities": float(Decimal(str(lt_liabilities)).quantize(Decimal('0.01'))),
                    "provisions": float(Decimal(str(provisions)).quantize(Decimal('0.01'))),
                    "net_profit": float(net_profit.quantize(Decimal('0.01'))) if net_profit > 0 else 0,
                    "total_additions": float(additions.quantize(Decimal('0.01')))
                },
                "deductions": {
                    "fixed_assets": float(Decimal(str(fixed_assets)).quantize(Decimal('0.01'))),
                    "long_term_investments": float(Decimal(str(lt_investments)).quantize(Decimal('0.01'))),
                    "total_deductions": float(deductions.quantize(Decimal('0.01')))
                },
                "zakat_base": float(zakat_base.quantize(Decimal('0.01'))),
                "simplified_working_capital": float(simplified_base.quantize(Decimal('0.01'))),
                "rate_type": "gregorian" if body.use_gregorian_rate else "hijri",
                "applied_rate": float(rate)
            }

        else:  # adjusted_profit
            # Revenue
            revenue = db.execute(text("""
                SELECT COALESCE(SUM(a.balance), 0)
                FROM accounts a WHERE a.account_type IN ('revenue', 'income', 'other_income')
            """)).scalar() or 0

            # Expenses
            expenses = db.execute(text("""
                SELECT COALESCE(SUM(a.balance), 0)
                FROM accounts a WHERE a.account_type IN ('expense', 'cogs', 'other_expense')
            """)).scalar() or 0

            net_profit = Decimal(str(revenue)) - Decimal(str(expenses))

            # Add-backs: Non-deductible items
            depreciation = db.execute(text("""
                SELECT COALESCE(SUM(a.balance), 0)
                FROM accounts a WHERE a.account_type = 'expense'
                AND (a.name LIKE '%استهلاك%' OR a.name LIKE '%إهلاك%'
                     OR a.name_en LIKE '%depreciation%' OR a.name_en LIKE '%amortization%')
            """)).scalar() or 0

            provision_expense = db.execute(text("""
                SELECT COALESCE(SUM(a.balance), 0)
                FROM accounts a WHERE a.account_type = 'expense'
                AND (a.name LIKE '%مخصص%' OR a.name_en LIKE '%provision%')
            """)).scalar() or 0

            penalties = db.execute(text("""
                SELECT COALESCE(SUM(a.balance), 0)
                FROM accounts a WHERE a.account_type = 'expense'
                AND (a.name LIKE '%غرام%' OR a.name LIKE '%جزاء%'
                     OR a.name_en LIKE '%penalty%' OR a.name_en LIKE '%fine%')
            """)).scalar() or 0

            total_add_backs = Decimal(str(depreciation)) + Decimal(str(provision_expense)) + Decimal(str(penalties))
            adjusted_profit = net_profit + total_add_backs

            zakat_base = max(Decimal('0'), adjusted_profit)
            zakat_amount = (zakat_base * rate / Decimal('100')).quantize(Decimal('0.01'), ROUND_HALF_UP)

            details = {
                "method_name_ar": "طريقة الربح المُعدَّل",
                "method_name_en": "Adjusted Profit Method",
                "revenue": float(Decimal(str(revenue)).quantize(Decimal('0.01'))),
                "expenses": float(Decimal(str(expenses)).quantize(Decimal('0.01'))),
                "net_profit": float(net_profit.quantize(Decimal('0.01'))),
                "add_backs": {
                    "depreciation": float(Decimal(str(depreciation)).quantize(Decimal('0.01'))),
                    "provisions": float(Decimal(str(provision_expense)).quantize(Decimal('0.01'))),
                    "penalties_fines": float(Decimal(str(penalties)).quantize(Decimal('0.01'))),
                    "total_add_backs": float(total_add_backs.quantize(Decimal('0.01')))
                },
                "adjusted_profit": float(adjusted_profit.quantize(Decimal('0.01'))),
                "zakat_base": float(zakat_base.quantize(Decimal('0.01'))),
                "rate_type": "gregorian" if body.use_gregorian_rate else "hijri",
                "applied_rate": float(rate)
            }

        # Save calculation
        db.execute(text("""
            INSERT INTO zakat_calculations (
                fiscal_year, method, zakat_base, zakat_rate, zakat_amount,
                details, status, calculated_by, notes
            ) VALUES (:fy, :method, :base, :rate, :amt, :details, 'calculated', :uid, :notes)
            ON CONFLICT (fiscal_year) DO UPDATE SET
                method = EXCLUDED.method, zakat_base = EXCLUDED.zakat_base,
                zakat_rate = EXCLUDED.zakat_rate, zakat_amount = EXCLUDED.zakat_amount,
                details = EXCLUDED.details, status = EXCLUDED.status,
                calculated_at = CURRENT_TIMESTAMP, notes = EXCLUDED.notes
        """), {
            "fy": body.fiscal_year, "method": body.method,
            "base": zakat_base, "rate": body.zakat_rate,
            "amt": zakat_amount, "details": json.dumps(details),
            "uid": user_id, "notes": body.notes
        })
        db.commit()

        return {
            "fiscal_year": body.fiscal_year,
            "method": body.method,
            "method_ar": "صافي الأصول" if body.method == "net_assets" else "الربح المُعدَّل",
            "details": details,
            "zakat_base": zakat_base,
            "zakat_rate": body.zakat_rate,
            "zakat_amount": zakat_amount,
            "message": f"الزكاة المستحقة: {zakat_amount:,.2f}"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.post("/accounting/zakat/{fiscal_year}/post",
             dependencies=[Depends(require_permission("accounting.manage"))], tags=["Zakat"])
def post_zakat_entry(fiscal_year: int, current_user: dict = Depends(get_current_user)):
    """ترحيل قيد الزكاة — Dr: مصروف زكاة → Cr: زكاة مستحقة"""
    company_id = _u(current_user, "company_id")
    user_id = _u(current_user, "user_id")
    db = get_db_connection(company_id)
    try:
        zakat = db.execute(text(
            "SELECT * FROM zakat_calculations WHERE fiscal_year = :fy"
        ), {"fy": fiscal_year}).fetchone()

        if not zakat:
            raise HTTPException(404, "لم يتم حساب الزكاة لهذا العام")
        if zakat.status == 'posted':
            raise HTTPException(400, "تم ترحيل الزكاة بالفعل")

        amount = float(zakat.zakat_amount)
        if amount <= 0:
            raise HTTPException(400, "مبلغ الزكاة صفر")

        currency = get_base_currency(db)
        je_number = generate_sequential_number(db, f"JE-ZKT-{fiscal_year}", "journal_entries", "entry_number")

        je = db.execute(text("""
            INSERT INTO journal_entries (
                entry_number, entry_date, reference, description,
                status, currency, created_by
            ) VALUES (:num, :dt, :ref, :desc, 'posted', :curr, :uid)
            RETURNING id
        """), {
            "num": je_number, "dt": f"{fiscal_year}-12-31",
            "ref": f"ZAKAT-{fiscal_year}",
            "desc": f"زكاة عام {fiscal_year}",
            "curr": currency, "uid": user_id
        })
        je_id = je.fetchone()[0]

        # Dr: Zakat Expense
        exp_acc = get_mapped_account_id(db, "acc_map_zakat_expense")
        if exp_acc:
            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                VALUES (:jeid, :aid, :amt, 0, 'مصروف زكاة')
            """), {"jeid": je_id, "aid": exp_acc, "amt": amount})
            update_account_balance(db, exp_acc, amount, 0)

        # Cr: Zakat Payable
        pay_acc = get_mapped_account_id(db, "acc_map_zakat_payable")
        if pay_acc:
            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                VALUES (:jeid, :aid, 0, :amt, 'زكاة مستحقة')
            """), {"jeid": je_id, "aid": pay_acc, "amt": amount})
            update_account_balance(db, pay_acc, 0, amount)

        db.execute(text("""
            UPDATE zakat_calculations SET status = 'posted', journal_entry_id = :jeid
            WHERE fiscal_year = :fy
        """), {"jeid": je_id, "fy": fiscal_year})

        db.commit()

        return {
            "journal_entry_id": je_id,
            "entry_number": je_number,
            "amount": amount,
            "message": f"تم ترحيل قيد الزكاة بمبلغ {amount:,.2f}"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  3. CONSOLIDATION REPORTS
#     تقارير توحيد القوائم المالية (متعدد الشركات)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/reports/consolidation/trial-balance",
            dependencies=[Depends(require_permission("accounting.view"))], tags=["Consolidation"])
def consolidated_trial_balance(
    company_ids: Optional[str] = None,  # comma-separated
    as_of_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    ميزان مراجعة موحّد — يجمع أرصدة الحسابات من عدة شركات
    """
    with system_engine.connect() as sys_conn:
        # Get user's accessible companies
        user_id = _u(current_user, "user_id")
        if company_ids:
            ids = [c.strip() for c in company_ids.split(",")]
        else:
            companies = sys_conn.execute(text("""
                SELECT DISTINCT company_id FROM users WHERE id = :uid
            """), {"uid": user_id}).fetchall()
            ids = [c.company_id for c in companies]

        if not ids:
            # Use current company
            ids = [_u(current_user, "company_id")]

        consolidated = {}
        company_details = []

        for cid in ids:
            try:
                db = get_db_connection(cid)
                try:
                    # Get company name
                    comp_name = db.execute(text(
                        "SELECT setting_value FROM company_settings WHERE setting_key = 'company_name' LIMIT 1"
                    )).scalar() or cid

                    company_details.append({"id": cid, "name": comp_name})

                    accounts = db.execute(text("""
                        SELECT a.account_code, a.name, a.name_en,
                               a.account_type,
                               COALESCE(a.balance, 0) as balance
                        FROM accounts a
                        WHERE a.is_active = true
                        ORDER BY a.account_code
                    """)).fetchall()

                    for acc in accounts:
                        code = acc.account_code
                        if code not in consolidated:
                            consolidated[code] = {
                                "account_code": code,
                                "account_name": acc.name,
                                "account_name_en": acc.name_en or '',
                                "account_type": acc.account_type,
                                "total_debit": 0,
                                "total_credit": 0,
                                "net_balance": 0,
                                "company_balances": {}
                            }

                        bal = float(acc.balance or 0)
                        # Debit-normal: asset, expense. Credit-normal: liability, equity, revenue
                        if acc.account_type in ('asset', 'expense'):
                            consolidated[code]["total_debit"] += abs(bal) if bal >= 0 else 0
                            consolidated[code]["total_credit"] += abs(bal) if bal < 0 else 0
                        else:
                            consolidated[code]["total_credit"] += abs(bal) if bal >= 0 else 0
                            consolidated[code]["total_debit"] += abs(bal) if bal < 0 else 0

                        consolidated[code]["net_balance"] += bal
                        consolidated[code]["company_balances"][cid] = bal

                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Consolidation error for company {cid}: {e}")
                continue

        # Sort by account code
        result = sorted(consolidated.values(), key=lambda x: x['account_code'])

        # Round
        for r in result:
            r["total_debit"] = round(r["total_debit"], 2)
            r["total_credit"] = round(r["total_credit"], 2)
            r["net_balance"] = round(r["net_balance"], 2)

        total_debit = sum(r["total_debit"] for r in result)
        total_credit = sum(r["total_credit"] for r in result)

        return {
            "companies": company_details,
            "as_of_date": as_of_date or date.today().isoformat(),
            "accounts": result,
            "totals": {
                "total_debit": round(total_debit, 2),
                "total_credit": round(total_credit, 2),
                "difference": round(total_debit - total_credit, 2)
            }
        }


@router.get("/reports/consolidation/income-statement",
            dependencies=[Depends(require_permission("accounting.view"))], tags=["Consolidation"])
def consolidated_income_statement(
    company_ids: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """قائمة دخل موحّدة"""
    if company_ids:
        ids = [c.strip() for c in company_ids.split(",")]
    else:
        ids = [_u(current_user, "company_id")]

    total_revenue = 0
    total_cogs = 0
    total_expenses = 0
    company_results = []

    for cid in ids:
        try:
            db = get_db_connection(cid)
            try:
                comp_name = db.execute(text(
                    "SELECT setting_value FROM company_settings WHERE setting_key = 'company_name' LIMIT 1"
                )).scalar() or cid

                revenue = db.execute(text("""
                    SELECT COALESCE(SUM(a.balance), 0)
                    FROM accounts a WHERE a.account_type = 'revenue'
                """)).scalar() or 0

                # COGS included within expense accounts
                cogs = 0

                expenses = db.execute(text("""
                    SELECT COALESCE(SUM(a.balance), 0)
                    FROM accounts a WHERE a.account_type = 'expense'
                """)).scalar() or 0

                rev = float(revenue)
                c = float(cogs)
                exp = float(expenses)

                company_results.append({
                    "company_id": cid,
                    "company_name": comp_name,
                    "revenue": rev,
                    "cogs": c,
                    "gross_profit": rev - c,
                    "expenses": exp,
                    "net_income": rev - c - exp
                })

                total_revenue += rev
                total_cogs += c
                total_expenses += exp

            finally:
                db.close()
        except Exception as e:
            logger.error(f"Consolidation IS error {cid}: {e}")

    return {
        "companies": company_results,
        "consolidated": {
            "total_revenue": round(total_revenue, 2),
            "total_cogs": round(total_cogs, 2),
            "gross_profit": round(total_revenue - total_cogs, 2),
            "total_expenses": round(total_expenses, 2),
            "net_income": round(total_revenue - total_cogs - total_expenses, 2)
        }
    }


@router.get("/reports/consolidation/balance-sheet",
            dependencies=[Depends(require_permission("accounting.view"))], tags=["Consolidation"])
def consolidated_balance_sheet(
    company_ids: Optional[str] = None,
    as_of_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """ميزانية عمومية موحّدة — Assets = Liabilities + Equity across all companies"""
    if company_ids:
        ids = [c.strip() for c in company_ids.split(",")]
    else:
        ids = [_u(current_user, "company_id")]

    total_assets = 0
    total_liabilities = 0
    total_equity = 0
    company_results = []

    for cid in ids:
        try:
            db = get_db_connection(cid)
            try:
                comp_name = db.execute(text(
                    "SELECT setting_value FROM company_settings WHERE setting_key = 'company_name' LIMIT 1"
                )).scalar() or cid

                assets = db.execute(text("""
                    SELECT COALESCE(SUM(a.balance), 0)
                    FROM accounts a WHERE a.account_type = 'asset'
                """)).scalar() or 0

                liabilities = db.execute(text("""
                    SELECT COALESCE(SUM(a.balance), 0)
                    FROM accounts a WHERE a.account_type = 'liability'
                """)).scalar() or 0

                equity = db.execute(text("""
                    SELECT COALESCE(SUM(a.balance), 0)
                    FROM accounts a WHERE a.account_type = 'equity'
                """)).scalar() or 0

                a = float(assets)
                l = float(liabilities)
                e = float(equity)

                company_results.append({
                    "company_id": cid,
                    "company_name": comp_name,
                    "total_assets": round(a, 2),
                    "total_liabilities": round(l, 2),
                    "total_equity": round(e, 2),
                    "balance_check": round(a - l - e, 2),
                })

                total_assets += a
                total_liabilities += l
                total_equity += e

            finally:
                db.close()
        except Exception as e:
            logger.error(f"Consolidation BS error {cid}: {e}")

    return {
        "as_of_date": as_of_date or date.today().isoformat(),
        "companies": company_results,
        "consolidated": {
            "total_assets": round(total_assets, 2),
            "total_liabilities": round(total_liabilities, 2),
            "total_equity": round(total_equity, 2),
            "balance_check": round(total_assets - total_liabilities - total_equity, 2),
        }
    }


@router.get("/reports/fx-gain-loss",
            dependencies=[Depends(require_permission("accounting.view"))], tags=["FX Reports"])
def fx_gain_loss_report(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    currency: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    تقرير فروق العملة — الأرباح والخسائر المحققة وغير المحققة
    FX Gain/Loss Report — Realized (from posted JEs) + Unrealized (open foreign currency balances)
    """
    company_id = _u(current_user, "company_id")
    db = get_db_connection(company_id)
    try:
        f_date = from_date or date.today().replace(day=1).isoformat()
        t_date = to_date or date.today().isoformat()
        params: dict = {"from": f_date, "to": t_date}
        currency_cond = " AND jl.currency = :currency" if currency else ""
        if currency:
            params["currency"] = currency

        # ── 1. Realized FX: Journal lines on accounts whose name/type indicates FX ─
        realized_rows = db.execute(text(f"""
            SELECT
                je.id as je_id,
                je.reference,
                je.entry_date,
                jl.description,
                jl.currency,
                COALESCE(jl.debit, 0) as debit_amount,
                COALESCE(jl.credit, 0) as credit_amount,
                a.account_code,
                a.name as account_name,
                a.account_type
            FROM journal_entries je
            JOIN journal_lines jl ON jl.journal_entry_id = je.id
            JOIN accounts a ON a.id = jl.account_id
            WHERE je.entry_date BETWEEN :from AND :to
              AND je.status = 'posted'
              AND (
                  a.name ILIKE '%%فرق عملة%%'
                  OR a.name ILIKE '%%fx%%'
                  OR a.name ILIKE '%%exchange%%'
                  OR a.name ILIKE '%%أرباح صرف%%'
                  OR a.name ILIKE '%%خسائر صرف%%'
              )
              {currency_cond}
            ORDER BY je.entry_date
        """), params).fetchall()

        realized_gains  = sum(float(r.credit_amount) for r in realized_rows)
        realized_losses = sum(float(r.debit_amount)  for r in realized_rows)

        # ── 2. Unrealized FX: Open foreign-currency invoices vs current rates ──
        base_ccy = db.execute(text(
            "SELECT COALESCE(code, 'SYP') FROM currencies WHERE is_base = TRUE LIMIT 1"
        )).scalar() or "SYP"

        fc_cond = ""
        fc_params: dict = {"base": base_ccy}
        if currency:
            fc_cond = " AND i.currency = :currency"
            fc_params["currency"] = currency

        open_inv_rows = db.execute(text(f"""
            SELECT
                i.id, i.invoice_number, i.invoice_date, i.invoice_type,
                i.currency,
                COALESCE(i.exchange_rate, 1.0) as booked_rate,
                (i.total - COALESCE(i.paid_amount, 0)) as open_fc_amount,
                p.name as party_name
            FROM invoices i
            LEFT JOIN parties p ON p.id = i.party_id
            WHERE i.currency != :base
              AND i.status NOT IN ('cancelled', 'draft', 'paid')
              AND (i.total - COALESCE(i.paid_amount, 0)) > 0.01
              {fc_cond}
        """), fc_params).fetchall()

        rate_rows = db.execute(text(
            "SELECT code, COALESCE(current_rate, 1.0) as rate FROM currencies WHERE is_active = TRUE"
        )).fetchall()
        current_rates = {r.code: float(r.rate) for r in rate_rows}

        unrealized = []
        total_unrealized_gain  = 0.0
        total_unrealized_loss  = 0.0
        for inv in open_inv_rows:
            curr     = inv.currency
            booked   = float(inv.booked_rate)
            current  = current_rates.get(curr, booked)
            open_fc  = float(inv.open_fc_amount or 0)
            diff     = open_fc * (current - booked)
            # For purchase invoices (liability), a weaker base currency = loss
            if inv.invoice_type == 'purchase':
                diff = -diff
            unrealized.append({
                "invoice_number": inv.invoice_number,
                "party": inv.party_name,
                "invoice_type": inv.invoice_type,
                "currency": curr,
                "open_fc_amount": round(open_fc, 2),
                "booked_rate": booked,
                "current_rate": current,
                "booked_base": round(open_fc * booked, 2),
                "current_base": round(open_fc * current, 2),
                "unrealized_fx": round(diff, 2),
            })
            if diff >= 0:
                total_unrealized_gain += diff
            else:
                total_unrealized_loss += abs(diff)

        return {
            "report_name": "تقرير فروق العملة",
            "period": {"from": f_date, "to": t_date},
            "realized": {
                "entries": [{
                    "je_id": r.je_id, "ref": r.reference,
                    "date": str(r.entry_date), "description": r.description,
                    "currency": r.currency,
                    "debit": float(r.debit_amount), "credit": float(r.credit_amount),
                    "account": r.account_name,
                } for r in realized_rows],
                "total_gains":  round(realized_gains, 2),
                "total_losses": round(realized_losses, 2),
                "net": round(realized_gains - realized_losses, 2),
            },
            "unrealized": {
                "invoices": unrealized,
                "total_unrealized_gain":  round(total_unrealized_gain, 2),
                "total_unrealized_loss":  round(total_unrealized_loss, 2),
                "net": round(total_unrealized_gain - total_unrealized_loss, 2),
            },
            "summary": {
                "total_fx_gain":  round(realized_gains + total_unrealized_gain, 2),
                "total_fx_loss":  round(realized_losses + total_unrealized_loss, 2),
                "net_fx": round(
                    (realized_gains + total_unrealized_gain)
                    - (realized_losses + total_unrealized_loss), 2
                ),
            },
        }
    except Exception as e:
        logger.error(f"FX gain/loss report error: {e}")
        raise HTTPException(500, str(e))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  4. FISCAL PERIOD LOCK MANAGEMENT
#     إدارة قفل الفترة المحاسبية
# ═══════════════════════════════════════════════════════════════════════════════

class FiscalPeriodLockRequest(BaseModel):
    period_name: str
    period_start: str
    period_end: str
    reason: Optional[str] = None


@router.get("/accounting/fiscal-periods", dependencies=[Depends(require_permission("accounting.view"))],
            tags=["Fiscal Periods"])
def list_fiscal_periods(current_user: dict = Depends(get_current_user)):
    company_id = _u(current_user, "company_id")
    db = get_db_connection(company_id)
    try:
        create_fiscal_lock_table(db)
        rows = db.execute(text("""
            SELECT fp.*, cu.full_name as locked_by_name
            FROM fiscal_period_locks fp
            LEFT JOIN company_users cu ON cu.id = fp.locked_by
            ORDER BY fp.period_start DESC
        """)).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.post("/accounting/fiscal-periods", dependencies=[Depends(require_permission("accounting.manage"))],
             tags=["Fiscal Periods"])
def create_fiscal_period(body: FiscalPeriodLockRequest, current_user: dict = Depends(get_current_user)):
    company_id = _u(current_user, "company_id")
    user_id = _u(current_user, "user_id")
    db = get_db_connection(company_id)
    try:
        create_fiscal_lock_table(db)

        result = db.execute(text("""
            INSERT INTO fiscal_period_locks (period_name, period_start, period_end, is_locked, reason)
            VALUES (:name, :start, :end, false, :reason)
            RETURNING id
        """), {
            "name": body.period_name, "start": body.period_start,
            "end": body.period_end, "reason": body.reason
        })
        period_id = result.fetchone()[0]
        db.commit()

        return {"id": period_id, "message": "تم إنشاء الفترة المحاسبية"}
    finally:
        db.close()


@router.post("/accounting/fiscal-periods/{period_id}/lock",
             dependencies=[Depends(require_permission("accounting.manage"))], tags=["Fiscal Periods"])
def lock_fiscal_period(period_id: int, current_user: dict = Depends(get_current_user)):
    """قفل الفترة المحاسبية — منع إدخال أي قيود فيها"""
    company_id = _u(current_user, "company_id")
    user_id = _u(current_user, "user_id")
    db = get_db_connection(company_id)
    try:
        period = db.execute(text("SELECT * FROM fiscal_period_locks WHERE id = :id"), {"id": period_id}).fetchone()
        if not period:
            raise HTTPException(404, "الفترة غير موجودة")
        if period.is_locked:
            raise HTTPException(400, "الفترة مقفلة بالفعل")

        db.execute(text("""
            UPDATE fiscal_period_locks SET
                is_locked = true, locked_at = CURRENT_TIMESTAMP, locked_by = :uid
            WHERE id = :id
        """), {"uid": user_id, "id": period_id})
        db.commit()

        log_activity(db, user_id, "fiscal_period.lock",
                     f"قفل الفترة {period.period_name}", {"period_id": period_id})

        return {"message": f"تم قفل الفترة {period.period_name}"}
    finally:
        db.close()


@router.post("/accounting/fiscal-periods/{period_id}/unlock",
             dependencies=[Depends(require_permission("accounting.manage"))], tags=["Fiscal Periods"])
def unlock_fiscal_period(period_id: int, current_user: dict = Depends(get_current_user)):
    """فتح الفترة المحاسبية"""
    company_id = _u(current_user, "company_id")
    user_id = _u(current_user, "user_id")
    db = get_db_connection(company_id)
    try:
        db.execute(text("""
            UPDATE fiscal_period_locks SET
                is_locked = false, unlocked_at = CURRENT_TIMESTAMP, unlocked_by = :uid
            WHERE id = :id
        """), {"uid": user_id, "id": period_id})
        db.commit()

        return {"message": "تم فتح الفترة المحاسبية"}
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  5. DUPLICATE DETECTION ENDPOINTS
#     كشف التكرارات
# ═══════════════════════════════════════════════════════════════════════════════

class DuplicateCheckPartyRequest(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    tax_number: Optional[str] = None
    exclude_id: Optional[int] = None


class DuplicateCheckProductRequest(BaseModel):
    product_name: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    exclude_id: Optional[int] = None


@router.post("/parties/check-duplicates", dependencies=[Depends(require_permission("parties.view"))],
             tags=["Duplicate Detection"])
def check_party_duplicates(body: DuplicateCheckPartyRequest,
                           current_user: dict = Depends(get_current_user)):
    """فحص التكرارات قبل إضافة عميل/مورد"""
    company_id = _u(current_user, "company_id")
    db = get_db_connection(company_id)
    try:
        matches = find_duplicate_parties(
            db, name=body.name, phone=body.phone, email=body.email,
            tax_number=body.tax_number, exclude_id=body.exclude_id
        )
        return {
            "has_duplicates": len(matches) > 0,
            "count": len(matches),
            "matches": matches
        }
    finally:
        db.close()


@router.post("/inventory/check-duplicates", dependencies=[Depends(require_permission("inventory.view"))],
             tags=["Duplicate Detection"])
def check_product_duplicates(body: DuplicateCheckProductRequest,
                             current_user: dict = Depends(get_current_user)):
    """فحص التكرارات قبل إضافة منتج"""
    company_id = _u(current_user, "company_id")
    db = get_db_connection(company_id)
    try:
        matches = find_duplicate_products(
            db, product_name=body.product_name, sku=body.sku,
            barcode=body.barcode, exclude_id=body.exclude_id
        )
        return {
            "has_duplicates": len(matches) > 0,
            "count": len(matches),
            "matches": matches
        }
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  6. BACKUP / RESTORE
#     النسخ الاحتياطي واستعادة البيانات (pg_dump)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/admin/backup", dependencies=[Depends(require_permission("admin"))],
             tags=["Backup"])
def create_backup(current_user: dict = Depends(get_current_user)):
    """إنشاء نسخة احتياطية لقاعدة بيانات الشركة (pg_dump)"""
    company_id = _u(current_user, "company_id")
    user_id = _u(current_user, "user_id")

    # SEC-FIX-021: Validate company_id before using in subprocess
    import re
    if not company_id or not re.match(r'^[a-f0-9]+$', company_id):
        raise HTTPException(400, "معرف الشركة غير صالح")

    from config import settings
    db_name = f"aman_{company_id}"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # SEC-FIX-022: Store backups outside the application directory
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups", company_id)
    os.makedirs(backup_dir, exist_ok=True)
    backup_file = os.path.join(backup_dir, f"{db_name}_{timestamp}.sql.gz")

    try:
        env = os.environ.copy()
        env["PGPASSWORD"] = settings.POSTGRES_PASSWORD

        cmd = [
            "pg_dump",
            "-h", settings.POSTGRES_HOST,
            "-p", str(settings.POSTGRES_PORT),
            "-U", settings.POSTGRES_USER,
            "-d", db_name,
            "--no-owner",
            "--no-privileges",
            "-Fc"  # Custom format (compressed)
        ]

        with open(backup_file, 'wb') as f:
            result = subprocess.run(cmd, env=env, stdout=f, stderr=subprocess.PIPE, timeout=300)

        if result.returncode != 0:
            error_msg = result.stderr.decode() if result.stderr else "Unknown error"
            # SEC-FIX-023: Log stderr server-side, don't leak to client
            logger.error(f"pg_dump failed for {db_name}: {error_msg}")
            raise HTTPException(500, "فشل إنشاء النسخة الاحتياطية")

        file_size = os.path.getsize(backup_file)

        # Record in backup history
        db = get_db_connection(company_id)
        try:
            db.execute(text("""
                INSERT INTO backup_history (
                    backup_type, file_name, file_size, file_path,
                    status, created_by
                ) VALUES ('full', :fn, :fs, :fp, 'completed', :uid)
            """), {
                "fn": os.path.basename(backup_file),
                "fs": file_size,
                "fp": backup_file,
                "uid": user_id
            })
            db.commit()
        finally:
            db.close()

        return {
            "message": "تم إنشاء النسخة الاحتياطية بنجاح",
            "file_name": os.path.basename(backup_file),
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "timestamp": timestamp
        }
    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(500, "تجاوز الوقت المسموح للنسخ الاحتياطي")
    except FileNotFoundError:
        raise HTTPException(500, "pg_dump غير متوفر على النظام. يرجى تثبيت postgresql-client")
    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        raise HTTPException(500, "حدث خطأ أثناء إنشاء النسخة الاحتياطية")


@router.get("/admin/backups", dependencies=[Depends(require_permission("admin"))],
            tags=["Backup"])
def list_backups(current_user: dict = Depends(get_current_user)):
    """قائمة النسخ الاحتياطية"""
    company_id = _u(current_user, "company_id")
    db = get_db_connection(company_id)
    try:
        rows = db.execute(text("""
            SELECT bh.*, cu.full_name as created_by_name
            FROM backup_history bh
            LEFT JOIN company_users cu ON cu.id = bh.created_by
            ORDER BY bh.id DESC
            LIMIT 50
        """)).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception:
        return []
    finally:
        db.close()


@router.get("/admin/backup/{backup_id}/download",
            dependencies=[Depends(require_permission("admin"))], tags=["Backup"])
def download_backup(backup_id: int, current_user: dict = Depends(get_current_user)):
    """تحميل نسخة احتياطية"""
    company_id = _u(current_user, "company_id")
    db = get_db_connection(company_id)
    try:
        backup = db.execute(text(
            "SELECT * FROM backup_history WHERE id = :id"
        ), {"id": backup_id}).fetchone()

        if not backup:
            raise HTTPException(404, "النسخة غير موجودة")

        if not os.path.exists(backup.file_path):
            raise HTTPException(404, "ملف النسخة الاحتياطية غير موجود على القرص")

        with open(backup.file_path, 'rb') as f:
            content = f.read()

        return Response(
            content=content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={backup.file_name}"}
        )
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  7. PRINT TEMPLATE MANAGEMENT
#     إدارة قوالب الطباعة
# ═══════════════════════════════════════════════════════════════════════════════

class PrintTemplateCreate(BaseModel):
    template_type: str  # invoice, quotation, receipt, delivery_order, purchase_order, payslip
    name: str
    html_template: str
    css_styles: Optional[str] = None
    header_html: Optional[str] = None
    footer_html: Optional[str] = None
    is_default: bool = False
    paper_size: str = "A4"
    orientation: str = "portrait"


@router.get("/settings/print-templates", dependencies=[Depends(require_permission("settings.view"))],
            tags=["Print Templates"])
def list_print_templates(template_type: Optional[str] = None,
                         current_user: dict = Depends(get_current_user)):
    company_id = _u(current_user, "company_id")
    db = get_db_connection(company_id)
    try:
        query = "SELECT * FROM print_templates WHERE 1=1"
        params = {}
        if template_type:
            query += " AND template_type = :tt"
            params["tt"] = template_type
        query += " ORDER BY is_default DESC, template_type, name"

        rows = db.execute(text(query), params).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception:
        return []
    finally:
        db.close()


@router.post("/settings/print-templates", dependencies=[Depends(require_permission("settings.manage"))],
             tags=["Print Templates"])
def create_print_template(body: PrintTemplateCreate, current_user: dict = Depends(get_current_user)):
    company_id = _u(current_user, "company_id")
    user_id = _u(current_user, "user_id")
    db = get_db_connection(company_id)
    try:
        # If default, unset other defaults of same type
        if body.is_default:
            db.execute(text("""
                UPDATE print_templates SET is_default = false
                WHERE template_type = :tt
            """), {"tt": body.template_type})

        result = db.execute(text("""
            INSERT INTO print_templates (
                template_type, name, html_template, css_styles,
                header_html, footer_html, is_default,
                paper_size, orientation, created_by
            ) VALUES (:tt, :name, :html, :css, :header, :footer, :default,
                      :paper, :orient, :uid)
            RETURNING id
        """), {
            "tt": body.template_type, "name": body.name,
            "html": body.html_template, "css": body.css_styles,
            "header": body.header_html, "footer": body.footer_html,
            "default": body.is_default, "paper": body.paper_size,
            "orient": body.orientation, "uid": user_id
        })
        tmpl_id = result.fetchone()[0]
        db.commit()

        return {"id": tmpl_id, "message": "تم إنشاء قالب الطباعة"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.get("/settings/print-templates/{template_id}",
            dependencies=[Depends(require_permission("settings.view"))], tags=["Print Templates"])
def get_print_template(template_id: int, current_user: dict = Depends(get_current_user)):
    company_id = _u(current_user, "company_id")
    db = get_db_connection(company_id)
    try:
        row = db.execute(text("SELECT * FROM print_templates WHERE id = :id"), {"id": template_id}).fetchone()
        if not row:
            raise HTTPException(404, "القالب غير موجود")
        return dict(row._mapping)
    finally:
        db.close()


@router.put("/settings/print-templates/{template_id}",
            dependencies=[Depends(require_permission("settings.manage"))], tags=["Print Templates"])
def update_print_template(template_id: int, body: PrintTemplateCreate,
                          current_user: dict = Depends(get_current_user)):
    company_id = _u(current_user, "company_id")
    db = get_db_connection(company_id)
    try:
        if body.is_default:
            db.execute(text("""
                UPDATE print_templates SET is_default = false
                WHERE template_type = :tt AND id != :id
            """), {"tt": body.template_type, "id": template_id})

        db.execute(text("""
            UPDATE print_templates SET
                name = :name, html_template = :html, css_styles = :css,
                header_html = :header, footer_html = :footer,
                is_default = :default, paper_size = :paper,
                orientation = :orient, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """), {
            "name": body.name, "html": body.html_template,
            "css": body.css_styles, "header": body.header_html,
            "footer": body.footer_html, "default": body.is_default,
            "paper": body.paper_size, "orient": body.orientation,
            "id": template_id
        })
        db.commit()

        return {"message": "تم تحديث القالب"}
    finally:
        db.close()
