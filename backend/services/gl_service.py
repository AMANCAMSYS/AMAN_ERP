import logging
from sqlalchemy import text
from fastapi import HTTPException
from datetime import datetime
from typing import List, Dict, Optional, Any

from utils.accounting import generate_sequential_number, update_account_balance

logger = logging.getLogger(__name__)

def create_journal_entry(
    db,
    company_id: str,
    date: str,
    description: str,
    lines: List[Dict[str, Any]],
    user_id: int,
    branch_id: Optional[int] = None,
    reference: Optional[str] = None,
    status: str = "posted",
    currency: Optional[str] = None,
    exchange_rate: float = 1.0,
    source: str = "Manual",
    source_id: Optional[int] = None,
) -> tuple[int, str]:
    """
    Centralized function to create a journal entry, validate it, insert lines, 
    and update account balances if posted.
    
    lines format:
        [
            {
                "account_id": int,
                "debit": float,
                "credit": float,
                "description": str (optional),
                "cost_center_id": int (optional),
                "currency": str (optional),
                "amount_currency": float (optional)
            }
        ]
    """
    # 1. Validation
    if not lines:
        raise HTTPException(status_code=400, detail="يجب إضافة سطر واحد على الأقل في القيد")

    total_debit = 0.0
    total_credit = 0.0

    for i, line in enumerate(lines):
        d = float(line.get("debit", 0))
        c = float(line.get("credit", 0))
        if d < 0 or c < 0:
            raise HTTPException(status_code=400, detail=f"السطر {i+1}: لا يمكن إدخال مبالغ سالبة")
        if d > 0 and c > 0:
            raise HTTPException(status_code=400, detail=f"السطر {i+1}: لا يمكن أن يكون مدين ودائن معاً في نفس السطر")
        total_debit += d
        total_credit += c

    if total_debit == 0 and total_credit == 0:
        raise HTTPException(status_code=400, detail="لا يمكن إنشاء قيد بمبالغ صفرية")

    if abs(total_debit - total_credit) > 0.01:
        raise HTTPException(status_code=400, detail="القيود غير موزونة (المدين لا يساوي الدائن)")

    if status not in ("draft", "posted"):
        status = "posted"

    # 1b. Closed Period Check
    if date and status == "posted":
        closed_period = db.execute(text("""
            SELECT 1 FROM fiscal_periods 
            WHERE :entry_date BETWEEN start_date AND end_date 
            AND is_closed = TRUE
            LIMIT 1
        """), {"entry_date": date}).fetchone()
        if closed_period:
            raise HTTPException(status_code=400, detail="لا يمكن ترحيل قيود في فترة محاسبية مغلقة")

    # 2. Header
    entry_number = generate_sequential_number(db, "JE", "journal_entries", "entry_number")
    
    # Get base currency
    if not currency:
        curr_row = db.execute(text("SELECT code FROM currencies WHERE is_base = TRUE LIMIT 1")).fetchone()
        if not curr_row:
            curr_row = db.execute(text("SELECT setting_value as code FROM company_settings WHERE setting_key = 'default_currency'")).fetchone()
        currency = curr_row[0] if curr_row else "SYP"

    # Insert header
    res = db.execute(text("""
        INSERT INTO journal_entries 
        (entry_number, entry_date, description, reference, status, branch_id, created_by, currency, exchange_rate, posted_at, source, source_id)
        VALUES 
        (:num, :date, :desc, :ref, :status, :branch_id, :user, :curr, :rate, :posted_at, :source, :s_id)
        RETURNING id
    """), {
        "num": entry_number,
        "date": date,
        "desc": description,
        "ref": reference,
        "status": status,
        "branch_id": branch_id,
        "user": user_id,
        "curr": currency,
        "rate": exchange_rate,
        "posted_at": datetime.now() if status == "posted" else None,
        "source": source,
        "s_id": source_id
    }).fetchone()
    
    journal_id = res[0]

    # 3. Lines
    for line in lines:
        input_debit = float(line.get("debit", 0))
        input_credit = float(line.get("credit", 0))
        
        line_rate = float(line.get("exchange_rate", exchange_rate))
        debit_base = input_debit * line_rate
        credit_base = input_credit * line_rate
        
        account_id = line["account_id"]
        line_currency = line.get("currency") or currency
        
        if line.get("amount_currency"):
            line_amount_currency = float(line["amount_currency"])
        else:
            line_amount_currency = input_debit + input_credit

        db.execute(text("""
            INSERT INTO journal_lines 
            (journal_entry_id, account_id, debit, credit, description, cost_center_id, amount_currency, currency)
            VALUES 
            (:jid, :aid, :deb, :cred, :desc, :cc_id, :amt_curr, :curr)
        """), {
            "jid": journal_id,
            "aid": account_id,
            "deb": debit_base,
            "cred": credit_base,
            "desc": line.get("description", description),
            "cc_id": line.get("cost_center_id"),
            "amt_curr": line_amount_currency,
            "curr": line_currency
        })
        
        if status == "posted":
            update_account_balance(
                db, 
                account_id=account_id, 
                debit_base=debit_base, 
                credit_base=credit_base, 
                debit_curr=input_debit, 
                credit_curr=input_credit, 
                currency=line_currency
            )

    return journal_id, entry_number
