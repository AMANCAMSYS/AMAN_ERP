"""
AMAN ERP — System Completion Router
Bank Import | Zakat Calculator | Consolidation Reports | Fiscal Period Lock | Backup
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from utils.i18n import http_error
from sqlalchemy import text
from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel
from decimal import Decimal, ROUND_HALF_UP
import io
import csv
import json
import logging
import subprocess
import os

from database import get_db_connection, engine as system_engine
from routers.auth import get_current_user
from utils.permissions import require_permission, validate_branch_access
from utils.audit import log_activity
from utils.accounting import (
    get_mapped_account_id,
    get_base_currency
)
from utils.fiscal_lock import create_fiscal_lock_table, check_fiscal_period_open
from utils.duplicate_detection import find_duplicate_parties, find_duplicate_products
from services.gl_service import create_journal_entry  # TASK-015: centralized GL posting

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

            except Exception:
                logger.warning("Bank import line %d failed", idx, exc_info=True)
                errors.append(f"سطر {idx}: خطأ في البيانات")

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
    except Exception:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
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
    except Exception:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  2. ZAKAT CALCULATOR
#     حاسبة الزكاة — حساب الزكاة الشرعي للشركات
#     ⚠️ Islamic Zakat — applies to Muslim-majority countries (SA, AE, etc.)
#     Non-Islamic countries may ignore this module.
#     Frontend should show/hide based on company settings.
#
#     الطرق المدعومة:
#     1. صافي الملكية (ZATCA) — المعتمدة نظامياً في السعودية (الافتراضية)
#     2. صافي الأصول المتداولة — النقد + عروض التجارة + المدينون المرجوون - الديون الحالة
#     3. الربح المعدل — للتقدير
#
#     المراجع: ZATCA، AAOIFI، بيت الزكاة الكويتي
# ═══════════════════════════════════════════════════════════════════════════════

class ZakatCalculateRequest(BaseModel):
    fiscal_year: int
    method: str = "net_assets"  # net_assets (ZATCA, default), net_current_assets, adjusted_profit
    zakat_rate: float = 2.5  # standard Hijri rate (2.5%)
    use_gregorian_rate: bool = False  # If True, uses 2.5775% for Gregorian year
    branch_id: Optional[int] = None  # Filter by branch (None = all branches)
    notes: Optional[str] = None


def _zakat_balance_query(account_filter: str, account_types: list, branch_id=None, sign="debit"):
    """
    Build a balance query that supports branch filtering.
    When branch_id is None: use accounts.balance (fast, all branches).
    When branch_id is set: compute from journal_lines (branch-specific).
    sign='debit' means debit-normal (assets/expenses), 'credit' means credit-normal (liabilities/equity/revenue).
    Returns (sql_string, params_dict).
    """
    type_list = "','".join(account_types)
    if branch_id:
        if sign == "debit":
            agg = "SUM(jl.debit - jl.credit)"
        else:
            agg = "SUM(jl.credit - jl.debit)"
        sql = f"""
            SELECT COALESCE({agg}, 0)
            FROM journal_lines jl
            JOIN journal_entries je ON jl.journal_entry_id = je.id AND je.status = 'posted'
            JOIN accounts a ON jl.account_id = a.id
            WHERE je.branch_id = :branch_id
            AND a.account_type IN ('{type_list}')
            AND ({account_filter})
        """
        return sql, {"branch_id": branch_id}
    else:
        sql = f"""
            SELECT COALESCE(SUM(a.balance), 0)
            FROM accounts a WHERE a.account_type IN ('{type_list}')
            AND ({account_filter})
        """
        return sql, {}


def _zakat_account_breakdown(db, account_filter: str, account_types: list, branch_id=None, sign="debit"):
    """
    Return list of individual accounts that matched the filter, with their balances.
    Used for debugging/audit to show which accounts contributed.
    """
    type_list = "','".join(account_types)
    if branch_id:
        if sign == "debit":
            agg = "SUM(jl.debit - jl.credit)"
        else:
            agg = "SUM(jl.credit - jl.debit)"
        sql = f"""
            SELECT a.account_code, a.name, a.name_en, {agg} as balance
            FROM journal_lines jl
            JOIN journal_entries je ON jl.journal_entry_id = je.id AND je.status = 'posted'
            JOIN accounts a ON jl.account_id = a.id
            WHERE je.branch_id = :branch_id
            AND a.account_type IN ('{type_list}')
            AND ({account_filter})
            GROUP BY a.id, a.account_code, a.name, a.name_en
            HAVING {agg} != 0
            ORDER BY a.account_code
        """
        rows = db.execute(text(sql), {"branch_id": branch_id}).fetchall()
    else:
        sql = f"""
            SELECT a.account_code, a.name, a.name_en, a.balance
            FROM accounts a WHERE a.account_type IN ('{type_list}')
            AND ({account_filter})
            AND a.balance != 0
            ORDER BY a.account_code
        """
        rows = db.execute(text(sql)).fetchall()
    return [{"code": r.account_code, "name": r.name, "name_en": r.name_en, "balance": float(r.balance)} for r in rows]


@router.post("/accounting/zakat/calculate", dependencies=[Depends(require_permission("accounting.manage"))],
             tags=["Zakat"])
def calculate_zakat(body: ZakatCalculateRequest, current_user: dict = Depends(get_current_user)):
    """
    حساب الزكاة الشرعية — Sharia-compliant Zakat Calculation
    Supports branch filtering via branch_id parameter.
    """
    company_id = _u(current_user, "company_id")
    user_id = _u(current_user, "user_id")
    db = get_db_connection(company_id)
    try:
        # Validate branch access
        branch_id = validate_branch_access(current_user, body.branch_id) if body.branch_id else None

        # Determine rate (Decimal for legal tax precision)
        rate = Decimal('2.57764') if body.use_gregorian_rate else Decimal(str(body.zakat_rate))

        if body.method == "net_current_assets":
            # ══════════════════════════════════════════════════════════════
            # طريقة صافي الأصول المتداولة — Net Current Assets Method
            # وفقاً لمعايير AAOIFI وجمهور الفقهاء
            # الوعاء = النقد + عروض التجارة + المدينون المرجوون
            #        + استثمارات المضاربة - الالتزامات المتداولة
            # ══════════════════════════════════════════════════════════════

            # ── النقد (أصل الأصول المالية في الزكاة بالإجماع) ──
            cash_filter = """
                    a.account_code LIKE '1101%%'
                    OR a.account_code LIKE '11001%%'
                    OR a.account_code LIKE '11010%%'
                    OR a.account_code LIKE '11020%%'
                    OR a.name LIKE '%%نقد%%' OR a.name LIKE '%%صندوق%%'
                    OR a.name LIKE '%%بنك%%' OR a.name LIKE '%%كاش%%'
                    OR a.name_en LIKE '%%cash%%' OR a.name_en LIKE '%%bank%%'
            """
            cash_exclude = """
                AND a.name NOT LIKE '%%مجمع%%'
                AND a.name NOT LIKE '%%استثمار%%'
                AND (a.name_en IS NULL OR a.name_en NOT LIKE '%%invest%%')
            """
            cash_full_filter = f"({cash_filter}) {cash_exclude}"
            cash_sql, cash_params = _zakat_balance_query(cash_full_filter, ['asset'], branch_id)
            cash = db.execute(text(cash_sql), cash_params).scalar() or 0
            cash_accounts = _zakat_account_breakdown(db, cash_full_filter, ['asset'], branch_id)

            # ── تصفية النقد — استبعاد شبه النقد والودائع الاستثمارية ──
            quasi_filter = """
                    a.name LIKE '%%نقد معادل%%' OR a.name LIKE '%%شبه نقد%%'
                    OR a.name LIKE '%%وديعة استثمار%%' OR a.name LIKE '%%سندات خزانة%%'
                    OR a.name_en LIKE '%%cash equivalent%%' OR a.name_en LIKE '%%treasury bill%%'
                    OR a.name_en LIKE '%%money market%%'
            """
            quasi_sql, quasi_params = _zakat_balance_query(quasi_filter, ['asset'], branch_id)
            quasi_cash = db.execute(text(quasi_sql), quasi_params).scalar() or 0

            net_cash = Decimal(str(cash)) - Decimal(str(quasi_cash))

            # ── عروض التجارة (كل مال أُعِد للبيع في سوقه خلال السنة) ──
            trade_filter = """
                    a.account_code LIKE '1103%%'
                    OR a.account_code LIKE '13001%%'
                    OR a.account_code LIKE '13010%%'
                    OR a.name LIKE '%%مخزون%%' OR a.name LIKE '%%بضاع%%'
                    OR a.name LIKE '%%عروض%%تجار%%'
                    OR a.name_en LIKE '%%inventory%%' OR a.name_en LIKE '%%stock%%'
                    OR a.name_en LIKE '%%goods%%'
            """
            trade_exclude = """
                AND a.name NOT LIKE '%%تحت التصنيع%%'
                AND a.name NOT LIKE '%%مواد خام%%'
                AND a.name NOT LIKE '%%قطع غيار%%'
                AND (a.name_en IS NULL OR a.name_en NOT LIKE '%%raw material%%')
                AND (a.name_en IS NULL OR a.name_en NOT LIKE '%%work in progress%%')
                AND (a.name_en IS NULL OR a.name_en NOT LIKE '%%spare part%%')
            """
            trade_full_filter = f"({trade_filter}) {trade_exclude}"
            trade_sql, trade_params = _zakat_balance_query(trade_full_filter, ['asset'], branch_id)
            trade_goods = db.execute(text(trade_sql), trade_params).scalar() or 0
            trade_accounts = _zakat_account_breakdown(db, trade_full_filter, ['asset'], branch_id)

            # ── تصفية عروض التجارة — استبعاد البضاعة الكاسدة ──
            stale_filter = """
                    a.name LIKE '%%كاسد%%' OR a.name LIKE '%%راكد%%'
                    OR a.name LIKE '%%تالف%%' OR a.name LIKE '%%منتهي الصلاحية%%'
                    OR a.name_en LIKE '%%obsolete%%' OR a.name_en LIKE '%%stale%%'
                    OR a.name_en LIKE '%%expired%%' OR a.name_en LIKE '%%damaged%%'
            """
            stale_sql, stale_params = _zakat_balance_query(stale_filter, ['asset'], branch_id)
            stale_inventory = db.execute(text(stale_sql), stale_params).scalar() or 0

            net_trade_goods = Decimal(str(trade_goods)) - Decimal(str(stale_inventory))

            # ── المدينون المرجوون ──
            recv_filter = """
                    a.account_code LIKE '1102%%' OR a.account_code LIKE '1108%%'
                    OR a.account_code LIKE '1109%%'
                    OR a.account_code LIKE '12001%%' OR a.account_code LIKE '12010%%'
                    OR a.account_code LIKE '12020%%'
                    OR a.name LIKE '%%عملاء%%' OR a.name LIKE '%%مدين%%'
                    OR a.name_en LIKE '%%receivable%%'
            """
            recv_exclude = """
                AND a.name NOT LIKE '%%مشكوك%%'
                AND a.name NOT LIKE '%%معدوم%%'
                AND (a.name_en IS NULL OR a.name_en NOT LIKE '%%doubtful%%')
                AND (a.name_en IS NULL OR a.name_en NOT LIKE '%%bad debt%%')
            """
            recv_full_filter = f"({recv_filter}) {recv_exclude}"
            recv_sql, recv_params = _zakat_balance_query(recv_full_filter, ['asset'], branch_id)
            receivables = db.execute(text(recv_sql), recv_params).scalar() or 0
            recv_accounts = _zakat_account_breakdown(db, recv_full_filter, ['asset'], branch_id)

            # ── استثمارات المضاربة (قصيرة الأجل) ──
            tinv_filter = """
                    a.name LIKE '%%أسهم%%متاجر%%' OR a.name LIKE '%%محفظة%%مضارب%%'
                    OR a.name LIKE '%%استثمار%%قصير%%'
                    OR a.name_en LIKE '%%trading%%invest%%'
                    OR a.name_en LIKE '%%short%%term%%invest%%'
            """
            tinv_sql, tinv_params = _zakat_balance_query(tinv_filter, ['asset'], branch_id)
            trading_investments = db.execute(text(tinv_sql), tinv_params).scalar() or 0

            # ── الالتزامات المتداولة (تُخصم من الوعاء) ──
            cl_filter = """
                    a.account_code LIKE '21%%'
                    OR a.name LIKE '%%دائن%%' OR a.name LIKE '%%مورد%%'
                    OR a.name LIKE '%%مستحق%%' OR a.name LIKE '%%مصروف%%مستحق%%'
                    OR a.name LIKE '%%قرض%%قصير%%'
                    OR a.name_en LIKE '%%payable%%' OR a.name_en LIKE '%%accrued%%'
                    OR a.name_en LIKE '%%supplier%%' OR a.name_en LIKE '%%short%%term%%loan%%'
                    OR a.name_en LIKE '%%current%%liabilit%%'
            """
            cl_sql, cl_params = _zakat_balance_query(cl_filter, ['liability', 'current_liability'], branch_id, sign="credit")
            current_liabilities = db.execute(text(cl_sql), cl_params).scalar() or 0
            cl_accounts = _zakat_account_breakdown(db, cl_filter, ['liability', 'current_liability'], branch_id, sign="credit")

            # ── الأصول المستبعدة (للعرض فقط) ──
            fa_filter = """
                    a.account_code LIKE '12%%' OR a.account_code LIKE '15%%'
                    OR a.account_code LIKE '16%%'
                    OR a.name LIKE '%%أصول ثابتة%%' OR a.name LIKE '%%معدات%%'
                    OR a.name LIKE '%%مباني%%' OR a.name LIKE '%%سيارات%%'
                    OR a.name LIKE '%%أثاث%%' OR a.name LIKE '%%أراضي%%'
                    OR a.name LIKE '%%مجمع%%'
                    OR a.name_en LIKE '%%fixed asset%%' OR a.name_en LIKE '%%equipment%%'
                    OR a.name_en LIKE '%%building%%' OR a.name_en LIKE '%%vehicle%%'
                    OR a.name_en LIKE '%%furniture%%' OR a.name_en LIKE '%%depreciation%%'
            """
            fa_sql, fa_params = _zakat_balance_query(fa_filter, ['asset'], branch_id)
            fixed_assets = db.execute(text(fa_sql), fa_params).scalar() or 0

            intang_filter = """
                    a.account_code LIKE '13%%' OR a.account_code LIKE '18%%'
                    OR a.name LIKE '%%شهرة%%' OR a.name LIKE '%%براءة%%'
                    OR a.name LIKE '%%علامة تجارية%%' OR a.name LIKE '%%رخصة%%'
                    OR a.name LIKE '%%غير ملموس%%'
                    OR a.name_en LIKE '%%intangible%%' OR a.name_en LIKE '%%goodwill%%'
                    OR a.name_en LIKE '%%patent%%' OR a.name_en LIKE '%%trademark%%'
            """
            intang_sql, intang_params = _zakat_balance_query(intang_filter, ['asset'], branch_id)
            intangible_assets = db.execute(text(intang_sql), intang_params).scalar() or 0

            wip_filter = """
                    a.account_code LIKE '1110%%'
                    OR a.name LIKE '%%تحت الإنشاء%%' OR a.name LIKE '%%تحت التصنيع%%'
                    OR a.name LIKE '%%مواد خام%%' OR a.name LIKE '%%قطع غيار%%'
                    OR a.name_en LIKE '%%work in progress%%' OR a.name_en LIKE '%%under construction%%'
                    OR a.name_en LIKE '%%raw material%%' OR a.name_en LIKE '%%spare part%%'
            """
            wip_sql, wip_params = _zakat_balance_query(wip_filter, ['asset'], branch_id)
            wip = db.execute(text(wip_sql), wip_params).scalar() or 0

            # ── حساب الوعاء الزكوي ──
            # الوعاء = النقد + عروض التجارة + المدينون المرجوون + استثمارات المضاربة
            #        - الالتزامات المتداولة (الديون الحالة)
            gross_zakatable = net_cash + net_trade_goods + Decimal(str(receivables)) + Decimal(str(trading_investments))
            cl_decimal = Decimal(str(current_liabilities))
            zakat_base = max(Decimal('0'), gross_zakatable - cl_decimal)

            zakat_amount = (zakat_base * rate / Decimal('100')).quantize(Decimal('0.01'), ROUND_HALF_UP)

            additions = [
                {"label": "Cash & Bank Balances", "label_ar": "النقد والأرصدة البنكية", "amount": float(Decimal(str(cash)).quantize(Decimal('0.01')))},
            ]
            if quasi_cash:
                additions.append({"label": "Less: Quasi-Cash / Investment Deposits", "label_ar": "(-) النقد المعادل / ودائع استثمارية", "amount": float(Decimal(str(-quasi_cash)).quantize(Decimal('0.01')))})
            additions.append({"label": "Net Cash", "label_ar": "صافي النقد", "amount": float(net_cash.quantize(Decimal('0.01'))), "is_subtotal": True})

            additions.append({"label": "Trade Goods (Inventory for Sale)", "label_ar": "عروض التجارة (المخزون المعد للبيع)", "amount": float(Decimal(str(trade_goods)).quantize(Decimal('0.01')))})
            if stale_inventory:
                additions.append({"label": "Less: Stale/Obsolete Inventory", "label_ar": "(-) بضاعة كاسدة / راكدة", "amount": float(Decimal(str(-stale_inventory)).quantize(Decimal('0.01')))})
            additions.append({"label": "Net Trade Goods", "label_ar": "صافي عروض التجارة", "amount": float(net_trade_goods.quantize(Decimal('0.01'))), "is_subtotal": True})

            if receivables:
                additions.append({"label": "Collectible Receivables", "label_ar": "المدينون المرجوون (مرجو تحصيلهم)", "amount": float(Decimal(str(receivables)).quantize(Decimal('0.01')))})
            if trading_investments:
                additions.append({"label": "Trading Investments (Short-term)", "label_ar": "استثمارات المضاربة (قصيرة الأجل)", "amount": float(Decimal(str(trading_investments)).quantize(Decimal('0.01')))})

            total_additions = str(gross_zakatable.quantize(Decimal('0.01')))

            deductions = []
            if current_liabilities:
                deductions.append({"label": "Current Liabilities (Short-term Debts)", "label_ar": "الالتزامات المتداولة (الديون الحالة قصيرة الأجل)", "amount": float(cl_decimal.quantize(Decimal('0.01')))})
            total_deductions = str(cl_decimal.quantize(Decimal('0.01')))

            # الأصول المستبعدة (للعرض فقط — informational)
            excluded_info = []
            if fixed_assets:
                excluded_info.append({"label": "Fixed Assets (non-zakatable)", "label_ar": "الأصول الثابتة (قنية — لا تُزكّى)", "amount": float(Decimal(str(fixed_assets)).quantize(Decimal('0.01')))})
            if intangible_assets:
                excluded_info.append({"label": "Intangible Assets", "label_ar": "الأصول المعنوية (غير ملموسة)", "amount": float(Decimal(str(intangible_assets)).quantize(Decimal('0.01')))})
            if wip:
                excluded_info.append({"label": "Work In Progress / Raw Materials", "label_ar": "تحت الإنشاء / مواد خام", "amount": float(Decimal(str(wip)).quantize(Decimal('0.01')))})

            details = {
                "method_name_ar": "طريقة صافي الأصول المتداولة",
                "method_name_en": "Net Current Assets Method (AAOIFI)",
                "sharia_basis": "النقد + عروض التجارة + المدينون المرجوون - الديون الحالة (وفقاً لجمهور الفقهاء ومعايير AAOIFI)",
                "excluded_assets": excluded_info,
                "zakat_base": float(zakat_base.quantize(Decimal('0.01'))),
                "rate_type": "gregorian" if body.use_gregorian_rate else "hijri",
                "applied_rate": float(rate),
                "account_breakdown": {
                    "cash": cash_accounts,
                    "trade_goods": trade_accounts,
                    "receivables": recv_accounts,
                    "current_liabilities": cl_accounts
                }
            }

        elif body.method == "net_assets":
            # ── طريقة صافي الملكية — ZATCA (المعتمدة نظامياً في السعودية) ──
            # الطريقة الملزمة للشركات السعودية التي تمسك حسابات نظامية

            # 1. Equity components
            eq_sql, eq_params = _zakat_balance_query("1=1", ['equity'], branch_id, sign="credit")
            equity = db.execute(text(eq_sql), eq_params).scalar() or 0

            # 2. Long-term liabilities
            lt_filter = """
                    a.name LIKE '%%طويل%%' OR a.name_en LIKE '%%long%%term%%'
                    OR a.account_code LIKE '22%%'
            """
            lt_sql, lt_params = _zakat_balance_query(lt_filter, ['long_term_liability', 'liability'], branch_id, sign="credit")
            lt_liabilities = db.execute(text(lt_sql), lt_params).scalar() or 0

            # 3. Provisions
            prov_filter = "a.name LIKE '%%مخصص%%' OR a.name_en LIKE '%%provision%%'"
            prov_sql, prov_params = _zakat_balance_query(prov_filter, ['liability', 'equity'], branch_id, sign="credit")
            provisions = db.execute(text(prov_sql), prov_params).scalar() or 0

            # 4. Net profit
            rev_sql, rev_params = _zakat_balance_query("1=1", ['revenue', 'income'], branch_id, sign="credit")
            revenue = db.execute(text(rev_sql), rev_params).scalar() or 0
            exp_sql, exp_params = _zakat_balance_query("1=1", ['expense', 'cogs'], branch_id, sign="debit")
            expenses = db.execute(text(exp_sql), exp_params).scalar() or 0
            net_profit = Decimal(str(revenue)) - Decimal(str(expenses))

            total_add = Decimal(str(equity)) + Decimal(str(lt_liabilities)) + Decimal(str(provisions))
            if net_profit > 0:
                total_add += net_profit

            # 5. Fixed assets (fixed: removed overly-broad '%أصل%' pattern)
            zatca_fa_filter = """
                    a.name LIKE '%%أصول ثابتة%%' OR a.name LIKE '%%معدات%%'
                    OR a.name LIKE '%%آلات%%' OR a.name LIKE '%%مباني%%'
                    OR a.name LIKE '%%سيارات%%' OR a.name LIKE '%%أثاث%%'
                    OR a.name LIKE '%%أراضي%%' OR a.name LIKE '%%مجمع%%'
                    OR a.name_en LIKE '%%fixed%%asset%%' OR a.name_en LIKE '%%equipment%%'
                    OR a.name_en LIKE '%%machine%%' OR a.name_en LIKE '%%building%%'
                    OR a.name_en LIKE '%%vehicle%%' OR a.name_en LIKE '%%furniture%%'
                    OR a.name_en LIKE '%%depreciation%%'
                    OR a.account_code LIKE '12%%' OR a.account_code LIKE '15%%'
                    OR a.account_code LIKE '16%%'
            """
            zatca_fa_sql, zatca_fa_params = _zakat_balance_query(zatca_fa_filter, ['asset'], branch_id)
            fixed_assets = db.execute(text(zatca_fa_sql), zatca_fa_params).scalar() or 0

            # 6. Long-term investments (fixed: removed overly-broad '%استثمار%' pattern)
            zatca_inv_filter = """
                    a.name LIKE '%%استثمار%%طويل%%'
                    OR a.name_en LIKE '%%long%%invest%%'
                    OR a.account_code LIKE '14%%'
            """
            zatca_inv_sql, zatca_inv_params = _zakat_balance_query(zatca_inv_filter, ['asset'], branch_id)
            lt_investments = db.execute(text(zatca_inv_sql), zatca_inv_params).scalar() or 0

            # 7. Intangible assets (شهرة، براءات، علامات تجارية — non-zakatable per ZATCA)
            # NOTE: account_code LIKE '13%%' is NOT used broadly because 13001 is inventory (مخزون بضاعة).
            #       Instead we use specific sub-codes 1301-1305 and name-based matching.
            zatca_intang_filter = """
                    a.name LIKE '%%شهرة%%' OR a.name LIKE '%%براءة%%'
                    OR a.name LIKE '%%علامة تجارية%%' OR a.name LIKE '%%رخصة%%'
                    OR a.name LIKE '%%غير ملموس%%' OR a.name LIKE '%%أصول معنوية%%'
                    OR a.name_en LIKE '%%intangible%%' OR a.name_en LIKE '%%goodwill%%'
                    OR a.name_en LIKE '%%patent%%' OR a.name_en LIKE '%%trademark%%'
                    OR a.account_code LIKE '1301%%' OR a.account_code LIKE '1302%%'
                    OR a.account_code LIKE '1303%%' OR a.account_code LIKE '1304%%'
                    OR a.account_code LIKE '1305%%' OR a.account_code LIKE '18%%'
            """
            zatca_intang_sql, zatca_intang_params = _zakat_balance_query(zatca_intang_filter, ['asset'], branch_id)
            intangible_assets = db.execute(text(zatca_intang_sql), zatca_intang_params).scalar() or 0

            # 8. Work in progress / under construction (non-zakatable)
            zatca_wip_filter = """
                    a.name LIKE '%%تحت الإنشاء%%' OR a.name LIKE '%%تحت التنفيذ%%'
                    OR a.name LIKE '%%مشروعات تحت%%'
                    OR a.name_en LIKE '%%under construction%%' OR a.name_en LIKE '%%work in progress%%'
                    OR a.account_code LIKE '17%%'
            """
            zatca_wip_sql, zatca_wip_params = _zakat_balance_query(zatca_wip_filter, ['asset'], branch_id)
            wip = db.execute(text(zatca_wip_sql), zatca_wip_params).scalar() or 0

            total_ded = Decimal(str(fixed_assets)) + Decimal(str(lt_investments)) + Decimal(str(intangible_assets)) + Decimal(str(wip))
            zakat_base = max(Decimal('0'), total_add - total_ded)
            zakat_amount = (zakat_base * rate / Decimal('100')).quantize(Decimal('0.01'), ROUND_HALF_UP)

            additions = [
                {"label": "Equity (Capital + Reserves + RE)", "label_ar": "حقوق الملكية (رأس المال + احتياطيات + أرباح مبقاة)", "amount": float(Decimal(str(equity)).quantize(Decimal('0.01')))},
                {"label": "Long-term Liabilities", "label_ar": "الالتزامات طويلة الأجل", "amount": float(Decimal(str(lt_liabilities)).quantize(Decimal('0.01')))},
                {"label": "Provisions", "label_ar": "المخصصات", "amount": float(Decimal(str(provisions)).quantize(Decimal('0.01')))},
                {"label": "Net Profit", "label_ar": "صافي الربح", "amount": float(net_profit.quantize(Decimal('0.01'))) if net_profit > 0 else 0},
            ]
            total_additions = str(total_add.quantize(Decimal('0.01')))

            deductions = [
                {"label": "Fixed Assets & Equipment", "label_ar": "الأصول الثابتة والمعدات", "amount": float(Decimal(str(fixed_assets)).quantize(Decimal('0.01')))},
                {"label": "Intangible Assets (Goodwill, Patents)", "label_ar": "الأصول المعنوية (شهرة، براءات)", "amount": float(Decimal(str(intangible_assets)).quantize(Decimal('0.01')))},
                {"label": "Long-term Investments", "label_ar": "الاستثمارات طويلة الأجل", "amount": float(Decimal(str(lt_investments)).quantize(Decimal('0.01')))},
            ]
            if wip:
                deductions.append({"label": "Work in Progress / Under Construction", "label_ar": "مشروعات تحت التنفيذ", "amount": float(Decimal(str(wip)).quantize(Decimal('0.01')))})
            total_deductions = str(total_ded.quantize(Decimal('0.01')))

            details = {
                "method_name_ar": "طريقة صافي الملكية — ZATCA (المعتمدة نظامياً)",
                "method_name_en": "Net Equity Method — ZATCA (Regulatory)",
                "note": "الطريقة المعتمدة نظامياً من هيئة الزكاة والضريبة والجمارك للشركات السعودية",
                "zakat_base": float(zakat_base.quantize(Decimal('0.01'))),
                "rate_type": "gregorian" if body.use_gregorian_rate else "hijri",
                "applied_rate": float(rate)
            }

        else:  # adjusted_profit
            # Revenue
            ap_rev_sql, ap_rev_params = _zakat_balance_query("1=1", ['revenue', 'income', 'other_income'], branch_id, sign="credit")
            revenue = db.execute(text(ap_rev_sql), ap_rev_params).scalar() or 0

            # Expenses
            ap_exp_sql, ap_exp_params = _zakat_balance_query("1=1", ['expense', 'cogs', 'other_expense'], branch_id, sign="debit")
            expenses = db.execute(text(ap_exp_sql), ap_exp_params).scalar() or 0

            net_profit = Decimal(str(revenue)) - Decimal(str(expenses))

            # Add-backs: Non-deductible items
            dep_filter = "a.name LIKE '%%استهلاك%%' OR a.name LIKE '%%إهلاك%%' OR a.name_en LIKE '%%depreciation%%' OR a.name_en LIKE '%%amortization%%'"
            dep_sql, dep_params = _zakat_balance_query(dep_filter, ['expense'], branch_id, sign="debit")
            depreciation = db.execute(text(dep_sql), dep_params).scalar() or 0

            provexp_filter = "a.name LIKE '%%مخصص%%' OR a.name_en LIKE '%%provision%%'"
            provexp_sql, provexp_params = _zakat_balance_query(provexp_filter, ['expense'], branch_id, sign="debit")
            provision_expense = db.execute(text(provexp_sql), provexp_params).scalar() or 0

            pen_filter = "a.name LIKE '%%غرام%%' OR a.name LIKE '%%جزاء%%' OR a.name_en LIKE '%%penalty%%' OR a.name_en LIKE '%%fine%%'"
            pen_sql, pen_params = _zakat_balance_query(pen_filter, ['expense'], branch_id, sign="debit")
            penalties = db.execute(text(pen_sql), pen_params).scalar() or 0

            total_add_backs = Decimal(str(depreciation)) + Decimal(str(provision_expense)) + Decimal(str(penalties))
            adjusted_profit = net_profit + total_add_backs

            zakat_base = max(Decimal('0'), adjusted_profit)
            zakat_amount = (zakat_base * rate / Decimal('100')).quantize(Decimal('0.01'), ROUND_HALF_UP)

            additions = [
                {"label": "Revenue", "label_ar": "الإيرادات", "amount": float(Decimal(str(revenue)).quantize(Decimal('0.01')))},
                {"label": "Less: Expenses", "label_ar": "(-) المصروفات", "amount": float(Decimal(str(-expenses)).quantize(Decimal('0.01'))) if expenses else 0},
                {"label": "Net Profit", "label_ar": "صافي الربح", "amount": float(net_profit.quantize(Decimal('0.01'))), "is_subtotal": True},
                {"label": "Add: Depreciation", "label_ar": "(+) الاستهلاك/الإهلاك", "amount": float(Decimal(str(depreciation)).quantize(Decimal('0.01')))},
                {"label": "Add: Provisions", "label_ar": "(+) المخصصات", "amount": float(Decimal(str(provision_expense)).quantize(Decimal('0.01')))},
                {"label": "Add: Penalties & Fines", "label_ar": "(+) الغرامات والجزاءات", "amount": float(Decimal(str(penalties)).quantize(Decimal('0.01')))},
            ]
            total_additions = str(adjusted_profit.quantize(Decimal('0.01')))
            deductions = []
            total_deductions = "0.00"

            details = {
                "method_name_ar": "طريقة الربح المُعدَّل",
                "method_name_en": "Adjusted Profit Method",
                "zakat_base": float(zakat_base.quantize(Decimal('0.01'))),
                "rate_type": "gregorian" if body.use_gregorian_rate else "hijri",
                "applied_rate": float(rate)
            }

        method_names = {
            "net_assets": "صافي الملكية — ZATCA",
            "net_current_assets": "صافي الأصول المتداولة",
            "adjusted_profit": "الربح المُعدَّل"
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
            "method_ar": method_names.get(body.method, body.method),
            "details": details,
            "additions": additions,
            "total_additions": total_additions,
            "deductions": deductions,
            "total_deductions": total_deductions,
            "zakat_base": str(zakat_base.quantize(Decimal('0.01'))),
            "zakat_rate": float(rate),
            "rate_display": f"{float(rate)}%" if body.use_gregorian_rate else f"{body.zakat_rate}%",
            "zakat_amount": str(zakat_amount),
            "branch_id": branch_id,
            "message": f"الزكاة المستحقة: {zakat_amount:,.2f}"
        }
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
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
            raise HTTPException(400, "تم ترحيل الزكاة بالفعل لهذا العام المالي")

        amount = Decimal(str(zakat.zakat_amount))
        if amount <= 0:
            raise HTTPException(400, "مبلغ الزكاة صفر")

        # Phase 5 / ZAK-F01: enforce fiscal lock on zakat posting date
        check_fiscal_period_open(db, f"{fiscal_year}-12-31")

        currency = get_base_currency(db)

        # TASK-015: route through centralized GL service (idempotent, validated, audited)
        exp_acc = get_mapped_account_id(db, "acc_map_zakat_expense")
        pay_acc = get_mapped_account_id(db, "acc_map_zakat_payable")
        if not exp_acc or not pay_acc:
            raise HTTPException(400, "حسابات الزكاة غير معرّفة في خريطة الحسابات")

        lines = [
            {"account_id": exp_acc, "debit": amount, "credit": 0, "description": "مصروف زكاة"},
            {"account_id": pay_acc, "debit": 0, "credit": amount, "description": "زكاة مستحقة"},
        ]
        je_id, je_number = create_journal_entry(
            db=db,
            company_id=company_id,
            date=f"{fiscal_year}-12-31",
            description=f"زكاة عام {fiscal_year}",
            lines=lines,
            user_id=user_id,
            reference=f"ZAKAT-{fiscal_year}",
            status="posted",
            currency=currency,
            source="Zakat",
            source_id=fiscal_year,
            username=_u(current_user, "username", ""),
            idempotency_key=f"zakat-{fiscal_year}",
        )

        db.execute(text("""
            UPDATE zakat_calculations SET status = 'posted', journal_entry_id = :jeid
            WHERE fiscal_year = :fy
        """), {"jeid": je_id, "fy": fiscal_year})

        db.commit()

        log_activity(db, user_id, _u(current_user, "username", ""),
                     "zakat.post", "zakat_calculation", str(fiscal_year),
                     {"amount": str(amount), "journal_entry": je_number})

        return {
            "journal_entry_id": je_id,
            "entry_number": je_number,
            "amount": str(amount),
            "message": f"تم ترحيل قيد الزكاة بمبلغ {amount:,.2f}"
        }
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
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
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
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

        log_activity(db, user_id, _u(current_user, "username", ""),
                     "fiscal_period.lock", "fiscal_period", str(period_id),
                     {"period_name": period.period_name})

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

            log_activity(db, user_id, _u(current_user, "username", ""),
                         "admin.backup.create", "backup",
                         os.path.basename(backup_file),
                         {"file_size_mb": round(file_size / (1024 * 1024), 2)})
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
    except Exception:
        db.rollback()
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
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
            raise HTTPException(**http_error(404, "template_not_found"))
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
