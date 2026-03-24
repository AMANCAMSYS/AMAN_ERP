#!/usr/bin/env python3
"""
Migration: add payment_method column to invoices table (if missing) for all companies.

Run:
    python backend/migrations/add_invoices_payment_method_column.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import get_db_connection, get_system_db


def migrate() -> None:
    sys_db = get_system_db()
    try:
        companies = sys_db.execute(
            text("SELECT id, company_name FROM system_companies ORDER BY created_at")
        ).fetchall()
    finally:
        sys_db.close()

    print(f"Applying migration to {len(companies)} company databases...")
    ok = 0
    failed = 0

    for row in companies:
        company_id = row[0]
        company_name = row[1] if len(row) > 1 else str(company_id)
        db = None
        try:
            db = get_db_connection(company_id)
            db.execute(
                text(
                    """
                    ALTER TABLE invoices
                    ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50)
                    """
                )
            )
            db.commit()
            ok += 1
            print(f"  OK: {company_name} ({company_id})")
        except Exception as exc:
            failed += 1
            if db is not None:
                db.rollback()
            print(f"  FAIL: {company_name} ({company_id}) -> {exc}")
        finally:
            if db is not None:
                db.close()

    print(f"Done. Success: {ok}, Failed: {failed}")


if __name__ == "__main__":
    migrate()
