"""
AMAN ERP — Fiscal Period Lock
قفل الفترة المحاسبية — منع إدخال قيود في فترة مقفلة
"""

from fastapi import Depends, HTTPException
from sqlalchemy import text
from functools import wraps
from datetime import date, datetime
from database import get_db_connection
import logging

logger = logging.getLogger(__name__)


def check_fiscal_period_open(db, entry_date, raise_error=True):
    """
    Check if a fiscal period is open for the given date.
    Used as a utility function called from endpoints that create journal entries.

    Returns True if open, False if locked.
    Raises HTTPException(400) if locked and raise_error=True.
    """
    if isinstance(entry_date, str):
        entry_date = datetime.strptime(entry_date[:10], "%Y-%m-%d").date()

    try:
        # Check for fiscal period locks
        locked = db.execute(text("""
            SELECT id, period_name, locked_at, locked_by
            FROM fiscal_period_locks
            WHERE :entry_date BETWEEN period_start AND period_end
            AND is_locked = true
            FOR UPDATE
            LIMIT 1
        """), {"entry_date": entry_date}).fetchone()

        if locked:
            if raise_error:
                raise HTTPException(
                    400,
                    f"الفترة المحاسبية مقفلة: {locked.period_name}. "
                    f"تم القفل بتاريخ {locked.locked_at}. "
                    "يرجى التواصل مع المدير لفتح الفترة."
                )
            return False

        return True

    except HTTPException:
        raise
    except Exception as e:
        # If table doesn't exist yet, allow all
        logger.debug(f"Fiscal period check skipped: {e}")
        return True


def create_fiscal_lock_table(db):
    """Create the fiscal_period_locks table if it doesn't exist"""
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS fiscal_period_locks (
            id SERIAL PRIMARY KEY,
            period_name VARCHAR(100) NOT NULL,
            period_start DATE NOT NULL,
            period_end DATE NOT NULL,
            is_locked BOOLEAN DEFAULT FALSE,
            locked_at TIMESTAMPTZ,
            locked_by INTEGER,
            unlocked_at TIMESTAMPTZ,
            unlocked_by INTEGER,
            reason TEXT,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.commit()
