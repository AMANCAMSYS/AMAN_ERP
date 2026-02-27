#!/usr/bin/env python3
"""
Comprehensive data entry for company 39a597c9 (SAR base)
Covers: Manufacturing, Projects, Services, Sales Returns, CRM, Payroll
"""
import requests
import json
import sys
import time

BASE = "http://localhost:8000/api"
TOKEN = open("/tmp/aman_token2.txt").read().strip()
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def api(method, path, data=None, label=""):
    url = f"{BASE}{path}"
    try:
        if method == "GET":
            r = requests.get(url, headers=HEADERS, timeout=30)
        elif method == "POST":
            r = requests.post(url, headers=HEADERS, json=data, timeout=30)
        elif method == "PUT":
            r = requests.put(url, headers=HEADERS, json=data, timeout=30)
        else:
            r = requests.request(method, url, headers=HEADERS, json=data, timeout=30)
        
        if r.status_code in (200, 201):
            try:
                return True, r.json()
            except:
                return True, {"status": "ok"}
        else:
            detail = ""
            try:
                detail = r.json().get("detail", r.text[:200])
            except:
                detail = r.text[:200]
            return False, f"HTTP {r.status_code}: {detail}"
    except Exception as e:
        return False, str(e)

results = {}

def phase(name, func):
    print(f"\n{'='*60}")
    print(f"📋 {name}")
    print(f"{'='*60}")
    try:
        func()
        results[name] = "✅"
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        results[name] = f"❌ {e}"

# ================================================================
# PHASE 1: MANUFACTURING
# ================================================================
def do_manufacturing():
    # 1a. Create Work Centers
    work_centers = [
        {"name": "خط التجميع الرئيسي", "name_en": "Main Assembly Line", "cost_per_hour": 150, "capacity": 8, "efficiency": 90},
        {"name": "ورشة اللحام", "name_en": "Welding Workshop", "cost_per_hour": 200, "capacity": 6, "efficiency": 85},
        {"name": "قسم الفحص والاختبار", "name_en": "QC & Testing", "cost_per_hour": 100, "capacity": 4, "efficiency": 95},
    ]
    wc_ids = []
    for wc in work_centers:
        ok, res = api("POST", "/manufacturing/work-centers", wc)
        if ok:
            wc_id = res.get("id", res.get("work_center", {}).get("id"))
            wc_ids.append(wc_id)
            print(f"  ✅ Work Center: {wc['name']} (ID: {wc_id})")
        else:
            print(f"  ❌ Work Center {wc['name']}: {res}")
            wc_ids.append(None)

    # 1b. Create Manufacturing Route
    route_data = {
        "name": "مسار تجميع الحاسوب",
        "name_en": "Computer Assembly Route",
        "operations": [
            {"name": "تجهيز المكونات", "name_en": "Prepare Components", "work_center_id": wc_ids[0] or 1, "sequence": 1, "setup_time": 15, "run_time": 30},
            {"name": "التجميع", "name_en": "Assembly", "work_center_id": wc_ids[0] or 1, "sequence": 2, "setup_time": 10, "run_time": 45},
            {"name": "الفحص النهائي", "name_en": "Final QC", "work_center_id": wc_ids[2] or 3, "sequence": 3, "setup_time": 5, "run_time": 20},
        ]
    }
    ok, res = api("POST", "/manufacturing/routes", route_data)
    route_id = None
    if ok:
        route_id = res.get("id", res.get("route", {}).get("id"))
        print(f"  ✅ Route: {route_data['name']} (ID: {route_id})")
    else:
        print(f"  ❌ Route: {res}")

    # 1c. Create BOM (Bill of Materials) - Assembled Computer
    # Product 1 = Laptop (finished good), Products 3,4,5 as components
    bom_data = {
        "product_id": 1,  # Laptop Dell
        "name": "قائمة مواد - لابتوب مجمع",
        "name_en": "BOM - Assembled Laptop",
        "quantity": 1,
        "route_id": route_id,
        "components": [
            {"product_id": 5, "quantity": 1, "notes": "شاشة Samsung"},  # Monitor
            {"product_id": 4, "quantity": 2, "notes": "حبر طابعة - ملحقات"},  # Toner - accessories
            {"product_id": 3, "quantity": 5, "notes": "ورق تغليف"},  # Paper - packaging
        ]
    }
    ok, res = api("POST", "/manufacturing/boms", bom_data)
    bom_id = None
    if ok:
        bom_id = res.get("id", res.get("bom", {}).get("id"))
        print(f"  ✅ BOM: {bom_data['name']} (ID: {bom_id})")
    else:
        print(f"  ❌ BOM: {res}")

    # 1d. Create Production Order
    prod_order_data = {
        "bom_id": bom_id or 1,
        "product_id": 1,
        "quantity": 5,
        "planned_start_date": "2026-02-20",
        "planned_end_date": "2026-02-25",
        "warehouse_id": 2,
        "notes": "أمر إنتاج 5 لابتوبات مجمعة"
    }
    ok, res = api("POST", "/manufacturing/orders", prod_order_data)
    order_id = None
    if ok:
        order_id = res.get("id", res.get("order", {}).get("id"))
        print(f"  ✅ Production Order (ID: {order_id})")
    else:
        print(f"  ❌ Production Order: {res}")

    # 1e. Start production
    if order_id:
        ok, res = api("POST", f"/manufacturing/orders/{order_id}/start", {})
        if ok:
            print(f"  ✅ Production started")
        else:
            print(f"  ⚠️ Start production: {res}")

        # 1f. Complete production
        ok, res = api("POST", f"/manufacturing/orders/{order_id}/complete", {})
        if ok:
            print(f"  ✅ Production completed")
        else:
            print(f"  ⚠️ Complete production: {res}")

    # 1g. Equipment
    equipment_data = [
        {"name": "ماكينة CNC", "name_en": "CNC Machine", "work_center_id": wc_ids[1] or 2, "serial_number": "CNC-001", "status": "operational", "purchase_date": "2025-06-01", "purchase_cost": 250000},
        {"name": "جهاز لحام بالليزر", "name_en": "Laser Welder", "work_center_id": wc_ids[1] or 2, "serial_number": "LW-001", "status": "operational", "purchase_date": "2025-08-15", "purchase_cost": 85000},
    ]
    for eq in equipment_data:
        ok, res = api("POST", "/manufacturing/equipment", eq)
        if ok:
            print(f"  ✅ Equipment: {eq['name']}")
        else:
            print(f"  ❌ Equipment {eq['name']}: {res}")

    # 1h. QC Check
    if order_id:
        qc_data = {
            "check_type": "visual_inspection",
            "parameter": "مظهر خارجي",
            "standard_value": "بدون خدوش",
            "tolerance": "0",
            "notes": "فحص بصري للمنتج النهائي"
        }
        ok, res = api("POST", f"/manufacturing/orders/{order_id}/qc-checks", qc_data)
        if ok:
            print(f"  ✅ QC Check created")
        else:
            print(f"  ⚠️ QC Check: {res}")


# ================================================================
# PHASE 2: PROJECTS
# ================================================================
def do_projects():
    projects = [
        {
            "name": "مشروع تطوير نظام ERP",
            "name_en": "ERP System Development",
            "code": "PRJ-001",
            "description": "تطوير نظام محاسبي متكامل للشركات",
            "status": "active",
            "start_date": "2026-01-15",
            "end_date": "2026-06-30",
            "budget": 150000,
            "customer_id": 5,
            "branch_id": 1,
            "project_type": "fixed_price",
            "billing_method": "milestone"
        },
        {
            "name": "مشروع تركيب شبكة - فرع جدة",
            "name_en": "Network Installation - Jeddah Branch",
            "code": "PRJ-002",
            "description": "تركيب وتشغيل البنية التحتية لشبكة فرع جدة",
            "status": "active",
            "start_date": "2026-02-01",
            "end_date": "2026-04-15",
            "budget": 75000,
            "customer_id": 6,
            "branch_id": 2,
            "project_type": "time_and_materials",
            "billing_method": "hourly"
        },
        {
            "name": "عقد صيانة سنوي - Gulf Services",
            "name_en": "Annual Maintenance Contract - Gulf Services",
            "code": "PRJ-003",
            "description": "عقد صيانة أجهزة وأنظمة لمدة سنة",
            "status": "active",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "budget": 200000,
            "customer_id": 7,
            "branch_id": 3,
            "project_type": "retainer",
            "billing_method": "monthly"
        }
    ]
    
    proj_ids = []
    for p in projects:
        ok, res = api("POST", "/projects/", p)
        if ok:
            pid = res.get("id", res.get("project", {}).get("id"))
            proj_ids.append(pid)
            print(f"  ✅ Project: {p['name']} (ID: {pid})")
        else:
            print(f"  ❌ Project {p['name']}: {res}")
            proj_ids.append(None)

    # Tasks for project 1
    if proj_ids[0]:
        tasks = [
            {"name": "تحليل المتطلبات", "description": "جمع وتوثيق جميع متطلبات النظام", "status": "completed", "priority": "high", "start_date": "2026-01-15", "end_date": "2026-02-01", "estimated_hours": 80, "actual_hours": 75, "progress": 100},
            {"name": "تصميم قاعدة البيانات", "description": "تصميم مخطط قاعدة البيانات وجداول النظام", "status": "completed", "priority": "high", "start_date": "2026-02-01", "end_date": "2026-02-15", "estimated_hours": 60, "actual_hours": 55, "progress": 100},
            {"name": "تطوير الواجهة الأمامية", "description": "برمجة واجهات المستخدم React", "status": "in_progress", "priority": "high", "start_date": "2026-02-15", "end_date": "2026-04-01", "estimated_hours": 200, "actual_hours": 80, "progress": 40},
            {"name": "تطوير الخادم الخلفي", "description": "برمجة API باستخدام FastAPI", "status": "in_progress", "priority": "high", "start_date": "2026-02-15", "end_date": "2026-04-01", "estimated_hours": 250, "actual_hours": 100, "progress": 35},
            {"name": "الاختبار والتسليم", "description": "اختبار شامل وتسليم المشروع", "status": "not_started", "priority": "medium", "start_date": "2026-05-01", "end_date": "2026-06-30", "estimated_hours": 120},
        ]
        for t in tasks:
            ok, res = api("POST", f"/projects/{proj_ids[0]}/tasks", t)
            if ok:
                print(f"  ✅ Task: {t['name']}")
            else:
                print(f"  ❌ Task {t['name']}: {res}")

        # Project expense
        expense = {
            "description": "تراخيص برمجيات وأدوات تطوير",
            "amount": 12000,
            "expense_date": "2026-02-10",
            "category": "software",
            "account_id": 69  # مصروفات عمومية
        }
        ok, res = api("POST", f"/projects/{proj_ids[0]}/expenses", expense)
        if ok:
            print(f"  ✅ Project expense: {expense['amount']} SAR")
        else:
            print(f"  ⚠️ Project expense: {res}")

        # Project revenue
        revenue = {
            "description": "دفعة أولى - مرحلة التحليل",
            "amount": 30000,
            "revenue_date": "2026-02-15",
            "category": "milestone",
            "account_id": 48  # مبيعات
        }
        ok, res = api("POST", f"/projects/{proj_ids[0]}/revenues", revenue)
        if ok:
            print(f"  ✅ Project revenue: {revenue['amount']} SAR")
        else:
            print(f"  ⚠️ Project revenue: {res}")

    # Timesheet for project 2
    if proj_ids[1]:
        timesheets = [
            {"employee_id": 1, "date": "2026-02-15", "hours": 8, "description": "تركيب كابلات الشبكة", "task_id": None},
            {"employee_id": 3, "date": "2026-02-16", "hours": 6, "description": "إعداد السيرفرات", "task_id": None},
            {"employee_id": 1, "date": "2026-02-17", "hours": 7, "description": "تركيب نقاط الوصول اللاسلكي", "task_id": None},
        ]
        for ts in timesheets:
            ok, res = api("POST", f"/projects/{proj_ids[1]}/timesheets", ts)
            if ok:
                print(f"  ✅ Timesheet: {ts['date']} ({ts['hours']}h)")
            else:
                print(f"  ⚠️ Timesheet: {res}")


# ================================================================
# PHASE 3: SERVICES & MAINTENANCE
# ================================================================
def do_services():
    requests_data = [
        {
            "title": "صيانة تكييف المكتب الرئيسي",
            "description": "التكييف المركزي لا يعمل بشكل صحيح - يحتاج فحص وصيانة",
            "category": "maintenance",
            "priority": "high",
            "customer_id": 5,
            "estimated_hours": 4,
            "estimated_cost": 2500,
            "scheduled_date": "2026-02-25",
            "location": "المقر الرئيسي - الرياض"
        },
        {
            "title": "تركيب طابعات - فرع جدة",
            "description": "تركيب 3 طابعات شبكية جديدة في فرع جدة",
            "category": "installation",
            "priority": "medium",
            "customer_id": 6,
            "estimated_hours": 3,
            "estimated_cost": 1500,
            "scheduled_date": "2026-02-28",
            "location": "فرع جدة"
        },
        {
            "title": "فحص دوري للسيرفرات",
            "description": "فحص وصيانة دورية لأربع سيرفرات في مركز البيانات",
            "category": "inspection",
            "priority": "low",
            "customer_id": 7,
            "estimated_hours": 6,
            "estimated_cost": 3000,
            "scheduled_date": "2026-03-01",
            "location": "مركز البيانات - دبي"
        },
        {
            "title": "إصلاح شاشة عرض مكسورة",
            "description": "شاشة عرض في قاعة الاجتماعات معطلة وتحتاج استبدال",
            "category": "repair",
            "priority": "medium",
            "customer_id": 5,
            "asset_id": 5,
            "estimated_hours": 2,
            "estimated_cost": 800,
            "scheduled_date": "2026-02-26",
            "location": "المقر الرئيسي - قاعة الاجتماعات"
        }
    ]
    
    for req in requests_data:
        ok, res = api("POST", "/services/requests", req)
        if ok:
            req_id = res.get("id")
            print(f"  ✅ Service Request: {req['title']} (ID: {req_id})")
        else:
            print(f"  ❌ Service Request {req['title']}: {res}")


# ================================================================
# PHASE 4: SALES RETURNS
# ================================================================
def do_sales_returns():
    # Return from invoice INV-2026-00001 (مبيعات لشركة الأفق, 28750 SAR)
    return_data = {
        "party_id": 5,  # شركة الأفق
        "invoice_id": 12,  # INV-2026-00001
        "return_date": "2026-02-22",
        "currency": "SAR",
        "exchange_rate": 1,
        "notes": "إرجاع بسبب عيب في المنتج",
        "items": [
            {"product_id": 1, "quantity": 2, "unit_price": 4500, "warehouse_id": 2, "reason": "عيب تصنيعي"}
        ]
    }
    ok, res = api("POST", "/sales/returns", return_data)
    return_id = None
    if ok:
        return_id = res.get("id", res.get("return_id"))
        print(f"  ✅ Sales Return created (ID: {return_id})")
    else:
        print(f"  ❌ Sales Return: {res}")

    # Approve the return
    if return_id:
        ok, res = api("POST", f"/sales/returns/{return_id}/approve", {"refund_method": "credit"})
        if ok:
            print(f"  ✅ Sales Return approved")
        else:
            print(f"  ⚠️ Approve return: {res}")

    # Another return - from AED invoice
    return_data2 = {
        "party_id": 7,  # Gulf Services
        "invoice_id": 14,  # INV-2026-00003 (AED)
        "return_date": "2026-02-23",
        "currency": "AED",
        "exchange_rate": 1.02,
        "notes": "إرجاع جزئي - كمية زائدة",
        "items": [
            {"product_id": 2, "quantity": 1, "unit_price": 950, "warehouse_id": 4, "reason": "كمية زائدة عن الطلب"}
        ]
    }
    ok, res = api("POST", "/sales/returns", return_data2)
    return_id2 = None
    if ok:
        return_id2 = res.get("id", res.get("return_id"))
        print(f"  ✅ Sales Return 2 created (ID: {return_id2})")
    else:
        print(f"  ❌ Sales Return 2: {res}")

    if return_id2:
        ok, res = api("POST", f"/sales/returns/{return_id2}/approve", {"refund_method": "credit"})
        if ok:
            print(f"  ✅ Sales Return 2 approved")
        else:
            print(f"  ⚠️ Approve return 2: {res}")


# ================================================================
# PHASE 5: SALES CREDIT NOTES
# ================================================================
def do_credit_notes():
    cn_data = {
        "party_id": 9,  # Deutsche Handel
        "invoice_id": 16,  # INV-2026-00005 (EUR)
        "credit_note_date": "2026-02-23",
        "currency": "EUR",
        "exchange_rate": 4.10,
        "reason": "خصم تجاري مُتفق عليه",
        "items": [
            {"product_id": 1, "quantity": 1, "unit_price": 200, "description": "خصم على الكمية"}
        ]
    }
    ok, res = api("POST", "/sales/credit-notes", cn_data)
    if ok:
        print(f"  ✅ Credit Note created (ID: {res.get('id')})")
    else:
        print(f"  ⚠️ Credit Note: {res}")


# ================================================================
# PHASE 6: PAYROLL
# ================================================================
def do_payroll():
    # Find payroll period
    ok, res = api("GET", "/hr/payroll-periods")
    if ok and isinstance(res, list) and len(res) > 0:
        period_id = res[0].get("id") if isinstance(res[0], dict) else None
        print(f"  Found payroll period ID: {period_id}")
        if period_id:
            # Generate payroll
            ok2, res2 = api("POST", f"/hr/payroll-periods/{period_id}/generate", {})
            if ok2:
                print(f"  ✅ Payroll generated")
            else:
                print(f"  ⚠️ Generate payroll: {res2}")

            # Post payroll
            ok3, res3 = api("POST", f"/hr/payroll-periods/{period_id}/post", {})
            if ok3:
                print(f"  ✅ Payroll posted")
            else:
                print(f"  ⚠️ Post payroll: {res3}")
    else:
        print(f"  ⚠️ No payroll periods found: {res}")
        # Create a new one
        pp_data = {
            "name": "رواتب فبراير 2026",
            "period_start": "2026-02-01",
            "period_end": "2026-02-28",
            "payment_date": "2026-02-28"
        }
        ok, res = api("POST", "/hr/payroll-periods", pp_data)
        if ok:
            pid = res.get("id")
            print(f"  ✅ Payroll period created (ID: {pid})")
            if pid:
                ok2, res2 = api("POST", f"/hr/payroll-periods/{pid}/generate", {})
                if ok2:
                    print(f"  ✅ Payroll generated")
                ok3, res3 = api("POST", f"/hr/payroll-periods/{pid}/post", {})
                if ok3:
                    print(f"  ✅ Payroll posted")
        else:
            print(f"  ❌ Create payroll period: {res}")


# ================================================================
# PHASE 7: CRM - Sales Opportunities
# ================================================================
def do_crm():
    # Check what columns sales_opportunities has
    opportunities = [
        {
            "name": "فرصة توريد أجهزة - شركة النور",
            "customer_id": 5,
            "stage": "proposal",
            "probability": 70,
            "expected_value": 85000,
            "expected_close_date": "2026-04-15",
            "currency": "SAR",
            "notes": "طلب عرض سعر لتوريد 20 جهاز لابتوب و10 شاشات",
            "source": "referral"
        },
        {
            "name": "عقد صيانة سنوي - American Import",
            "customer_id": 8,
            "stage": "negotiation",
            "probability": 50,
            "expected_value": 15000,
            "expected_close_date": "2026-03-30",
            "currency": "USD",
            "notes": "مفاوضات على عقد صيانة سنوي",
            "source": "direct"
        },
        {
            "name": "مشروع تجهيز مكاتب - مؤسسة النجاح",
            "customer_id": 6,
            "stage": "qualified",
            "probability": 40,
            "expected_value": 120000,
            "expected_close_date": "2026-05-01",
            "currency": "SAR",
            "notes": "تجهيز مكاتب جديدة بالكامل - أثاث وأجهزة",
            "source": "website"
        }
    ]

    # Try via direct DB insert since there may not be a dedicated CRM API
    import psycopg2
    conn = psycopg2.connect(host='localhost', dbname='aman_39a597c9', user='aman', password='YourPassword123!@#')
    cur = conn.cursor()
    
    # Check columns
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='sales_opportunities' ORDER BY ordinal_position")
    cols = [r[0] for r in cur.fetchall()]
    print(f"  sales_opportunities columns: {cols}")
    
    for opp in opportunities:
        try:
            cur.execute("""
                INSERT INTO sales_opportunities (name, customer_id, stage, probability, expected_value, 
                    expected_close_date, currency, notes, source, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING id
            """, (opp["name"], opp["customer_id"], opp["stage"], opp["probability"],
                  opp["expected_value"], opp["expected_close_date"], opp["currency"],
                  opp["notes"], opp["source"]))
            oid = cur.fetchone()[0]
            print(f"  ✅ Opportunity: {opp['name']} (ID: {oid})")
        except Exception as e:
            conn.rollback()
            print(f"  ❌ Opportunity {opp['name']}: {e}")
    
    conn.commit()
    conn.close()


# ================================================================
# PHASE 8: SUPPORT TICKETS
# ================================================================
def do_support_tickets():
    import psycopg2
    conn = psycopg2.connect(host='localhost', dbname='aman_39a597c9', user='aman', password='YourPassword123!@#')
    cur = conn.cursor()
    
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='support_tickets' ORDER BY ordinal_position")
    cols = [r[0] for r in cur.fetchall()]
    print(f"  support_tickets columns: {cols}")
    
    tickets = [
        {"title": "مشكلة في الطباعة", "description": "طابعة HP في الطابق الثاني لا تعمل", "priority": "high", "status": "open", "customer_id": 5, "category": "hardware"},
        {"title": "طلب تحديث نظام Windows", "description": "تحديث نظام التشغيل لـ 15 جهاز", "priority": "medium", "status": "in_progress", "customer_id": 6, "category": "software"},
        {"title": "إعداد بريد إلكتروني جديد", "description": "إنشاء حسابات بريد لـ 5 موظفين جدد", "priority": "low", "status": "resolved", "customer_id": 7, "category": "email"},
    ]
    
    for ticket in tickets:
        try:
            # Try flexible insert based on actual columns
            insert_cols = []
            insert_vals = []
            insert_params = []
            for k, v in ticket.items():
                if k in cols:
                    insert_cols.append(k)
                    insert_vals.append("%s")
                    insert_params.append(v)
            
            if insert_cols:
                insert_cols.append("created_at")
                insert_vals.append("CURRENT_TIMESTAMP")
                sql = f"INSERT INTO support_tickets ({', '.join(insert_cols)}) VALUES ({', '.join(insert_vals)}) RETURNING id"
                cur.execute(sql, insert_params)
                tid = cur.fetchone()[0]
                print(f"  ✅ Ticket: {ticket['title']} (ID: {tid})")
            else:
                print(f"  ⚠️ No matching columns for ticket")
        except Exception as e:
            conn.rollback()
            print(f"  ❌ Ticket {ticket['title']}: {e}")
    
    conn.commit()
    conn.close()


# ================================================================
# PHASE 9: SALES ORDERS
# ================================================================
def do_sales_orders():
    orders = [
        {
            "customer_id": 5,
            "order_date": "2026-02-10",
            "expected_date": "2026-02-20",
            "currency": "SAR",
            "exchange_rate": 1,
            "branch_id": 1,
            "notes": "طلب بيع عاجل",
            "items": [
                {"product_id": 1, "quantity": 5, "unit_price": 4500, "tax_rate": 15, "warehouse_id": 2},
                {"product_id": 5, "quantity": 3, "unit_price": 700, "tax_rate": 15, "warehouse_id": 2}
            ]
        },
        {
            "customer_id": 8,
            "order_date": "2026-02-12",
            "expected_date": "2026-03-01",
            "currency": "USD",
            "exchange_rate": 3.75,
            "branch_id": 1,
            "notes": "أمر تصدير للسوق الأمريكي",
            "items": [
                {"product_id": 1, "quantity": 10, "unit_price": 1200, "tax_rate": 0, "warehouse_id": 2},
                {"product_id": 2, "quantity": 5, "unit_price": 250, "tax_rate": 0, "warehouse_id": 3}
            ]
        }
    ]
    
    for so in orders:
        ok, res = api("POST", "/sales/orders", so)
        if ok:
            soid = res.get("id", res.get("order", {}).get("id"))
            print(f"  ✅ Sales Order (ID: {soid})")
        else:
            print(f"  ❌ Sales Order: {res}")


# ================================================================
# PHASE 10: SALES QUOTATIONS
# ================================================================
def do_quotations():
    quotes = [
        {
            "customer_id": 9,
            "quotation_date": "2026-02-18",
            "valid_until": "2026-03-18",
            "currency": "EUR",
            "exchange_rate": 4.10,
            "branch_id": 1,
            "notes": "عرض سعر للعميل الألماني",
            "items": [
                {"product_id": 1, "quantity": 20, "unit_price": 1100, "tax_rate": 0},
                {"product_id": 5, "quantity": 10, "unit_price": 170, "tax_rate": 0}
            ]
        }
    ]
    
    for q in quotes:
        ok, res = api("POST", "/sales/quotations", q)
        if ok:
            qid = res.get("id")
            print(f"  ✅ Sales Quotation (ID: {qid})")
        else:
            print(f"  ❌ Quotation: {res}")


# ================================================================
# PHASE 11: APPROVAL WORKFLOWS
# ================================================================
def do_approvals():
    workflows = [
        {
            "name": "اعتماد أوامر الشراء الكبيرة",
            "document_type": "purchase_order",
            "description": "مسار اعتماد لأوامر الشراء التي تزيد عن 50,000 ريال",
            "min_amount": 50000,
            "is_active": True,
            "steps": [
                {"step": 1, "approver_role": "superuser", "label": "مدير المشتريات"},
                {"step": 2, "approver_role": "superuser", "label": "المدير المالي"}
            ]
        },
        {
            "name": "اعتماد فواتير المبيعات",
            "document_type": "sales_invoice",
            "description": "مسار اعتماد لفواتير المبيعات",
            "min_amount": 10000,
            "is_active": True,
            "steps": [
                {"step": 1, "approver_role": "superuser", "label": "مدير المبيعات"}
            ]
        }
    ]
    
    for wf in workflows:
        ok, res = api("POST", "/approvals/workflows", wf)
        if ok:
            print(f"  ✅ Workflow: {wf['name']}")
        else:
            print(f"  ❌ Workflow {wf['name']}: {res}")


# ================================================================
# PHASE 12: BUDGETS
# ================================================================
def do_budgets():
    budget = {
        "name": "ميزانية 2026 - الفرع الرئيسي",
        "fiscal_year_id": 1,
        "branch_id": 1,
        "budget_type": "annual",
        "status": "approved",
        "notes": "الميزانية السنوية للفرع الرئيسي",
        "lines": [
            {"account_id": 62, "month_1": 15000, "month_2": 15000, "month_3": 15000, "month_4": 15000, "month_5": 15000, "month_6": 15000, "month_7": 15000, "month_8": 15000, "month_9": 15000, "month_10": 15000, "month_11": 15000, "month_12": 15000},
            {"account_id": 63, "month_1": 5000, "month_2": 5000, "month_3": 5000, "month_4": 5000, "month_5": 5000, "month_6": 5000, "month_7": 5000, "month_8": 5000, "month_9": 5000, "month_10": 5000, "month_11": 5000, "month_12": 5000},
            {"account_id": 48, "month_1": 50000, "month_2": 50000, "month_3": 50000, "month_4": 50000, "month_5": 50000, "month_6": 50000, "month_7": 50000, "month_8": 50000, "month_9": 50000, "month_10": 50000, "month_11": 50000, "month_12": 50000}
        ]
    }
    ok, res = api("POST", "/budgets/", budget)
    if ok:
        print(f"  ✅ Budget created (ID: {res.get('id')})")
    else:
        print(f"  ❌ Budget: {res}")


# ================================================================
# PHASE 13: COST CENTERS 
# ================================================================
def do_cost_centers():
    centers = [
        {"name": "الإدارة العامة", "name_en": "General Admin", "code": "CC-001"},
        {"name": "قسم المبيعات", "name_en": "Sales Dept", "code": "CC-002"},
        {"name": "قسم الإنتاج", "name_en": "Production Dept", "code": "CC-003"},
        {"name": "قسم تقنية المعلومات", "name_en": "IT Dept", "code": "CC-004"},
    ]
    for cc in centers:
        ok, res = api("POST", "/cost-centers/", cc)
        if ok:
            print(f"  ✅ Cost Center: {cc['name']}")
        else:
            print(f"  ❌ Cost Center {cc['name']}: {res}")


# ================================================================
# PHASE 14: STOCK ADJUSTMENTS & TRANSFERS
# ================================================================
def do_stock_operations():
    # Stock adjustment
    adj = {
        "product_id": 3,
        "warehouse_id": 2,
        "quantity": -10,
        "reason": "تالف - ورق مبلل",
        "adjustment_date": "2026-02-20"
    }
    ok, res = api("POST", "/inventory/adjustments", adj)
    if ok:
        print(f"  ✅ Stock Adjustment: Product 3, -10 units")
    else:
        print(f"  ⚠️ Stock Adjustment: {res}")

    # Stock transfer between warehouses
    transfer = {
        "product_id": 1,
        "from_warehouse_id": 2,
        "to_warehouse_id": 3,
        "quantity": 5,
        "notes": "نقل لابتوبات لفرع جدة",
        "transfer_date": "2026-02-21"
    }
    ok, res = api("POST", "/inventory/transfers", transfer)
    if ok:
        print(f"  ✅ Stock Transfer: 5 laptops WH2→WH3")
    else:
        print(f"  ⚠️ Stock Transfer: {res}")


# ================================================================
# PHASE 15: CONTRACTS
# ================================================================
def do_contracts():
    contracts = [
        {
            "contract_number": "CON-2026-001",
            "name": "عقد توريد أجهزة سنوي",
            "contract_type": "sales",
            "party_id": 5,
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "total_amount": 500000,
            "currency": "SAR",
            "status": "active",
            "payment_terms": "net_30",
            "notes": "عقد توريد أجهزة حاسب سنوي لشركة الأفق",
            "branch_id": 1
        },
        {
            "contract_number": "CON-2026-002",
            "name": "عقد صيانة ربع سنوي",
            "contract_type": "service",
            "party_id": 7,
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "total_amount": 48000,
            "currency": "AED",
            "exchange_rate": 1.02,
            "status": "active",
            "payment_terms": "net_15",
            "notes": "عقد صيانة ربع سنوي لأجهزة Gulf Services",
            "branch_id": 3
        }
    ]
    
    for c in contracts:
        ok, res = api("POST", "/contracts/", c)
        if ok:
            print(f"  ✅ Contract: {c['name']}")
        else:
            print(f"  ❌ Contract {c['name']}: {res}")


# ================================================================
# PHASE 16: PURCHASE AGREEMENTS / RFQs
# ================================================================
def do_purchase_agreements():
    # Request for Quotation
    rfq = {
        "title": "طلب عرض أسعار - أجهزة حاسب",
        "rfq_date": "2026-02-15",
        "deadline": "2026-03-01",
        "status": "sent",
        "notes": "طلب عرض أسعار لتوريد 50 جهاز لابتوب",
        "items": [
            {"product_id": 1, "quantity": 50, "specifications": "Dell Latitude 5540 أو ما يعادله"},
            {"product_id": 5, "quantity": 50, "specifications": "Samsung 27 بوصة 4K"}
        ]
    }
    ok, res = api("POST", "/buying/rfq", rfq)
    if ok:
        print(f"  ✅ RFQ created")
    else:
        print(f"  ⚠️ RFQ: {res}")


# ================================================================
# RUN ALL PHASES
# ================================================================
if __name__ == "__main__":
    print("🚀 Starting comprehensive data entry for company 39a597c9\n")
    
    phase("1. Cost Centers", do_cost_centers)
    phase("2. Manufacturing", do_manufacturing)
    phase("3. Projects", do_projects)
    phase("4. Services & Maintenance", do_services)
    phase("5. Sales Returns", do_sales_returns)
    phase("6. Credit Notes", do_credit_notes)
    phase("7. Payroll", do_payroll)
    phase("8. CRM - Opportunities", do_crm)
    phase("9. Support Tickets", do_support_tickets)
    phase("10. Sales Orders", do_sales_orders)
    phase("11. Sales Quotations", do_quotations)
    phase("12. Approval Workflows", do_approvals)
    phase("13. Budgets", do_budgets)
    phase("14. Stock Operations", do_stock_operations)
    phase("15. Contracts", do_contracts)
    phase("16. Purchase Agreements", do_purchase_agreements)
    
    print("\n\n" + "="*60)
    print("📊 FINAL RESULTS")
    print("="*60)
    for name, status in results.items():
        print(f"  {status} {name}")
    
    success = sum(1 for v in results.values() if v == "✅")
    total = len(results)
    print(f"\n  {success}/{total} phases completed successfully")
