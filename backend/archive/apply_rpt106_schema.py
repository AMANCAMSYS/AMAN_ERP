"""
Migration: Apply RPT-106 schema changes
- Add report_name, report_config, last_status to scheduled_reports
- Create shared_reports table
Run once: python migrations/apply_rpt106_schema.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_all_company_ids, get_db_connection
from sqlalchemy import text

def run(company_id: str):
    db = get_db_connection(company_id)
    try:
        # 1. Add columns to scheduled_reports if missing
        db.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='scheduled_reports' AND column_name='report_name'
                ) THEN
                    ALTER TABLE scheduled_reports ADD COLUMN report_name VARCHAR(255);
                END IF;

                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='scheduled_reports' AND column_name='report_config'
                ) THEN
                    ALTER TABLE scheduled_reports ADD COLUMN report_config JSONB DEFAULT '{}';
                END IF;

                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='scheduled_reports' AND column_name='last_status'
                ) THEN
                    ALTER TABLE scheduled_reports ADD COLUMN last_status VARCHAR(20) DEFAULT 'pending';
                END IF;

                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='scheduled_reports' AND column_name='last_run_at'
                ) THEN
                    ALTER TABLE scheduled_reports ADD COLUMN last_run_at TIMESTAMPTZ;
                END IF;

                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='scheduled_reports' AND column_name='updated_at'
                ) THEN
                    ALTER TABLE scheduled_reports ADD COLUMN updated_at TIMESTAMPTZ;
                END IF;
            END $$;
        """))

        # 2. Create shared_reports table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS shared_reports (
                id SERIAL PRIMARY KEY,
                report_type VARCHAR(30) NOT NULL CHECK (report_type IN ('custom', 'scheduled')),
                report_id INTEGER NOT NULL,
                shared_by INTEGER REFERENCES company_users(id) ON DELETE SET NULL,
                shared_with INTEGER REFERENCES company_users(id) ON DELETE CASCADE,
                permission VARCHAR(20) DEFAULT 'view' CHECK (permission IN ('view', 'edit')),
                message TEXT,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(report_type, report_id, shared_with)
            );
        """))

        db.commit()
        print(f"✅ Company {company_id}: Migration applied")
    except Exception as e:
        db.rollback()
        print(f"❌ Company {company_id}: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    company_ids = get_all_company_ids()
    print(f"Applying RPT-106 migration to {len(company_ids)} companies...")
    for cid in company_ids:
        run(cid)
    print("Done.")
