from sqlalchemy import text
from typing import Optional, List, Dict
from fastapi import HTTPException
from decimal import Decimal, ROUND_HALF_UP
import logging

logger = logging.getLogger(__name__)

_D2 = Decimal('0.01')

def _to_decimal(v) -> Decimal:
    """Convert any numeric value to Decimal safely."""
    if v is None:
        return Decimal('0')
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))


def validate_je_lines(je_lines: List[Dict], source: str = "auto") -> List[Dict]:
    """
    Validate journal entry lines before insertion.
    1. Reject lines with None account_id (instead of silently dropping them)
    2. Verify total debits == total credits
    3. Reject negative amounts
    Returns only valid, non-zero lines.
    Raises HTTPException if validation fails.
    """
    # Check for None account IDs
    missing = [l.get("description", "unknown") for l in je_lines if l.get("account_id") is None]
    if missing:
        logger.error(f"JE validation ({source}): Missing account mappings for: {missing}")
        raise HTTPException(
            400,
            f"لا يمكن ترحيل القيد - حسابات غير معرفة: {', '.join(missing)}"
        )

    # Filter out zero lines
    valid = [l for l in je_lines if l.get("debit", 0) > 0 or l.get("credit", 0) > 0]

    if len(valid) < 2:
        raise HTTPException(400, "القيد المحاسبي يحتاج سطرين على الأقل")

    # Check for negatives
    for l in valid:
        if l.get("debit", 0) < 0 or l.get("credit", 0) < 0:
            raise HTTPException(400, f"لا يمكن وجود قيم سالبة في القيد: {l.get('description')}")

    # Balance check
    total_debit = sum(l.get("debit", 0) for l in valid)
    total_credit = sum(l.get("credit", 0) for l in valid)
    diff = abs(total_debit - total_credit)

    if diff > 0.01:
        logger.error(f"JE validation ({source}): Unbalanced D={total_debit:.2f} C={total_credit:.2f} diff={diff:.2f}")
        raise HTTPException(
            400,
            f"القيد غير متوازن: مدين={total_debit:.2f} دائن={total_credit:.2f} فرق={diff:.2f}"
        )

    return valid


def generate_sequential_number(db, prefix: str, table: str, column: str) -> str:
    """
    Generate a sequential document number.
    Example: prefix='SINV-2026' → 'SINV-2026-00001'
    
    Uses MAX extraction of trailing digits from existing numbers to determine next.
    table and column are developer-defined constants (not user input).
    """
    # SEC-003: Validate table/column identifiers to prevent SQL injection
    from utils.sql_safety import validate_sql_identifier
    validate_sql_identifier(table, "table")
    validate_sql_identifier(column, "column")
    
    result = db.execute(text(f"""
        SELECT MAX(CAST(SUBSTRING({column} FROM '[0-9]+$') AS INTEGER))
        FROM {table} WHERE {column} LIKE :pattern
    """), {"pattern": f"{prefix}-%"}).scalar()
    next_num = (result or 0) + 1
    return f"{prefix}-{str(next_num).zfill(5)}"


def get_mapped_account_id(db, mapping_key: str) -> Optional[int]:
    """
    Retrieves the account ID mapped to a specific system role from company_settings.
    """
    result = db.execute(
        text("SELECT setting_value FROM company_settings WHERE setting_key = :key"),
        {"key": mapping_key}
    ).fetchone()

    if not result or not result[0]:
        return None

    try:
        return int(result[0])
    except (TypeError, ValueError):
        logger.error("Invalid mapped account id for key '%s': %s", mapping_key, result[0])
        return None

def get_account_id_legacy(db, account_code: str) -> Optional[int]:
    """
    Legacy helper to find an account ID by its code. 
    Use get_mapped_account_id instead wherever possible.
    """
    result = db.execute(text("SELECT id FROM accounts WHERE account_code = :code"), {"code": account_code}).fetchone()
    return result[0] if result else None

def get_base_currency(db) -> str:
    """
    Resolve the company's base currency dynamically.
    Checks currencies table first, then company_settings, falls back to 'SYP'.
    """
    row = db.execute(text("SELECT code FROM currencies WHERE is_base = TRUE LIMIT 1")).fetchone()
    if not row:
        row = db.execute(text("SELECT setting_value AS code FROM company_settings WHERE setting_key = 'default_currency'")).fetchone()
    return row[0] if row else "SYP"

def update_account_balance(db, account_id: int, debit_base, credit_base, debit_curr=0, credit_curr=0, currency: str = None):
    """
    Updates both the base balance and the foreign currency balance of an account.
    Accepts float or Decimal values — internally uses Decimal for precision.
    """
    # Convert all inputs to Decimal for precision
    debit_base = _to_decimal(debit_base)
    credit_base = _to_decimal(credit_base)
    debit_curr = _to_decimal(debit_curr)
    credit_curr = _to_decimal(credit_curr)

    # 1. Get account type and currency
    acct_data = db.execute(text("SELECT account_type, currency FROM accounts WHERE id = :id"), {"id": account_id}).fetchone()
    if not acct_data:
        return
        
    acct_type = acct_data.account_type
    acct_currency = acct_data.currency
    
    # 2. Calculate balance changes using Decimal
    if acct_type in ['asset', 'expense']:
        change_base = (debit_base - credit_base).quantize(_D2, ROUND_HALF_UP)
        change_curr = ((debit_curr - credit_curr).quantize(_D2, ROUND_HALF_UP)
                       if (currency and currency == acct_currency) else Decimal('0'))
    else:
        change_base = (credit_base - debit_base).quantize(_D2, ROUND_HALF_UP)
        change_curr = ((credit_curr - debit_curr).quantize(_D2, ROUND_HALF_UP)
                       if (currency and currency == acct_currency) else Decimal('0'))
        
    # 3. Always update base balance
    db.execute(text("""
        UPDATE accounts SET balance = balance + :change WHERE id = :id
    """), {"change": change_base, "id": account_id})
    
    # 4. Update foreign balance only if currency matches
    if acct_currency and change_curr != 0:
        db.execute(text("""
            UPDATE accounts SET balance_currency = balance_currency + :change WHERE id = :id
        """), {"change": change_curr, "id": account_id})

