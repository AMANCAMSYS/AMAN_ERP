import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.database import _get_engine
from sqlalchemy import text

COMPANY_ID = '39a597c9'

def run_migration():
    engine = _get_engine(COMPANY_ID)
    with engine.begin() as conn:
        print(f"Migrating {COMPANY_ID}...")
        # customer_groups
        try: conn.execute(text("ALTER TABLE customer_groups ADD COLUMN IF NOT EXISTS effect_type VARCHAR(20) DEFAULT 'discount'"))
        except Exception as e: print(e)
        try: conn.execute(text("ALTER TABLE customer_groups ADD COLUMN IF NOT EXISTS application_scope VARCHAR(20) DEFAULT 'total'"))
        except Exception as e: print(e)
        
        # supplier_groups
        try: conn.execute(text("ALTER TABLE supplier_groups ADD COLUMN IF NOT EXISTS effect_type VARCHAR(20) DEFAULT 'discount'"))
        except Exception as e: print(e)
        try: conn.execute(text("ALTER TABLE supplier_groups ADD COLUMN IF NOT EXISTS application_scope VARCHAR(20) DEFAULT 'total'"))
        except Exception as e: print(e)

        # party_groups
        try: conn.execute(text("ALTER TABLE party_groups ADD COLUMN IF NOT EXISTS effect_type VARCHAR(20) DEFAULT 'discount'"))
        except Exception as e: print(e)
        try: conn.execute(text("ALTER TABLE party_groups ADD COLUMN IF NOT EXISTS application_scope VARCHAR(20) DEFAULT 'total'"))
        except Exception as e: print(e)

        # invoices
        try: conn.execute(text("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS effect_type VARCHAR(20) DEFAULT 'discount'"))
        except Exception as e: print(e)
        try: conn.execute(text("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS effect_percentage DECIMAL(5, 2) DEFAULT 0"))
        except Exception as e: print(e)
        try: conn.execute(text("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS markup_amount DECIMAL(18, 4) DEFAULT 0"))
        except Exception as e: print(e)

        # invoice_lines
        try: conn.execute(text("ALTER TABLE invoice_lines ADD COLUMN IF NOT EXISTS markup DECIMAL(18, 4) DEFAULT 0"))
        except Exception as e: print(e)

if __name__ == "__main__":
    run_migration()
