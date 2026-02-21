
import logging
from sqlalchemy import text
from database import get_db_connection, get_system_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_company_db(company_id):
    logger.info(f"Migrating company database: {company_id}")
    db = get_db_connection(company_id)
    try:
        # 1. Project Documents
        logger.info("Checking/Creating project_documents table...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS project_documents (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                file_name VARCHAR(255) NOT NULL,
                file_url TEXT NOT NULL,
                file_type VARCHAR(50),
                uploaded_by INTEGER REFERENCES company_users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # 2. Notifications
        logger.info("Checking/Creating notifications table...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES company_users(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                message TEXT,
                link VARCHAR(255),
                is_read BOOLEAN DEFAULT FALSE,
                type VARCHAR(20) DEFAULT 'info',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # 3. Custom Reports
        logger.info("Checking/Creating custom_reports table...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS custom_reports (
                id SERIAL PRIMARY KEY,
                report_name VARCHAR(255) NOT NULL,
                description TEXT,
                config JSONB DEFAULT '{}',
                created_by INTEGER REFERENCES company_users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        db.commit()
        logger.info(f"✅ Migration successful for company: {company_id}")

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error migrating company {company_id}: {e}")
    finally:
        db.close()

def main():
    system_db = get_system_db()
    try:
        # Get all companies from existing databases (assuming convention or just applying to known ones)
        # For this environment, we might not have a master list of created company DBs in system_db easily validatable 
        # without querying pg_database, but let's assume we want to migrate the current user's DB.
        # Since we don't have the company ID context here directly, we'll try to find databases starting with "aman_"
        
        result = system_db.execute(text("SELECT datname FROM pg_database WHERE datname LIKE 'aman_%'"))
        databases = [row[0] for row in result]
        
        for db_name in databases:
            company_id = db_name.replace("aman_", "")
            migrate_company_db(company_id)
            
    except Exception as e:
        logger.error(f"System Error: {e}")
    finally:
        system_db.close()

if __name__ == "__main__":
    main()
