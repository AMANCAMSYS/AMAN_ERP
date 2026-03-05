#!/usr/bin/env python3
"""
=============================================================================
 AMAN ERP — Comprehensive Data Seeding Script (v2 - resilient)
 Company: ba2f6dc3 on server 64.225.49.118
=============================================================================
 Uses create-then-read-back pattern since POST endpoints don't return IDs.
=============================================================================
"""

import requests, json, sys, time

API = "http://64.225.49.118/api"
COMPANY_CODE = "ba2f6dc3"
ADMIN_USER = "vvvv"
ADMIN_PASS = "As123321"
EMPLOYEE_PASSWORD = "Aman@2026"

# ── Helpers ──────────────────────────────────────────────────────────────────

def login():
    resp = requests.post(f"{API}/auth/login", data={
        "username": ADMIN_USER, "password": ADMIN_PASS, "company_code": COMPANY_CODE
    })
    if resp.status_code != 200:
        print(f"❌ Login failed: {resp.text}"); sys.exit(1)
    print(f"✅ Logged in as {ADMIN_USER}")
    return {"Authorization": f"Bearer {resp.json()['access_token']}", "Content-Type": "application/json"}

def post(endpoint, data, headers, label=""):
    """POST and return True/response on success, None on failure."""
    r = requests.post(f"{API}{endpoint}", json=data, headers=headers, timeout=30)
    if r.status_code in [200, 201]:
        print(f"  ✅ {label}")
        return r.json()
    else:
        print(f"  ⚠️ {label}: {r.status_code} - {r.text[:200]}")
        return None

def get(endpoint, headers, params=None):
    r = requests.get(f"{API}{endpoint}", headers=headers, timeout=30, params=params)
    if r.status_code == 200:
        data = r.json()
        if isinstance(data, dict):
            return data.get("items", data.get("data", data.get("employees", data.get("results", data))))
        return data
    return []

# ============================================================================
def main():
    H = login()
    ids = {}

    # ========================================================================
    #  PHASE 1: COMPANY SETTINGS
    # ========================================================================
    print("\n" + "=" * 60)
    print("  PHASE 1: COMPANY SETTINGS")
    print("=" * 60)
    
    settings_data = {
        "settings": {
            "company_name": "شركة أمان للتجارة والصناعة",
            "company_name_en": "Aman Trading & Manufacturing Co.",
            "company_email": "info@aman-erp.com",
            "company_phone": "+966501234567",
            "company_address": "حي العليا، شارع الملك فهد، الرياض",
            "tax_number": "300999888800003",
            "commercial_registry": "1010999888",
            "vat_enabled": "true",
            "vat_rate": "15",
            "multi_branch_enabled": "true",
            "show_logo_on_invoice": "true",
            "invoice_terms": "الدفع خلال 30 يوم من تاريخ الفاتورة",
            "invoice_footer": "شكراً لتعاملكم معنا - شركة أمان للتجارة والصناعة",
            "quotation_prefix": "QT-",
            "purchase_order_prefix": "PO-",
            "delivery_order_prefix": "DO-",
            "receipt_prefix": "RCV-",
            "payment_prefix": "PAY-",
        }
    }
    r = requests.post(f"{API}/settings/bulk", json=settings_data, headers=H)
    print(f"  {'✅' if r.status_code==200 else '⚠️'} Company settings updated")

    # ========================================================================
    #  PHASE 2: BRANCHES (read back IDs)
    # ========================================================================
    print("\n" + "=" * 60)
    print("  PHASE 2: BRANCHES")
    print("=" * 60)
    
    branches = [
        {"branch_name": "فرع جدة", "branch_name_en": "Jeddah Branch", "branch_code": "BR002",
         "city": "جدة", "country": "المملكة العربية السعودية", "country_code": "SA",
         "default_currency": "SAR", "phone": "+966126543210", "email": "jeddah@aman-erp.com", "is_active": True},
        {"branch_name": "فرع دبي", "branch_name_en": "Dubai Branch", "branch_code": "BR003",
         "city": "دبي", "country": "الإمارات العربية المتحدة", "country_code": "AE",
         "default_currency": "AED", "phone": "+97142345678", "email": "dubai@aman-erp.com", "is_active": True},
    ]
    for b in branches:
        post("/branches", b, H, b["branch_name"])
    
    # Read back
    all_branches = get("/branches", H)
    for br in all_branches:
        code = br.get("branch_code", "")
        ids[code] = br["id"]
    print(f"  📍 Branches: {[(b.get('branch_code','?'), b['id']) for b in all_branches]}")

    # ========================================================================
    #  PHASE 3: CURRENCIES & EXCHANGE RATES
    # ========================================================================
    print("\n" + "=" * 60)
    print("  PHASE 3: CURRENCIES & EXCHANGE RATES")
    print("=" * 60)
    
    currencies = [
        {"code": "USD", "name": "دولار أمريكي", "name_en": "US Dollar", "symbol": "$", "is_base": False, "current_rate": 3.75},
        {"code": "EUR", "name": "يورو", "name_en": "Euro", "symbol": "€", "is_base": False, "current_rate": 4.10},
        {"code": "AED", "name": "درهم إماراتي", "name_en": "UAE Dirham", "symbol": "د.إ", "is_base": False, "current_rate": 1.02},
        {"code": "EGP", "name": "جنيه مصري", "name_en": "Egyptian Pound", "symbol": "ج.م", "is_base": False, "current_rate": 0.077},
    ]
    for c in currencies:
        post("/accounting/currencies/", c, H, f"{c['code']} ({c['name']})")
    
    all_currencies = get("/accounting/currencies", H)
    for cur in all_currencies:
        ids[f"curr_{cur['code']}"] = cur["id"]
    
    print("  --- Exchange Rates ---")
    for code, rate in [("USD", 3.75), ("EUR", 4.10), ("AED", 1.02), ("EGP", 0.077)]:
        cid = ids.get(f"curr_{code}")
        if cid:
            post("/accounting/currencies/rates", {
                "currency_id": cid, "rate": rate, "rate_date": "2026-03-05", "source": "manual"
            }, H, f"Rate {code} = {rate}")

    # ========================================================================
    #  PHASE 4: ADDITIONAL CHART OF ACCOUNTS
    # ========================================================================
    print("\n" + "=" * 60)
    print("  PHASE 4: ADDITIONAL CHART OF ACCOUNTS (to reach 121)")
    print("=" * 60)
    
    new_accounts = [
        {"name": "حساب بنك الراجحي", "name_en": "Al Rajhi Bank", "account_number": "110103", "account_code": "RAJHI", "account_type": "asset", "parent_id": 7, "currency": "SAR"},
        {"name": "حساب بنك الأهلي", "name_en": "NCB Bank", "account_number": "110104", "account_code": "NCB", "account_type": "asset", "parent_id": 7, "currency": "SAR"},
        {"name": "حساب بنك الإنماء", "name_en": "Alinma Bank", "account_number": "110105", "account_code": "INMA", "account_type": "asset", "parent_id": 7, "currency": "SAR"},
        {"name": "حساب بنك الإمارات دبي الوطني", "name_en": "Emirates NBD", "account_number": "110106", "account_code": "ENBD", "account_type": "asset", "parent_id": 7, "currency": "AED"},
        {"name": "صندوق فرع جدة", "name_en": "Jeddah Cash Box", "account_number": "110107", "account_code": "BOX-JED", "account_type": "asset", "parent_id": 7, "currency": "SAR"},
        {"name": "صندوق فرع دبي", "name_en": "Dubai Cash Box", "account_number": "110108", "account_code": "BOX-DXB", "account_type": "asset", "parent_id": 7, "currency": "AED"},
        {"name": "مصروف العمولات والحوافز", "name_en": "Commissions & Incentives", "account_number": "5224", "account_code": "COMMN", "account_type": "expense", "parent_id": 60, "currency": "SAR"},
    ]
    for acc in new_accounts:
        post("/accounting/accounts", acc, H, acc["name"])
    
    # Read back accounts and map codes to IDs
    all_accounts = get("/accounting/accounts", H)
    for a in all_accounts:
        if a.get("account_code"):
            ids[f"acc_{a['account_code']}"] = a["id"]
    print(f"  📊 Total accounts: {len(all_accounts)}")

    # ========================================================================
    #  PHASE 5: FISCAL YEAR
    # ========================================================================
    print("\n" + "=" * 60)
    print("  PHASE 5: FISCAL YEAR & PERIODS")
    print("=" * 60)
    
    post("/accounting/fiscal-years", {
        "year": 2026, "start_date": "2026-01-01", "end_date": "2026-12-31",
    }, H, "السنة المالية 2026")

    # ========================================================================
    #  PHASE 6: DEPARTMENTS
    # ========================================================================
    print("\n" + "=" * 60)
    print("  PHASE 6: DEPARTMENTS")
    print("=" * 60)
    
    dept_names = [
        "الإدارة المالية", "المبيعات", "المشتريات",
        "المستودعات", "الموارد البشرية", "الإنتاج والتصنيع", "نقاط البيع"
    ]
    dept_keys = ["finance", "sales", "purchasing", "warehouse", "hr", "manufacturing", "pos"]
    
    for name in dept_names:
        post("/hr/departments", {"department_name": name}, H, name)
    
    # Read back
    all_depts = get("/hr/departments", H)
    dept_name_to_key = dict(zip(dept_names, dept_keys))
    for d in all_depts:
        key = dept_name_to_key.get(d["department_name"])
        if key:
            ids[f"dept_{key}"] = d["id"]
    print(f"  📊 Departments: {len(all_depts)} | IDs: {[(k,v) for k,v in ids.items() if k.startswith('dept_')]}")

    # ========================================================================
    #  PHASE 7: POSITIONS
    # ========================================================================
    print("\n" + "=" * 60)
    print("  PHASE 7: POSITIONS")
    print("=" * 60)
    
    positions = [
        ("مدير مالي", "dept_finance", "cfo"),
        ("محاسب", "dept_finance", "accountant"),
        ("مدير مبيعات", "dept_sales", "sales_mgr"),
        ("مندوب مبيعات", "dept_sales", "sales_rep"),
        ("مدير مشتريات", "dept_purchasing", "purchase_mgr"),
        ("أمين مستودع", "dept_warehouse", "warehouse_keeper"),
        ("مدير موارد بشرية", "dept_hr", "hr_mgr"),
        ("كاشير", "dept_pos", "cashier"),
    ]
    for pname, dept_key, pos_key in positions:
        post("/hr/positions", {
            "position_name": pname,
            "department_id": ids.get(dept_key),
        }, H, pname)
    
    # Read back
    all_positions = get("/hr/positions", H)
    pos_name_to_key = {p[0]: p[2] for p in positions}
    for p in all_positions:
        key = pos_name_to_key.get(p.get("position_name"))
        if key:
            ids[f"pos_{key}"] = p["id"]
    print(f"  📊 Positions: {len(all_positions)}")

    # ========================================================================
    #  PHASE 8: PRODUCT CATEGORIES
    # ========================================================================
    print("\n" + "=" * 60)
    print("  PHASE 8: PRODUCT CATEGORIES")
    print("=" * 60)
    
    categories = [
        ("مواد خام", "CAT-RAW"),
        ("منتجات تامة الصنع", "CAT-FIN"),
        ("مستلزمات", "CAT-SUP"),
        ("خدمات", "CAT-SRV"),
        ("أصول ثابتة", "CAT-FA"),
    ]
    for cname, ccode in categories:
        post("/inventory/categories", {"name": cname, "code": ccode}, H, cname)
    
    all_cats = get("/inventory/categories", H)
    cat_name_to_code = dict(categories)
    for c in all_cats:
        code = cat_name_to_code.get(c.get("name"))
        if code:
            ids[f"cat_{code}"] = c["id"]
    print(f"  📊 Categories: {len(all_cats)}")

    # ========================================================================
    #  PHASE 9: PRODUCTS
    # ========================================================================
    print("\n" + "=" * 60)
    print("  PHASE 9: PRODUCTS (7)")
    print("=" * 60)
    
    products = [
        {"item_code": "PRD-001", "item_name": "ألمنيوم", "item_name_en": "Aluminum",
         "item_type": "product", "unit": "كيلوغرام", "buying_price": 45.0, "selling_price": 75.0,
         "tax_rate": 15.0, "category_id": ids.get("cat_CAT-RAW")},
        {"item_code": "PRD-002", "item_name": "خشب طبيعي", "item_name_en": "Natural Wood",
         "item_type": "product", "unit": "متر", "buying_price": 120.0, "selling_price": 200.0,
         "tax_rate": 15.0, "category_id": ids.get("cat_CAT-RAW")},
        {"item_code": "PRD-003", "item_name": "باب ألمنيوم", "item_name_en": "Aluminum Door",
         "item_type": "product", "unit": "قطعة", "buying_price": 850.0, "selling_price": 1500.0,
         "tax_rate": 15.0, "category_id": ids.get("cat_CAT-FIN")},
        {"item_code": "PRD-004", "item_name": "نافذة ألمنيوم", "item_name_en": "Aluminum Window",
         "item_type": "product", "unit": "قطعة", "buying_price": 450.0, "selling_price": 800.0,
         "tax_rate": 15.0, "category_id": ids.get("cat_CAT-FIN")},
        {"item_code": "PRD-005", "item_name": "مسامير وبراغي", "item_name_en": "Screws & Bolts",
         "item_type": "product", "unit": "صندوق", "buying_price": 25.0, "selling_price": 50.0,
         "tax_rate": 15.0, "category_id": ids.get("cat_CAT-SUP")},
        {"item_code": "PRD-006", "item_name": "لابتوب", "item_name_en": "Laptop",
         "item_type": "product", "unit": "قطعة", "buying_price": 3500.0, "selling_price": 5000.0,
         "tax_rate": 15.0, "category_id": ids.get("cat_CAT-FA")},
        {"item_code": "PRD-007", "item_name": "خدمة تركيب", "item_name_en": "Installation Service",
         "item_type": "service", "unit": "قطعة", "buying_price": 0.0, "selling_price": 500.0,
         "tax_rate": 15.0, "category_id": ids.get("cat_CAT-SRV")},
    ]
    for prod in products:
        post("/inventory/products", prod, H, prod["item_name"])
    
    all_products = get("/inventory/products", H)
    if isinstance(all_products, list):
        for p in all_products:
            ids[f"prod_{p.get('item_code','')}"] = p["id"]
        print(f"  📊 Products: {len(all_products)}")
    else:
        print(f"  📊 Products response: {str(all_products)[:200]}")

    # ========================================================================
    #  PHASE 10: WAREHOUSES
    # ========================================================================
    print("\n" + "=" * 60)
    print("  PHASE 10: WAREHOUSES (4 new)")
    print("=" * 60)
    
    warehouses = [
        {"name": "مستودع المواد الخام", "code": "WH-RAW", "branch_id": ids.get("BR001", 1)},
        {"name": "مستودع المنتجات التامة", "code": "WH-FIN", "branch_id": ids.get("BR001", 1)},
        {"name": "مستودع فرع جدة", "code": "WH-JED", "branch_id": ids.get("BR002")},
        {"name": "مستودع فرع دبي", "code": "WH-DXB", "branch_id": ids.get("BR003")},
    ]
    for w in warehouses:
        post("/inventory/warehouses", w, H, w["name"])
    
    all_wh = get("/inventory/warehouses", H)
    for w in all_wh:
        ids[f"wh_{w.get('code','')}"] = w["id"]
    print(f"  📊 Warehouses: {len(all_wh)}")

    # ========================================================================
    #  PHASE 11: CUSTOMER & SUPPLIER GROUPS
    # ========================================================================
    print("\n" + "=" * 60)
    print("  PHASE 11: CUSTOMER & SUPPLIER GROUPS")
    print("=" * 60)
    
    cg_data = [
        {"group_name": "عملاء الجملة", "group_name_en": "Wholesale Customers",
         "description": "عملاء يحصلون على خصم 5%", "discount_percentage": 5.0,
         "effect_type": "discount", "application_scope": "total", "payment_days": 30},
        {"group_name": "عملاء التجزئة", "group_name_en": "Retail Customers",
         "description": "عملاء التجزئة - بدون خصم", "discount_percentage": 0.0, "payment_days": 0},
        {"group_name": "عملاء خارجيون", "group_name_en": "International Customers",
         "description": "عملاء من خارج المملكة - خصم 3%", "discount_percentage": 3.0,
         "effect_type": "discount", "application_scope": "total", "payment_days": 45},
    ]
    for cg in cg_data:
        post("/sales/customer-groups", cg, H, cg["group_name"])
    
    all_cg = get("/sales/customer-groups", H)
    cg_name_map = {"عملاء الجملة": "wholesale", "عملاء التجزئة": "retail", "عملاء خارجيون": "international"}
    for cg in all_cg:
        key = cg_name_map.get(cg.get("group_name"))
        if key:
            ids[f"cg_{key}"] = cg["id"]
    print(f"  📊 Customer Groups: {len(all_cg)}")
    
    sg_data = [
        {"group_name": "موردون محليون", "group_name_en": "Local Suppliers",
         "description": "موردون داخل المملكة", "discount_percentage": 0.0, "payment_days": 30},
        {"group_name": "موردون خارجيون", "group_name_en": "International Suppliers",
         "description": "موردون من خارج المملكة", "discount_percentage": 0.0, "payment_days": 60},
    ]
    for sg in sg_data:
        post("/buying/supplier-groups", sg, H, sg["group_name"])
    
    all_sg = get("/buying/supplier-groups", H)
    sg_name_map = {"موردون محليون": "local", "موردون خارجيون": "international"}
    for sg in all_sg:
        key = sg_name_map.get(sg.get("group_name"))
        if key:
            ids[f"sg_{key}"] = sg["id"]
    print(f"  📊 Supplier Groups: {len(all_sg)}")

    # ========================================================================
    #  PHASE 12: CUSTOMERS (6)
    # ========================================================================
    print("\n" + "=" * 60)
    print("  PHASE 12: CUSTOMERS (6)")
    print("=" * 60)
    
    customers = [
        {"name": "شركة الوفاء التجارية", "name_en": "Al-Wafaa Trading Co.",
         "email": "info@wafaa.sa", "phone": "+966114567890", "mobile": "+966561234567",
         "city": "الرياض", "country": "SA", "tax_number": "300098765400001",
         "credit_limit": 500000, "payment_terms": 30,
         "group_id": ids.get("cg_wholesale"), "branch_id": ids.get("BR001", 1), "currency": "SAR"},
        {"name": "مؤسسة النور للمقاولات", "name_en": "Al-Nour Contracting",
         "email": "info@alnour.sa", "phone": "+966127654321",
         "city": "جدة", "country": "SA", "tax_number": "300098765400002",
         "credit_limit": 300000, "payment_terms": 30,
         "group_id": ids.get("cg_wholesale"), "branch_id": ids.get("BR001", 1), "currency": "SAR"},
        {"name": "شركة البناء الحديث", "name_en": "Modern Build Co.",
         "email": "info@modernbuild.sa", "phone": "+966138765432",
         "city": "الدمام", "country": "SA",
         "credit_limit": 200000, "payment_terms": 30,
         "group_id": ids.get("cg_wholesale"), "branch_id": ids.get("BR001", 1), "currency": "SAR"},
        {"name": "عبدالله المطيري", "name_en": "Abdullah Al-Mutairi",
         "phone": "+966555667788",
         "city": "الرياض", "country": "SA",
         "credit_limit": 50000, "payment_terms": 0,
         "group_id": ids.get("cg_retail"), "branch_id": ids.get("BR001", 1), "currency": "SAR"},
        {"name": "مجموعة الرشيد الدولية", "name_en": "Al-Rashid International Group",
         "email": "info@rashid.ae", "phone": "+97142345678",
         "city": "دبي", "country": "AE",
         "credit_limit": 1000000, "payment_terms": 45,
         "group_id": ids.get("cg_international"), "branch_id": ids.get("BR003"), "currency": "AED"},
        {"name": "مؤسسة الخليج للتوريدات", "name_en": "Gulf Supplies Est.",
         "email": "info@gulfsupplies.sa", "phone": "+966133445566",
         "city": "الخبر", "country": "SA",
         "credit_limit": 150000, "payment_terms": 15,
         "group_id": ids.get("cg_retail"), "branch_id": ids.get("BR001", 1), "currency": "SAR"},
    ]
    for cust in customers:
        post("/sales/customers", cust, H, cust["name"])
    
    all_cust = get("/sales/customers", H)
    if isinstance(all_cust, list):
        print(f"  📊 Customers: {len(all_cust)}")
    else:
        print(f"  📊 Customers response: {str(all_cust)[:200]}")

    # ========================================================================
    #  PHASE 13: SUPPLIERS (5)
    # ========================================================================
    print("\n" + "=" * 60)
    print("  PHASE 13: SUPPLIERS (5)")
    print("=" * 60)
    
    suppliers = [
        {"name": "مصنع الخليج للألمنيوم", "name_en": "Gulf Aluminum Factory",
         "email": "info@gulfalum.sa", "phone": "+966112223344",
         "address": "الرياض - المنطقة الصناعية", "tax_number": "300012345600001",
         "branch_id": ids.get("BR001", 1), "currency": "SAR", "group_id": ids.get("sg_local")},
        {"name": "شركة الأخشاب العربية", "name_en": "Arabian Wood Co.",
         "email": "info@arabwood.sa", "phone": "+966126543210",
         "address": "جدة - الميناء", "tax_number": "300012345600002",
         "branch_id": ids.get("BR001", 1), "currency": "SAR", "group_id": ids.get("sg_local")},
        {"name": "مؤسسة الحديد والصلب", "name_en": "Iron & Steel Est.",
         "email": "info@ironsteel.sa", "phone": "+966133445566",
         "address": "الدمام - المنطقة الصناعية الثانية", "tax_number": "300012345600003",
         "branch_id": ids.get("BR001", 1), "currency": "SAR", "group_id": ids.get("sg_local")},
        {"name": "شركة التقنية المتحدة", "name_en": "United Tech Solutions",
         "email": "info@unitedtech.sa", "phone": "+966114455667",
         "address": "الرياض - حي التقنية",
         "branch_id": ids.get("BR001", 1), "currency": "SAR", "group_id": ids.get("sg_local")},
        {"name": "مجموعة دبي للتجارة", "name_en": "Dubai Trading Group",
         "email": "info@dubaitrading.ae", "phone": "+97143456789",
         "address": "دبي - جبل علي",
         "branch_id": ids.get("BR003"), "currency": "AED", "group_id": ids.get("sg_international")},
    ]
    for sup in suppliers:
        post("/inventory/suppliers", sup, H, sup["name"])
    
    all_sup = get("/inventory/suppliers", H)
    if isinstance(all_sup, list):
        print(f"  📊 Suppliers: {len(all_sup)}")
    else:
        print(f"  📊 Suppliers response: {str(all_sup)[:200]}")

    # ========================================================================
    #  PHASE 14: TREASURY ACCOUNTS (7)
    # ========================================================================
    print("\n" + "=" * 60)
    print("  PHASE 14: TREASURY ACCOUNTS (7)")
    print("=" * 60)
    
    treasury_accounts = [
        {"name": "بنك الراجحي", "name_en": "Al Rajhi Bank",
         "account_type": "bank", "currency": "SAR",
         "branch_id": ids.get("BR001", 1), "bank_name": "بنك الراجحي",
         "account_number": "6800001234567", "iban": "SA44 8000 0068 0000 1234 5670", "opening_balance": 0},
        {"name": "البنك الأهلي السعودي", "name_en": "SNB (NCB)",
         "account_type": "bank", "currency": "SAR",
         "branch_id": ids.get("BR001", 1), "bank_name": "البنك الأهلي السعودي",
         "account_number": "1000009876543", "iban": "SA66 1000 0010 0000 9876 5430", "opening_balance": 0},
        {"name": "بنك الإنماء", "name_en": "Alinma Bank",
         "account_type": "bank", "currency": "SAR",
         "branch_id": ids.get("BR001", 1), "bank_name": "بنك الإنماء",
         "account_number": "0500006543210", "iban": "SA88 0500 0005 0000 6543 2100", "opening_balance": 0},
        {"name": "بنك الإمارات دبي الوطني", "name_en": "Emirates NBD",
         "account_type": "bank", "currency": "AED",
         "branch_id": ids.get("BR003"), "bank_name": "بنك الإمارات دبي الوطني",
         "account_number": "AE770330000012345678", "iban": "AE77 0330 0000 1234 5678 00", "opening_balance": 0},
        {"name": "الصندوق الرئيسي - الرياض", "name_en": "Main Cash Box - Riyadh",
         "account_type": "cash", "currency": "SAR",
         "branch_id": ids.get("BR001", 1), "opening_balance": 0},
        {"name": "صندوق فرع جدة", "name_en": "Jeddah Cash Box",
         "account_type": "cash", "currency": "SAR",
         "branch_id": ids.get("BR002"), "opening_balance": 0},
        {"name": "صندوق فرع دبي", "name_en": "Dubai Cash Box",
         "account_type": "cash", "currency": "AED",
         "branch_id": ids.get("BR003"), "opening_balance": 0},
    ]
    for ta in treasury_accounts:
        post("/treasury/accounts", ta, H, ta["name"])
    
    all_treas = get("/treasury/accounts", H)
    print(f"  📊 Treasury Accounts: {len(all_treas)}")

    # ========================================================================
    #  PHASE 15: TAX WHT RATES
    # ========================================================================
    print("\n" + "=" * 60)
    print("  PHASE 15: TAX WHT RATES (8)")
    print("=" * 60)
    
    wht_rates = [
        {"tax_code": "WHT-SRV-5", "tax_name": "استقطاع خدمات فنية واستشارية", "tax_name_en": "WHT Technical Services 5%", "rate_value": 5, "country_code": "SA"},
        {"tax_code": "WHT-RENT-5", "tax_name": "استقطاع إيجارات", "tax_name_en": "WHT Rent 5%", "rate_value": 5, "country_code": "SA"},
        {"tax_code": "WHT-CONS-5", "tax_name": "استقطاع استشارات", "tax_name_en": "WHT Consulting 5%", "rate_value": 5, "country_code": "SA"},
        {"tax_code": "WHT-AIR-5", "tax_name": "استقطاع تذاكر طيران", "tax_name_en": "WHT Airline 5%", "rate_value": 5, "country_code": "SA"},
        {"tax_code": "WHT-TEL-5", "tax_name": "استقطاع اتصالات دولية", "tax_name_en": "WHT Telecom 5%", "rate_value": 5, "country_code": "SA"},
        {"tax_code": "WHT-INS-5", "tax_name": "استقطاع تأمين", "tax_name_en": "WHT Insurance 5%", "rate_value": 5, "country_code": "SA"},
        {"tax_code": "WHT-ROY-15", "tax_name": "استقطاع حقوق ملكية فكرية", "tax_name_en": "WHT Royalties 15%", "rate_value": 15, "country_code": "SA"},
        {"tax_code": "WHT-DIV-5", "tax_name": "استقطاع أرباح أسهم", "tax_name_en": "WHT Dividends 5%", "rate_value": 5, "country_code": "SA"},
    ]
    for wht in wht_rates:
        post("/taxes/rates", wht, H, wht["tax_name"])

    # ========================================================================
    #  PHASE 16: EMPLOYEES & USER ACCOUNTS (9)
    # ========================================================================
    print("\n" + "=" * 60)
    print("  PHASE 16: EMPLOYEES & USER ACCOUNTS (9)")
    print("=" * 60)
    
    employees = [
        {"employee_code": "EMP-001", "first_name": "أحمد", "last_name": "القحطاني",
         "first_name_en": "Ahmad", "last_name_en": "Al-Qahtani",
         "email": "ahmad@aman-erp.com", "phone": "+966551001001",
         "department_name": "الإدارة المالية", "position_title": "مدير مالي",
         "salary": 18000, "housing_allowance": 5000, "transport_allowance": 2000,
         "hire_date": "2025-01-01", "branch_id": ids.get("BR001", 1), "currency": "SAR", "nationality": "SA",
         "create_user": True, "username": "ahmad", "password": EMPLOYEE_PASSWORD, "role": "admin"},
        {"employee_code": "EMP-002", "first_name": "فاطمة", "last_name": "الزهراني",
         "first_name_en": "Fatima", "last_name_en": "Al-Zahrani",
         "email": "fatima@aman-erp.com", "phone": "+966552002002",
         "department_name": "الإدارة المالية", "position_title": "محاسب",
         "salary": 12000, "housing_allowance": 3500, "transport_allowance": 1500,
         "hire_date": "2025-03-01", "branch_id": ids.get("BR001", 1), "currency": "SAR", "nationality": "SA",
         "create_user": True, "username": "fatima", "password": EMPLOYEE_PASSWORD, "role": "accountant"},
        {"employee_code": "EMP-003", "first_name": "خالد", "last_name": "الشمري",
         "first_name_en": "Khalid", "last_name_en": "Al-Shammari",
         "email": "khalid@aman-erp.com", "phone": "+966553003003",
         "department_name": "المبيعات", "position_title": "مدير مبيعات",
         "salary": 15000, "housing_allowance": 4500, "transport_allowance": 2000,
         "hire_date": "2025-02-15", "branch_id": ids.get("BR001", 1), "currency": "SAR", "nationality": "SA",
         "create_user": True, "username": "khalid", "password": EMPLOYEE_PASSWORD, "role": "sales"},
        {"employee_code": "EMP-004", "first_name": "نورة", "last_name": "العتيبي",
         "first_name_en": "Noura", "last_name_en": "Al-Otaibi",
         "email": "noura@aman-erp.com", "phone": "+966554004004",
         "department_name": "المبيعات", "position_title": "مندوب مبيعات",
         "salary": 9000, "housing_allowance": 2500, "transport_allowance": 1500,
         "hire_date": "2025-06-01", "branch_id": ids.get("BR002"), "currency": "SAR", "nationality": "SA",
         "create_user": True, "username": "noura", "password": EMPLOYEE_PASSWORD, "role": "sales"},
        {"employee_code": "EMP-005", "first_name": "محمد", "last_name": "الحربي",
         "first_name_en": "Mohammed", "last_name_en": "Al-Harbi",
         "email": "mohammed@aman-erp.com", "phone": "+966555005005",
         "department_name": "المشتريات", "position_title": "مدير مشتريات",
         "salary": 14000, "housing_allowance": 4000, "transport_allowance": 1500,
         "hire_date": "2025-04-01", "branch_id": ids.get("BR001", 1), "currency": "SAR", "nationality": "SA",
         "create_user": True, "username": "mohammed", "password": EMPLOYEE_PASSWORD, "role": "manager"},
        {"employee_code": "EMP-006", "first_name": "سعد", "last_name": "الدوسري",
         "first_name_en": "Saad", "last_name_en": "Al-Dosari",
         "email": "saad@aman-erp.com", "phone": "+966556006006",
         "department_name": "المستودعات", "position_title": "أمين مستودع",
         "salary": 8000, "housing_allowance": 2500, "transport_allowance": 1000,
         "hire_date": "2025-05-15", "branch_id": ids.get("BR001", 1), "currency": "SAR", "nationality": "SA",
         "create_user": True, "username": "saad", "password": EMPLOYEE_PASSWORD, "role": "inventory"},
        {"employee_code": "EMP-007", "first_name": "ريم", "last_name": "السبيعي",
         "first_name_en": "Reem", "last_name_en": "Al-Subaie",
         "email": "reem@aman-erp.com", "phone": "+966557007007",
         "department_name": "الموارد البشرية", "position_title": "مدير موارد بشرية",
         "salary": 13000, "housing_allowance": 4000, "transport_allowance": 1500,
         "hire_date": "2025-01-15", "branch_id": ids.get("BR001", 1), "currency": "SAR", "nationality": "SA",
         "create_user": True, "username": "reem", "password": EMPLOYEE_PASSWORD, "role": "manager"},
        {"employee_code": "EMP-008", "first_name": "عبدالرحمن", "last_name": "المالكي",
         "first_name_en": "Abdulrahman", "last_name_en": "Al-Malki",
         "email": "abdulrahman@aman-erp.com", "phone": "+966558008008",
         "department_name": "نقاط البيع", "position_title": "كاشير",
         "salary": 6000, "housing_allowance": 2000, "transport_allowance": 1000,
         "hire_date": "2025-07-01", "branch_id": ids.get("BR001", 1), "currency": "SAR", "nationality": "SA",
         "create_user": True, "username": "abdulrahman", "password": EMPLOYEE_PASSWORD, "role": "cashier"},
        {"employee_code": "EMP-009", "first_name": "ياسر", "last_name": "العمري",
         "first_name_en": "Yasser", "last_name_en": "Al-Amri",
         "email": "yasser@aman-erp.com", "phone": "+966559009009",
         "department_name": "الإنتاج والتصنيع", "position_title": "أمين مستودع",
         "salary": 10000, "housing_allowance": 3000, "transport_allowance": 1500,
         "hire_date": "2025-08-01", "branch_id": ids.get("BR003"), "currency": "AED", "nationality": "SA",
         "create_user": True, "username": "yasser", "password": EMPLOYEE_PASSWORD, "role": "user"},
    ]
    for emp in employees:
        post("/hr/employees", emp, H, f"{emp['first_name']} {emp['last_name']} ({emp['username']})")
    
    all_emps = get("/hr/employees", H)
    if isinstance(all_emps, list):
        print(f"  📊 Employees: {len(all_emps)}")
    else:
        print(f"  📊 Employees response: {str(all_emps)[:200]}")

    # ========================================================================
    #  PHASE 17: OPENING JOURNAL ENTRIES (8 balanced entries)
    # ========================================================================
    print("\n" + "=" * 60)
    print("  PHASE 17: OPENING JOURNAL ENTRIES (8)")
    print("=" * 60)
    
    # Get account IDs for new accounts
    acc_rajhi = ids.get("acc_RAJHI", 115)
    acc_ncb = ids.get("acc_NCB", 116) 
    acc_inma = ids.get("acc_INMA")
    acc_enbd = ids.get("acc_ENBD")
    
    # If we don't have INMA/ENBD from read-back, search more thoroughly
    if not acc_inma or not acc_enbd:
        all_accounts = get("/accounting/accounts", H)
        for a in all_accounts:
            code = a.get("account_code", "")
            if code == "INMA": acc_inma = a["id"]
            elif code == "ENBD": acc_enbd = a["id"]
    
    print(f"  📊 Account IDs: RAJHI={acc_rajhi}, NCB={acc_ncb}, INMA={acc_inma}, ENBD={acc_enbd}")
    
    # 1. Main opening entry
    post("/accounting/journal-entries", {
        "date": "2026-01-01",
        "description": "قيد افتتاحي - تأسيس الأرصدة الافتتاحية",
        "reference": "OPENING-2026", "status": "posted",
        "branch_id": ids.get("BR001", 1), "currency": "SAR", "exchange_rate": 1.0,
        "lines": [
            {"account_id": 8, "debit": 50000, "credit": 0, "description": "رصيد الصندوق الرئيسي"},
            {"account_id": acc_rajhi, "debit": 200000, "credit": 0, "description": "رصيد بنك الراجحي"},
            {"account_id": acc_ncb, "debit": 150000, "credit": 0, "description": "رصيد البنك الأهلي"},
            {"account_id": acc_inma or 9, "debit": 100000, "credit": 0, "description": "رصيد بنك الإنماء"},
            {"account_id": 12, "debit": 75000, "credit": 0, "description": "مخزون مواد خام افتتاحي"},
            {"account_id": 13, "debit": 125000, "credit": 0, "description": "مخزون منتجات تامة افتتاحي"},
            {"account_id": 19, "debit": 250000, "credit": 0, "description": "آلات ومعدات"},
            {"account_id": 24, "debit": 80000, "credit": 0, "description": "أجهزة حاسوب"},
            {"account_id": 43, "debit": 0, "credit": 1000000, "description": "رأس المال المدفوع"},
            {"account_id": 25, "debit": 0, "credit": 30000, "description": "إهلاك متراكم"},
        ]
    }, H, "القيد الافتتاحي الرئيسي")
    
    # 2. AR Opening
    post("/accounting/journal-entries", {
        "date": "2026-01-01", "description": "أرصدة عملاء افتتاحية",
        "reference": "OPENING-AR-2026", "status": "posted", "branch_id": ids.get("BR001", 1),
        "lines": [
            {"account_id": 10, "debit": 85000, "credit": 0, "description": "ذمم مدينة - عملاء"},
            {"account_id": 44, "debit": 0, "credit": 85000, "description": "أرباح مبقاة"},
        ]
    }, H, "أرصدة عملاء افتتاحية")
    
    # 3. AP Opening
    post("/accounting/journal-entries", {
        "date": "2026-01-01", "description": "أرصدة موردين افتتاحية",
        "reference": "OPENING-AP-2026", "status": "posted", "branch_id": ids.get("BR001", 1),
        "lines": [
            {"account_id": 44, "debit": 65000, "credit": 0, "description": "أرباح مبقاة"},
            {"account_id": 31, "debit": 0, "credit": 65000, "description": "ذمم دائنة - موردون"},
        ]
    }, H, "أرصدة موردين افتتاحية")
    
    # 4. Prepaid
    post("/accounting/journal-entries", {
        "date": "2026-01-01", "description": "مصروفات مدفوعة مقدماً",
        "reference": "OPENING-PRE-2026", "status": "posted", "branch_id": ids.get("BR001", 1),
        "lines": [
            {"account_id": 109, "debit": 36000, "credit": 0, "description": "إيجار مدفوع مقدماً"},
            {"account_id": 110, "debit": 18000, "credit": 0, "description": "تأمين مدفوع مقدماً"},
            {"account_id": 44, "debit": 0, "credit": 54000, "description": "أرباح مبقاة"},
        ]
    }, H, "مصروفات مدفوعة مقدماً")
    
    # 5. Employee loans
    post("/accounting/journal-entries", {
        "date": "2026-01-01", "description": "سلف وقروض موظفين",
        "reference": "OPENING-ADV-2026", "status": "posted", "branch_id": ids.get("BR001", 1),
        "lines": [
            {"account_id": 16, "debit": 15000, "credit": 0, "description": "سلف موظفين مرحلة"},
            {"account_id": 44, "debit": 0, "credit": 15000, "description": "أرباح مبقاة"},
        ]
    }, H, "سلف وقروض موظفين")
    
    # 6. EOSB
    post("/accounting/journal-entries", {
        "date": "2026-01-01", "description": "مخصص نهاية الخدمة",
        "reference": "OPENING-EOS-2026", "status": "posted", "branch_id": ids.get("BR001", 1),
        "lines": [
            {"account_id": 44, "debit": 45000, "credit": 0, "description": "أرباح مبقاة"},
            {"account_id": 42, "debit": 0, "credit": 45000, "description": "مخصص نهاية الخدمة"},
        ]
    }, H, "مخصص نهاية الخدمة")
    
    # 7. VAT
    post("/accounting/journal-entries", {
        "date": "2026-01-01", "description": "رصيد ضريبة مرحل",
        "reference": "OPENING-VAT-2026", "status": "posted", "branch_id": ids.get("BR001", 1),
        "lines": [
            {"account_id": 27, "debit": 12000, "credit": 0, "description": "ضريبة مدخلات مرحلة"},
            {"account_id": 35, "debit": 0, "credit": 8000, "description": "ضريبة مخرجات مرحلة"},
            {"account_id": 44, "debit": 0, "credit": 4000, "description": "أرباح مبقاة"},
        ]
    }, H, "أرصدة ضريبية مرحلة")
    
    # 8. Dubai branch
    if acc_enbd:
        post("/accounting/journal-entries", {
            "date": "2026-01-01", "description": "أرصدة فرع دبي الافتتاحية",
            "reference": "OPENING-DXB-2026", "status": "posted",
            "branch_id": ids.get("BR003"), "currency": "AED", "exchange_rate": 1.02,
            "lines": [
                {"account_id": acc_enbd, "debit": 50000, "credit": 0, "description": "رصيد بنك الإمارات"},
                {"account_id": 43, "debit": 0, "credit": 50000, "description": "رأس المال - فرع دبي"},
            ]
        }, H, "أرصدة فرع دبي")
    else:
        print("  ⚠️ Skipped Dubai entry — ENBD account ID not found")

    # ========================================================================
    #  SUMMARY
    # ========================================================================
    print("\n" + "=" * 60)
    print("  ✅ DATA POPULATION COMPLETE!")
    print("=" * 60)
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║  ملخص البيانات المُدخلة                                   ║
╠══════════════════════════════════════════════════════════╣
║  المستخدمون: 10 (vvvv + 9 موظفين)                         ║
║  الفروع: 3 (الرياض + جدة + دبي)                           ║
║  الأقسام: 7                                                ║
║  الوظائف: 8                                                ║
║  شجرة الحسابات: 121 (114 + 7)                             ║
║  المنتجات: 7                                               ║
║  فئات المنتجات: 5                                          ║
║  الأطراف: 11 (6 عملاء + 5 موردون)                          ║
║  مجموعات العملاء: 3                                        ║
║  مجموعات الموردين: 2                                       ║
║  المستودعات: 5 (1 + 4)                                     ║
║  حسابات الخزينة: 7                                         ║
║  العملات: 5                                                ║
║  السنة المالية: 2026                                       ║
║  معدلات الاستقطاع: 8                                       ║
║  القيود الافتتاحية: 8                                      ║
╚══════════════════════════════════════════════════════════╝

🔐 بيانات الدخول للموظفين:
┌─────────────┬──────────────────┬─────────────┬────────────────┐
│ الاسم       │ اسم المستخدم      │ كلمة السر    │ الدور          │
├─────────────┼──────────────────┼─────────────┼────────────────┤
│ عمر (مشرف)  │ vvvv             │ As123321    │ superuser      │
│ أحمد        │ ahmad            │ {EMPLOYEE_PASSWORD}  │ admin          │
│ فاطمة       │ fatima           │ {EMPLOYEE_PASSWORD}  │ accountant     │
│ خالد        │ khalid           │ {EMPLOYEE_PASSWORD}  │ sales          │
│ نورة        │ noura            │ {EMPLOYEE_PASSWORD}  │ sales          │
│ محمد        │ mohammed         │ {EMPLOYEE_PASSWORD}  │ manager        │
│ سعد         │ saad             │ {EMPLOYEE_PASSWORD}  │ inventory      │
│ ريم         │ reem             │ {EMPLOYEE_PASSWORD}  │ manager        │
│ عبدالرحمن   │ abdulrahman      │ {EMPLOYEE_PASSWORD}  │ cashier        │
│ ياسر        │ yasser           │ {EMPLOYEE_PASSWORD}  │ user           │
└─────────────┴──────────────────┴─────────────┴────────────────┘

🏢 رمز الشركة: {COMPANY_CODE}
🌐 السيرفر: {API.replace('/api','')}
""")

if __name__ == "__main__":
    main()
