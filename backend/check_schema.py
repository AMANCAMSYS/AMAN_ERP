from sqlalchemy import text, create_engine
from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_employees_schema():
    company_id = "be67ce39"
    try:
        company_url = settings.get_company_database_url(company_id)
        engine = create_engine(company_url)
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'employees';
            """)).fetchall()
            for row in result:
                print(f"{row[0]}: {row[1]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_employees_schema()
