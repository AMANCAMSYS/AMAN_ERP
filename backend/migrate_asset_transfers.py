#!/usr/bin/env python3
"""
Migration: Fix asset_transfers table schema for all existing companies.
Run: python3 migrate_asset_transfers.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text, create_engine
from config import settings

def get_all_company_ids():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id FROM system_companies WHERE status = 'active'")).fetchall()
        return [r[0] for r in rows]

def migrate_company(company_id: str):
    try:
        db_url = settings.get_company_database_url(company_id)
        engine = create_engine(db_url)

        with engine.begin() as conn:
            # Check if asset_transfers exists
            exists = conn.execute(text("""
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'asset_transfers'
            """)).fetchone()

            if not exists:
                print(f"  ⏭️  [{company_id}] asset_transfers table missing — will be created on next startup")
                return True

            # Get existing columns
            col_rows = conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'asset_transfers'
            """)).fetchall()
            col_names = {r[0] for r in col_rows}

            changes = 0

            if 'from_branch_id' not in col_names:
                conn.execute(text("ALTER TABLE asset_transfers ADD COLUMN from_branch_id INTEGER"))
                changes += 1

            if 'to_branch_id' not in col_names:
                conn.execute(text("ALTER TABLE asset_transfers ADD COLUMN to_branch_id INTEGER"))
                changes += 1

            if 'book_value_at_transfer' not in col_names:
                conn.execute(text("ALTER TABLE asset_transfers ADD COLUMN book_value_at_transfer NUMERIC(15,2) DEFAULT 0"))
                changes += 1

            if 'created_by' not in col_names:
                conn.execute(text("ALTER TABLE asset_transfers ADD COLUMN created_by INTEGER"))
                changes += 1

            if 'notes' not in col_names:
                conn.execute(text("ALTER TABLE asset_transfers ADD COLUMN notes TEXT"))
                changes += 1

            # Set default on transfer_date
            conn.execute(text("ALTER TABLE asset_transfers ALTER COLUMN transfer_date SET DEFAULT CURRENT_DATE"))

            # Add indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_asset_transfers_asset ON asset_transfers(asset_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_asset_transfers_status ON asset_transfers(status)"))

            if changes > 0:
                print(f"  ✅ [{company_id}] Added {changes} column(s) to asset_transfers")
            else:
                print(f"  ✅ [{company_id}] asset_transfers already up to date")

        # Migrate asset_revaluations if needed
        with engine.begin() as conn:
            reval_exists = conn.execute(text("""
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'asset_revaluations'
            """)).fetchone()

            if reval_exists:
                rcols = conn.execute(text("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'asset_revaluations'
                """)).fetchall()
                rcol_names = {r[0] for r in rcols}

                rchanges = 0
                if 'revaluation_date' not in rcol_names:
                    conn.execute(text("ALTER TABLE asset_revaluations ADD COLUMN revaluation_date DATE DEFAULT CURRENT_DATE"))
                    rchanges += 1
                if 'difference' not in rcol_names:
                    conn.execute(text("ALTER TABLE asset_revaluations ADD COLUMN difference NUMERIC(15,2) DEFAULT 0"))
                    rchanges += 1
                if rchanges:
                    print(f"  ✅ [{company_id}] Added {rchanges} column(s) to asset_revaluations")

        return True

    except Exception as e:
        print(f"  ❌ [{company_id}] Error: {e}")
        return False


def main():
    print("🔧 AMAN ERP — Asset Transfers Migration")
    print("=" * 50)

    try:
        company_ids = get_all_company_ids()
    except Exception as e:
        print(f"❌ Cannot fetch company list: {e}")
        sys.exit(1)

    if not company_ids:
        print("ℹ️  No active companies found.")
        return

    print(f"📋 Found {len(company_ids)} active company/companies: {company_ids}")
    print()

    ok = sum(migrate_company(cid) for cid in company_ids)
    print()
    print(f"{'✅' if ok == len(company_ids) else '⚠️ '} Migration complete: {ok}/{len(company_ids)} succeeded.")


if __name__ == "__main__":
    main()
