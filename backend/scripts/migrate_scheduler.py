import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

def migrate():
    print("🚀 Starting migration for Scheduled Reports...")
    
    # Connect to system DB to list company DBs
    sys_engine = create_engine(settings.DATABASE_URL, isolation_level="AUTOCOMMIT")
    with sys_engine.connect() as conn:
        # List all databases starting with aman_
        # Note: listing databases might require specific permissions or query on pg_database
        try:
            result = conn.execute(text("SELECT datname FROM pg_database WHERE datname LIKE 'aman_%'"))
            databases = [row[0] for row in result.fetchall()]
        except Exception as e:
            print(f"❌ Failed to list databases: {e}")
            return

    print(f"📦 Found {len(databases)} company databases: {databases}")
    
    sql = """
    CREATE TABLE IF NOT EXISTS scheduled_reports (
        id SERIAL PRIMARY KEY,
        report_type VARCHAR(50) NOT NULL,
        frequency VARCHAR(20) NOT NULL,
        recipients TEXT NOT NULL,
        format VARCHAR(10) DEFAULT 'pdf',
        branch_id INTEGER,
        next_run_at TIMESTAMP,
        last_run_at TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    for db_name in databases:
        print(f"🔄 Migrating {db_name}...")
        try:
            # Construct DB URL for this company
            # Assuming same credentials as system DB
            base_url = settings.DATABASE_URL.rsplit('/', 1)[0]
            company_db_url = f"{base_url}/{db_name}"
            
            engine = create_engine(company_db_url, isolation_level="AUTOCOMMIT")
            with engine.connect() as conn:
                conn.execute(text(sql))
                print(f"✅ Migrated {db_name}")
        except Exception as e:
            print(f"❌ Failed to migrate {db_name}: {e}")

    print("🏁 Migration complete.")

if __name__ == "__main__":
    migrate()
