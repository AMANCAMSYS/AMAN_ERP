"""
Migration: Add UNIQUE partial index on pos_sessions to prevent duplicate open sessions.
Fixes TOCTOU race condition — even if two requests pass the FOR UPDATE SKIP LOCKED check,
the UNIQUE constraint guarantees only one open session per user.

Run: python migrations/add_pos_session_unique_index.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine, get_all_company_ids


def migrate():
    """Apply UNIQUE partial index to all company databases."""
    company_ids = get_all_company_ids()
    print(f"🔄 Applying pos_sessions unique index to {len(company_ids)} company databases ...")

    for cid in company_ids:
        try:
            from database import get_company_engine
            eng = get_company_engine(cid)
            with eng.connect() as conn:
                # Check if table exists first
                exists = conn.execute(text(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'pos_sessions')"
                )).scalar()
                if not exists:
                    print(f"  ⏩ {cid}: pos_sessions table does not exist — skipping")
                    continue

                conn.execute(text("""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_pos_sessions_user_open
                    ON pos_sessions (user_id)
                    WHERE status = 'opened'
                """))
                conn.commit()
                print(f"  ✅ {cid}: index created")
        except Exception as e:
            print(f"  ❌ {cid}: {e}")

    print("✅ Migration complete")


if __name__ == "__main__":
    migrate()
