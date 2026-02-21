import sys
import os
import logging

# Add parent directory to path to allow imports from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import create_company_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Target Company
COMPANY_ID = "be67ce39"

def main():
    logger.info(f"🛠️ Synchronizing schema for company: {COMPANY_ID}")
    
    try:
        # create_company_tables uses CREATE TABLE IF NOT EXISTS, 
        # so it's safe to run on an existing database to add any missing tables.
        success, msg = create_company_tables(COMPANY_ID)
        
        if success:
            logger.info(f"✅ Schema synchronized successfully for {COMPANY_ID}: {msg}")
        else:
            logger.error(f"❌ Failed to synchronize schema: {msg}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
