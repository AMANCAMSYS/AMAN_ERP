
import psycopg2
import sys

# Try both potential DB names just in case
DBS = ["aman_b08f3451", "aman_39a597c9"]
USER = "aman"
PASS = "sword123!@#"
HOST = "localhost"

def delete_all_customers():
    results = []
    
    for db_name in DBS:
        try:
            conn = psycopg2.connect(dbname=db_name, user=USER, password=PASS, host=HOST)
            cur = conn.cursor()
            
            # Check customers before
            cur.execute("SELECT count(*) FROM parties WHERE is_customer = TRUE OR party_type = 'customer'")
            count_before = cur.fetchone()[0]
            if count_before > 0:
                results.append(f"DB {db_name}: Found {count_before} customers. Deleting...")
                
                # Delete related tables in order
                tables_to_clear = [
                     "sales_return_lines", "sales_returns",
                     "sales_order_lines", "sales_orders", 
                     "sales_quotation_lines", "sales_quotations",
                     "invoice_lines", "invoices",
                     "payment_allocations", "payment_vouchers",
                     "party_transactions" # Important! Transactions link to parties
                ]
                
                for table in tables_to_clear:
                    try:
                        cur.execute(f"DELETE FROM {table} WHERE EXISTS (SELECT 1 FROM parties WHERE parties.id = {table}.party_id AND (parties.is_customer = TRUE OR parties.party_type = 'customer'))")
                    except Exception as e:
                        # Some tables might not have party_id directly or might be named differently
                        pass

                # Direct deletes for tables with explicit party_id reference
                cur.execute("DELETE FROM payment_allocations WHERE payment_id IN (SELECT id FROM payment_vouchers WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE))")
                cur.execute("DELETE FROM payment_vouchers WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE)")
                cur.execute("DELETE FROM invoice_lines WHERE invoice_id IN (SELECT id FROM invoices WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE))")
                cur.execute("DELETE FROM invoices WHERE party_id IN (SELECT id FROM parties WHERE is_customer = TRUE)")
                
                # Finally delete parties
                cur.execute("DELETE FROM parties WHERE is_customer = TRUE OR party_type = 'customer'")
                
                # Verify
                cur.execute("SELECT count(*) FROM parties WHERE is_customer = TRUE OR party_type = 'customer'")
                count_after = cur.fetchone()[0]
                results.append(f"DB {db_name}: Finished. Remaining: {count_after}")
                conn.commit()
            else:
                results.append(f"DB {db_name}: No customers found.")
                
            conn.close()
            
        except psycopg2.OperationalError:
            results.append(f"DB {db_name}: Does not exist or cannot connect.")
        except Exception as e:
            results.append(f"DB {db_name}: Error - {e}")

    with open("/home/omar/Desktop/aman/delete_log.txt", "w") as f:
        f.write("\n".join(results))

if __name__ == "__main__":
    delete_all_customers()
