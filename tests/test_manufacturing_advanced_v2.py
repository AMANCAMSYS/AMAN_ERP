
import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_db_connection
from sqlalchemy import text
import datetime

client = TestClient(app)

# Helper to get auth token
def get_auth_headers():
    login_res = client.post("/auth/token", data={"username": "admin", "password": "adminpassword"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="module")
def auth_headers():
    return get_auth_headers()

def test_equipment_lifecycle(auth_headers):
    # 1. Create Work Center for Equipment
    wc_res = client.post("/manufacturing/work-centers", json={
        "name": "Test WC Equipment",
        "code": "WC-EQ-001",
        "cost_per_hour": 100.0
    }, headers=auth_headers)
    assert wc_res.status_code == 200
    wc_id = wc_res.json()["id"]

    # 2. Create Equipment
    eq_res = client.post("/manufacturing/equipment", json={
        "name": "Heavy Press",
        "code": "EQ-001",
        "work_center_id": wc_id,
        "status": "active"
    }, headers=auth_headers)
    assert eq_res.status_code == 200
    eq_data = eq_res.json()
    assert eq_data["name"] == "Heavy Press"
    eq_id = eq_data["id"]

    # 3. List Equipment
    list_res = client.get("/manufacturing/equipment", headers=auth_headers)
    assert list_res.status_code == 200
    assert any(e["id"] == eq_id for e in list_res.json())

    # 4. Create Maintenance Log
    log_res = client.post("/manufacturing/maintenance-logs", json={
        "equipment_id": eq_id,
        "maintenance_type": "preventive",
        "maintenance_date": datetime.date.today().isoformat(),
        "cost": 500.0,
        "description": "Oil Change"
    }, headers=auth_headers)
    assert log_res.status_code == 200
    
    # 5. Check Equipment Last Maintenance Date Update
    eq_check = client.get(f"/manufacturing/equipment/{eq_id}", headers=auth_headers) # We don't have get single equipment endpoint, assume list or implementation details
    # Actually we only implemented list.
    list_res = client.get("/manufacturing/equipment", headers=auth_headers)
    updated_eq = next(e for e in list_res.json() if e["id"] == eq_id)
    assert updated_eq["last_maintenance_date"] == datetime.date.today().isoformat()

def test_scheduling_operations(auth_headers):
    # 1. Create Route & Operations
    # Create Product first
    prod_res = client.post("/products/", json={
        "product_name": "Schedule Product",
        "sku": "SCH-001",
        "cost_price": 10.0,
        "selling_price": 20.0
    }, headers=auth_headers)
    pid = prod_res.json()["id"]

    wc_res = client.post("/manufacturing/work-centers", json={"name": "Schedule WC", "cost_per_hour": 50}, headers=auth_headers)
    wcid = wc_res.json()["id"]

    route_res = client.post("/manufacturing/routes", json={
        "name": "Schedule Route",
        "product_id": pid,
        "operations": [
            {"sequence": 10, "work_center_id": wcid, "description": "Op 1", "setup_time": 10, "cycle_time": 20}
        ]
    }, headers=auth_headers)
    rid = route_res.json()["id"]

    # 2. Create Order
    order_res = client.post("/manufacturing/orders", json={
        "product_id": pid,
        "route_id": rid,
        "quantity": 10,
        "start_date": datetime.date.today().isoformat()
    }, headers=auth_headers)
    assert order_res.status_code == 200
    
    # 3. List Operations (Scheduling Endpoint)
    ops_res = client.get("/manufacturing/operations", params={"start_date": datetime.date.today().isoformat()}, headers=auth_headers)
    assert ops_res.status_code == 200
    ops = ops_res.json()
    assert len(ops) > 0
    # Verify strict structure
    assert "order_number" in ops[0]
    assert "work_center_name" in ops[0]

def test_production_costing(auth_headers):
    # 1. Setup Data
    # Product
    p_res = client.post("/products/", json={"product_name": "Cost Product", "sku": "COST-001", "cost_price": 100}, headers=auth_headers)
    pid = p_res.json()["id"]

    # WC with Cost
    wc_res = client.post("/manufacturing/work-centers", json={"name": "Cost WC", "cost_per_hour": 600}, headers=auth_headers) # 600/hr = 10/min
    wcid = wc_res.json()["id"]
    
    # Route
    r_res = client.post("/manufacturing/routes", json={
        "name": "Cost Route",
        "product_id": pid,
        "operations": [{"sequence": 10, "work_center_id": wcid, "description": "Cost Op"}]
    }, headers=auth_headers)
    rid = r_res.json()["id"]
    op_def_id = r_res.json()["operations"][0]["id"] # This is route operation ID, not order operation ID yet.

    # Order
    o_res = client.post("/manufacturing/orders", json={"product_id": pid, "route_id": rid, "quantity": 1, "status": "confirmed"}, headers=auth_headers)
    oid = o_res.json()["id"]
    order_op_id = o_res.json()["operations"][0]["id"]

    # 2. Start Order
    client.post(f"/manufacturing/orders/{oid}/start", headers=auth_headers)
    
    # 3. Start Operation
    client.post(f"/manufacturing/operations/{order_op_id}/start", headers=auth_headers)
    
    # 4. Mock Time Passing (Update start_time manually in DB to be 30 mins ago)
    # 30 mins * 10/min = 300 cost
    db = get_db_connection(1) # Assuming company 1
    db.execute(text("UPDATE production_order_operations SET start_time = NOW() - INTERVAL '30 minutes' WHERE id = :id"), {"id": order_op_id})
    db.commit()
    db.close()

    # 5. Complete Operation
    comp_op_res = client.post(f"/manufacturing/operations/{order_op_id}/complete", params={"completed_qty": 1}, headers=auth_headers)
    assert comp_op_res.status_code == 200
    assert comp_op_res.json()["actual_run_time"] >= 29 # Should count ~30 mins

    # 6. Check Order Cost (Get Order)
    get_o_res = client.get(f"/manufacturing/orders/{oid}", headers=auth_headers)
    data = get_o_res.json()
    
    labor_cost = data.get("total_labor_overhead_cost", 0)
    # Expected: 0.5 hours * 600 = 300
    assert 290 <= labor_cost <= 310

    # 7. Complete Order (Check Journal)
    comp_order_res = client.post(f"/manufacturing/orders/{oid}/complete", headers=auth_headers)
    assert comp_order_res.status_code == 200
    
