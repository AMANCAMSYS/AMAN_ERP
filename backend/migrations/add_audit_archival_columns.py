#!/usr/bin/env python3
"""
Migration: Add archival columns and partial indexes to audit_logs table.

T001: Add is_archived BOOLEAN DEFAULT FALSE and archived_at TIMESTAMPTZ columns.
T002: Add partial indexes for live and archival queries.

Run:
    python backend/migrations/add_audit_archival_columns.py
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

    print(f"Applying audit archival migration to {len(companies)} company databases...")
    ok = 0
    failed = 0

    for row in companies:
        company_id = row[0]
        company_name = row[1] if len(row) > 1 else str(company_id)
        db = None
        try:
            db = get_db_connection(company_id)

            # T001: Add archival columns
            db.execute(text(
                "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE"
            ))
            db.execute(text(
                "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ"
            ))

            # T002: Add partial indexes for live and archival queries
            db.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_live "
                "ON audit_logs (created_at DESC) WHERE NOT is_archived"
            ))
            db.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_archival "
                "ON audit_logs (created_at) WHERE is_archived = TRUE"
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
