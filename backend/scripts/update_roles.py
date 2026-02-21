import sys
import os
import json
import logging

# Add parent directory to path to allow imports from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_connection
from sqlalchemy import text
from routers.roles import DEFAULT_ROLES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Target Company
COMPANY_ID = "be67ce39"

def main():
    logger.info(f"🔄 Updating roles and permissions for company: {COMPANY_ID}")
    
    db = get_db_connection(COMPANY_ID)
    try:
        for role_name, perms in DEFAULT_ROLES.items():
            # Get existing record
            existing = db.execute(text("SELECT id, permissions FROM roles WHERE role_name = :n"), {"n": role_name}).fetchone()
            
            if existing:
                # Merge permissions
                existing_perms = set(existing.permissions or [])
                if "*" in existing_perms or "*" in perms:
                    merged = ["*"]
                else:
                    new_perms = set(perms)
                    merged = list(existing_perms.union(new_perms))
                
                logger.info(f"Updating {role_name}: {len(existing_perms)} -> {len(merged)} permissions")
                
                db.execute(text("""
                    UPDATE roles SET permissions = :p WHERE id = :id
                """), {"p": json.dumps(merged), "id": existing.id})
            else:
                logger.warning(f"Role '{role_name}' does not exist in DB, skipping.")
        
        db.commit()
        logger.info(f"✅ All default roles updated for {COMPANY_ID}")
        
    except Exception as e:
        logger.error(f"❌ Failed to update roles: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
