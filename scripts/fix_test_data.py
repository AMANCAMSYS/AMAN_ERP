#!/usr/bin/env python3
"""
AMAN ERP - Fix and complete remaining test data
Fixes: departments, employees, PO approval/receiving, expense approval, assets
"""

import requests
import json
import sys
from datetime import date, datetime

BASE_URL = "http://localhost:8000/api"
TOKEN = open("/tmp/aman_token.txt").read().strip()
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def api_post(path, data, label=""):
    r = requests.post(f"{BASE_URL}{path}", json=data, headers=HEADERS)
    status = "✓" if r.status_code < 300 else "✗"
    detail = ""
    try:
        resp = r.json()
        if r.status_code >= 300:
            detail = str(resp.get("detail", resp))[:100]
    except:
        resp = r.text
        detail = resp[:100]
    print(f"  {status} [{r.status_code}] {label}: {detail if detail else 'OK'}")
    return r.status_code, resp if isinstance(resp, dict) else {"raw": resp}

def api_put(path, data=None, label=""):
    r = requests.put(f"{BASE_URL}{path}", json=data, headers=HEADERS)
    status = "✓" if r.status_code < 300 else "✗"
    detail = ""
    try:
        resp = r.json()
        if r.status_code >= 300:
            detail = str(resp.get("detail", resp))[:100]
    except:
        resp = r.text
        detail = resp[:100]
    print(f"  {status} [{r.status_code}] {label}: {detail if detail else 'OK'}")
    return r.status_code, resp if isinstance(resp, dict) else {"raw": resp}

def api_get(path):
    r = requests.get(f"{BASE_URL}{path}", headers=HEADERS)
    try:
        return r.json()
    except:
        return r.text

print("="*60)
print("🔧 FIXING REMAINING DATA")
print("="*60)

# ============================================================
# 1. FIX: HR Departments (need department_name field)
# ============================================================
print("\n--- HR DEPARTMENTS ---")
departments = [
    {"department_name": "الإدارة العامة"},
    {"department_name": "المحاسبة والمالية"},
    {"department_name": "المبيعات"},
    {"department_name": "المشتريات"},
    {"department_name": "المستودعات"},
    {"department_name": "تقنية المعلومات"},
]
for d in departments:
    api_post("/hr/departments", d, d["department_name"])

# ============================================================
# 2. FIX: Employees (without create_ledger to avoid duplicate account)
# ============================================================
print("\n--- HR EMPLOYEES ---")
employees = [
    {"first_name": "أحمد", "last_name": "الشريف", "first_name_en": "Ahmed", "last_name_en": "Al-Sharif",
     "email": "ahmed@company.com", "phone": "+90 555 1111",
     "position_title": "مدير عام", "department_name": "الإدارة العامة",
     "salary": 25000, "housing_allowance": 5000, "transport_allowance": 2000, "other_allowances": 3000,
     "hire_date": "2024-01-01", "branch_id": 1, "create_ledger": False},
    {"first_name": "محمد", "last_name": "العتيبي", "first_name_en": "Mohammed", "last_name_en": "Al-Otaibi",
     "email": "mohammed@company.com", "phone": "+90 555 2222",
     "position_title": "محاسب رئيسي", "department_name": "المحاسبة والمالية",
     "salary": 15000, "housing_allowance": 3000, "transport_allowance": 1500, "other_allowances": 1000,
     "hire_date": "2024-03-01", "branch_id": 1, "create_ledger": False},
    {"first_name": "فاطمة", "last_name": "الزهراني", "first_name_en": "Fatima", "last_name_en": "Al-Zahrani",
     "email": "fatima@company.com", "phone": "+90 555 3333",
     "position_title": "مديرة مبيعات", "department_name": "المبيعات",
     "salary": 12000, "housing_allowance": 2500, "transport_allowance": 1500, "other_allowances": 1000,
     "hire_date": "2024-06-01", "branch_id": 1, "create_ledger": False},
    {"first_name": "خالد", "last_name": "القحطاني", "first_name_en": "Khaled", "last_name_en": "Al-Qahtani",
     "email": "khaled@company.com", "phone": "+90 555 4444",
     "position_title": "مسؤول مشتريات", "department_name": "المشتريات",
     "salary": 10000, "housing_allowance": 2000, "transport_allowance": 1000, "other_allowances": 500,
     "hire_date": "2024-04-01", "branch_id": 1, "create_ledger": False},
    {"first_name": "سارة", "last_name": "المالكي", "first_name_en": "Sarah", "last_name_en": "Al-Malki",
     "email": "sarah@company.com", "phone": "+90 555 5555",
     "position_title": "أمينة مستودع", "department_name": "المستودعات",
     "salary": 8000, "housing_allowance": 1500, "transport_allowance": 1000, "other_allowances": 500,
     "hire_date": "2024-07-01", "branch_id": 2, "create_ledger": False},
    {"first_name": "عمر", "last_name": "الحربي", "first_name_en": "Omar", "last_name_en": "Al-Harbi",
     "email": "omar.h@company.com", "phone": "+90 555 6666",
     "position_title": "مندوب مبيعات", "department_name": "المبيعات",
     "salary": 7000, "housing_allowance": 1500, "transport_allowance": 1000, "other_allowances": 500,
     "hire_date": "2025-01-01", "branch_id": 2, "create_ledger": False},
    {"first_name": "نورة", "last_name": "السبيعي", "first_name_en": "Noura", "last_name_en": "Al-Subaie",
     "email": "noura@company.com", "phone": "+971 555 7777",
     "position_title": "مديرة فرع دبي", "department_name": "الإدارة العامة",
     "salary": 18000, "housing_allowance": 4000, "transport_allowance": 2000, "other_allowances": 2000,
     "hire_date": "2024-09-01", "branch_id": 3, "create_ledger": False},
    {"first_name": "يوسف", "last_name": "الدوسري", "first_name_en": "Yousef", "last_name_en": "Al-Dosari",
     "email": "yousef@company.com", "phone": "+90 555 8888",
     "position_title": "فني IT", "department_name": "تقنية المعلومات",
     "salary": 9000, "housing_allowance": 2000, "transport_allowance": 1000, "other_allowances": 500,
     "hire_date": "2025-02-01", "branch_id": 1, "create_ledger": False},
]
for e in employees:
    api_post("/hr/employees", e, f"{e['first_name']} {e['last_name']}")

# ============================================================
# 3. FIX: Approve POs (use PUT method)
# ============================================================
print("\n--- APPROVE PURCHASE ORDERS ---")
# Get POs
pos = api_get("/buying/orders")
po_list = pos if isinstance(pos, list) else pos.get("items", pos.get("orders", []))
print(f"  Found {len(po_list)} POs")
for po in po_list:
    po_id = po.get("id")
    st = po.get("status", "")
    if st in ("draft", "pending"):
        api_put(f"/buying/orders/{po_id}/approve", None, f"Approve PO#{po_id} (was {st})")

# ============================================================
# 4. RECEIVE POs
# ============================================================
print("\n--- RECEIVE PURCHASE ORDERS ---")
warehouses = api_get("/inventory/warehouses")
wh_list = warehouses if isinstance(warehouses, list) else warehouses.get("items", [])
wh_map = {w.get("name", ""): w["id"] for w in wh_list}

for po in po_list:
    po_id = po.get("id")
    # Re-fetch to get updated status
    po_detail = api_get(f"/buying/orders/{po_id}")
    if not isinstance(po_detail, dict):
        continue
    status = po_detail.get("status", "")
    if status != "approved":
        print(f"  ⚠ PO#{po_id} status={status}, skipping receive")
        continue
    
    lines = po_detail.get("items", po_detail.get("lines", []))
    if not lines:
        print(f"  ⚠ PO#{po_id} no lines found")
        continue
    
    branch_id = po_detail.get("branch_id", 1)
    wh_id = wh_map.get("المستودع الرئيسي", 1)
    if branch_id == 2:
        wh_id = wh_map.get("مستودع جدة", wh_id)
    elif branch_id == 3:
        wh_id = wh_map.get("مستودع دبي", wh_id)
    
    receive_items = []
    for line in lines:
        lid = line.get("id") or line.get("line_id")
        qty = line.get("quantity", 0)
        if lid:
            receive_items.append({"line_id": lid, "received_quantity": qty})
    
    if receive_items:
        recv = {"items": receive_items, "warehouse_id": wh_id, "notes": f"استلام PO#{po_id}"}
        api_post(f"/buying/orders/{po_id}/receive", recv, f"Receive PO#{po_id}")

# ============================================================
# 5. FIX: Approve expenses (use approval_status field)
# ============================================================
print("\n--- APPROVE EXPENSES ---")
expenses_resp = api_get("/expenses/")
exp_list = expenses_resp if isinstance(expenses_resp, list) else expenses_resp.get("items", expenses_resp.get("expenses", []))
for exp in exp_list:
    eid = exp.get("id")
    st = exp.get("status", exp.get("approval_status", ""))
    if st in ("pending", "draft", "submitted"):
        api_post(f"/expenses/{eid}/approve", 
                {"approval_status": "approved", "approval_notes": "تمت الموافقة"}, 
                f"Approve expense #{eid}")

# ============================================================
# 6. FIX: Assets (add currency=TRY)
# ============================================================
print("\n--- FIXED ASSETS ---")
assets = [
    {"name": "سيارة تويوتا كامري 2026", "code": "AST-VEH-001",
     "type": "vehicle", "purchase_date": "2026-01-15",
     "cost": 120000, "residual_value": 20000, "life_years": 5, "branch_id": 1,
     "depreciation_method": "straight_line", "currency": "TRY"},
    {"name": "خادم Dell PowerEdge", "code": "AST-CMP-001",
     "type": "equipment", "purchase_date": "2026-01-20",
     "cost": 45000, "residual_value": 5000, "life_years": 4, "branch_id": 1,
     "depreciation_method": "straight_line", "currency": "TRY"},
    {"name": "أثاث مكتبي - المقر الرئيسي", "code": "AST-FUR-001",
     "type": "furniture", "purchase_date": "2026-01-01",
     "cost": 30000, "residual_value": 3000, "life_years": 7, "branch_id": 1,
     "depreciation_method": "straight_line", "currency": "TRY"},
    {"name": "طابعة صناعية", "code": "AST-MAC-001",
     "type": "equipment", "purchase_date": "2026-02-01",
     "cost": 80000, "residual_value": 8000, "life_years": 6, "branch_id": 1,
     "depreciation_method": "straight_line", "currency": "TRY"},
    {"name": "أثاث مكتبي - فرع جدة", "code": "AST-FUR-002",
     "type": "furniture", "purchase_date": "2026-02-10",
     "cost": 15000, "residual_value": 1500, "life_years": 7, "branch_id": 2,
     "depreciation_method": "straight_line", "currency": "TRY"},
    {"name": "سيارة نقل - دبي", "code": "AST-VEH-002",
     "type": "vehicle", "purchase_date": "2026-01-25",
     "cost": 8500, "residual_value": 1500, "life_years": 5, "branch_id": 3,
     "currency": "AED", "depreciation_method": "straight_line"},
]
for a in assets:
    api_post("/assets/", a, a["name"][:40])

# ============================================================
# 7. CUSTOMER GROUPS (fix field name)
# ============================================================
print("\n--- CUSTOMER GROUPS ---")
groups = [
    {"group_name": "عملاء محليون"},
    {"group_name": "عملاء دوليون"},
    {"group_name": "عملاء VIP"},
]
for g in groups:
    api_post("/sales/customer-groups", g, g["group_name"])

print("\n" + "="*60)
print("✅ FIX COMPLETE!")
print("="*60)
