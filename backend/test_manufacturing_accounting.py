
import requests
from database import get_db_connection
from sqlalchemy import text
import sys
import time

# Configuration
BASE_URL = "http://localhost:8000"
COMPANY_ID = "be67ce39"
USERNAME = "aman" # Assuming this is the username
PASSWORD = "YourPassword123!@#" # From .env

def test_manufacturing_flow():
    print("Testing Manufacturing Flow...", flush=True)
    # 1. Setup Data directly in DB (to rely less on API for setup)
    print("Connecting to DB...", flush=True)
    conn = get_db_connection(COMPANY_ID)
    print("Connected.", flush=True)
    try:
        # Cleanup previous test data
        product_ids = conn.execute(text("SELECT id FROM products WHERE product_code IN ('RM-TEST-003', 'FG-TEST-003')")).fetchall()
        if product_ids:
            pids = [p[0] for p in product_ids]
            conn.execute(text("DELETE FROM inventory_transactions WHERE product_id = ANY(:pids)"), {"pids": pids})
            conn.execute(text("DELETE FROM inventory WHERE product_id = ANY(:pids)"), {"pids": pids})
            conn.execute(text("DELETE FROM production_orders WHERE product_id = ANY(:pids)"), {"pids": pids})
            conn.execute(text("DELETE FROM bom_components WHERE component_product_id = ANY(:pids) OR bom_id IN (SELECT id FROM bill_of_materials WHERE product_id = ANY(:pids))"), {"pids": pids})
            conn.execute(text("DELETE FROM bill_of_materials WHERE product_id = ANY(:pids)"), {"pids": pids})
            conn.execute(text("DELETE FROM manufacturing_routes WHERE product_id = ANY(:pids)"), {"pids": pids})
            conn.execute(text("DELETE FROM products WHERE id = ANY(:pids)"), {"pids": pids})
        conn.commit()

        # Create RM
        rm_id = conn.execute(text("""
            INSERT INTO products (product_name, product_code, cost_price, selling_price)
            VALUES ('Raw Material Test 3', 'RM-TEST-003', 10.0, 0)
            RETURNING id
        """)).fetchone().id
        
        # Create FG
        fg_id = conn.execute(text("""
            INSERT INTO products (product_name, product_code, cost_price, selling_price)
            VALUES ('Finish Good Test 3', 'FG-TEST-003', 50.0, 100)
            RETURNING id
        """)).fetchone().id
        
        # Create Warehouse
        wh_id = conn.execute(text("SELECT id FROM warehouses LIMIT 1")).fetchone().id
        
        # Add Stock to RM
        conn.execute(text("""
            INSERT INTO inventory (warehouse_id, product_id, quantity, updated_at)
            VALUES (:whid, :pid, 100, NOW())
            ON CONFLICT (warehouse_id, product_id) DO UPDATE SET quantity = 100, updated_at = NOW()
        """), {"whid": wh_id, "pid": rm_id})
        
        # Create Route
        route = conn.execute(text("""
            INSERT INTO manufacturing_routes (name, product_id, is_active) VALUES ('Test Route 2', :pid, true) RETURNING id
        """), {"pid": fg_id}).fetchone()
        
        # Create BOM
        bom = conn.execute(text("""
            INSERT INTO bill_of_materials (product_id, code, name, yield_quantity, route_id, is_active)
            VALUES (:pid, 'BOM-TEST-2', 'Test BOM 2', 1, :rid, true)
            RETURNING id
        """), {"pid": fg_id, "rid": route.id}).fetchone()
        
        # Add BOM Component (2 RM per FG)
        conn.execute(text("""
            INSERT INTO bom_components (bom_id, component_product_id, quantity)
            VALUES (:bid, :cpid, 2)
        """), {"bid": bom.id, "cpid": rm_id})
        
        conn.commit()
        
        # 2. Authenticate (Manual Token Generation to bypass login)
        print("Bypassing login via manual token generation...")
        from jose import jwt
        from config import settings
        from datetime import datetime, timedelta, timezone
        
        # We need a user_id from the company database for 'admin'
        user = conn.execute(text("SELECT id FROM company_users WHERE username = 'admin' LIMIT 1")).fetchone()
        if not user:
             # Create admin user if not exists for test
             from database import hash_password
             user_id = conn.execute(text("""
                INSERT INTO company_users (username, password, full_name, role, permissions, is_active)
                VALUES ('admin', :pwd, 'Test Admin', 'admin', '["*"]', true)
                RETURNING id
             """), {"pwd": hash_password("YourPassword123!@#")}).fetchone().id
             conn.commit()
        else:
             user_id = user.id

        token_data = {
            "sub": "admin",
            "user_id": user_id,
            "company_id": COMPANY_ID,
            "role": "admin",
            "permissions": ["*"],
            "type": "company_user"
        }
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)
        token_data.update({"exp": expire, "iat": datetime.now(timezone.utc)})
        token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        headers = {"Authorization": f"Bearer {token}"}
        print("Authenticated.")

        # 3. Create Order via API
        print("Creating Order...")
        res = requests.post(f"{BASE_URL}/api/manufacturing/orders", json={
            "product_id": fg_id,
            "bom_id": bom.id,
            "route_id": route.id,
            "quantity": 5, 
            "warehouse_id": wh_id,
            "destination_warehouse_id": wh_id,
            "status": "draft",
            "start_date": "2026-02-16",
            "due_date": "2026-02-20"
        }, headers=headers)
        
        if res.status_code != 200:
            print(f"Failed to create order: {res.text}")
            return
            
        order = res.json()
        order_id = order['id']
        print(f"Order Created: {order['order_number']}")
        
        # 4. Start Order
        print("Starting Order...")
        res = requests.post(f"{BASE_URL}/api/manufacturing/orders/{order_id}/start", headers=headers)
        print(f"Start Order Response: {res.status_code}")
        if res.status_code != 200:
           print(f"Failed to start order: {res.text}")
           return
           
        print("Order Started. Checking Accounting...")
        
        # Check Journal for Start
        journals = conn.execute(text("""
            SELECT j.id, l.account_id, l.debit, l.credit, a.account_number
            FROM journal_entries j
            JOIN journal_lines l ON j.id = l.journal_entry_id
            JOIN accounts a ON l.account_id = a.id
            WHERE j.reference = :ref AND j.description LIKE '%Material Consumption%'
        """), {"ref": order['order_number']}).fetchall()
        
        if not journals:
            print("❌ No Journal Entry found for Start!")
        else:
            print("✅ Journal Entry for Start found:")
            for j in journals:
                print(f"   Acc: {j.account_number} | Dr: {j.debit} | Cr: {j.credit}")
        
        # Check Inventory Transaction
        tx = conn.execute(text("""
            SELECT * FROM inventory_transactions 
            WHERE reference_id = :ref AND transaction_type = 'production_out'
        """), {"ref": order_id}).fetchall()
        if tx:
             print(f"✅ Inventory deducted: {len(tx)} transactions")
        else:
             print("❌ No Inventory deducted!")

        # 5. Complete Order
        print("Completing Order...")
        res = requests.post(f"{BASE_URL}/api/manufacturing/orders/{order_id}/complete", headers=headers)
        if res.status_code != 200:
           print(f"Failed to complete order: {res.text}")
           return
           
        print("Order Completed. Checking Accounting...")
        
        # Check Journal for Complete
        journals = conn.execute(text("""
            SELECT j.id, l.account_id, l.debit, l.credit, a.account_number
            FROM journal_entries j
            JOIN journal_lines l ON j.id = l.journal_entry_id
            JOIN accounts a ON l.account_id = a.id
            WHERE j.reference = :ref AND j.description LIKE '%FG Capitalization%'
        """), {"ref": order['order_number']}).fetchall()
        
        if not journals:
            print("❌ No Journal Entry found for Complete!")
        else:
            print("✅ Journal Entry for Complete found:")
            for j in journals:
                print(f"   Acc: {j.account_number} | Dr: {j.debit} | Cr: {j.credit}")

    except Exception as e:
        print(f"Test Failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_manufacturing_flow()
