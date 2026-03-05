#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
AMAN ERP — Comprehensive Data Seed v3
Company: ba2f6dc3 | Server: http://64.225.49.118
═══════════════════════════════════════════════════════════════════════

This script adds:
  1. Cost Centers (linked to departments)
  2. USD/EUR Suppliers (international)
  3. Manufacturing Setup (work centers, routes, BOMs, equipment)
  4. Manufacturing Settings
  5. Additional Journal Entries (more funds for testing)
  6. Stock Receipts (initial inventory for all warehouses)
  7. Price Lists
  8. Purchase Orders (sample)
  9. Sales Invoices (sample)

Pre-existing data (from v1/v2 seeds):
  - Branches: 3, Accounts: 121, FiscalYear: 2026
  - Departments: 8, Positions: 8, Employees: 9
  - Categories: 5, Products: 7, Warehouses: 5
  - Customers: 6, Suppliers: 5, Treasury: 7
  - TaxRates: 9, Currencies: 5 (SAR,USD,EUR,AED,EGP)
  - CustomerGroups: 3, JournalEntries: 8, Roles: 8
"""

import requests
import json
import sys
import time
from datetime import date, datetime

# ── Configuration ────────────────────────────────────────────────────────
API = "http://64.225.49.118/api"
USERNAME = "vvvv"
PASSWORD = "As123321"
COMPANY_CODE = "ba2f6dc3"

# ── Known Account IDs ────────────────────────────────────────────────────
ACC = {
    "cash": 8,          # صندوق نقدي
    "bank": 9,          # حساب بنكي عام
    "ar": 10,           # ذمم مدينة
    "inventory": 11,    # مخزون بضاعة
    "raw_materials": 12,# مواد خام
    "finished_goods": 13,# بضاعة تامة الصنع
    "wip": 14,          # إنتاج تحت التشغيل
    "emp_loans": 16,    # سلف وقروض موظفين
    "prepaid": 17,      # مصروفات مدفوعة مقدماً
    "fixed_assets": 18, # أصول ثابتة - أثاث ومعدات
    "machinery": 19,    # آلات ومعدات ثقيلة
    "computers": 24,    # أجهزة حاسب وتقنية
    "accum_depr": 25,   # مجمع إهلاك
    "vat_in": 27,       # ضريبة مدخلات
    "ap": 31,           # ذمم دائنة
    "vat_out": 35,      # ضريبة مخرجات
    "gosi": 37,         # تأمينات اجتماعية
    "eos": 42,          # نهاية خدمة
    "capital": 43,      # رأس المال
    "retained": 44,     # أرباح مبقاة
    "curr_year": 45,    # أرباح العام الحالي
    "sales_goods": 48,  # إيرادات بيع بضاعة
    "cogs": 56,         # تكلفة البضاعة المباعة
    "salaries": 61,     # رواتب وأجور
    "prepaid_rent": 109,# إيجارات مدفوعة مقدماً
    "prepaid_ins": 110, # تأمينات مدفوعة مقدماً
    "rajhi": 115,       # بنك الراجحي
    "ncb": 116,         # البنك الأهلي
    "inma": 117,        # بنك الإنماء
    "enbd": 118,        # بنك الإمارات
}

# ── Session ──────────────────────────────────────────────────────────────
session = requests.Session()
stats = {"created": 0, "skipped": 0, "errors": 0}


def login():
    r = session.post(f"{API}/auth/login", data={
        "username": USERNAME,
        "password": PASSWORD,
        "company_code": COMPANY_CODE
    })
    if r.status_code != 200:
        print(f"❌ Login failed: {r.status_code} {r.text}")
        sys.exit(1)
    token = r.json()["access_token"]
    session.headers["Authorization"] = f"Bearer {token}"
    session.headers["X-Company-ID"] = COMPANY_CODE
    print(f"✅ Logged in as {USERNAME}")


def api_post(endpoint, data, label=""):
    """POST with error handling. Returns response JSON or None."""
    try:
        r = session.post(f"{API}{endpoint}", json=data)
        if r.status_code in (200, 201):
            stats["created"] += 1
            result = r.json()
            if label:
                rid = result.get("id", result.get("message", "ok"))
                print(f"  ✅ {label} → {rid}")
            return result
        elif r.status_code == 409 or "already exists" in r.text.lower() or "duplicate" in r.text.lower():
            stats["skipped"] += 1
            if label:
                print(f"  ⏭️  {label} (exists)")
            return None
        else:
            stats["errors"] += 1
            print(f"  ❌ {label}: {r.status_code} {r.text[:150]}")
            return None
    except Exception as e:
        stats["errors"] += 1
        print(f"  ❌ {label}: {e}")
        return None


def api_get(endpoint):
    """GET with error handling."""
    try:
        r = session.get(f"{API}{endpoint}")
        if r.status_code == 200:
            return r.json()
        return None
    except:
        return None


def readback_ids(endpoint, name_field="name"):
    """Read back a list and build name→id map."""
    data = api_get(endpoint)
    if not data:
        return {}
    items = data
    if isinstance(data, dict):
        items = data.get("items", data.get("data", []))
    result = {}
    for item in items:
        key = item.get(name_field, item.get("name", ""))
        result[key] = item.get("id", 0)
    return result


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 1: Cost Centers
# ═══════════════════════════════════════════════════════════════════════════
def phase_cost_centers():
    print("\n▶ Phase 1: Cost Centers")
    
    # Get department IDs
    depts = readback_ids("/hr/departments", "name")
    
    cost_centers = [
        {"center_code": "CC-FIN",  "center_name": "مركز تكلفة - الإدارة المالية",   "center_name_en": "Finance",       "department_id": depts.get("الإدارة المالية")},
        {"center_code": "CC-SALES","center_name": "مركز تكلفة - المبيعات",          "center_name_en": "Sales",         "department_id": depts.get("قسم المبيعات")},
        {"center_code": "CC-PURCH","center_name": "مركز تكلفة - المشتريات",         "center_name_en": "Purchasing",    "department_id": depts.get("قسم المشتريات")},
        {"center_code": "CC-WH",   "center_name": "مركز تكلفة - المستودعات",        "center_name_en": "Warehouse",     "department_id": depts.get("إدارة المستودعات")},
        {"center_code": "CC-HR",   "center_name": "مركز تكلفة - الموارد البشرية",   "center_name_en": "HR",            "department_id": depts.get("الموارد البشرية")},
        {"center_code": "CC-MFG",  "center_name": "مركز تكلفة - التصنيع",           "center_name_en": "Manufacturing", "department_id": depts.get("قسم التصنيع")},
        {"center_code": "CC-IT",   "center_name": "مركز تكلفة - تقنية المعلومات",   "center_name_en": "IT",            "department_id": depts.get("تقنية المعلومات")},
    ]
    
    for cc in cost_centers:
        cc["is_active"] = True
        api_post("/cost-centers/", cc, cc["center_name_en"])
    
    return readback_ids("/cost-centers/", "center_name")


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 2: International Suppliers (USD/EUR)
# ═══════════════════════════════════════════════════════════════════════════
def phase_intl_suppliers():
    print("\n▶ Phase 2: International Suppliers (USD/EUR)")
    
    suppliers = [
        {
            "name": "Shanghai Metal Corp",
            "name_en": "Shanghai Metal Corporation",
            "phone": "+86-21-58854942",
            "email": "sales@shanghaimetal.com",
            "address": "Shanghai, China",
            "tax_number": "CN912101003A",
            "currency": "USD",
            "branch_id": 1,
        },
        {
            "name": "European Glass Industries",
            "name_en": "European Glass Industries GmbH",
            "phone": "+49-89-123456",
            "email": "info@eu-glass.de",
            "address": "Munich, Germany",
            "tax_number": "DE123456789",
            "currency": "EUR",
            "branch_id": 1,
        },
        {
            "name": "US Aluminium Supply Co",
            "name_en": "US Aluminium Supply Company",
            "phone": "+1-281-555-0100",
            "email": "orders@usaluminium.com",
            "address": "Houston, TX, USA",
            "tax_number": "US87-1234567",
            "currency": "USD",
            "branch_id": 1,
        },
        {
            "name": "Italian Hardware SpA",
            "name_en": "Italian Hardware SpA",
            "phone": "+39-02-9876543",
            "email": "export@italhardware.it",
            "address": "Milan, Italy",
            "tax_number": "IT12345678901",
            "currency": "EUR",
            "branch_id": 1,
        },
    ]
    
    for sup in suppliers:
        api_post("/inventory/suppliers", sup, f"{sup['name_en']} ({sup['currency']})")
    
    return readback_ids("/parties/suppliers", "name")


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 3: Supplier Groups
# ═══════════════════════════════════════════════════════════════════════════
def phase_supplier_groups():
    print("\n▶ Phase 3: Supplier Groups")
    
    groups = [
        {"group_name": "موردون محليون",    "group_name_en": "Local Suppliers",        "description": "موردون داخل المملكة العربية السعودية", "payment_days": 30},
        {"group_name": "موردون دوليون",    "group_name_en": "International Suppliers", "description": "موردون من خارج المملكة", "payment_days": 60},
        {"group_name": "مصنعون",           "group_name_en": "Manufacturers",           "description": "مصانع وشركات تصنيع", "payment_days": 45},
    ]
    
    for g in groups:
        api_post("/buying/supplier-groups", g, g["group_name_en"])


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 4: Additional Products (Raw Materials for Manufacturing)
# ═══════════════════════════════════════════════════════════════════════════
def phase_additional_products():
    print("\n▶ Phase 4: Additional Products (Raw Materials)")
    
    # Get existing categories - API returns 'name' field
    cats = readback_ids("/inventory/categories", "name")
    
    # We need raw material category - check if exists
    raw_mat_cat = cats.get("مواد خام ومستلزمات") or cats.get("مواد خام")
    if not raw_mat_cat:
        # Create raw materials category
        r = api_post("/inventory/categories", {
            "name": "مواد خام ومستلزمات",
            "name_en": "Raw Materials & Supplies",
            "description": "المواد الأولية المستخدمة في التصنيع"
        }, "Raw Materials Category")
        if r:
            raw_mat_cat = r.get("id")
        cats = readback_ids("/inventory/categories", "name")
        raw_mat_cat = raw_mat_cat or cats.get("مواد خام ومستلزمات") or cats.get("مواد خام")
    
    # Get existing products
    existing = api_get("/inventory/products") or []
    existing_names = {p.get("item_name", p.get("product_name", "")) for p in existing}
    
    products = [
        {"item_code": "RAW-ALU-001", "item_name": "ألمنيوم خام - بروفايل", "item_name_en": "Aluminium Profile Raw",
         "item_type": "raw_material", "unit": "متر", "buying_price": 25, "selling_price": 0,
         "category_id": raw_mat_cat, "description": "بروفايل ألمنيوم خام 6 متر"},
        {"item_code": "RAW-GLS-001", "item_name": "زجاج شفاف 6 مم", "item_name_en": "Clear Glass 6mm",
         "item_type": "raw_material", "unit": "متر مربع", "buying_price": 45, "selling_price": 0,
         "category_id": raw_mat_cat, "description": "زجاج شفاف سمك 6 مم"},
        {"item_code": "RAW-HDL-001", "item_name": "مقابض ألمنيوم", "item_name_en": "Aluminium Handles",
         "item_type": "raw_material", "unit": "قطعة", "buying_price": 15, "selling_price": 0,
         "category_id": raw_mat_cat, "description": "مقابض أبواب ونوافذ ألمنيوم"},
        {"item_code": "RAW-RUB-001", "item_name": "مطاط عازل", "item_name_en": "Rubber Seal",
         "item_type": "raw_material", "unit": "متر", "buying_price": 5, "selling_price": 0,
         "category_id": raw_mat_cat, "description": "شريط مطاطي عازل للأبواب والنوافذ"},
        {"item_code": "RAW-SCR-001", "item_name": "براغي وتثبيتات", "item_name_en": "Screws & Fasteners",
         "item_type": "raw_material", "unit": "علبة", "buying_price": 8, "selling_price": 0,
         "category_id": raw_mat_cat, "description": "أدوات تثبيت متنوعة"},
        {"item_code": "RAW-PNT-001", "item_name": "دهان بودرة ألمنيوم", "item_name_en": "Aluminium Powder Paint",
         "item_type": "raw_material", "unit": "كيلوغرام", "buying_price": 35, "selling_price": 0,
         "category_id": raw_mat_cat, "description": "دهان بودرة للألمنيوم"},
    ]
    
    for p in products:
        if p["item_name"] not in existing_names:
            api_post("/inventory/products", p, p["item_name_en"])
        else:
            print(f"  ⏭️  {p['item_name_en']} (exists)")
            stats["skipped"] += 1


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 5: Manufacturing Setup
# ═══════════════════════════════════════════════════════════════════════════
def phase_manufacturing(cc_map):
    print("\n▶ Phase 5: Manufacturing Setup")
    
    cc_mfg_id = None
    for k, v in cc_map.items():
        if "تصنيع" in k or "Manufacturing" in k.lower():
            cc_mfg_id = v
            break
    
    # 5a. Work Centers
    print("  📍 Work Centers:")
    work_centers = [
        {
            "name": "ورشة القطع والتشكيل",
            "code": "WC-CUT",
            "capacity_per_day": 8,
            "cost_per_hour": 75.0,
            "location": "المصنع الرئيسي - جناح A",
            "status": "active",
            "cost_center_id": cc_mfg_id,
            "default_expense_account_id": ACC["machinery"],
        },
        {
            "name": "ورشة التجميع",
            "code": "WC-ASM",
            "capacity_per_day": 6,
            "cost_per_hour": 60.0,
            "location": "المصنع الرئيسي - جناح B",
            "status": "active",
            "cost_center_id": cc_mfg_id,
            "default_expense_account_id": ACC["machinery"],
        },
        {
            "name": "ورشة الدهان والتشطيب",
            "code": "WC-FIN",
            "capacity_per_day": 10,
            "cost_per_hour": 50.0,
            "location": "المصنع الرئيسي - جناح C",
            "status": "active",
            "cost_center_id": cc_mfg_id,
            "default_expense_account_id": ACC["machinery"],
        },
        {
            "name": "ورشة التركيب والزجاج",
            "code": "WC-GLS",
            "capacity_per_day": 5,
            "cost_per_hour": 65.0,
            "location": "المصنع الرئيسي - جناح D",
            "status": "active",
            "cost_center_id": cc_mfg_id,
            "default_expense_account_id": ACC["machinery"],
        },
    ]
    
    for wc in work_centers:
        api_post("/manufacturing/work-centers", wc, wc["name"])
    
    wc_map = readback_ids("/manufacturing/work-centers", "name")
    wc_cut = wc_map.get("ورشة القطع والتشكيل")
    wc_asm = wc_map.get("ورشة التجميع")
    wc_fin = wc_map.get("ورشة الدهان والتشطيب")
    wc_gls = wc_map.get("ورشة التركيب والزجاج")
    
    # 5b. Equipment
    print("  🔧 Equipment:")
    equipment = [
        {"name": "ماكينة قطع ألمنيوم CNC", "code": "EQ-CNC-01", "work_center_id": wc_cut, "status": "active", "purchase_date": "2024-01-15", "notes": "ماكينة قطع رقمية عالية الدقة"},
        {"name": "ماكينة ثقب وتفريز", "code": "EQ-DRL-01", "work_center_id": wc_cut, "status": "active", "purchase_date": "2024-03-01", "notes": "ماكينة ثقب وتفريز للبروفايل"},
        {"name": "ماكينة لحام ألمنيوم", "code": "EQ-WLD-01", "work_center_id": wc_asm, "status": "active", "purchase_date": "2024-02-10", "notes": "لحام زوايا الأبواب والنوافذ"},
        {"name": "فرن دهان بودرة", "code": "EQ-OVN-01", "work_center_id": wc_fin, "status": "active", "purchase_date": "2023-06-20", "notes": "فرن دهان بودرة حراري"},
        {"name": "ماكينة قطع زجاج", "code": "EQ-GCT-01", "work_center_id": wc_gls, "status": "active", "purchase_date": "2024-05-12", "notes": "ماكينة قطع زجاج أوتوماتيكية"},
        {"name": "كمبروسر ضغط هواء", "code": "EQ-CMP-01", "work_center_id": wc_asm, "status": "active", "purchase_date": "2023-11-05", "notes": "ضاغط هواء صناعي 500 لتر"},
    ]
    
    for eq in equipment:
        api_post("/manufacturing/equipment", eq, eq["name"])
    
    # 5c. Manufacturing Routes (Routings)
    print("  🛤️  Manufacturing Routes:")
    
    # Get products for linking
    products = api_get("/inventory/products") or []
    prod_map = {}
    for p in products:
        name = p.get("item_name") or p.get("product_name", "")
        prod_map[name] = p.get("id")
        name_en = p.get("item_name_en") or p.get("product_name_en", "")
        if name_en:
            prod_map[name_en] = p.get("id")
    
    routes = [
        {
            "name": "مسار تصنيع أبواب ألمنيوم",
            "description": "المسار الكامل لتصنيع أبواب ألمنيوم من القطع إلى التركيب",
            "is_active": True,
            "operations": [
                {"sequence": 1, "work_center_id": wc_cut, "description": "قطع بروفايلات الألمنيوم حسب المقاسات", "setup_time": 15, "cycle_time": 30},
                {"sequence": 2, "work_center_id": wc_cut, "description": "ثقب وتفريز البروفايلات", "setup_time": 10, "cycle_time": 20},
                {"sequence": 3, "work_center_id": wc_fin, "description": "الدهان والتشطيب", "setup_time": 20, "cycle_time": 45},
                {"sequence": 4, "work_center_id": wc_asm, "description": "تجميع إطار الباب", "setup_time": 10, "cycle_time": 40},
                {"sequence": 5, "work_center_id": wc_gls, "description": "تركيب الزجاج والمقابض", "setup_time": 5, "cycle_time": 25},
            ]
        },
        {
            "name": "مسار تصنيع نوافذ ألمنيوم",
            "description": "المسار الكامل لتصنيع نوافذ ألمنيوم",
            "is_active": True,
            "operations": [
                {"sequence": 1, "work_center_id": wc_cut, "description": "قطع بروفايلات النوافذ", "setup_time": 10, "cycle_time": 20},
                {"sequence": 2, "work_center_id": wc_fin, "description": "دهان بودرة", "setup_time": 15, "cycle_time": 30},
                {"sequence": 3, "work_center_id": wc_asm, "description": "تجميع إطار النافذة", "setup_time": 10, "cycle_time": 30},
                {"sequence": 4, "work_center_id": wc_gls, "description": "تركيب الزجاج وختم العزل", "setup_time": 5, "cycle_time": 20},
            ]
        },
        {
            "name": "مسار تصنيع واجهات كرتن وول",
            "description": "تصنيع واجهات زجاجية كرتن وول",
            "is_active": True,
            "operations": [
                {"sequence": 1, "work_center_id": wc_cut, "description": "قطع الهيكل الحامل", "setup_time": 20, "cycle_time": 60},
                {"sequence": 2, "work_center_id": wc_fin, "description": "معالجة وطلاء السطح", "setup_time": 15, "cycle_time": 45},
                {"sequence": 3, "work_center_id": wc_asm, "description": "تجميع الوحدات", "setup_time": 15, "cycle_time": 60},
                {"sequence": 4, "work_center_id": wc_gls, "description": "تركيب الألواح الزجاجية", "setup_time": 10, "cycle_time": 50},
            ]
        },
    ]
    
    route_ids = {}
    for rt in routes:
        result = api_post("/manufacturing/routes", rt, rt["name"])
        if result:
            route_ids[rt["name"]] = result.get("id")
    
    # Read back routes if needed
    routes_data = api_get("/manufacturing/routes") or []
    for rd in routes_data:
        route_ids[rd.get("name", "")] = rd.get("id")
    
    # 5d. Bills of Materials (BOMs)
    print("  📋 Bills of Materials (BOMs):")
    
    # Refresh product map - uses item_name or product_name
    products = api_get("/inventory/products") or []
    prod_map = {}
    for p in products:
        name = p.get("item_name") or p.get("product_name", "")
        prod_map[name] = p.get("id")
    
    door_route = route_ids.get("مسار تصنيع أبواب ألمنيوم")
    window_route = route_ids.get("مسار تصنيع نوافذ ألمنيوم")
    
    # Get product IDs for raw materials and finished goods
    alu_profile = prod_map.get("ألمنيوم خام - بروفايل")
    glass = prod_map.get("زجاج شفاف 6 مم")
    handles = prod_map.get("مقابض ألمنيوم")
    rubber = prod_map.get("مطاط عازل")
    screws = prod_map.get("براغي وتثبيتات")
    paint = prod_map.get("دهان بودرة ألمنيوم")
    
    # Find existing finished products (doors, windows)
    door_prod = None
    window_prod = None
    for pname, pid in prod_map.items():
        if any(x in str(pname) for x in ["باب", "أبواب", "door", "Door"]):
            door_prod = door_prod or pid
        if any(x in str(pname) for x in ["نافذة", "نوافذ", "window", "Window"]):
            window_prod = window_prod or pid
    
    boms = []
    
    if door_prod and alu_profile:
        boms.append({
            "name": "قائمة مواد - باب ألمنيوم قياسي",
            "code": "BOM-DOOR-STD",
            "product_id": door_prod,
            "yield_quantity": 1,
            "route_id": door_route,
            "is_active": True,
            "notes": "باب ألمنيوم قياسي 210×90 سم",
            "components": [
                {"component_product_id": alu_profile, "quantity": 12, "waste_percentage": 5, "cost_share_percentage": 40},
                {"component_product_id": glass, "quantity": 1.5, "waste_percentage": 3, "cost_share_percentage": 25} if glass else None,
                {"component_product_id": handles, "quantity": 1, "waste_percentage": 0, "cost_share_percentage": 10} if handles else None,
                {"component_product_id": rubber, "quantity": 6, "waste_percentage": 5, "cost_share_percentage": 5} if rubber else None,
                {"component_product_id": screws, "quantity": 1, "waste_percentage": 0, "cost_share_percentage": 5} if screws else None,
                {"component_product_id": paint, "quantity": 2, "waste_percentage": 10, "cost_share_percentage": 15} if paint else None,
            ],
            "outputs": []
        })
    
    if window_prod and alu_profile:
        boms.append({
            "name": "قائمة مواد - نافذة ألمنيوم قياسية",
            "code": "BOM-WIN-STD",
            "product_id": window_prod,
            "yield_quantity": 1,
            "route_id": window_route,
            "is_active": True,
            "notes": "نافذة ألمنيوم انزلاقية 150×120 سم",
            "components": [
                {"component_product_id": alu_profile, "quantity": 8, "waste_percentage": 5, "cost_share_percentage": 35},
                {"component_product_id": glass, "quantity": 3.6, "waste_percentage": 3, "cost_share_percentage": 30} if glass else None,
                {"component_product_id": handles, "quantity": 1, "waste_percentage": 0, "cost_share_percentage": 8} if handles else None,
                {"component_product_id": rubber, "quantity": 5, "waste_percentage": 5, "cost_share_percentage": 7} if rubber else None,
                {"component_product_id": screws, "quantity": 1, "waste_percentage": 0, "cost_share_percentage": 5} if screws else None,
                {"component_product_id": paint, "quantity": 1.5, "waste_percentage": 10, "cost_share_percentage": 15} if paint else None,
            ],
            "outputs": []
        })
    
    for bom in boms:
        # Remove None components
        bom["components"] = [c for c in bom["components"] if c is not None]
        api_post("/manufacturing/boms", bom, bom["name"])
    
    return wc_map, route_ids


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 6: Manufacturing Settings
# ═══════════════════════════════════════════════════════════════════════════
def phase_manufacturing_settings():
    print("\n▶ Phase 6: Manufacturing Settings")
    
    settings = {
        "mfg_overhead_rate": "15",
        "mfg_default_warehouse": "1",
        "mfg_auto_generate_order_number": "true",
        "mfg_allow_over_production": "false",
        "mfg_scrap_account_id": str(ACC["cogs"]),
        "acc_map_wip": str(ACC["wip"]),
        "acc_map_raw_materials": str(ACC["raw_materials"]),
        "acc_map_finished_goods": str(ACC["finished_goods"]),
        "acc_map_labor_cost": str(ACC["salaries"]),
        "acc_map_mfg_overhead": str(ACC["machinery"]),
    }
    
    r = session.post(f"{API}/settings/bulk", json={"settings": settings})
    if r.status_code == 200:
        print(f"  ✅ Manufacturing settings updated ({len(settings)} keys)")
        stats["created"] += 1
    else:
        print(f"  ❌ Settings update failed: {r.status_code} {r.text[:150]}")
        stats["errors"] += 1


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 7: Additional Journal Entries (More Funds)
# ═══════════════════════════════════════════════════════════════════════════
def phase_additional_funds():
    print("\n▶ Phase 7: Additional Funds (Journal Entries)")
    
    entries = [
        {
            "date": "2026-01-05",
            "description": "زيادة رأس المال - ضخ نقدي إضافي من الشركاء",
            "reference": "CAP-INJECT-001",
            "lines": [
                {"account_id": ACC["rajhi"],  "debit": 500000, "credit": 0, "description": "ضخ نقدي - بنك الراجحي"},
                {"account_id": ACC["ncb"],    "debit": 300000, "credit": 0, "description": "ضخ نقدي - البنك الأهلي"},
                {"account_id": ACC["inma"],   "debit": 200000, "credit": 0, "description": "ضخ نقدي - بنك الإنماء"},
                {"account_id": ACC["capital"],"debit": 0, "credit": 1000000, "description": "زيادة رأس المال"},
            ]
        },
        {
            "date": "2026-01-10",
            "description": "شراء آلات ومعدات تصنيع",
            "reference": "FA-MFG-001",
            "lines": [
                {"account_id": ACC["machinery"], "debit": 350000, "credit": 0, "description": "ماكينات تصنيع ألمنيوم"},
                {"account_id": ACC["computers"], "debit": 50000, "credit": 0,  "description": "أنظمة تحكم CNC وأجهزة"},
                {"account_id": ACC["vat_in"],     "debit": 60000, "credit": 0,  "description": "ضريبة مدخلات 15%"},
                {"account_id": ACC["rajhi"],      "debit": 0, "credit": 460000, "description": "سداد من بنك الراجحي"},
            ]
        },
        {
            "date": "2026-01-15",
            "description": "شراء مواد خام أولية - افتتاحية المخزون",
            "reference": "INV-RAW-001",
            "lines": [
                {"account_id": ACC["raw_materials"], "debit": 250000, "credit": 0, "description": "مواد خام - ألمنيوم وزجاج"},
                {"account_id": ACC["vat_in"],        "debit": 37500, "credit": 0,  "description": "ضريبة مدخلات 15%"},
                {"account_id": ACC["ap"],            "debit": 0, "credit": 187500, "description": "ذمم دائنة - مصنع الخليج"},
                {"account_id": ACC["rajhi"],         "debit": 0, "credit": 100000, "description": "دفعة مقدمة - بنك الراجحي"},
            ]
        },
        {
            "date": "2026-01-20",
            "description": "إيداع نقدي في صندوق الشركة وبنك الإمارات",
            "reference": "CASH-DEP-001",
            "lines": [
                {"account_id": ACC["cash"],  "debit": 100000, "credit": 0,  "description": "إيداع في صندوق الشركة الرئيسي"},
                {"account_id": ACC["enbd"],  "debit": 150000, "credit": 0,  "description": "إيداع في بنك الإمارات دبي"},
                {"account_id": ACC["capital"], "debit": 0, "credit": 250000, "description": "مساهمة إضافية من المالك"},
            ]
        },
        {
            "date": "2026-02-01",
            "description": "شراء بضاعة تامة الصنع للبيع المباشر",
            "reference": "INV-FG-001",
            "lines": [
                {"account_id": ACC["finished_goods"], "debit": 180000, "credit": 0, "description": "بضاعة تامة - أبواب ونوافذ جاهزة"},
                {"account_id": ACC["vat_in"],          "debit": 27000, "credit": 0,  "description": "ضريبة مدخلات 15%"},
                {"account_id": ACC["ncb"],             "debit": 0, "credit": 207000, "description": "سداد من البنك الأهلي"},
            ]
        },
        {
            "date": "2026-02-10",
            "description": "تحويل بين البنوك - تغذية حساب المشتريات",
            "reference": "BANK-TRF-001",
            "lines": [
                {"account_id": ACC["enbd"],  "debit": 200000, "credit": 0, "description": "تحويل وارد - بنك الإمارات"},
                {"account_id": ACC["rajhi"], "debit": 0, "credit": 200000, "description": "تحويل صادر - بنك الراجحي"},
            ]
        },
    ]
    
    for je in entries:
        api_post("/accounting/journal-entries", je, je["description"][:50])


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 8: Stock Receipts (Initial Inventory)
# ═══════════════════════════════════════════════════════════════════════════
def phase_stock_receipts():
    print("\n▶ Phase 8: Stock Receipts (Initial Inventory)")
    
    # Get products
    products = api_get("/inventory/products") or []
    prod_map = {}
    for p in products:
        name = p.get("item_name") or p.get("product_name", "")
        prod_map[name] = p.get("id")
    
    # Get warehouses
    warehouses = api_get("/inventory/warehouses") or []
    wh_map = {}
    for w in warehouses:
        wh_map[w.get("warehouse_name", "")] = w.get("id")
    
    # Main warehouse receipt - all products
    main_wh = wh_map.get("المستودع الرئيسي") or 1
    raw_wh = wh_map.get("مستودع المواد الخام") or main_wh
    fg_wh = wh_map.get("مستودع البضاعة التامة") or main_wh
    
    # Raw material product names (as stored in item_name)
    raw_material_names = ["ألمنيوم خام - بروفايل", "زجاج شفاف 6 مم", "مقابض ألمنيوم", "مطاط عازل", "براغي وتثبيتات", "دهان بودرة ألمنيوم"]
    # Stock receipt for raw materials warehouse
    raw_items = []
    for pname in raw_material_names:
        pid = prod_map.get(pname)
        if pid:
            qty = {"ألمنيوم خام - بروفايل": 500, "زجاج شفاف 6 مم": 200, "مقابض ألمنيوم": 300,
                   "مطاط عازل": 1000, "براغي وتثبيتات": 100, "دهان بودرة ألمنيوم": 150}.get(pname, 100)
            raw_items.append({"product_id": pid, "quantity": qty})
    
    if raw_items:
        api_post("/inventory/receipt", {
            "warehouse_id": raw_wh,
            "items": raw_items,
            "notes": "استلام مواد خام أولية - المخزون الافتتاحي",
            "date": "2026-01-16",
            "reference": "REC-RAW-001"
        }, "Raw materials receipt")
    
    # Stock receipt for finished goods
    fg_items = []
    for pname, pid in prod_map.items():
        if pname not in raw_material_names:
            fg_items.append({"product_id": pid, "quantity": 50})
    
    if fg_items:
        api_post("/inventory/receipt", {
            "warehouse_id": fg_wh if fg_wh != main_wh else main_wh,
            "items": fg_items,
            "notes": "استلام بضاعة تامة - المخزون الافتتاحي",
            "date": "2026-01-16",
            "reference": "REC-FG-001"
        }, "Finished goods receipt")
    
    # Some stock in main warehouse too
    main_items = []
    for pname, pid in prod_map.items():
        main_items.append({"product_id": pid, "quantity": 20})
    
    if main_items and main_wh != fg_wh:
        api_post("/inventory/receipt", {
            "warehouse_id": main_wh,
            "items": main_items,
            "notes": "مخزون عام في المستودع الرئيسي",
            "date": "2026-01-17",
            "reference": "REC-MAIN-001"
        }, "Main warehouse receipt")


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 9: Price Lists
# ═══════════════════════════════════════════════════════════════════════════
def phase_price_lists():
    print("\n▶ Phase 9: Price Lists")
    
    lists = [
        {"name": "قائمة أسعار التجزئة",   "currency": "SAR", "is_active": True, "is_default": True},
        {"name": "قائمة أسعار الجملة",     "currency": "SAR", "is_active": True, "is_default": False},
        {"name": "قائمة أسعار التصدير USD","currency": "USD", "is_active": True, "is_default": False},
        {"name": "قائمة أسعار التصدير EUR","currency": "EUR", "is_active": True, "is_default": False},
    ]
    
    for pl in lists:
        api_post("/inventory/price-lists", pl, pl["name"])


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 10: Sample Purchase Order
# ═══════════════════════════════════════════════════════════════════════════
def phase_purchase_orders():
    print("\n▶ Phase 10: Sample Purchase Orders")
    
    # Get suppliers
    sup_data = api_get("/parties/suppliers")
    suppliers = sup_data.get("items", []) if isinstance(sup_data, dict) else (sup_data or [])
    if not suppliers:
        print("  ⚠️ No suppliers found, skipping")
        return
    
    supplier = suppliers[0]
    
    # Get products
    products = api_get("/inventory/products") or []
    if len(products) < 2:
        print("  ⚠️ Not enough products, skipping")
        return
    
    po = {
        "supplier_id": supplier["id"],
        "order_date": "2026-02-15",
        "expected_date": "2026-03-01",
        "notes": "أمر شراء مواد خام - الدفعة الثانية",
        "items": [
            {
                "product_id": products[0]["id"],
                "description": products[0].get("item_name") or products[0].get("product_name", "منتج 1"),
                "quantity": 100,
                "unit_price": float(products[0].get("buying_price") or products[0].get("selling_price", 50)),
                "tax_rate": 15,
                "discount": 0,
                "markup": 0,
            },
            {
                "product_id": products[1]["id"],
                "description": products[1].get("item_name") or products[1].get("product_name", "منتج 2"),
                "quantity": 50,
                "unit_price": float(products[1].get("buying_price") or products[1].get("selling_price", 100)),
                "tax_rate": 15,
                "discount": 0,
                "markup": 0,
            },
        ]
    }
    
    api_post("/buying/orders", po, f"PO for {supplier['name'][:30]}")


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 11: Sample Sales Invoice
# ═══════════════════════════════════════════════════════════════════════════
def phase_sales_invoices():
    print("\n▶ Phase 11: Sample Sales Invoices")
    
    # Get customers
    cust_data = api_get("/sales/customers")
    customers = cust_data if isinstance(cust_data, list) else (cust_data.get("items", []) if isinstance(cust_data, dict) else [])
    if not customers:
        print("  ⚠️ No customers found, skipping")
        return
    
    # Get products
    products = api_get("/inventory/products") or []
    if not products:
        print("  ⚠️ No products found, skipping")
        return
    
    # Create 2 invoices for different customers
    for i, cust in enumerate(customers[:2]):
        prod_idx = i % len(products)
        prod2_idx = (i + 1) % len(products)
        p1 = products[prod_idx]
        p2 = products[prod2_idx]
        p1_name = p1.get("item_name") or p1.get("product_name", "منتج")
        p2_name = p2.get("item_name") or p2.get("product_name", "منتج")
        p1_price = float(p1.get("selling_price") or p1.get("sell_price") or 500.0)
        p2_price = float(p2.get("selling_price") or p2.get("sell_price") or 500.0)
        # Ensure non-zero price
        if p1_price <= 0:
            p1_price = 500.0
        if p2_price <= 0:
            p2_price = 300.0
        
        inv = {
            "customer_id": cust["id"],
            "invoice_date": f"2026-02-{20+i}",
            "due_date": f"2026-03-{20+i}",
            "warehouse_id": 1,
            "notes": f"فاتورة مبيعات - {cust['name'][:30]}",
            "items": [
                {
                    "product_id": p1["id"],
                    "description": p1_name,
                    "quantity": 5,
                    "unit_price": p1_price,
                    "tax_rate": 15,
                    "discount": 0,
                },
                {
                    "product_id": p2["id"],
                    "description": p2_name,
                    "quantity": 3,
                    "unit_price": p2_price,
                    "tax_rate": 15,
                    "discount": 0,
                },
            ]
        }
        
        api_post("/sales/invoices", inv, f"Invoice for {cust['name'][:30]}")


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 12: Sample Production Order
# ═══════════════════════════════════════════════════════════════════════════
def phase_production_orders():
    print("\n▶ Phase 12: Sample Production Orders")
    
    # Get BOMs
    boms = api_get("/manufacturing/boms") or []
    if not boms:
        print("  ⚠️ No BOMs found, skipping")
        return
    
    # Get routes
    routes = api_get("/manufacturing/routes") or []
    
    for bom in boms[:2]:
        order = {
            "product_id": bom["product_id"],
            "bom_id": bom["id"],
            "route_id": bom.get("route_id"),
            "quantity": 10,
            "start_date": "2026-03-01",
            "due_date": "2026-03-15",
            "warehouse_id": 1,
            "destination_warehouse_id": 1,
            "status": "draft",
            "notes": f"أمر إنتاج - {bom.get('name', '')}",
        }
        
        api_post("/manufacturing/orders", order, f"Production Order: {bom.get('name', '')[:40]}")


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 13: Sample Quotation (CRM)
# ═══════════════════════════════════════════════════════════════════════════
def phase_quotations():
    print("\n▶ Phase 13: Sample Sales Quotation")
    
    # Get customers
    cust_data = api_get("/sales/customers")
    customers = cust_data if isinstance(cust_data, list) else (cust_data.get("items", []) if isinstance(cust_data, dict) else [])
    if not customers:
        print("  ⚠️ No customers, skipping")
        return
    
    products = api_get("/inventory/products") or []
    if not products:
        return
    
    p = products[0]
    p_price = float(p.get("selling_price") or 500.0)
    if p_price <= 0:
        p_price = 500.0
    p_name = p.get("item_name") or p.get("product_name", "منتج 1")
    
    quot = {
        "customer_id": customers[0]["id"],
        "quotation_date": "2026-03-01",
        "expiry_date": "2026-03-31",
        "notes": "عرض سعر شامل أبواب ونوافذ ألمنيوم",
        "items": [
            {
                "product_id": p["id"],
                "description": p_name,
                "quantity": 20,
                "unit_price": p_price,
                "tax_rate": 15,
                "discount": 5,
            },
        ]
    }
    
    api_post("/sales/quotations", quot, "Sales Quotation")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 65)
    print("  AMAN ERP — Comprehensive Data Seed v3")
    print(f"  Server: {API}")
    print(f"  Company: {COMPANY_CODE}")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 65)
    
    login()
    
    # Phase 1: Cost Centers
    cc_map = phase_cost_centers()
    
    # Phase 2: International Suppliers
    phase_intl_suppliers()
    
    # Phase 3: Supplier Groups
    phase_supplier_groups()
    
    # Phase 4: Additional Products (Raw Materials)
    phase_additional_products()
    
    # Phase 5: Manufacturing Setup
    phase_manufacturing(cc_map)
    
    # Phase 6: Manufacturing Settings
    phase_manufacturing_settings()
    
    # Phase 7: Additional Funds
    phase_additional_funds()
    
    # Phase 8: Stock Receipts
    phase_stock_receipts()
    
    # Phase 9: Price Lists
    phase_price_lists()
    
    # Phase 10: Purchase Orders
    phase_purchase_orders()
    
    # Phase 11: Sales Invoices
    phase_sales_invoices()
    
    # Phase 12: Production Orders
    phase_production_orders()
    
    # Phase 13: Quotations
    phase_quotations()
    
    # Summary
    print("\n" + "=" * 65)
    print(f"  ✅ Created: {stats['created']}")
    print(f"  ⏭️  Skipped: {stats['skipped']}")
    print(f"  ❌ Errors:  {stats['errors']}")
    print("=" * 65)


if __name__ == "__main__":
    main()
