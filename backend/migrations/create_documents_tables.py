"""Migration: Create documents and document_versions tables for services document management."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import get_db_connection
from sqlalchemy import text

def run(company_id: str):
    db = get_db_connection(company_id)
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                category VARCHAR(50) DEFAULT 'general',
                file_name VARCHAR(500),
                file_path VARCHAR(500),
                file_size INTEGER,
                mime_type VARCHAR(200),
                tags TEXT,
                access_level VARCHAR(50) DEFAULT 'company',
                related_module VARCHAR(50),
                related_id INTEGER,
                current_version INTEGER DEFAULT 1,
                created_by INTEGER REFERENCES company_users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS document_versions (
                id SERIAL PRIMARY KEY,
                document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                version_number INTEGER NOT NULL,
                file_name VARCHAR(500),
                file_path VARCHAR(500),
                file_size INTEGER,
                change_notes TEXT,
                uploaded_by INTEGER REFERENCES company_users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        db.commit()
        r = db.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_name IN ('documents','document_versions') ORDER BY table_name"
        )).fetchall()
        print(f"[{company_id}] Tables ready: {[x[0] for x in r]}")
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    cid = sys.argv[1] if len(sys.argv) > 1 else "39a597c9"
    run(cid)
