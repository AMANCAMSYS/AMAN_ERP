#!/usr/bin/env python3
"""Check current state of company ba2f6dc3 on remote server"""
import requests
import json

API = "http://64.225.49.118/api"

# Login
resp = requests.post(f"{API}/auth/login", data={
    "username": "vvvv",
    "password": "As123321",
    "company_code": "ba2f6dc3"
})
token = resp.json()["access_token"]
H = {"Authorization": f"Bearer {token}"}

endpoints = [
    ("Branches", "/branches"),
    ("Accounts", "/accounting/accounts"),
    ("Currencies", "/accounting/currencies"),
    ("Roles", "/roles"),
    ("Warehouses", "/inventory/warehouses"),
    ("Products", "/inventory/products"),
    ("Parties", "/parties"),
    ("Settings", "/settings"),
    ("Fiscal Years", "/accounting/fiscal-years"),
    ("Treasury", "/treasury/accounts"),
    ("Departments", "/hr/departments"),
    ("Positions", "/hr/positions"),
    ("Employees", "/hr/employees"),
    ("Product Categories", "/inventory/categories"),
    ("Units", "/inventory/units"),
    ("Customer Groups", "/sales/customer-groups"),
    ("Supplier Groups", "/buying/supplier-groups"),
    ("Tax Rates", "/taxes/rates"),
    ("WHT Rates", "/taxes/wht-rates"),
]

for name, ep in endpoints:
    try:
        r = requests.get(f"{API}{ep}", headers=H, timeout=10)
        d = r.json()
        if isinstance(d, list):
            print(f"{name}: {len(d)} items")
            if len(d) > 0 and len(d) <= 10:
                for item in d[:5]:
                    if isinstance(item, dict):
                        key = next((k for k in ['name','branch_name','role_name','warehouse_name','code','setting_key','department_name','position_name'] if k in item), None)
                        if key:
                            print(f"  - {item.get(key, '?')} (id={item.get('id','?')})")
        elif isinstance(d, dict):
            print(f"{name}: {len(d)} keys")
        else:
            print(f"{name}: {d}")
    except Exception as e:
        print(f"{name}: ERROR - {e}")
