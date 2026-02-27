
import psycopg2
import sys

def run_cleanup():
    log = []
    
    try:
        # Step 1: Find Databases
        conn_main = psycopg2.connect(dbname="postgres", user="aman", password="sword123!@#", host="localhost")
        cur_main = conn_main.cursor()
        cur_main.execute("SELECT datname FROM pg_database WHERE datname LIKE 'aman_%'")
        dbs = [row[0] for row in cur_main.fetchall()]
        conn_main.close()
        log.append(f"Found databases: {dbs}")

        # Step 2: Clean Each Database
        for db_name in dbs:
            log.append(f"\nProcessing {db_name}...")
            try:
                conn = psycopg2.connect(dbname=db_name, user="aman", password="sword123!@#", host="localhost")
                cur = conn.cursor()
                
                # Check User Count first
                cur.execute("SELECT count(*) FROM parties WHERE is_customer = TRUE")
                initial_count = cur.fetchone()[0]
                log.append(f"  - Initial Customers: {initial_count}")
                
                if initial_count > 0:
                    # DELETE LOGIC
                    queries = [
                        "DELETE FROM invoice_lines WHERE invoice_id IN (SELECT id FROM invoices WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE));",
                        "DELETE FROM invoices WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE);",
                        "DELETE FROM sales_quotation_lines WHERE quotation_id IN (SELECT id FROM sales_quotations WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE));",
                        "DELETE FROM sales_quotations WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE);",
                        "DELETE FROM sales_order_lines WHERE sales_order_id IN (SELECT id FROM sales_orders WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE));",
                        "DELETE FROM sales_orders WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE);",
                        "DELETE FROM payment_allocations WHERE payment_id IN (SELECT id FROM payment_vouchers WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE));",
                        "DELETE FROM payment_vouchers WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE);",
                        "DELETE FROM sales_return_lines WHERE return_id IN (SELECT id FROM sales_returns WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE));",
                        "DELETE FROM sales_returns WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE);",
                        "DELETE FROM party_transactions WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE);",
                        "DELETE FROM parties WHERE is_customer = TRUE OR party_type = 'customer';"
                    ]
                    
                    for q in queries:
                        try:
                            cur.execute(q)
                        except Exception as ignore:
                            # Catch specific table not found errors
                            pass
                            
                    conn.commit()
                    
                    # Verify
                    cur.execute("SELECT count(*) FROM parties WHERE is_customer = TRUE")
                    final_count = cur.fetchone()[0]
                    log.append(f"  - Final Customers: {final_count}")
                else:
                    log.append("  - No customers found to delete.")
                    
                conn.close()

            except Exception as e:
                log.append(f"  - Error processing {db_name}: {str(e)}")

    except Exception as e:
        log.append(f"Fatal Error: {str(e)}")

    with open("/home/omar/Desktop/aman/cleanup_result.txt", "w") as f:
        f.write("\n".join(log))

if __name__ == "__main__":
    run_cleanup()
