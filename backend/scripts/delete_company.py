import sys
import os
import argparse
import logging
from sqlalchemy import text

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_system_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("delete_company")

def delete_company(company_id: str, force: bool = False):
    """
    Safely delete a company:
    1. Terminate connections to the company database.
    2. Drop the company database.
    3. Drop the company PostgreSQL role.
    4. Remove from system_companies table.
    """
    db_name = f"aman_{company_id}"
    role_name = f"company_{company_id}"
    
    logger.info(f"🚀 Starting deletion for company ID: {company_id}")
    
    if not force:
        confirm = input(f"⚠️  ARE YOU SURE? This will permanently delete database '{db_name}' and all associated data. Type '{company_id}' to confirm: ")
        if confirm != company_id:
            logger.info("❌ Aborted.")
            return False

    db = get_system_db()
    try:
        # 1. Terminate active connections
        logger.info(f"🔌 Terminating active connections to {db_name}...")
        db.execute(text(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{db_name}'
            AND pid <> pg_backend_pid();
        """))
        db.commit()

        # 2. Drop Database
        logger.info(f"🗑️  Dropping database {db_name}...")
        db.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))
        db.commit()

        # 3. Drop Role
        logger.info(f"👤 Dropping role {role_name}...")
        try:
            # Reassign objects owned by the role before dropping
            db.execute(text(f'REASSIGN OWNED BY "{role_name}" TO CURRENT_USER'))
            db.execute(text(f'DROP OWNED BY "{role_name}"'))
            db.execute(text(f'DROP ROLE IF EXISTS "{role_name}"'))
            db.commit()
        except Exception as e:
            logger.warning(f"  ⚠️  Could not drop role {role_name}: {e}")
            db.rollback()

        # 4. Remove from system_companies
        logger.info("📝 Removing entry from system_companies...")
        db.execute(text("DELETE FROM system_companies WHERE id = :id"), {"id": company_id})
        db.commit()

        logger.info(f"✅ Company {company_id} deleted successfully.")
        return True

    except Exception as e:
        logger.error(f"❌ Error during deletion: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete a company and its database.")
    parser.add_argument("company_id", help="The ID of the company to delete.")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt.")
    
    args = parser.parse_args()
    
    if args.company_id == "all_unregistered":
        # Special logic to cleanup databases that exist but are not in system_companies
        db = get_system_db()
        try:
            # Get all aman_ databases
            all_dbs = db.execute(text("SELECT datname FROM pg_database WHERE datname LIKE 'aman_%'")).fetchall()
            registered_dbs = db.execute(text("SELECT database_name FROM system_companies")).fetchall()
            registered_db_names = {r[0] for r in registered_dbs}
            
            for (dbname,) in all_dbs:
                if dbname not in registered_db_names:
                    cid = dbname.replace("aman_", "")
                    logger.info(f"🔍 Found unregistered database: {dbname}")
                    delete_company(cid, force=args.force)
        finally:
            db.close()
    else:
        delete_company(args.company_id, force=args.force)
