
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app
from database import get_system_db, hash_password
from sqlalchemy import text, create_engine
from config import settings
import logging

# Ensure logging is configured to see output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = TestClient(app)

COMPANY_ID = "99900001"
DB_NAME = f"aman_{COMPANY_ID}"
HQ_USER = "user.hq.1"
JED_USER = "user.br-jed.1"
PASSWORD = "123456"

def get_token(username, password):
    response = client.post("/api/auth/login", data={"username": username, "password": password})
    if response.status_code != 200:
        logger.error(f"Login failed for {username}: {response.text}")
        return None
    return response.json()["access_token"]

def verify_access():
    logger.info(f"🔒 Verifying Branch Access Control for Company {COMPANY_ID}...")
    
    # 1. Login as HQ User
    hq_token = get_token(HQ_USER, PASSWORD)
    if not hq_token:
        logger.error("Failed to get HQ token. Seeding might be incomplete.")
        return

    # 2. Get Employees (No filter) -> Should see only HQ employees
    headers = {"Authorization": f"Bearer {hq_token}"}
    response = client.get("/api/hr/employees", headers=headers)
    assert response.status_code == 200
    employees = response.json()
    
    # Verify all employees belong to HQ branch
    # We need to know HQ branch ID. Let's fetch it or infer from names.
    # Assuming seed script created branches: HQ, BR-JED, BR-DAM
    # And users were assigned effectively.
    
    logger.info(f"HQ User sees {len(employees)} employees.")
    for emp in employees:
        # Check if branch name contains 'Main' or 'HQ' or check ID consistency
        # Since we don't have IDs easily, let's just check if they differ from Jeddah employees.
        pass

    # 3. Try to access Jeddah Branch Data explicitly (Mock ID needed)
    # We need a valid branch ID for Jeddah to test the 403
    # Let's fetch branch IDs from DB first
    
    db_url = settings.get_company_database_url(COMPANY_ID)
    engine = create_engine(db_url)
    with engine.connect() as conn:
        hq_id = conn.execute(text("SELECT id FROM branches WHERE branch_code = 'HQ'")).scalar()
        jed_id = conn.execute(text("SELECT id FROM branches WHERE branch_code = 'BR-JED'")).scalar()
    
    logger.info(f"HQ Branch ID: {hq_id}, Jeddah Branch ID: {jed_id}")
    
    # Verify fetched employees match HQ ID
    for emp in employees:
        if emp['branch_id'] != hq_id:
            logger.error(f"❌ Security Breach! HQ user saw employee {emp['first_name']} from branch {emp['branch_id']}")
        else:
            # logger.info(f"✅ Employee {emp['first_name']} is from HQ.")
            pass
            
    # 4. Attempt to access Jeddah employees explicitly
    response_forbidden = client.get(f"/api/hr/employees?branch_id={jed_id}", headers=headers)
    if response_forbidden.status_code == 403:
        logger.info("✅ Access to Jeddah branch denied for HQ user (403 Forbidden).")
    else:
        logger.error(f"❌ Expected 403 Forbidden, got {response_forbidden.status_code}: {response_forbidden.text}")

    logger.info("🎉 Verification Complete!")

if __name__ == "__main__":
    verify_access()
