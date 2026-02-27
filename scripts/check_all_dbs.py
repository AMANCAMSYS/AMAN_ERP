
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

DB_PASS = "sword123!@#"
DB_USER = "aman"
DB_HOST = "localhost"

def check_databases():
    try:
        conn = psycopg2.connect(dbname="postgres", user=DB_USER, password=DB_PASS, host=DB_HOST)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        cur.execute("SELECT datname FROM pg_database WHERE datname LIKE 'aman_%';")
        dbs = cur.fetchall()
        
        print(f"Found {len(dbs)} aman databases:")
        for db in dbs:
            db_name = db[0]
            print(f"- {db_name}")
            check_customers(db_name)
            
        conn.close()
    except Exception as e:
        print(f"Main Error: {e}")

def check_customers(db_name):
    try:
        conn = psycopg2.connect(dbname=db_name, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = conn.cursor()
        
        cur.execute("SELECT count(*) FROM parties WHERE is_customer = TRUE OR party_type = 'customer';")
        count = cur.fetchone()[0]
        print(f"  > Customers count in {db_name}: {count}")
        
        if count > 0:
             cur.execute("SELECT id, name, status FROM parties WHERE is_customer = TRUE OR party_type = 'customer' LIMIT 5;")
             rows = cur.fetchall()
             for r in rows:
                 print(f"    - ID: {r[0]}, Name: {r[1]}, Status: {r[2]}")

        conn.close()
    except Exception as e:
        # print(f"  > Error checking {db_name}: {e}")
        pass

if __name__ == "__main__":
    check_databases()
