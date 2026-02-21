from sqlalchemy import text
from typing import Optional


def generate_sequential_number(db, prefix: str, table: str, column: str) -> str:
    """
    Generate a sequential document number.
    Example: prefix='SINV-2026' → 'SINV-2026-00001'
    
    Uses MAX extraction of trailing digits from existing numbers to determine next.
    table and column are developer-defined constants (not user input).
    """
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
    try:
        result = db.execute(
            text("SELECT setting_value FROM company_settings WHERE setting_key = :key"),
            {"key": mapping_key}
        ).fetchone()
        
        if result and result[0]:
            return int(result[0])
        return None
    except Exception:
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
    Checks currencies table first, then company_settings, falls back to 'SAR'.
    """
    row = db.execute(text("SELECT code FROM currencies WHERE is_base = TRUE LIMIT 1")).fetchone()
    if not row:
        row = db.execute(text("SELECT setting_value AS code FROM company_settings WHERE setting_key = 'default_currency'")).fetchone()
    return row[0] if row else "SAR"

def update_account_balance(db, account_id: int, debit_base: float, credit_base: float, debit_curr: float = 0, credit_curr: float = 0, currency: str = None):
    """
    Updates both the base balance and the foreign currency balance of an account.
    """
    # 1. Get account type and currency
    acct_data = db.execute(text("SELECT account_type, currency FROM accounts WHERE id = :id"), {"id": account_id}).fetchone()
    if not acct_data:
        return
        
    acct_type = acct_data.account_type
    acct_currency = acct_data.currency
    
    # 2. Calculate balance changes
    if acct_type in ['asset', 'expense']:
        change_base = debit_base - credit_base
        change_curr = (debit_curr - credit_curr) if (currency and currency == acct_currency) else 0
    else:
        change_base = credit_base - debit_base
        change_curr = (credit_curr - debit_curr) if (currency and currency == acct_currency) else 0
        
    # 3. Always update base balance
    db.execute(text("""
        UPDATE accounts SET balance = balance + :change WHERE id = :id
    """), {"change": change_base, "id": account_id})
    
    # 4. Update foreign balance only if currency matches
    if acct_currency and change_curr != 0:
        db.execute(text("""
            UPDATE accounts SET balance_currency = balance_currency + :change WHERE id = :id
        """), {"change": change_curr, "id": account_id})
