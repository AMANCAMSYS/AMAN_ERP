import sys
import os
import logging

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_connection
from scripts.seed_data import seed_branches, seed_accounts, seed_parties, seed_journal_entries
import scripts.seed_data as sd

# Override defaults for faster seeding of target company
sd.NUM_JOURNAL_ENTRIES = 1000
sd.NUM_PARTIES = 100
sd.NUM_ACCOUNTS = 100
sd.NUM_PRODUCTS = 50
sd.NUM_BRANCHES = 3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Target Company
COMPANY_ID = "be67ce39"

def main():
    logger.info(f"🚀 Seeding data for company: {COMPANY_ID}")
    
    try:
        with get_db_connection(COMPANY_ID) as conn:
            # Seed basic entities
            seed_branches(conn)
            seed_accounts(conn)
            seed_parties(conn)
            # Seed transactions
            seed_journal_entries(conn)
            
            conn.commit()
            logger.info(f"✨ Successfully seeded data for {COMPANY_ID}")
    except Exception as e:
        logger.error(f"❌ Failed to seed data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
