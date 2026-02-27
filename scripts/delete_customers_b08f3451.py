
import psycopg2
import sys

DB_NAME = "aman_b08f3451"
DB_USER = "aman"
DB_PASS = "sword123!@#"
DB_HOST = "localhost"

def delete_customers():
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = conn.cursor()
        
        # Check current customers
        cur.execute("SELECT count(*) FROM parties WHERE is_customer = TRUE OR party_type = 'customer';")
        count = cur.fetchone()[0]
        print(f"Found {count} customers to delete.")

        if count == 0:
            print("No customers found.")
            return

        # Delete related records first to avoid FK constraints if not cascading
        # Invoices
        cur.execute("DELETE FROM invoice_lines WHERE invoice_id IN (SELECT id FROM invoices WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE));")
        cur.execute("DELETE FROM invoices WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE);")
        
        # Sales Orders
        cur.execute("DELETE FROM sales_order_lines WHERE sales_order_id IN (SELECT id FROM sales_orders WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE));")
        cur.execute("DELETE FROM sales_orders WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE);")
        
        # Quotations
        cur.execute("DELETE FROM sales_quotation_lines WHERE quotation_id IN (SELECT id FROM sales_quotations WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE));")
        cur.execute("DELETE FROM sales_quotations WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE);")
        
        # Vouchers
        cur.execute("DELETE FROM payment_allocations WHERE payment_id IN (SELECT id FROM payment_vouchers WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE));")
        cur.execute("DELETE FROM payment_vouchers WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE);")

        # Returns
        cur.execute("DELETE FROM sales_return_lines WHERE return_id IN (SELECT id FROM sales_returns WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE));")
        cur.execute("DELETE FROM sales_returns WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE);")

        # Finally Delete Customers
        cur.execute("DELETE FROM parties WHERE is_customer = TRUE OR party_type = 'customer';")
        
        conn.commit()
        print("Successfully deleted all customers and related records.")
        
    except psycopg2.OperationalError as e:
        print(f"Could not connect to database {DB_NAME}: {e}")
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    delete_customers()
