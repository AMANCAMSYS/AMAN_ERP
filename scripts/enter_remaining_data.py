#!/usr/bin/env python3
"""
Enter remaining test data for company 39a597c9
Base currency: SAR
Exchange rates: 1 USD = 3.75 SAR, 1 EUR = 4.10 SAR, 1 AED = 1.02 SAR
"""
import requests
import json
import sys
from datetime import date

TOKEN = open("/tmp/aman_token2.txt").read().strip()
BASE = "http://localhost:8000/api"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def api(method, path, data=None):
    url = f"{BASE}{path}"
    if method == "POST":
        r = requests.post(url, headers=HEADERS, json=data)
    elif method == "GET":
        r = requests.get(url, headers=HEADERS)
    else:
        r = requests.request(method, url, headers=HEADERS, json=data)
    return r

def ok(r, label):
    if r.status_code in (200, 201):
        print(f"  ✅ {label}: {r.json()}")
        return True
    else:
        print(f"  ❌ {label}: [{r.status_code}] {r.text[:300]}")
        return False

# ============================================================
# PHASE 4: SUPPLIER PAYMENTS
# ============================================================
print("\n" + "="*60)
print("PHASE 4: SUPPLIER PAYMENTS")
print("="*60)

# 4.1 Pay supplier 1 for PINV-1 (80,500 SAR) from bank 4 (SAR)
print("\n4.1 Pay supplier 1 - PINV-1 (80,500 SAR)")
r = api("POST", "/buying/payments", {
    "supplier_id": 1,
    "voucher_date": "2026-02-20",
    "amount": 80500.0,
    "payment_method": "bank",
    "treasury_account_id": 4,
    "reference": "PAY-SUP-001",
    "notes": "دفعة فاتورة مشتريات لابتوبات",
    "branch_id": 1,
    "currency": "SAR",
    "exchange_rate": 1.0,
    "allocations": [{"invoice_id": 1, "allocated_amount": 80500.0}]
})
ok(r, "Supplier 1 payment (SAR)")

# 4.2 Pay supplier 3 for PINV-3/id=9 (4,830 USD) from bank 5 (USD)
print("\n4.2 Pay supplier 3 - PINV-3 (4,830 USD)")
r = api("POST", "/buying/payments", {
    "supplier_id": 3,
    "voucher_date": "2026-02-22",
    "amount": 4830.0,
    "payment_method": "bank",
    "treasury_account_id": 5,
    "reference": "PAY-SUP-002",
    "notes": "Payment for monitors - USD",
    "branch_id": 1,
    "currency": "USD",
    "exchange_rate": 3.75,
    "allocations": [{"invoice_id": 9, "allocated_amount": 4830.0}]
})
ok(r, "Supplier 3 payment (USD)")

# 4.3 Partial pay supplier 4 for PINV-4/id=10 (2,000 of 4,025 EUR) from cash 1 (SAR equivalent)
print("\n4.3 Partial pay supplier 4 - PINV-4 (2,000 EUR)")
r = api("POST", "/buying/payments", {
    "supplier_id": 4,
    "voucher_date": "2026-02-25",
    "amount": 2000.0,
    "payment_method": "cash",
    "treasury_account_id": 1,
    "reference": "PAY-SUP-003",
    "notes": "Partial payment for printers - EUR",
    "branch_id": 2,
    "currency": "EUR",
    "exchange_rate": 4.10,
    "allocations": [{"invoice_id": 10, "allocated_amount": 2000.0}]
})
ok(r, "Supplier 4 partial payment (EUR)")

# ============================================================
# PHASE 5: SALES INVOICES
# ============================================================
print("\n" + "="*60)
print("PHASE 5: SALES INVOICES")
print("="*60)

sales_invoice_ids = {}

# 5.1 Customer 5 (SAR) - 5 laptops @ 5,000 SAR + 15% tax
print("\n5.1 Sales Invoice - Customer 5 (5 laptops, SAR)")
r = api("POST", "/sales/invoices", {
    "customer_id": 5,
    "invoice_date": "2026-02-15",
    "due_date": "2026-03-15",
    "items": [{
        "product_id": 1,
        "description": "لابتوب Dell Latitude 5540",
        "quantity": 5,
        "unit_price": 5000.0,
        "tax_rate": 15.0,
        "discount": 0.0
    }],
    "payment_method": "credit",
    "paid_amount": 0,
    "branch_id": 1,
    "warehouse_id": 2,
    "currency": "SAR",
    "exchange_rate": 1.0
})
if ok(r, "Sales Invoice 1 (SAR)"):
    sales_invoice_ids["sinv1"] = r.json().get("invoice_id") or r.json().get("id")

# 5.2 Customer 6 (SAR) - Paper + Toner
print("\n5.2 Sales Invoice - Customer 6 (paper+toner, SAR)")
r = api("POST", "/sales/invoices", {
    "customer_id": 6,
    "invoice_date": "2026-02-16",
    "due_date": "2026-03-16",
    "items": [
        {"product_id": 3, "description": "ورق طباعة A4", "quantity": 30, "unit_price": 25.0, "tax_rate": 15.0, "discount": 0.0},
        {"product_id": 4, "description": "حبر طابعة HP", "quantity": 10, "unit_price": 350.0, "tax_rate": 15.0, "discount": 0.0}
    ],
    "payment_method": "credit",
    "paid_amount": 0,
    "branch_id": 1,
    "warehouse_id": 2,
    "currency": "SAR",
    "exchange_rate": 1.0
})
if ok(r, "Sales Invoice 2 (SAR)"):
    sales_invoice_ids["sinv2"] = r.json().get("invoice_id") or r.json().get("id")

# 5.3 Customer 7 (AED) - 3 monitors @ 450 AED + 5% VAT (UAE rate)
print("\n5.3 Sales Invoice - Customer 7 (3 monitors, AED)")
r = api("POST", "/sales/invoices", {
    "customer_id": 7,
    "invoice_date": "2026-02-17",
    "due_date": "2026-03-17",
    "items": [{
        "product_id": 5,
        "description": "Samsung 27 inch Monitor",
        "quantity": 3,
        "unit_price": 450.0,
        "tax_rate": 5.0,
        "discount": 0.0
    }],
    "payment_method": "credit",
    "paid_amount": 0,
    "branch_id": 3,
    "warehouse_id": 4,
    "currency": "AED",
    "exchange_rate": 1.02
})
if ok(r, "Sales Invoice 3 (AED)"):
    sales_invoice_ids["sinv3"] = r.json().get("invoice_id") or r.json().get("id")

# 5.4 Customer 8 (USD) - 2 laptops @ 1,500 USD + 0% (export)
print("\n5.4 Sales Invoice - Customer 8 (2 laptops, USD)")
r = api("POST", "/sales/invoices", {
    "customer_id": 8,
    "invoice_date": "2026-02-18",
    "due_date": "2026-04-18",
    "items": [{
        "product_id": 1,
        "description": "Dell Latitude 5540 Laptop",
        "quantity": 2,
        "unit_price": 1500.0,
        "tax_rate": 0.0,
        "discount": 0.0
    }],
    "payment_method": "credit",
    "paid_amount": 0,
    "branch_id": 1,
    "warehouse_id": 2,
    "currency": "USD",
    "exchange_rate": 3.75
})
if ok(r, "Sales Invoice 4 (USD)"):
    sales_invoice_ids["sinv4"] = r.json().get("invoice_id") or r.json().get("id")

# 5.5 Customer 9 (EUR) - 3 printers @ 550 EUR + 19% (EU VAT)
print("\n5.5 Sales Invoice - Customer 9 (3 printers, EUR)")
r = api("POST", "/sales/invoices", {
    "customer_id": 9,
    "invoice_date": "2026-02-19",
    "due_date": "2026-04-19",
    "items": [{
        "product_id": 2,
        "description": "HP LaserJet Pro Printer",
        "quantity": 3,
        "unit_price": 550.0,
        "tax_rate": 15.0,
        "discount": 0.0
    }],
    "payment_method": "credit",
    "paid_amount": 0,
    "branch_id": 2,
    "warehouse_id": 3,
    "currency": "EUR",
    "exchange_rate": 4.10
})
if ok(r, "Sales Invoice 5 (EUR)"):
    sales_invoice_ids["sinv5"] = r.json().get("invoice_id") or r.json().get("id")

# 5.6 Customer 5 (SAR) - Service invoice
print("\n5.6 Sales Invoice - Customer 5 (service, SAR)")
r = api("POST", "/sales/invoices", {
    "customer_id": 5,
    "invoice_date": "2026-02-20",
    "due_date": "2026-03-20",
    "items": [{
        "product_id": 6,
        "description": "خدمة دعم فني - 10 ساعات",
        "quantity": 10,
        "unit_price": 500.0,
        "tax_rate": 15.0,
        "discount": 0.0
    }],
    "payment_method": "credit",
    "paid_amount": 0,
    "branch_id": 1,
    "currency": "SAR",
    "exchange_rate": 1.0
})
if ok(r, "Sales Invoice 6 (Service, SAR)"):
    sales_invoice_ids["sinv6"] = r.json().get("invoice_id") or r.json().get("id")

print(f"\n  Sales invoice IDs: {sales_invoice_ids}")

# ============================================================
# PHASE 6: CUSTOMER RECEIPTS
# ============================================================
print("\n" + "="*60)
print("PHASE 6: CUSTOMER RECEIPTS")
print("="*60)

# 6.1 Receipt from customer 5 for first invoice (28,750 SAR)
if "sinv1" in sales_invoice_ids and sales_invoice_ids["sinv1"]:
    print("\n6.1 Receipt from Customer 5 (28,750 SAR)")
    r = api("POST", "/sales/receipts", {
        "customer_id": 5,
        "voucher_date": "2026-03-01",
        "amount": 28750.0,
        "payment_method": "bank",
        "notes": "سداد فاتورة مبيعات لابتوبات",
        "branch_id": 1,
        "treasury_id": 4,
        "currency": "SAR",
        "exchange_rate": 1.0,
        "allocations": [{"invoice_id": sales_invoice_ids["sinv1"], "allocated_amount": 28750.0}]
    })
    ok(r, "Customer 5 receipt (SAR)")

# 6.2 Receipt from customer 8 (3,000 USD)
if "sinv4" in sales_invoice_ids and sales_invoice_ids["sinv4"]:
    print("\n6.2 Receipt from Customer 8 (3,000 USD)")
    r = api("POST", "/sales/receipts", {
        "customer_id": 8,
        "voucher_date": "2026-03-05",
        "amount": 3000.0,
        "payment_method": "bank",
        "notes": "Full payment for laptops - USD",
        "branch_id": 1,
        "treasury_id": 5,
        "currency": "USD",
        "exchange_rate": 3.75,
        "allocations": [{"invoice_id": sales_invoice_ids["sinv4"], "allocated_amount": 3000.0}]
    })
    ok(r, "Customer 8 receipt (USD)")

# 6.3 Partial receipt from customer 7 (500 AED of 1,417.50 AED)
if "sinv3" in sales_invoice_ids and sales_invoice_ids["sinv3"]:
    print("\n6.3 Partial receipt from Customer 7 (500 AED)")
    r = api("POST", "/sales/receipts", {
        "customer_id": 7,
        "voucher_date": "2026-03-10",
        "amount": 500.0,
        "payment_method": "cash",
        "notes": "Partial payment for monitors - AED",
        "branch_id": 3,
        "treasury_id": 3,
        "currency": "AED",
        "exchange_rate": 1.02,
        "allocations": [{"invoice_id": sales_invoice_ids["sinv3"], "allocated_amount": 500.0}]
    })
    ok(r, "Customer 7 partial receipt (AED)")

# 6.4 Receipt from customer 5 for service invoice
if "sinv6" in sales_invoice_ids and sales_invoice_ids["sinv6"]:
    print("\n6.4 Receipt from Customer 5 for service invoice (5,750 SAR)")
    r = api("POST", "/sales/receipts", {
        "customer_id": 5,
        "voucher_date": "2026-03-12",
        "amount": 5750.0,
        "payment_method": "cash",
        "notes": "سداد فاتورة خدمات دعم فني",
        "branch_id": 1,
        "treasury_id": 1,
        "currency": "SAR",
        "exchange_rate": 1.0,
        "allocations": [{"invoice_id": sales_invoice_ids["sinv6"], "allocated_amount": 5750.0}]
    })
    ok(r, "Customer 5 service receipt (SAR)")

# ============================================================
# PHASE 7: TREASURY TRANSFERS
# ============================================================
print("\n" + "="*60)
print("PHASE 7: TREASURY TRANSFERS")
print("="*60)

# 7.1 Transfer SAR cash to SAR bank: 10,000
print("\n7.1 Transfer 10,000 SAR from cash to bank")
r = api("POST", "/treasury/transactions/transfer", {
    "transaction_date": "2026-03-01",
    "transaction_type": "transfer",
    "amount": 10000.0,
    "treasury_id": 1,
    "target_treasury_id": 4,
    "description": "تحويل من الصندوق إلى البنك",
    "reference_number": "TRF-001",
    "branch_id": 1,
    "exchange_rate": 1.0
})
ok(r, "Transfer SAR cash→bank")

# 7.2 Transfer 5,000 AED between AED accounts
print("\n7.2 Transfer 5,000 AED from cash to bank")
r = api("POST", "/treasury/transactions/transfer", {
    "transaction_date": "2026-03-05",
    "transaction_type": "transfer",
    "amount": 5000.0,
    "treasury_id": 3,
    "target_treasury_id": 6,
    "description": "Transfer AED cash to bank",
    "reference_number": "TRF-002",
    "branch_id": 3,
    "exchange_rate": 1.0
})
ok(r, "Transfer AED cash→bank")

# ============================================================
# PHASE 8: EXPENSES
# ============================================================
print("\n" + "="*60)
print("PHASE 8: EXPENSES")
print("="*60)

# 8.1 Office Rent - 15,000 SAR
print("\n8.1 Office Rent (15,000 SAR)")
r = api("POST", "/expenses/", {
    "expense_date": "2026-02-28",
    "expense_type": "إيجار المكتب",
    "amount": 15000.0,
    "description": "إيجار مكتب الرياض - فبراير 2026",
    "category": "rent",
    "payment_method": "bank",
    "treasury_id": 4,
    "branch_id": 1,
    "requires_approval": False,
    "receipt_number": "RNT-2026-02",
    "vendor_name": "شركة العقارية"
})
ok(r, "Rent Expense")

# 8.2 Office Supplies - 2,500 SAR
print("\n8.2 Office Supplies (2,500 SAR)")
r = api("POST", "/expenses/", {
    "expense_date": "2026-02-15",
    "expense_type": "لوازم مكتبية",
    "amount": 2500.0,
    "description": "مستلزمات مكتبية متنوعة",
    "category": "supplies",
    "payment_method": "cash",
    "treasury_id": 1,
    "branch_id": 1,
    "requires_approval": False,
    "receipt_number": "EXP-2026-001"
})
ok(r, "Supplies Expense")

# 8.3 Travel Expense - 3,000 SAR
print("\n8.3 Travel Expense (3,000 SAR)")
r = api("POST", "/expenses/", {
    "expense_date": "2026-02-20",
    "expense_type": "سفر وتنقلات",
    "amount": 3000.0,
    "description": "تذاكر سفر - زيارة فرع دبي",
    "category": "travel",
    "payment_method": "bank",
    "treasury_id": 4,
    "branch_id": 1,
    "requires_approval": False,
    "receipt_number": "TRV-2026-001"
})
ok(r, "Travel Expense")

# 8.4 Internet & Phone - 1,200 SAR
print("\n8.4 Internet & Phone (1,200 SAR)")
r = api("POST", "/expenses/", {
    "expense_date": "2026-02-28",
    "expense_type": "اتصالات وإنترنت",
    "amount": 1200.0,
    "description": "فاتورة STC - فبراير",
    "category": "utilities",
    "payment_method": "bank",
    "treasury_id": 4,
    "branch_id": 1,
    "requires_approval": False,
    "receipt_number": "UTL-2026-02"
})
ok(r, "Utilities Expense")

# ============================================================
# PHASE 9: HR / EMPLOYEES / PAYROLL
# ============================================================
print("\n" + "="*60)
print("PHASE 9: HR / EMPLOYEES / PAYROLL")
print("="*60)

employee_ids = {}

# 9.1 Employee 1 - Ahmed (Accountant, Riyadh)
print("\n9.1 Create Employee - أحمد محمد (محاسب)")
r = api("POST", "/hr/employees", {
    "first_name": "أحمد",
    "last_name": "محمد",
    "first_name_en": "Ahmed",
    "last_name_en": "Mohammed",
    "email": "ahmed@company.sa",
    "phone": "0501234567",
    "position_title": "محاسب أول",
    "department_name": "المالية",
    "salary": 8000.0,
    "housing_allowance": 2000.0,
    "transport_allowance": 500.0,
    "other_allowances": 300.0,
    "hire_date": "2025-01-01",
    "branch_id": 1,
    "create_user": False,
    "create_ledger": False
})
if ok(r, "Employee Ahmed"):
    data = r.json()
    employee_ids["ahmed"] = data.get("employee_id") or data.get("id")

# 9.2 Employee 2 - Sara (Sales, Jeddah)
print("\n9.2 Create Employee - سارة أحمد (مبيعات)")
r = api("POST", "/hr/employees", {
    "first_name": "سارة",
    "last_name": "أحمد",
    "first_name_en": "Sara",
    "last_name_en": "Ahmed",
    "email": "sara@company.sa",
    "phone": "0509876543",
    "position_title": "مسؤولة مبيعات",
    "department_name": "المبيعات",
    "salary": 6000.0,
    "housing_allowance": 1500.0,
    "transport_allowance": 500.0,
    "other_allowances": 200.0,
    "hire_date": "2025-03-15",
    "branch_id": 2,
    "create_user": False,
    "create_ledger": False
})
if ok(r, "Employee Sara"):
    data = r.json()
    employee_ids["sara"] = data.get("employee_id") or data.get("id")

# 9.3 Employee 3 - Omar (IT, Dubai)
print("\n9.3 Create Employee - عمر خالد (تقنية)")
r = api("POST", "/hr/employees", {
    "first_name": "عمر",
    "last_name": "خالد",
    "first_name_en": "Omar",
    "last_name_en": "Khalid",
    "email": "omar@company.sa",
    "phone": "0551122334",
    "position_title": "مهندس تقنية معلومات",
    "department_name": "تقنية المعلومات",
    "salary": 10000.0,
    "housing_allowance": 2500.0,
    "transport_allowance": 800.0,
    "other_allowances": 500.0,
    "hire_date": "2024-06-01",
    "branch_id": 3,
    "create_user": False,
    "create_ledger": False
})
if ok(r, "Employee Omar"):
    data = r.json()
    employee_ids["omar"] = data.get("employee_id") or data.get("id")

print(f"\n  Employee IDs: {employee_ids}")

# 9.4 Create Payroll Period
print("\n9.4 Create Payroll Period - February 2026")
r = api("POST", "/hr/payroll-periods", {
    "name": "رواتب فبراير 2026",
    "start_date": "2026-02-01",
    "end_date": "2026-02-28",
    "payment_date": "2026-02-28"
})
payroll_period_id = None
if ok(r, "Payroll Period"):
    data = r.json()
    payroll_period_id = data.get("period_id") or data.get("id")

# 9.5 Generate Payroll
if payroll_period_id:
    print(f"\n9.5 Generate Payroll for period {payroll_period_id}")
    r = api("POST", f"/hr/payroll-periods/{payroll_period_id}/generate", {})
    ok(r, "Generate Payroll")
    
    # 9.6 Post Payroll
    print(f"\n9.6 Post Payroll for period {payroll_period_id}")
    r = api("POST", f"/hr/payroll-periods/{payroll_period_id}/post", {})
    ok(r, "Post Payroll")

# ============================================================
# PHASE 10: FIXED ASSETS
# ============================================================
print("\n" + "="*60)
print("PHASE 10: FIXED ASSETS")
print("="*60)

# 10.1 Office Furniture
print("\n10.1 Create Asset - أثاث مكتبي")
r = api("POST", "/assets/", {
    "name": "أثاث مكتبي - الرياض",
    "type": "أثاث ومفروشات",
    "purchase_date": "2026-01-15",
    "cost": 25000.0,
    "life_years": 5,
    "code": "AST-001",
    "residual_value": 2500.0,
    "branch_id": 1,
    "depreciation_method": "straight_line"
})
ok(r, "Asset: Office Furniture")

# 10.2 Company Vehicle
print("\n10.2 Create Asset - سيارة الشركة")
r = api("POST", "/assets/", {
    "name": "سيارة تويوتا كامري 2026",
    "type": "سيارات ووسائل نقل",
    "purchase_date": "2026-01-20",
    "cost": 120000.0,
    "life_years": 8,
    "code": "AST-002",
    "residual_value": 15000.0,
    "branch_id": 1,
    "depreciation_method": "straight_line"
})
ok(r, "Asset: Company Vehicle")

# 10.3 Server Equipment
print("\n10.3 Create Asset - خادم الشبكة")
r = api("POST", "/assets/", {
    "name": "خادم Dell PowerEdge",
    "type": "أجهزة حاسوب",
    "purchase_date": "2026-02-01",
    "cost": 35000.0,
    "life_years": 4,
    "code": "AST-003",
    "residual_value": 3000.0,
    "branch_id": 1,
    "depreciation_method": "straight_line"
})
ok(r, "Asset: Server")

# ============================================================
# PHASE 11: JOURNAL ENTRIES
# ============================================================
print("\n" + "="*60)
print("PHASE 11: MANUAL JOURNAL ENTRIES")
print("="*60)

# 11.1 Prepaid Insurance (12 months × 2,000 = 24,000 SAR)
print("\n11.1 Prepaid Insurance Entry")
r = api("POST", "/accounting/journal-entries", {
    "date": "2026-01-01",
    "description": "تأمين طبي مدفوع مقدماً - 12 شهر",
    "reference": "JE-PREP-001",
    "status": "posted",
    "currency": "SAR",
    "exchange_rate": 1.0,
    "branch_id": 1,
    "lines": [
        {"account_id": 17, "debit": 24000, "credit": 0, "description": "مصروفات مدفوعة مقدماً - تأمين"},
        {"account_id": 9, "debit": 0, "credit": 24000, "description": "البنك - دفع التأمين"}
    ]
})
ok(r, "Prepaid Insurance JE")

# 11.2 Insurance expense recognition - January portion (2,000 SAR)
print("\n11.2 Insurance Expense Recognition - Jan")
r = api("POST", "/accounting/journal-entries", {
    "date": "2026-01-31",
    "description": "استهلاك التأمين المدفوع مقدماً - يناير",
    "reference": "JE-INS-JAN",
    "status": "posted",
    "currency": "SAR",
    "exchange_rate": 1.0,
    "branch_id": 1,
    "lines": [
        {"account_id": 5, "debit": 2000, "credit": 0, "description": "مصروف تأمين - يناير"},
        {"account_id": 17, "debit": 0, "credit": 2000, "description": "تخفيض المدفوع مقدماً"}
    ]
})
ok(r, "Insurance Expense Jan JE")

# 11.3 Insurance expense recognition - February portion (2,000 SAR) 
print("\n11.3 Insurance Expense Recognition - Feb")
r = api("POST", "/accounting/journal-entries", {
    "date": "2026-02-28",
    "description": "استهلاك التأمين المدفوع مقدماً - فبراير",
    "reference": "JE-INS-FEB",
    "status": "posted",
    "currency": "SAR",
    "exchange_rate": 1.0,
    "branch_id": 1,
    "lines": [
        {"account_id": 5, "debit": 2000, "credit": 0, "description": "مصروف تأمين - فبراير"},
        {"account_id": 17, "debit": 0, "credit": 2000, "description": "تخفيض المدفوع مقدماً"}
    ]
})
ok(r, "Insurance Expense Feb JE")

# 11.4 Accrue salary for February (if payroll didn't post)
print("\n11.4 Accrued Salary Entry")
r = api("POST", "/accounting/journal-entries", {
    "date": "2026-02-28",
    "description": "رواتب مستحقة - فبراير 2026",
    "reference": "JE-SAL-FEB",
    "status": "posted",
    "currency": "SAR",
    "exchange_rate": 1.0,
    "branch_id": 1,
    "lines": [
        {"account_id": 5, "debit": 32300, "credit": 0, "description": "مصروف رواتب وبدلات"},
        {"account_id": 32, "debit": 0, "credit": 32300, "description": "مصاريف مستحقة - رواتب"}
    ]
})
ok(r, "Accrued Salary JE")

# 11.5 FX Revaluation: USD supplier balance at new rate (3.80 instead of 3.75)
# Supplier 3 owed 4,830 USD at 3.75 = 18,112.50 SAR. At 3.80 = 18,354 SAR. Loss = 241.50
# But we already paid supplier 3, skip if paid. Let's do AED revaluation instead.
# Supplier 1 AED balance: 108,045 AED at 1.02 = 110,205.90 SAR. At 1.03 = 111,286.35. Loss = 1,080.45
print("\n11.5 FX Revaluation Entry (AED rate change 1.02 → 1.03)")
r = api("POST", "/accounting/journal-entries", {
    "date": "2026-02-28",
    "description": "إعادة تقييم عملات أجنبية - الدرهم الإماراتي",
    "reference": "JE-FX-AED",
    "status": "posted",
    "currency": "SAR",
    "exchange_rate": 1.0,
    "branch_id": 1,
    "lines": [
        {"account_id": 5, "debit": 1080, "credit": 0, "description": "خسارة فروقات عملة - AED"},
        {"account_id": 31, "debit": 0, "credit": 1080, "description": "تعديل رصيد الموردين - فروقات العملة"}
    ]
})
ok(r, "FX Revaluation JE")

print("\n" + "="*60)
print("ALL PHASES COMPLETE!")
print("="*60)
print(f"\nSales Invoice IDs: {sales_invoice_ids}")
print(f"Employee IDs: {employee_ids}")
print(f"Payroll Period ID: {payroll_period_id}")
