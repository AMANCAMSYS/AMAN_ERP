import sys
import os
import logging
from sqlalchemy import create_engine, text

# Add backend directory to path so config imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Direct connection to the master database to find all tenant company databases
engine_ddl = create_engine(
    settings.DATABASE_URL,
    isolation_level="AUTOCOMMIT"
)

def apply_trigger():
    logger.info("Applying DB balance trigger to all existing databases...")
    with engine_ddl.connect() as conn:
        databases = conn.execute(text(
            "SELECT datname FROM pg_database WHERE datname LIKE 'aman_%'"
        )).fetchall()
        
    for db_name, in databases:
        company_id = db_name.replace("aman_", "")
        logger.info(f"Applying to company {company_id}...")
        
        url = settings.get_company_database_url(company_id)
        company_engine = create_engine(url)
        
        try:
            with company_engine.connect() as conn:
                with conn.begin():
                    # Check for currently unbalanced entries to avoid trigger failure during constraint evaluation
                    # Wait, the constraint trigger only fires ON INSERT OR UPDATE
                    # It won't fail existing data unless they are updated. But it's good to be pure.
                    
                    conn.execute(text("""
                        CREATE OR REPLACE FUNCTION check_journal_balance() RETURNS TRIGGER AS $$
                        BEGIN
                            IF (SELECT ABS(SUM(debit) - SUM(credit)) FROM journal_lines
                                WHERE journal_entry_id = NEW.journal_entry_id) > 0.01 THEN
                                RAISE EXCEPTION 'Journal entry % is not balanced', NEW.journal_entry_id;
                            END IF;
                            RETURN NEW;
                        END;
                        $$ LANGUAGE plpgsql;
                    """))
                    
                    conn.execute(text("""
                        DO $$
                        BEGIN
                            IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_journal_balance') THEN
                                CREATE CONSTRAINT TRIGGER trg_journal_balance
                                AFTER INSERT OR UPDATE ON journal_lines
                                DEFERRABLE INITIALLY DEFERRED
                                FOR EACH ROW EXECUTE FUNCTION check_journal_balance();
                            END IF;
                        END
                        $$;
                    """))
                logger.info(f"✅ Trigger applied to {db_name}")
        except Exception as e:
            logger.error(f"❌ Failed on {db_name}: {e}")

if __name__ == "__main__":
    apply_trigger()
