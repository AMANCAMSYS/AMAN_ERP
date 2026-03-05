#!/usr/bin/env python3
"""
Setup Test Data for AMAN ERP - Remote Server
Company: ba2f6dc3 @ http://64.225.49.118

Base/master data ONLY — No purchase/sales transactions.
Based on setup_test_data.py structure.
"""

import requests
import json
import sys
import time

BASE_URL = "http://64.225.49.118/api"
COMPANY_CODE = "ba2f6dc3"
USERNAME = "vvvv"
PASSWORD = "As123321"
TOKEN = None

# ── Counters ──
stats = {"created": 0, "skipped": 0, "errors": 0}

def login():
    global TOKEN
    resp = requests.post(f"{BASE_URL}/auth/login", data={
        "username": USERNAME,
        "password": PASSWORD,
        "company_code": COMPANY_CODE
    })
    if resp.status_code != 200:
        print(f"❌ Login failed: {resp.text}")
        sys.exit(1)
    TOKEN = resp.json()["access_token"]
    print(f"✅ Login successful as {USERNAME}")

def headers():
    return {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def api_post(endpoint, data, desc=""):
    resp = requests.post(f"{BASE_URL}{endpoint}", json=data, headers=headers())
    if resp.status_code in [200, 201]:
        result = resp.json()
        rid = result.get("id", result.get("entry_id", ""))
        print(f"  ✅ {desc} (id={rid})")
        stats["created"] += 1
        return result
    elif resp.status_code == 409 or "already exists" in resp.text.lower() or "موجود" in resp.text:
        print(f"  ⏭️  {desc}: already exists")
        stats["skipped"] += 1
        return None
    else:
        print(f"  ❌ {desc}: {resp.status_code} - {resp.text[:300]}")
        stats["errors"] += 1
        return None

def api_put(endpoint, data, desc=""):
    resp = requests.put(f"{BASE_URL}{endpoint}", json=data, headers=headers())
    if resp.status_code in [200, 201]:
        result = resp.json()
        print(f"  ✅ {desc}")
        stats["created"] += 1
        return result
    else:
        print(f"  ❌ PUT {desc}: {resp.status_code} - {resp.text[:300]}")
        stats["errors"] += 1
        return None

def api_get(endpoint, desc=""):
    resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers())
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"  ❌ GET {desc}: {resp.status_code} - {resp.text[:200]}")
        return None


# ═══════════════════════════════════════════
# 1. FISCAL YEAR (must be first for any JE to work)
# ═══════════════════════════════════════════
def setup_fiscal_year():
    print("\n" + "="*60)
    print("📌 1. إنشاء السنة المالية 2026")
    print("="*60)
    
    existing = api_get("/accounting/fiscal-years", "fiscal years")
    if existing and len(existing) > 0:
        print("  ℹ️  سنة مالية موجودة مسبقاً")
        return
    
    api_post("/accounting/fiscal-years", {
        "year": 2026,
        "start_date": "2026-01-01",
        "end_date": "2026-12-31"
    }, "السنة المالية 2026 (يناير - ديسمبر)")


# ═══════════════════════════════════════════
# 2. CURRENCIES & EXCHANGE RATES
# ═══════════════════════════════════════════
def setup_currencies():
    print("\n" + "="*60)
    print("📌 2. إعداد العملات وأسعار الصرف")
    print("="*60)
    
    currencies = api_get("/accounting/currencies/", "currencies")
    existing = {c["code"]: c for c in (currencies or [])}
    
    if "SAR" in existing:
        print(f"  ℹ️  SAR موجود (id={existing['SAR']['id']})")
    
    currency_data = [
        {"code": "USD", "name": "دولار أمريكي", "name_en": "US Dollar", "symbol": "$", "is_base": False, "current_rate": 3.75, "is_active": True},
        {"code": "EUR", "name": "يورو", "name_en": "Euro", "symbol": "€", "is_base": False, "current_rate": 4.10, "is_active": True},
        {"code": "AED", "name": "درهم إماراتي", "name_en": "UAE Dirham", "symbol": "د.إ", "is_base": False, "current_rate": 1.02, "is_active": True},
        {"code": "EGP", "name": "جنيه مصري", "name_en": "Egyptian Pound", "symbol": "ج.م", "is_base": False, "current_rate": 0.077, "is_active": True},
    ]
    
    for c in currency_data:
        if c["code"] in existing:
            api_put(f"/accounting/currencies/{existing[c['code']]['id']}", c, f"تحديث {c['code']}")
        else:
            api_post("/accounting/currencies/", c, f"إنشاء {c['code']}")
    
    # Add exchange rates
    print("\n  📊 إضافة أسعار الصرف ليوم 2026-03-01:")
    currencies = api_get("/accounting/currencies/", "reload") or []
    rates = {"USD": 3.75, "EUR": 4.10, "AED": 1.02, "EGP": 0.077}
    for c in currencies:
        if c["code"] in rates:
            api_post("/accounting/currencies/rates", {
                "currency_id": c["id"],
                "rate": rates[c["code"]],
                "rate_date": "2026-03-01",
                "source": "manual"
            }, f"سعر صرف {c['code']} = {rates[c['code']]}")


# ═══════════════════════════════════════════
# 3. BRANCHES
# ═══════════════════════════════════════════
def setup_branches():
    print("\n" + "="*60)
    print("📌 3. تحديث/إنشاء الفروع")
    print("="*60)
    
    branches = api_get("/branches", "branches") or []
    existing_codes = {b["branch_code"]: b for b in branches}
    
    # Update existing HQ
    if "BR001" in existing_codes:
        b = existing_codes["BR001"]
        api_put(f"/branches/{b['id']}", {
            "branch_name": "المقر الرئيسي - الرياض",
            "branch_name_en": "Headquarters - Riyadh",
            "branch_code": "HQ",
            "city": "الرياض",
            "country": "المملكة العربية السعودية",
            "country_code": "SA",
            "default_currency": "SAR",
            "is_default": True,
            "is_active": True
        }, "تحديث المقر الرئيسي → HQ")
    
    # Jeddah
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
    
    # Dubai
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


# ═══════════════════════════════════════════
# 4. WAREHOUSES
# ═══════════════════════════════════════════
def setup_warehouses():
    print("\n" + "="*60)
    print("📌 4. إنشاء المستودعات")
    print("="*60)
    
    branches = api_get("/branches", "branches") or []
    bmap = {b["branch_code"]: b["id"] for b in branches}
    hq = bmap.get("HQ", bmap.get("BR001", 1))
    jed = bmap.get("JED", 2)
    dxb = bmap.get("DXB", 3)
    
    # Update existing default warehouse
    existing_wh = api_get("/inventory/warehouses", "warehouses") or []
    for w in existing_wh:
        if w.get("code") == "WH001":
            api_put(f"/inventory/warehouses/{w['id']}", {
                "name": "مستودع مواد خام - الرياض",
                "code": "WH-RAW-RYD",
                "location": "المنطقة الصناعية، الرياض",
                "branch_id": hq,
                "is_default": True
            }, "تحديث المستودع الرئيسي → WH-RAW-RYD")
    
    wh_data = [
        {"name": "مستودع منتجات تامة - الرياض", "code": "WH-FIN-RYD", "location": "الرياض", "branch_id": hq},
        {"name": "مستودع جدة الرئيسي", "code": "WH-JED", "location": "جدة", "branch_id": jed},
        {"name": "مستودع دبي", "code": "WH-DXB", "location": "دبي", "branch_id": dxb},
    ]
    
    for wh in wh_data:
        api_post("/inventory/warehouses", wh, f"مستودع: {wh['name']}")


# ═══════════════════════════════════════════
# 5. PRODUCT CATEGORIES & PRODUCTS
# ═══════════════════════════════════════════
def setup_products():
    print("\n" + "="*60)
    print("📌 5. إنشاء فئات المنتجات والمنتجات")
    print("="*60)
    
    # Categories
    cats = {}
    for cat in [
        {"name": "مواد خام", "code": "RAW"},
        {"name": "منتجات تامة", "code": "FIN"},
        {"name": "مستلزمات", "code": "SUP"},
        {"name": "خدمات", "code": "SRV"},
        {"name": "أصول ثابتة", "code": "AST"},
    ]:
        result = api_post("/inventory/categories", cat, f"فئة: {cat['name']}")
        if result:
            cats[cat["code"]] = result["id"]
    
    # Products
    products = [
        {
            "item_code": "ALU-001", "item_name": "لوح ألمنيوم 3 مم", "item_name_en": "Aluminum Sheet 3mm",
            "item_type": "product", "unit": "متر", "selling_price": 150, "buying_price": 80,
            "tax_rate": 15, "category_id": cats.get("RAW"),
            "description": "لوح ألمنيوم بسماكة 3 مم للتصنيع"
        },
        {
            "item_code": "WOD-001", "item_name": "خشب طبيعي MDF", "item_name_en": "Natural MDF Wood",
            "item_type": "product", "unit": "لوح", "selling_price": 200, "buying_price": 120,
            "tax_rate": 15, "category_id": cats.get("RAW"),
            "description": "خشب MDF طبيعي للنجارة"
        },
        {
            "item_code": "GLS-001", "item_name": "زجاج مزدوج 6 مم", "item_name_en": "Double Glass 6mm",
            "item_type": "product", "unit": "متر مربع", "selling_price": 180, "buying_price": 95,
            "tax_rate": 15, "category_id": cats.get("RAW"),
            "description": "زجاج مزدوج عازل للحرارة والصوت"
        },
        {
            "item_code": "DOOR-001", "item_name": "باب ألمنيوم جاهز", "item_name_en": "Ready Aluminum Door",
            "item_type": "product", "unit": "قطعة", "selling_price": 1500, "buying_price": 900,
            "tax_rate": 15, "category_id": cats.get("FIN"),
            "description": "باب ألمنيوم جاهز للتركيب"
        },
        {
            "item_code": "WIN-001", "item_name": "نافذة زجاج مزدوج", "item_name_en": "Double Glass Window",
            "item_type": "product", "unit": "قطعة", "selling_price": 800, "buying_price": 450,
            "tax_rate": 15, "category_id": cats.get("FIN"),
            "description": "نافذة زجاج مزدوج عازلة"
        },
        {
            "item_code": "CRT-001", "item_name": "حائط ستائري", "item_name_en": "Curtain Wall Panel",
            "item_type": "product", "unit": "متر مربع", "selling_price": 2500, "buying_price": 1400,
            "tax_rate": 15, "category_id": cats.get("FIN"),
            "description": "حائط ستائري ألمنيوم وزجاج"
        },
        {
            "item_code": "SCR-001", "item_name": "مسامير ستنلس ستيل", "item_name_en": "Stainless Steel Screws",
            "item_type": "product", "unit": "علبة", "selling_price": 25, "buying_price": 10,
            "tax_rate": 15, "category_id": cats.get("SUP"),
            "description": "مسامير ستنلس ستيل متنوعة الأحجام"
        },
        {
            "item_code": "RBR-001", "item_name": "إطار مطاطي عازل", "item_name_en": "Rubber Seal Strip",
            "item_type": "product", "unit": "متر", "selling_price": 15, "buying_price": 5,
            "tax_rate": 15, "category_id": cats.get("SUP"),
            "description": "إطار مطاطي عازل للأبواب والنوافذ"
        },
        {
            "item_code": "SRV-001", "item_name": "خدمة تركيب", "item_name_en": "Installation Service",
            "item_type": "service", "unit": "ساعة", "selling_price": 200, "buying_price": 0,
            "tax_rate": 15, "category_id": cats.get("SRV"),
            "description": "خدمة تركيب أبواب ونوافذ"
        },
        {
            "item_code": "SRV-002", "item_name": "خدمة صيانة", "item_name_en": "Maintenance Service",
            "item_type": "service", "unit": "زيارة", "selling_price": 350, "buying_price": 0,
            "tax_rate": 15, "category_id": cats.get("SRV"),
            "description": "خدمة صيانة دورية"
        },
    ]
    
    for p in products:
        api_post("/inventory/products", p, f"منتج: {p['item_code']} - {p['item_name']}")


# ═══════════════════════════════════════════
# 6. CUSTOMER GROUPS & CUSTOMERS
# ═══════════════════════════════════════════
def setup_customers():
    print("\n" + "="*60)
    print("📌 6. إنشاء مجموعات العملاء والعملاء")
    print("="*60)
    
    branches = api_get("/branches", "branches") or []
    bmap = {b["branch_code"]: b["id"] for b in branches}
    hq = bmap.get("HQ", bmap.get("BR001", 1))
    jed = bmap.get("JED", 2)
    dxb = bmap.get("DXB", 3)
    
    # groups
    group_ids = {}
    for g in [
        {"group_name": "عملاء جملة", "group_name_en": "Wholesale Customers", "discount_percentage": 5, "payment_days": 30},
        {"group_name": "عملاء تجزئة", "group_name_en": "Retail Customers", "discount_percentage": 0, "payment_days": 15},
        {"group_name": "عملاء خارجيين", "group_name_en": "International Customers", "discount_percentage": 3, "payment_days": 45},
    ]:
        result = api_post("/sales/customer-groups", g, f"مجموعة عملاء: {g['group_name']}")
        if result:
            group_ids[g["group_name"]] = result.get("id")
    
    # customers
    customers = [
        {
            "name": "شركة النور للإلكترونيات", "name_en": "Al Nour Electronics Co.",
            "phone": "0112345678", "email": "info@alnour.sa", "city": "الرياض",
            "country": "SA", "credit_limit": 500000, "payment_terms": 30,
            "group_id": group_ids.get("عملاء جملة"), "branch_id": hq, "currency": "SAR",
            "tax_number": "300098765600001"
        },
        {
            "name": "مؤسسة الفجر التجارية", "name_en": "Al Fajr Trading Est.",
            "phone": "0126789012", "email": "info@alfajr.sa", "city": "جدة",
            "country": "SA", "credit_limit": 100000, "payment_terms": 15,
            "group_id": group_ids.get("عملاء تجزئة"), "branch_id": jed, "currency": "SAR",
            "tax_number": "300098765600002"
        },
        {
            "name": "Gulf Trading LLC", "name_en": "Gulf Trading LLC",
            "phone": "+97145678901", "email": "info@gulftrading.ae", "city": "Dubai",
            "country": "AE", "credit_limit": 200000, "payment_terms": 45,
            "group_id": group_ids.get("عملاء خارجيين"), "branch_id": dxb, "currency": "AED",
            "tax_number": "TRN100234567"
        },
        {
            "name": "Euro Supplies GmbH", "name_en": "Euro Supplies GmbH",
            "phone": "+4930123456", "email": "info@eurosupplies.de", "city": "Berlin",
            "country": "DE", "credit_limit": 150000, "payment_terms": 45,
            "group_id": group_ids.get("عملاء خارجيين"), "branch_id": dxb, "currency": "EUR"
        },
        {
            "name": "مؤسسة السلام للمقاولات", "name_en": "Al Salam Contracting Est.",
            "phone": "0113456789", "email": "info@alsalam.sa", "city": "الرياض",
            "country": "SA", "credit_limit": 300000, "payment_terms": 30,
            "group_id": group_ids.get("عملاء جملة"), "branch_id": hq, "currency": "SAR",
            "tax_number": "300098765600003"
        },
        {
            "name": "Cairo Import Co.", "name_en": "Cairo Import Co.",
            "phone": "+20234567890", "email": "info@cairoimport.eg", "city": "Cairo",
            "country": "EG", "credit_limit": 5000000, "payment_terms": 45,
            "group_id": group_ids.get("عملاء خارجيين"), "branch_id": hq, "currency": "EGP"
        },
    ]
    for c in customers:
        api_post("/sales/customers", c, f"عميل: {c['name']}")


# ═══════════════════════════════════════════
# 7. SUPPLIER GROUPS & SUPPLIERS
# ═══════════════════════════════════════════
def setup_suppliers():
    print("\n" + "="*60)
    print("📌 7. إنشاء مجموعات الموردين والموردين")
    print("="*60)
    
    branches = api_get("/branches", "branches") or []
    bmap = {b["branch_code"]: b["id"] for b in branches}
    hq = bmap.get("HQ", bmap.get("BR001", 1))
    jed = bmap.get("JED", 2)
    dxb = bmap.get("DXB", 3)
    
    group_ids = {}
    for g in [
        {"group_name": "موردون محليون", "group_name_en": "Local Suppliers", "payment_days": 30},
        {"group_name": "موردون خارجيون", "group_name_en": "International Suppliers", "payment_days": 60},
    ]:
        result = api_post("/buying/supplier-groups", g, f"مجموعة موردين: {g['group_name']}")
        if result:
            gid = result.get("id") or result.get("group_id")
            if gid:
                group_ids[g["group_name"]] = gid
    
    suppliers = [
        {
            "name": "مصنع الألمنيوم الوطني", "name_en": "National Aluminum Factory",
            "phone": "0114567890", "email": "info@natalu.sa", "address": "المنطقة الصناعية، الرياض",
            "currency": "SAR", "tax_number": "300098765600010",
            "group_id": group_ids.get("موردون محليون"), "branch_id": hq
        },
        {
            "name": "China Materials Co.", "name_en": "China Materials Co.",
            "phone": "+862012345678", "email": "sales@chinamaterials.cn", "address": "Guangzhou, China",
            "currency": "USD",
            "group_id": group_ids.get("موردون خارجيون"), "branch_id": hq
        },
        {
            "name": "مورد الخشب المتحد", "name_en": "United Wood Supplier",
            "phone": "0125678901", "email": "info@unitedwood.sa", "address": "منطقة الميناء، جدة",
            "currency": "SAR", "tax_number": "300098765600011",
            "group_id": group_ids.get("موردون محليون"), "branch_id": jed
        },
        {
            "name": "European Parts AG", "name_en": "European Parts AG",
            "phone": "+4989123456", "email": "info@europarts.de", "address": "Munich, Germany",
            "currency": "EUR",
            "group_id": group_ids.get("موردون خارجيون"), "branch_id": dxb
        },
        {
            "name": "Nile Trading Co.", "name_en": "Nile Trading Co.",
            "phone": "+201234567890", "email": "info@niletrading.eg", "address": "Cairo, Egypt",
            "currency": "EGP",
            "group_id": group_ids.get("موردون خارجيون"), "branch_id": hq
        },
    ]
    for s in suppliers:
        api_post("/inventory/suppliers", s, f"مورد: {s['name']}")


# ═══════════════════════════════════════════
# 8. TREASURY ACCOUNTS
# ═══════════════════════════════════════════
def setup_treasury():
    print("\n" + "="*60)
    print("📌 8. إنشاء حسابات الخزينة (البنوك والصناديق)")
    print("="*60)
    
    branches = api_get("/branches", "branches") or []
    bmap = {b["branch_code"]: b["id"] for b in branches}
    hq = bmap.get("HQ", bmap.get("BR001", 1))
    jed = bmap.get("JED", 2)
    dxb = bmap.get("DXB", 3)
    
    accounts = [
        {
            "name": "البنك الأهلي - الرياض", "name_en": "Al Ahli Bank - Riyadh",
            "account_type": "bank", "currency": "SAR", "branch_id": hq,
            "bank_name": "البنك الأهلي السعودي", "account_number": "40001234567",
            "iban": "SA0380000000608010167519",
            "opening_balance": 500000, "exchange_rate": 1.0
        },
        {
            "name": "صندوق نقدي المقر", "name_en": "HQ Cash Box",
            "account_type": "cash", "currency": "SAR", "branch_id": hq,
            "opening_balance": 50000, "exchange_rate": 1.0
        },
        {
            "name": "بنك الراجحي - جدة", "name_en": "Al Rajhi Bank - Jeddah",
            "account_type": "bank", "currency": "SAR", "branch_id": jed,
            "bank_name": "مصرف الراجحي", "account_number": "50001234567",
            "iban": "SA4420000000608010167520",
            "opening_balance": 200000, "exchange_rate": 1.0
        },
        {
            "name": "صندوق نقدي جدة", "name_en": "Jeddah Cash Box",
            "account_type": "cash", "currency": "SAR", "branch_id": jed,
            "opening_balance": 30000, "exchange_rate": 1.0
        },
        {
            "name": "بنك دبي الإسلامي", "name_en": "Dubai Islamic Bank",
            "account_type": "bank", "currency": "AED", "branch_id": dxb,
            "bank_name": "بنك دبي الإسلامي", "account_number": "AE1234567890",
            "iban": "AE070331234567890123456",
            "opening_balance": 100000, "exchange_rate": 1.02
        },
        {
            "name": "صندوق نقدي دبي", "name_en": "Dubai Cash Box",
            "account_type": "cash", "currency": "AED", "branch_id": dxb,
            "opening_balance": 20000, "exchange_rate": 1.02
        },
        {
            "name": "بنك مصر", "name_en": "Bank Misr",
            "account_type": "bank", "currency": "EGP", "branch_id": hq,
            "bank_name": "بنك مصر", "account_number": "EG1234567890",
            "iban": "EG380019000500000000263180002",
            "opening_balance": 500000, "exchange_rate": 0.077
        },
    ]
    for t in accounts:
        api_post("/treasury/accounts", t, f"خزينة: {t['name']} ({t['account_type']}) - {t['currency']}")


# ═══════════════════════════════════════════
# 9. COST CENTERS
# ═══════════════════════════════════════════
def setup_cost_centers():
    print("\n" + "="*60)
    print("📌 9. إنشاء مراكز التكلفة")
    print("="*60)
    
    centers = [
        {"center_name": "الإدارة العامة", "center_name_en": "General Administration", "center_code": "CC-ADM"},
        {"center_name": "المبيعات", "center_name_en": "Sales", "center_code": "CC-SAL"},
        {"center_name": "الإنتاج", "center_name_en": "Production", "center_code": "CC-PRD"},
        {"center_name": "المشتريات", "center_name_en": "Purchasing", "center_code": "CC-PUR"},
        {"center_name": "المستودعات", "center_name_en": "Warehousing", "center_code": "CC-WH"},
        {"center_name": "الموارد البشرية", "center_name_en": "Human Resources", "center_code": "CC-HR"},
    ]
    for cc in centers:
        api_post("/cost-centers/", cc, f"مركز تكلفة: {cc['center_name']}")


# ═══════════════════════════════════════════
# 10. EMPLOYEES
# ═══════════════════════════════════════════
def setup_employees():
    print("\n" + "="*60)
    print("📌 10. إنشاء الموظفين (مع حسابات مستخدمين)")
    print("="*60)
    
    branches = api_get("/branches", "branches") or []
    bmap = {b["branch_code"]: b["id"] for b in branches}
    hq = bmap.get("HQ", bmap.get("BR001", 1))
    jed = bmap.get("JED", 2)
    dxb = bmap.get("DXB", 3)
    
    employees = [
        {
            "first_name": "أحمد", "last_name": "محمد",
            "first_name_en": "Ahmed", "last_name_en": "Mohammed",
            "email": "ahmed@aman.com", "phone": "0501234567",
            "position_title": "مدير مالي", "department_name": "المالية",
            "salary": 25000, "housing_allowance": 5000, "transport_allowance": 2000,
            "currency": "SAR", "nationality": "SA", "hire_date": "2025-01-01",
            "create_user": True, "username": "ahmed", "password": "Test1234!",
            "role": "accountant",
            "branch_id": hq, "allowed_branch_ids": [hq]
        },
        {
            "first_name": "سارة", "last_name": "خالد",
            "first_name_en": "Sara", "last_name_en": "Khaled",
            "email": "sara@aman.com", "phone": "0502345678",
            "position_title": "محاسبة", "department_name": "المالية",
            "salary": 15000, "housing_allowance": 3000, "transport_allowance": 1500,
            "currency": "SAR", "nationality": "SA", "hire_date": "2025-03-01",
            "create_user": True, "username": "sara", "password": "Test1234!",
            "role": "accountant",
            "branch_id": jed, "allowed_branch_ids": [jed]
        },
        {
            "first_name": "محمد", "last_name": "علي",
            "first_name_en": "Mohammed", "last_name_en": "Ali",
            "email": "mali@aman.com", "phone": "0503456789",
            "position_title": "مندوب مبيعات", "department_name": "المبيعات",
            "salary": 12000, "housing_allowance": 2500, "transport_allowance": 2000,
            "currency": "SAR", "nationality": "SA", "hire_date": "2025-06-01",
            "create_user": True, "username": "mohammed", "password": "Test1234!",
            "role": "sales",
            "branch_id": hq, "allowed_branch_ids": [hq]
        },
        {
            "first_name": "فاطمة", "last_name": "حسن",
            "first_name_en": "Fatma", "last_name_en": "Hassan",
            "email": "fatma@aman.com", "phone": "0504567890",
            "position_title": "مسؤولة مشتريات", "department_name": "المشتريات",
            "salary": 14000, "housing_allowance": 3000, "transport_allowance": 1500,
            "currency": "SAR", "nationality": "EG", "hire_date": "2025-04-01",
            "create_user": True, "username": "fatma", "password": "Test1234!",
            "role": "purchasing",
            "branch_id": jed, "allowed_branch_ids": [jed]
        },
        {
            "first_name": "خالد", "last_name": "سعيد",
            "first_name_en": "Khaled", "last_name_en": "Saeed",
            "email": "khaled@aman.com", "phone": "0505678901",
            "position_title": "مدير المستودعات", "department_name": "المستودعات",
            "salary": 16000, "housing_allowance": 3500, "transport_allowance": 2000,
            "currency": "SAR", "nationality": "SA", "hire_date": "2025-02-01",
            "create_user": True, "username": "khaled", "password": "Test1234!",
            "role": "warehouse",
            "branch_id": hq, "allowed_branch_ids": [hq, jed]
        },
        {
            "first_name": "نورة", "last_name": "أحمد",
            "first_name_en": "Noura", "last_name_en": "Ahmed",
            "email": "noura@aman.com", "phone": "0506789012",
            "position_title": "مسؤولة موارد بشرية", "department_name": "الموارد البشرية",
            "salary": 13000, "housing_allowance": 2500, "transport_allowance": 1500,
            "currency": "SAR", "nationality": "SA", "hire_date": "2025-05-01",
            "create_user": True, "username": "noura", "password": "Test1234!",
            "role": "hr",
            "branch_id": jed, "allowed_branch_ids": [jed]
        },
        {
            "first_name": "ياسر", "last_name": "حمد",
            "first_name_en": "Yaser", "last_name_en": "Hamad",
            "email": "yaser@aman.com", "phone": "0507890123",
            "position_title": "مدير إنتاج", "department_name": "الإنتاج",
            "salary": 18000, "housing_allowance": 4000, "transport_allowance": 2000,
            "currency": "SAR", "nationality": "SA", "hire_date": "2025-01-15",
            "create_user": True, "username": "yaser", "password": "Test1234!",
            "role": "production",
            "branch_id": hq, "allowed_branch_ids": [hq]
        },
        {
            "first_name": "ليلى", "last_name": "عبدالله",
            "first_name_en": "Layla", "last_name_en": "Abdullah",
            "email": "layla@aman.com", "phone": "0508901234",
            "position_title": "أمينة صندوق", "department_name": "نقاط البيع",
            "salary": 10000, "housing_allowance": 2000, "transport_allowance": 1500,
            "currency": "SAR", "nationality": "SA", "hire_date": "2025-07-01",
            "create_user": True, "username": "layla", "password": "Test1234!",
            "role": "pos",
            "branch_id": jed, "allowed_branch_ids": [jed]
        },
        {
            "first_name": "حسين", "last_name": "عمار",
            "first_name_en": "Hussein", "last_name_en": "Ammar",
            "email": "hussein@aman.com", "phone": "0509012345",
            "position_title": "مندوب مبيعات", "department_name": "المبيعات",
            "salary": 12000, "housing_allowance": 2500, "transport_allowance": 2000,
            "currency": "AED", "nationality": "AE", "hire_date": "2025-08-01",
            "create_user": True, "username": "hussein", "password": "Test1234!",
            "role": "sales",
            "branch_id": dxb, "allowed_branch_ids": [dxb]
        },
    ]
    for e in employees:
        api_post("/hr/employees", e, f"موظف: {e['first_name']} {e['last_name']} ({e['position_title']})")


# ═══════════════════════════════════════════
# 11. OPENING BALANCES (via dedicated endpoint)
# ═══════════════════════════════════════════
def setup_opening_balances():
    print("\n" + "="*60)
    print("📌 11. قيود الأرصدة الافتتاحية (المخزون + الأصول + الذمم)")
    print("="*60)
    
    accounts = api_get("/accounting/accounts", "accounts") or []
    acct_map = {}
    for a in accounts:
        acct_map[a.get("account_number", "")] = a["id"]
        acct_map[a.get("name", "")] = a["id"]
    
    # Find key accounts by common numbers in default chart
    # Standard AMAN chart: 1301=inventory, 14xx=fixed assets, 1201=AR, 2101=AP, 31xx=capital
    inv_id = None
    fa_id = None
    ar_id = None
    ap_id = None
    capital_id = None
    
    for num, aid in acct_map.items():
        if num in ("1301", "130101"):
            inv_id = aid
        elif num in ("1401", "140101", "1402"):
            fa_id = fa_id or aid
        elif num in ("1201", "120101"):
            ar_id = aid
        elif num in ("2101", "210101"):
            ap_id = aid
        elif num in ("3101", "310101", "31"):
            capital_id = capital_id or aid
    
    # Fallback: search by name
    for a in accounts:
        name = a.get("name", "")
        num = a.get("account_number", "")
        if not inv_id and ("مخزون" in name and "خام" not in name):
            inv_id = a["id"]
        if not fa_id and "أصول ثابتة" in name and not a.get("is_header"):
            fa_id = a["id"]
        if not ar_id and "ذمم مدينة" in name:
            ar_id = a["id"]
        if not ap_id and "ذمم دائنة" in name:
            ap_id = a["id"]
        if not capital_id and "رأس المال" in name and "مدفوع" not in name:
            capital_id = a["id"]
    
    print(f"  ℹ️  مخزون={inv_id}, أصول ثابتة={fa_id}, ذمم مدينة={ar_id}, ذمم دائنة={ap_id}, رأسمال={capital_id}")
    
    lines = []
    if inv_id:
        lines.append({"account_id": inv_id, "debit": 300000, "credit": 0, "description": "رصيد مخزون افتتاحي"})
    if fa_id:
        lines.append({"account_id": fa_id, "debit": 200000, "credit": 0, "description": "رصيد أصول ثابتة افتتاحي"})
    if ar_id:
        lines.append({"account_id": ar_id, "debit": 150000, "credit": 0, "description": "رصيد ذمم مدينة افتتاحي"})
    if ap_id:
        lines.append({"account_id": ap_id, "debit": 0, "credit": 80000, "description": "رصيد ذمم دائنة افتتاحي"})
    
    if lines:
        api_post("/accounting/opening-balances", {
            "date": "2026-01-01",
            "lines": lines
        }, "قيد أرصدة افتتاحية (مخزون + أصول + ذمم)")


# ═══════════════════════════════════════════
# 12. ACCOUNT MAPPINGS
# ═══════════════════════════════════════════
def setup_account_mappings():
    print("\n" + "="*60)
    print("📌 12. ربط الحسابات النظامية (Account Mappings)")
    print("="*60)
    
    # Get all accounts to build a map
    accounts = api_get("/accounting/accounts", "accounts") or []
    num_to_id = {}
    name_to_id = {}
    for a in accounts:
        num_to_id[a.get("account_number", "")] = a["id"]
        name_to_id[a.get("name", "")] = a["id"]
    
    # Standard account mappings based on default chart
    # We need to find the right account numbers
    mappings = {}
    
    # Helper to find account by trying multiple patterns
    def find_acct(*patterns):
        for p in patterns:
            if p in num_to_id:
                return num_to_id[p]
            if p in name_to_id:
                return name_to_id[p]
        return None
    
    mapping_defs = {
        "acc_map_cash_main": ["110101", "الصندوق الرئيسي"],
        "acc_map_bank": ["110102", "البنك"],
        "acc_map_ar": ["120101", "1201", "ذمم مدينة تجارية", "الذمم المدينة"],
        "acc_map_inventory": ["130101", "1301", "مخزون بضاعة", "المخزون"],
        "acc_map_raw_materials": ["130102", "1302", "مواد خام"],
        "acc_map_finished_goods": ["130103", "1303", "منتجات تامة"],
        "acc_map_wip": ["130104", "1304", "إنتاج تحت التشغيل"],
        "acc_map_prepaid_exp": ["130201", "1305", "مصروفات مدفوعة مقدماً"],
        "acc_map_fixed_assets": ["140101", "1401", "أصول ثابتة"],
        "acc_map_acc_depr": ["140201", "1402", "مجمع الإهلاك", "مجمع الاستهلاك"],
        "acc_map_ap": ["210101", "2101", "ذمم دائنة تجارية", "الذمم الدائنة"],
        "acc_map_vat_in": ["210301", "2103", "ضريبة القيمة المضافة - مدخلات"],
        "acc_map_vat_out": ["210302", "2104", "ضريبة القيمة المضافة - مخرجات"],
        "acc_map_accrued_expenses": ["210201", "2102", "مصروفات مستحقة"],
        "acc_map_gosi_payable": ["210401", "2105", "تأمينات اجتماعية مستحقة"],
        "acc_map_eos_provision": ["210501", "2106", "مخصص نهاية الخدمة"],
        "acc_map_sales_rev": ["410101", "4101", "إيرادات مبيعات"],
        "acc_map_service_rev": ["410102", "4102", "إيرادات خدمات"],
        "acc_map_cogs": ["510101", "5101", "تكلفة البضاعة المباعة"],
        "acc_map_salaries": ["520101", "5201", "رواتب وأجور"],
        "acc_map_rent_expense": ["520201", "5202", "إيجارات"],
        "acc_map_depr_exp": ["520301", "5203", "مصروف الإهلاك", "مصروف الاستهلاك"],
        "acc_map_general_expense": ["520401", "5204", "مصروفات عمومية"],
    }
    
    settings = {}
    for key, patterns in mapping_defs.items():
        aid = find_acct(*patterns)
        if aid:
            settings[key] = str(aid)
    
    if settings:
        resp = requests.post(f"{BASE_URL}/settings/bulk", json={"settings": settings}, headers=headers())
        if resp.status_code in [200, 201]:
            print(f"  ✅ تم ربط {len(settings)} حساب نظامي")
            stats["created"] += 1
        else:
            print(f"  ❌ فشل ربط الحسابات: {resp.status_code} - {resp.text[:200]}")
            stats["errors"] += 1
    else:
        print("  ⚠️ لم يتم العثور على أي حسابات لربطها")


# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════
def main():
    print("=" * 60)
    print("🚀 إعداد بيانات الاختبار الأساسية — شركة أمان ERP")
    print(f"   Server: {BASE_URL}")
    print(f"   Company: {COMPANY_CODE}")
    print(f"   Date: 2026-03-05")
    print("=" * 60)
    
    login()
    
    setup_fiscal_year()       # 1
    setup_currencies()        # 2
    setup_branches()          # 3
    setup_warehouses()        # 4
    setup_products()          # 5
    setup_customers()         # 6
    setup_suppliers()         # 7
    setup_treasury()          # 8
    setup_cost_centers()      # 9
    setup_employees()         # 10
    setup_opening_balances()  # 11
    setup_account_mappings()  # 12
    
    print("\n" + "=" * 60)
    print("✅ اكتمل إعداد البيانات الأساسية!")
    print(f"   Created: {stats['created']}")
    print(f"   Skipped: {stats['skipped']}")
    print(f"   Errors:  {stats['errors']}")
    print("=" * 60)
    print("\n📋 ملخص البيانات المُدخلة:")
    print("   • 5 عملات (SAR, USD, EUR, AED, EGP) + أسعار صرف")
    print("   • 3 فروع (المقر - جدة - دبي)")
    print("   • 4 مستودعات (مواد خام، منتجات تامة، جدة، دبي)")
    print("   • 5 فئات منتجات + 10 منتجات")
    print("   • 3 مجموعات عملاء + 6 عملاء (محلي + دولي)")
    print("   • 2 مجموعات موردين + 5 موردين (محلي + دولي)")
    print("   • 7 حسابات خزينة (4 بنوك + 3 صناديق) مع أرصدة افتتاحية")
    print("   • 6 مراكز تكلفة")
    print("   • 9 موظفين (مع حسابات مستخدمين)")
    print("   • قيد أرصدة افتتاحية (مخزون + أصول + ذمم)")
    print("   • ربط الحسابات النظامية")

if __name__ == "__main__":
    main()
