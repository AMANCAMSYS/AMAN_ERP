
import psycopg2
try:
    conn = psycopg2.connect(dbname="aman_b08f3451", user="aman", password="sword123!@#", host="localhost")
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM parties WHERE is_customer = TRUE")
    count = cur.fetchone()[0]
    print(f"Remaining customers: {count}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
