#!/usr/bin/env python3
"""
ترحيل: إضافة أعمدة advanced_workflow إلى approval_requests لجميع الشركات
الأعمدة: action_date, action_notes, current_approver_id, escalated_to, escalated_at
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_system_db, get_db_connection
from sqlalchemy import text

MIGRATION_SQL = """
ALTER TABLE approval_requests ADD COLUMN IF NOT EXISTS action_date TIMESTAMPTZ;
ALTER TABLE approval_requests ADD COLUMN IF NOT EXISTS action_notes TEXT;
ALTER TABLE approval_requests ADD COLUMN IF NOT EXISTS current_approver_id INTEGER;
ALTER TABLE approval_requests ADD COLUMN IF NOT EXISTS escalated_to INTEGER;
ALTER TABLE approval_requests ADD COLUMN IF NOT EXISTS escalated_at TIMESTAMPTZ;
"""

def main():
    print("🔍 جلب قائمة الشركات...")
    sys_db = get_system_db()
    try:
        companies = sys_db.execute(text("SELECT id, company_name FROM system_companies ORDER BY created_at")).fetchall()
    finally:
        sys_db.close()

    print(f"📋 عدد الشركات: {len(companies)}")

    success_count = 0
    fail_count = 0

    for company in companies:
        company_id = company[0]
        company_name = company[1] if len(company) > 1 else company_id
        try:
            db = get_db_connection(company_id)
            try:
                for stmt in MIGRATION_SQL.strip().split(";"):
                    stmt = stmt.strip()
                    if stmt:
                        db.execute(text(stmt))
                db.commit()
                print(f"  ✅ {company_name} ({company_id})")
                success_count += 1
            finally:
                db.close()
        except Exception as e:
            print(f"  ❌ {company_name} ({company_id}): {e}")
            fail_count += 1

    print(f"\n{'='*40}")
    print(f"✅ نجح: {success_count} شركة")
    print(f"❌ فشل: {fail_count} شركة")

if __name__ == "__main__":
    main()
