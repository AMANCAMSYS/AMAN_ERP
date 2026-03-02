#!/usr/bin/env python3
"""
Setup Test Data for AMAN ERP - Company b08f3451
Based on FULL_SYSTEM_TEST_SCENARIOS.md

This script enters all base/master data (non-cycle data):
- Currencies & Exchange Rates
- Branches (update existing)
- Warehouses
- Product Categories & Products
- Customer Groups & Customers
- Supplier Groups & Suppliers
- Treasury Accounts (Banks & Cash Boxes)
- Employees (with user accounts)
- Fiscal Year & Periods
- Chart of Accounts (additional accounts)
- Opening Balances (Journal Entries)

All operations go through the API to ensure audit logs are recorded.
"""

import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000/api"
TOKEN = None

def login():
    global TOKEN
    resp = requests.post(f"{BASE_URL}/auth/login", data={
        "username": "omar",
        "password": "As123321"
    })
    if resp.status_code != 200:
        print(f"❌ Login failed: {resp.text}")
        sys.exit(1)
    data = resp.json()
    TOKEN = data["access_token"]
    print(f"✅ Login successful as omar")
    return TOKEN

def headers():
    return {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def api_post(endpoint, data, desc=""):
    resp = requests.post(f"{BASE_URL}{endpoint}", json=data, headers=headers())
    if resp.status_code in [200, 201]:
        result = resp.json()
        rid = result.get("id", "")
        print(f"  ✅ {desc} (id={rid})")
        return result
    else:
        print(f"  ❌ {desc}: {resp.status_code} - {resp.text[:200]}")
        return None

def api_put(endpoint, data, desc=""):
    resp = requests.put(f"{BASE_URL}{endpoint}", json=data, headers=headers())
    if resp.status_code in [200, 201]:
        result = resp.json()
        print(f"  ✅ {desc}")
        return result
    else:
        print(f"  ❌ {desc}: {resp.status_code} - {resp.text[:200]}")
        return None

def api_get(endpoint, desc=""):
    resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers())
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"  ❌ GET {desc}: {resp.status_code} - {resp.text[:200]}")
        return None

# ========================================
# 1. CURRENCIES
# ========================================
def setup_currencies():
    print("\n" + "="*60)
    print("📌 1. إعداد العملات وأسعار الصرف")
    print("="*60)
    
    # Check existing currencies
    currencies = api_get("/accounting/currencies/", "currencies")
    existing = {c["code"]: c for c in (currencies if currencies else [])}
    
    # Update SAR if needed
    if "SAR" in existing:
        print(f"  ℹ️  SAR موجود (id={existing['SAR']['id']})")
    
    # Update USD
    if "USD" in existing:
        api_put(f"/accounting/currencies/{existing['USD']['id']}", {
            "code": "USD", "name": "دولار أمريكي", "name_en": "US Dollar",
            "symbol": "$", "is_base": False, "current_rate": 3.75, "is_active": True
        }, "تحديث USD")
    else:
        api_post("/accounting/currencies/", {
            "code": "USD", "name": "دولار أمريكي", "name_en": "US Dollar",
            "symbol": "$", "is_base": False, "current_rate": 3.75, "is_active": True
        }, "إنشاء USD")
    
    # Update EUR
    if "EUR" in existing:
        api_put(f"/accounting/currencies/{existing['EUR']['id']}", {
            "code": "EUR", "name": "يورو", "name_en": "Euro",
            "symbol": "€", "is_base": False, "current_rate": 4.10, "is_active": True
        }, "تحديث EUR")
    else:
        api_post("/accounting/currencies/", {
            "code": "EUR", "name": "يورو", "name_en": "Euro",
            "symbol": "€", "is_base": False, "current_rate": 4.10, "is_active": True
        }, "إنشاء EUR")
    
    # Update AED
    if "AED" in existing:
        api_put(f"/accounting/currencies/{existing['AED']['id']}", {
            "code": "AED", "name": "درهم إماراتي", "name_en": "UAE Dirham",
            "symbol": "د.إ", "is_base": False, "current_rate": 1.02, "is_active": True
        }, "تحديث AED")
    else:
        api_post("/accounting/currencies/", {
            "code": "AED", "name": "درهم إماراتي", "name_en": "UAE Dirham",
            "symbol": "د.إ", "is_base": False, "current_rate": 1.02, "is_active": True
        }, "إنشاء AED")
    
    # Add EGP (likely missing)
    if "EGP" in existing:
        api_put(f"/accounting/currencies/{existing['EGP']['id']}", {
            "code": "EGP", "name": "جنيه مصري", "name_en": "Egyptian Pound",
            "symbol": "ج.م", "is_base": False, "current_rate": 0.077, "is_active": True
        }, "تحديث EGP")
    else:
        api_post("/accounting/currencies/", {
            "code": "EGP", "name": "جنيه مصري", "name_en": "Egyptian Pound",
            "symbol": "ج.م", "is_base": False, "current_rate": 0.077, "is_active": True
        }, "إنشاء EGP")
    
    # Add exchange rates for today
    print("\n  📊 إضافة أسعار الصرف ليوم 2026-03-01:")
    currencies = api_get("/accounting/currencies/", "reload currencies")
    if currencies:
        for c in currencies:
            if c["code"] != "SAR":
                rates = {
                    "USD": 3.75, "EUR": 4.10, "AED": 1.02, "EGP": 0.077
                }
                rate = rates.get(c["code"])
                if rate:
                    api_post("/accounting/currencies/rates", {
                        "currency_id": c["id"],
                        "rate": rate,
                        "rate_date": "2026-03-01",
                        "source": "manual"
                    }, f"سعر صرف {c['code']} = {rate}")

# ========================================
# 2. BRANCHES (Update existing)
# ========================================
def setup_branches():
    print("\n" + "="*60)
    print("📌 2. تحديث/إنشاء الفروع")
    print("="*60)
    
    branches = api_get("/branches", "branches")
    if not branches:
        branches = []
    
    existing_codes = {b["branch_code"] for b in branches}
    
    # Update existing HQ branch
    for b in branches:
        if b["branch_code"] == "BR001" or b["branch_code"] == "HQ":
            api_put(f"/branches/{b['id']}", {
                "branch_name": "المقر الرئيسي",
                "branch_name_en": "Headquarters",
                "branch_code": "HQ",
                "city": "الرياض",
                "country": "المملكة العربية السعودية",
                "country_code": "SA",
                "default_currency": "SAR",
                "is_default": True,
                "is_active": True
            }, "تحديث المقر الرئيسي → HQ")
    
    # Create Jeddah branch if not exists
    if "JED" not in existing_codes:
        api_post("/branches", {
            "branch_name": "فرع جدة",
            "branch_name_en": "Jeddah Branch",
            "branch_code": "JED",
            "city": "جدة",
            "country": "المملكة العربية السعودية",
            "country_code": "SA",
            "default_currency": "SAR",
            "is_active": True
        }, "إنشاء فرع جدة")
    else:
        for b in branches:
            if b["branch_code"] == "JED":
                api_put(f"/branches/{b['id']}", {
                    "branch_name": "فرع جدة",
                    "branch_name_en": "Jeddah Branch",
                    "branch_code": "JED",
                    "city": "جدة",
                    "country": "المملكة العربية السعودية",
                    "country_code": "SA",
                    "default_currency": "SAR",
                    "is_active": True
                }, "تحديث فرع جدة")
    
    # Create Dubai branch if not exists
    if "DXB" not in existing_codes:
        api_post("/branches", {
            "branch_name": "فرع دبي",
            "branch_name_en": "Dubai Branch",
            "branch_code": "DXB",
            "city": "دبي",
            "country": "الإمارات العربية المتحدة",
            "country_code": "AE",
            "default_currency": "AED",
            "is_active": True
        }, "إنشاء فرع دبي")
    else:
        for b in branches:
            if b["branch_code"] == "DXB":
                api_put(f"/branches/{b['id']}", {
                    "branch_name": "فرع دبي",
                    "branch_name_en": "Dubai Branch",
                    "branch_code": "DXB",
                    "city": "دبي",
                    "country": "الإمارات العربية المتحدة",
                    "country_code": "AE",
                    "default_currency": "AED",
                    "is_active": True
                }, "تحديث فرع دبي")

# ========================================
# 3. WAREHOUSES
# ========================================
def setup_warehouses():
    print("\n" + "="*60)
    print("📌 3. إنشاء المستودعات")
    print("="*60)
    
    branches = api_get("/branches", "branches")
    if not branches:
        return {}
    
    branch_map = {b["branch_code"]: b["id"] for b in branches}
    # Handle both old code BR001 and new code HQ
    hq_id = branch_map.get("HQ", branch_map.get("BR001", 1))
    jed_id = branch_map.get("JED", 2)
    dxb_id = branch_map.get("DXB", 3)
    
    warehouses_data = [
        {"name": "مستودع مواد خام - الرياض", "code": "WH-RAW-RYD", "location": "الرياض", "branch_id": hq_id},
        {"name": "مستودع منتجات تامة - الرياض", "code": "WH-FIN-RYD", "location": "الرياض", "branch_id": hq_id},
        {"name": "مستودع جدة الرئيسي", "code": "WH-JED", "location": "جدة", "branch_id": jed_id},
        {"name": "مستودع دبي", "code": "WH-DXB", "location": "دبي", "branch_id": dxb_id},
    ]
    
    wh_map = {}
    for wh in warehouses_data:
        result = api_post("/inventory/warehouses", wh, f"مستودع: {wh['name']}")
        if result:
            wh_map[wh["code"]] = result["id"]
    
    return wh_map

# ========================================
# 4. PRODUCT CATEGORIES & PRODUCTS
# ========================================
def setup_products():
    print("\n" + "="*60)
    print("📌 4. إنشاء فئات المنتجات والمنتجات")
    print("="*60)
    
    # Categories
    categories = {
        "مواد خام": api_post("/inventory/categories", {"name": "مواد خام", "code": "RAW"}, "فئة: مواد خام"),
        "منتجات تامة": api_post("/inventory/categories", {"name": "منتجات تامة", "code": "FIN"}, "فئة: منتجات تامة"),
        "مستلزمات": api_post("/inventory/categories", {"name": "مستلزمات", "code": "SUP"}, "فئة: مستلزمات"),
        "خدمات": api_post("/inventory/categories", {"name": "خدمات", "code": "SRV"}, "فئة: خدمات"),
        "أصول ثابتة": api_post("/inventory/categories", {"name": "أصول ثابتة", "code": "AST"}, "فئة: أصول ثابتة"),
    }
    
    cat_ids = {k: v["id"] if v else None for k, v in categories.items()}
    
    # Products
    products = [
        {
            "item_code": "ALU-001", "item_name": "لوح ألمنيوم 3 مم", "item_name_en": "Aluminum Sheet 3mm",
            "item_type": "product", "unit": "متر", "selling_price": 150, "buying_price": 80,
            "tax_rate": 15, "category_id": cat_ids.get("مواد خام"),
            "has_batch_tracking": True, "has_serial_tracking": False,
            "description": "لوح ألمنيوم بسماكة 3 مم للتصنيع"
        },
        {
            "item_code": "WOD-001", "item_name": "خشب طبيعي MDF", "item_name_en": "Natural MDF Wood",
            "item_type": "product", "unit": "لوح", "selling_price": 200, "buying_price": 120,
            "tax_rate": 15, "category_id": cat_ids.get("مواد خام"),
            "has_batch_tracking": False, "has_serial_tracking": False,
            "description": "خشب MDF طبيعي للنجارة"
        },
        {
            "item_code": "DOOR-001", "item_name": "باب ألمنيوم جاهز", "item_name_en": "Ready Aluminum Door",
            "item_type": "product", "unit": "قطعة", "selling_price": 1500, "buying_price": 900,
            "tax_rate": 15, "category_id": cat_ids.get("منتجات تامة"),
            "has_batch_tracking": False, "has_serial_tracking": True,
            "description": "باب ألمنيوم جاهز للتركيب"
        },
        {
            "item_code": "WIN-001", "item_name": "نافذة زجاج مزدوج", "item_name_en": "Double Glass Window",
            "item_type": "product", "unit": "قطعة", "selling_price": 800, "buying_price": 450,
            "tax_rate": 15, "category_id": cat_ids.get("منتجات تامة"),
            "has_batch_tracking": False, "has_serial_tracking": True,
            "description": "نافذة زجاج مزدوج عازلة"
        },
        {
            "item_code": "SCR-001", "item_name": "مسامير ستنلس ستيل", "item_name_en": "Stainless Steel Screws",
            "item_type": "product", "unit": "علبة", "selling_price": 25, "buying_price": 10,
            "tax_rate": 15, "category_id": cat_ids.get("مستلزمات"),
            "has_batch_tracking": False, "has_serial_tracking": False,
            "description": "مسامير ستنلس ستيل متنوعة الأحجام"
        },
        {
            "item_code": "LAP-001", "item_name": "لابتوب Dell", "item_name_en": "Dell Laptop",
            "item_type": "product", "unit": "قطعة", "selling_price": 0, "buying_price": 4500,
            "tax_rate": 15, "category_id": cat_ids.get("أصول ثابتة"),
            "has_batch_tracking": False, "has_serial_tracking": True,
            "description": "لابتوب Dell للموظفين - أصل ثابت"
        },
        {
            "item_code": "SRV-001", "item_name": "خدمة تركيب", "item_name_en": "Installation Service",
            "item_type": "service", "unit": "ساعة", "selling_price": 200, "buying_price": 0,
            "tax_rate": 15, "category_id": cat_ids.get("خدمات"),
            "has_batch_tracking": False, "has_serial_tracking": False,
            "description": "خدمة تركيب أبواب ونوافذ"
        },
    ]
    
    for p in products:
        api_post("/inventory/products", p, f"منتج: {p['item_code']} - {p['item_name']}")

# ========================================
# 5. CUSTOMER GROUPS & CUSTOMERS
# ========================================
def setup_customers():
    print("\n" + "="*60)
    print("📌 5. إنشاء مجموعات العملاء والعملاء")
    print("="*60)
    
    branches = api_get("/branches", "branches")
    branch_map = {}
    if branches:
        for b in branches:
            branch_map[b["branch_code"]] = b["id"]
    hq_id = branch_map.get("HQ", branch_map.get("BR001", 1))
    jed_id = branch_map.get("JED", 2)
    dxb_id = branch_map.get("DXB", 3)
    
    # Customer Groups
    groups = [
        {"group_name": "عملاء جملة", "group_name_en": "Wholesale Customers", "discount_percentage": 5, "payment_days": 30},
        {"group_name": "عملاء تجزئة", "group_name_en": "Retail Customers", "discount_percentage": 0, "payment_days": 15},
        {"group_name": "عملاء خارجيين", "group_name_en": "International Customers", "discount_percentage": 3, "payment_days": 45},
    ]
    
    group_ids = {}
    for g in groups:
        result = api_post("/sales/customer-groups", g, f"مجموعة عملاء: {g['group_name']}")
        if result:
            group_ids[g["group_name"]] = result["id"]
    
    # Customers
    customers = [
        {
            "name": "شركة النور للإلكترونيات", "name_en": "Al Nour Electronics Co.",
            "phone": "0112345678", "email": "info@alnour.sa", "city": "الرياض",
            "country": "SA", "credit_limit": 500000, "payment_terms": 30,
            "group_id": group_ids.get("عملاء جملة"), "branch_id": hq_id, "currency": "SAR",
            "tax_number": "300098765600001"
        },
        {
            "name": "مؤسسة الفجر التجارية", "name_en": "Al Fajr Trading Est.",
            "phone": "0126789012", "email": "info@alfajr.sa", "city": "جدة",
            "country": "SA", "credit_limit": 100000, "payment_terms": 15,
            "group_id": group_ids.get("عملاء تجزئة"), "branch_id": jed_id, "currency": "SAR",
            "tax_number": "300098765600002"
        },
        {
            "name": "Gulf Trading LLC", "name_en": "Gulf Trading LLC",
            "phone": "+97145678901", "email": "info@gulftrading.ae", "city": "Dubai",
            "country": "AE", "credit_limit": 200000, "payment_terms": 45,
            "group_id": group_ids.get("عملاء خارجيين"), "branch_id": dxb_id, "currency": "AED",
            "tax_number": "TRN100234567"
        },
        {
            "name": "Euro Supplies GmbH", "name_en": "Euro Supplies GmbH",
            "phone": "+4930123456", "email": "info@eurosupplies.de", "city": "Berlin",
            "country": "DE", "credit_limit": 150000, "payment_terms": 45,
            "group_id": group_ids.get("عملاء خارجيين"), "branch_id": dxb_id, "currency": "EUR"
        },
        {
            "name": "مؤسسة السلام", "name_en": "Al Salam Est.",
            "phone": "0113456789", "email": "info@alsalam.sa", "city": "الرياض",
            "country": "SA", "credit_limit": 300000, "payment_terms": 30,
            "group_id": group_ids.get("عملاء جملة"), "branch_id": hq_id, "currency": "SAR",
            "tax_number": "300098765600003"
        },
        {
            "name": "Cairo Import Co.", "name_en": "Cairo Import Co.",
            "phone": "+20234567890", "email": "info@cairoimport.eg", "city": "Cairo",
            "country": "EG", "credit_limit": 5000000, "payment_terms": 45,
            "group_id": group_ids.get("عملاء خارجيين"), "branch_id": hq_id, "currency": "EGP"
        },
    ]
    
    for c in customers:
        api_post("/sales/customers", c, f"عميل: {c['name']}")

# ========================================
# 6. SUPPLIER GROUPS & SUPPLIERS
# ========================================
def setup_suppliers():
    print("\n" + "="*60)
    print("📌 6. إنشاء مجموعات الموردين والموردين")
    print("="*60)
    
    # Supplier Groups
    groups = [
        {"group_name": "موردون محليون", "group_name_en": "Local Suppliers", "payment_days": 30},
        {"group_name": "موردون خارجيون", "group_name_en": "International Suppliers", "payment_days": 60},
    ]
    
    group_ids = {}
    for g in groups:
        result = api_post("/buying/supplier-groups", g, f"مجموعة موردين: {g['group_name']}")
        if result:
            # Handle different response formats
            gid = result.get("id") or result.get("group_id") or result.get("data", {}).get("id")
            if gid:
                group_ids[g["group_name"]] = gid
            else:
                # Try to fetch the just-created group
                all_groups = api_get("/buying/supplier-groups", "supplier groups")
                if all_groups:
                    for sg in (all_groups if isinstance(all_groups, list) else []):
                        if sg.get("group_name") == g["group_name"]:
                            group_ids[g["group_name"]] = sg.get("id")
                            break
    
    # Suppliers
    suppliers = [
        {
            "name": "مصنع الألمنيوم الوطني", "name_en": "National Aluminum Factory",
            "phone": "0114567890", "email": "info@natalu.sa", "address": "المنطقة الصناعية، الرياض",
            "currency": "SAR", "tax_number": "300098765600010",
            "group_id": group_ids.get("موردون محليون")
        },
        {
            "name": "China Materials Co.", "name_en": "China Materials Co.",
            "phone": "+862012345678", "email": "sales@chinamaterials.cn", "address": "Guangzhou, China",
            "currency": "USD",
            "group_id": group_ids.get("موردون خارجيون")
        },
        {
            "name": "مورد الخشب المتحد", "name_en": "United Wood Supplier",
            "phone": "0125678901", "email": "info@unitedwood.sa", "address": "منطقة الميناء، جدة",
            "currency": "SAR", "tax_number": "300098765600011",
            "group_id": group_ids.get("موردون محليون")
        },
        {
            "name": "European Parts AG", "name_en": "European Parts AG",
            "phone": "+4989123456", "email": "info@europarts.de", "address": "Munich, Germany",
            "currency": "EUR",
            "group_id": group_ids.get("موردون خارجيون")
        },
        {
            "name": "Nile Trading Co.", "name_en": "Nile Trading Co.",
            "phone": "+201234567890", "email": "info@niletrading.eg", "address": "Cairo, Egypt",
            "currency": "EGP",
            "group_id": group_ids.get("موردون خارجيون")
        },
    ]
    
    for s in suppliers:
        api_post("/inventory/suppliers", s, f"مورد: {s['name']}")

# ========================================
# 7. TREASURY ACCOUNTS (Banks & Cash Boxes)
# ========================================
def setup_treasury():
    print("\n" + "="*60)
    print("📌 7. إنشاء حسابات الخزينة (البنوك والصناديق)")
    print("="*60)
    
    branches = api_get("/branches", "branches")
    branch_map = {}
    if branches:
        for b in branches:
            branch_map[b["branch_code"]] = b["id"]
    hq_id = branch_map.get("HQ", branch_map.get("BR001", 1))
    jed_id = branch_map.get("JED", 2)
    dxb_id = branch_map.get("DXB", 3)
    
    treasury_accounts = [
        {
            "name": "البنك الأهلي", "name_en": "Al Ahli Bank",
            "account_type": "bank", "currency": "SAR", "branch_id": hq_id,
            "bank_name": "البنك الأهلي السعودي", "account_number": "40001234567",
            "iban": "SA0380000000608010167519",
            "opening_balance": 500000, "exchange_rate": 1.0
        },
        {
            "name": "صندوق نقدي المقر", "name_en": "HQ Cash Box",
            "account_type": "cash", "currency": "SAR", "branch_id": hq_id,
            "opening_balance": 50000, "exchange_rate": 1.0
        },
        {
            "name": "بنك الراجحي - جدة", "name_en": "Al Rajhi Bank - Jeddah",
            "account_type": "bank", "currency": "SAR", "branch_id": jed_id,
            "bank_name": "مصرف الراجحي", "account_number": "50001234567",
            "iban": "SA4420000000608010167520",
            "opening_balance": 200000, "exchange_rate": 1.0
        },
        {
            "name": "صندوق نقدي جدة", "name_en": "Jeddah Cash Box",
            "account_type": "cash", "currency": "SAR", "branch_id": jed_id,
            "opening_balance": 30000, "exchange_rate": 1.0
        },
        {
            "name": "بنك دبي الإسلامي", "name_en": "Dubai Islamic Bank",
            "account_type": "bank", "currency": "AED", "branch_id": dxb_id,
            "bank_name": "بنك دبي الإسلامي", "account_number": "AE1234567890",
            "iban": "AE070331234567890123456",
            "opening_balance": 100000, "exchange_rate": 1.02
        },
        {
            "name": "صندوق نقدي دبي", "name_en": "Dubai Cash Box",
            "account_type": "cash", "currency": "AED", "branch_id": dxb_id,
            "opening_balance": 20000, "exchange_rate": 1.02
        },
        {
            "name": "بنك مصر", "name_en": "Bank Misr",
            "account_type": "bank", "currency": "EGP", "branch_id": hq_id,
            "bank_name": "بنك مصر", "account_number": "EG1234567890",
            "iban": "EG380019000500000000263180002",
            "opening_balance": 500000, "exchange_rate": 0.077
        },
    ]
    
    for t in treasury_accounts:
        api_post("/treasury/accounts", t, f"خزينة: {t['name']} ({t['account_type']}) - {t['currency']}")

# ========================================
# 8. EMPLOYEES 
# ========================================
def setup_employees():
    print("\n" + "="*60)
    print("📌 8. إنشاء الموظفين")
    print("="*60)
    
    branches = api_get("/branches", "branches")
    branch_map = {}
    if branches:
        for b in branches:
            branch_map[b["branch_code"]] = b["id"]
    hq_id = branch_map.get("HQ", branch_map.get("BR001", 1))
    jed_id = branch_map.get("JED", 2)
    dxb_id = branch_map.get("DXB", 3)
    
    employees = [
        {
            "first_name": "أحمد", "last_name": "محمد",
            "first_name_en": "Ahmed", "last_name_en": "Mohammed",
            "email": "ahmed@aman.com", "phone": "0501234567",
            "position_title": "مدير مالي", "department_name": "المالية",
            "salary": 25000, "housing_allowance": 5000, "transport_allowance": 2000,
            "currency": "SAR", "nationality": "SA",
            "hire_date": "2025-01-01",
            "create_user": True, "username": "ahmed", "password": "Test1234!",
            "role": "accountant",
            "branch_id": hq_id, "allowed_branch_ids": [hq_id]
        },
        {
            "first_name": "سارة", "last_name": "خالد",
            "first_name_en": "Sara", "last_name_en": "Khaled",
            "email": "sara@aman.com", "phone": "0502345678",
            "position_title": "محاسبة", "department_name": "المالية",
            "salary": 15000, "housing_allowance": 3000, "transport_allowance": 1500,
            "currency": "SAR", "nationality": "SA",
            "hire_date": "2025-03-01",
            "create_user": True, "username": "sara", "password": "Test1234!",
            "role": "accountant",
            "branch_id": jed_id, "allowed_branch_ids": [jed_id]
        },
        {
            "first_name": "محمد", "last_name": "علي",
            "first_name_en": "Mohammed", "last_name_en": "Ali",
            "email": "mali@aman.com", "phone": "0503456789",
            "position_title": "مندوب مبيعات", "department_name": "المبيعات",
            "salary": 12000, "housing_allowance": 2500, "transport_allowance": 2000,
            "currency": "SAR", "nationality": "SA",
            "hire_date": "2025-06-01",
            "create_user": True, "username": "mohammed", "password": "Test1234!",
            "role": "sales",
            "branch_id": hq_id, "allowed_branch_ids": [hq_id]
        },
        {
            "first_name": "فاطمة", "last_name": "حسن",
            "first_name_en": "Fatma", "last_name_en": "Hassan",
            "email": "fatma@aman.com", "phone": "0504567890",
            "position_title": "مسؤولة مشتريات", "department_name": "المشتريات",
            "salary": 14000, "housing_allowance": 3000, "transport_allowance": 1500,
            "currency": "SAR", "nationality": "EG",
            "hire_date": "2025-04-01",
            "create_user": True, "username": "fatma", "password": "Test1234!",
            "role": "purchasing",
            "branch_id": jed_id, "allowed_branch_ids": [jed_id]
        },
        {
            "first_name": "خالد", "last_name": "سعيد",
            "first_name_en": "Khaled", "last_name_en": "Saeed",
            "email": "khaled@aman.com", "phone": "0505678901",
            "position_title": "مدير المستودعات", "department_name": "المستودعات",
            "salary": 16000, "housing_allowance": 3500, "transport_allowance": 2000,
            "currency": "SAR", "nationality": "SA",
            "hire_date": "2025-02-01",
            "create_user": True, "username": "khaled", "password": "Test1234!",
            "role": "warehouse",
            "branch_id": hq_id, "allowed_branch_ids": [hq_id, jed_id]
        },
        {
            "first_name": "نورة", "last_name": "أحمد",
            "first_name_en": "Noura", "last_name_en": "Ahmed",
            "email": "noura@aman.com", "phone": "0506789012",
            "position_title": "موارد بشرية", "department_name": "الموارد البشرية",
            "salary": 13000, "housing_allowance": 2500, "transport_allowance": 1500,
            "currency": "SAR", "nationality": "SA",
            "hire_date": "2025-05-01",
            "create_user": True, "username": "noura", "password": "Test1234!",
            "role": "hr",
            "branch_id": jed_id, "allowed_branch_ids": [jed_id]
        },
        {
            "first_name": "ياسر", "last_name": "حمد",
            "first_name_en": "Yaser", "last_name_en": "Hamad",
            "email": "yaser@aman.com", "phone": "0507890123",
            "position_title": "مدير إنتاج", "department_name": "الإنتاج",
            "salary": 18000, "housing_allowance": 4000, "transport_allowance": 2000,
            "currency": "SAR", "nationality": "SA",
            "hire_date": "2025-01-15",
            "create_user": True, "username": "yaser", "password": "Test1234!",
            "role": "production",
            "branch_id": hq_id, "allowed_branch_ids": [hq_id]
        },
        {
            "first_name": "ليلى", "last_name": "عبدالله",
            "first_name_en": "Layla", "last_name_en": "Abdullah",
            "email": "layla@aman.com", "phone": "0508901234",
            "position_title": "أمينة صندوق", "department_name": "نقاط البيع",
            "salary": 10000, "housing_allowance": 2000, "transport_allowance": 1500,
            "currency": "SAR", "nationality": "SA",
            "hire_date": "2025-07-01",
            "create_user": True, "username": "layla", "password": "Test1234!",
            "role": "pos",
            "branch_id": jed_id, "allowed_branch_ids": [jed_id]
        },
        {
            "first_name": "حسين", "last_name": "عمار",
            "first_name_en": "Hussein", "last_name_en": "Ammar",
            "email": "hussein@aman.com", "phone": "0509012345",
            "position_title": "مندوب مبيعات", "department_name": "المبيعات",
            "salary": 12000, "housing_allowance": 2500, "transport_allowance": 2000,
            "currency": "AED", "nationality": "AE",
            "hire_date": "2025-08-01",
            "create_user": True, "username": "hussein", "password": "Test1234!",
            "role": "sales",
            "branch_id": dxb_id, "allowed_branch_ids": [dxb_id]
        },
    ]
    
    for e in employees:
        api_post("/hr/employees", e, f"موظف: {e['first_name']} {e['last_name']} ({e['position_title']})")

# ========================================
# 9. FISCAL YEAR
# ========================================
def setup_fiscal_year():
    print("\n" + "="*60)
    print("📌 9. إنشاء السنة المالية 2026")
    print("="*60)
    
    api_post("/accounting/fiscal-years", {
        "year": 2026,
        "start_date": "2026-01-01",
        "end_date": "2026-12-31"
    }, "السنة المالية 2026 (يناير - ديسمبر)")

# ========================================
# 10. CHART OF ACCOUNTS (Additional)
# ========================================
def setup_accounts():
    print("\n" + "="*60)
    print("📌 10. إنشاء حسابات إضافية في شجرة الحسابات")
    print("="*60)
    
    # Get existing accounts to find parent IDs
    accounts = api_get("/accounting/accounts", "accounts")
    if not accounts:
        print("  ⚠️ لا يمكن قراءة شجرة الحسابات")
        return
    
    # Build map of account numbers to IDs  
    acct_map = {}
    if isinstance(accounts, list):
        for a in accounts:
            num = a.get("account_number", "")
            acct_map[num] = a["id"]
    elif isinstance(accounts, dict) and "items" in accounts:
        for a in accounts["items"]:
            num = a.get("account_number", "")
            acct_map[num] = a["id"]
    
    # Identify key parent accounts
    # We need to check what's already there and only add what's missing
    existing_numbers = set(acct_map.keys())
    
    print(f"  ℹ️  عدد الحسابات الموجودة: {len(existing_numbers)}")
    
    # Additional accounts from test scenario 2.1
    additional = [
        {"account_number": "2301", "name": "زكاة مستحقة", "name_en": "Zakat Payable", "account_type": "liability"},
        {"account_number": "6101", "name": "أرباح فروق عملة", "name_en": "Currency Exchange Gains", "account_type": "revenue"},
        {"account_number": "6102", "name": "خسائر فروق عملة", "name_en": "Currency Exchange Losses", "account_type": "expense"},
    ]
    
    for acct in additional:
        if acct["account_number"] not in existing_numbers:
            api_post("/accounting/accounts", acct, f"حساب: {acct['account_number']} - {acct['name']}")
        else:
            print(f"  ℹ️  الحساب {acct['account_number']} موجود مسبقاً")

# ========================================
# 11. OPENING BALANCE JOURNAL ENTRIES  
# ========================================
def setup_opening_balances():
    print("\n" + "="*60)
    print("📌 11. قيود الأرصدة الافتتاحية")
    print("="*60)
    
    # Note: Treasury accounts auto-create opening balance JEs when opening_balance > 0
    # So we only need additional opening balance entries for:
    # - Inventory (300,000 SAR)
    # - Fixed Assets (200,000 SAR) 
    # - Accounts Receivable (150,000 SAR)
    # - Accounts Payable (80,000 SAR) - credit side
    
    # Get accounts to find correct IDs
    accounts = api_get("/accounting/accounts", "accounts")
    acct_map = {}
    if isinstance(accounts, list):
        for a in accounts:
            acct_map[a.get("account_number", "")] = a["id"]
            # Also map by name for lookup
            acct_map[a.get("name", "")] = a["id"]
    elif isinstance(accounts, dict) and "items" in accounts:
        for a in accounts["items"]:
            acct_map[a.get("account_number", "")] = a["id"]
            acct_map[a.get("name", "")] = a["id"]
    
    # Find key account IDs (try various common numbering)
    inv_id = acct_map.get("1301") or acct_map.get("1300") or acct_map.get("مخزون بضاعة") or acct_map.get("المخزون")
    fa_id = acct_map.get("1401") or acct_map.get("1400") or acct_map.get("أصول ثابتة") or acct_map.get("الأصول الثابتة")
    ar_id = acct_map.get("1201") or acct_map.get("1200") or acct_map.get("ذمم مدينة") or acct_map.get("الذمم المدينة")
    ap_id = acct_map.get("2101") or acct_map.get("2100") or acct_map.get("ذمم دائنة") or acct_map.get("الذمم الدائنة")
    
    # Find opening balances/equity account
    ob_id = None
    for key in ["3101", "3100", "3001", "3000", "أرصدة افتتاحية", "رأس المال", "رأس المال المدفوع", "حقوق الملكية"]:
        if key in acct_map:
            ob_id = acct_map[key]
            break
    
    if not ob_id:
        # Try retained earnings
        for key in ["3200", "3201", "أرباح مبقاة", "الأرباح المحتجزة"]:
            if key in acct_map:
                ob_id = acct_map[key]
                break
    
    print(f"  ℹ️  حسابات: مخزون={inv_id}, أصول ثابتة={fa_id}, ذمم مدينة={ar_id}, ذمم دائنة={ap_id}, رأسمال={ob_id}")
    
    if not all([inv_id, fa_id, ar_id, ap_id, ob_id]):
        print("  ⚠️ بعض الحسابات غير موجودة، سيتم إنشاء قيد جزئي فقط")
    
    # Build journal entry lines
    lines = []
    total_debit = 0
    total_credit = 0
    
    if inv_id:
        lines.append({"account_id": inv_id, "debit": 300000, "credit": 0, "description": "رصيد مخزون افتتاحي"})
        total_debit += 300000
    
    if fa_id:
        lines.append({"account_id": fa_id, "debit": 200000, "credit": 0, "description": "رصيد أصول ثابتة افتتاحي"})
        total_debit += 200000
    
    if ar_id:
        lines.append({"account_id": ar_id, "debit": 150000, "credit": 0, "description": "رصيد ذمم مدينة افتتاحي"})
        total_debit += 150000
    
    if ap_id:
        lines.append({"account_id": ap_id, "debit": 0, "credit": 80000, "description": "رصيد ذمم دائنة افتتاحي"})
        total_credit += 80000
    
    # Balance with opening balances / equity account
    if ob_id and lines:
        remaining = total_debit - total_credit
        lines.append({"account_id": ob_id, "debit": 0, "credit": remaining, "description": "أرصدة افتتاحية - رأس المال"})
        
        api_post("/accounting/journal-entries", {
            "date": "2026-01-01",
            "description": "قيد أرصدة افتتاحية — مخزون وأصول ثابتة وذمم",
            "reference": "OB-2026-001",
            "status": "posted",
            "lines": lines
        }, "قيد أرصدة افتتاحية (مخزون + أصول + ذمم)")

# ========================================
# 12. COST CENTERS
# ========================================
def setup_cost_centers():
    print("\n" + "="*60)
    print("📌 12. إنشاء مراكز التكلفة")
    print("="*60)
    
    cost_centers = [
        {"name": "الإدارة العامة", "name_en": "General Administration", "code": "CC-ADM"},
        {"name": "المبيعات", "name_en": "Sales", "code": "CC-SAL"},
        {"name": "الإنتاج", "name_en": "Production", "code": "CC-PRD"},
        {"name": "المشتريات", "name_en": "Purchasing", "code": "CC-PUR"},
    ]
    
    for cc in cost_centers:
        api_post("/accounting/cost-centers", cc, f"مركز تكلفة: {cc['name']}")


# ========================================
# MAIN
# ========================================
def main():
    print("=" * 60)
    print("🚀 إعداد بيانات الاختبار الأساسية — شركة أمان ERP")
    print("   Company: b08f3451")
    print("   Date: 2026-03-01")
    print("=" * 60)
    
    login()
    
    setup_currencies()
    setup_branches()
    setup_warehouses()
    setup_products()
    setup_customers()
    setup_suppliers()
    setup_treasury()
    setup_employees()
    setup_fiscal_year()
    setup_accounts()
    setup_cost_centers()
    setup_opening_balances()
    
    print("\n" + "=" * 60)
    print("✅ اكتمل إعداد البيانات الأساسية!")
    print("=" * 60)
    print("\n📋 ملخص البيانات المُدخلة:")
    print("   • 5 عملات (SAR, USD, EUR, AED, EGP) + أسعار صرف")
    print("   • 3 فروع (المقر - جدة - دبي)")
    print("   • 4 مستودعات")
    print("   • 5 فئات منتجات + 7 منتجات")
    print("   • 3 مجموعات عملاء + 6 عملاء")
    print("   • 2 مجموعات موردين + 5 موردين")
    print("   • 6 حسابات خزينة (4 بنوك + 3 صناديق) مع أرصدة افتتاحية")
    print("   • 9 موظفين (مع حسابات مستخدمين)")
    print("   • سنة مالية 2026 (12 فترة)")
    print("   • حسابات إضافية في شجرة الحسابات")
    print("   • 4 مراكز تكلفة")
    print("   • قيد أرصدة افتتاحية (مخزون + أصول + ذمم)")
    print("\n🔍 كل العمليات مسجلة في سجل التدقيق:")
    print("   http://localhost:5173/admin/audit-logs")

if __name__ == "__main__":
    main()
