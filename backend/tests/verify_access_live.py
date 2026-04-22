
import requests

import os

BASE_URL = os.environ.get("AMAN_BASE_URL", "http://localhost:8000/api")
COMPANY_ID = "99900001"
HQ_USER = "user.hq.1"
JED_USER = "user.br-jed.1"
PASSWORD = os.environ.get("AMAN_VERIFY_PASSWORD", "")
if not PASSWORD:
    raise RuntimeError("AMAN_VERIFY_PASSWORD must be set before running verify_access_live.py")

def get_token(username, password):
    try:
        response = requests.post(f"{BASE_URL}/auth/login", data={"username": username, "password": password})
        if response.status_code != 200:
            print(f"Login failed for {username}: {response.text}")
            return None
        return response.json()["access_token"]
    except Exception as e:
        print(f"Connection error: {e}")
        return None

def verify_access():
    print("🔒 Verifying Branch Access Control...")
    
    # 1. Login as HQ User
    hq_token = get_token(HQ_USER, PASSWORD)
    if not hq_token:
        print("Failed to get HQ token.")
        return

    headers = {"Authorization": f"Bearer {hq_token}"}
    
    # 2. Get Employees (No filter)
    print("Requesting employees (no filter)...")
    response = requests.get(f"{BASE_URL}/hr/employees", headers=headers)
    
    if response.status_code == 200:
        employees = response.json()
        print(f"✅ HQ User sees {len(employees)} employees.")
    else:
        print(f"❌ Failed to get employees: {response.text}")

    # 3. Get Jeddah User Token to find their allowed branch ID
    jed_token = get_token(JED_USER, PASSWORD)
    if not jed_token:
         print("Failed to get Jeddah token.")
         return

    jed_response = requests.get(f"{BASE_URL}/auth/me", headers={"Authorization": f"Bearer {jed_token}"})
    jed_branch_id = jed_response.json()["allowed_branches"][0]
    print(f"Target Branch ID (Jeddah): {jed_branch_id}")

    # 4. Attempt to access Jeddah employees explicitly as HQ User
    print(f"Attempting to access Jeddah branch ({jed_branch_id}) as HQ User...")
    response_forbidden = requests.get(f"{BASE_URL}/hr/employees?branch_id={jed_branch_id}", headers=headers)
    
    if response_forbidden.status_code == 403:
        print("✅ Access to Jeddah branch denied for HQ user (403 Forbidden).")
    elif response_forbidden.status_code == 200 and len(response_forbidden.json()) == 0:
        print("⚠️ Returned empty list instead of 403. Check strictness.")
    else:
        print(f"❌ Expected 403, got {response_forbidden.status_code}")

if __name__ == "__main__":
    verify_access()
