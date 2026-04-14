#!/usr/bin/env python3
"""
Migration: Add delivery tracking columns to notifications table.

T003: Add delivery_status, retry_count, last_retry_at, delivery_channel columns
      and retry index for the notification retry scheduler job.

Run:
    python backend/migrations/add_notification_delivery_columns.py
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

    print(f"Applying notification delivery columns migration to {len(companies)} company databases...")
    ok = 0
    failed = 0

    for row in companies:
        company_id = row[0]
        company_name = row[1] if len(row) > 1 else str(company_id)
        db = None
        try:
            db = get_db_connection(company_id)

            # T003: Add delivery tracking columns
            db.execute(text(
                "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS delivery_status VARCHAR DEFAULT 'pending'"
            ))
            db.execute(text(
                "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0"
            ))
            db.execute(text(
                "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS last_retry_at TIMESTAMPTZ"
            ))
            db.execute(text(
                "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS delivery_channel VARCHAR"
            ))

            # Index for retry job (find pending retries efficiently)
            db.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_notifications_retry "
                "ON notifications (last_retry_at) "
                "WHERE delivery_status = 'failed' AND retry_count < 3"
            ))

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
