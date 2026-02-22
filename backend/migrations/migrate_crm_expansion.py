"""
Migration: Create CRM expansion tables (marketing_campaigns, knowledge_base)
Also creates tax_calendar for TAX-002
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import get_db_connection

TABLES_SQL = """
-- CRM-003: Marketing Campaigns 
CREATE TABLE IF NOT EXISTS marketing_campaigns (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    campaign_type VARCHAR(50) DEFAULT 'email' CHECK (campaign_type IN ('email', 'sms', 'social', 'event')),
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'paused', 'completed')),
    start_date DATE,
    end_date DATE,
    budget NUMERIC(15,2) DEFAULT 0,
    target_audience TEXT,
    description TEXT,
    sent_count INT DEFAULT 0,
    open_count INT DEFAULT 0,
    click_count INT DEFAULT 0,
    conversion_count INT DEFAULT 0,
    created_by INT,
    branch_id INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- CRM-005: Knowledge Base
CREATE TABLE IF NOT EXISTS knowledge_base (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    category VARCHAR(50) DEFAULT 'general' CHECK (category IN ('faq', 'guide', 'policy', 'general')),
    content TEXT NOT NULL,
    tags VARCHAR(500),
    is_published BOOLEAN DEFAULT FALSE,
    views INT DEFAULT 0,
    created_by INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- TAX-002: Tax Filing Calendar
CREATE TABLE IF NOT EXISTS tax_calendar (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    tax_type VARCHAR(50) NOT NULL,
    due_date DATE NOT NULL,
    reminder_days INT[] DEFAULT '{7,3,1}',
    status VARCHAR(50) DEFAULT 'upcoming' CHECK (status IN ('upcoming', 'submitted', 'overdue')),
    notes TEXT,
    branch_id INT,
    created_by INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
"""


def migrate(company_id: str):
    db = get_db_connection(company_id)
    try:
        db.execute(text(TABLES_SQL))
        db.commit()
        print(f"  ✅ Tables created for {company_id}")
    except Exception as e:
        db.rollback()
        print(f"  ❌ Error for {company_id}: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    from database import engine
    with engine.connect() as conn:
        dbs = conn.execute(text("SELECT datname FROM pg_database WHERE datname LIKE 'aman_%'")).fetchall()
    
    for row in dbs:
        dbname = row[0]
        company_id = dbname.replace("aman_", "")
        print(f"Migrating {dbname}...")
        migrate(company_id)
    
    print("\nDone!")
