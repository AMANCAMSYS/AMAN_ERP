#!/usr/bin/env python3
"""
Comprehensive test data entry script for AMAN ERP
Company: 39a597c9 (SAR base currency)
User: bbbb / As123321

Exchange Rate Logic:
  base_amount = foreign_amount × exchange_rate
  1 USD = 3.75 SAR, 1 EUR = 4.10 SAR, 1 AED = 1.02 SAR
"""
import requests
import json
import sys
from datetime import datetime

BASE = "http://localhost:8000"
COMPANY_ID = "39a597c9"
USERNAME = "bbbb"
PASSWORD = "As123321"

# ===== Storage for created IDs =====
IDS = {}

def login():
    r = requests.post(f"{BASE}/api/auth/login", data={
        "username": USERNAME,
        "password": PASSWORD,
        "company_id": COMPANY_ID
    })
    r.raise_for_status()
    token = r.json()["access_token"]
    print(f"✅ Login successful")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def api(method, path, data=None, headers=None):
    url = f"{BASE}{path}"
    try:
        if method == "GET":
            r = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            r = requests.post(url, headers=headers, json=data, timeout=30)
        elif method == "PUT":
            r = requests.put(url, headers=headers, json=data, timeout=30)
        else:
            r = requests.request(method, url, headers=headers, json=data, timeout=30)
        
        try:
            result = r.json()
        except:
            result = {"status_code": r.status_code, "text": r.text[:200]}
        
        if r.status_code >= 400:
            detail = result.get("detail", result) if isinstance(result, dict) else result
            print(f"  ⚠️  {method} {path} → {r.status_code}: {detail}")
            return result
        
        return result
    except Exception as e:
        print(f"  ❌ {method} {path} → Error: {e}")
        return None

def step(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")

# ============================================================
# PHASE 1: CURRENCIES
# ============================================================
def setup_currencies(h):
    step("المرحلة 1: إعداد العملات")
    
    # Check existing
    existing = api("GET", "/api/accounting/currencies/", headers=h)
    existing_codes = [c["code"] for c in existing] if isinstance(existing, list) else []
    print(f"  العملات الموجودة: {existing_codes}")
    
    currencies = [
        {"code": "USD", "name": "دولار أمريكي", "name_en": "US Dollar", "symbol": "$",
         "is_base": False, "current_rate": 3.75, "is_active": True},
        {"code": "EUR", "name": "يورو", "name_en": "Euro", "symbol": "€",
         "is_base": False, "current_rate": 4.10, "is_active": True},
        {"code": "AED", "name": "درهم إماراتي", "name_en": "UAE Dirham", "symbol": "د.إ",
         "is_base": False, "current_rate": 1.02, "is_active": True},
    ]
    
    for c in currencies:
        if c["code"] in existing_codes:
            print(f"  ℹ️  {c['code']} موجودة مسبقاً")
            continue
        result = api("POST", "/api/accounting/currencies/", c, h)
        if result and isinstance(result, dict) and result.get("id"):
            IDS[f"currency_{c['code']}"] = result["id"]
            print(f"  ✅ {c['code']} - {c['name']} (rate={c['current_rate']})")
        elif isinstance(result, dict) and "already" in str(result.get("detail", "")):
            print(f"  ℹ️  {c['code']} موجودة مسبقاً")
    
    # Refresh currency IDs
    all_curr = api("GET", "/api/accounting/currencies/", headers=h)
    if isinstance(all_curr, list):
        for c in all_curr:
            IDS[f"currency_{c['code']}"] = c["id"]
            print(f"  → {c['code']} id={c['id']} rate={c['current_rate']} base={c['is_base']}")

# ============================================================
# PHASE 2: BRANCHES
# ============================================================
def setup_branches(h):
    step("المرحلة 2: إعداد الفروع")
    
    existing = api("GET", "/api/branches", headers=h)
    existing_codes = [b["branch_code"] for b in existing] if isinstance(existing, list) else []
    
    # Store main branch
    if existing:
        for b in existing:
            IDS[f"branch_{b['branch_code']}"] = b["id"]
            print(f"  ℹ️  فرع موجود: {b['branch_name']} (id={b['id']})")
    
    branches = [
        {"branch_name": "فرع جدة", "branch_name_en": "Jeddah Branch", "branch_code": "BR002",
         "city": "جدة", "country": "السعودية", "country_code": "SA", "default_currency": "SAR"},
        {"branch_name": "فرع دبي", "branch_name_en": "Dubai Branch", "branch_code": "BR003",
         "city": "دبي", "country": "الإمارات", "country_code": "AE", "default_currency": "AED"},
    ]
    
    for b in branches:
        if b["branch_code"] in existing_codes:
            continue
        result = api("POST", "/api/branches", b, h)
        if result and isinstance(result, dict) and result.get("id"):
            IDS[f"branch_{b['branch_code']}"] = result["id"]
            print(f"  ✅ {b['branch_name']} (id={result['id']})")
    
    # Refresh
    all_branches = api("GET", "/api/branches", headers=h)
    if isinstance(all_branches, list):
        for b in all_branches:
            IDS[f"branch_{b['branch_code']}"] = b["id"]

# ============================================================
# PHASE 3: FISCAL YEAR
# ============================================================
def setup_fiscal_year(h):
    step("المرحلة 3: إعداد السنة المالية 2026")
    
    existing = api("GET", "/api/accounting/fiscal-years", headers=h)
    if isinstance(existing, list) and any(fy.get("year") == 2026 for fy in existing):
        print("  ℹ️  السنة المالية 2026 موجودة مسبقاً")
        return
    
    result = api("POST", "/api/accounting/fiscal-years", {
        "year": 2026,
        "start_date": "2026-01-01",
        "end_date": "2026-12-31"
    }, h)
    if result:
        print(f"  ✅ السنة المالية 2026 تم إنشاؤها")

# ============================================================
# PHASE 4: WAREHOUSES
# ============================================================
def setup_warehouses(h):
    step("المرحلة 4: إعداد المستودعات")
    
    existing = api("GET", "/api/inventory/warehouses", headers=h)
    existing_codes = []
    if isinstance(existing, list):
        existing_codes = [w.get("code","") for w in existing]
        for w in existing:
            if w.get("code"):
                IDS[f"wh_{w['code']}"] = w["id"]
                print(f"  ℹ️  مستودع موجود: {w['name']} (id={w['id']})")
    
    warehouses = [
        {"name": "المستودع الرئيسي - الرياض", "code": "WH-RYD", "location": "الرياض",
         "branch_id": IDS.get("branch_BR001", 1), "is_default": True},
        {"name": "مستودع جدة", "code": "WH-JED", "location": "جدة",
         "branch_id": IDS.get("branch_BR002", 2), "is_default": False},
        {"name": "مستودع دبي", "code": "WH-DXB", "location": "دبي",
         "branch_id": IDS.get("branch_BR003", 3), "is_default": False},
    ]
    
    for w in warehouses:
        if w["code"] in existing_codes:
            continue
        result = api("POST", "/api/inventory/warehouses", w, h)
        if result and isinstance(result, dict) and result.get("id"):
            IDS[f"wh_{w['code']}"] = result["id"]
            print(f"  ✅ {w['name']} (id={result['id']})")

# ============================================================
# PHASE 5: PRODUCTS
# ============================================================
def setup_products(h):
    step("المرحلة 5: إعداد المنتجات")
    
    existing = api("GET", "/api/inventory/products", headers=h)
    existing_codes = []
    if isinstance(existing, list):
        existing_codes = [p.get("item_code","") for p in existing]
        for p in existing:
            IDS[f"prod_{p['item_code']}"] = p["id"]
    elif isinstance(existing, dict) and existing.get("items"):
        for p in existing["items"]:
            existing_codes.append(p.get("item_code",""))
            IDS[f"prod_{p['item_code']}"] = p["id"]
    
    products = [
        {"item_code": "PRD-001", "item_name": "لابتوب Dell Latitude", "item_name_en": "Dell Latitude Laptop",
         "item_type": "product", "unit": "قطعة", "selling_price": 4500.0, "buying_price": 0,
         "tax_rate": 15.0, "description": "لابتوب ديل للأعمال", "has_serial_tracking": True},
        {"item_code": "PRD-002", "item_name": "طابعة HP LaserJet", "item_name_en": "HP LaserJet Printer",
         "item_type": "product", "unit": "قطعة", "selling_price": 1800.0, "buying_price": 0,
         "tax_rate": 15.0, "description": "طابعة ليزر HP"},
        {"item_code": "PRD-003", "item_name": "ورق طباعة A4", "item_name_en": "A4 Paper",
         "item_type": "product", "unit": "رزمة", "selling_price": 25.0, "buying_price": 0,
         "tax_rate": 15.0, "description": "ورق طباعة 500 ورقة", "has_batch_tracking": True},
        {"item_code": "PRD-004", "item_name": "حبر طابعة HP", "item_name_en": "HP Toner",
         "item_type": "product", "unit": "قطعة", "selling_price": 350.0, "buying_price": 0,
         "tax_rate": 15.0, "description": "حبر طابعة HP أصلي"},
        {"item_code": "PRD-005", "item_name": "شاشة Samsung 27 بوصة", "item_name_en": "Samsung 27\" Monitor",
         "item_type": "product", "unit": "قطعة", "selling_price": 1200.0, "buying_price": 0,
         "tax_rate": 15.0, "description": "شاشة سامسونج 27 بوصة 4K", "has_serial_tracking": True},
        {"item_code": "SRV-001", "item_name": "خدمة صيانة", "item_name_en": "Maintenance Service",
         "item_type": "service", "unit": "ساعة", "selling_price": 150.0, "buying_price": 0,
         "tax_rate": 15.0, "description": "خدمة صيانة بالساعة"},
    ]
    
    for p in products:
        if p["item_code"] in existing_codes:
            print(f"  ℹ️  {p['item_code']} موجود")
            continue
        result = api("POST", "/api/inventory/products", p, h)
        if result and isinstance(result, dict) and result.get("id"):
            IDS[f"prod_{p['item_code']}"] = result["id"]
            print(f"  ✅ {p['item_name']} (id={result['id']})")

# ============================================================
# PHASE 6: SUPPLIERS
# ============================================================
def setup_suppliers(h):
    step("المرحلة 6: إعداد الموردين")
    
    existing = api("GET", "/api/buying/suppliers", headers=h)
    existing_names = []
    if isinstance(existing, list):
        for s in existing:
            existing_names.append(s.get("supplier_name",""))
            IDS[f"sup_{s.get('supplier_name','')}"] = s["id"]
    elif isinstance(existing, dict):
        items = existing.get("items", existing.get("suppliers", []))
        for s in items:
            existing_names.append(s.get("supplier_name",""))
            IDS[f"sup_{s.get('supplier_name','')}"] = s["id"]
    
    suppliers = [
        {"supplier_name": "شركة التقنية المتقدمة", "supplier_name_en": "Advanced Tech Co",
         "email": "info@advtech.sa", "phone": "0112345678", "tax_number": "300123456789003",
         "address": "الرياض - حي العليا", "branch_id": IDS.get("branch_BR001", 1)},
        {"supplier_name": "مؤسسة المكتبية", "supplier_name_en": "Office Supplies Est",
         "email": "info@office.sa", "phone": "0112345679", "tax_number": "300123456789004",
         "address": "الرياض - حي الملز", "branch_id": IDS.get("branch_BR001", 1)},
        {"supplier_name": "Global Electronics LLC", "supplier_name_en": "Global Electronics LLC",
         "email": "sales@globalelec.com", "phone": "+1-555-0123", "tax_number": "US-EIN-123456",
         "address": "New York, USA", "branch_id": IDS.get("branch_BR001", 1)},
        {"supplier_name": "Euro Parts GmbH", "supplier_name_en": "Euro Parts GmbH",
         "email": "info@europarts.de", "phone": "+49-30-12345", "tax_number": "DE-VAT-789012",
         "address": "Berlin, Germany", "branch_id": IDS.get("branch_BR001", 1)},
    ]
    
    for s in suppliers:
        if s["supplier_name"] in existing_names:
            print(f"  ℹ️  {s['supplier_name']} موجود")
            continue
        result = api("POST", "/api/buying/suppliers", s, h)
        if result and isinstance(result, dict) and result.get("id"):
            IDS[f"sup_{s['supplier_name']}"] = result["id"]
            print(f"  ✅ {s['supplier_name']} (id={result['id']})")

# ============================================================
# PHASE 7: CUSTOMERS
# ============================================================
def setup_customers(h):
    step("المرحلة 7: إعداد العملاء")
    
    existing = api("GET", "/api/sales/customers", headers=h)
    existing_names = []
    if isinstance(existing, list):
        for c in existing:
            existing_names.append(c.get("name",""))
            IDS[f"cust_{c.get('name','')}"] = c["id"]
    elif isinstance(existing, dict):
        items = existing.get("items", existing.get("customers", []))
        for c in items:
            existing_names.append(c.get("name",""))
            IDS[f"cust_{c.get('name','')}"] = c["id"]
    
    customers = [
        {"name": "شركة الأفق للتجارة", "name_en": "Al Ufuq Trading Co", "email": "info@alufuq.sa",
         "phone": "0551234567", "tax_number": "310987654321003", "address": "الرياض - طريق الملك فهد",
         "city": "الرياض", "country": "السعودية", "credit_limit": 100000, "payment_terms": 30,
         "currency": "SAR", "branch_id": IDS.get("branch_BR001", 1)},
        {"name": "مؤسسة النجاح", "name_en": "Al Najah Est", "email": "info@najah.sa",
         "phone": "0559876543", "tax_number": "310987654321004", "address": "جدة - حي الحمراء",
         "city": "جدة", "country": "السعودية", "credit_limit": 50000, "payment_terms": 15,
         "currency": "SAR", "branch_id": IDS.get("branch_BR002", 2)},
        {"name": "Gulf Services FZE", "name_en": "Gulf Services FZE", "email": "info@gulfserv.ae",
         "phone": "+971501234567", "tax_number": "AE-TRN-100234567", "address": "دبي - المنطقة الحرة",
         "city": "دبي", "country": "الإمارات", "credit_limit": 200000, "payment_terms": 45,
         "currency": "AED", "branch_id": IDS.get("branch_BR003", 3)},
        {"name": "American Import Corp", "name_en": "American Import Corp", "email": "imports@amcorp.com",
         "phone": "+1-555-9876", "tax_number": "US-TIN-987654", "address": "Houston, TX",
         "city": "Houston", "country": "USA", "credit_limit": 150000, "payment_terms": 60,
         "currency": "USD"},
        {"name": "Deutsche Handel AG", "name_en": "Deutsche Handel AG", "email": "info@dhandel.de",
         "phone": "+49-89-54321", "tax_number": "DE-VAT-345678", "address": "Munich, Germany",
         "city": "Munich", "country": "Germany", "credit_limit": 120000, "payment_terms": 30,
         "currency": "EUR"},
    ]
    
    for c in customers:
        if c["name"] in existing_names:
            print(f"  ℹ️  {c['name']} موجود")
            continue
        result = api("POST", "/api/sales/customers", c, h)
        if result and isinstance(result, dict) and result.get("id"):
            IDS[f"cust_{c['name']}"] = result["id"]
            print(f"  ✅ {c['name']} (id={result['id']}) عملة={c.get('currency','SAR')}")

# ============================================================
# PHASE 8: TREASURY ACCOUNTS
# ============================================================
def setup_treasury(h):
    step("المرحلة 8: إعداد حسابات الخزينة")
    
    existing = api("GET", "/api/treasury/accounts", headers=h)
    existing_names = []
    if isinstance(existing, list):
        for t in existing:
            existing_names.append(t.get("name",""))
            IDS[f"treasury_{t.get('name','')}"] = t["id"]
    elif isinstance(existing, dict):
        items = existing.get("accounts", existing.get("items", []))
        for t in items:
            existing_names.append(t.get("name",""))
            IDS[f"treasury_{t.get('name','')}"] = t["id"]
    
    treasury_accounts = [
        {"name": "صندوق الرياض", "name_en": "Riyadh Cash Box", "account_type": "cash",
         "currency": "SAR", "branch_id": IDS.get("branch_BR001", 1), "opening_balance": 50000, "exchange_rate": 1.0},
        {"name": "صندوق جدة", "name_en": "Jeddah Cash Box", "account_type": "cash",
         "currency": "SAR", "branch_id": IDS.get("branch_BR002", 2), "opening_balance": 30000, "exchange_rate": 1.0},
        {"name": "صندوق دبي", "name_en": "Dubai Cash Box", "account_type": "cash",
         "currency": "AED", "branch_id": IDS.get("branch_BR003", 3), "opening_balance": 20000, "exchange_rate": 1.02},
        {"name": "بنك الراجحي - جاري", "name_en": "Al Rajhi Bank - Current", "account_type": "bank",
         "currency": "SAR", "bank_name": "مصرف الراجحي", "account_number": "SA001234567890",
         "iban": "SA0380000000608010167519", "branch_id": IDS.get("branch_BR001", 1),
         "opening_balance": 500000, "exchange_rate": 1.0},
        {"name": "بنك الراجحي - دولار", "name_en": "Al Rajhi Bank - USD", "account_type": "bank",
         "currency": "USD", "bank_name": "مصرف الراجحي", "account_number": "SA001234567891",
         "iban": "SA0380000000608010167520", "branch_id": IDS.get("branch_BR001", 1),
         "opening_balance": 25000, "exchange_rate": 3.75},
        {"name": "بنك الإمارات دبي الوطني", "name_en": "Emirates NBD", "account_type": "bank",
         "currency": "AED", "bank_name": "بنك الإمارات دبي الوطني", "account_number": "AE001234567892",
         "iban": "AE070331234567890123456", "branch_id": IDS.get("branch_BR003", 3),
         "opening_balance": 100000, "exchange_rate": 1.02},
    ]
    
    for t in treasury_accounts:
        if t["name"] in existing_names:
            print(f"  ℹ️  {t['name']} موجود")
            continue
        result = api("POST", "/api/treasury/accounts", t, h)
        if result and isinstance(result, dict) and result.get("id"):
            IDS[f"treasury_{t['name']}"] = result["id"]
            print(f"  ✅ {t['name']} (id={result['id']}) {t['currency']} رصيد={t['opening_balance']}")

# ============================================================
# PHASE 9: OPENING BALANCE JOURNAL ENTRY
# ============================================================
def setup_opening_balances(h):
    step("المرحلة 9: قيد الأرصدة الافتتاحية")
    
    # Get account IDs
    accounts = api("GET", "/api/accounting/accounts", headers=h)
    acct_map = {}
    if isinstance(accounts, list):
        for a in accounts:
            acct_map[a["account_code"]] = a["id"]
    
    if not acct_map:
        print("  ❌ لم يتم العثور على الحسابات")
        return
    
    # The treasury accounts already have opening balances via their creation
    # Now create opening balance JE for equity
    # Total opening assets:
    # Cash: 50000 + 30000 + (20000×1.02) = 100,400
    # Banks: 500000 + (25000×3.75) + (100000×1.02) = 695,750
    # Total = 796,150 SAR
    
    # This should be balanced by Capital (رأس المال)
    # Treasury accounts already create JEs, so let's create additional balances
    
    # Opening inventory - stock worth 200,000 SAR
    cap_id = acct_map.get("CAP")
    inv_id = acct_map.get("INV")
    ar_id = acct_map.get("AR")
    ret_id = acct_map.get("RET")
    
    if not cap_id:
        print("  ⚠️  حساب رأس المال غير موجود")
        return
    
    # Create JE for opening AR + Inventory balanced by Retained Earnings
    lines = []
    
    # Opening AR balance - 150,000 SAR 
    if ar_id:
        lines.append({"account_id": ar_id, "debit": 150000, "credit": 0,
                       "description": "رصيد افتتاحي - ذمم مدينة"})
    
    # Opening Inventory - 200,000 SAR
    if inv_id:
        lines.append({"account_id": inv_id, "debit": 200000, "credit": 0,
                       "description": "رصيد افتتاحي - مخزون"})
    
    # Balance by retained earnings
    total_debit = sum(l["debit"] for l in lines)
    if ret_id and total_debit > 0:
        lines.append({"account_id": ret_id, "debit": 0, "credit": total_debit,
                       "description": "رصيد افتتاحي - أرباح مدورة"})
    
    if lines and len(lines) >= 2:
        result = api("POST", "/api/accounting/journal-entries", {
            "date": "2026-01-01",
            "description": "قيد الأرصدة الافتتاحية - ذمم ومخزون",
            "reference": "OPEN-001",
            "status": "posted",
            "branch_id": IDS.get("branch_BR001", 1),
            "currency": "SAR",
            "exchange_rate": 1.0,
            "lines": lines
        }, h)
        if result and isinstance(result, dict) and (result.get("id") or result.get("entry_id")):
            print(f"  ✅ قيد الأرصدة الافتتاحية (مدين={total_debit:,.0f} ر.س)")
        else:
            print(f"  ℹ️  نتيجة القيد: {result}")

# ============================================================
# PHASE 10: PURCHASE ORDERS (Multi-currency)
# ============================================================
def execute_purchases(h):
    step("المرحلة 10: أوامر الشراء والفواتير")
    
    # --- PO 1: شراء محلي بالريال ---
    sup1_id = IDS.get("sup_شركة التقنية المتقدمة")
    sup2_id = IDS.get("sup_مؤسسة المكتبية")
    sup3_id = IDS.get("sup_Global Electronics LLC")
    sup4_id = IDS.get("sup_Euro Parts GmbH")
    
    prod1 = IDS.get("prod_PRD-001")  # لابتوب
    prod2 = IDS.get("prod_PRD-002")  # طابعة
    prod3 = IDS.get("prod_PRD-003")  # ورق
    prod4 = IDS.get("prod_PRD-004")  # حبر
    prod5 = IDS.get("prod_PRD-005")  # شاشة
    
    wh1 = IDS.get("wh_WH-RYD", 1)
    wh2 = IDS.get("wh_WH-JED", 2)
    wh3 = IDS.get("wh_WH-DXB", 3)
    
    br1 = IDS.get("branch_BR001", 1)
    br2 = IDS.get("branch_BR002", 2)
    br3 = IDS.get("branch_BR003", 3)
    
    # ======= PO1: شراء لابتوبات (SAR) من شركة التقنية =======
    # 20 لابتوب × 3500 = 70,000 + ضريبة 15% = 80,500
    print("\n  --- أمر شراء 1: لابتوبات (SAR) ---")
    if sup1_id and prod1:
        po1 = api("POST", "/api/buying/orders", {
            "supplier_id": sup1_id,
            "order_date": "2026-02-01",
            "expected_date": "2026-02-10",
            "items": [
                {"product_id": prod1, "description": "لابتوب Dell Latitude 5540",
                 "quantity": 20, "unit_price": 3500, "tax_rate": 15, "discount": 0}
            ],
            "notes": "طلب شراء لابتوبات للمكتب الرئيسي",
            "branch_id": br1, "currency": "SAR", "exchange_rate": 1.0
        }, h)
        po1_id = po1.get("id") if po1 and isinstance(po1, dict) else None
        if po1_id:
            IDS["po1"] = po1_id
            print(f"    ✅ أمر شراء #{po1_id} — 20 لابتوب × 3,500 = 70,000 + ض15% = 80,500 ر.س")
            
            # Approve
            apr = api("PUT", f"/api/buying/orders/{po1_id}/approve", {}, h)
            print(f"    ✅ تمت الموافقة")
            
            # Receive
            # Need to get PO lines
            po_detail = api("GET", f"/api/buying/orders/{po1_id}", headers=h)
            lines_data = []
            if po_detail and isinstance(po_detail, dict):
                po_items = po_detail.get("items", po_detail.get("lines", []))
                for item in po_items:
                    line_id = item.get("id", item.get("line_id"))
                    if line_id:
                        lines_data.append({"line_id": line_id, "received_quantity": 20})
            
            if lines_data:
                rcv = api("POST", f"/api/buying/orders/{po1_id}/receive", {
                    "items": lines_data, "warehouse_id": wh1, "notes": "استلام كامل"
                }, h)
                print(f"    ✅ تم الاستلام — 20 لابتوب في مستودع الرياض")
            
            # Purchase Invoice
            inv1 = api("POST", "/api/buying/invoices", {
                "supplier_id": sup1_id, "invoice_date": "2026-02-05", "due_date": "2026-03-05",
                "items": [{"product_id": prod1, "description": "لابتوب Dell Latitude 5540",
                          "quantity": 20, "unit_price": 3500, "tax_rate": 15, "discount": 0}],
                "payment_method": "credit", "paid_amount": 0,
                "original_invoice_id": po1_id,
                "branch_id": br1, "warehouse_id": wh1,
                "currency": "SAR", "exchange_rate": 1.0
            }, h)
            if inv1 and isinstance(inv1, dict) and inv1.get("id"):
                IDS["pinv1"] = inv1["id"]
                print(f"    ✅ فاتورة شراء #{inv1['id']} — 80,500 ر.س (آجل)")
    
    # ======= PO2: شراء مستلزمات مكتبية (SAR) =======
    # 100 رزمة ورق × 15 + 50 حبر × 200 = 1,500 + 10,000 = 11,500 + ض15% = 13,225
    print("\n  --- أمر شراء 2: مستلزمات مكتبية (SAR) ---")
    if sup2_id and prod3 and prod4:
        po2 = api("POST", "/api/buying/orders", {
            "supplier_id": sup2_id,
            "order_date": "2026-02-03",
            "expected_date": "2026-02-07",
            "items": [
                {"product_id": prod3, "description": "ورق طباعة A4",
                 "quantity": 100, "unit_price": 15, "tax_rate": 15, "discount": 0},
                {"product_id": prod4, "description": "حبر طابعة HP",
                 "quantity": 50, "unit_price": 200, "tax_rate": 15, "discount": 0}
            ],
            "notes": "مستلزمات مكتبية شهرية",
            "branch_id": br1, "currency": "SAR", "exchange_rate": 1.0
        }, h)
        po2_id = po2.get("id") if po2 and isinstance(po2, dict) else None
        if po2_id:
            IDS["po2"] = po2_id
            print(f"    ✅ أمر شراء #{po2_id} — ورق+حبر = 11,500 + ض15% = 13,225 ر.س")
            
            api("PUT", f"/api/buying/orders/{po2_id}/approve", {}, h)
            print(f"    ✅ تمت الموافقة")
            
            po_detail = api("GET", f"/api/buying/orders/{po2_id}", headers=h)
            lines_data = []
            if po_detail and isinstance(po_detail, dict):
                for item in po_detail.get("items", po_detail.get("lines", [])):
                    lid = item.get("id", item.get("line_id"))
                    qty = item.get("quantity", 0)
                    if lid: lines_data.append({"line_id": lid, "received_quantity": qty})
            
            if lines_data:
                api("POST", f"/api/buying/orders/{po2_id}/receive", {
                    "items": lines_data, "warehouse_id": wh1, "notes": "استلام كامل"
                }, h)
                print(f"    ✅ تم الاستلام في مستودع الرياض")
            
            inv2 = api("POST", "/api/buying/invoices", {
                "supplier_id": sup2_id, "invoice_date": "2026-02-07", "due_date": "2026-03-07",
                "items": [
                    {"product_id": prod3, "description": "ورق طباعة A4",
                     "quantity": 100, "unit_price": 15, "tax_rate": 15, "discount": 0},
                    {"product_id": prod4, "description": "حبر طابعة HP",
                     "quantity": 50, "unit_price": 200, "tax_rate": 15, "discount": 0}
                ],
                "payment_method": "cash", "paid_amount": 13225,
                "original_invoice_id": po2_id,
                "branch_id": br1, "warehouse_id": wh1,
                "currency": "SAR", "exchange_rate": 1.0,
                "treasury_id": IDS.get("treasury_صندوق الرياض")
            }, h)
            if inv2 and isinstance(inv2, dict) and inv2.get("id"):
                IDS["pinv2"] = inv2["id"]
                print(f"    ✅ فاتورة شراء #{inv2['id']} — 13,225 ر.س (نقداً)")
    
    # ======= PO3: شراء شاشات بالدولار (USD) من Global Electronics =======
    # 15 شاشة × 280 USD = 4,200 USD + ض15% = 4,830 USD
    # بالريال: 4,830 × 3.75 = 18,112.50 ر.س
    print("\n  --- أمر شراء 3: شاشات (USD) ---")
    if sup3_id and prod5:
        po3 = api("POST", "/api/buying/orders", {
            "supplier_id": sup3_id,
            "order_date": "2026-02-05",
            "expected_date": "2026-02-20",
            "items": [
                {"product_id": prod5, "description": "Samsung 27\" 4K Monitor",
                 "quantity": 15, "unit_price": 280, "tax_rate": 15, "discount": 0}
            ],
            "notes": "Purchase order for monitors - USD",
            "branch_id": br1, "currency": "USD", "exchange_rate": 3.75
        }, h)
        po3_id = po3.get("id") if po3 and isinstance(po3, dict) else None
        if po3_id:
            IDS["po3"] = po3_id
            print(f"    ✅ أمر شراء #{po3_id} — 15 شاشة × 280$ = 4,200$ + ض15% = 4,830$")
            print(f"       بالريال: 4,830 × 3.75 = 18,112.50 ر.س")
            
            api("PUT", f"/api/buying/orders/{po3_id}/approve", {}, h)
            print(f"    ✅ تمت الموافقة")
            
            po_detail = api("GET", f"/api/buying/orders/{po3_id}", headers=h)
            lines_data = []
            if po_detail and isinstance(po_detail, dict):
                for item in po_detail.get("items", po_detail.get("lines", [])):
                    lid = item.get("id", item.get("line_id"))
                    if lid: lines_data.append({"line_id": lid, "received_quantity": 15})
            
            if lines_data:
                api("POST", f"/api/buying/orders/{po3_id}/receive", {
                    "items": lines_data, "warehouse_id": wh1, "notes": "Received all monitors"
                }, h)
                print(f"    ✅ تم الاستلام — 15 شاشة في مستودع الرياض")
            
            inv3 = api("POST", "/api/buying/invoices", {
                "supplier_id": sup3_id, "invoice_date": "2026-02-10", "due_date": "2026-04-10",
                "items": [{"product_id": prod5, "description": "Samsung 27\" 4K Monitor",
                          "quantity": 15, "unit_price": 280, "tax_rate": 15, "discount": 0}],
                "payment_method": "credit", "paid_amount": 0,
                "original_invoice_id": po3_id,
                "branch_id": br1, "warehouse_id": wh1,
                "currency": "USD", "exchange_rate": 3.75
            }, h)
            if inv3 and isinstance(inv3, dict) and inv3.get("id"):
                IDS["pinv3"] = inv3["id"]
                print(f"    ✅ فاتورة شراء #{inv3['id']} — 4,830$ = 18,112.50 ر.س (آجل)")
    
    # ======= PO4: شراء طابعات باليورو (EUR) من Euro Parts =======
    # 10 طابعات × 350 EUR = 3,500 EUR + ض15% = 4,025 EUR
    # بالريال: 4,025 × 4.10 = 16,502.50 ر.س
    print("\n  --- أمر شراء 4: طابعات (EUR) ---")
    if sup4_id and prod2:
        po4 = api("POST", "/api/buying/orders", {
            "supplier_id": sup4_id,
            "order_date": "2026-02-08",
            "expected_date": "2026-02-25",
            "items": [
                {"product_id": prod2, "description": "HP LaserJet Pro MFP",
                 "quantity": 10, "unit_price": 350, "tax_rate": 15, "discount": 0}
            ],
            "notes": "Bestellung von Druckern - EUR",
            "branch_id": br2, "currency": "EUR", "exchange_rate": 4.10
        }, h)
        po4_id = po4.get("id") if po4 and isinstance(po4, dict) else None
        if po4_id:
            IDS["po4"] = po4_id
            print(f"    ✅ أمر شراء #{po4_id} — 10 طابعات × 350€ = 3,500€ + ض15% = 4,025€")
            print(f"       بالريال: 4,025 × 4.10 = 16,502.50 ر.س")
            
            api("PUT", f"/api/buying/orders/{po4_id}/approve", {}, h)
            print(f"    ✅ تمت الموافقة")
            
            po_detail = api("GET", f"/api/buying/orders/{po4_id}", headers=h)
            lines_data = []
            if po_detail and isinstance(po_detail, dict):
                for item in po_detail.get("items", po_detail.get("lines", [])):
                    lid = item.get("id", item.get("line_id"))
                    if lid: lines_data.append({"line_id": lid, "received_quantity": 10})
            
            if lines_data:
                api("POST", f"/api/buying/orders/{po4_id}/receive", {
                    "items": lines_data, "warehouse_id": wh2, "notes": "استلام في جدة"
                }, h)
                print(f"    ✅ تم الاستلام — 10 طابعات في مستودع جدة")
            
            inv4 = api("POST", "/api/buying/invoices", {
                "supplier_id": sup4_id, "invoice_date": "2026-02-15", "due_date": "2026-04-15",
                "items": [{"product_id": prod2, "description": "HP LaserJet Pro MFP",
                          "quantity": 10, "unit_price": 350, "tax_rate": 15, "discount": 0}],
                "payment_method": "credit", "paid_amount": 0,
                "original_invoice_id": po4_id,
                "branch_id": br2, "warehouse_id": wh2,
                "currency": "EUR", "exchange_rate": 4.10
            }, h)
            if inv4 and isinstance(inv4, dict) and inv4.get("id"):
                IDS["pinv4"] = inv4["id"]
                print(f"    ✅ فاتورة شراء #{inv4['id']} — 4,025€ = 16,502.50 ر.س (آجل)")
    
    # ======= PO5: شراء لفرع دبي بالدرهم (AED) =======
    # 30 لابتوب × 3,430 AED = 102,900 AED + ض5% = 108,045 AED
    # بالريال: 108,045 × 1.02 = 110,205.90 ر.س
    print("\n  --- أمر شراء 5: لابتوبات لدبي (AED) ---")
    if sup1_id and prod1:
        po5 = api("POST", "/api/buying/orders", {
            "supplier_id": sup1_id,
            "order_date": "2026-02-10",
            "expected_date": "2026-02-20",
            "items": [
                {"product_id": prod1, "description": "Dell Latitude laptop for Dubai",
                 "quantity": 30, "unit_price": 3430, "tax_rate": 5, "discount": 0}
            ],
            "notes": "طلب لابتوبات لفرع دبي",
            "branch_id": br3, "currency": "AED", "exchange_rate": 1.02
        }, h)
        po5_id = po5.get("id") if po5 and isinstance(po5, dict) else None
        if po5_id:
            IDS["po5"] = po5_id
            print(f"    ✅ أمر شراء #{po5_id} — 30 لابتوب × 3,430 د.إ")
            print(f"       الإجمالي: 102,900 + ض5% = 108,045 د.إ = {108045*1.02:,.2f} ر.س")
            
            api("PUT", f"/api/buying/orders/{po5_id}/approve", {}, h)
            
            po_detail = api("GET", f"/api/buying/orders/{po5_id}", headers=h)
            lines_data = []
            if po_detail and isinstance(po_detail, dict):
                for item in po_detail.get("items", po_detail.get("lines", [])):
                    lid = item.get("id", item.get("line_id"))
                    if lid: lines_data.append({"line_id": lid, "received_quantity": 30})
            
            if lines_data:
                api("POST", f"/api/buying/orders/{po5_id}/receive", {
                    "items": lines_data, "warehouse_id": wh3, "notes": "استلام في دبي"
                }, h)
                print(f"    ✅ تم الاستلام — 30 لابتوب في مستودع دبي")
            
            inv5 = api("POST", "/api/buying/invoices", {
                "supplier_id": sup1_id, "invoice_date": "2026-02-12", "due_date": "2026-03-12",
                "items": [{"product_id": prod1, "description": "Dell Latitude laptop",
                          "quantity": 30, "unit_price": 3430, "tax_rate": 5, "discount": 0}],
                "payment_method": "credit", "paid_amount": 0,
                "original_invoice_id": po5_id,
                "branch_id": br3, "warehouse_id": wh3,
                "currency": "AED", "exchange_rate": 1.02
            }, h)
            if inv5 and isinstance(inv5, dict) and inv5.get("id"):
                IDS["pinv5"] = inv5["id"]
                print(f"    ✅ فاتورة شراء #{inv5['id']} — 108,045 د.إ (آجل)")

# ============================================================
# PHASE 11: SUPPLIER PAYMENTS
# ============================================================
def execute_supplier_payments(h):
    step("المرحلة 11: سداد الموردين")
    
    # Pay PO1 partially (40,000 from 80,500) by bank
    pinv1 = IDS.get("pinv1")
    sup1_id = IDS.get("sup_شركة التقنية المتقدمة")
    treasury_bank = IDS.get("treasury_بنك الراجحي - جاري")
    treasury_usd = IDS.get("treasury_بنك الراجحي - دولار")
    treasury_aed = IDS.get("treasury_بنك الإمارات دبي الوطني")
    br1 = IDS.get("branch_BR001", 1)
    
    if pinv1 and sup1_id and treasury_bank:
        print("\n  --- سداد جزئي لفاتورة الشراء 1 (SAR) ---")
        pay1 = api("POST", "/api/buying/payments", {
            "supplier_id": sup1_id,
            "voucher_date": "2026-02-15",
            "amount": 40000,
            "payment_method": "bank",
            "reference": "PAY-SUP-001",
            "notes": "دفعة أولى - لابتوبات",
            "branch_id": br1,
            "voucher_type": "payment",
            "currency": "SAR",
            "exchange_rate": 1.0,
            "treasury_account_id": treasury_bank,
            "allocations": [{"invoice_id": pinv1, "allocated_amount": 40000}]
        }, h)
        if pay1 and isinstance(pay1, dict) and pay1.get("id"):
            print(f"    ✅ سند صرف #{pay1['id']} — 40,000 ر.س (بنك الراجحي)")
    
    # Pay PO3 fully in USD (4,830 USD)
    pinv3 = IDS.get("pinv3")
    sup3_id = IDS.get("sup_Global Electronics LLC")
    if pinv3 and sup3_id and treasury_usd:
        print("\n  --- سداد كامل لفاتورة الشراء 3 (USD) ---")
        pay3 = api("POST", "/api/buying/payments", {
            "supplier_id": sup3_id,
            "voucher_date": "2026-02-20",
            "amount": 4830,
            "payment_method": "bank",
            "reference": "PAY-SUP-003",
            "notes": "Full payment - monitors USD",
            "branch_id": br1,
            "voucher_type": "payment",
            "currency": "USD",
            "exchange_rate": 3.75,
            "treasury_account_id": treasury_usd,
            "allocations": [{"invoice_id": pinv3, "allocated_amount": 4830}]
        }, h)
        if pay3 and isinstance(pay3, dict) and pay3.get("id"):
            print(f"    ✅ سند صرف #{pay3['id']} — 4,830$ = 18,112.50 ر.س (بنك الراجحي - دولار)")

# ============================================================
# PHASE 12: SALES ORDERS & INVOICES
# ============================================================
def execute_sales(h):
    step("المرحلة 12: المبيعات والفواتير")
    
    cust1 = IDS.get("cust_شركة الأفق للتجارة")
    cust2 = IDS.get("cust_مؤسسة النجاح")
    cust3 = IDS.get("cust_Gulf Services FZE")
    cust4 = IDS.get("cust_American Import Corp")
    cust5 = IDS.get("cust_Deutsche Handel AG")
    
    prod1 = IDS.get("prod_PRD-001")  # لابتوب 4500
    prod2 = IDS.get("prod_PRD-002")  # طابعة 1800
    prod3 = IDS.get("prod_PRD-003")  # ورق 25
    prod4 = IDS.get("prod_PRD-004")  # حبر 350
    prod5 = IDS.get("prod_PRD-005")  # شاشة 1200
    srv1 = IDS.get("prod_SRV-001")   # خدمة 150
    
    wh1 = IDS.get("wh_WH-RYD", 1)
    wh2 = IDS.get("wh_WH-JED", 2)
    wh3 = IDS.get("wh_WH-DXB", 3)
    
    br1 = IDS.get("branch_BR001", 1)
    br2 = IDS.get("branch_BR002", 2)
    br3 = IDS.get("branch_BR003", 3)
    
    treasury_cash = IDS.get("treasury_صندوق الرياض")
    treasury_bank = IDS.get("treasury_بنك الراجحي - جاري")
    
    # ======= فاتورة بيع 1: بيع لابتوبات + شاشات (SAR) =======
    # 5 لابتوب × 4500 + 5 شاشة × 1200 = 22,500 + 6,000 = 28,500 + ض15% = 32,775
    print("\n  --- فاتورة بيع 1: شركة الأفق (SAR) ---")
    if cust1 and prod1 and prod5:
        sinv1 = api("POST", "/api/sales/invoices", {
            "customer_id": cust1,
            "invoice_date": "2026-02-10",
            "due_date": "2026-03-10",
            "items": [
                {"product_id": prod1, "description": "لابتوب Dell Latitude 5540",
                 "quantity": 5, "unit_price": 4500, "tax_rate": 15, "discount": 0},
                {"product_id": prod5, "description": "شاشة Samsung 27\" 4K",
                 "quantity": 5, "unit_price": 1200, "tax_rate": 15, "discount": 0}
            ],
            "notes": "فاتورة مبيعات - أجهزة كمبيوتر",
            "payment_method": "credit",
            "paid_amount": 0,
            "branch_id": br1, "warehouse_id": wh1,
            "currency": "SAR", "exchange_rate": 1.0
        }, h)
        if sinv1 and isinstance(sinv1, dict) and sinv1.get("id"):
            IDS["sinv1"] = sinv1["id"]
            print(f"    ✅ فاتورة بيع #{sinv1['id']} — 28,500 + ض15% = 32,775 ر.س (آجل)")
    
    # ======= فاتورة بيع 2: بيع بضاعة (SAR) نقداً =======
    # 20 ورق × 25 + 10 حبر × 350 = 500 + 3,500 = 4,000 + ض15% = 4,600
    print("\n  --- فاتورة بيع 2: مؤسسة النجاح (SAR - نقد) ---")
    if cust2 and prod3 and prod4:
        sinv2 = api("POST", "/api/sales/invoices", {
            "customer_id": cust2,
            "invoice_date": "2026-02-12",
            "due_date": "2026-02-12",
            "items": [
                {"product_id": prod3, "description": "ورق طباعة A4",
                 "quantity": 20, "unit_price": 25, "tax_rate": 15, "discount": 0},
                {"product_id": prod4, "description": "حبر طابعة HP",
                 "quantity": 10, "unit_price": 350, "tax_rate": 15, "discount": 0}
            ],
            "notes": "بيع مستلزمات مكتبية - نقداً",
            "payment_method": "cash",
            "paid_amount": 4600,
            "branch_id": br2, "warehouse_id": wh1,
            "treasury_id": treasury_cash,
            "currency": "SAR", "exchange_rate": 1.0
        }, h)
        if sinv2 and isinstance(sinv2, dict) and sinv2.get("id"):
            IDS["sinv2"] = sinv2["id"]
            print(f"    ✅ فاتورة بيع #{sinv2['id']} — 4,000 + ض15% = 4,600 ر.س (نقداً)")
    
    # ======= فاتورة بيع 3: بيع بالدرهم (AED) لعميل دبي =======
    # 10 لابتوب × 4,410 AED = 44,100 AED + ض5% = 46,305 AED
    # بالريال: 46,305 × 1.02 = 47,231.10 ر.س
    print("\n  --- فاتورة بيع 3: Gulf Services (AED) ---")
    if cust3 and prod1:
        sinv3 = api("POST", "/api/sales/invoices", {
            "customer_id": cust3,
            "invoice_date": "2026-02-15",
            "due_date": "2026-03-30",
            "items": [
                {"product_id": prod1, "description": "Dell Latitude Laptop",
                 "quantity": 10, "unit_price": 4410, "tax_rate": 5, "discount": 0}
            ],
            "notes": "Invoice for laptops - AED",
            "payment_method": "credit",
            "paid_amount": 0,
            "branch_id": br3, "warehouse_id": wh3,
            "currency": "AED", "exchange_rate": 1.02
        }, h)
        if sinv3 and isinstance(sinv3, dict) and sinv3.get("id"):
            IDS["sinv3"] = sinv3["id"]
            print(f"    ✅ فاتورة بيع #{sinv3['id']} — 44,100 + ض5% = 46,305 د.إ = {46305*1.02:,.2f} ر.س")
    
    # ======= فاتورة بيع 4: بيع بالدولار (USD) =======
    # 3 لابتوب × 1,200 USD + 3 شاشة × 320 USD = 3,600 + 960 = 4,560 + ض15% = 5,244 USD
    # بالريال: 5,244 × 3.75 = 19,665 ر.س
    print("\n  --- فاتورة بيع 4: American Import (USD) ---")
    if cust4 and prod1 and prod5:
        sinv4 = api("POST", "/api/sales/invoices", {
            "customer_id": cust4,
            "invoice_date": "2026-02-18",
            "due_date": "2026-04-18",
            "items": [
                {"product_id": prod1, "description": "Dell Latitude Laptop",
                 "quantity": 3, "unit_price": 1200, "tax_rate": 15, "discount": 0},
                {"product_id": prod5, "description": "Samsung 27\" Monitor",
                 "quantity": 3, "unit_price": 320, "tax_rate": 15, "discount": 0}
            ],
            "notes": "Export invoice - USD",
            "payment_method": "credit",
            "paid_amount": 0,
            "branch_id": br1, "warehouse_id": wh1,
            "currency": "USD", "exchange_rate": 3.75
        }, h)
        if sinv4 and isinstance(sinv4, dict) and sinv4.get("id"):
            IDS["sinv4"] = sinv4["id"]
            print(f"    ✅ فاتورة بيع #{sinv4['id']} — 4,560 + ض15% = 5,244$ = {5244*3.75:,.2f} ر.س")
    
    # ======= فاتورة بيع 5: بيع باليورو (EUR) =======
    # 2 طابعة × 430 EUR = 860 + ض15% = 989 EUR
    # بالريال: 989 × 4.10 = 4,054.90 ر.س
    print("\n  --- فاتورة بيع 5: Deutsche Handel (EUR) ---")
    if cust5 and prod2:
        sinv5 = api("POST", "/api/sales/invoices", {
            "customer_id": cust5,
            "invoice_date": "2026-02-20",
            "due_date": "2026-03-20",
            "items": [
                {"product_id": prod2, "description": "HP LaserJet Pro MFP",
                 "quantity": 2, "unit_price": 430, "tax_rate": 15, "discount": 0}
            ],
            "notes": "Rechnung - EUR",
            "payment_method": "credit",
            "paid_amount": 0,
            "branch_id": br2, "warehouse_id": wh2,
            "currency": "EUR", "exchange_rate": 4.10
        }, h)
        if sinv5 and isinstance(sinv5, dict) and sinv5.get("id"):
            IDS["sinv5"] = sinv5["id"]
            print(f"    ✅ فاتورة بيع #{sinv5['id']} — 860 + ض15% = 989€ = {989*4.10:,.2f} ر.س")
    
    # ======= فاتورة بيع 6: بيع خدمات (SAR) =======
    # 40 ساعة صيانة × 150 = 6,000 + ض15% = 6,900
    print("\n  --- فاتورة بيع 6: خدمات صيانة (SAR) ---")
    if cust1 and srv1:
        sinv6 = api("POST", "/api/sales/invoices", {
            "customer_id": cust1,
            "invoice_date": "2026-02-22",
            "due_date": "2026-03-22",
            "items": [
                {"product_id": srv1, "description": "خدمة صيانة أجهزة - 40 ساعة",
                 "quantity": 40, "unit_price": 150, "tax_rate": 15, "discount": 0}
            ],
            "notes": "عقد صيانة شهري",
            "payment_method": "credit",
            "paid_amount": 0,
            "branch_id": br1,
            "currency": "SAR", "exchange_rate": 1.0
        }, h)
        if sinv6 and isinstance(sinv6, dict) and sinv6.get("id"):
            IDS["sinv6"] = sinv6["id"]
            print(f"    ✅ فاتورة بيع #{sinv6['id']} — 6,000 + ض15% = 6,900 ر.س")

# ============================================================
# PHASE 13: CUSTOMER RECEIPTS (سندات قبض)
# ============================================================
def execute_customer_receipts(h):
    step("المرحلة 13: سندات القبض (تحصيل من العملاء)")
    
    treasury_cash = IDS.get("treasury_صندوق الرياض")
    treasury_bank = IDS.get("treasury_بنك الراجحي - جاري")
    treasury_usd = IDS.get("treasury_بنك الراجحي - دولار")
    treasury_aed = IDS.get("treasury_بنك الإمارات دبي الوطني")
    
    # Receipt 1: شركة الأفق تدفع 20,000 من فاتورة 32,775
    sinv1 = IDS.get("sinv1")
    cust1 = IDS.get("cust_شركة الأفق للتجارة")
    if sinv1 and cust1 and treasury_bank:
        print("\n  --- سند قبض 1: شركة الأفق (SAR - بنك) ---")
        rcpt1 = api("POST", "/api/sales/receipts", {
            "customer_id": cust1,
            "voucher_date": "2026-02-20",
            "amount": 20000,
            "payment_method": "bank",
            "reference": "RCV-001",
            "notes": "دفعة من شركة الأفق - تحويل بنكي",
            "allocations": [{"invoice_id": sinv1, "allocated_amount": 20000}],
            "branch_id": IDS.get("branch_BR001", 1),
            "treasury_id": treasury_bank,
            "currency": "SAR", "exchange_rate": 1.0
        }, h)
        if rcpt1 and isinstance(rcpt1, dict) and rcpt1.get("id"):
            print(f"    ✅ سند قبض #{rcpt1['id']} — 20,000 ر.س (بنك الراجحي)")
            print(f"       المتبقي على الفاتورة: 32,775 - 20,000 = 12,775 ر.س")
    
    # Receipt 2: Gulf Services pays AED 30,000 from 46,305
    sinv3 = IDS.get("sinv3")
    cust3 = IDS.get("cust_Gulf Services FZE")
    if sinv3 and cust3 and treasury_aed:
        print("\n  --- سند قبض 2: Gulf Services (AED) ---")
        rcpt2 = api("POST", "/api/sales/receipts", {
            "customer_id": cust3,
            "voucher_date": "2026-02-22",
            "amount": 30000,
            "payment_method": "bank",
            "reference": "RCV-002",
            "notes": "Partial payment - AED bank transfer",
            "allocations": [{"invoice_id": sinv3, "allocated_amount": 30000}],
            "branch_id": IDS.get("branch_BR003", 3),
            "treasury_id": treasury_aed,
            "currency": "AED", "exchange_rate": 1.02
        }, h)
        if rcpt2 and isinstance(rcpt2, dict) and rcpt2.get("id"):
            print(f"    ✅ سند قبض #{rcpt2['id']} — 30,000 د.إ = {30000*1.02:,.2f} ر.س")
            print(f"       المتبقي: 46,305 - 30,000 = 16,305 د.إ")
    
    # Receipt 3: American Import pays full in USD
    sinv4 = IDS.get("sinv4")
    cust4 = IDS.get("cust_American Import Corp")
    if sinv4 and cust4 and treasury_usd:
        print("\n  --- سند قبض 3: American Import (USD - كامل) ---")
        rcpt3 = api("POST", "/api/sales/receipts", {
            "customer_id": cust4,
            "voucher_date": "2026-02-23",
            "amount": 5244,
            "payment_method": "bank",
            "reference": "RCV-003",
            "notes": "Full payment - wire transfer USD",
            "allocations": [{"invoice_id": sinv4, "allocated_amount": 5244}],
            "branch_id": IDS.get("branch_BR001", 1),
            "treasury_id": treasury_usd,
            "currency": "USD", "exchange_rate": 3.75
        }, h)
        if rcpt3 and isinstance(rcpt3, dict) and rcpt3.get("id"):
            print(f"    ✅ سند قبض #{rcpt3['id']} — 5,244$ = {5244*3.75:,.2f} ر.س (مسدد بالكامل)")

# ============================================================
# PHASE 14: TREASURY TRANSFERS
# ============================================================
def execute_treasury_transfers(h):
    step("المرحلة 14: تحويلات الخزينة")
    
    treasury_cash_ryd = IDS.get("treasury_صندوق الرياض")
    treasury_cash_jed = IDS.get("treasury_صندوق جدة")
    treasury_bank = IDS.get("treasury_بنك الراجحي - جاري")
    treasury_usd = IDS.get("treasury_بنك الراجحي - دولار")
    
    # Transfer 1: Bank to Cash (SAR to SAR) - 15,000
    if treasury_bank and treasury_cash_ryd:
        print("\n  --- تحويل 1: بنك → صندوق الرياض (SAR) ---")
        tr1 = api("POST", "/api/treasury/transactions/transfer", {
            "transaction_date": "2026-02-15",
            "transaction_type": "transfer",
            "amount": 15000,
            "treasury_id": treasury_bank,
            "target_treasury_id": treasury_cash_ryd,
            "description": "سحب نقدي من البنك للصندوق",
            "reference_number": "TRF-001",
            "branch_id": IDS.get("branch_BR001", 1),
            "exchange_rate": 1.0
        }, h)
        if tr1 and isinstance(tr1, dict) and tr1.get("id"):
            print(f"    ✅ تحويل #{tr1['id']} — 15,000 ر.س (بنك → صندوق)")
    
    # Transfer 2: Bank SAR to Cash Jeddah (SAR to SAR) - 10,000
    if treasury_bank and treasury_cash_jed:
        print("\n  --- تحويل 2: البنك → صندوق جدة (SAR) ---")
        tr2 = api("POST", "/api/treasury/transactions/transfer", {
            "transaction_date": "2026-02-16",
            "transaction_type": "transfer",
            "amount": 10000,
            "treasury_id": treasury_bank,
            "target_treasury_id": treasury_cash_jed,
            "description": "تحويل نقدي لصندوق فرع جدة",
            "reference_number": "TRF-002",
            "branch_id": IDS.get("branch_BR002", 2),
            "exchange_rate": 1.0
        }, h)
        if tr2 and isinstance(tr2, dict) and tr2.get("id"):
            print(f"    ✅ تحويل #{tr2['id']} — 10,000 ر.س (بنك → صندوق جدة)")
    
    # Transfer 3: Buy USD - SAR bank to USD bank (10,000 SAR = 2,666.67 USD)
    # source=SAR bank, rate=1.0; target=USD bank, rate=3.75
    if treasury_bank and treasury_usd:
        print("\n  --- تحويل 3: شراء دولار (SAR → USD) ---")
        tr3 = api("POST", "/api/treasury/transactions/transfer", {
            "transaction_date": "2026-02-18",
            "transaction_type": "transfer",
            "amount": 10000,
            "treasury_id": treasury_bank,
            "target_treasury_id": treasury_usd,
            "description": "شراء دولارات - 10,000 ر.س ÷ 3.75 = 2,666.67$",
            "reference_number": "TRF-003",
            "branch_id": IDS.get("branch_BR001", 1),
            "exchange_rate": 1.0
        }, h)
        if tr3 and isinstance(tr3, dict) and tr3.get("id"):
            print(f"    ✅ تحويل #{tr3['id']} — 10,000 ر.س → ~2,666.67$")

# ============================================================
# PHASE 15: EXPENSES
# ============================================================
def execute_expenses(h):
    step("المرحلة 15: المصروفات")
    
    treasury_cash = IDS.get("treasury_صندوق الرياض")
    treasury_bank = IDS.get("treasury_بنك الراجحي - جاري")
    treasury_cash_jed = IDS.get("treasury_صندوق جدة")
    
    br1 = IDS.get("branch_BR001", 1)
    br2 = IDS.get("branch_BR002", 2)
    br3 = IDS.get("branch_BR003", 3)
    
    expenses = [
        {"expense_date": "2026-02-01", "expense_type": "rent", "amount": 25000,
         "description": "إيجار المقر الرئيسي - فبراير 2026", "category": "general",
         "payment_method": "bank", "treasury_id": treasury_bank, "branch_id": br1,
         "requires_approval": False, "vendor_name": "شركة العقارات المتحدة"},
        {"expense_date": "2026-02-01", "expense_type": "rent", "amount": 15000,
         "description": "إيجار فرع جدة - فبراير 2026", "category": "general",
         "payment_method": "cash", "treasury_id": treasury_cash_jed, "branch_id": br2,
         "requires_approval": False, "vendor_name": "مؤسسة الإسكان"},
        {"expense_date": "2026-02-05", "expense_type": "utilities", "amount": 3500,
         "description": "فاتورة الكهرباء - المقر الرئيسي", "category": "general",
         "payment_method": "bank", "treasury_id": treasury_bank, "branch_id": br1,
         "requires_approval": False, "receipt_number": "ELEC-20260205"},
        {"expense_date": "2026-02-05", "expense_type": "utilities", "amount": 1200,
         "description": "فاتورة المياه - المقر الرئيسي", "category": "general",
         "payment_method": "bank", "treasury_id": treasury_bank, "branch_id": br1,
         "requires_approval": False, "receipt_number": "WATER-20260205"},
        {"expense_date": "2026-02-10", "expense_type": "travel", "amount": 4500,
         "description": "رحلة عمل - زيارة فرع جدة", "category": "general",
         "payment_method": "cash", "treasury_id": treasury_cash, "branch_id": br1,
         "requires_approval": True, "vendor_name": "وكالة السفر"},
        {"expense_date": "2026-02-12", "expense_type": "materials", "amount": 2800,
         "description": "مستلزمات تنظيف ونظافة", "category": "general",
         "payment_method": "cash", "treasury_id": treasury_cash, "branch_id": br1,
         "requires_approval": False, "vendor_name": "شركة النظافة"},
        {"expense_date": "2026-02-15", "expense_type": "utilities", "amount": 850,
         "description": "فاتورة الإنترنت - المقر الرئيسي", "category": "general",
         "payment_method": "bank", "treasury_id": treasury_bank, "branch_id": br1,
         "requires_approval": False, "receipt_number": "NET-20260215"},
        {"expense_date": "2026-02-20", "expense_type": "materials", "amount": 1500,
         "description": "أثاث مكتبي - كراسي", "category": "general",
         "payment_method": "cash", "treasury_id": treasury_cash, "branch_id": br2,
         "requires_approval": True, "vendor_name": "معرض الأثاث"},
    ]
    
    for i, exp in enumerate(expenses, 1):
        result = api("POST", "/api/expenses/", exp, h)
        if result and isinstance(result, dict) and result.get("id"):
            IDS[f"exp_{i}"] = result["id"]
            status = "بدون موافقة" if not exp.get("requires_approval") else "بانتظار الموافقة"
            print(f"  ✅ مصروف #{result['id']} — {exp['amount']:,.0f} ر.س — {exp['description'][:40]} ({status})")
            
            # Auto-approve if requires_approval
            if exp.get("requires_approval"):
                apr = api("POST", f"/api/expenses/{result['id']}/approve", {
                    "approval_status": "approved",
                    "approval_notes": "تمت الموافقة"
                }, h)
                if apr:
                    print(f"    ✅ تمت الموافقة على المصروف")

# ============================================================
# PHASE 16: HR & PAYROLL
# ============================================================
def execute_hr(h):
    step("المرحلة 16: الموارد البشرية والرواتب")
    
    br1 = IDS.get("branch_BR001", 1)
    br2 = IDS.get("branch_BR002", 2)
    br3 = IDS.get("branch_BR003", 3)
    
    employees = [
        {"first_name": "أحمد", "last_name": "العتيبي", "first_name_en": "Ahmed", "last_name_en": "Al-Otaibi",
         "employee_code": "EMP-001", "email": "ahmed@company.sa", "phone": "0501234567",
         "position_title": "مدير مالي", "department_name": "المالية",
         "salary": 15000, "housing_allowance": 3750, "transport_allowance": 1000, "other_allowances": 500,
         "hire_date": "2025-01-01", "branch_id": br1, "create_ledger": True},
        {"first_name": "فاطمة", "last_name": "الشهري", "first_name_en": "Fatimah", "last_name_en": "Al-Shahri",
         "employee_code": "EMP-002", "email": "fatimah@company.sa", "phone": "0502345678",
         "position_title": "محاسبة", "department_name": "المالية",
         "salary": 8000, "housing_allowance": 2000, "transport_allowance": 500, "other_allowances": 300,
         "hire_date": "2025-03-01", "branch_id": br1, "create_ledger": True},
        {"first_name": "خالد", "last_name": "المالكي", "first_name_en": "Khalid", "last_name_en": "Al-Malki",
         "employee_code": "EMP-003", "email": "khalid@company.sa", "phone": "0503456789",
         "position_title": "مدير مبيعات", "department_name": "المبيعات",
         "salary": 12000, "housing_allowance": 3000, "transport_allowance": 800, "other_allowances": 400,
         "hire_date": "2025-02-01", "branch_id": br1, "create_ledger": True},
        {"first_name": "نورة", "last_name": "القحطاني", "first_name_en": "Noura", "last_name_en": "Al-Qahtani",
         "employee_code": "EMP-004", "email": "noura@company.sa", "phone": "0504567890",
         "position_title": "مندوبة مبيعات", "department_name": "المبيعات",
         "salary": 7000, "housing_allowance": 1750, "transport_allowance": 500, "other_allowances": 200,
         "hire_date": "2025-06-01", "branch_id": br2, "create_ledger": True},
        {"first_name": "محمد", "last_name": "الدوسري", "first_name_en": "Mohammed", "last_name_en": "Al-Dosari",
         "employee_code": "EMP-005", "email": "mohammed@company.sa", "phone": "0505678901",
         "position_title": "مدير مستودعات", "department_name": "المستودعات",
         "salary": 9000, "housing_allowance": 2250, "transport_allowance": 600, "other_allowances": 300,
         "hire_date": "2025-04-01", "branch_id": br1, "create_ledger": True},
        {"first_name": "سارة", "last_name": "الحربي", "first_name_en": "Sara", "last_name_en": "Al-Harbi",
         "employee_code": "EMP-006", "email": "sara@company.sa", "phone": "0506789012",
         "position_title": "أخصائية موارد بشرية", "department_name": "الموارد البشرية",
         "salary": 8500, "housing_allowance": 2125, "transport_allowance": 500, "other_allowances": 200,
         "hire_date": "2025-05-01", "branch_id": br1, "create_ledger": True},
    ]
    
    for emp in employees:
        result = api("POST", "/api/hr/employees", emp, h)
        if result and isinstance(result, dict) and result.get("id"):
            IDS[f"emp_{emp['employee_code']}"] = result["id"]
            total = emp['salary'] + emp['housing_allowance'] + emp['transport_allowance'] + emp['other_allowances']
            print(f"  ✅ {emp['first_name']} {emp['last_name']} ({emp['employee_code']}) — إجمالي: {total:,.0f} ر.س")
        elif isinstance(result, dict) and "already" in str(result.get("detail","")):
            print(f"  ℹ️  {emp['first_name']} {emp['last_name']} موجود مسبقاً")
    
    # Create payroll period for February 2026
    print("\n  --- إنشاء فترة الرواتب ---")
    payroll = api("POST", "/api/hr/payroll-periods", {
        "name": "رواتب فبراير 2026",
        "start_date": "2026-02-01",
        "end_date": "2026-02-28",
        "payment_date": "2026-02-28"
    }, h)
    
    if payroll and isinstance(payroll, dict) and payroll.get("id"):
        period_id = payroll["id"]
        IDS["payroll_feb"] = period_id
        print(f"  ✅ فترة الرواتب #{period_id} — فبراير 2026")
        
        # Generate payroll
        gen = api("POST", f"/api/hr/payroll-periods/{period_id}/generate", {}, h)
        if gen:
            print(f"  ✅ تم احتساب الرواتب")
        
        # Post payroll
        post = api("POST", f"/api/hr/payroll-periods/{period_id}/post", {}, h)
        if post:
            print(f"  ✅ تم ترحيل الرواتب - قيد محاسبي تم إنشاؤه")

# ============================================================
# PHASE 17: FIXED ASSETS
# ============================================================
def execute_assets(h):
    step("المرحلة 17: الأصول الثابتة")
    
    br1 = IDS.get("branch_BR001", 1)
    br2 = IDS.get("branch_BR002", 2)
    
    assets = [
        {"name": "سيارة نقل تويوتا هايلوكس", "code": "AST-VEH-001", "type": "vehicles",
         "purchase_date": "2026-01-15", "cost": 150000, "residual_value": 30000,
         "life_years": 5, "branch_id": br1, "currency": "SAR", "depreciation_method": "straight_line"},
        {"name": "أثاث مكتبي - المقر الرئيسي", "code": "AST-FUR-001", "type": "furniture",
         "purchase_date": "2026-01-01", "cost": 45000, "residual_value": 5000,
         "life_years": 10, "branch_id": br1, "currency": "SAR", "depreciation_method": "straight_line"},
        {"name": "خادم Dell PowerEdge", "code": "AST-EQP-001", "type": "equipment",
         "purchase_date": "2026-02-01", "cost": 85000, "residual_value": 10000,
         "life_years": 4, "branch_id": br1, "currency": "SAR", "depreciation_method": "straight_line"},
        {"name": "أثاث مكتبي - فرع جدة", "code": "AST-FUR-002", "type": "furniture",
         "purchase_date": "2026-01-15", "cost": 30000, "residual_value": 3000,
         "life_years": 10, "branch_id": br2, "currency": "SAR", "depreciation_method": "straight_line"},
    ]
    
    for asset in assets:
        result = api("POST", "/api/assets/", asset, h)
        if result and isinstance(result, dict) and result.get("id"):
            IDS[f"asset_{asset['code']}"] = result["id"]
            annual_dep = (asset['cost'] - asset['residual_value']) / asset['life_years']
            print(f"  ✅ {asset['name']} — {asset['cost']:,.0f} ر.س (إهلاك سنوي: {annual_dep:,.0f})")

# ============================================================
# PHASE 18: JOURNAL ENTRIES (Additional)
# ============================================================
def execute_journal_entries(h):
    step("المرحلة 18: قيود يدوية إضافية")
    
    accounts = api("GET", "/api/accounting/accounts", headers=h)
    acct_map = {}
    if isinstance(accounts, list):
        for a in accounts:
            acct_map[a["account_code"]] = a["id"]
    
    br1 = IDS.get("branch_BR001", 1)
    
    # JE 1: تسوية مصروفات مستحقة (إيجار مستحق لم يُدفع)
    acc_id = acct_map.get("ACC")  # مستحقة
    rnt_id = acct_map.get("RNT")  # مصروف الإيجار
    if acc_id and rnt_id:
        je1 = api("POST", "/api/accounting/journal-entries", {
            "date": "2026-02-28",
            "description": "تسوية - إيجار مستحق لفرع دبي",
            "reference": "ADJ-001",
            "status": "posted",
            "branch_id": IDS.get("branch_BR003", 3),
            "currency": "SAR",
            "exchange_rate": 1.0,
            "lines": [
                {"account_id": rnt_id, "debit": 18000, "credit": 0,
                 "description": "مصروف إيجار فرع دبي - فبراير"},
                {"account_id": acc_id, "debit": 0, "credit": 18000,
                 "description": "إيجار مستحق - فرع دبي"}
            ]
        }, h)
        if je1 and isinstance(je1, dict) and (je1.get("id") or je1.get("entry_id")):
            print(f"  ✅ قيد تسوية - إيجار مستحق 18,000 ر.س")
    
    # JE 2: قيد بعملة أجنبية (مصروف بالدولار)
    # مصروف استشارة 2,000 USD × 3.75 = 7,500 SAR
    legal_id = acct_map.get("LEGAL")  # مصروفات قانونية
    bnk_id = acct_map.get("BNK")      # البنك
    if legal_id and bnk_id:
        je2 = api("POST", "/api/accounting/journal-entries", {
            "date": "2026-02-20",
            "description": "استشارة قانونية دولية - USD",
            "reference": "JE-USD-001",
            "status": "posted",
            "branch_id": br1,
            "currency": "USD",
            "exchange_rate": 3.75,
            "lines": [
                {"account_id": legal_id, "debit": 2000, "credit": 0,
                 "description": "مصروف استشارة قانونية",
                 "currency": "USD", "amount_currency": 2000},
                {"account_id": bnk_id, "debit": 0, "credit": 2000,
                 "description": "دفع من البنك",
                 "currency": "USD", "amount_currency": 2000}
            ]
        }, h)
        if je2 and isinstance(je2, dict) and (je2.get("id") or je2.get("entry_id")):
            print(f"  ✅ قيد بالدولار — 2,000$ = 7,500 ر.س (استشارة قانونية)")
    
    # JE 3: مصروف مدفوع مقدماً
    pre_id = acct_map.get("PRE-INS")  # تأمين مدفوع مقدماً
    cash_id = acct_map.get("BOX")     # الصندوق
    if pre_id and cash_id:
        je3 = api("POST", "/api/accounting/journal-entries", {
            "date": "2026-02-15",
            "description": "تأمين سيارات مدفوع مقدماً - سنة كاملة",
            "reference": "PRE-001",
            "status": "posted",
            "branch_id": br1,
            "currency": "SAR",
            "exchange_rate": 1.0,
            "lines": [
                {"account_id": pre_id, "debit": 12000, "credit": 0,
                 "description": "تأمين سيارات مدفوع مقدماً (12 شهر)"},
                {"account_id": cash_id, "debit": 0, "credit": 12000,
                 "description": "دفع نقدي"}
            ]
        }, h)
        if je3 and isinstance(je3, dict) and (je3.get("id") or je3.get("entry_id")):
            print(f"  ✅ قيد مدفوع مقدماً — 12,000 ر.س (تأمين سيارات)")

# ============================================================
# PHASE 19: VERIFICATION
# ============================================================
def verify_all(h):
    step("المرحلة 19: التحقق من صحة جميع البيانات")
    
    print("\n  === 1. التحقق من أرصدة الحسابات ===")
    accounts = api("GET", "/api/accounting/accounts", headers=h)
    if isinstance(accounts, list):
        total_debit_balance = 0
        total_credit_balance = 0
        print(f"  عدد الحسابات: {len(accounts)}")
        key_accounts = {}
        for a in accounts:
            bal = float(a.get("balance", 0))
            code = a.get("account_code", "")
            name = a.get("name", "")
            atype = a.get("account_type", "")
            if bal != 0:
                key_accounts[code] = {"name": name, "balance": bal, "type": atype}
            if atype in ["asset", "expense"]:
                total_debit_balance += bal
            else:
                total_credit_balance += bal
        
        print(f"\n  حسابات ذات أرصدة:")
        for code, info in sorted(key_accounts.items()):
            direction = "مدين" if info["type"] in ["asset","expense"] else "دائن"
            print(f"    {code:15} {info['name']:30} {info['balance']:>15,.2f} ({direction})")
        
        print(f"\n  إجمالي الأرصدة المدينة: {total_debit_balance:,.2f}")
        print(f"  إجمالي الأرصدة الدائنة: {total_credit_balance:,.2f}")
        diff = abs(total_debit_balance - total_credit_balance)
        if diff < 0.01:
            print(f"  ✅ ميزان المراجعة متوازن!")
        else:
            print(f"  ⚠️  فرق في ميزان المراجعة: {diff:,.2f}")
    
    print("\n  === 2. التحقق من أرصدة الخزينة ===")
    treasury = api("GET", "/api/treasury/accounts", headers=h)
    if isinstance(treasury, list):
        for t in treasury:
            bal = t.get("balance", t.get("current_balance", 0))
            print(f"    {t['name']:30} {bal:>15,.2f} {t.get('currency','SAR')}")
    elif isinstance(treasury, dict):
        items = treasury.get("accounts", treasury.get("items", []))
        for t in items:
            bal = t.get("balance", t.get("current_balance", 0))
            print(f"    {t['name']:30} {bal:>15,.2f} {t.get('currency','SAR')}")
    
    print("\n  === 3. التحقق من المخزون ===")
    products = api("GET", "/api/inventory/products", headers=h)
    if isinstance(products, list):
        for p in products:
            stock = p.get("stock_quantity", p.get("total_stock", 0))
            cost = p.get("buying_price", p.get("avg_cost", 0))
            print(f"    {p['item_code']:10} {p['item_name']:25} كمية={stock:>6} تكلفة={cost:>10,.2f}")
    elif isinstance(products, dict):
        items = products.get("items", [])
        for p in items:
            stock = p.get("stock_quantity", p.get("total_stock", 0))
            cost = p.get("buying_price", p.get("avg_cost", 0))
            print(f"    {p['item_code']:10} {p['item_name']:25} كمية={stock:>6} تكلفة={cost:>10,.2f}")
    
    print("\n  === 4. التحقق من العملاء والموردين ===")
    customers = api("GET", "/api/sales/customers", headers=h)
    if isinstance(customers, list):
        print(f"  عدد العملاء: {len(customers)}")
        for c in customers:
            bal = c.get("balance", c.get("outstanding", 0))
            print(f"    {c['name']:30} رصيد={bal:>12,.2f} {c.get('currency','SAR')}")
    
    suppliers = api("GET", "/api/buying/suppliers", headers=h)
    sup_list = suppliers if isinstance(suppliers, list) else (suppliers.get("items", []) if isinstance(suppliers, dict) else [])
    print(f"  عدد الموردين: {len(sup_list)}")
    for s in sup_list:
        bal = s.get("balance", s.get("outstanding", 0))
        print(f"    {s.get('supplier_name',''):30} رصيد={bal:>12,.2f}")
    
    print("\n  === 5. التحقق من الفواتير ===")
    # Sales invoices
    sinvoices = api("GET", "/api/sales/invoices", headers=h)
    sinv_list = sinvoices if isinstance(sinvoices, list) else (sinvoices.get("invoices", sinvoices.get("items", [])) if isinstance(sinvoices, dict) else [])
    print(f"  فواتير المبيعات: {len(sinv_list)}")
    for inv in sinv_list:
        total = inv.get("total", inv.get("grand_total", 0))
        paid = inv.get("paid_amount", 0)
        status = inv.get("status", "")
        curr = inv.get("currency", "SAR")
        print(f"    #{inv.get('id','?'):3} | {total:>10,.2f} {curr:4} | مدفوع={paid:>10,.2f} | {status}")
    
    # Purchase invoices 
    pinvoices = api("GET", "/api/buying/invoices", headers=h)
    pinv_list = pinvoices if isinstance(pinvoices, list) else (pinvoices.get("invoices", pinvoices.get("items", [])) if isinstance(pinvoices, dict) else [])
    print(f"  فواتير المشتريات: {len(pinv_list)}")
    for inv in pinv_list:
        total = inv.get("total", inv.get("grand_total", 0))
        paid = inv.get("paid_amount", 0)
        status = inv.get("status", "")
        curr = inv.get("currency", "SAR")
        print(f"    #{inv.get('id','?'):3} | {total:>10,.2f} {curr:4} | مدفوع={paid:>10,.2f} | {status}")
    
    print("\n  === 6. الموظفين والرواتب ===")
    employees = api("GET", "/api/hr/employees", headers=h)
    emp_list = employees if isinstance(employees, list) else (employees.get("employees", employees.get("items", [])) if isinstance(employees, dict) else [])
    print(f"  عدد الموظفين: {len(emp_list)}")
    for e in emp_list:
        name = f"{e.get('first_name','')} {e.get('last_name','')}"
        salary = e.get("salary", 0)
        print(f"    {name:25} راتب={salary:>10,.2f}")
    
    print("\n  === 7. الأصول الثابتة ===")
    assets = api("GET", "/api/assets/", headers=h)
    ast_list = assets if isinstance(assets, list) else (assets.get("assets", assets.get("items", [])) if isinstance(assets, dict) else [])
    print(f"  عدد الأصول: {len(ast_list)}")
    for a in ast_list:
        print(f"    {a.get('name',''):35} تكلفة={a.get('cost',0):>12,.2f}")

# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("  AMAN ERP — إدخال بيانات اختبارية شاملة")
    print(f"  الشركة: {COMPANY_ID}")
    print(f"  التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    h = login()
    
    # Setup phases
    setup_currencies(h)
    setup_branches(h)
    setup_fiscal_year(h)
    setup_warehouses(h)
    setup_products(h)
    setup_suppliers(h)
    setup_customers(h)
    setup_treasury(h)
    setup_opening_balances(h)
    
    # Transaction phases
    execute_purchases(h)
    execute_supplier_payments(h)
    execute_sales(h)
    execute_customer_receipts(h)
    execute_treasury_transfers(h)
    execute_expenses(h)
    execute_hr(h)
    execute_assets(h)
    execute_journal_entries(h)
    
    # Verification
    verify_all(h)
    
    print("\n" + "=" * 60)
    print("  ✅ اكتمل إدخال البيانات والتحقق")
    print("=" * 60)

if __name__ == "__main__":
    main()
