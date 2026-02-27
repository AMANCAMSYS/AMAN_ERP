#!/usr/bin/env python3
"""
AMAN ERP - Comprehensive Test Data Insertion Script
Inserts all test data into company aman_80b0ada0 via API calls
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
    """POST to API and return response"""
    r = requests.post(f"{BASE_URL}{path}", json=data, headers=HEADERS)
    status = "✓" if r.status_code < 300 else "✗"
    detail = ""
    try:
        resp = r.json()
        if r.status_code >= 300:
            detail = resp.get("detail", str(resp))
    except:
        resp = r.text
        detail = resp
    print(f"  {status} [{r.status_code}] {label}: {detail if detail else 'OK'}")
    return r.status_code, resp if isinstance(resp, dict) else {"raw": resp}

def api_get(path, label=""):
    """GET from API"""
    r = requests.get(f"{BASE_URL}{path}", headers=HEADERS)
    try:
        return r.json()
    except:
        return r.text

# ============================================================
# 1. TREASURY ACCOUNTS
# ============================================================
def setup_treasury():
    print("\n" + "="*60)
    print("📦 TREASURY ACCOUNTS")
    print("="*60)
    
    treasuries = [
        {"name": "الصندوق الرئيسي", "name_en": "Main Cash Box", "account_type": "cash", 
         "currency": "TRY", "branch_id": 1, "opening_balance": 50000, "is_default": True},
        {"name": "صندوق جدة", "name_en": "Jeddah Cash Box", "account_type": "cash",
         "currency": "TRY", "branch_id": 2, "opening_balance": 20000},
        {"name": "صندوق دبي", "name_en": "Dubai Cash Box", "account_type": "cash",
         "currency": "AED", "branch_id": 3, "opening_balance": 15000, "exchange_rate": 0.115},
        {"name": "بنك الأهلي - حساب جاري", "name_en": "Al Ahli Bank - Current", "account_type": "bank",
         "currency": "TRY", "branch_id": 1, "bank_name": "البنك الأهلي",
         "account_number": "SA001234567890", "iban": "TR001234567890123456", "opening_balance": 200000},
        {"name": "بنك الراجحي", "name_en": "Al Rajhi Bank", "account_type": "bank",
         "currency": "TRY", "branch_id": 1, "bank_name": "بنك الراجحي",
         "account_number": "SA009876543210", "iban": "TR009876543210123456", "opening_balance": 150000},
        {"name": "بنك الأهلي - فرع جدة", "name_en": "Al Ahli - Jeddah", "account_type": "bank",
         "currency": "TRY", "branch_id": 2, "bank_name": "البنك الأهلي",
         "account_number": "SA001234500002", "opening_balance": 100000},
        {"name": "بنك دبي - AED", "name_en": "Dubai Bank - AED", "account_type": "bank",
         "currency": "AED", "branch_id": 3, "bank_name": "بنك دبي",
         "account_number": "AE001234567890", "opening_balance": 80000, "exchange_rate": 0.115},
    ]
    
    ids = {}
    for t in treasuries:
        code, resp = api_post("/treasury/accounts", t, t["name"])
        if code < 300:
            ids[t["name"]] = resp.get("id", resp.get("account_id"))
    return ids

# ============================================================
# 2. WAREHOUSES
# ============================================================
def setup_warehouses():
    print("\n" + "="*60)
    print("🏭 WAREHOUSES")
    print("="*60)
    
    warehouses = [
        {"name": "المستودع الرئيسي", "code": "WH001", "location": "المقر الرئيسي", "branch_id": 1, "is_default": True},
        {"name": "مستودع المواد الخام", "code": "WH002", "location": "المقر الرئيسي", "branch_id": 1},
        {"name": "مستودع جدة", "code": "WH003", "location": "جدة", "branch_id": 2},
        {"name": "مستودع دبي", "code": "WH004", "location": "دبي", "branch_id": 3},
    ]
    
    ids = {}
    for w in warehouses:
        code, resp = api_post("/inventory/warehouses", w, w["name"])
        if code < 300:
            ids[w["name"]] = resp.get("id", resp.get("warehouse_id"))
    return ids

# ============================================================
# 3. PRODUCT CATEGORIES
# ============================================================
def setup_categories():
    print("\n" + "="*60)
    print("📂 PRODUCT CATEGORIES")
    print("="*60)
    
    # Check if the endpoint exists
    cats = [
        {"name": "أجهزة إلكترونية", "name_en": "Electronics"},
        {"name": "مواد خام", "name_en": "Raw Materials"},
        {"name": "مستلزمات مكتبية", "name_en": "Office Supplies"},
        {"name": "خدمات", "name_en": "Services"},
    ]
    
    ids = {}
    for c in cats:
        code, resp = api_post("/inventory/categories", c, c["name"])
        if code < 300:
            ids[c["name"]] = resp.get("id", resp.get("category_id"))
        elif code == 404 or code == 405:
            print("  ⚠ Categories endpoint not available, skipping...")
            break
    return ids

# ============================================================
# 4. PRODUCTS
# ============================================================
def setup_products(cat_ids):
    print("\n" + "="*60)
    print("📦 PRODUCTS")
    print("="*60)
    
    products = [
        {"item_code": "PROD001", "item_name": "لابتوب HP ProBook", "item_name_en": "HP ProBook Laptop",
         "item_type": "product", "unit": "قطعة", "selling_price": 5000, "buying_price": 3500,
         "tax_rate": 18.0, "description": "لابتوب HP ProBook 450 G8",
         "has_serial_tracking": True},
        {"item_code": "PROD002", "item_name": "شاشة سامسونج 27 بوصة", "item_name_en": "Samsung 27\" Monitor",
         "item_type": "product", "unit": "قطعة", "selling_price": 1500, "buying_price": 1000,
         "tax_rate": 18.0, "has_batch_tracking": True},
        {"item_code": "PROD003", "item_name": "طابعة HP LaserJet", "item_name_en": "HP LaserJet Printer",
         "item_type": "product", "unit": "قطعة", "selling_price": 2000, "buying_price": 1400,
         "tax_rate": 18.0},
        {"item_code": "PROD004", "item_name": "ورق طباعة A4", "item_name_en": "A4 Paper",
         "item_type": "consumable", "unit": "رزمة", "selling_price": 30, "buying_price": 20,
         "tax_rate": 18.0},
        {"item_code": "PROD005", "item_name": "حبر طابعة HP", "item_name_en": "HP Ink Cartridge",
         "item_type": "consumable", "unit": "قطعة", "selling_price": 200, "buying_price": 130,
         "tax_rate": 18.0, "has_batch_tracking": True, "has_expiry_tracking": True, "shelf_life_days": 365},
        {"item_code": "SVC001", "item_name": "خدمة صيانة", "item_name_en": "Maintenance Service",
         "item_type": "service", "unit": "ساعة", "selling_price": 300, "buying_price": 0,
         "tax_rate": 18.0},
        {"item_code": "PROD006", "item_name": "كرسي مكتبي", "item_name_en": "Office Chair",
         "item_type": "product", "unit": "قطعة", "selling_price": 800, "buying_price": 500,
         "tax_rate": 18.0},
        {"item_code": "PROD007", "item_name": "مكتب خشبي", "item_name_en": "Wooden Desk",
         "item_type": "product", "unit": "قطعة", "selling_price": 1200, "buying_price": 750,
         "tax_rate": 18.0},
    ]
    
    ids = {}
    for p in products:
        code, resp = api_post("/inventory/products", p, p["item_name"])
        if code < 300:
            ids[p["item_code"]] = resp.get("id", resp.get("product_id"))
    return ids

# ============================================================
# 5. CUSTOMER GROUPS & CUSTOMERS
# ============================================================
def setup_customers():
    print("\n" + "="*60)
    print("👥 CUSTOMER GROUPS & CUSTOMERS")
    print("="*60)
    
    # Customer groups
    groups = [
        {"name": "عملاء محليون", "name_en": "Local Customers"},
        {"name": "عملاء دوليون", "name_en": "International Customers"},
        {"name": "عملاء VIP", "name_en": "VIP Customers"},
    ]
    
    group_ids = {}
    for g in groups:
        code, resp = api_post("/sales/customer-groups", g, g["name"])
        if code < 300:
            group_ids[g["name"]] = resp.get("id", resp.get("group_id"))
    
    # Customers
    customers = [
        {"name": "شركة التقنية المتقدمة", "name_en": "Advanced Tech Co.", 
         "email": "info@advtech.com", "phone": "+90 555 1001", "mobile": "+90 555 1002",
         "address": "أنقرة، تركيا", "city": "أنقرة", "country": "تركيا",
         "tax_number": "1234567890", "contact_person": "أحمد محمد",
         "credit_limit": 100000, "payment_terms": 30, "branch_id": 1, "currency": "TRY",
         "group_id": group_ids.get("عملاء محليون")},
        {"name": "مؤسسة الحلول الذكية", "name_en": "Smart Solutions Est.",
         "email": "info@smartsol.com", "phone": "+90 555 2001",
         "address": "إسطنبول، تركيا", "city": "إسطنبول", "country": "تركيا",
         "tax_number": "0987654321", "credit_limit": 50000, "payment_terms": 15,
         "branch_id": 1, "currency": "TRY",
         "group_id": group_ids.get("عملاء محليون")},
        {"name": "Global Trading LLC", "name_en": "Global Trading LLC",
         "email": "info@globaltrading.com", "phone": "+1 555 3001",
         "address": "New York, USA", "city": "New York", "country": "USA",
         "tax_number": "US-123456789", "credit_limit": 200000, "payment_terms": 45,
         "branch_id": 1, "currency": "USD",
         "group_id": group_ids.get("عملاء دوليون")},
        {"name": "EuroTech GmbH", "name_en": "EuroTech GmbH",
         "email": "info@eurotech.de", "phone": "+49 555 4001",
         "address": "Berlin, Germany", "city": "Berlin", "country": "Germany",
         "tax_number": "DE-987654321", "credit_limit": 150000, "payment_terms": 60,
         "branch_id": 1, "currency": "EUR",
         "group_id": group_ids.get("عملاء دوليون")},
        {"name": "شركة الخليج للتجارة", "name_en": "Gulf Trading Co.",
         "email": "info@gulftrading.ae", "phone": "+971 555 5001",
         "address": "دبي، الإمارات", "city": "دبي", "country": "الإمارات",
         "tax_number": "AE-555999888", "credit_limit": 300000, "payment_terms": 30,
         "branch_id": 3, "currency": "AED",
         "group_id": group_ids.get("عملاء VIP")},
    ]
    
    ids = {}
    for c in customers:
        code, resp = api_post("/sales/customers", c, c["name"])
        if code < 300:
            ids[c["name"]] = resp.get("id", resp.get("customer_id"))
    return ids

# ============================================================
# 6. SUPPLIER GROUPS & SUPPLIERS
# ============================================================
def setup_suppliers():
    print("\n" + "="*60)
    print("🏢 SUPPLIERS")
    print("="*60)
    
    suppliers = [
        {"supplier_name": "شركة الإمداد التقني", "supplier_name_en": "Tech Supply Co.",
         "email": "info@techsupply.com", "phone": "+90 555 6001",
         "address": "أنقرة، تركيا", "tax_number": "TR-111222333", "branch_id": 1},
        {"supplier_name": "مصنع المعدات الصناعية", "supplier_name_en": "Industrial Equipment Factory",
         "email": "info@indequip.com", "phone": "+90 555 7001",
         "address": "إسطنبول، تركيا", "tax_number": "TR-444555666", "branch_id": 1},
        {"supplier_name": "Dell Technologies", "supplier_name_en": "Dell Technologies",
         "email": "orders@dell.com", "phone": "+1 555 8001",
         "address": "Texas, USA", "tax_number": "US-777888999", "branch_id": 1},
        {"supplier_name": "Samsung Electronics", "supplier_name_en": "Samsung Electronics",
         "email": "b2b@samsung.com", "phone": "+82 555 9001",
         "address": "Seoul, South Korea", "tax_number": "KR-111000222", "branch_id": 1},
    ]
    
    ids = {}
    for s in suppliers:
        code, resp = api_post("/buying/suppliers", s, s["supplier_name"])
        if code < 300:
            ids[s["supplier_name"]] = resp.get("id", resp.get("supplier_id"))
    return ids

# ============================================================
# 7. HR: DEPARTMENTS, POSITIONS, EMPLOYEES
# ============================================================
def setup_hr():
    print("\n" + "="*60)
    print("👤 HR: DEPARTMENTS & EMPLOYEES")
    print("="*60)
    
    # Departments
    departments = [
        {"name": "الإدارة العامة", "name_en": "General Management"},
        {"name": "المحاسبة والمالية", "name_en": "Accounting & Finance"},
        {"name": "المبيعات", "name_en": "Sales"},
        {"name": "المشتريات", "name_en": "Purchasing"},
        {"name": "المستودعات", "name_en": "Warehousing"},
        {"name": "تقنية المعلومات", "name_en": "IT"},
    ]
    dept_ids = {}
    for d in departments:
        code, resp = api_post("/hr/departments", d, d["name"])
        if code < 300:
            dept_ids[d["name"]] = resp.get("id", resp.get("department_id"))
    
    # Employees
    employees = [
        {"first_name": "أحمد", "last_name": "الشريف", "first_name_en": "Ahmed", "last_name_en": "Al-Sharif",
         "email": "ahmed@company.com", "phone": "+90 555 1111",
         "position_title": "مدير عام", "department_name": "الإدارة العامة",
         "salary": 25000, "housing_allowance": 5000, "transport_allowance": 2000, "other_allowances": 3000,
         "hire_date": "2024-01-01", "branch_id": 1, "create_ledger": True},
        {"first_name": "محمد", "last_name": "العتيبي", "first_name_en": "Mohammed", "last_name_en": "Al-Otaibi",
         "email": "mohammed@company.com", "phone": "+90 555 2222",
         "position_title": "محاسب رئيسي", "department_name": "المحاسبة والمالية",
         "salary": 15000, "housing_allowance": 3000, "transport_allowance": 1500, "other_allowances": 1000,
         "hire_date": "2024-03-01", "branch_id": 1, "create_ledger": True},
        {"first_name": "فاطمة", "last_name": "الزهراني", "first_name_en": "Fatima", "last_name_en": "Al-Zahrani",
         "email": "fatima@company.com", "phone": "+90 555 3333",
         "position_title": "مديرة مبيعات", "department_name": "المبيعات",
         "salary": 12000, "housing_allowance": 2500, "transport_allowance": 1500, "other_allowances": 1000,
         "hire_date": "2024-06-01", "branch_id": 1, "create_ledger": True},
        {"first_name": "خالد", "last_name": "القحطاني", "first_name_en": "Khaled", "last_name_en": "Al-Qahtani",
         "email": "khaled@company.com", "phone": "+90 555 4444",
         "position_title": "مسؤول مشتريات", "department_name": "المشتريات",
         "salary": 10000, "housing_allowance": 2000, "transport_allowance": 1000, "other_allowances": 500,
         "hire_date": "2024-04-01", "branch_id": 1, "create_ledger": True},
        {"first_name": "سارة", "last_name": "المالكي", "first_name_en": "Sarah", "last_name_en": "Al-Malki",
         "email": "sarah@company.com", "phone": "+90 555 5555",
         "position_title": "أمينة مستودع", "department_name": "المستودعات",
         "salary": 8000, "housing_allowance": 1500, "transport_allowance": 1000, "other_allowances": 500,
         "hire_date": "2024-07-01", "branch_id": 2, "create_ledger": True},
        {"first_name": "عمر", "last_name": "الحربي", "first_name_en": "Omar", "last_name_en": "Al-Harbi",
         "email": "omar.h@company.com", "phone": "+90 555 6666",
         "position_title": "مندوب مبيعات", "department_name": "المبيعات",
         "salary": 7000, "housing_allowance": 1500, "transport_allowance": 1000, "other_allowances": 500,
         "hire_date": "2025-01-01", "branch_id": 2, "create_ledger": True},
        {"first_name": "نورة", "last_name": "السبيعي", "first_name_en": "Noura", "last_name_en": "Al-Subaie",
         "email": "noura@company.com", "phone": "+971 555 7777",
         "position_title": "مديرة فرع دبي", "department_name": "الإدارة العامة",
         "salary": 18000, "housing_allowance": 4000, "transport_allowance": 2000, "other_allowances": 2000,
         "hire_date": "2024-09-01", "branch_id": 3, "create_ledger": True},
        {"first_name": "يوسف", "last_name": "الدوسري", "first_name_en": "Yousef", "last_name_en": "Al-Dosari",
         "email": "yousef@company.com", "phone": "+90 555 8888",
         "position_title": "فني IT", "department_name": "تقنية المعلومات",
         "salary": 9000, "housing_allowance": 2000, "transport_allowance": 1000, "other_allowances": 500,
         "hire_date": "2025-02-01", "branch_id": 1, "create_ledger": True},
    ]
    
    emp_ids = {}
    for e in employees:
        code, resp = api_post("/hr/employees", e, f"{e['first_name']} {e['last_name']}")
        if code < 300:
            emp_ids[f"{e['first_name']} {e['last_name']}"] = resp.get("id", resp.get("employee_id"))
    return dept_ids, emp_ids

# ============================================================
# 8. PURCHASE ORDERS (with receiving)
# ============================================================
def execute_purchases(supplier_ids, product_ids, warehouse_ids):
    print("\n" + "="*60)
    print("🛒 PURCHASE ORDERS")
    print("="*60)
    
    # Get actual IDs
    suppliers = api_get("/buying/suppliers")
    supp_list = suppliers if isinstance(suppliers, list) else suppliers.get("items", suppliers.get("suppliers", []))
    supp_map = {s.get("supplier_name", s.get("name", "")): s["id"] for s in supp_list}
    
    products = api_get("/inventory/products")
    prod_list = products if isinstance(products, list) else products.get("items", products.get("products", []))
    prod_map = {p.get("item_code", ""): p["id"] for p in prod_list}
    
    warehouses = api_get("/inventory/warehouses")
    wh_list = warehouses if isinstance(warehouses, list) else warehouses.get("items", warehouses.get("warehouses", []))
    wh_map = {w.get("name", ""): w["id"] for w in wh_list}
    
    print(f"\n  Suppliers found: {list(supp_map.keys())}")
    print(f"  Products found: {list(prod_map.keys())}")
    print(f"  Warehouses found: {list(wh_map.keys())}")
    
    # PO1: Large electronics order from Dell, TRY, Main Branch
    po1_supp = supp_map.get("Dell Technologies", list(supp_map.values())[2] if len(supp_map) > 2 else 1)
    po1 = {
        "supplier_id": po1_supp,
        "order_date": "2026-02-01",
        "expected_date": "2026-02-15",
        "items": [
            {"product_id": prod_map.get("PROD001"), "description": "لابتوب HP ProBook", "quantity": 20, "unit_price": 3500, "tax_rate": 18.0},
            {"product_id": prod_map.get("PROD002"), "description": "شاشة سامسونج 27 بوصة", "quantity": 30, "unit_price": 1000, "tax_rate": 18.0},
            {"product_id": prod_map.get("PROD003"), "description": "طابعة HP LaserJet", "quantity": 10, "unit_price": 1400, "tax_rate": 18.0},
        ],
        "notes": "طلب شراء أجهزة إلكترونية - الدفعة الأولى",
        "branch_id": 1,
        "currency": "TRY",
        "exchange_rate": 1.0
    }
    code1, resp1 = api_post("/buying/orders", po1, "PO#1: Electronics order (TRY)")
    po1_id = resp1.get("id", resp1.get("order_id"))
    
    # PO2: Office supplies, Main branch
    po2_supp = supp_map.get("شركة الإمداد التقني", list(supp_map.values())[0] if supp_map else 1)
    po2 = {
        "supplier_id": po2_supp,
        "order_date": "2026-02-05",
        "expected_date": "2026-02-10",
        "items": [
            {"product_id": prod_map.get("PROD004"), "description": "ورق طباعة A4", "quantity": 100, "unit_price": 20, "tax_rate": 18.0},
            {"product_id": prod_map.get("PROD005"), "description": "حبر طابعة HP", "quantity": 50, "unit_price": 130, "tax_rate": 18.0},
            {"product_id": prod_map.get("PROD006"), "description": "كرسي مكتبي", "quantity": 15, "unit_price": 500, "tax_rate": 18.0},
            {"product_id": prod_map.get("PROD007"), "description": "مكتب خشبي", "quantity": 10, "unit_price": 750, "tax_rate": 18.0},
        ],
        "notes": "طلب مستلزمات مكتبية",
        "branch_id": 1,
        "currency": "TRY",
        "exchange_rate": 1.0
    }
    code2, resp2 = api_post("/buying/orders", po2, "PO#2: Office supplies (TRY)")
    po2_id = resp2.get("id", resp2.get("order_id"))
    
    # PO3: Electronics for Jeddah branch
    po3_supp = supp_map.get("Samsung Electronics", list(supp_map.values())[3] if len(supp_map) > 3 else 1)
    po3 = {
        "supplier_id": po3_supp,
        "order_date": "2026-02-10",
        "expected_date": "2026-02-25",
        "items": [
            {"product_id": prod_map.get("PROD001"), "description": "لابتوب HP ProBook", "quantity": 10, "unit_price": 3600, "tax_rate": 18.0},
            {"product_id": prod_map.get("PROD002"), "description": "شاشة سامسونج 27 بوصة", "quantity": 15, "unit_price": 950, "tax_rate": 18.0},
        ],
        "notes": "طلب أجهزة لفرع جدة",
        "branch_id": 2,
        "currency": "TRY",
        "exchange_rate": 1.0
    }
    code3, resp3 = api_post("/buying/orders", po3, "PO#3: Electronics for Jeddah (TRY)")
    po3_id = resp3.get("id", resp3.get("order_id"))
    
    # PO4: Foreign currency order (USD)
    po4 = {
        "supplier_id": po2_supp,
        "order_date": "2026-02-15",
        "expected_date": "2026-03-01",
        "items": [
            {"product_id": prod_map.get("PROD003"), "description": "طابعة HP LaserJet - USD", "quantity": 5, "unit_price": 450, "tax_rate": 18.0},
        ],
        "notes": "طلب بالدولار الأمريكي",
        "branch_id": 1,
        "currency": "USD",
        "exchange_rate": 32.25
    }
    code4, resp4 = api_post("/buying/orders", po4, "PO#4: USD order")
    po4_id = resp4.get("id", resp4.get("order_id"))
    
    # Approve POs
    print("\n  --- Approving POs ---")
    po_ids = [po1_id, po2_id, po3_id, po4_id]
    for pid in po_ids:
        if pid:
            api_post(f"/buying/orders/{pid}/approve", {}, f"Approve PO#{pid}")
    
    # Receive POs
    print("\n  --- Receiving POs ---")
    
    # Get PO details to find line IDs
    for pid in po_ids:
        if not pid:
            continue
        po = api_get(f"/buying/orders/{pid}")
        if isinstance(po, dict):
            lines = po.get("items", po.get("lines", []))
            if lines:
                wh_id = wh_map.get("المستودع الرئيسي", 1)
                if po.get("branch_id") == 2:
                    wh_id = wh_map.get("مستودع جدة", wh_id)
                receive_items = [{"line_id": line.get("id", line.get("line_id")), "received_quantity": line.get("quantity", 0)} for line in lines if line.get("id") or line.get("line_id")]
                if receive_items:
                    recv = {
                        "items": receive_items,
                        "warehouse_id": wh_id,
                        "notes": f"استلام أمر شراء #{pid}"
                    }
                    api_post(f"/buying/orders/{pid}/receive", recv, f"Receive PO#{pid}")
    
    return po_ids

# ============================================================
# 9. SALES ORDERS
# ============================================================
def execute_sales(customer_ids, product_ids):
    print("\n" + "="*60)
    print("💰 SALES ORDERS")
    print("="*60)
    
    # Get IDs
    customers = api_get("/sales/customers")
    cust_list = customers if isinstance(customers, list) else customers.get("items", customers.get("customers", []))
    cust_map = {c.get("name", ""): c["id"] for c in cust_list}
    
    products = api_get("/inventory/products")
    prod_list = products if isinstance(products, list) else products.get("items", products.get("products", []))
    prod_map = {p.get("item_code", ""): p["id"] for p in prod_list}
    
    warehouses = api_get("/inventory/warehouses")
    wh_list = warehouses if isinstance(warehouses, list) else warehouses.get("items", warehouses.get("warehouses", []))
    wh_map = {w.get("name", ""): w["id"] for w in wh_list}
    
    print(f"\n  Customers found: {list(cust_map.keys())}")
    
    # SO1: Local sale - TRY
    so1_cust = cust_map.get("شركة التقنية المتقدمة", list(cust_map.values())[0] if cust_map else 1)
    so1 = {
        "customer_id": so1_cust,
        "order_date": "2026-02-20",
        "expected_delivery_date": "2026-02-25",
        "items": [
            {"product_id": prod_map.get("PROD001"), "description": "لابتوب HP ProBook", "quantity": 5, "unit_price": 5000, "tax_rate": 18.0},
            {"product_id": prod_map.get("PROD002"), "description": "شاشة سامسونج", "quantity": 10, "unit_price": 1500, "tax_rate": 18.0},
            {"product_id": prod_map.get("PROD003"), "description": "طابعة HP", "quantity": 3, "unit_price": 2000, "tax_rate": 18.0},
        ],
        "notes": "أمر بيع لشركة التقنية المتقدمة",
        "branch_id": 1,
        "warehouse_id": wh_map.get("المستودع الرئيسي", 1),
        "currency": "TRY",
        "exchange_rate": 1.0
    }
    code1, resp1 = api_post("/sales/orders", so1, "SO#1: Local TRY sale")
    so1_id = resp1.get("id", resp1.get("order_id"))
    
    # SO2: Local small sale
    so2_cust = cust_map.get("مؤسسة الحلول الذكية", list(cust_map.values())[1] if len(cust_map) > 1 else 1)
    so2 = {
        "customer_id": so2_cust,
        "order_date": "2026-02-22",
        "items": [
            {"product_id": prod_map.get("PROD004"), "description": "ورق طباعة A4", "quantity": 20, "unit_price": 30, "tax_rate": 18.0},
            {"product_id": prod_map.get("PROD005"), "description": "حبر طابعة HP", "quantity": 10, "unit_price": 200, "tax_rate": 18.0},
            {"product_id": prod_map.get("PROD006"), "description": "كرسي مكتبي", "quantity": 5, "unit_price": 800, "tax_rate": 18.0},
        ],
        "branch_id": 1,
        "warehouse_id": wh_map.get("المستودع الرئيسي", 1),
        "currency": "TRY"
    }
    code2, resp2 = api_post("/sales/orders", so2, "SO#2: Office supplies (TRY)")
    so2_id = resp2.get("id", resp2.get("order_id"))
    
    # SO3: International sale - USD
    so3_cust = cust_map.get("Global Trading LLC", list(cust_map.values())[2] if len(cust_map) > 2 else 1)
    so3 = {
        "customer_id": so3_cust,
        "order_date": "2026-02-25",
        "items": [
            {"product_id": prod_map.get("PROD001"), "description": "HP ProBook Laptop", "quantity": 8, "unit_price": 155, "tax_rate": 18.0},
            {"product_id": prod_map.get("PROD003"), "description": "HP LaserJet Printer", "quantity": 4, "unit_price": 62, "tax_rate": 18.0},
        ],
        "branch_id": 1,
        "warehouse_id": wh_map.get("المستودع الرئيسي", 1),
        "currency": "USD",
        "exchange_rate": 32.25
    }
    code3, resp3 = api_post("/sales/orders", so3, "SO#3: International USD sale")
    so3_id = resp3.get("id", resp3.get("order_id"))
    
    # SO4: EUR sale
    so4_cust = cust_map.get("EuroTech GmbH", list(cust_map.values())[3] if len(cust_map) > 3 else 1)
    so4 = {
        "customer_id": so4_cust,
        "order_date": "2026-03-01",
        "items": [
            {"product_id": prod_map.get("PROD001"), "description": "HP ProBook Laptop", "quantity": 3, "unit_price": 145, "tax_rate": 18.0},
            {"product_id": prod_map.get("PROD002"), "description": "Samsung Monitor", "quantity": 6, "unit_price": 44, "tax_rate": 18.0},
        ],
        "branch_id": 1,
        "warehouse_id": wh_map.get("المستودع الرئيسي", 1),
        "currency": "EUR",
        "exchange_rate": 37.0
    }
    code4, resp4 = api_post("/sales/orders", so4, "SO#4: EUR sale to Germany")
    so4_id = resp4.get("id", resp4.get("order_id"))
    
    # SO5: Dubai branch sale - AED
    so5_cust = cust_map.get("شركة الخليج للتجارة", list(cust_map.values())[4] if len(cust_map) > 4 else 1)
    so5 = {
        "customer_id": so5_cust,
        "order_date": "2026-03-05",
        "items": [
            {"product_id": prod_map.get("PROD001"), "description": "لابتوب HP ProBook", "quantity": 4, "unit_price": 1370, "tax_rate": 5.0},
            {"product_id": prod_map.get("PROD007"), "description": "مكتب خشبي", "quantity": 3, "unit_price": 330, "tax_rate": 5.0},
        ],
        "branch_id": 3,
        "warehouse_id": wh_map.get("مستودع دبي", 4),
        "currency": "AED",
        "exchange_rate": 8.69
    }
    code5, resp5 = api_post("/sales/orders", so5, "SO#5: Dubai AED sale")
    so5_id = resp5.get("id", resp5.get("order_id"))
    
    return [so1_id, so2_id, so3_id, so4_id, so5_id]

# ============================================================
# 10. TREASURY TRANSACTIONS (Expenses & Transfers)
# ============================================================
def execute_treasury():
    print("\n" + "="*60)
    print("💳 TREASURY TRANSACTIONS")
    print("="*60)
    
    # Get treasury accounts
    treasuries = api_get("/treasury/accounts")
    tr_list = treasuries if isinstance(treasuries, list) else treasuries.get("items", treasuries.get("accounts", []))
    tr_map = {t.get("name", ""): t["id"] for t in tr_list}
    print(f"  Treasury accounts: {list(tr_map.keys())}")
    
    # Get accounts for expenses
    accounts = api_get("/accounting/accounts")
    acc_list = accounts if isinstance(accounts, list) else accounts.get("items", [])
    acc_map = {a.get("account_code", ""): a["id"] for a in acc_list}
    
    # Expense transactions
    expenses = [
        {"transaction_date": "2026-02-01", "transaction_type": "expense", "amount": 5000,
         "treasury_id": tr_map.get("الصندوق الرئيسي", 1),
         "target_account_id": acc_map.get("RNT"),
         "description": "إيجار المقر الرئيسي - فبراير 2026", "branch_id": 1},
        {"transaction_date": "2026-02-01", "transaction_type": "expense", "amount": 1200,
         "treasury_id": tr_map.get("الصندوق الرئيسي", 1),
         "target_account_id": acc_map.get("UTL"),
         "description": "فاتورة كهرباء ومياه - يناير", "branch_id": 1},
        {"transaction_date": "2026-02-05", "transaction_type": "expense", "amount": 800,
         "treasury_id": tr_map.get("الصندوق الرئيسي", 1),
         "target_account_id": acc_map.get("COM"),
         "description": "اتصالات وإنترنت - فبراير", "branch_id": 1},
        {"transaction_date": "2026-02-10", "transaction_type": "expense", "amount": 2000,
         "treasury_id": tr_map.get("صندوق جدة", 2),
         "target_account_id": acc_map.get("RNT"),
         "description": "إيجار فرع جدة - فبراير", "branch_id": 2},
        {"transaction_date": "2026-02-10", "transaction_type": "expense", "amount": 500,
         "treasury_id": tr_map.get("صندوق جدة", 2),
         "target_account_id": acc_map.get("CLEAN"),
         "description": "مصروف نظافة - فرع جدة", "branch_id": 2},
        {"transaction_date": "2026-02-15", "transaction_type": "expense", "amount": 3500,
         "treasury_id": tr_map.get("صندوق دبي", 3),
         "target_account_id": acc_map.get("RNT"),
         "description": "إيجار فرع دبي - فبراير (AED)", "branch_id": 3, "exchange_rate": 0.115},
    ]
    
    for exp in expenses:
        api_post("/treasury/transactions/expense", exp, exp["description"][:40])
    
    # Transfer transactions
    transfers = [
        {"transaction_date": "2026-02-12", "transaction_type": "transfer", "amount": 10000,
         "treasury_id": tr_map.get("الصندوق الرئيسي", 1),
         "target_treasury_id": tr_map.get("بنك الأهلي - حساب جاري", 4),
         "description": "تحويل من الصندوق للبنك الأهلي", "branch_id": 1},
        {"transaction_date": "2026-02-15", "transaction_type": "transfer", "amount": 5000,
         "treasury_id": tr_map.get("بنك الراجحي", 5),
         "target_treasury_id": tr_map.get("صندوق جدة", 2),
         "description": "تحويل من الراجحي لصندوق جدة", "branch_id": 1},
    ]
    
    for tr in transfers:
        api_post("/treasury/transactions/transfer", tr, tr["description"][:40])

# ============================================================
# 11. EXPENSES MODULE
# ============================================================
def execute_expenses():
    print("\n" + "="*60)
    print("📋 EXPENSES MODULE")
    print("="*60)
    
    # Get treasury IDs
    treasuries = api_get("/treasury/accounts")
    tr_list = treasuries if isinstance(treasuries, list) else treasuries.get("items", [])
    tr_map = {t.get("name", ""): t["id"] for t in tr_list}
    
    expenses = [
        {"expense_date": "2026-02-01", "expense_type": "rent", "amount": 5000,
         "description": "إيجار مكتب إضافي", "category": "operational",
         "payment_method": "bank_transfer", "treasury_id": tr_map.get("بنك الأهلي - حساب جاري"),
         "branch_id": 1, "requires_approval": True, "vendor_name": "شركة العقارات"},
        {"expense_date": "2026-02-05", "expense_type": "marketing", "amount": 3000,
         "description": "حملة إعلانية رقمية", "category": "marketing",
         "payment_method": "bank_transfer", "treasury_id": tr_map.get("بنك الأهلي - حساب جاري"),
         "branch_id": 1, "requires_approval": True},
        {"expense_date": "2026-02-10", "expense_type": "travel", "amount": 2500,
         "description": "سفر عمل - معرض تقني", "category": "travel",
         "payment_method": "cash", "treasury_id": tr_map.get("الصندوق الرئيسي"),
         "branch_id": 1, "requires_approval": True, "receipt_number": "TRV-001"},
        {"expense_date": "2026-02-12", "expense_type": "maintenance", "amount": 1500,
         "description": "صيانة مكيفات المقر الرئيسي", "category": "maintenance",
         "payment_method": "cash", "treasury_id": tr_map.get("الصندوق الرئيسي"),
         "branch_id": 1, "requires_approval": False},
        {"expense_date": "2026-02-15", "expense_type": "utilities", "amount": 800,
         "description": "كهرباء فرع جدة", "category": "operational",
         "payment_method": "cash", "treasury_id": tr_map.get("صندوق جدة"),
         "branch_id": 2, "requires_approval": False},
        {"expense_date": "2026-02-20", "expense_type": "hospitality", "amount": 600,
         "description": "ضيافة اجتماع عملاء", "category": "general",
         "payment_method": "cash", "treasury_id": tr_map.get("الصندوق الرئيسي"),
         "branch_id": 1, "requires_approval": False, "vendor_name": "مطعم الضيافة"},
    ]
    
    exp_ids = []
    for e in expenses:
        code, resp = api_post("/expenses/", e, e["description"][:40])
        if code < 300:
            exp_ids.append(resp.get("id", resp.get("expense_id")))
    
    # Approve the ones requiring approval
    print("\n  --- Approving expenses ---")
    for eid in exp_ids[:3]:
        if eid:
            api_post(f"/expenses/{eid}/approve", {"status": "approved", "notes": "موافق"}, f"Approve expense #{eid}")
    
    return exp_ids

# ============================================================
# 12. FIXED ASSETS
# ============================================================
def execute_assets():
    print("\n" + "="*60)
    print("🏗️ FIXED ASSETS")
    print("="*60)
    
    assets = [
        {"name": "سيارة تويوتا كامري 2026", "code": "AST-VEH-001",
         "type": "vehicle", "purchase_date": "2026-01-15",
         "cost": 120000, "residual_value": 20000, "life_years": 5, "branch_id": 1,
         "depreciation_method": "straight_line"},
        {"name": "خادم Dell PowerEdge", "code": "AST-CMP-001",
         "type": "equipment", "purchase_date": "2026-01-20",
         "cost": 45000, "residual_value": 5000, "life_years": 4, "branch_id": 1,
         "depreciation_method": "straight_line"},
        {"name": "أثاث مكتبي - المقر الرئيسي", "code": "AST-FUR-001",
         "type": "furniture", "purchase_date": "2026-01-01",
         "cost": 30000, "residual_value": 3000, "life_years": 7, "branch_id": 1,
         "depreciation_method": "straight_line"},
        {"name": "طابعة صناعية", "code": "AST-MAC-001",
         "type": "equipment", "purchase_date": "2026-02-01",
         "cost": 80000, "residual_value": 8000, "life_years": 6, "branch_id": 1,
         "depreciation_method": "straight_line"},
        {"name": "أثاث مكتبي - فرع جدة", "code": "AST-FUR-002",
         "type": "furniture", "purchase_date": "2026-02-10",
         "cost": 15000, "residual_value": 1500, "life_years": 7, "branch_id": 2,
         "depreciation_method": "straight_line"},
        {"name": "سيارة نقل - دبي", "code": "AST-VEH-002",
         "type": "vehicle", "purchase_date": "2026-01-25",
         "cost": 8500, "residual_value": 1500, "life_years": 5, "branch_id": 3,
         "currency": "AED", "depreciation_method": "straight_line"},
    ]
    
    ids = []
    for a in assets:
        code, resp = api_post("/assets/", a, a["name"][:40])
        if code < 300:
            ids.append(resp.get("id", resp.get("asset_id")))
    return ids


# ============================================================
# MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    print("="*60)
    print("🚀 AMAN ERP - COMPREHENSIVE TEST DATA INSERTION")
    print(f"   Company: aman_80b0ada0")
    print(f"   Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*60)
    
    # Check auth
    me = api_get("/auth/me")
    if isinstance(me, dict) and me.get("username"):
        print(f"   Logged in as: {me['username']}")
    else:
        print("   ⚠ Not authenticated! Please login first.")
        sys.exit(1)
    
    # 1. Treasury
    treasury_ids = setup_treasury()
    
    # 2. Warehouses
    warehouse_ids = setup_warehouses()
    
    # 3. Categories
    cat_ids = setup_categories()
    
    # 4. Products
    product_ids = setup_products(cat_ids)
    
    # 5. Customers
    customer_ids = setup_customers()
    
    # 6. Suppliers
    supplier_ids = setup_suppliers()
    
    # 7. HR
    dept_ids, emp_ids = setup_hr()
    
    # 8. Purchases
    po_ids = execute_purchases(supplier_ids, product_ids, warehouse_ids)
    
    # 9. Sales
    so_ids = execute_sales(customer_ids, product_ids)
    
    # 10. Treasury transactions
    execute_treasury()
    
    # 11. Expenses
    exp_ids = execute_expenses()
    
    # 12. Assets
    asset_ids = execute_assets()
    
    print("\n" + "="*60)
    print("✅ DATA INSERTION COMPLETE!")
    print("="*60)
    print(f"  Treasury accounts: {len(treasury_ids)} created")
    print(f"  Warehouses: {len(warehouse_ids)} created")
    print(f"  Products: {len(product_ids)} created")
    print(f"  Customers: {len(customer_ids)} created")
    print(f"  Suppliers: {len(supplier_ids)} created")
    print(f"  Employees: {len(emp_ids)} created")
    print(f"  Purchase Orders: {len([x for x in po_ids if x])} created")
    print(f"  Sales Orders: {len([x for x in so_ids if x])} created")
    print(f"  Expenses: {len(exp_ids)} created")
    print(f"  Fixed Assets: {len(asset_ids)} created")
