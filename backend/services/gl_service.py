import logging
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from datetime import datetime
from typing import List, Dict, Optional, Any
from decimal import Decimal, ROUND_HALF_UP

from utils.accounting import generate_sequential_number, update_account_balance
from utils.audit import log_activity

logger = logging.getLogger(__name__)
_D2 = Decimal("0.01")


def _dec(v: Any) -> Decimal:
    return Decimal(str(v or 0))

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
    username: Optional[str] = None,
    idempotency_key: Optional[str] = None,
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
    # 0. Idempotency guard — if caller supplied a key, return existing JE
    if idempotency_key:
        existing = db.execute(text("""
            SELECT id, entry_number FROM journal_entries
            WHERE idempotency_key = :key
            LIMIT 1
        """), {"key": idempotency_key}).fetchone()
        if existing:
            logger.info("Idempotency hit: key=%s → JE %s", idempotency_key, existing[1])
            return existing[0], existing[1]

    # 1. Validation
    if not lines:
        raise HTTPException(status_code=400, detail="يجب إضافة سطر واحد على الأقل في القيد")

    total_debit = Decimal("0")
    total_credit = Decimal("0")

    for i, line in enumerate(lines):
        d = _dec(line.get("debit", 0)).quantize(_D2, ROUND_HALF_UP)
        c = _dec(line.get("credit", 0)).quantize(_D2, ROUND_HALF_UP)
        if d < 0 or c < 0:
            raise HTTPException(status_code=400, detail=f"السطر {i+1}: لا يمكن إدخال مبالغ سالبة")
        if d > 0 and c > 0:
            raise HTTPException(status_code=400, detail=f"السطر {i+1}: لا يمكن أن يكون مدين ودائن معاً في نفس السطر")
        total_debit += d
        total_credit += c

    if total_debit == 0 and total_credit == 0:
        raise HTTPException(status_code=400, detail="لا يمكن إنشاء قيد بمبالغ صفرية")

    if abs(total_debit - total_credit) > _D2:
        raise HTTPException(status_code=400, detail="القيود غير موزونة (المدين لا يساوي الدائن)")

    if status not in ("draft", "posted"):
        status = "posted"

    # 1b. Source-level duplicate guard (prevents double-posting from same module action)
    if source and source != "Manual" and source_id is not None:
        dup = db.execute(text("""
            SELECT id, entry_number FROM journal_entries
            WHERE source = :src AND source_id = :sid AND entry_date = :dt
            LIMIT 1
        """), {"src": source, "sid": source_id, "dt": date}).fetchone()
        if dup:
            logger.warning("Duplicate source posting blocked: source=%s source_id=%s date=%s → existing JE %s",
                           source, source_id, date, dup[1])
            return dup[0], dup[1]

    # 1c. Closed Period Check
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
    try:
        res = db.execute(text("""
            INSERT INTO journal_entries 
            (entry_number, entry_date, description, reference, status, branch_id, created_by, currency, exchange_rate, posted_at, source, source_id, idempotency_key)
            VALUES 
            (:num, :date, :desc, :ref, :status, :branch_id, :user, :curr, :rate, :posted_at, :source, :s_id, :idem_key)
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
            "rate": _dec(exchange_rate).quantize(Decimal("0.000001"), ROUND_HALF_UP),
            "posted_at": datetime.now() if status == "posted" else None,
            "source": source,
            "s_id": source_id,
            "idem_key": idempotency_key
        }).fetchone()
    except IntegrityError as e:
        # Race: a concurrent request landed the same idempotency_key or source triplet.
        db.rollback()
        if idempotency_key:
            row = db.execute(text(
                "SELECT id, entry_number FROM journal_entries WHERE idempotency_key = :k LIMIT 1"
            ), {"k": idempotency_key}).fetchone()
            if row:
                logger.info("Idempotency race resolved: key=%s → JE %s", idempotency_key, row[1])
                return row[0], row[1]
        if source and source != "Manual" and source_id is not None:
            row = db.execute(text("""
                SELECT id, entry_number FROM journal_entries
                WHERE source = :s AND source_id = :sid AND entry_date = :d LIMIT 1
            """), {"s": source, "sid": source_id, "d": date}).fetchone()
            if row:
                logger.info("Source-duplicate race resolved: %s/%s → JE %s", source, source_id, row[1])
                return row[0], row[1]
        logger.exception("IntegrityError creating journal entry: %s", e)
        raise HTTPException(status_code=409, detail="تعذر إنشاء القيد — تعارض في البيانات")

    journal_id = res[0]

    # 3. Lines
    for line in lines:
        input_debit = _dec(line.get("debit", 0)).quantize(_D2, ROUND_HALF_UP)
        input_credit = _dec(line.get("credit", 0)).quantize(_D2, ROUND_HALF_UP)
        
        line_rate = _dec(line.get("exchange_rate", exchange_rate))
        if line_rate <= 0:
            raise HTTPException(status_code=400, detail="سعر الصرف يجب أن يكون أكبر من صفر")
        debit_base = (input_debit * line_rate).quantize(_D2, ROUND_HALF_UP)
        credit_base = (input_credit * line_rate).quantize(_D2, ROUND_HALF_UP)
        
        account_id = line["account_id"]
        line_currency = line.get("currency") or currency
        
        if line.get("amount_currency"):
            line_amount_currency = _dec(line["amount_currency"]).quantize(_D2, ROUND_HALF_UP)
        else:
            line_amount_currency = (input_debit + input_credit).quantize(_D2, ROUND_HALF_UP)

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

    # Audit logging — internal to GL service for 100% coverage (FR-017)
    try:
        log_activity(
            db,
            user_id=user_id,
            username=username or "system",
            action="create_journal_entry",
            resource_type="journal_entry",
            resource_id=str(journal_id),
            details={"entry_number": entry_number, "source": source, "lines": len(lines), "status": status}
        )
    except Exception:
        logger.warning("Failed to log audit activity for JE %s", entry_number)

    return journal_id, entry_number
