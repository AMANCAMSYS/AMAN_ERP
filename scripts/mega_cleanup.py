
import psycopg2
from psycopg2 import sql

DB_USER = "aman"
DB_PASS = "sword123!@#"
DB_HOST = "localhost"

def get_aman_dbs():
    conn = psycopg2.connect(dbname="postgres", user=DB_USER, password=DB_PASS, host=DB_HOST)
    cur = conn.cursor()
    cur.execute("SELECT datname FROM pg_database WHERE datname LIKE 'aman_%'")
    dbs = [row[0] for row in cur.fetchall()]
    conn.close()
    return dbs

def clean_db(db_name):
    print(f"Checking {db_name}...")
    try:
        conn = psycopg2.connect(dbname=db_name, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = conn.cursor()
        
        # Check if target customers exist
        cur.execute("SELECT count(*) FROM parties WHERE is_customer = TRUE OR party_type = 'customer'")
        count = cur.fetchone()[0]
        
        if count == 0:
            print(f"  - No customers found in {db_name}")
            conn.close()
            return

        print(f"  - Found {count} customers in {db_name}. Cleaning...")
        
        # List tables with foreign keys to parties
        # This is a bit brute force but effective for cleanup
        tables = [
            'sales_return_lines', 'sales_returns',
            'sales_order_lines', 'sales_orders',
            'sales_quotation_lines', 'sales_quotations',
            'invoice_lines', 'invoices',
            'payment_allocations', 'payment_vouchers',
            'party_transactions',
            'journal_entries', # sometimes linked
        ]
        
        for table in tables:
            try:
                # Check if table exists
                cur.execute(f"SELECT to_regclass('public.{table}')")
                if cur.fetchone()[0]:
                    print(f"    - Cleaning {table}...")
                    # Build delete query based on table strcuture - simplified assumption
                    if table in ['invoices', 'sales_orders', 'sales_quotations', 'sales_returns', 'payment_vouchers', 'party_transactions']:
                        cur.execute(f"DELETE FROM {table} WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE OR party_type = 'customer')")
                    elif table.endswith('_lines'):
                        parent = table.replace('_lines', 's') # e.g. invoice_lines -> invoices
                        if parent == 'sales_return_lines': parent = 'sales_returns'
                        if parent == 'sales_order_lines': parent = 'sales_orders'
                        if parent == 'sales_quotation_lines': parent = 'sales_quotations'
                        
                        # Sub-query delete
                        query = f"DELETE FROM {table} WHERE {parent[:-1]}_id IN (SELECT id FROM {parent} WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE OR party_type = 'customer'))"
                        # Adjust for specific naming if needed
                        if table == 'invoice_lines': query = f"DELETE FROM invoice_lines WHERE invoice_id IN (SELECT id FROM invoices WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE OR party_type = 'customer'))"
                        
                        try:
                            cur.execute(query)
                        except Exception as e:
                            print(f"      - Error cleaning {table}: {e}")
            except Exception as e:
                print(f"    - Error checking/cleaning {table}: {e}")
                conn.rollback()

        # Finally delete parties
        print("    - Deleting parties...")
        cur.execute("DELETE FROM parties WHERE is_customer = TRUE OR party_type = 'customer'")
        
        conn.commit()
        print(f"  - Successfully cleaned {db_name}")
        conn.close()
        
    except Exception as e:
        print(f"  - Error in {db_name}: {e}")

if __name__ == "__main__":
    dbs = get_aman_dbs()
    for db in dbs:
        clean_db(db)
