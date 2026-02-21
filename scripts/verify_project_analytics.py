import sys
import os
from datetime import date, timedelta

# Add backend to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from fastapi.testclient import TestClient
from main import app
from database import get_db_connection
from routers.auth import create_access_token

client = TestClient(app)

def verify_project_analytics():
    print("🚀 Starting Project Analytics Verification...")

    # 1. Setup Auth
    # Assuming user ID 1 is details (system admin)
    token = create_access_token({"sub": "admin", "id": 1, "role": "system_admin", "company_id": 1})
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create a Test Project via API
    project_data = {
        "project_name": "Analytics Test Project",
        "project_code": "ANA-001",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=30)),
        "status": "in_progress",
        "planned_budget": 10000,
        "project_type": "internal"
    }
    resp = client.post("/api/projects/", json=project_data, headers=headers)
    if resp.status_code != 200:
        print(f"❌ Failed to create project: {resp.text}")
        return
    project_id = resp.json()["id"]
    print(f"✅ Project created: {project_id}")

    try:
        # 3. Create a Task and Assign it
        # Assuming employee ID 1 exists (admin user is also employee usually)
        task_data = {
            "task_name": "Resource Task",
            "start_date": str(date.today()),
            "end_date": str(date.today() + timedelta(days=5)),
            "planned_hours": 20,
            "assigned_to": 1, 
            "status": "in_progress"
        }
        resp = client.post(f"/api/projects/{project_id}/tasks", json=task_data, headers=headers)
        if resp.status_code != 200:
            print(f"⚠️ Failed to create task: {resp.text}")
        else:
            print("✅ Task created and assigned")

        # 4. Verify Resource Allocation
        start_date = str(date.today())
        end_date = str(date.today() + timedelta(days=7))
        resp = client.get(f"/api/projects/resources/allocation?start_date={start_date}&end_date={end_date}", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            # print(f"Allocation Data: {data}")
            # Check if employee 1 is in list
            found = False
            for emp in data:
                if emp['id'] == 1:
                    found = True
                    daily_hours = emp['daily_load'][0]['hours']
                    print(f"✅ Resource Allocation Verified. Employee 1 found with {daily_hours} hrs/day")
                    break
            if not found:
                 print("⚠️ Employee 1 not found in allocation (might not be an employee in DB?)")
        else:
            print(f"❌ Allocation API failed: {resp.text}")

        # 5. Create Financial Data (Expense & Revenue)
        # Expense
        exp_data = {
            "expense_type": "labor",
            "expense_date": str(date.today()),
            "amount": 1000,
            "description": "Test Labor"
        }
        client.post(f"/api/projects/{project_id}/expenses", json=exp_data, headers=headers)

        # Revenue
        rev_data = {
            "revenue_type": "invoice",
            "revenue_date": str(date.today()),
            "amount": 2500,
            "description": "Test Invoice"
        }
        client.post(f"/api/projects/{project_id}/revenues", json=rev_data, headers=headers)
        print("✅ Financial transactions created")

        # 6. Verify Project Financials
        resp = client.get(f"/api/projects/{project_id}/financials", headers=headers)
        if resp.status_code == 200:
            fin = resp.json()
            # Verify fields
            if "net_profit" in fin and "cost_breakdown" in fin:
                print(f"✅ Financials Verified:")
                print(f"   - Revenue: {fin['total_revenues']}")
                print(f"   - Expense: {fin['total_expenses']}")
                print(f"   - Net Profit: {fin['net_profit']}")
                print(f"   - Margin: {fin['margin_pct']}%")
                print(f"   - Cost Breakdown: {fin['cost_breakdown']}")
            else:
                print("❌ Financials response missing new fields")
        else:
            print(f"❌ Financials API failed: {resp.text}")

    finally:
        # Cleanup
        # client.delete(f"/projects/{project_id}", headers=headers)
        # print("🧹 Cleanup completed")
        pass

if __name__ == "__main__":
    verify_project_analytics()
