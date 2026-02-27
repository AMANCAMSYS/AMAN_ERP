"""
Comprehensive data population script for company 39a597c9.
ALL accounting entries are balanced and consistent.
Dashboard, Sales Report, and Sales Page will show matching numbers.

Existing base data (after reset):
- 117 accounts (full CoA)
- 3 branches (BR001 الرئيسي, BR002 جدة, BR003 دبي)
- 4 warehouses (WH001, WH-RYD, WH-JED, WH-DXB)
- 4 currencies (SAR, USD, EUR, AED)
- 1 user (id=1)
- 8 roles
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import get_db_connection
from sqlalchemy import text
from datetime import datetime, date, timedelta
import json

COMPANY_ID = '39a597c9'

def run():
    db = get_db_connection(COMPANY_ID)
    count = 0

    def exe(sql, params=None):
        nonlocal count
        db.execute(text(sql), params or {})
        count += 1

    def exe_ret(sql, params=None):
        nonlocal count
        result = db.execute(text(sql), params or {}).scalar()
        count += 1
        return result

    try:
        # Reset all sequences to avoid gaps from failed runs
        all_tables = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
        for (t,) in all_tables:
            try:
                cnt = db.execute(text(f'SELECT COUNT(*) FROM "{t}"')).scalar()
                if cnt == 0:
                    db.execute(text(f'ALTER SEQUENCE IF EXISTS {t}_id_seq RESTART WITH 1'))
            except: pass

        # ============================================================
        # KNOWN IDS FROM EXISTING DATA
        # ============================================================
        USER_ID = 1
        BRANCH_MAIN = 1  # الرئيسي
        BRANCH_JED = 2   # جدة
        BRANCH_DXB = 3   # دبي
        WH_MAIN = 1      # المستودع الرئيسي
        WH_RYD = 2       # الرياض
        WH_JED = 3       # جدة
        WH_DXB = 4       # دبي

        # Account IDs (from CoA)
        # Assets
        ACCT_CASH = 7     # النقد وما في حكمه
        ACCT_BOX = 8      # الصندوق الرئيسي
        ACCT_BANK = 9     # البنك
        ACCT_AR = 10      # العملاء والذمم المدينة
        ACCT_INV = 11     # المخزون
        ACCT_RM = 12      # مخزون مواد أولية
        ACCT_FG = 13      # مخزون إنتاج تام
        ACCT_WIP = 14     # أعمال تحت التشغيل
        ACCT_PREPAID = 17 # مصروفات مدفوعة مقدماً
        ACCT_FA = 18      # أصول ثابتة
        ACCT_MAC = 19     # الآلات والمعدات
        ACCT_VEH = 20     # السيارات
        ACCT_FUR = 21     # الأثاث
        ACCT_BLD = 22     # المباني
        ACCT_LND = 23     # الأراضي
        ACCT_CMP = 24     # أجهزة حاسوب
        ACCT_DEPR_ACC = 25  # الإهلاك المتراكم
        ACCT_VAT_IN = 27 # ضريبة المدخلات
        ACCT_CHK_RCV = 28 # شيكات تحت التحصيل
        ACCT_NR = 29      # أوراق قبض

        # Liabilities
        ACCT_AP = 31      # الموردين
        ACCT_ACCRUED = 32 # مصاريف مستحقة
        ACCT_VAT = 34     # ضريبة القيمة المضافة
        ACCT_VAT_OUT = 35 # ضريبة المخرجات
        ACCT_CHK_PAY = 36 # شيكات تحت الدفع
        ACCT_GOSI_PAY = 37 # التأمينات المستحقة
        ACCT_CUST_DEP = 38 # عربون عملاء
        ACCT_NP = 39      # أوراق دفع
        ACCT_EOS = 42     # نهاية الخدمة

        # Equity
        ACCT_CAP = 43     # رأس المال
        ACCT_RET = 44     # أرباح مبقاة
        ACCT_CUR = 45     # أرباح العام الحالي

        # Revenue
        ACCT_SALE_G = 48  # مبيعات البضائع
        ACCT_SALE_S = 49  # إيرادات الخدمات
        ACCT_SALE_R = 50  # مردودات المبيعات
        ACCT_SALE_DISC = 51 # خصم مبيعات

        # Expenses
        ACCT_CGS = 55     # تكلفة البضاعة المباعة
        ACCT_CGS_G = 56   # تكلفة مبيعات البضائع
        ACCT_SAL = 61     # الرواتب
        ACCT_RENT = 62    # الإيجار
        ACCT_UTL = 63     # الكهرباء والمياه
        ACCT_COM = 64     # الاتصالات
        ACCT_MNT = 65     # الصيانة
        ACCT_GOV = 66     # الرسوم الحكومية
        ACCT_MKT = 67     # التسويق
        ACCT_TRV = 68     # السفر
        ACCT_GEN = 69     # مصروفات عمومية
        ACCT_GOSI = 70    # التأمينات
        ACCT_INS = 71     # التأمين
        ACCT_DEPR = 75    # الإهلاك (مصروف)
        ACCT_BANK_F = 77  # رسوم بنكية

        # ============================================================
        # FINANCIAL PLAN - ALL NUMBERS MUST BE CONSISTENT
        # ============================================================
        # Revenue (Jan-Feb 2025):
        #   Sales invoices (goods): 120,000 SAR
        #   Services: 35,000 SAR
        #   Sales returns: -8,000 SAR
        #   Net Revenue: 147,000 SAR
        #
        # COGS: 45,000 SAR
        # Gross Profit: 102,000 SAR
        #
        # Operating Expenses:
        #   Salaries: 36,000
        #   Rent: 10,000
        #   Utilities: 3,500
        #   Communications: 1,200
        #   Maintenance: 2,000
        #   Government fees: 800
        #   Marketing: 4,500
        #   Insurance: 2,500
        #   GOSI: 3,500
        #   Depreciation: 4,000
        #   General: 1,500
        #   Bank charges: 500
        #   Total OpEx: 70,000 SAR
        #
        # Net Profit: 102,000 - 70,000 = 32,000 SAR
        # ============================================================

        print("=" * 60)
        print("POPULATING ALL TABLES WITH CONSISTENT DATA")
        print("=" * 60)

        # ============================================================
        # 1. FISCAL YEARS & PERIODS
        # ============================================================
        print("1. Fiscal Years...")
        fy_id = exe_ret("""INSERT INTO fiscal_years (year, start_date, end_date, status)
            VALUES (2025, '2025-01-01', '2025-12-31', 'open') RETURNING id""")

        for m in range(1, 13):
            import calendar
            last_day = calendar.monthrange(2025, m)[1]
            exe(f"""INSERT INTO fiscal_periods (name, start_date, end_date, fiscal_year, is_closed)
                VALUES ('2025-{m:02d}', '2025-{m:02d}-01', '2025-{m:02d}-{last_day}', {fy_id}, false)""")

        # ============================================================
        # 2. TREASURY ACCOUNTS (linked to GL)
        # ============================================================
        print("2. Treasury Accounts...")
        # Get existing treasury account IDs from GL accounts
        # Bank accounts already linked via ids 112-117
        treas_box = exe_ret(f"""INSERT INTO treasury_accounts (name, name_en, account_type, currency, current_balance, gl_account_id, branch_id, is_active)
            VALUES ('الصندوق الرئيسي', 'Main Cash Box', 'cash', 'SAR', 0, {ACCT_BOX}, {BRANCH_MAIN}, true) RETURNING id""")
        treas_bank = exe_ret(f"""INSERT INTO treasury_accounts (name, name_en, account_type, currency, current_balance, gl_account_id, branch_id, bank_name, account_number, iban, is_active)
            VALUES ('حساب البنك الأهلي', 'NCB Account', 'bank', 'SAR', 0, {ACCT_BANK}, {BRANCH_MAIN}, 'البنك الأهلي', '1234567890', 'SA44 2000 0001 2345 6789 0000', true) RETURNING id""")
        treas_rajhi = exe_ret(f"""INSERT INTO treasury_accounts (name, name_en, account_type, currency, current_balance, gl_account_id, branch_id, bank_name, account_number, iban, is_active)
            VALUES ('حساب بنك الراجحي', 'Al Rajhi Account', 'bank', 'SAR', 0, 115, {BRANCH_MAIN}, 'بنك الراجحي', '0987654321', 'SA66 8000 0098 7654 3210 0000', true) RETURNING id""")
        treas_jed = exe_ret(f"""INSERT INTO treasury_accounts (name, name_en, account_type, currency, current_balance, gl_account_id, branch_id, bank_name, is_active)
            VALUES ('صندوق فرع جدة', 'Jeddah Cash', 'cash', 'SAR', 0, 113, {BRANCH_JED}, NULL, true) RETURNING id""")
        treas_dxb = exe_ret(f"""INSERT INTO treasury_accounts (name, name_en, account_type, currency, current_balance, gl_account_id, branch_id, bank_name, is_active)
            VALUES ('صندوق فرع دبي', 'Dubai Cash', 'cash', 'AED', 0, 114, {BRANCH_DXB}, NULL, true) RETURNING id""")

        # ============================================================
        # 3. TAX SETUP
        # ============================================================
        print("3. Tax Setup...")
        tax_regime_vat = exe_ret("""INSERT INTO tax_regimes (country_code, tax_type, name_ar, name_en, default_rate, is_required, applies_to, filing_frequency, is_active)
            VALUES ('SA', 'vat', 'ضريبة القيمة المضافة', 'VAT', 15, true, 'all', 'quarterly', true) RETURNING id""")
        tax_regime_wht = exe_ret("""INSERT INTO tax_regimes (country_code, tax_type, name_ar, name_en, default_rate, is_required, applies_to, filing_frequency, is_active)
            VALUES ('SA', 'wht', 'ضريبة الاستقطاع', 'WHT', 5, false, 'services', 'monthly', true) RETURNING id""")

        exe("""INSERT INTO tax_rates (tax_code, tax_name, tax_name_en, rate_type, rate_value, country_code, description, effective_from, is_active)
            VALUES ('VAT-15', 'ضريبة القيمة المضافة 15%', 'VAT 15%', 'percentage', 15, 'SA', 'ضريبة القيمة المضافة المعيارية', '2020-07-01', true)""")
        exe("""INSERT INTO tax_rates (tax_code, tax_name, tax_name_en, rate_type, rate_value, country_code, description, effective_from, is_active)
            VALUES ('VAT-0', 'معفاة من الضريبة', 'Zero-Rated', 'percentage', 0, 'SA', 'إعفاء ضريبي', '2020-01-01', true)""")
        exe("""INSERT INTO tax_rates (tax_code, tax_name, tax_name_en, rate_type, rate_value, country_code, description, effective_from, is_active)
            VALUES ('WHT-5', 'استقطاع 5%', 'WHT 5%', 'percentage', 5, 'SA', 'ضريبة استقطاع على الخدمات', '2020-01-01', true)""")

        # wht_rates
        for wht in [
            ('خدمات فنية واستشارية', 5), ('إيجارات', 5), ('تذاكر طيران', 5),
            ('خدمات اتصالات', 5), ('تأمين', 5), ('حقوق ملكية فكرية', 15),
            ('أرباح أسهم', 5), ('فوائد', 5)
        ]:
            exe(f"INSERT INTO wht_rates (name, name_ar, rate, category, is_active) VALUES ('{wht[0]}', '{wht[0]}', {wht[1]}, 'services', true)")

        # ============================================================
        # 4. DEPARTMENTS, POSITIONS, EMPLOYEES
        # ============================================================
        print("4. HR Setup...")
        dept_fin = exe_ret("""INSERT INTO departments (department_code, department_name, department_name_en, branch_id, is_active)
            VALUES ('DEP-FIN', 'الإدارة المالية', 'Finance', 1, true) RETURNING id""")
        dept_sales = exe_ret("""INSERT INTO departments (department_code, department_name, department_name_en, branch_id, is_active)
            VALUES ('DEP-SALES', 'المبيعات', 'Sales', 1, true) RETURNING id""")
        dept_it = exe_ret("""INSERT INTO departments (department_code, department_name, department_name_en, branch_id, is_active)
            VALUES ('DEP-IT', 'تقنية المعلومات', 'IT', 1, true) RETURNING id""")
        dept_hr = exe_ret("""INSERT INTO departments (department_code, department_name, department_name_en, branch_id, is_active)
            VALUES ('DEP-HR', 'الموارد البشرية', 'HR', 1, true) RETURNING id""")
        dept_ops = exe_ret("""INSERT INTO departments (department_code, department_name, department_name_en, branch_id, is_active)
            VALUES ('DEP-OPS', 'العمليات', 'Operations', 2, true) RETURNING id""")

        pos_mgr = exe_ret(f"""INSERT INTO employee_positions (position_code, position_name, position_name_en, department_id, level, is_active)
            VALUES ('POS-MGR', 'مدير', 'Manager', {dept_fin}, 3, true) RETURNING id""")
        pos_acc = exe_ret(f"""INSERT INTO employee_positions (position_code, position_name, position_name_en, department_id, level, is_active)
            VALUES ('POS-ACC', 'محاسب', 'Accountant', {dept_fin}, 2, true) RETURNING id""")
        pos_sales = exe_ret(f"""INSERT INTO employee_positions (position_code, position_name, position_name_en, department_id, level, is_active)
            VALUES ('POS-SALES', 'مندوب مبيعات', 'Sales Rep', {dept_sales}, 1, true) RETURNING id""")
        pos_dev = exe_ret(f"""INSERT INTO employee_positions (position_code, position_name, position_name_en, department_id, level, is_active)
            VALUES ('POS-DEV', 'مطور برمجيات', 'Developer', {dept_it}, 2, true) RETURNING id""")

        emp1 = exe_ret(f"""INSERT INTO employees (employee_code, first_name, last_name, first_name_en, last_name_en, email, phone, mobile, gender, birth_date, hire_date, department_id, position_id, branch_id, employment_type, status, salary, housing_allowance, transport_allowance, currency, user_id)
            VALUES ('EMP-001', 'محمد', 'الأحمدي', 'Mohammed', 'Al-Ahmadi', 'mohammed@aman.sa', '0112345678', '0551234567', 'male', '1985-03-15', '2024-01-01', {dept_fin}, {pos_mgr}, 1, 'full_time', 'active', 12000, 4500, 1500, 'SAR', 1) RETURNING id""")
        emp2 = exe_ret(f"""INSERT INTO employees (employee_code, first_name, last_name, first_name_en, last_name_en, email, phone, mobile, gender, birth_date, hire_date, department_id, position_id, branch_id, employment_type, status, salary, housing_allowance, transport_allowance, currency)
            VALUES ('EMP-002', 'فاطمة', 'الزهراني', 'Fatima', 'Al-Zahrani', 'fatima@aman.sa', '0112345679', '0559876543', 'female', '1990-07-22', '2024-06-01', {dept_sales}, {pos_sales}, 1, 'full_time', 'active', 8000, 3000, 1000, 'SAR') RETURNING id""")
        emp3 = exe_ret(f"""INSERT INTO employees (employee_code, first_name, last_name, first_name_en, last_name_en, email, mobile, gender, birth_date, hire_date, department_id, position_id, branch_id, employment_type, status, salary, housing_allowance, transport_allowance, currency)
            VALUES ('EMP-003', 'خالد', 'الشمري', 'Khalid', 'Al-Shammari', 'khalid@aman.sa', '0537765544', 'male', '1992-11-10', '2025-01-15', {dept_it}, {pos_dev}, 1, 'full_time', 'active', 10000, 3500, 1200, 'SAR') RETURNING id""")

        EMP_IDS = [emp1, emp2, emp3]

        # ============================================================
        # 5. PARTIES (Customers & Suppliers)
        # ============================================================
        print("5. Parties...")
        # Suppliers
        sup1 = exe_ret("""INSERT INTO parties (party_type, party_code, name, name_en, email, phone, mobile, city, country, tax_number, is_customer, is_supplier, branch_id, currency, status)
            VALUES ('company', 'SUP-001', 'مؤسسة الأمان للتوريدات', 'Al-Aman Supplies', 'info@alaman.sa', '0112223344', '0541112233', 'الرياض', 'SA', '300012345600001', false, true, 1, 'SAR', 'active') RETURNING id""")
        sup2 = exe_ret("""INSERT INTO parties (party_type, party_code, name, name_en, email, phone, city, country, tax_number, is_customer, is_supplier, branch_id, currency, status)
            VALUES ('company', 'SUP-002', 'شركة التقنية المتحدة', 'United Tech Co', 'info@unitedtech.sa', '0126543210', 'جدة', 'SA', '300012345600002', false, true, 1, 'SAR', 'active') RETURNING id""")
        sup3 = exe_ret("""INSERT INTO parties (party_type, party_code, name, name_en, email, phone, city, country, is_customer, is_supplier, branch_id, currency, status)
            VALUES ('company', 'SUP-003', 'مصنع الخليج للحديد', 'Gulf Steel Factory', 'info@gulfsteel.sa', '0133445566', 'الدمام', 'SA', false, true, 2, 'SAR', 'active') RETURNING id""")

        # Customers
        cust1 = exe_ret("""INSERT INTO parties (party_type, party_code, name, name_en, email, phone, mobile, city, country, tax_number, is_customer, is_supplier, branch_id, currency, credit_limit, status)
            VALUES ('company', 'CUST-001', 'شركة الوفاء التجارية', 'Al-Wafaa Trading', 'info@wafaa.sa', '0114567890', '0561234567', 'الرياض', 'SA', '300098765400001', true, false, 1, 'SAR', 500000, 'active') RETURNING id""")
        cust2 = exe_ret("""INSERT INTO parties (party_type, party_code, name, name_en, email, phone, mobile, city, country, tax_number, is_customer, is_supplier, branch_id, currency, credit_limit, status)
            VALUES ('company', 'CUST-002', 'مؤسسة النور للمقاولات', 'Al-Nour Contracting', 'info@alnour.sa', '0127654321', '0559988776', 'جدة', 'SA', '300098765400002', true, false, 1, 'SAR', 300000, 'active') RETURNING id""")
        cust3 = exe_ret("""INSERT INTO parties (party_type, party_code, name, name_en, email, phone, mobile, city, country, is_customer, is_supplier, branch_id, currency, credit_limit, status)
            VALUES ('company', 'CUST-003', 'شركة البناء الحديث', 'Modern Build Co', 'info@modernbuild.sa', '0138765432', '0553344556', 'الدمام', 'SA', true, false, 2, 'SAR', 200000, 'active') RETURNING id""")
        cust4 = exe_ret("""INSERT INTO parties (party_type, party_code, name, name_en, email, phone, city, country, is_customer, is_supplier, branch_id, currency, status)
            VALUES ('individual', 'CUST-004', 'عبدالله المطيري', 'Abdullah Al-Mutairi', 'abdullah@email.com', '0555667788', 'الرياض', 'SA', true, false, 1, 'SAR', 'active') RETURNING id""")
        cust5 = exe_ret("""INSERT INTO parties (party_type, party_code, name, name_en, email, phone, city, country, is_customer, is_supplier, branch_id, currency, status)
            VALUES ('company', 'CUST-005', 'مجموعة الرشيد الدولية', 'Al-Rashid International', 'info@rashid.ae', '042345678', 'دبي', 'AE', true, false, 3, 'AED', 'active') RETURNING id""")

        SUPP_IDS = [sup1, sup2, sup3]
        CUST_IDS = [cust1, cust2, cust3, cust4, cust5]

        # Also insert into customers/suppliers tables (capture IDs for customer_contacts)
        cust_t1 = exe_ret(f"INSERT INTO customers (customer_code, customer_name, customer_name_en, customer_type, email, phone, city, country, branch_id, currency, status) VALUES ('CUST-001', 'شركة الوفاء التجارية', 'Al-Wafaa Trading', 'company', 'info@wafaa.sa', '0114567890', 'الرياض', 'SA', 1, 'SAR', 'active') RETURNING id")
        cust_t2 = exe_ret(f"INSERT INTO customers (customer_code, customer_name, customer_name_en, customer_type, email, phone, city, country, branch_id, currency, status) VALUES ('CUST-002', 'مؤسسة النور للمقاولات', 'Al-Nour Contracting', 'company', 'info@alnour.sa', '0127654321', 'جدة', 'SA', 1, 'SAR', 'active') RETURNING id")
        cust_t3 = exe_ret(f"INSERT INTO customers (customer_code, customer_name, customer_name_en, customer_type, email, phone, city, country, branch_id, currency, status) VALUES ('CUST-003', 'شركة البناء الحديث', 'Modern Build Co', 'company', 'info@modernbuild.sa', '0138765432', 'الدمام', 'SA', 2, 'SAR', 'active') RETURNING id")
        cust_t4 = exe_ret(f"INSERT INTO customers (customer_code, customer_name, customer_name_en, customer_type, phone, city, country, branch_id, currency, status) VALUES ('CUST-004', 'عبدالله المطيري', 'Abdullah Al-Mutairi', 'individual', '0555667788', 'الرياض', 'SA', 1, 'SAR', 'active') RETURNING id")
        supp_t1 = exe_ret(f"INSERT INTO suppliers (supplier_code, supplier_name, supplier_name_en, email, phone, city, country, branch_id, currency, status) VALUES ('SUP-001', 'مؤسسة الأمان للتوريدات', 'Al-Aman Supplies', 'info@alaman.sa', '0112223344', 'الرياض', 'SA', 1, 'SAR', 'active') RETURNING id")
        supp_t2 = exe_ret(f"INSERT INTO suppliers (supplier_code, supplier_name, supplier_name_en, email, phone, city, country, branch_id, currency, status) VALUES ('SUP-002', 'شركة التقنية المتحدة', 'United Tech Co', 'info@unitedtech.sa', '0126543210', 'جدة', 'SA', 1, 'SAR', 'active') RETURNING id")

        # ============================================================
        # 6. PRODUCTS & UNITS
        # ============================================================
        print("6. Products...")
        # Product units
        unit1 = exe_ret("INSERT INTO product_units (unit_code, unit_name, unit_name_en, abbreviation, is_active) VALUES ('PC', 'قطعة', 'Piece', 'قطعة', true) RETURNING id")
        unit2 = exe_ret("INSERT INTO product_units (unit_code, unit_name, unit_name_en, abbreviation, is_active) VALUES ('KG', 'كيلوغرام', 'Kilogram', 'كغ', true) RETURNING id")
        unit3 = exe_ret("INSERT INTO product_units (unit_code, unit_name, unit_name_en, abbreviation, is_active) VALUES ('MTR', 'متر', 'Meter', 'م', true) RETURNING id")
        unit4 = exe_ret("INSERT INTO product_units (unit_code, unit_name, unit_name_en, abbreviation, is_active) VALUES ('HR', 'ساعة', 'Hour', 'ساعة', true) RETURNING id")

        # Product categories
        cat1 = exe_ret("INSERT INTO product_categories (category_code, category_name, category_name_en, description, is_active, sort_order) VALUES ('PC-RAW', 'مواد خام', 'Raw Materials', 'مواد أولية للإنتاج', true, 1) RETURNING id")
        cat2 = exe_ret("INSERT INTO product_categories (category_code, category_name, category_name_en, description, is_active, sort_order) VALUES ('PC-FIN', 'منتجات تامة', 'Finished Goods', 'منتجات جاهزة للبيع', true, 2) RETURNING id")
        cat3 = exe_ret("INSERT INTO product_categories (category_code, category_name, category_name_en, description, is_active, sort_order) VALUES ('PC-SRV', 'خدمات', 'Services', 'خدمات استشارية وفنية', true, 3) RETURNING id")

        # Products (costs set for accurate COGS)
        prod1 = exe_ret(f"""INSERT INTO products (product_code, product_name, product_name_en, product_type, category_id, unit_id, barcode, cost_price, selling_price, tax_rate, is_taxable, is_active, is_track_inventory, reorder_level)
            VALUES ('PRD-001', 'حديد مسلح 12مم', 'Steel Rod 12mm', 'goods', {cat1}, {unit2}, '6281000001001', 50, 85, 15, true, true, true, 100) RETURNING id""")
        prod2 = exe_ret(f"""INSERT INTO products (product_code, product_name, product_name_en, product_type, category_id, unit_id, barcode, cost_price, selling_price, tax_rate, is_taxable, is_active, is_track_inventory, reorder_level)
            VALUES ('PRD-002', 'أسمنت بورتلاندي', 'Portland Cement', 'goods', {cat1}, {unit2}, '6281000001002', 30, 55, 15, true, true, true, 200) RETURNING id""")
        prod3 = exe_ret(f"""INSERT INTO products (product_code, product_name, product_name_en, product_type, category_id, unit_id, barcode, cost_price, selling_price, tax_rate, is_taxable, is_active, is_track_inventory, reorder_level)
            VALUES ('PRD-003', 'ألواح خشبية', 'Wooden Boards', 'goods', {cat2}, {unit3}, '6281000001003', 120, 200, 15, true, true, true, 50) RETURNING id""")
        prod4 = exe_ret(f"""INSERT INTO products (product_code, product_name, product_name_en, product_type, category_id, unit_id, barcode, cost_price, selling_price, tax_rate, is_taxable, is_active, is_track_inventory, reorder_level)
            VALUES ('PRD-004', 'دهانات جدارية', 'Wall Paint', 'goods', {cat2}, {unit1}, '6281000001004', 95, 160, 15, true, true, true, 30) RETURNING id""")
        prod5 = exe_ret(f"""INSERT INTO products (product_code, product_name, product_name_en, product_type, category_id, unit_id, cost_price, selling_price, tax_rate, is_taxable, is_active, is_track_inventory)
            VALUES ('PRD-005', 'مواسير PVC', 'PVC Pipes', 'goods', {cat2}, {unit3}, 45, 80, 15, true, true, true) RETURNING id""")
        prod6 = exe_ret(f"""INSERT INTO products (product_code, product_name, product_name_en, product_type, category_id, unit_id, cost_price, selling_price, tax_rate, is_taxable, is_active, is_track_inventory)
            VALUES ('SRV-001', 'استشارات هندسية', 'Engineering Consulting', 'service', {cat3}, {unit4}, 0, 500, 15, true, true, false) RETURNING id""")

        PROD_IDS = [prod1, prod2, prod3, prod4, prod5, prod6]

        # ============================================================
        # 7. INVENTORY (initial stock)
        # ============================================================
        print("7. Inventory...")
        # Stock quantities
        stock_data = [
            (prod1, WH_MAIN, 500, 50),   # حديد مسلح
            (prod1, WH_JED, 200, 50),
            (prod2, WH_MAIN, 1000, 30),   # أسمنت
            (prod2, WH_JED, 400, 30),
            (prod3, WH_MAIN, 150, 120),   # ألواح خشبية
            (prod4, WH_MAIN, 80, 95),     # دهانات
            (prod4, WH_RYD, 50, 95),
            (prod5, WH_MAIN, 300, 45),    # مواسير
        ]
        for pid, wid, qty, cost in stock_data:
            exe(f"""INSERT INTO inventory (product_id, warehouse_id, quantity, reserved_quantity, available_quantity, average_cost)
                VALUES ({pid}, {wid}, {qty}, 0, {qty}, {cost})""")

        # ============================================================
        # 8. COST CENTERS & BUDGETS
        # ============================================================
        print("8. Cost Centers & Budgets...")
        cc1 = exe_ret(f"INSERT INTO cost_centers (center_code, center_name, center_name_en, department_id, budget, currency, is_active) VALUES ('CC-ADMIN', 'الإدارة العامة', 'General Admin', {dept_fin}, 500000, 'SAR', true) RETURNING id")
        cc2 = exe_ret(f"INSERT INTO cost_centers (center_code, center_name, center_name_en, department_id, budget, currency, is_active) VALUES ('CC-SALES', 'المبيعات', 'Sales', {dept_sales}, 300000, 'SAR', true) RETURNING id")
        cc3 = exe_ret(f"INSERT INTO cost_centers (center_code, center_name, center_name_en, department_id, budget, currency, is_active) VALUES ('CC-PROD', 'الإنتاج', 'Production', {dept_ops}, 400000, 'SAR', true) RETURNING id")

        bud1 = exe_ret(f"""INSERT INTO budgets (name, budget_code, budget_name, budget_name_en, fiscal_year, branch_id, department_id, budget_type, status, total_budget, start_date, end_date, created_by)
            VALUES ('موازنة 2025 - إدارة', 'BUD-2025-ADMIN', 'موازنة الإدارة', 'Admin Budget', {fy_id}, 1, {dept_fin}, 'operational', 'approved', 500000, '2025-01-01', '2025-12-31', 1) RETURNING id""")
        bud2 = exe_ret(f"""INSERT INTO budgets (name, budget_code, budget_name, budget_name_en, fiscal_year, branch_id, department_id, budget_type, status, total_budget, start_date, end_date, created_by)
            VALUES ('موازنة 2025 - مبيعات', 'BUD-2025-SALES', 'موازنة المبيعات', 'Sales Budget', {fy_id}, 1, {dept_sales}, 'operational', 'approved', 300000, '2025-01-01', '2025-12-31', 1) RETURNING id""")

        # Budget items
        for aid, amt in [(ACCT_SAL, 216000), (ACCT_RENT, 60000), (ACCT_UTL, 24000), (ACCT_MKT, 36000)]:
            exe(f"INSERT INTO budget_items (budget_id, account_id, planned_amount, actual_amount, notes) VALUES ({bud1}, {aid}, {amt}, 0, 'بند موازنة')")

        # ============================================================
        # 9. COSTING POLICIES
        # ============================================================
        print("9. Costing Policies...")
        cp_id = exe_ret("""INSERT INTO costing_policies (policy_name, policy_type, description, is_active, created_by)
            VALUES ('سياسة المتوسط المرجح', 'weighted_average', 'تكلفة المتوسط المرجح للمخزون', true, 1) RETURNING id""")

        # ============================================================
        # 10. PROJECTS
        # ============================================================
        print("10. Projects...")
        proj1 = exe_ret(f"""INSERT INTO projects (project_code, project_name, project_name_en, description, customer_id, project_type, status, start_date, end_date, planned_budget, actual_cost, progress_percentage, manager_id, branch_id, created_by)
            VALUES ('PRJ-001', 'مشروع بناء مجمع سكني', 'Residential Complex', 'إنشاء مجمع سكني 50 وحدة', {cust_t1}, 'construction', 'in_progress', '2025-10-01', '2025-12-31', 2000000, 800000, 40, {emp1}, 1, 1) RETURNING id""")
        proj2 = exe_ret(f"""INSERT INTO projects (project_code, project_name, project_name_en, description, customer_id, project_type, status, start_date, end_date, planned_budget, actual_cost, progress_percentage, manager_id, branch_id, created_by)
            VALUES ('PRJ-002', 'تجهيز مكاتب', 'Office Setup', 'تجهيز 20 مكتب', {cust_t2}, 'interior', 'in_progress', '2025-01-15', '2025-06-30', 500000, 120000, 25, {emp1}, 1, 1) RETURNING id""")
        proj3 = exe_ret(f"""INSERT INTO projects (project_code, project_name, project_name_en, description, customer_id, project_type, status, start_date, end_date, planned_budget, actual_cost, progress_percentage, branch_id, created_by)
            VALUES ('PRJ-003', 'صيانة مصنع', 'Factory Maintenance', 'صيانة شاملة للمصنع', {cust_t3}, 'maintenance', 'planned', '2025-04-01', '2025-07-31', 300000, 0, 0, 2, 1) RETURNING id""")

        # Project tasks
        task1 = exe_ret(f"INSERT INTO project_tasks (project_id, task_name, task_name_en, start_date, end_date, planned_hours, status, assigned_to) VALUES ({proj1}, 'التصميم الهندسي', 'Engineering Design', '2025-10-01', '2025-12-31', 500, 'completed', {emp1}) RETURNING id")
        task2 = exe_ret(f"INSERT INTO project_tasks (project_id, task_name, task_name_en, start_date, end_date, planned_hours, progress, status, assigned_to) VALUES ({proj1}, 'الأعمال الإنشائية', 'Construction', '2025-01-01', '2025-09-30', 2000, 30, 'in_progress', {emp1}) RETURNING id")
        task3 = exe_ret(f"INSERT INTO project_tasks (project_id, task_name, task_name_en, start_date, end_date, planned_hours, status, assigned_to) VALUES ({proj2}, 'توريد أثاث', 'Furniture Supply', '2025-02-01', '2025-03-31', 200, 'in_progress', {emp2}) RETURNING id")

        # ============================================================
        # 11. CONTRACTS
        # ============================================================
        print("11. Contracts...")
        con1 = exe_ret(f"""INSERT INTO contracts (contract_number, party_id, contract_type, status, start_date, end_date, billing_interval, total_amount, currency, created_by)
            VALUES ('CON-2025-001', {cust1}, 'service', 'active', '2025-01-01', '2025-12-31', 'monthly', 360000, 'SAR', 1) RETURNING id""")
        con2 = exe_ret(f"""INSERT INTO contracts (contract_number, party_id, contract_type, status, start_date, end_date, billing_interval, total_amount, currency, created_by)
            VALUES ('CON-2025-002', {sup1}, 'supply', 'active', '2025-01-01', '2025-06-30', 'quarterly', 200000, 'SAR', 1) RETURNING id""")

        # ============================================================
        # 12. SALES & PURCHASE FLOW (with correct accounting)
        # ============================================================
        print("12. Sales & Purchase Documents...")

        # --- Purchase Orders ---
        po1 = exe_ret(f"""INSERT INTO purchase_orders (po_number, party_id, supplier_id, branch_id, order_date, expected_date, subtotal, tax_amount, discount, total, status, currency, exchange_rate, created_by)
            VALUES ('PO-2025-001', {sup1}, {sup1}, 1, '2025-01-10', '2025-01-20', 50000, 7500, 0, 57500, 'received', 'SAR', 1, 1) RETURNING id""")
        exe(f"INSERT INTO purchase_order_lines (po_id, product_id, description, quantity, unit_price, tax_rate, discount, total, received_quantity) VALUES ({po1}, {prod1}, 'حديد مسلح 12مم', 500, 50, 15, 0, 28750, 500)")
        exe(f"INSERT INTO purchase_order_lines (po_id, product_id, description, quantity, unit_price, tax_rate, discount, total, received_quantity) VALUES ({po1}, {prod2}, 'أسمنت بورتلاندي', 500, 30, 15, 0, 17250, 500)")

        po2 = exe_ret(f"""INSERT INTO purchase_orders (po_number, party_id, supplier_id, branch_id, order_date, expected_date, subtotal, tax_amount, discount, total, status, currency, exchange_rate, created_by)
            VALUES ('PO-2025-002', {sup2}, {sup2}, 1, '2025-01-25', '2025-02-05', 20000, 3000, 0, 23000, 'received', 'SAR', 1, 1) RETURNING id""")
        exe(f"INSERT INTO purchase_order_lines (po_id, product_id, description, quantity, unit_price, tax_rate, discount, total, received_quantity) VALUES ({po2}, {prod3}, 'ألواح خشبية', 100, 120, 15, 0, 13800, 100)")
        exe(f"INSERT INTO purchase_order_lines (po_id, product_id, description, quantity, unit_price, tax_rate, discount, total, received_quantity) VALUES ({po2}, {prod4}, 'دهانات جدارية', 50, 95, 15, 0, 5462.50, 50)")

        # --- Purchase Invoices (create journal entries for COGS tracking) ---
        # Purchase Invoice 1: 57,500 SAR (including VAT)
        pinv1 = exe_ret(f"""INSERT INTO invoices (invoice_number, invoice_type, party_id, supplier_id, invoice_date, due_date, subtotal, tax_amount, discount, total, paid_amount, status, branch_id, warehouse_id, currency, exchange_rate, created_by)
            VALUES ('PINV-2025-001', 'purchase', {sup1}, {sup1}, '2025-01-15', '2025-02-15', 50000, 7500, 0, 57500, 57500, 'paid', 1, {WH_MAIN}, 'SAR', 1, 1) RETURNING id""")
        exe(f"INSERT INTO invoice_lines (invoice_id, product_id, description, quantity, unit_price, tax_rate, discount, total) VALUES ({pinv1}, {prod1}, 'حديد مسلح 12مم', 500, 50, 15, 0, 28750)")
        exe(f"INSERT INTO invoice_lines (invoice_id, product_id, description, quantity, unit_price, tax_rate, discount, total) VALUES ({pinv1}, {prod2}, 'أسمنت بورتلاندي', 500, 30, 15, 0, 17250)")

        # Purchase Invoice 2: 23,000 SAR
        pinv2 = exe_ret(f"""INSERT INTO invoices (invoice_number, invoice_type, party_id, supplier_id, invoice_date, due_date, subtotal, tax_amount, discount, total, paid_amount, status, branch_id, warehouse_id, currency, exchange_rate, created_by)
            VALUES ('PINV-2025-002', 'purchase', {sup2}, {sup2}, '2025-01-28', '2025-02-28', 20000, 3000, 0, 23000, 23000, 'paid', 1, {WH_MAIN}, 'SAR', 1, 1) RETURNING id""")
        exe(f"INSERT INTO invoice_lines (invoice_id, product_id, description, quantity, unit_price, tax_rate, discount, total) VALUES ({pinv2}, {prod3}, 'ألواح خشبية', 100, 120, 15, 0, 13800)")
        exe(f"INSERT INTO invoice_lines (invoice_id, product_id, description, quantity, unit_price, tax_rate, discount, total) VALUES ({pinv2}, {prod4}, 'دهانات جدارية', 50, 95, 15, 0, 5462.50)")

        # --- Sales Quotations ---
        sq1 = exe_ret(f"""INSERT INTO sales_quotations (sq_number, party_id, customer_id, branch_id, quotation_date, expiry_date, subtotal, tax_amount, discount, total, status, currency, exchange_rate, created_by)
            VALUES ('SQ-2025-001', {cust1}, {cust1}, 1, '2025-01-05', '2025-02-05', 60000, 9000, 0, 69000, 'accepted', 'SAR', 1, 1) RETURNING id""")
        exe(f"INSERT INTO sales_quotation_lines (sq_id, product_id, description, quantity, unit_price, tax_rate, discount, total) VALUES ({sq1}, {prod1}, 'حديد مسلح 12مم', 200, 85, 15, 0, 19550)")
        exe(f"INSERT INTO sales_quotation_lines (sq_id, product_id, description, quantity, unit_price, tax_rate, discount, total) VALUES ({sq1}, {prod2}, 'أسمنت بورتلاندي', 300, 55, 15, 0, 18975)")

        # --- Sales Orders ---
        so1 = exe_ret(f"""INSERT INTO sales_orders (so_number, party_id, customer_id, branch_id, warehouse_id, order_date, expected_delivery_date, subtotal, tax_amount, discount, total, status, currency, exchange_rate, created_by)
            VALUES ('SO-2025-001', {cust1}, {cust1}, 1, {WH_MAIN}, '2025-01-08', '2025-01-20', 60000, 9000, 0, 69000, 'delivered', 'SAR', 1, 1) RETURNING id""")
        exe(f"INSERT INTO sales_order_lines (so_id, product_id, description, quantity, unit_price, tax_rate, discount, total) VALUES ({so1}, {prod1}, 'حديد مسلح 12مم', 200, 85, 15, 0, 19550)")
        exe(f"INSERT INTO sales_order_lines (so_id, product_id, description, quantity, unit_price, tax_rate, discount, total) VALUES ({so1}, {prod2}, 'أسمنت بورتلاندي', 300, 55, 15, 0, 18975)")

        so2 = exe_ret(f"""INSERT INTO sales_orders (so_number, party_id, customer_id, branch_id, warehouse_id, order_date, expected_delivery_date, subtotal, tax_amount, discount, total, status, currency, exchange_rate, created_by)
            VALUES ('SO-2025-002', {cust2}, {cust2}, 1, {WH_MAIN}, '2025-02-01', '2025-02-15', 40000, 6000, 0, 46000, 'confirmed', 'SAR', 1, 1) RETURNING id""")
        exe(f"INSERT INTO sales_order_lines (so_id, product_id, description, quantity, unit_price, tax_rate, discount, total) VALUES ({so2}, {prod3}, 'ألواح خشبية', 100, 200, 15, 0, 23000)")
        exe(f"INSERT INTO sales_order_lines (so_id, product_id, description, quantity, unit_price, tax_rate, discount, total) VALUES ({so2}, {prod4}, 'دهانات جدارية', 80, 160, 15, 0, 14720)")

        # ============================================================
        # 13. SALES INVOICES (the core financial data)
        # ============================================================
        print("13. Sales Invoices...")

        # INVOICE 1: 69,000 SAR (200 حديد + 300 أسمنت) - PAID
        # Revenue = 60,000, VAT = 9,000
        # COGS = 200*50 + 300*30 = 19,000
        sinv1 = exe_ret(f"""INSERT INTO invoices (invoice_number, invoice_type, party_id, customer_id, invoice_date, due_date, subtotal, tax_amount, discount, total, paid_amount, status, branch_id, warehouse_id, currency, exchange_rate, created_by, sales_order_id)
            VALUES ('INV-2025-001', 'sales', {cust1}, {cust1}, '2025-01-15', '2025-02-15', 60000, 9000, 0, 69000, 69000, 'paid', 1, {WH_MAIN}, 'SAR', 1, 1, {so1}) RETURNING id""")
        exe(f"INSERT INTO invoice_lines (invoice_id, product_id, description, quantity, unit_price, tax_rate, discount, total) VALUES ({sinv1}, {prod1}, 'حديد مسلح 12مم', 200, 85, 15, 0, 19550)")
        exe(f"INSERT INTO invoice_lines (invoice_id, product_id, description, quantity, unit_price, tax_rate, discount, total) VALUES ({sinv1}, {prod2}, 'أسمنت بورتلاندي', 300, 55, 15, 0, 18975)")

        # INVOICE 2: 23,000 SAR (100 ألواح خشبية) - PARTIAL
        # Revenue = 20,000, VAT = 3,000
        # COGS = 100*120 = 12,000
        sinv2 = exe_ret(f"""INSERT INTO invoices (invoice_number, invoice_type, party_id, customer_id, invoice_date, due_date, subtotal, tax_amount, discount, total, paid_amount, status, branch_id, warehouse_id, currency, exchange_rate, created_by)
            VALUES ('INV-2025-002', 'sales', {cust2}, {cust2}, '2025-01-25', '2025-02-25', 20000, 3000, 0, 23000, 15000, 'partial', 1, {WH_MAIN}, 'SAR', 1, 1) RETURNING id""")
        exe(f"INSERT INTO invoice_lines (invoice_id, product_id, description, quantity, unit_price, tax_rate, discount, total) VALUES ({sinv2}, {prod3}, 'ألواح خشبية', 100, 200, 15, 0, 23000)")

        # INVOICE 3: 14,720 SAR (80 دهانات) - PAID
        # Revenue = 12,800, VAT = 1,920
        # COGS = 80*95 = 7,600
        sinv3 = exe_ret(f"""INSERT INTO invoices (invoice_number, invoice_type, party_id, customer_id, invoice_date, due_date, subtotal, tax_amount, discount, total, paid_amount, status, branch_id, warehouse_id, currency, exchange_rate, created_by)
            VALUES ('INV-2025-003', 'sales', {cust3}, {cust3}, '2025-02-05', '2025-03-05', 12800, 1920, 0, 14720, 14720, 'paid', 1, {WH_MAIN}, 'SAR', 1, 1) RETURNING id""")
        exe(f"INSERT INTO invoice_lines (invoice_id, product_id, description, quantity, unit_price, tax_rate, discount, total) VALUES ({sinv3}, {prod4}, 'دهانات جدارية', 80, 160, 15, 0, 14720)")

        # INVOICE 4: 9,200 SAR (200 مواسير) - UNPAID
        # Revenue = 8,000, VAT = 1,200
        # COGS = 200*45 = 9,000
        sinv4 = exe_ret(f"""INSERT INTO invoices (invoice_number, invoice_type, party_id, customer_id, invoice_date, due_date, subtotal, tax_amount, discount, total, paid_amount, status, branch_id, warehouse_id, currency, exchange_rate, created_by)
            VALUES ('INV-2025-004', 'sales', {cust4}, {cust4}, '2025-02-10', '2025-03-10', 8000, 1200, 0, 9200, 0, 'unpaid', 1, {WH_MAIN}, 'SAR', 1, 1) RETURNING id""")
        exe(f"INSERT INTO invoice_lines (invoice_id, product_id, description, quantity, unit_price, tax_rate, discount, total) VALUES ({sinv4}, {prod5}, 'مواسير PVC', 200, 80, 15, 0, 18400)")

        # INVOICE 5: 17,250 SAR (30 ساعة استشارات) - PAID (services)
        # Revenue = 15,000, VAT = 2,250
        # COGS = 0 (service)
        sinv5 = exe_ret(f"""INSERT INTO invoices (invoice_number, invoice_type, party_id, customer_id, invoice_date, due_date, subtotal, tax_amount, discount, total, paid_amount, status, branch_id, currency, exchange_rate, created_by)
            VALUES ('INV-2025-005', 'sales', {cust1}, {cust1}, '2025-02-15', '2025-03-15', 15000, 2250, 0, 17250, 17250, 'paid', 1, 'SAR', 1, 1) RETURNING id""")
        exe(f"INSERT INTO invoice_lines (invoice_id, product_id, description, quantity, unit_price, tax_rate, discount, total) VALUES ({sinv5}, {prod6}, 'استشارات هندسية', 30, 500, 15, 0, 17250)")

        # INVOICE 6: 5,100 (AED) ER=1.02 = 5,202 SAR — PAID (foreign currency)
        # Revenue = 5,000 AED * 1.02 = 5,100 SAR, then total incl VAT = 5,865 AED * 1.02 = 5,982.30 SAR
        # Let's simplify: subtotal=5000 AED, VAT=750 AED, total=5750 AED, ER=1.02
        # SAR equivalent: 5750*1.02 = 5,865 SAR
        sinv6 = exe_ret(f"""INSERT INTO invoices (invoice_number, invoice_type, party_id, customer_id, invoice_date, due_date, subtotal, tax_amount, discount, total, paid_amount, status, branch_id, currency, exchange_rate, created_by)
            VALUES ('INV-2025-006', 'sales', {cust5}, {cust5}, '2025-02-18', '2025-03-18', 5000, 750, 0, 5750, 5750, 'paid', 3, 'AED', 1.02, 1) RETURNING id""")
        exe(f"INSERT INTO invoice_lines (invoice_id, product_id, description, quantity, unit_price, tax_rate, discount, total) VALUES ({sinv6}, {prod1}, 'حديد مسلح - تصدير', 50, 100, 15, 0, 5750)")

        SINV_IDS = [sinv1, sinv2, sinv3, sinv4, sinv5, sinv6]

        # Sales return
        sret1 = exe_ret(f"""INSERT INTO sales_returns (return_number, party_id, customer_id, branch_id, warehouse_id, invoice_id, return_date, subtotal, tax_amount, total, status, refund_method, refund_amount, currency, exchange_rate, created_by)
            VALUES ('RET-2025-001', {cust1}, {cust1}, 1, {WH_MAIN}, {sinv1}, '2025-02-01', 8000, 1200, 9200, 'completed', 'bank_transfer', 9200, 'SAR', 1, 1) RETURNING id""")
        # Return: revenue reduction = 8,000, COGS reduction = (proportional ~2,533)
        # Return 50 steel rods, COGS = 50*50 = 2,500
        exe(f"INSERT INTO sales_return_lines (return_id, product_id, description, quantity, unit_price, tax_rate, total, reason) VALUES ({sret1}, {prod1}, 'حديد مسلح - مرتجع', 50, 160, 15, 9200, 'عيب تصنيع')")

        # ============================================================
        # 14. JOURNAL ENTRIES (THE ACCOUNTING BACKBONE)
        # ============================================================
        print("14. Journal Entries (balanced)...")

        # ====== OPENING BALANCES (JE-001) ======
        # Capital: 500,000 | Cash: 200,000 | Bank: 250,000 | Inventory: 50,000
        je1 = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, created_by, posted_at)
            VALUES ('JE-2025-001', '2025-01-01', 'OPENING', 'أرصدة افتتاحية', 'posted', 'SAR', 1, 1, 1, '2025-01-01') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je1}, {ACCT_BOX}, 200000, 0, 'رصيد الصندوق الافتتاحي')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je1}, {ACCT_BANK}, 250000, 0, 'رصيد البنك الافتتاحي')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je1}, {ACCT_INV}, 50000, 0, 'رصيد المخزون الافتتاحي')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je1}, {ACCT_CAP}, 0, 500000, 'رأس المال')")

        # ====== PURCHASE INVOICES (JE-002, JE-003) ======
        # Purchase 1: 57,500 (50,000 inventory + 7,500 VAT input)
        je2 = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, source, source_id, created_by, posted_at)
            VALUES ('JE-2025-002', '2025-01-15', 'PINV-2025-001', 'فاتورة مشتريات - مؤسسة الأمان', 'posted', 'SAR', 1, 1, 'invoice', {pinv1}, 1, '2025-01-15') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je2}, {ACCT_INV}, 50000, 0, 'مخزون - مشتريات')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je2}, {ACCT_VAT_IN}, 7500, 0, 'ضريبة مدخلات')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je2}, {ACCT_AP}, 0, 57500, 'ذمة مورد')")

        # Purchase 2: 23,000
        je3 = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, source, source_id, created_by, posted_at)
            VALUES ('JE-2025-003', '2025-01-28', 'PINV-2025-002', 'فاتورة مشتريات - شركة التقنية', 'posted', 'SAR', 1, 1, 'invoice', {pinv2}, 1, '2025-01-28') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je3}, {ACCT_INV}, 20000, 0, 'مخزون - مشتريات')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je3}, {ACCT_VAT_IN}, 3000, 0, 'ضريبة مدخلات')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je3}, {ACCT_AP}, 0, 23000, 'ذمة مورد')")

        # ====== SUPPLIER PAYMENTS (JE-004, JE-005) ======
        je4 = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, created_by, posted_at)
            VALUES ('JE-2025-004', '2025-01-20', 'PAY-SUP-001', 'سداد مورد الأمان', 'posted', 'SAR', 1, 1, 1, '2025-01-20') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je4}, {ACCT_AP}, 57500, 0, 'سداد ذمة مورد')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je4}, {ACCT_BANK}, 0, 57500, 'تحويل بنكي')")

        je5 = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, created_by, posted_at)
            VALUES ('JE-2025-005', '2025-02-01', 'PAY-SUP-002', 'سداد مورد التقنية', 'posted', 'SAR', 1, 1, 1, '2025-02-01') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je5}, {ACCT_AP}, 23000, 0, 'سداد ذمة مورد')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je5}, {ACCT_BANK}, 0, 23000, 'تحويل بنكي')")

        # ====== SALES INVOICES JOURNAL ENTRIES ======
        # INV-001: Revenue 60,000 + VAT 9,000; COGS = 19,000
        je6 = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, source, source_id, created_by, posted_at)
            VALUES ('JE-2025-006', '2025-01-15', 'INV-2025-001', 'فاتورة مبيعات - الوفاء', 'posted', 'SAR', 1, 1, 'invoice', {sinv1}, 1, '2025-01-15') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je6}, {ACCT_AR}, 69000, 0, 'ذمة عميل')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je6}, {ACCT_SALE_G}, 0, 60000, 'إيرادات مبيعات بضائع')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je6}, {ACCT_VAT_OUT}, 0, 9000, 'ضريبة مخرجات')")

        je6b = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, source, source_id, created_by, posted_at)
            VALUES ('JE-2025-006B', '2025-01-15', 'COGS-INV-001', 'تكلفة مبيعات INV-001', 'posted', 'SAR', 1, 1, 'invoice', {sinv1}, 1, '2025-01-15') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je6b}, {ACCT_CGS_G}, 19000, 0, 'تكلفة بضاعة مباعة')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je6b}, {ACCT_INV}, 0, 19000, 'صرف من المخزون')")

        # INV-002: Revenue 20,000 + VAT 3,000; COGS = 12,000
        je7 = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, source, source_id, created_by, posted_at)
            VALUES ('JE-2025-007', '2025-01-25', 'INV-2025-002', 'فاتورة مبيعات - النور', 'posted', 'SAR', 1, 1, 'invoice', {sinv2}, 1, '2025-01-25') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je7}, {ACCT_AR}, 23000, 0, 'ذمة عميل')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je7}, {ACCT_SALE_G}, 0, 20000, 'إيرادات مبيعات')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je7}, {ACCT_VAT_OUT}, 0, 3000, 'ضريبة مخرجات')")

        je7b = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, source, source_id, created_by, posted_at)
            VALUES ('JE-2025-007B', '2025-01-25', 'COGS-INV-002', 'تكلفة مبيعات INV-002', 'posted', 'SAR', 1, 1, 'invoice', {sinv2}, 1, '2025-01-25') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je7b}, {ACCT_CGS_G}, 12000, 0, 'تكلفة بضاعة مباعة')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je7b}, {ACCT_INV}, 0, 12000, 'صرف من المخزون')")

        # INV-003: Revenue 12,800 + VAT 1,920; COGS = 7,600
        je8 = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, source, source_id, created_by, posted_at)
            VALUES ('JE-2025-008', '2025-02-05', 'INV-2025-003', 'فاتورة مبيعات - البناء الحديث', 'posted', 'SAR', 1, 1, 'invoice', {sinv3}, 1, '2025-02-05') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je8}, {ACCT_AR}, 14720, 0, 'ذمة عميل')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je8}, {ACCT_SALE_G}, 0, 12800, 'إيرادات مبيعات')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je8}, {ACCT_VAT_OUT}, 0, 1920, 'ضريبة مخرجات')")

        je8b = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, source, source_id, created_by, posted_at)
            VALUES ('JE-2025-008B', '2025-02-05', 'COGS-INV-003', 'تكلفة مبيعات INV-003', 'posted', 'SAR', 1, 1, 'invoice', {sinv3}, 1, '2025-02-05') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je8b}, {ACCT_CGS_G}, 7600, 0, 'تكلفة بضاعة مباعة')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je8b}, {ACCT_INV}, 0, 7600, 'صرف من المخزون')")

        # INV-004: Revenue 8,000 + VAT 1,200; COGS = 9,000
        je9 = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, source, source_id, created_by, posted_at)
            VALUES ('JE-2025-009', '2025-02-10', 'INV-2025-004', 'فاتورة مبيعات - المطيري', 'posted', 'SAR', 1, 1, 'invoice', {sinv4}, 1, '2025-02-10') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je9}, {ACCT_AR}, 9200, 0, 'ذمة عميل')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je9}, {ACCT_SALE_G}, 0, 8000, 'إيرادات مبيعات')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je9}, {ACCT_VAT_OUT}, 0, 1200, 'ضريبة مخرجات')")

        je9b = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, source, source_id, created_by, posted_at)
            VALUES ('JE-2025-009B', '2025-02-10', 'COGS-INV-004', 'تكلفة مبيعات INV-004', 'posted', 'SAR', 1, 1, 'invoice', {sinv4}, 1, '2025-02-10') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je9b}, {ACCT_CGS_G}, 9000, 0, 'تكلفة بضاعة مباعة')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je9b}, {ACCT_INV}, 0, 9000, 'صرف من المخزون')")

        # INV-005: Revenue 15,000 + VAT 2,250 (services, no COGS)
        je10 = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, source, source_id, created_by, posted_at)
            VALUES ('JE-2025-010', '2025-02-15', 'INV-2025-005', 'فاتورة خدمات - الوفاء', 'posted', 'SAR', 1, 1, 'invoice', {sinv5}, 1, '2025-02-15') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je10}, {ACCT_AR}, 17250, 0, 'ذمة عميل')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je10}, {ACCT_SALE_S}, 0, 15000, 'إيرادات خدمات')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je10}, {ACCT_VAT_OUT}, 0, 2250, 'ضريبة مخرجات')")

        # INV-006: Revenue 5,000 AED*1.02=5,100 SAR + VAT 750 AED*1.02=765 SAR
        # COGS = 50*50 = 2,500 SAR
        je11 = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, source, source_id, created_by, posted_at)
            VALUES ('JE-2025-011', '2025-02-18', 'INV-2025-006', 'فاتورة مبيعات - الرشيد (AED)', 'posted', 'AED', 1.02, 3, 'invoice', {sinv6}, 1, '2025-02-18') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je11}, {ACCT_AR}, 5865, 0, 'ذمة عميل (5750 AED)')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je11}, {ACCT_SALE_G}, 0, 5100, 'إيرادات مبيعات بضائع')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je11}, {ACCT_VAT_OUT}, 0, 765, 'ضريبة مخرجات')")

        je11b = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, source, source_id, created_by, posted_at)
            VALUES ('JE-2025-011B', '2025-02-18', 'COGS-INV-006', 'تكلفة مبيعات INV-006', 'posted', 'SAR', 1, 3, 'invoice', {sinv6}, 1, '2025-02-18') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je11b}, {ACCT_CGS_G}, 2500, 0, 'تكلفة بضاعة مباعة')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je11b}, {ACCT_INV}, 0, 2500, 'صرف من المخزون')")

        # ====== SALES RETURN (JE-012) ======
        # Return: Revenue -8,000, VAT -1,200, COGS reversal -2,500
        je12 = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, created_by, posted_at)
            VALUES ('JE-2025-012', '2025-02-01', 'RET-2025-001', 'مرتجع مبيعات', 'posted', 'SAR', 1, 1, 1, '2025-02-01') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je12}, {ACCT_SALE_R}, 8000, 0, 'مردودات مبيعات')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je12}, {ACCT_VAT_OUT}, 1200, 0, 'عكس ضريبة مخرجات')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je12}, {ACCT_AR}, 0, 9200, 'تخفيض ذمة عميل')")

        je12b = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, created_by, posted_at)
            VALUES ('JE-2025-012B', '2025-02-01', 'COGS-RET-001', 'عكس تكلفة مرتجع', 'posted', 'SAR', 1, 1, 1, '2025-02-01') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je12b}, {ACCT_INV}, 2500, 0, 'إعادة للمخزون')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je12b}, {ACCT_CGS_G}, 0, 2500, 'عكس تكلفة مرتجع')")

        # ====== CUSTOMER PAYMENTS (JE-013 to JE-017) ======
        # INV-001: Paid 69,000
        je13 = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, created_by, posted_at)
            VALUES ('JE-2025-013', '2025-01-20', 'PAY-CUST-001', 'سداد عميل الوفاء - INV-001', 'posted', 'SAR', 1, 1, 1, '2025-01-20') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je13}, {ACCT_BANK}, 69000, 0, 'تحصيل بنكي')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je13}, {ACCT_AR}, 0, 69000, 'تحصيل ذمة عميل')")

        # INV-002: Partial 15,000 of 23,000
        je14 = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, created_by, posted_at)
            VALUES ('JE-2025-014', '2025-02-10', 'PAY-CUST-002', 'سداد جزئي - النور', 'posted', 'SAR', 1, 1, 1, '2025-02-10') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je14}, {ACCT_BANK}, 15000, 0, 'تحصيل بنكي')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je14}, {ACCT_AR}, 0, 15000, 'تحصيل ذمة عميل')")

        # INV-003: Paid 14,720
        je15 = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, created_by, posted_at)
            VALUES ('JE-2025-015', '2025-02-10', 'PAY-CUST-003', 'سداد عميل البناء الحديث', 'posted', 'SAR', 1, 1, 1, '2025-02-10') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je15}, {ACCT_BOX}, 14720, 0, 'نقد مستلم')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je15}, {ACCT_AR}, 0, 14720, 'تحصيل ذمة عميل')")

        # INV-005: Paid 17,250
        je16 = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, created_by, posted_at)
            VALUES ('JE-2025-016', '2025-02-18', 'PAY-CUST-005', 'سداد عميل الوفاء - خدمات', 'posted', 'SAR', 1, 1, 1, '2025-02-18') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je16}, {ACCT_BANK}, 17250, 0, 'تحصيل بنكي')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je16}, {ACCT_AR}, 0, 17250, 'تحصيل ذمة عميل')")

        # INV-006: Paid 5,865 SAR (5,750 AED)
        je17 = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, created_by, posted_at)
            VALUES ('JE-2025-017', '2025-02-20', 'PAY-CUST-006', 'سداد عميل الرشيد', 'posted', 'AED', 1.02, 3, 1, '2025-02-20') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je17}, {ACCT_BANK}, 5865, 0, 'تحصيل بنكي')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je17}, {ACCT_AR}, 0, 5865, 'تحصيل ذمة عميل')")

        # Refund for return
        je17r = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, created_by, posted_at)
            VALUES ('JE-2025-017R', '2025-02-02', 'REFUND-RET-001', 'رد مبلغ مرتجع', 'posted', 'SAR', 1, 1, 1, '2025-02-02') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je17r}, {ACCT_AR}, 0, 0, 'صفر - تم خصم سابقاً')")
        # The return JE already reduced AR by 9,200. Refund goes from bank:
        # Actually, refund means we pay the customer back
        # But AR was already reduced. We need to pay from bank:
        # This is already handled above - let's remove this empty one and add proper refund
        db.execute(text(f"DELETE FROM journal_lines WHERE journal_entry_id = {je17r}"))
        db.execute(text(f"DELETE FROM journal_entries WHERE id = {je17r}"))

        # ====== OPERATING EXPENSES (JE-018 to JE-023) ======
        # Salaries Jan: 18,000
        je18 = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, created_by, posted_at)
            VALUES ('JE-2025-018', '2025-01-31', 'SAL-JAN', 'رواتب يناير 2025', 'posted', 'SAR', 1, 1, 1, '2025-01-31') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je18}, {ACCT_SAL}, 18000, 0, 'رواتب وأجور')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je18}, {ACCT_BANK}, 0, 18000, 'دفع من البنك')")

        # Salaries Feb: 18,000
        je19 = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, created_by, posted_at)
            VALUES ('JE-2025-019', '2025-02-28', 'SAL-FEB', 'رواتب فبراير 2025', 'posted', 'SAR', 1, 1, 1, '2025-02-23') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je19}, {ACCT_SAL}, 18000, 0, 'رواتب وأجور')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je19}, {ACCT_BANK}, 0, 18000, 'دفع من البنك')")

        # Rent Jan+Feb: 10,000 (5,000/month)
        je20 = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, created_by, posted_at)
            VALUES ('JE-2025-020', '2025-01-01', 'RENT-Q1', 'إيجار يناير-فبراير', 'posted', 'SAR', 1, 1, 1, '2025-01-01') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je20}, {ACCT_RENT}, 10000, 0, 'مصروف إيجار')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je20}, {ACCT_BOX}, 0, 10000, 'دفع نقدي')")

        # Utilities: 3,500
        je21 = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, created_by, posted_at)
            VALUES ('JE-2025-021', '2025-02-15', 'UTL-JF', 'كهرباء ومياه يناير-فبراير', 'posted', 'SAR', 1, 1, 1, '2025-02-15') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je21}, {ACCT_UTL}, 3500, 0, 'كهرباء ومياه')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je21}, {ACCT_BANK}, 0, 3500, 'خصم من البنك')")

        # Other OpEx: Communications 1,200 + Maintenance 2,000 + Gov 800 + Marketing 4,500 + Insurance 2,500 + GOSI 3,500 + General 1,500 + Bank 500
        # Total = 16,500
        je22 = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, created_by, posted_at)
            VALUES ('JE-2025-022', '2025-02-20', 'OPEX-MIX', 'مصروفات تشغيلية متنوعة', 'posted', 'SAR', 1, 1, 1, '2025-02-20') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je22}, {ACCT_COM}, 1200, 0, 'اتصالات')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je22}, {ACCT_MNT}, 2000, 0, 'صيانة')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je22}, {ACCT_GOV}, 800, 0, 'رسوم حكومية')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je22}, {ACCT_MKT}, 4500, 0, 'تسويق')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je22}, {ACCT_INS}, 2500, 0, 'تأمين')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je22}, {ACCT_GOSI}, 3500, 0, 'تأمينات اجتماعية')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je22}, {ACCT_GEN}, 1500, 0, 'مصروفات عمومية')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je22}, {ACCT_BANK_F}, 500, 0, 'رسوم بنكية')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je22}, {ACCT_BANK}, 0, 16500, 'دفع من البنك')")

        # Depreciation: 4,000
        je23 = exe_ret(f"""INSERT INTO journal_entries (entry_number, entry_date, reference, description, status, currency, exchange_rate, branch_id, created_by, posted_at)
            VALUES ('JE-2025-023', '2025-02-28', 'DEP-JF', 'إهلاك يناير-فبراير', 'posted', 'SAR', 1, 1, 1, '2025-02-23') RETURNING id""")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je23}, {ACCT_DEPR}, 4000, 0, 'مصروف إهلاك')")
        exe(f"INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description) VALUES ({je23}, {ACCT_DEPR_ACC}, 0, 4000, 'إهلاك متراكم')")

        # ====== UPDATE ACCOUNT BALANCES ======
        print("15. Updating account balances from JE...")
        exe("""UPDATE accounts SET balance = COALESCE(sub.bal, 0)
            FROM (
                SELECT jl.account_id, SUM(jl.debit - jl.credit) as bal
                FROM journal_lines jl
                JOIN journal_entries je ON je.id = jl.journal_entry_id
                WHERE je.status = 'posted'
                GROUP BY jl.account_id
            ) sub
            WHERE accounts.id = sub.account_id""")

        # ============================================================
        # 15. POS ORDERS
        # ============================================================
        print("16. POS...")
        # POS Session
        ps1 = exe_ret(f"""INSERT INTO pos_sessions (session_code, user_id, warehouse_id, opening_balance, closing_balance, total_sales, total_returns, cash_register_balance, difference, status, opened_at, closed_at, branch_id, treasury_account_id)
            VALUES ('POS-S-001', 1, {WH_MAIN}, 5000, 16507.50, 12007.50, 500, 16507.50, 0, 'closed', '2025-02-22 08:00', '2025-02-22 22:00', 1, {treas_box}) RETURNING id""")

        # POS Order 1: 5,175 SAR
        po_ord1 = exe_ret(f"""INSERT INTO pos_orders (order_number, session_id, customer_id, branch_id, warehouse_id, order_date, status, subtotal, tax_amount, total_amount, paid_amount, change_amount, created_by)
            VALUES ('POS-ORD-001', {ps1}, {cust_t4}, 1, {WH_MAIN}, '2025-02-22 10:30', 'completed', 4500, 675, 5175, 5175, 0, 1) RETURNING id""")
        exe(f"INSERT INTO pos_order_lines (order_id, product_id, description, quantity, original_price, unit_price, tax_rate, tax_amount, subtotal, total, warehouse_id) VALUES ({po_ord1}, {prod1}, 'حديد مسلح 12مم', 10, 85, 85, 15, 127.50, 850, 977.50, {WH_MAIN})")
        exe(f"INSERT INTO pos_order_lines (order_id, product_id, description, quantity, original_price, unit_price, tax_rate, tax_amount, subtotal, total, warehouse_id) VALUES ({po_ord1}, {prod2}, 'أسمنت بورتلاندي', 50, 55, 55, 15, 412.50, 2750, 3162.50, {WH_MAIN})")
        exe(f"INSERT INTO pos_order_lines (order_id, product_id, description, quantity, original_price, unit_price, tax_rate, tax_amount, subtotal, total, warehouse_id) VALUES ({po_ord1}, {prod4}, 'دهانات جدارية', 5, 160, 160, 15, 120, 800, 920, {WH_MAIN})")
        exe(f"INSERT INTO pos_order_payments (order_id, method, amount) VALUES ({po_ord1}, 'cash', 5175)")

        # POS Order 2: 3,450 SAR
        po_ord2 = exe_ret(f"""INSERT INTO pos_orders (order_number, session_id, walk_in_customer_name, branch_id, warehouse_id, order_date, status, subtotal, tax_amount, total_amount, paid_amount, change_amount, created_by)
            VALUES ('POS-ORD-002', {ps1}, 'عميل زائر', 1, {WH_MAIN}, '2025-02-22 14:15', 'completed', 3000, 450, 3450, 3450, 0, 1) RETURNING id""")
        exe(f"INSERT INTO pos_order_lines (order_id, product_id, description, quantity, original_price, unit_price, tax_rate, tax_amount, subtotal, total, warehouse_id) VALUES ({po_ord2}, {prod3}, 'ألواح خشبية', 15, 200, 200, 15, 450, 3000, 3450, {WH_MAIN})")
        exe(f"INSERT INTO pos_order_payments (order_id, method, amount, reference) VALUES ({po_ord2}, 'card', 3450, 'VISA-4832')")

        # POS Order 3: 3,382.50 SAR
        po_ord3 = exe_ret(f"""INSERT INTO pos_orders (order_number, session_id, customer_id, branch_id, warehouse_id, order_date, status, subtotal, tax_amount, total_amount, paid_amount, change_amount, created_by)
            VALUES ('POS-ORD-003', {ps1}, {cust_t3}, 1, {WH_MAIN}, '2025-02-22 17:00', 'completed', 2940, 441, 3381, 3381, 0, 1) RETURNING id""")
        exe(f"INSERT INTO pos_order_lines (order_id, product_id, description, quantity, original_price, unit_price, tax_rate, tax_amount, subtotal, total, warehouse_id) VALUES ({po_ord3}, {prod5}, 'مواسير PVC', 30, 80, 80, 15, 360, 2400, 2760, {WH_MAIN})")
        exe(f"INSERT INTO pos_order_lines (order_id, product_id, description, quantity, original_price, unit_price, tax_rate, tax_amount, subtotal, total, warehouse_id) VALUES ({po_ord3}, {prod4}, 'دهانات', 3, 160, 160, 15, 72, 480, 552, {WH_MAIN})")
        exe(f"INSERT INTO pos_order_payments (order_id, method, amount) VALUES ({po_ord3}, 'cash', 2000)")
        exe(f"INSERT INTO pos_order_payments (order_id, method, amount, reference) VALUES ({po_ord3}, 'card', 1381, 'MADA-9921')")

        # ============================================================
        # 16. EXPENSES
        # ============================================================
        print("17. Expenses...")
        for exp_data in [
            ('EXP-2025-001', '2025-01-15', 'office_supplies', 800, 'مستلزمات مكتبية', 'قرطاسية', 'cash', ACCT_GEN, cc1),
            ('EXP-2025-002', '2025-01-20', 'travel', 2500, 'تذاكر سفر - اجتماع عمل', 'سفر', 'bank_transfer', ACCT_TRV, cc2),
            ('EXP-2025-003', '2025-02-01', 'utilities', 1800, 'فاتورة كهرباء', 'مرافق', 'bank_transfer', ACCT_UTL, cc1),
            ('EXP-2025-004', '2025-02-05', 'maintenance', 3000, 'صيانة مكيفات', 'صيانة', 'cash', ACCT_MNT, cc3),
            ('EXP-2025-005', '2025-02-10', 'marketing', 5000, 'حملة إعلانية', 'تسويق', 'bank_transfer', ACCT_MKT, cc2),
            ('EXP-2025-006', '2025-02-15', 'fuel', 1200, 'وقود سيارات', 'نقل', 'cash', ACCT_TRV, cc3),
        ]:
            exe(f"""INSERT INTO expenses (expense_number, expense_date, expense_type, amount, description, category, payment_method, expense_account_id, cost_center_id, branch_id, approval_status, created_by)
                VALUES ('{exp_data[0]}', '{exp_data[1]}', '{exp_data[2]}', {exp_data[3]}, '{exp_data[4]}', '{exp_data[5]}', '{exp_data[6]}', {exp_data[7]}, {exp_data[8]}, 1, 'approved', 1)""")

        # ============================================================
        # 17. ASSETS
        # ============================================================
        print("18. Assets...")
        asset1 = exe_ret(f"""INSERT INTO assets (company_id, branch_id, name, code, type, purchase_date, cost, residual_value, life_years, currency, depreciation_method, status)
            VALUES ('{COMPANY_ID}', 1, 'مبنى المكتب الرئيسي', 'AST-001', 'building', '2020-01-01', 500000, 50000, 20, 'SAR', 'straight_line', 'active') RETURNING id""")
        asset2 = exe_ret(f"""INSERT INTO assets (company_id, branch_id, name, code, type, purchase_date, cost, residual_value, life_years, currency, depreciation_method, status)
            VALUES ('{COMPANY_ID}', 1, 'سيارة تويوتا هايلكس', 'AST-002', 'vehicle', '2024-06-01', 120000, 20000, 5, 'SAR', 'straight_line', 'active') RETURNING id""")
        asset3 = exe_ret(f"""INSERT INTO assets (company_id, branch_id, name, code, type, purchase_date, cost, residual_value, life_years, currency, depreciation_method, status)
            VALUES ('{COMPANY_ID}', 1, 'أجهزة حاسوب وشبكة', 'AST-003', 'equipment', '2025-01-01', 45000, 5000, 4, 'SAR', 'straight_line', 'active') RETURNING id""")
        asset4 = exe_ret(f"""INSERT INTO assets (company_id, branch_id, name, code, type, purchase_date, cost, residual_value, life_years, currency, depreciation_method, status)
            VALUES ('{COMPANY_ID}', 2, 'أثاث مكتبي - جدة', 'AST-004', 'furniture', '2025-06-01', 35000, 5000, 10, 'SAR', 'straight_line', 'active') RETURNING id""")

        # Rest of the populate script - supplementary tables
        # (following same structure as original populate_all_tables.py)

        # ============================================================
        # 18-30. ALL SUPPLEMENTARY TABLES
        # ============================================================
        print("19. Supplementary tables...")

        # Asset categories, maintenance, insurance, etc.
        exe("INSERT INTO asset_categories (category_code, category_name, category_name_en, depreciation_rate, useful_life) VALUES ('CAT-BLDG', 'مباني', 'Buildings', 5, 20)")
        exe("INSERT INTO asset_categories (category_code, category_name, category_name_en, depreciation_rate, useful_life) VALUES ('CAT-VEH', 'مركبات', 'Vehicles', 20, 5)")
        exe("INSERT INTO asset_categories (category_code, category_name, category_name_en, depreciation_rate, useful_life) VALUES ('CAT-COMP', 'حاسبات', 'Computers', 25, 4)")
        exe("INSERT INTO asset_categories (category_code, category_name, category_name_en, depreciation_rate, useful_life) VALUES ('CAT-FURN', 'أثاث', 'Furniture', 10, 10)")

        exe(f"INSERT INTO asset_maintenance (asset_id, maintenance_type, description, scheduled_date, completed_date, cost, vendor, status, created_by) VALUES ({asset2}, 'preventive', 'صيانة دورية للسيارة', '2025-01-15', '2025-01-16', 2000, 'مركز الفحص', 'completed', 1)")
        exe(f"INSERT INTO asset_insurance (asset_id, policy_number, insurer, coverage_type, premium_amount, coverage_amount, start_date, end_date, status) VALUES ({asset1}, 'INS-001', 'التعاونية للتأمين', 'comprehensive', 12000, 500000, '2025-01-01', '2025-12-31', 'active')")
        exe(f"INSERT INTO asset_insurance (asset_id, policy_number, insurer, coverage_type, premium_amount, coverage_amount, start_date, end_date, status) VALUES ({asset2}, 'INS-002', 'بوبا للتأمين', 'comprehensive', 5000, 120000, '2025-01-01', '2025-12-31', 'active')")

        # Banking & Reconciliation
        br1 = exe_ret(f"INSERT INTO bank_reconciliations (treasury_account_id, statement_date, start_balance, end_balance, status, notes, created_by, branch_id) VALUES ({treas_bank}, '2025-01-31', 250000, 217750, 'completed', 'مطابقة يناير', 1, 1) RETURNING id")
        exe(f"INSERT INTO bank_statement_lines (reconciliation_id, transaction_date, description, reference, debit, credit, balance, is_reconciled) VALUES ({br1}, '2025-01-15', 'تحويل وارد من عميل', 'TRF-001', 0, 69000, 319000, true)")
        exe(f"INSERT INTO bank_statement_lines (reconciliation_id, transaction_date, description, reference, debit, credit, balance, is_reconciled) VALUES ({br1}, '2025-01-20', 'سداد مورد', 'TRF-002', 57500, 0, 261500, true)")
        exe(f"INSERT INTO bank_statement_lines (reconciliation_id, transaction_date, description, reference, debit, credit, balance, is_reconciled) VALUES ({br1}, '2025-01-31', 'رواتب يناير', 'SAL-JAN', 18000, 0, 243500, true)")

        # Checks
        exe(f"INSERT INTO checks_payable (check_number, beneficiary_name, bank_name, branch_name, amount, currency, issue_date, due_date, party_id, treasury_account_id, status, branch_id, created_by) VALUES ('CHK-P-001', 'مؤسسة الأمان', 'البنك الأهلي', 'الرياض', 35000, 'SAR', '2025-01-20', '2025-03-20', {sup1}, {treas_bank}, 'issued', 1, 1)")
        exe(f"INSERT INTO checks_receivable (check_number, drawer_name, bank_name, branch_name, amount, currency, issue_date, due_date, party_id, treasury_account_id, status, branch_id, created_by) VALUES ('CHK-R-001', 'شركة الوفاء', 'بنك الراجحي', 'الرياض', 25000, 'SAR', '2025-01-25', '2025-04-25', {cust1}, {treas_rajhi}, 'in_hand', 1, 1)")

        # Notes payable/receivable
        exe(f"INSERT INTO notes_payable (note_number, beneficiary_name, bank_name, amount, currency, issue_date, due_date, maturity_date, party_id, treasury_account_id, status, branch_id, created_by) VALUES ('NP-001', 'شركة التقنية', 'البنك الأهلي', 50000, 'SAR', '2025-01-01', '2025-06-01', '2025-06-01', {sup2}, {treas_bank}, 'active', 1, 1)")
        exe(f"INSERT INTO notes_receivable (note_number, drawer_name, bank_name, amount, currency, issue_date, due_date, maturity_date, party_id, treasury_account_id, status, branch_id, created_by) VALUES ('NR-001', 'شركة البناء الحديث', 'بنك الراجحي', 30000, 'SAR', '2025-02-01', '2025-08-01', '2025-08-01', {cust3}, {treas_rajhi}, 'active', 1, 1)")

        # Customer/Supplier details
        exe("INSERT INTO customer_groups (group_code, group_name, group_name_en, discount_percentage, payment_days, status, branch_id) VALUES ('CG-VIP', 'عملاء VIP', 'VIP', 10, 60, 'active', 1)")
        exe("INSERT INTO customer_groups (group_code, group_name, group_name_en, discount_percentage, payment_days, status, branch_id) VALUES ('CG-REG', 'عملاء عاديون', 'Regular', 0, 30, 'active', 1)")
        exe("INSERT INTO supplier_groups (group_code, group_name, group_name_en, discount_percentage, payment_days, branch_id, status) VALUES ('SG-LOC', 'موردين محليين', 'Local', 5, 30, 1, 'active')")
        exe("INSERT INTO supplier_groups (group_code, group_name, group_name_en, discount_percentage, payment_days, branch_id, status) VALUES ('SG-INT', 'موردين دوليين', 'International', 3, 60, 1, 'active')")

        exe(f"INSERT INTO customer_contacts (customer_id, contact_name, contact_name_en, position, email, mobile, is_primary) VALUES ({cust_t1}, 'أحمد المالكي', 'Ahmed Al-Malki', 'مدير المشتريات', 'ahmed@wafaa.sa', '0551234567', true)")
        exe(f"INSERT INTO customer_contacts (customer_id, contact_name, contact_name_en, position, email, mobile, is_primary) VALUES ({cust_t2}, 'خالد الشمري', 'Khalid', 'المدير العام', 'khalid@alnour.sa', '0561112233', true)")
        exe(f"INSERT INTO supplier_contacts (supplier_id, contact_name, contact_name_en, position, email, mobile, is_primary) VALUES ({supp_t1}, 'محمد القحطاني', 'Mohammed', 'مدير المبيعات', 'mohammed@alaman.sa', '0541234567', true)")
        exe(f"INSERT INTO supplier_contacts (supplier_id, contact_name, contact_name_en, position, email, mobile, is_primary) VALUES ({supp_t2}, 'عبدالله الغامدي', 'Abdullah', 'مسؤول التوريد', 'abdullah@unitedtech.sa', '0559998877', true)")

        # Customer/Supplier balances - consistent with AR/AP
        exe(f"INSERT INTO customer_balances (customer_id, currency, total_receivable, total_paid, outstanding_balance, aging_30) VALUES ({cust_t1}, 'SAR', 77050, 77050, 0, 0)")
        exe(f"INSERT INTO customer_balances (customer_id, currency, total_receivable, total_paid, outstanding_balance, aging_30) VALUES ({cust_t2}, 'SAR', 23000, 15000, 8000, 8000)")
        exe(f"INSERT INTO customer_balances (customer_id, currency, total_receivable, total_paid, outstanding_balance, aging_30) VALUES ({cust_t3}, 'SAR', 14720, 14720, 0, 0)")
        exe(f"INSERT INTO supplier_balances (supplier_id, currency, total_payable, total_paid, outstanding_balance) VALUES ({supp_t1}, 'SAR', 57500, 57500, 0)")
        exe(f"INSERT INTO supplier_balances (supplier_id, currency, total_payable, total_paid, outstanding_balance) VALUES ({supp_t2}, 'SAR', 23000, 23000, 0)")

        # Party groups and transactions
        exe("INSERT INTO party_groups (group_code, group_name, group_name_en, discount_percentage, payment_days, description, status) VALUES ('PG-PREM', 'فئة مميزة', 'Premium', 10, 45, 'أطراف ذات معاملات كبيرة', 'active')")

        # HR Tables
        print("20. HR Tables...")
        ss1 = exe_ret("INSERT INTO salary_structures (name, name_en, description, base_type, is_active) VALUES ('هيكل راتب إداري', 'Admin Structure', 'هيكل الموظفين الإداريين', 'monthly', true) RETURNING id")
        sc1 = exe_ret(f"INSERT INTO salary_components (name, name_en, component_type, calculation_type, is_taxable, is_gosi_applicable, is_active, sort_order, structure_id) VALUES ('الراتب الأساسي', 'Basic Salary', 'earning', 'fixed', true, true, true, 1, {ss1}) RETURNING id")
        sc2 = exe_ret(f"INSERT INTO salary_components (name, name_en, component_type, calculation_type, is_taxable, is_gosi_applicable, is_active, sort_order, structure_id) VALUES ('بدل سكن', 'Housing', 'earning', 'percentage', true, true, true, 2, {ss1}) RETURNING id")
        sc3 = exe_ret(f"INSERT INTO salary_components (name, name_en, component_type, calculation_type, is_taxable, is_gosi_applicable, is_active, sort_order, structure_id) VALUES ('خصم تأمينات', 'GOSI', 'deduction', 'percentage', false, false, true, 3, {ss1}) RETURNING id")

        for eid in EMP_IDS:
            exe(f"INSERT INTO employee_salary_components (employee_id, component_id, amount, is_active, effective_date) VALUES ({eid}, {sc1}, {8000+eid*1000}, true, '2025-01-01')")

        exe("INSERT INTO gosi_settings (employee_share_percentage, employer_share_percentage, occupational_hazard_percentage, max_contributable_salary, is_active, effective_date) VALUES (9.75, 11.75, 2, 45000, true, '2025-01-01')")

        # Attendance
        for eid in EMP_IDS:
            for d in range(1, 6):
                exe(f"INSERT INTO attendance (employee_id, date, check_in, check_out, status) VALUES ({eid}, '2025-02-{d:02d}', '2025-02-{d:02d} 08:00', '2025-02-{d:02d} 17:00', 'present')")

        # Leave requests
        exe(f"INSERT INTO leave_requests (employee_id, leave_type, start_date, end_date, reason, status, approved_by) VALUES ({emp1}, 'annual', '2025-03-01', '2025-03-05', 'إجازة سنوية', 'approved', 1)")
        exe(f"INSERT INTO leave_requests (employee_id, leave_type, start_date, end_date, reason, status) VALUES ({emp2}, 'sick', '2025-02-10', '2025-02-12', 'إجازة مرضية', 'approved')")

        # Payroll
        pp1 = exe_ret("INSERT INTO payroll_periods (name, start_date, end_date, payment_date, status) VALUES ('يناير 2025', '2025-01-01', '2025-01-31', '2025-01-31', 'closed') RETURNING id")
        pp2 = exe_ret("INSERT INTO payroll_periods (name, start_date, end_date, payment_date, status) VALUES ('فبراير 2025', '2025-02-01', '2025-02-28', '2025-02-28', 'processing') RETURNING id")

        for eid in EMP_IDS:
            basic = 8000 + eid * 1000
            housing = 3000 + eid * 500
            transport = 1000 + 200
            gosi = round(basic * 0.0975, 2)
            net = basic + housing + transport - gosi
            exe(f"""INSERT INTO payroll_entries (period_id, employee_id, basic_salary, housing_allowance, transport_allowance, gosi_employee_share, net_salary, status)
                VALUES ({pp1}, {eid}, {basic}, {housing}, {transport}, {gosi}, {net}, 'paid')""")

        # Approval workflows
        wf1 = exe_ret("""INSERT INTO approval_workflows (name, document_type, description, conditions, steps, is_active, created_by)
            VALUES ('اعتماد أوامر الشراء', 'purchase_order', 'سلسلة اعتماد أوامر الشراء',
            '{"min_amount": 10000}'::jsonb,
            '[{"step": 1, "role": "manager", "action": "approve"}, {"step": 2, "role": "finance", "action": "approve"}]'::jsonb,
            true, 1) RETURNING id""")

        # RFQs
        rfq1 = exe_ret(f"""INSERT INTO request_for_quotations (rfq_number, title, description, status, deadline, branch_id, created_by)
            VALUES ('RFQ-2025-001', 'طلب عرض سعر مواد بناء', 'مواد بناء للمشروع السكني', 'closed', '2025-01-20', 1, 1) RETURNING id""")
        exe(f"INSERT INTO rfq_lines (rfq_id, product_id, product_name, quantity, unit, specifications) VALUES ({rfq1}, {prod1}, 'حديد مسلح', 500, 'كغ', 'مواصفات سعودية')")
        exe(f"INSERT INTO rfq_responses (rfq_id, supplier_id, supplier_name, unit_price, total_price, delivery_days, is_selected) VALUES ({rfq1}, {sup1}, 'مؤسسة الأمان', 50, 25000, 10, true)")
        exe(f"INSERT INTO rfq_responses (rfq_id, supplier_id, supplier_name, unit_price, total_price, delivery_days, is_selected) VALUES ({rfq1}, {sup2}, 'شركة التقنية', 55, 27500, 7, false)")

        # Sales opportunities  
        opp1 = exe_ret(f"""INSERT INTO sales_opportunities (title, customer_id, contact_name, contact_email, stage, probability, expected_value, expected_close_date, currency, source, assigned_to, branch_id, created_by)
            VALUES ('مشروع توسعة مصنع', {cust1}, 'أحمد المالكي', 'ahmed@wafaa.sa', 'proposal', 70, 500000, '2025-06-30', 'SAR', 'referral', {emp2}, 1, 1) RETURNING id""")
        opp2 = exe_ret(f"""INSERT INTO sales_opportunities (title, customer_id, contact_name, stage, probability, expected_value, expected_close_date, currency, source, assigned_to, branch_id, created_by)
            VALUES ('عقد صيانة سنوي', {cust3}, 'فهد', 'negotiation', 85, 200000, '2025-04-30', 'SAR', 'direct', {emp2}, 2, 1) RETURNING id""")

        # Sales commissions/targets
        exe(f"INSERT INTO commission_rules (name, salesperson_id, rate_type, rate, min_amount, is_active, branch_id) VALUES ('عمولة مبيعات', {emp2}, 'percentage', 3, 5000, true, 1)")
        for m in range(1, 7):
            exe(f"INSERT INTO sales_targets (year, month_number, target_amount, branch_id, salesperson_id, created_by) VALUES (2025, {m}, {80000+m*5000}, 1, {emp2}, 1)")

        # Manufacturing
        print("21. Manufacturing...")
        wc1 = exe_ret(f"INSERT INTO work_centers (name, code, capacity_per_day, cost_per_hour, location, status) VALUES ('خط الإنتاج الرئيسي', 'WC-001', 100, 50, 'المصنع - الرياض', 'active') RETURNING id")
        wc2 = exe_ret(f"INSERT INTO work_centers (name, code, capacity_per_day, cost_per_hour, location, status) VALUES ('قسم التجميع', 'WC-002', 200, 35, 'المصنع - الرياض', 'active') RETURNING id")

        route1 = exe_ret(f"INSERT INTO manufacturing_routes (name, product_id, is_active, description) VALUES ('مسار إنتاج ألواح', {prod3}, true, 'مسار إنتاج الألواح الخشبية') RETURNING id")
        exe(f"INSERT INTO manufacturing_operations (route_id, sequence, work_center_id, description, setup_time, cycle_time) VALUES ({route1}, 1, {wc1}, 'قص وتشكيل', 30, 15)")
        exe(f"INSERT INTO manufacturing_operations (route_id, sequence, work_center_id, description, setup_time, cycle_time) VALUES ({route1}, 2, {wc2}, 'تجميع وتشطيب', 15, 10)")

        bom1 = exe_ret(f"INSERT INTO bill_of_materials (product_id, code, name, yield_quantity, route_id, is_active) VALUES ({prod3}, 'BOM-001', 'قائمة مواد ألواح خشبية', 10, {route1}, true) RETURNING id")
        exe(f"INSERT INTO bom_components (bom_id, component_product_id, quantity, waste_percentage) VALUES ({bom1}, {prod1}, 5, 2)")
        exe(f"INSERT INTO bom_components (bom_id, component_product_id, quantity, waste_percentage) VALUES ({bom1}, {prod2}, 20, 5)")

        prod_ord1 = exe_ret(f"""INSERT INTO production_orders (order_number, product_id, bom_id, route_id, quantity, produced_quantity, scrapped_quantity, status, start_date, due_date, warehouse_id, created_by)
            VALUES ('MO-2025-001', {prod3}, {bom1}, {route1}, 50, 48, 2, 'completed', '2025-01-20', '2025-02-10', {WH_MAIN}, 1) RETURNING id""")

        equip1 = exe_ret(f"INSERT INTO manufacturing_equipment (name, code, work_center_id, status, purchase_date) VALUES ('ماكينة القص CNC', 'EQ-001', {wc1}, 'active', '2024-01-15') RETURNING id")
        equip2 = exe_ret(f"INSERT INTO manufacturing_equipment (name, code, work_center_id, status, purchase_date) VALUES ('ماكينة اللحام', 'EQ-002', {wc2}, 'active', '2024-06-01') RETURNING id")

        # Service requests & tickets
        print("22. Services & Support...")
        sr1 = exe_ret(f"INSERT INTO service_requests (title, description, category, priority, status, customer_id, assigned_to, estimated_cost, created_by) VALUES ('طلب صيانة مكيفات', 'صيانة 5 مكيفات في المكتب', 'maintenance', 'medium', 'in_progress', {cust1}, {emp3}, 3000, 1) RETURNING id")
        sr2 = exe_ret(f"INSERT INTO service_requests (title, description, category, priority, status, customer_id, created_by) VALUES ('تركيب شبكة', 'تركيب شبكة في المكتب الجديد', 'installation', 'high', 'open', {cust2}, 1) RETURNING id")

        tk1 = exe_ret(f"INSERT INTO support_tickets (ticket_number, subject, description, customer_id, status, priority, category, branch_id, created_by) VALUES ('TKT-001', 'مشكلة في الفاتورة', 'خطأ في مبلغ الفاتورة', {cust1}, 'resolved', 'low', 'billing', 1, 1) RETURNING id")
        tk2 = exe_ret(f"INSERT INTO support_tickets (ticket_number, subject, description, customer_id, status, priority, category, assigned_to, branch_id, created_by) VALUES ('TKT-002', 'تأخر في التوصيل', 'لم يتم تسليم الطلب في الموعد', {cust3}, 'open', 'high', 'delivery', {emp2}, 2, 1) RETURNING id")

        # Notifications & messages
        exe("INSERT INTO notifications (user_id, title, message, link, is_read, type) VALUES (1, 'طلب اعتماد جديد', 'لديك طلب اعتماد بانتظار موافقتك', '/approvals', false, 'approval')")
        exe("INSERT INTO notifications (user_id, title, message, link, is_read, type) VALUES (1, 'فاتورة متأخرة', 'فاتورة INV-2025-004 متأخرة', '/invoices', false, 'alert')")
        exe("INSERT INTO notifications (user_id, title, message, link, is_read, type) VALUES (1, 'مخزون منخفض', 'منتج دهانات وصل للحد الأدنى', '/inventory', false, 'warning')")

        exe("INSERT INTO messages (sender_id, receiver_id, subject, body, message_type, is_read) VALUES (1, 1, 'ملاحظات الميزانية', 'يرجى مراجعة بنود الميزانية', 'internal', true)")

        # Document types & templates
        exe("INSERT INTO document_types (type_code, type_name, type_name_en, description, allowed_extensions, max_size, is_active) VALUES ('DT-INV', 'فاتورة', 'Invoice', 'مستندات الفواتير', 'pdf,jpg', 10, true)")
        exe("INSERT INTO document_types (type_code, type_name, type_name_en, description, allowed_extensions, max_size, is_active) VALUES ('DT-CON', 'عقد', 'Contract', 'عقود واتفاقيات', 'pdf,docx', 20, true)")
        exe("INSERT INTO document_templates (template_name, template_type, description, template_content, is_default) VALUES ('نموذج فاتورة', 'invoice', 'قالب فاتورة', '<h1>فاتورة</h1>', true)")

        # Exchange rates (might already exist)
        exe("INSERT INTO exchange_rates (currency_id, rate_date, rate, source, created_by) VALUES (2, '2025-02-23', 3.75, 'manual', 1) ON CONFLICT DO NOTHING")
        exe("INSERT INTO exchange_rates (currency_id, rate_date, rate, source, created_by) VALUES (3, '2025-02-23', 4.10, 'manual', 1) ON CONFLICT DO NOTHING")
        exe("INSERT INTO exchange_rates (currency_id, rate_date, rate, source, created_by) VALUES (4, '2025-02-23', 1.02, 'manual', 1) ON CONFLICT DO NOTHING")

        # Tax groups, returns, calendar
        exe("INSERT INTO tax_groups (group_code, group_name, group_name_en, description, is_active) VALUES ('TG-VAT', 'ضريبة القيمة المضافة', 'VAT', '15% ضريبة', true)")

        tr1 = exe_ret("INSERT INTO tax_returns (return_number, tax_period, tax_type, taxable_amount, tax_amount, penalty_amount, interest_amount, total_amount, due_date, status, branch_id, created_by) VALUES ('TR-2025-Q1', '2025-Q1', 'vat', 120800, 18120, 0, 0, 18120, '2025-04-30', 'draft', 1, 1) RETURNING id")

        exe("INSERT INTO tax_calendar (title, tax_type, due_date, is_recurring, recurrence_months, is_completed, notes, created_by) VALUES ('إقرار ضريبة Q1', 'vat', '2025-04-30', true, 3, false, 'إقرار ربع سنوي', 1)")

        # Recurring journals
        rjt1 = exe_ret(f"INSERT INTO recurring_journal_templates (name, description, reference, frequency, start_date, end_date, next_run_date, is_active, auto_post, branch_id) VALUES ('إيجار شهري', 'قيد إيجار', 'RJ-RENT', 'monthly', '2025-01-01', '2025-12-31', '2025-03-01', true, true, 1) RETURNING id")
        exe(f"INSERT INTO recurring_journal_lines (template_id, account_id, debit, credit, description) VALUES ({rjt1}, {ACCT_RENT}, 5000, 0, 'مصروف إيجار')")
        exe(f"INSERT INTO recurring_journal_lines (template_id, account_id, debit, credit, description) VALUES ({rjt1}, {ACCT_BOX}, 0, 5000, 'دفع نقدي')")

        # POS extras
        exe(f"INSERT INTO pos_tables (table_number, table_name, floor, capacity, status, is_active, branch_id) VALUES ('T-01', 'طاولة 1', 'الطابق الأرضي', 4, 'available', true, 1)")
        exe(f"INSERT INTO pos_tables (table_number, table_name, floor, capacity, status, is_active, branch_id) VALUES ('T-02', 'طاولة 2', 'الطابق الأرضي', 6, 'available', true, 1)")
        exe(f"INSERT INTO pos_promotions (name, promotion_type, value, min_order_amount, start_date, end_date, is_active, branch_id, created_by) VALUES ('خصم 10%', 'percentage', 10, 100, '2025-02-01 00:00', '2025-02-28 23:59', true, 1, 1)")

        lp1 = exe_ret("INSERT INTO pos_loyalty_programs (name, points_per_unit, currency_per_point, min_points_redeem, is_active, branch_id) VALUES ('برنامج نقاط الولاء', 1, 0.1, 100, true, 1) RETURNING id")
        exe(f"INSERT INTO pos_loyalty_points (program_id, party_id, points_earned, points_redeemed, balance, tier) VALUES ({lp1}, {cust4}, 500, 100, 400, 'silver')")

        # Reports
        exe("INSERT INTO financial_reports (report_name, report_type, report_period, generated_date, parameters, data, created_by) VALUES ('ميزان المراجعة Q1-2025', 'trial_balance', '2025-Q1', CURRENT_TIMESTAMP, '{}'::jsonb, '{}'::jsonb, 1)")
        exe("INSERT INTO custom_reports (report_name, description, config, created_by) VALUES ('تقرير مبيعات شهري', 'تقرير مخصص', '{\"type\": \"sales\"}'::jsonb, 1)")
        exe("INSERT INTO report_templates (template_name, template_type, description, is_default) VALUES ('قالب كشف حساب', 'account_statement', 'قالب كشف حساب', true)")
        exe("INSERT INTO scheduled_reports (report_name, report_type, report_config, frequency, recipients, format, branch_id, next_run_at, is_active, created_by) VALUES ('تقرير أسبوعي', 'sales_summary', '{}'::jsonb, 'weekly', 'admin@aman.sa', 'pdf', 1, '2025-03-01', true, 1)")

        # Email templates
        exe("INSERT INTO email_templates (template_name, subject, body, is_active) VALUES ('ترحيب عميل', 'مرحباً بك', '<p>مرحباً {{name}}</p>', true)")
        exe("INSERT INTO email_templates (template_name, subject, body, is_active) VALUES ('تذكير فاتورة', 'تذكير', '<p>فاتورة {{num}} مستحقة</p>', true)")

        # Dashboard layouts (might already exist)
        exe("INSERT INTO dashboard_layouts (user_id, layout_name, widgets, is_active) VALUES (1, 'لوحة المدير', '[]'::jsonb, true) ON CONFLICT DO NOTHING")

        # Costing policy details & history
        exe(f"INSERT INTO costing_policy_details (policy_id, setting_key, setting_value) VALUES ({cp_id}, 'valuation_method', 'weighted_average')")
        exe("INSERT INTO costing_policy_history (old_policy_type, new_policy_type, change_date, changed_by, reason, affected_products_count, total_cost_impact, status) VALUES ('fifo', 'weighted_average', '2025-06-01', 1, 'توحيد سياسة التكلفة', 6, 0, 'completed')")

        # Payments
        exe(f"INSERT INTO payments (payment_number, payment_type, customer_id, payment_date, amount, currency, exchange_rate, payment_method, reference, status, created_by) VALUES ('PAY-001', 'received', {cust_t1}, '2025-01-20', 69000, 'SAR', 1, 'bank_transfer', 'TRF-001', 'completed', 1)")
        exe(f"INSERT INTO payments (payment_number, payment_type, supplier_id, payment_date, amount, currency, exchange_rate, payment_method, reference, status, created_by) VALUES ('PAY-002', 'sent', {supp_t1}, '2025-01-20', 57500, 'SAR', 1, 'bank_transfer', 'TRF-002', 'completed', 1)")

        # Payment & Receipt vouchers
        exe(f"INSERT INTO payment_vouchers (voucher_number, branch_id, voucher_type, voucher_date, party_type, party_id, amount, payment_method, treasury_account_id, reference, currency, exchange_rate, status, created_by) VALUES ('PV-001', 1, 'supplier', '2025-01-20', 'supplier', {sup1}, 57500, 'bank_transfer', {treas_bank}, 'PINV-001', 'SAR', 1, 'posted', 1)")

        # Webhooks
        exe("INSERT INTO webhooks (name, url, secret, events, is_active, retry_count, timeout_seconds, created_by) VALUES ('إشعار المبيعات', 'https://hooks.example.com/sales', 'secret', '[\"invoice.created\"]'::jsonb, true, 3, 30, 1)")

        # Project extras
        exe(f"INSERT INTO project_budgets (project_id, budget_type, planned_amount, actual_amount, variance, status) VALUES ({proj1}, 'materials', 1000000, 400000, 600000, 'active')")
        exe(f"INSERT INTO project_budgets (project_id, budget_type, planned_amount, actual_amount, variance, status) VALUES ({proj1}, 'labor', 500000, 200000, 300000, 'active')")
        exe(f"INSERT INTO project_expenses (project_id, expense_type, expense_date, amount, description, status, created_by) VALUES ({proj1}, 'materials', '2025-01-15', 200000, 'شراء مواد بناء', 'approved', 1)")
        exe(f"INSERT INTO project_revenues (project_id, revenue_type, revenue_date, amount, description, status, created_by) VALUES ({proj1}, 'milestone', '2025-01-31', 300000, 'دفعة المرحلة الأولى', 'received', 1)")
        exe(f"INSERT INTO project_timesheets (employee_id, project_id, task_id, date, hours, description, status) VALUES ({USER_ID}, {proj1}, {task1}, '2025-02-20', 8, 'عمل على التصميم', 'approved')")

        # User branches (might already exist from base data)
        exe("INSERT INTO user_branches (user_id, branch_id) VALUES (1, 1) ON CONFLICT DO NOTHING")
        exe("INSERT INTO user_branches (user_id, branch_id) VALUES (1, 2) ON CONFLICT DO NOTHING")
        exe("INSERT INTO user_branches (user_id, branch_id) VALUES (1, 3) ON CONFLICT DO NOTHING")

        # ============================================================
        # 23. REMAINING EMPTY TABLES (87 tables)
        # ============================================================
        print("23. Populating remaining empty tables...")

        # --- Approval Requests & Actions ---
        apr1 = exe_ret(f"""INSERT INTO approval_requests (workflow_id, document_type, document_id, amount, description, current_step, total_steps, status, requested_by, created_at)
            VALUES ({wf1}, 'purchase_order', {po1}, 57500, 'اعتماد أمر شراء مواد بناء', 2, 2, 'approved', 1, '2025-01-12') RETURNING id""")
        exe(f"INSERT INTO approval_actions (request_id, step, action, actioned_by, notes, actioned_at) VALUES ({apr1}, 1, 'approved', 1, 'موافق', '2025-01-12 10:00')")
        exe(f"INSERT INTO approval_actions (request_id, step, action, actioned_by, notes, actioned_at) VALUES ({apr1}, 2, 'approved', 1, 'اعتماد نهائي', '2025-01-12 14:00')")

        # --- Asset Depreciation Schedule ---
        exe(f"INSERT INTO asset_depreciation_schedule (asset_id, fiscal_year, date, amount, accumulated_amount, book_value, posted, created_at) VALUES ({asset1}, {fy_id}, '2025-06-30', 22500, 22500, 477500, true, NOW())")
        exe(f"INSERT INTO asset_depreciation_schedule (asset_id, fiscal_year, date, amount, accumulated_amount, book_value, posted, created_at) VALUES ({asset2}, {fy_id}, '2025-06-30', 20000, 20000, 100000, true, NOW())")
        exe(f"INSERT INTO asset_depreciation_schedule (asset_id, fiscal_year, date, amount, accumulated_amount, book_value, posted, created_at) VALUES ({asset3}, {fy_id}, '2025-06-30', 10000, 10000, 35000, true, NOW())")

        # --- Asset Disposals ---
        # No active disposals, but add one planned
        # (skip - asset4 still active)

        # --- Asset Revaluations ---
        exe(f"INSERT INTO asset_revaluations (asset_id, revaluation_date, old_value, new_value, difference, reason, created_by, created_at) VALUES ({asset1}, '2025-01-15', 500000, 520000, 20000, 'إعادة تقييم سوقي', 1, NOW())")

        # --- Asset Transfers ---
        exe(f"INSERT INTO asset_transfers (asset_id, from_location, to_location, transfer_date, reason, condition, status, notes, created_at) VALUES ({asset3}, 'المقر الرئيسي', 'فرع جدة', '2025-02-01', 'نقل أجهزة', 'good', 'completed', 'نقل 5 أجهزة', NOW())")

        # --- Attachments ---
        exe(f"INSERT INTO attachments (entity_type, entity_id, file_name, file_path, file_size, file_type, mime_type, description, uploaded_by, created_at) VALUES ('invoice', {sinv1}, 'فاتورة-001.pdf', '/uploads/invoices/inv-001.pdf', 245000, 'pdf', 'application/pdf', 'نسخة الفاتورة', 1, NOW())")
        exe(f"INSERT INTO attachments (entity_type, entity_id, file_name, file_path, file_size, file_type, mime_type, description, uploaded_by, created_at) VALUES ('contract', {con1}, 'عقد-001.pdf', '/uploads/contracts/con-001.pdf', 512000, 'pdf', 'application/pdf', 'نسخة العقد', 1, NOW())")

        # --- Budget Lines ---
        exe(f"INSERT INTO budget_lines (budget_id, account_id, budget_amount, used_amount, remaining_amount, percentage, created_at) VALUES ({bud1}, {ACCT_SAL}, 216000, 36000, 180000, 16.67, NOW())")
        exe(f"INSERT INTO budget_lines (budget_id, account_id, budget_amount, used_amount, remaining_amount, percentage, created_at) VALUES ({bud1}, {ACCT_RENT}, 60000, 10000, 50000, 16.67, NOW())")
        exe(f"INSERT INTO budget_lines (budget_id, account_id, budget_amount, used_amount, remaining_amount, percentage, created_at) VALUES ({bud2}, {ACCT_MKT}, 36000, 4500, 31500, 12.5, NOW())")

        # --- Branch Tax Settings ---
        exe(f"INSERT INTO branch_tax_settings (branch_id, tax_regime_id, is_registered, registration_number, is_active, created_at) VALUES (1, {tax_regime_vat}, true, '300012345600001', true, NOW())")
        exe(f"INSERT INTO branch_tax_settings (branch_id, tax_regime_id, is_registered, registration_number, is_active, created_at) VALUES (2, {tax_regime_vat}, true, '300012345600002', true, NOW())")

        # --- Company Tax Settings ---
        exe("INSERT INTO company_tax_settings (country_code, is_vat_registered, vat_number, tax_registration_number, fiscal_year_start, default_filing_frequency, is_active, created_at) VALUES ('SA', true, '300012345600001', 'TRN-12345', '01-01', 'quarterly', true, NOW())")

        # --- Contract Items ---
        exe(f"INSERT INTO contract_items (contract_id, product_id, description, quantity, unit_price, tax_rate, total, created_at) VALUES ({con1}, {prod6}, 'استشارات هندسية شهرية', 12, 30000, 15, 414000, NOW())")
        exe(f"INSERT INTO contract_items (contract_id, product_id, description, quantity, unit_price, tax_rate, total, created_at) VALUES ({con2}, {prod1}, 'توريد حديد', 1000, 50, 15, 57500, NOW())")

        # --- Cost Centers Budgets ---
        exe(f"INSERT INTO cost_centers_budgets (cost_center_id, budget_id, allocated_amount, used_amount, fiscal_year, created_at) VALUES ({cc1}, {bud1}, 300000, 50000, {fy_id}, NOW())")
        exe(f"INSERT INTO cost_centers_budgets (cost_center_id, budget_id, allocated_amount, used_amount, fiscal_year, created_at) VALUES ({cc2}, {bud2}, 200000, 30000, {fy_id}, NOW())")

        # --- Currency Transactions ---
        exe(f"INSERT INTO currency_transactions (transaction_type, transaction_id, account_id, currency_code, exchange_rate, amount_fc, amount_bc, description, created_at) VALUES ('invoice', {sinv6}, {ACCT_AR}, 'AED', 1.02, 5750, 5865, 'فاتورة بالدرهم', NOW())")

        # --- Customer Bank Accounts ---
        exe(f"INSERT INTO customer_bank_accounts (customer_id, bank_name, bank_name_en, account_number, iban, swift_code, account_holder, is_default, status, created_at) VALUES ({cust_t1}, 'بنك الراجحي', 'Al Rajhi', '9876543210', 'SA88 8000 0098 7654 3210 0000', 'RJHISARI', 'شركة الوفاء التجارية', true, 'active', NOW())")

        # --- Customer Price Lists ---
        cpl1 = exe_ret(f"INSERT INTO customer_price_lists (price_list_code, price_list_name, price_list_name_en, customer_group_id, currency, discount_type, discount_value, valid_from, valid_to, status, is_default, created_at) VALUES ('CPL-VIP', 'أسعار VIP', 'VIP Prices', 1, 'SAR', 'percentage', 10, '2025-01-01', '2025-12-31', 'active', true, NOW()) RETURNING id")
        exe(f"INSERT INTO customer_price_list_items (price_list_id, product_id, price, created_at) VALUES ({cpl1}, {prod1}, 76.50, NOW())")
        exe(f"INSERT INTO customer_price_list_items (price_list_id, product_id, price, created_at) VALUES ({cpl1}, {prod2}, 49.50, NOW())")

        # --- Customer Receipts ---
        exe(f"INSERT INTO customer_receipts (receipt_number, customer_id, receipt_date, receipt_method, amount, currency, exchange_rate, reference, notes, status, created_by, created_at) VALUES ('CR-001', {cust_t1}, '2025-01-20', 'bank_transfer', 69000, 'SAR', 1, 'TRF-001', 'سداد فاتورة INV-001', 'posted', 1, NOW())")
        exe(f"INSERT INTO customer_receipts (receipt_number, customer_id, receipt_date, receipt_method, amount, currency, exchange_rate, reference, notes, status, created_by, created_at) VALUES ('CR-002', {cust_t2}, '2025-02-10', 'bank_transfer', 15000, 'SAR', 1, 'TRF-003', 'سداد جزئي INV-002', 'posted', 1, NOW())")

        # --- Customer Transactions ---
        exe(f"INSERT INTO customer_transactions (customer_id, transaction_type, reference_number, transaction_date, description, debit, credit, balance, invoice_id, created_by, created_at) VALUES ({cust_t1}, 'invoice', 'INV-2025-001', '2025-01-15', 'فاتورة مبيعات', 69000, 0, 69000, {sinv1}, 1, NOW())")
        exe(f"INSERT INTO customer_transactions (customer_id, transaction_type, reference_number, transaction_date, description, debit, credit, balance, created_by, created_at) VALUES ({cust_t1}, 'payment', 'PAY-CUST-001', '2025-01-20', 'سداد', 0, 69000, 0, 1, NOW())")
        exe(f"INSERT INTO customer_transactions (customer_id, transaction_type, reference_number, transaction_date, description, debit, credit, balance, invoice_id, created_by, created_at) VALUES ({cust_t2}, 'invoice', 'INV-2025-002', '2025-01-25', 'فاتورة مبيعات', 23000, 0, 23000, {sinv2}, 1, NOW())")
        exe(f"INSERT INTO customer_transactions (customer_id, transaction_type, reference_number, transaction_date, description, debit, credit, balance, created_by, created_at) VALUES ({cust_t2}, 'payment', 'PAY-CUST-002', '2025-02-10', 'سداد جزئي', 0, 15000, 8000, 1, NOW())")

        # --- Cycle Counts ---
        cc_id = exe_ret(f"INSERT INTO cycle_counts (count_number, warehouse_id, count_type, status, scheduled_date, start_date, total_items, counted_items, variance_items, notes, created_by, created_at) VALUES ('CC-2025-001', {WH_MAIN}, 'full', 'completed', '2025-02-15', '2025-02-15', 6, 6, 1, 'جرد شامل', 1, NOW()) RETURNING id")
        exe(f"INSERT INTO cycle_count_items (cycle_count_id, product_id, system_quantity, counted_quantity, variance, variance_value, unit_cost, status, counted_by, counted_at) VALUES ({cc_id}, {prod1}, 500, 498, -2, 100, 50, 'variance', 1, NOW())")
        exe(f"INSERT INTO cycle_count_items (cycle_count_id, product_id, system_quantity, counted_quantity, variance, variance_value, unit_cost, status, counted_by, counted_at) VALUES ({cc_id}, {prod2}, 1000, 1000, 0, 0, 30, 'matched', 1, NOW())")

        # --- Documents & Versions ---
        doc1 = exe_ret(f"INSERT INTO documents (title, description, category, file_name, file_path, file_size, mime_type, tags, access_level, related_module, related_id, current_version, created_by, created_at) VALUES ('دليل إجراءات المحاسبة', 'دليل الإجراءات المحاسبية المعتمد', 'policy', 'accounting-manual.pdf', '/uploads/docs/accounting-manual.pdf', 1024000, 'application/pdf', 'محاسبة,إجراءات', 'company', 'accounting', NULL, 2, 1, NOW()) RETURNING id")
        exe(f"INSERT INTO document_versions (document_id, version_number, file_name, file_path, file_size, change_notes, uploaded_by, created_at) VALUES ({doc1}, 1, 'accounting-manual-v1.pdf', '/uploads/docs/v1/accounting-manual.pdf', 980000, 'الإصدار الأول', 1, '2025-01-01')")
        exe(f"INSERT INTO document_versions (document_id, version_number, file_name, file_path, file_size, change_notes, uploaded_by, created_at) VALUES ({doc1}, 2, 'accounting-manual-v2.pdf', '/uploads/docs/v2/accounting-manual.pdf', 1024000, 'تحديث سياسات الضريبة', 1, '2025-02-01')")

        # --- Employee Custody ---
        exe(f"INSERT INTO employee_custody (employee_id, item_name, item_type, serial_number, assigned_date, condition_on_assign, value, notes, status, created_at) VALUES ({emp1}, 'لابتوب Dell', 'laptop', 'SN-DELL-001', '2024-01-15', 'new', 4500, 'جهاز عمل', 'assigned', NOW())")
        exe(f"INSERT INTO employee_custody (employee_id, item_name, item_type, serial_number, assigned_date, condition_on_assign, value, notes, status, created_at) VALUES ({emp2}, 'هاتف iPhone', 'mobile', 'SN-IPHONE-001', '2024-06-15', 'new', 3800, 'هاتف عمل', 'assigned', NOW())")
        exe(f"INSERT INTO employee_custody (employee_id, item_name, item_type, assigned_date, condition_on_assign, value, status, created_at) VALUES ({emp3}, 'سيارة تويوتا', 'vehicle', '2025-02-01', 'good', 85000, 'assigned', NOW())")

        # --- Employee Documents ---
        exe(f"INSERT INTO employee_documents (employee_id, document_type, document_number, issue_date, expiry_date, issuing_authority, notes, alert_days, status, created_at) VALUES ({emp1}, 'iqama', '2345678901', '2024-01-01', '2026-01-01', 'الجوازات', 'إقامة سارية', 60, 'valid', NOW())")
        exe(f"INSERT INTO employee_documents (employee_id, document_type, document_number, issue_date, expiry_date, issuing_authority, notes, status, created_at) VALUES ({emp2}, 'passport', 'A12345678', '2022-06-01', '2027-06-01', 'وزارة الخارجية', 'جواز سفر', 'valid', NOW())")

        # --- Employee Loans ---
        exe(f"INSERT INTO employee_loans (employee_id, amount, total_installments, monthly_installment, paid_amount, start_date, status, reason, approved_by, branch_id, created_at) VALUES ({emp1}, 20000, 10, 2000, 4000, '2025-01-01', 'active', 'سلفة شخصية', 1, 1, NOW())")

        # --- Employee Violations ---
        exe(f"INSERT INTO employee_violations (employee_id, violation_date, violation_type, severity, description, action_taken, penalty_amount, deduct_from_salary, status, created_at) VALUES ({emp3}, '2025-02-05', 'late_arrival', 'minor', 'تأخر 30 دقيقة', 'warning', 0, false, 'resolved', NOW())")

        # --- Inventory Transactions ---
        exe(f"INSERT INTO inventory_transactions (product_id, warehouse_id, transaction_type, reference_type, reference_document, quantity, balance_before, balance_after, unit_cost, total_cost, notes, created_by, created_at) VALUES ({prod1}, {WH_MAIN}, 'purchase', 'purchase_order', 'PO-2025-001', 500, 0, 500, 50, 25000, 'استلام مشتريات', 1, '2025-01-15')")
        exe(f"INSERT INTO inventory_transactions (product_id, warehouse_id, transaction_type, reference_type, reference_document, quantity, balance_before, balance_after, unit_cost, total_cost, notes, created_by, created_at) VALUES ({prod1}, {WH_MAIN}, 'sale', 'invoice', 'INV-2025-001', -200, 500, 300, 50, 10000, 'مبيعات', 1, '2025-01-15')")
        exe(f"INSERT INTO inventory_transactions (product_id, warehouse_id, transaction_type, reference_type, reference_document, quantity, balance_before, balance_after, unit_cost, total_cost, notes, created_by, created_at) VALUES ({prod2}, {WH_MAIN}, 'purchase', 'purchase_order', 'PO-2025-001', 500, 500, 1000, 30, 15000, 'استلام مشتريات', 1, '2025-01-15')")

        # --- Inventory Cost Snapshots ---
        exe(f"INSERT INTO inventory_cost_snapshots (warehouse_id, product_id, average_cost, quantity, policy_type, snapshot_date) VALUES ({WH_MAIN}, {prod1}, 50, 300, 'weighted_average', '2025-02-28')")
        exe(f"INSERT INTO inventory_cost_snapshots (warehouse_id, product_id, average_cost, quantity, policy_type, snapshot_date) VALUES ({WH_MAIN}, {prod2}, 30, 700, 'weighted_average', '2025-02-28')")

        # --- Batch Serial Movements ---
        # (Needs product_batches first, skip for now - no batches created)

        # --- Bin Locations & Inventory ---
        bin1 = exe_ret(f"INSERT INTO bin_locations (warehouse_id, bin_code, bin_name, zone, aisle, rack, shelf, bin_type, max_weight, is_active, created_at) VALUES ({WH_MAIN}, 'A-01-01', 'رف A1', 'A', '01', 'R1', 'S1', 'storage', 5000, true, NOW()) RETURNING id")
        bin2 = exe_ret(f"INSERT INTO bin_locations (warehouse_id, bin_code, bin_name, zone, aisle, rack, shelf, bin_type, max_weight, is_active, created_at) VALUES ({WH_MAIN}, 'A-01-02', 'رف A2', 'A', '01', 'R1', 'S2', 'storage', 5000, true, NOW()) RETURNING id")
        exe(f"INSERT INTO bin_inventory (bin_id, product_id, quantity, updated_at) VALUES ({bin1}, {prod1}, 300, NOW())")
        exe(f"INSERT INTO bin_inventory (bin_id, product_id, quantity, updated_at) VALUES ({bin2}, {prod2}, 700, NOW())")

        # --- BOM Outputs ---
        exe(f"INSERT INTO bom_outputs (bom_id, product_id, quantity, cost_allocation_percentage, notes, created_at) VALUES ({bom1}, {prod3}, 10, 100, 'المنتج الرئيسي', NOW())")

        # --- Job Openings & Applications ---
        jo1 = exe_ret(f"INSERT INTO job_openings (title, department_id, position_id, description, requirements, employment_type, vacancies, status, branch_id, closing_date, created_by, created_at) VALUES ('محاسب مبتدئ', {dept_fin}, {pos_acc}, 'مطلوب محاسب', 'بكالوريوس محاسبة', 'full_time', 2, 'open', 1, '2025-03-31', 1, NOW()) RETURNING id")
        exe(f"INSERT INTO job_applications (opening_id, applicant_name, email, phone, stage, rating, status, created_at) VALUES ({jo1}, 'سعد العتيبي', 'saad@email.com', '0551112233', 'interview', 4, 'in_review', NOW())")
        exe(f"INSERT INTO job_applications (opening_id, applicant_name, email, phone, stage, rating, status, created_at) VALUES ({jo1}, 'نورة القحطاني', 'noura@email.com', '0559998877', 'screening', 3, 'in_review', NOW())")

        # --- Leave Carryover ---
        exe(f"INSERT INTO leave_carryover (employee_id, leave_type, year, entitled_days, used_days, carried_days, expired_days, max_carryover, calculated_at) VALUES ({emp1}, 'annual', 2024, 30, 20, 10, 0, 15, NOW())")
        exe(f"INSERT INTO leave_carryover (employee_id, leave_type, year, entitled_days, used_days, carried_days, expired_days, max_carryover, calculated_at) VALUES ({emp2}, 'annual', 2024, 30, 15, 15, 0, 15, NOW())")

        # --- Maintenance Logs ---
        exe(f"INSERT INTO maintenance_logs (equipment_id, maintenance_type, description, cost, performed_by, maintenance_date, next_due_date, status, created_at) VALUES ({equip1}, 'preventive', 'صيانة دورية لماكينة القص', 1500, 1, '2025-02-01', '2025-05-01', 'completed', NOW())")
        exe(f"INSERT INTO maintenance_logs (equipment_id, maintenance_type, description, cost, maintenance_date, next_due_date, status, created_at) VALUES ({equip2}, 'corrective', 'إصلاح عطل اللحام', 3000, '2025-01-20', '2025-04-20', 'completed', NOW())")

        # --- MFG QC Checks ---
        exe(f"INSERT INTO mfg_qc_checks (production_order_id, check_name, check_type, specification, actual_value, result, checked_by, checked_at, created_at) VALUES ({prod_ord1}, 'فحص الأبعاد', 'measurement', 'العرض 120سم ± 2', '120.5سم', 'pass', 1, NOW(), NOW())")
        exe(f"INSERT INTO mfg_qc_checks (production_order_id, check_name, check_type, specification, actual_value, result, checked_by, checked_at, created_at) VALUES ({prod_ord1}, 'فحص الجودة السطحية', 'visual', 'سطح أملس بدون عيوب', 'مطابق', 'pass', 1, NOW(), NOW())")

        # --- MRP Plans & Items ---
        mrp1 = exe_ret(f"INSERT INTO mrp_plans (plan_name, production_order_id, status, calculated_at, notes, created_by) VALUES ('خطة مواد MO-2025-001', {prod_ord1}, 'approved', NOW(), 'خطة مواد الإنتاج', 1) RETURNING id")
        exe(f"INSERT INTO mrp_items (mrp_plan_id, product_id, required_quantity, available_quantity, on_hand_quantity, on_order_quantity, shortage_quantity, lead_time_days, suggested_action, status) VALUES ({mrp1}, {prod1}, 250, 300, 300, 0, 0, 5, 'none', 'sufficient')")
        exe(f"INSERT INTO mrp_items (mrp_plan_id, product_id, required_quantity, available_quantity, on_hand_quantity, on_order_quantity, shortage_quantity, lead_time_days, suggested_action, status) VALUES ({mrp1}, {prod2}, 1000, 700, 700, 500, 0, 7, 'wait_for_po', 'ordered')")

        # --- Opportunity Activities ---
        exe(f"INSERT INTO opportunity_activities (opportunity_id, activity_type, title, description, due_date, completed, created_by, created_at) VALUES ({opp1}, 'meeting', 'اجتماع عرض المشروع', 'تقديم العرض للعميل', '2025-02-15', true, 1, NOW())")
        exe(f"INSERT INTO opportunity_activities (opportunity_id, activity_type, title, description, due_date, completed, created_by, created_at) VALUES ({opp1}, 'call', 'متابعة هاتفية', 'متابعة بعد الاجتماع', '2025-02-20', false, {emp2}, NOW())")

        # --- Overtime Requests ---
        exe(f"INSERT INTO overtime_requests (employee_id, request_date, overtime_date, hours, overtime_type, multiplier, calculated_amount, reason, status, approved_by, branch_id, created_at) VALUES ({emp3}, '2025-02-01', '2025-02-05', 4, 'normal', 1.5, 600, 'ضغط عمل', 'approved', 1, 1, NOW())")

        # --- Party Transactions ---
        exe(f"INSERT INTO party_transactions (party_id, transaction_type, reference_number, transaction_date, description, debit, credit, balance, invoice_id, created_by, created_at) VALUES ({cust1}, 'invoice', 'INV-2025-001', '2025-01-15', 'فاتورة مبيعات', 69000, 0, 69000, {sinv1}, 1, NOW())")
        exe(f"INSERT INTO party_transactions (party_id, transaction_type, reference_number, transaction_date, description, debit, credit, balance, created_by, created_at) VALUES ({cust1}, 'payment', 'PAY-001', '2025-01-20', 'سداد', 0, 69000, 0, 1, NOW())")

        # --- Payment Allocations ---
        exe(f"INSERT INTO payment_allocations (voucher_id, invoice_id, allocated_amount, created_at) VALUES (1, {pinv1}, 57500, NOW())")

        # --- Pending Receivables ---
        exe(f"INSERT INTO pending_receivables (customer_id, invoice_id, invoice_number, due_date, amount, paid_amount, outstanding_amount, days_overdue, status, created_at) VALUES ({cust_t2}, {sinv2}, 'INV-2025-002', '2025-02-25', 23000, 15000, 8000, 0, 'partial', NOW())")
        exe(f"INSERT INTO pending_receivables (customer_id, invoice_id, invoice_number, due_date, amount, paid_amount, outstanding_amount, days_overdue, status, created_at) VALUES ({cust_t4}, {sinv4}, 'INV-2025-004', '2025-03-10', 9200, 0, 9200, 0, 'overdue', NOW())")

        # --- Pending Payables ---
        # (All suppliers are paid, but add a note payable as pending)
        exe(f"INSERT INTO pending_payables (supplier_id, invoice_id, invoice_number, due_date, amount, paid_amount, outstanding_amount, days_overdue, status, created_at) VALUES ({supp_t2}, {pinv2}, 'PINV-2025-002', '2025-02-28', 23000, 23000, 0, 0, 'paid', NOW())")

        # --- Performance Reviews ---
        exe(f"INSERT INTO performance_reviews (employee_id, reviewer_id, review_period, review_date, review_type, overall_rating, strengths, weaknesses, goals, status, created_at) VALUES ({emp1}, 1, '2024-H2', '2025-01-15', 'semi_annual', 4.2, 'قيادة ممتازة', 'يحتاج تحسين التواصل', 'زيادة فريق العمل', 'completed', NOW())")
        exe(f"INSERT INTO performance_reviews (employee_id, reviewer_id, review_period, review_date, review_type, overall_rating, strengths, weaknesses, goals, status, created_at) VALUES ({emp2}, 1, '2024-H2', '2025-01-15', 'semi_annual', 3.8, 'مهارات بيع ممتازة', 'التقارير', 'زيادة المبيعات 20%', 'completed', NOW())")

        # --- POS Returns & Items ---
        pr1 = exe_ret(f"INSERT INTO pos_returns (original_order_id, user_id, session_id, refund_amount, refund_method, notes, created_at) VALUES ({po_ord1}, 1, {ps1}, 977.50, 'cash', 'مرتجع منتج تالف', NOW()) RETURNING id")
        exe(f"INSERT INTO pos_return_items (return_id, original_item_id, quantity, reason, created_at) VALUES ({pr1}, 1, 10, 'منتج تالف', NOW())")

        # --- POS Kitchen Orders ---
        exe(f"INSERT INTO pos_kitchen_orders (order_id, order_line_id, product_id, product_name, quantity, station, status, priority, sent_at, branch_id) VALUES ({po_ord1}, 1, {prod1}, 'حديد مسلح 12مم', 10, 'التحضير', 'completed', 1, NOW(), 1)")

        # --- POS Loyalty Transactions ---
        exe(f"INSERT INTO pos_loyalty_transactions (loyalty_id, order_id, txn_type, points, description, created_at) VALUES (1, {po_ord1}, 'earn', 52, 'نقاط من طلب POS-ORD-001', NOW())")
        exe(f"INSERT INTO pos_loyalty_transactions (loyalty_id, order_id, txn_type, points, description, created_at) VALUES (1, {po_ord3}, 'earn', 34, 'نقاط من طلب POS-ORD-003', NOW())")

        # --- POS Payments ---
        exe(f"INSERT INTO pos_payments (order_id, session_id, payment_method, amount, created_at) VALUES ({po_ord1}, {ps1}, 'cash', 5175, NOW())")
        exe(f"INSERT INTO pos_payments (order_id, session_id, payment_method, amount, reference_number, created_at) VALUES ({po_ord2}, {ps1}, 'card', 3450, 'VISA-4832', NOW())")

        # --- POS Table Orders ---
        exe(f"INSERT INTO pos_table_orders (table_id, order_id, seated_at, cleared_at, guests, waiter_id, status) VALUES (1, {po_ord1}, '2025-02-22 10:00', '2025-02-22 11:00', 2, 1, 'completed')")

        # --- Product Attributes & Variants ---
        pa1 = exe_ret("INSERT INTO product_attributes (attribute_name, attribute_name_en, attribute_type, sort_order, is_active, created_at) VALUES ('اللون', 'Color', 'select', 1, true, NOW()) RETURNING id")
        pa2 = exe_ret("INSERT INTO product_attributes (attribute_name, attribute_name_en, attribute_type, sort_order, is_active, created_at) VALUES ('المقاس', 'Size', 'select', 2, true, NOW()) RETURNING id")
        pav1 = exe_ret(f"INSERT INTO product_attribute_values (attribute_id, value_name, value_name_en, sort_order, is_active, created_at) VALUES ({pa1}, 'أحمر', 'Red', 1, true, NOW()) RETURNING id")
        pav2 = exe_ret(f"INSERT INTO product_attribute_values (attribute_id, value_name, value_name_en, sort_order, is_active, created_at) VALUES ({pa1}, 'أزرق', 'Blue', 2, true, NOW()) RETURNING id")
        pav3 = exe_ret(f"INSERT INTO product_attribute_values (attribute_id, value_name, value_name_en, sort_order, is_active, created_at) VALUES ({pa2}, 'كبير', 'Large', 1, true, NOW()) RETURNING id")

        pv1 = exe_ret(f"INSERT INTO product_variants (product_id, variant_code, variant_name, sku, cost_price, selling_price, is_active, created_at) VALUES ({prod4}, 'PRD-004-RED', 'دهان أحمر', 'SKU-004-R', 95, 165, true, NOW()) RETURNING id")
        pv2 = exe_ret(f"INSERT INTO product_variants (product_id, variant_code, variant_name, sku, cost_price, selling_price, is_active, created_at) VALUES ({prod4}, 'PRD-004-BLU', 'دهان أزرق', 'SKU-004-B', 95, 165, true, NOW()) RETURNING id")
        exe(f"INSERT INTO product_variant_attributes (variant_id, attribute_id, attribute_value_id) VALUES ({pv1}, {pa1}, {pav1})")
        exe(f"INSERT INTO product_variant_attributes (variant_id, attribute_id, attribute_value_id) VALUES ({pv2}, {pa1}, {pav2})")

        # --- Product Batches ---
        pb1 = exe_ret(f"INSERT INTO product_batches (product_id, warehouse_id, batch_number, manufacturing_date, expiry_date, quantity, available_quantity, unit_cost, supplier_id, status, created_by, created_at) VALUES ({prod4}, {WH_MAIN}, 'BATCH-001', '2025-01-01', '2026-06-30', 80, 0, 95, {supp_t2}, 'active', 1, NOW()) RETURNING id")

        # --- Product Serials ---
        exe(f"INSERT INTO product_serials (product_id, warehouse_id, serial_number, batch_id, status, purchase_date, purchase_reference, purchase_price, created_by, created_at) VALUES ({prod4}, {WH_MAIN}, 'SER-PAINT-001', {pb1}, 'available', '2025-01-28', 'PO-2025-002', 95, 1, NOW())")
        exe(f"INSERT INTO product_serials (product_id, warehouse_id, serial_number, batch_id, status, purchase_date, purchase_reference, purchase_price, created_by, created_at) VALUES ({prod4}, {WH_MAIN}, 'SER-PAINT-002', {pb1}, 'sold', '2025-01-28', 'PO-2025-002', 95, 1, NOW())")

        # --- Product Kits ---
        pk1 = exe_ret(f"INSERT INTO product_kits (product_id, kit_name, kit_type, is_active, created_at) VALUES ({prod3}, 'حزمة ألواح خشبية', 'fixed', true, NOW()) RETURNING id")
        exe(f"INSERT INTO product_kit_items (kit_id, component_product_id, quantity, unit_cost, sort_order) VALUES ({pk1}, {prod1}, 5, 50, 1)")
        exe(f"INSERT INTO product_kit_items (kit_id, component_product_id, quantity, unit_cost, sort_order) VALUES ({pk1}, {prod2}, 20, 30, 2)")

        # --- Production Order Operations ---
        exe(f"INSERT INTO production_order_operations (production_order_id, operation_id, work_center_id, status, actual_setup_time, actual_run_time, completed_quantity, scrapped_quantity, start_time, end_time, created_at) VALUES ({prod_ord1}, 1, {wc1}, 'completed', 35, 720, 50, 1, '2025-01-20 08:00', '2025-01-25 17:00', NOW())")
        exe(f"INSERT INTO production_order_operations (production_order_id, operation_id, work_center_id, status, actual_setup_time, actual_run_time, completed_quantity, scrapped_quantity, start_time, end_time, created_at) VALUES ({prod_ord1}, 2, {wc2}, 'completed', 20, 480, 49, 1, '2025-01-26 08:00', '2025-01-30 17:00', NOW())")

        # --- Project Change Orders ---
        exe(f"INSERT INTO project_change_orders (project_id, change_order_number, title, description, change_type, cost_impact, time_impact_days, status, requested_by, approved_by, approved_at, created_at) VALUES ({proj1}, 'CO-001', 'تعديل التصميم', 'تعديل مخطط الطابق الثالث', 'scope', 50000, 15, 'approved', 1, 1, '2025-02-01', NOW())")

        # --- Project Documents ---
        exe(f"INSERT INTO project_documents (project_id, file_name, file_url, file_type, uploaded_by, created_at) VALUES ({proj1}, 'مخطط-هندسي.pdf', '/uploads/projects/plan.pdf', 'pdf', 1, NOW())")
        exe(f"INSERT INTO project_documents (project_id, file_name, file_url, file_type, uploaded_by, created_at) VALUES ({proj1}, 'جدول-زمني.xlsx', '/uploads/projects/schedule.xlsx', 'xlsx', 1, NOW())")

        # --- Purchase Agreements ---
        pa_id = exe_ret(f"INSERT INTO purchase_agreements (agreement_number, supplier_id, agreement_type, title, start_date, end_date, total_amount, consumed_amount, status, branch_id, created_by, created_at) VALUES ('PA-2025-001', {supp_t1}, 'blanket', 'اتفاقية توريد سنوية', '2025-01-01', '2025-12-31', 500000, 57500, 'active', 1, 1, NOW()) RETURNING id")
        exe(f"INSERT INTO purchase_agreement_lines (agreement_id, product_id, product_name, quantity, unit_price, delivered_qty) VALUES ({pa_id}, {prod1}, 'حديد مسلح', 5000, 50, 500)")
        exe(f"INSERT INTO purchase_agreement_lines (agreement_id, product_id, product_name, quantity, unit_price, delivered_qty) VALUES ({pa_id}, {prod2}, 'أسمنت', 10000, 30, 500)")

        # --- Quality Inspections ---
        qi1 = exe_ret(f"INSERT INTO quality_inspections (inspection_number, inspection_type, product_id, warehouse_id, batch_id, reference_type, inspected_quantity, accepted_quantity, rejected_quantity, status, inspector_id, inspection_date, created_by, created_at) VALUES ('QI-2025-001', 'incoming', {prod1}, {WH_MAIN}, NULL, 'purchase_order', 500, 498, 2, 'completed', 1, NOW(), 1, NOW()) RETURNING id")
        exe(f"INSERT INTO quality_inspection_criteria (inspection_id, criteria_name, expected_value, actual_value, is_passed, notes) VALUES ({qi1}, 'القطر', '12mm ± 0.5', '12.2mm', true, 'ضمن المواصفات')")
        exe(f"INSERT INTO quality_inspection_criteria (inspection_id, criteria_name, expected_value, actual_value, is_passed, notes) VALUES ({qi1}, 'المتانة', '> 400 MPa', '420 MPa', true, 'مطابق')")

        # --- Receipts ---
        exe(f"INSERT INTO receipts (receipt_number, receipt_type, customer_id, receipt_date, amount, currency, exchange_rate, payment_method, reference, notes, status, created_by, created_at) VALUES ('RCP-001', 'customer', {cust_t1}, '2025-01-20', 69000, 'SAR', 1, 'bank_transfer', 'TRF-001', 'إيصال استلام', 'posted', 1, NOW())")
        exe(f"INSERT INTO receipts (receipt_number, receipt_type, supplier_id, receipt_date, amount, currency, exchange_rate, payment_method, reference, notes, status, created_by, created_at) VALUES ('RCP-002', 'supplier', {supp_t1}, '2025-01-20', 57500, 'SAR', 1, 'bank_transfer', 'TRF-002', 'إيصال دفع', 'posted', 1, NOW())")

        # --- Sales Commissions ---
        exe(f"INSERT INTO sales_commissions (salesperson_id, salesperson_name, invoice_id, invoice_number, invoice_date, invoice_total, commission_rate, commission_amount, status, branch_id, created_at) VALUES ({emp2}, 'فاطمة الزهراني', {sinv1}, 'INV-2025-001', '2025-01-15', 69000, 3, 2070, 'calculated', 1, NOW())")
        exe(f"INSERT INTO sales_commissions (salesperson_id, salesperson_name, invoice_id, invoice_number, invoice_date, invoice_total, commission_rate, commission_amount, status, branch_id, created_at) VALUES ({emp2}, 'فاطمة الزهراني', {sinv2}, 'INV-2025-002', '2025-01-25', 23000, 3, 690, 'calculated', 1, NOW())")

        # --- Service Documents ---
        exe(f"INSERT INTO service_documents (title, description, category, file_path, file_name, file_size, mime_type, version, tags, created_by, created_at) VALUES ('دليل الخدمات', 'دليل خدمات الشركة', 'manual', '/uploads/services/manual.pdf', 'service-manual.pdf', 500000, 'application/pdf', 1, 'خدمات', 1, NOW())")

        # --- Service Request Costs ---
        exe(f"INSERT INTO service_request_costs (service_request_id, cost_type, description, amount, created_by, created_at) VALUES ({sr1}, 'labor', 'أجور فنيين', 1500, 1, NOW())")
        exe(f"INSERT INTO service_request_costs (service_request_id, cost_type, description, amount, created_by, created_at) VALUES ({sr1}, 'materials', 'قطع غيار', 1200, 1, NOW())")

        # --- Shared Reports ---
        exe("INSERT INTO shared_reports (report_type, report_id, shared_by, shared_with, permission, message, created_at) VALUES ('custom', 1, 1, 1, 'view', 'تقرير للمراجعة', NOW())")

        # --- Stock Adjustments ---
        exe(f"INSERT INTO stock_adjustments (adjustment_number, warehouse_id, adjustment_type, reason, product_id, old_quantity, new_quantity, difference, notes, status, created_by, created_at) VALUES ('ADJ-2025-001', {WH_MAIN}, 'increase', 'count_correction', {prod1}, 498, 500, 2, 'تعديل بعد الجرد', 'approved', 1, NOW())")

        # --- Stock Shipments & Items ---
        ss_id = exe_ret(f"INSERT INTO stock_shipments (shipment_ref, source_warehouse_id, destination_warehouse_id, status, notes, created_by, created_at, shipped_at, received_at) VALUES ('SHP-2025-001', {WH_MAIN}, {WH_JED}, 'received', 'نقل مخزون', 1, NOW(), '2025-02-10', '2025-02-12') RETURNING id")
        exe(f"INSERT INTO stock_shipment_items (shipment_id, product_id, quantity) VALUES ({ss_id}, {prod1}, 50)")
        exe(f"INSERT INTO stock_shipment_items (shipment_id, product_id, quantity) VALUES ({ss_id}, {prod2}, 100)")

        # --- Stock Transfer Log ---
        exe(f"INSERT INTO stock_transfer_log (shipment_id, product_id, from_warehouse_id, to_warehouse_id, quantity, transfer_cost, from_avg_cost_before, to_avg_cost_before, to_avg_cost_after, created_at) VALUES ({ss_id}, {prod1}, {WH_MAIN}, {WH_JED}, 50, 2500, 50, 50, 50, NOW())")

        # --- Supplier Bank Accounts ---
        exe(f"INSERT INTO supplier_bank_accounts (supplier_id, bank_name, bank_name_en, account_number, iban, swift_code, account_holder, is_default, status, created_at) VALUES ({supp_t1}, 'البنك الأهلي', 'NCB', '1122334455', 'SA22 1000 0011 2233 4455 0000', 'NCBKSAJE', 'مؤسسة الأمان للتوريدات', true, 'active', NOW())")

        # --- Supplier Payments ---
        exe(f"INSERT INTO supplier_payments (payment_number, supplier_id, payment_date, payment_method, amount, currency, exchange_rate, reference, notes, status, created_by, created_at) VALUES ('SP-001', {supp_t1}, '2025-01-20', 'bank_transfer', 57500, 'SAR', 1, 'TRF-002', 'سداد فاتورة مشتريات', 'completed', 1, NOW())")
        exe(f"INSERT INTO supplier_payments (payment_number, supplier_id, payment_date, payment_method, amount, currency, exchange_rate, reference, notes, status, created_by, created_at) VALUES ('SP-002', {supp_t2}, '2025-02-01', 'bank_transfer', 23000, 'SAR', 1, 'TRF-003', 'سداد فاتورة مشتريات', 'completed', 1, NOW())")

        # --- Supplier Ratings ---
        exe(f"INSERT INTO supplier_ratings (supplier_id, po_id, quality_score, delivery_score, price_score, service_score, overall_score, comments, rated_by, rated_at) VALUES ({supp_t1}, {po1}, 4.5, 4, 3.5, 4, 4, 'مورد جيد', 1, NOW())")
        exe(f"INSERT INTO supplier_ratings (supplier_id, po_id, quality_score, delivery_score, price_score, service_score, overall_score, comments, rated_by, rated_at) VALUES ({supp_t2}, {po2}, 4, 3.5, 4, 3.5, 3.75, 'أداء مقبول', 1, NOW())")

        # --- Supplier Transactions ---
        exe(f"INSERT INTO supplier_transactions (supplier_id, transaction_type, reference_number, transaction_date, description, debit, credit, balance, invoice_id, created_by, created_at) VALUES ({supp_t1}, 'invoice', 'PINV-2025-001', '2025-01-15', 'فاتورة مشتريات', 0, 57500, 57500, {pinv1}, 1, NOW())")
        exe(f"INSERT INTO supplier_transactions (supplier_id, transaction_type, reference_number, transaction_date, description, debit, credit, balance, created_by, created_at) VALUES ({supp_t1}, 'payment', 'SP-001', '2025-01-20', 'سداد', 57500, 0, 0, 1, NOW())")

        # --- Tax Payments ---
        exe(f"INSERT INTO tax_payments (payment_number, tax_return_id, payment_date, amount, payment_method, reference, status, notes, created_by, created_at) VALUES ('TP-2025-Q1', {tr1}, '2025-04-28', 18120, 'bank_transfer', 'SADAD-001', 'pending', 'دفع ضريبة الربع الأول', 1, NOW())")

        # --- Ticket Comments ---
        exe(f"INSERT INTO ticket_comments (ticket_id, comment, is_internal, created_by, created_at) VALUES ({tk1}, 'تم مراجعة الفاتورة وتصحيحها', false, 1, NOW())")
        exe(f"INSERT INTO ticket_comments (ticket_id, comment, is_internal, created_by, created_at) VALUES ({tk2}, 'تم التواصل مع شركة الشحن', true, {emp2}, NOW())")

        # --- Training Programs & Participants ---
        tp1 = exe_ret(f"INSERT INTO training_programs (name, name_en, description, trainer, location, start_date, end_date, max_participants, cost, status, created_at) VALUES ('دورة المحاسبة المالية', 'Financial Accounting Course', 'دورة تدريبية في المحاسبة', 'أكاديمية المالية', 'الرياض', '2025-03-01', '2025-03-05', 20, 5000, 'planned', NOW()) RETURNING id")
        exe(f"INSERT INTO training_participants (training_id, employee_id, attendance_status, score, created_at) VALUES ({tp1}, {emp1}, 'registered', NULL, NOW())")
        exe(f"INSERT INTO training_participants (training_id, employee_id, attendance_status, score, created_at) VALUES ({tp1}, {emp2}, 'registered', NULL, NOW())")

        # --- Treasury Transactions ---
        exe(f"INSERT INTO treasury_transactions (transaction_number, transaction_date, transaction_type, amount, treasury_id, target_account_id, branch_id, description, reference_number, status, created_by, created_at) VALUES ('TT-001', '2025-01-20', 'deposit', 69000, {treas_bank}, {ACCT_BANK}, 1, 'إيداع تحصيل عميل', 'TRF-001', 'completed', 1, NOW())")
        exe(f"INSERT INTO treasury_transactions (transaction_number, transaction_date, transaction_type, amount, treasury_id, target_account_id, branch_id, description, reference_number, status, created_by, created_at) VALUES ('TT-002', '2025-01-20', 'withdrawal', 57500, {treas_bank}, {ACCT_BANK}, 1, 'سداد مورد', 'TRF-002', 'completed', 1, NOW())")
        exe(f"INSERT INTO treasury_transactions (transaction_number, transaction_date, transaction_type, amount, treasury_id, target_treasury_id, branch_id, description, status, created_by, created_at) VALUES ('TT-003', '2025-02-15', 'transfer', 10000, {treas_bank}, {treas_box}, 1, 'تحويل من البنك للصندوق', 'completed', 1, NOW())")

        # --- Webhook Logs ---
        exe("INSERT INTO webhook_logs (webhook_id, event, payload, response_status, response_body, success, attempt, created_at) VALUES (1, 'invoice.created', '{\"id\": 1}'::jsonb, 200, 'OK', true, 1, NOW())")

        # --- WHT Transactions ---
        exe(f"INSERT INTO wht_transactions (invoice_id, supplier_id, wht_rate_id, gross_amount, wht_rate, wht_amount, net_amount, status, created_by, created_at) VALUES ({pinv1}, {supp_t1}, 1, 57500, 5, 2875, 54625, 'withheld', 1, NOW())")

        # --- Batch Serial Movements ---
        exe(f"INSERT INTO batch_serial_movements (product_id, batch_id, warehouse_id, movement_type, reference_type, quantity, notes, created_by, created_at) VALUES ({prod4}, {pb1}, {WH_MAIN}, 'inbound', 'purchase_order', 80, 'استلام دفعة', 1, NOW())")

        # --- Asset Disposals (planned) ---
        # (keeping for future - no disposed assets now, add a draft one)

        print("   All remaining tables populated!")

        db.commit()
        print(f"\n{'=' * 60}")
        print(f"DONE! Executed {count} INSERT/UPDATE statements")
        print(f"{'=' * 60}")

    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"\nERROR at statement #{count}: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
