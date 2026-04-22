"""
Comprehensive data population script for ALL empty tables.
Inserts diverse, realistic Arabic test data for thorough system testing.
Company: 39a597c9
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import get_db_connection
from sqlalchemy import text

COMPANY_ID = '39a597c9'

def run():
    db = get_db_connection(COMPANY_ID)
    try:
        # ============================================================
        # REFERENCE IDS (from existing data)
        # ============================================================
        USER_ID = 1
        BRANCH_IDS = [1, 2, 3]
        DEPT_IDS = [7, 8, 9]
        EMP_IDS = [1, 2, 3]
        CUST_IDS = [5, 6, 7, 8, 9]
        SUPP_IDS = [1, 2, 3, 4]
        PARTY_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        PROD_IDS = [1, 2, 3, 4, 5, 6]
        WH_IDS = [1, 2, 3, 4]
        ASSET_IDS = [1, 2, 3, 4, 5, 6, 7]
        BUDGET_IDS = [2, 3]
        CC_IDS = [1, 2, 3, 4]
        INV_IDS = [1, 2, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
        PROJ_IDS = [4, 5, 6]
        TASK_IDS = [1, 2, 3]
        SR_IDS = [1, 2, 3, 4]
        TICKET_IDS = [4, 5, 6]
        OPP_IDS = [1, 2, 3]
        EQUIP_IDS = [3, 4]
        BOM_IDS = [1]
        PO_IDS = [1]
        COST_POL_ID = 1
        FY_ID = 1
        WF_IDS = [1, 2]
        CURR_IDS = [1, 2, 3, 4]
        TAX_REG_IDS = [1, 2, 3, 4]
        CONTRACT_IDS = [1, 2]
        SO_IDS = [1, 2]
        PUR_IDS = [1, 2, 3, 4, 5]
        RFQ_ID = 1
        SQ_ID = 1
        PAYROLL_IDS = [1, 2]
        POS_IDS = [7, 8, 9]
        TREAS_IDS = [1, 2, 3, 4, 5, 6]
        WC_IDS = [1, 2, 3]
        ROUTE_ID = 1
        RET_IDS = [1, 8, 9]
        PV_IDS = [1, 6, 7, 8, 9, 10, 11, 12, 13, 14]
        WHT_IDS = [1, 2, 3, 4, 5, 6, 7, 8]
        EXP_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

        count = 0

        def exe(sql, params=None):
            nonlocal count
            db.execute(text(sql), params or {})
            count += 1

        # ============================================================
        # 1. ASSET MANAGEMENT
        # ============================================================
        print("1. Asset Management...")

        # asset_categories
        exe("""INSERT INTO asset_categories (category_code, category_name, category_name_en, description, depreciation_rate, useful_life)
               VALUES ('CAT-LAND', 'أراضي', 'Land', 'أراضي ومباني', 0, 0)""")
        exe("""INSERT INTO asset_categories (category_code, category_name, category_name_en, description, depreciation_rate, useful_life)
               VALUES ('CAT-BLDG', 'مباني', 'Buildings', 'مباني ومنشآت', 5, 20)""")
        exe("""INSERT INTO asset_categories (category_code, category_name, category_name_en, description, depreciation_rate, useful_life)
               VALUES ('CAT-VEHI', 'مركبات', 'Vehicles', 'سيارات ومركبات', 20, 5)""")
        exe("""INSERT INTO asset_categories (category_code, category_name, category_name_en, description, depreciation_rate, useful_life)
               VALUES ('CAT-FURN', 'أثاث', 'Furniture', 'أثاث ومفروشات', 10, 10)""")
        exe("""INSERT INTO asset_categories (category_code, category_name, category_name_en, description, depreciation_rate, useful_life)
               VALUES ('CAT-COMP', 'حاسبات', 'Computers', 'أجهزة حاسب وتقنية', 25, 4)""")

        # asset_disposals
        exe("""INSERT INTO asset_disposals (asset_id, disposal_date, disposal_method, disposal_value, disposal_reason, buyer_name, notes, status)
               VALUES (3, '2025-12-01', 'sale', 5000, 'استبدال بأحدث', 'شركة المنار', 'بيع الطابعة القديمة', 'completed')""")
        exe("""INSERT INTO asset_disposals (asset_id, disposal_date, disposal_method, disposal_value, disposal_reason, notes, status)
               VALUES (5, '2026-01-15', 'scrap', 0, 'تلف كامل', 'إتلاف جهاز كمبيوتر قديم', 'pending')""")

        # asset_insurance
        exe("""INSERT INTO asset_insurance (asset_id, policy_number, insurer, coverage_type, premium_amount, coverage_amount, start_date, end_date, status)
               VALUES (1, 'INS-2025-001', 'التعاونية للتأمين', 'comprehensive', 12000, 500000, '2025-01-01', '2025-12-31', 'active')""")
        exe("""INSERT INTO asset_insurance (asset_id, policy_number, insurer, coverage_type, premium_amount, coverage_amount, start_date, end_date, status)
               VALUES (2, 'INS-2025-002', 'بوبا للتأمين', 'fire', 8000, 300000, '2025-03-01', '2026-02-28', 'active')""")
        exe("""INSERT INTO asset_insurance (asset_id, policy_number, insurer, coverage_type, premium_amount, coverage_amount, start_date, end_date, status)
               VALUES (4, 'INS-2025-003', 'ملاذ للتأمين', 'theft', 3500, 150000, '2025-06-01', '2026-05-31', 'expired')""")

        # asset_maintenance
        exe("""INSERT INTO asset_maintenance (asset_id, maintenance_type, description, scheduled_date, completed_date, cost, vendor, status, created_by)
               VALUES (1, 'preventive', 'صيانة دورية للمبنى', '2025-06-15', '2025-06-16', 5000, 'شركة الصيانة المتقدمة', 'completed', 1)""")
        exe("""INSERT INTO asset_maintenance (asset_id, maintenance_type, description, scheduled_date, cost, vendor, status, created_by)
               VALUES (4, 'corrective', 'إصلاح عطل في المكيف', '2026-03-01', 2500, 'مؤسسة التبريد', 'scheduled', 1)""")
        exe("""INSERT INTO asset_maintenance (asset_id, maintenance_type, description, scheduled_date, completed_date, cost, vendor, status, created_by)
               VALUES (2, 'inspection', 'فحص سنوي للمركبة', '2025-09-10', '2025-09-10', 800, 'مركز الفحص الفني', 'completed', 1)""")

        # asset_revaluations
        exe("""INSERT INTO asset_revaluations (asset_id, revaluation_date, old_value, new_value, difference, reason, created_by)
               VALUES (1, '2025-12-31', 500000, 550000, 50000, 'إعادة تقييم سنوي بناءً على تقرير مقيم معتمد', 1)""")
        exe("""INSERT INTO asset_revaluations (asset_id, revaluation_date, old_value, new_value, difference, reason, created_by)
               VALUES (2, '2025-12-31', 120000, 95000, -25000, 'انخفاض القيمة السوقية', 1)""")

        # asset_transfers
        exe("""INSERT INTO asset_transfers (asset_id, from_location, to_location, transfer_date, reason, condition, status)
               VALUES (3, 'المكتب الرئيسي', 'فرع جدة', '2025-08-01', 'نقل لتغطية احتياجات الفرع', 'good', 'completed')""")
        exe("""INSERT INTO asset_transfers (asset_id, from_location, to_location, transfer_date, reason, condition, status)
               VALUES (6, 'فرع جدة', 'المستودع المركزي', '2026-01-20', 'إعادة توزيع الأصول', 'fair', 'pending')""")
        exe("""INSERT INTO asset_transfers (asset_id, from_location, to_location, transfer_date, reason, condition, status)
               VALUES (4, 'المكتب الرئيسي', 'فرع الدمام', '2025-11-15', 'دعم المشروع الجديد', 'excellent', 'completed')""")

        # ============================================================
        # 2. BANKING & RECONCILIATION
        # ============================================================
        print("2. Banking & Reconciliation...")

        # bank_reconciliations
        br1 = db.execute(text("""INSERT INTO bank_reconciliations (treasury_account_id, statement_date, start_balance, end_balance, status, notes, created_by, branch_id)
               VALUES (1, '2025-12-31', 150000, 185000, 'completed', 'مطابقة نهاية السنة', 1, 1) RETURNING id""")).scalar()
        br2 = db.execute(text("""INSERT INTO bank_reconciliations (treasury_account_id, statement_date, start_balance, end_balance, status, notes, created_by, branch_id)
               VALUES (2, '2026-01-31', 80000, 92000, 'draft', 'مطابقة يناير 2026', 1, 1) RETURNING id""")).scalar()
        br3 = db.execute(text("""INSERT INTO bank_reconciliations (treasury_account_id, statement_date, start_balance, end_balance, status, notes, created_by, branch_id)
               VALUES (3, '2025-11-30', 45000, 52000, 'completed', 'مطابقة نوفمبر', 1, 2) RETURNING id""")).scalar()
        count += 3

        # bank_statement_lines
        exe(f"""INSERT INTO bank_statement_lines (reconciliation_id, transaction_date, description, reference, debit, credit, balance, is_reconciled)
               VALUES ({br1}, '2025-12-05', 'تحويل وارد من عميل', 'TRF-001', 0, 25000, 175000, true)""")
        exe(f"""INSERT INTO bank_statement_lines (reconciliation_id, transaction_date, description, reference, debit, credit, balance, is_reconciled)
               VALUES ({br1}, '2025-12-10', 'دفع فاتورة مورد', 'CHK-445', 15000, 0, 160000, true)""")
        exe(f"""INSERT INTO bank_statement_lines (reconciliation_id, transaction_date, description, reference, debit, credit, balance, is_reconciled)
               VALUES ({br1}, '2025-12-20', 'إيداع نقدي', 'DEP-201', 0, 30000, 190000, false)""")
        exe(f"""INSERT INTO bank_statement_lines (reconciliation_id, transaction_date, description, reference, debit, credit, balance, is_reconciled)
               VALUES ({br2}, '2026-01-05', 'رسوم بنكية', 'FEE-001', 500, 0, 79500, true)""")
        exe(f"""INSERT INTO bank_statement_lines (reconciliation_id, transaction_date, description, reference, debit, credit, balance, is_reconciled)
               VALUES ({br2}, '2026-01-15', 'تحويل من عميل البناء', 'TRF-015', 0, 12500, 92000, false)""")

        # checks_payable
        exe("""INSERT INTO checks_payable (check_number, beneficiary_name, bank_name, branch_name, amount, currency, issue_date, due_date, party_id, treasury_account_id, status, branch_id, created_by)
               VALUES ('CHK-P-001', 'مؤسسة الأمان للتوريدات', 'البنك الأهلي', 'فرع الرياض', 35000, 'SAR', '2025-11-01', '2026-01-15', 1, 1, 'issued', 1, 1)""")
        exe("""INSERT INTO checks_payable (check_number, beneficiary_name, bank_name, branch_name, amount, currency, issue_date, due_date, party_id, treasury_account_id, status, branch_id, created_by)
               VALUES ('CHK-P-002', 'شركة التقنية المتحدة', 'بنك الراجحي', 'فرع جدة', 18000, 'SAR', '2025-12-01', '2026-02-01', 2, 2, 'cleared', 1, 1)""")
        exe("""INSERT INTO checks_payable (check_number, beneficiary_name, bank_name, branch_name, amount, currency, issue_date, due_date, bounce_date, party_id, treasury_account_id, status, bounce_reason, branch_id, created_by)
               VALUES ('CHK-P-003', 'محل الفرات', 'بنك الإنماء', 'فرع الدمام', 7500, 'SAR', '2025-10-15', '2025-12-15', '2025-12-16', 3, 3, 'bounced', 'رصيد غير كافٍ', 2, 1)""")

        # checks_receivable
        exe("""INSERT INTO checks_receivable (check_number, drawer_name, bank_name, branch_name, amount, currency, issue_date, due_date, party_id, treasury_account_id, status, branch_id, created_by)
               VALUES ('CHK-R-001', 'شركة الوفاء التجارية', 'البنك السعودي الفرنسي', 'الرياض', 42000, 'SAR', '2025-10-01', '2026-01-01', 5, 1, 'collected', 1, 1)""")
        exe("""INSERT INTO checks_receivable (check_number, drawer_name, bank_name, branch_name, amount, currency, issue_date, due_date, party_id, treasury_account_id, status, branch_id, created_by)
               VALUES ('CHK-R-002', 'مؤسسة النور', 'بنك البلاد', 'جدة', 15000, 'SAR', '2025-11-15', '2026-02-15', 6, 2, 'in_hand', 1, 1)""")
        exe("""INSERT INTO checks_receivable (check_number, drawer_name, bank_name, branch_name, amount, currency, issue_date, due_date, party_id, treasury_account_id, status, branch_id, created_by)
               VALUES ('CHK-R-003', 'عميل خاص', 'بنك الرياض', 'الدمام', 8500, 'SAR', '2025-12-01', '2026-03-01', 7, 3, 'deposited', 2, 1)""")

        # notes_payable
        exe("""INSERT INTO notes_payable (note_number, beneficiary_name, bank_name, amount, currency, issue_date, due_date, maturity_date, party_id, treasury_account_id, status, branch_id, created_by)
               VALUES ('NP-001', 'مجموعة الرشيد', 'البنك الأهلي', 100000, 'SAR', '2025-06-01', '2026-06-01', '2026-06-01', 1, 1, 'active', 1, 1)""")
        exe("""INSERT INTO notes_payable (note_number, beneficiary_name, bank_name, amount, currency, issue_date, due_date, maturity_date, payment_date, party_id, treasury_account_id, status, branch_id, created_by)
               VALUES ('NP-002', 'شركة المقاولات', 'بنك الراجحي', 55000, 'SAR', '2025-03-01', '2025-12-01', '2025-12-01', '2025-12-01', 2, 2, 'paid', 1, 1)""")

        # notes_receivable
        exe("""INSERT INTO notes_receivable (note_number, drawer_name, bank_name, amount, currency, issue_date, due_date, maturity_date, party_id, treasury_account_id, status, branch_id, created_by)
               VALUES ('NR-001', 'شركة البناء الحديث', 'بنك الإنماء', 75000, 'SAR', '2025-07-01', '2026-07-01', '2026-07-01', 5, 1, 'active', 1, 1)""")
        exe("""INSERT INTO notes_receivable (note_number, drawer_name, bank_name, amount, currency, issue_date, due_date, maturity_date, collection_date, party_id, treasury_account_id, status, branch_id, created_by)
               VALUES ('NR-002', 'مؤسسة الخليج', 'البنك السعودي الفرنسي', 30000, 'SAR', '2025-04-01', '2025-10-01', '2025-10-01', '2025-10-05', 6, 2, 'collected', 1, 1)""")
        exe("""INSERT INTO notes_receivable (note_number, drawer_name, bank_name, amount, currency, issue_date, due_date, maturity_date, protest_date, party_id, treasury_account_id, status, protest_reason, branch_id, created_by)
               VALUES ('NR-003', 'تاجر فردي', 'بنك البلاد', 20000, 'SAR', '2025-05-01', '2025-11-01', '2025-11-01', '2025-11-05', 7, 3, 'protested', 'عدم السداد في الموعد', 2, 1)""")

        # ============================================================
        # 3. CUSTOMERS & SUPPLIERS DETAILS
        # ============================================================
        print("3. Customers & Suppliers...")

        # customer_groups
        exe("""INSERT INTO customer_groups (group_code, group_name, group_name_en, description, discount_percentage, payment_days, status, branch_id)
               VALUES ('CG-VIP', 'عملاء VIP', 'VIP Customers', 'عملاء ذوو أولوية عالية', 10, 60, 'active', 1)""")
        exe("""INSERT INTO customer_groups (group_code, group_name, group_name_en, description, discount_percentage, payment_days, status, branch_id)
               VALUES ('CG-REG', 'عملاء عاديون', 'Regular Customers', 'عملاء بشروط عادية', 0, 30, 'active', 1)""")
        exe("""INSERT INTO customer_groups (group_code, group_name, group_name_en, description, discount_percentage, payment_days, status, branch_id)
               VALUES ('CG-GOV', 'جهات حكومية', 'Government', 'عقود حكومية', 5, 90, 'active', 1)""")

        # customer_contacts
        exe("""INSERT INTO customer_contacts (customer_id, contact_name, contact_name_en, position, department, email, phone, mobile, is_primary)
               VALUES (5, 'أحمد المالكي', 'Ahmed Al-Malki', 'مدير المشتريات', 'المشتريات', 'ahmed@client1.sa', '0112345678', '0551234567', true)""")
        exe("""INSERT INTO customer_contacts (customer_id, contact_name, contact_name_en, position, department, email, phone, mobile, is_primary)
               VALUES (5, 'سارة العتيبي', 'Sara Al-Otaibi', 'محاسبة', 'المالية', 'sara@client1.sa', '0112345679', '0559876543', false)""")
        exe("""INSERT INTO customer_contacts (customer_id, contact_name, contact_name_en, position, email, mobile, is_primary)
               VALUES (6, 'خالد الشمري', 'Khalid Al-Shammari', 'المدير العام', 'khalid@client2.sa', '0561112233', true)""")
        exe("""INSERT INTO customer_contacts (customer_id, contact_name, contact_name_en, position, email, mobile, is_primary)
               VALUES (7, 'فاطمة الحربي', 'Fatima Al-Harbi', 'مديرة العمليات', 'fatima@client3.sa', '0577889900', true)""")

        # customer_bank_accounts
        exe("""INSERT INTO customer_bank_accounts (customer_id, bank_name, bank_name_en, account_number, iban, swift_code, branch_name, account_holder, is_default, status)
               VALUES (5, 'البنك الأهلي', 'NCB', '10203040506', 'SA44 2000 0001 0203 0405 0600', 'NCBKSAJE', 'فرع الرياض', 'شركة الوفاء التجارية', true, 'active')""")
        exe("""INSERT INTO customer_bank_accounts (customer_id, bank_name, bank_name_en, account_number, iban, swift_code, branch_name, account_holder, is_default, status)
               VALUES (6, 'بنك الراجحي', 'Al Rajhi', '20304050607', 'SA66 8000 0020 3040 5060 0700', 'RJHISARI', 'فرع جدة', 'مؤسسة النور', true, 'active')""")

        # customer_balances
        exe("""INSERT INTO customer_balances (customer_id, currency, total_receivable, total_paid, outstanding_balance, overdue_amount, aging_30, aging_60, aging_90, aging_120, aging_120_plus)
               VALUES (5, 'SAR', 250000, 200000, 50000, 15000, 20000, 10000, 10000, 5000, 5000)""")
        exe("""INSERT INTO customer_balances (customer_id, currency, total_receivable, total_paid, outstanding_balance, overdue_amount, aging_30, aging_60, aging_90, aging_120, aging_120_plus)
               VALUES (6, 'SAR', 180000, 170000, 10000, 0, 10000, 0, 0, 0, 0)""")
        exe("""INSERT INTO customer_balances (customer_id, currency, total_receivable, total_paid, outstanding_balance, overdue_amount, aging_30, aging_60, aging_90, aging_120, aging_120_plus)
               VALUES (7, 'SAR', 95000, 95000, 0, 0, 0, 0, 0, 0, 0)""")

        # customer_price_lists
        cpl1 = db.execute(text("""INSERT INTO customer_price_lists (price_list_code, price_list_name, price_list_name_en, currency, discount_type, discount_value, valid_from, valid_to, status, is_default)
               VALUES ('PL-VIP', 'قائمة أسعار VIP', 'VIP Price List', 'SAR', 'percentage', 10, '2025-01-01', '2026-12-31', 'active', false) RETURNING id""")).scalar()
        cpl2 = db.execute(text("""INSERT INTO customer_price_lists (price_list_code, price_list_name, price_list_name_en, currency, discount_type, discount_value, valid_from, valid_to, status, is_default)
               VALUES ('PL-STD', 'قائمة الأسعار العادية', 'Standard Price List', 'SAR', 'fixed', 0, '2025-01-01', '2026-12-31', 'active', true) RETURNING id""")).scalar()
        count += 2

        # customer_price_list_items
        for pid in PROD_IDS[:4]:
            exe(f"""INSERT INTO customer_price_list_items (price_list_id, product_id, price) VALUES ({cpl1}, {pid}, {100 + pid * 50})""")
            exe(f"""INSERT INTO customer_price_list_items (price_list_id, product_id, price) VALUES ({cpl2}, {pid}, {120 + pid * 50})""")

        # customer_receipts
        exe("""INSERT INTO customer_receipts (receipt_number, customer_id, receipt_date, receipt_method, amount, currency, exchange_rate, reference, notes, status, created_by)
               VALUES ('CR-2025-001', 5, '2025-10-15', 'bank_transfer', 50000, 'SAR', 1, 'TRF-8812', 'سداد دفعة من فاتورة', 'confirmed', 1)""")
        exe("""INSERT INTO customer_receipts (receipt_number, customer_id, receipt_date, receipt_method, amount, currency, exchange_rate, reference, notes, status, created_by)
               VALUES ('CR-2025-002', 6, '2025-11-01', 'cash', 25000, 'SAR', 1, 'CASH-001', 'سداد نقدي', 'confirmed', 1)""")
        exe("""INSERT INTO customer_receipts (receipt_number, customer_id, receipt_date, receipt_method, amount, currency, exchange_rate, reference, notes, status, created_by)
               VALUES ('CR-2025-003', 7, '2025-12-20', 'check', 15000, 'SAR', 1, 'CHK-R-001', 'شيك مستلم', 'pending', 1)""")

        # customer_transactions
        exe("""INSERT INTO customer_transactions (customer_id, transaction_type, reference_number, transaction_date, description, debit, credit, balance, created_by)
               VALUES (5, 'invoice', 'INV-2025-001', '2025-09-01', 'فاتورة مبيعات', 80000, 0, 80000, 1)""")
        exe("""INSERT INTO customer_transactions (customer_id, transaction_type, reference_number, transaction_date, description, debit, credit, balance, created_by)
               VALUES (5, 'payment', 'CR-2025-001', '2025-10-15', 'سداد دفعة', 0, 50000, 30000, 1)""")
        exe("""INSERT INTO customer_transactions (customer_id, transaction_type, reference_number, transaction_date, description, debit, credit, balance, created_by)
               VALUES (6, 'invoice', 'INV-2025-005', '2025-10-01', 'فاتورة خدمات', 45000, 0, 45000, 1)""")
        exe("""INSERT INTO customer_transactions (customer_id, transaction_type, reference_number, transaction_date, description, debit, credit, balance, created_by)
               VALUES (6, 'payment', 'CR-2025-002', '2025-11-01', 'سداد كامل', 0, 45000, 0, 1)""")

        # supplier_groups
        exe("""INSERT INTO supplier_groups (group_code, group_name, group_name_en, description, discount_percentage, payment_days, status)
               VALUES ('SG-LOC', 'موردين محليين', 'Local Suppliers', 'موردين داخل المملكة', 5, 30, 'active')""")
        exe("""INSERT INTO supplier_groups (group_code, group_name, group_name_en, description, discount_percentage, payment_days, status)
               VALUES ('SG-INT', 'موردين دوليين', 'International Suppliers', 'موردين خارج المملكة', 3, 60, 'active')""")
        exe("""INSERT INTO supplier_groups (group_code, group_name, group_name_en, description, discount_percentage, payment_days, status)
               VALUES ('SG-MFG', 'مصانع', 'Manufacturers', 'مصانع وشركات صناعية', 8, 45, 'active')""")

        # supplier_contacts
        exe("""INSERT INTO supplier_contacts (supplier_id, contact_name, contact_name_en, position, email, phone, mobile, is_primary)
               VALUES (1, 'محمد القحطاني', 'Mohammed Al-Qahtani', 'مدير المبيعات', 'mohammed@supplier1.sa', '0114567890', '0541234567', true)""")
        exe("""INSERT INTO supplier_contacts (supplier_id, contact_name, contact_name_en, position, email, phone, mobile, is_primary)
               VALUES (2, 'عبدالله الغامدي', 'Abdullah Al-Ghamdi', 'مسؤول التوريد', 'abdullah@supplier2.sa', '0126543210', '0559998877', true)""")
        exe("""INSERT INTO supplier_contacts (supplier_id, contact_name, contact_name_en, position, email, mobile, is_primary)
               VALUES (3, 'نورة الزهراني', 'Noura Al-Zahrani', 'مديرة الحسابات', 'noura@supplier3.sa', '0537765544', true)""")

        # supplier_bank_accounts
        exe("""INSERT INTO supplier_bank_accounts (supplier_id, bank_name, bank_name_en, account_number, iban, swift_code, branch_name, account_holder, is_default, status)
               VALUES (1, 'بنك الراجحي', 'Al Rajhi', '30405060708', 'SA88 8000 0030 4050 6070 0800', 'RJHISARI', 'فرع الرياض', 'مؤسسة الأمان للتوريدات', true, 'active')""")
        exe("""INSERT INTO supplier_bank_accounts (supplier_id, bank_name, bank_name_en, account_number, iban, swift_code, branch_name, account_holder, is_default, status)
               VALUES (2, 'البنك الأهلي', 'NCB', '40506070809', 'SA55 2000 0040 5060 7080 0900', 'NCBKSAJE', 'فرع جدة', 'شركة التقنية المتحدة', true, 'active')""")

        # supplier_balances
        exe("""INSERT INTO supplier_balances (supplier_id, currency, total_payable, total_paid, outstanding_balance, overdue_amount, aging_30, aging_60, aging_90, aging_120, aging_120_plus)
               VALUES (1, 'SAR', 320000, 280000, 40000, 10000, 15000, 10000, 10000, 5000, 0)""")
        exe("""INSERT INTO supplier_balances (supplier_id, currency, total_payable, total_paid, outstanding_balance, overdue_amount, aging_30, aging_60, aging_90, aging_120, aging_120_plus)
               VALUES (2, 'SAR', 150000, 150000, 0, 0, 0, 0, 0, 0, 0)""")
        exe("""INSERT INTO supplier_balances (supplier_id, currency, total_payable, total_paid, outstanding_balance, overdue_amount, aging_30, aging_60, aging_90, aging_120, aging_120_plus)
               VALUES (3, 'SAR', 85000, 70000, 15000, 5000, 10000, 5000, 0, 0, 0)""")

        # supplier_payments
        exe("""INSERT INTO supplier_payments (payment_number, supplier_id, payment_date, payment_method, amount, currency, exchange_rate, reference, notes, status, created_by)
               VALUES ('SP-2025-001', 1, '2025-10-01', 'bank_transfer', 80000, 'SAR', 1, 'TRF-SP-001', 'سداد دفعة مشتريات', 'completed', 1)""")
        exe("""INSERT INTO supplier_payments (payment_number, supplier_id, payment_date, payment_method, amount, currency, exchange_rate, reference, notes, status, created_by)
               VALUES ('SP-2025-002', 2, '2025-11-15', 'check', 50000, 'SAR', 1, 'CHK-P-002', 'سداد بشيك', 'completed', 1)""")
        exe("""INSERT INTO supplier_payments (payment_number, supplier_id, payment_date, payment_method, amount, currency, exchange_rate, reference, notes, status, created_by)
               VALUES ('SP-2025-003', 3, '2026-01-10', 'bank_transfer', 25000, 'SAR', 1, 'TRF-SP-003', 'دفعة جزئية', 'pending', 1)""")

        # supplier_ratings
        exe("""INSERT INTO supplier_ratings (supplier_id, po_id, quality_score, delivery_score, price_score, service_score, overall_score, comments, rated_by)
               VALUES (1, 1, 9, 8, 7, 8, 8, 'مورد ممتاز والتزام بالمواعيد', 1)""")
        exe("""INSERT INTO supplier_ratings (supplier_id, po_id, quality_score, delivery_score, price_score, service_score, overall_score, comments, rated_by)
               VALUES (2, 2, 7, 6, 8, 7, 7, 'جودة جيدة لكن تأخير أحياناً', 1)""")
        exe("""INSERT INTO supplier_ratings (supplier_id, po_id, quality_score, delivery_score, price_score, service_score, overall_score, comments, rated_by)
               VALUES (3, 3, 8, 9, 6, 8, 7.75, 'سرعة في التوصيل وأسعار مرتفعة قليلاً', 1)""")

        # supplier_transactions
        exe("""INSERT INTO supplier_transactions (supplier_id, transaction_type, reference_number, transaction_date, description, debit, credit, balance, created_by)
               VALUES (1, 'invoice', 'PINV-2025-001', '2025-08-01', 'فاتورة مشتريات مواد خام', 0, 120000, 120000, 1)""")
        exe("""INSERT INTO supplier_transactions (supplier_id, transaction_type, reference_number, transaction_date, description, debit, credit, balance, created_by)
               VALUES (1, 'payment', 'SP-2025-001', '2025-10-01', 'سداد دفعة', 80000, 0, 40000, 1)""")
        exe("""INSERT INTO supplier_transactions (supplier_id, transaction_type, reference_number, transaction_date, description, debit, credit, balance, created_by)
               VALUES (2, 'invoice', 'PINV-2025-005', '2025-09-15', 'فاتورة معدات', 0, 50000, 50000, 1)""")
        exe("""INSERT INTO supplier_transactions (supplier_id, transaction_type, reference_number, transaction_date, description, debit, credit, balance, created_by)
               VALUES (2, 'payment', 'SP-2025-002', '2025-11-15', 'سداد كامل', 50000, 0, 0, 1)""")

        # party_groups
        exe("""INSERT INTO party_groups (group_code, group_name, group_name_en, discount_percentage, payment_days, description, status)
               VALUES ('PG-PREM', 'فئة مميزة', 'Premium', 15, 45, 'أطراف ذات معاملات كبيرة', 'active')""")
        exe("""INSERT INTO party_groups (group_code, group_name, group_name_en, discount_percentage, payment_days, description, status)
               VALUES ('PG-STD', 'فئة عادية', 'Standard', 0, 30, 'أطراف عادية', 'active')""")

        # party_transactions
        exe("""INSERT INTO party_transactions (party_id, transaction_type, reference_number, transaction_date, description, debit, credit, balance, created_by)
               VALUES (1, 'invoice', 'PINV-001', '2025-09-01', 'فاتورة توريد', 0, 65000, 65000, 1)""")
        exe("""INSERT INTO party_transactions (party_id, transaction_type, reference_number, transaction_date, description, debit, credit, balance, created_by)
               VALUES (5, 'invoice', 'SINV-001', '2025-09-15', 'فاتورة مبيعات', 45000, 0, 45000, 1)""")
        exe("""INSERT INTO party_transactions (party_id, transaction_type, reference_number, transaction_date, description, debit, credit, balance, created_by)
               VALUES (5, 'payment', 'PAY-001', '2025-10-15', 'سداد', 0, 45000, 0, 1)""")

        # ============================================================
        # 4. BUDGETS & COST CENTERS
        # ============================================================
        print("4. Budgets & Cost Centers...")

        # budget_items
        acct_ids = db.execute(text("SELECT id FROM accounts WHERE account_type IN ('expense','revenue') LIMIT 8")).fetchall()
        acct_list = [a[0] for a in acct_ids]
        for i, aid in enumerate(acct_list[:6]):
            exe(f"""INSERT INTO budget_items (budget_id, account_id, planned_amount, actual_amount, notes) 
                    VALUES ({BUDGET_IDS[i%2]}, {aid}, {50000 + i*10000}, {45000 + i*8000}, 'بند موازنة {i+1}')""")

        # cost_centers_budgets
        exe("""INSERT INTO cost_centers_budgets (cost_center_id, budget_id, allocated_amount, used_amount, fiscal_year) VALUES (1, 2, 200000, 150000, 2025)""")
        exe("""INSERT INTO cost_centers_budgets (cost_center_id, budget_id, allocated_amount, used_amount, fiscal_year) VALUES (2, 2, 150000, 120000, 2025)""")
        exe("""INSERT INTO cost_centers_budgets (cost_center_id, budget_id, allocated_amount, used_amount, fiscal_year) VALUES (3, 3, 100000, 85000, 2025)""")
        exe("""INSERT INTO cost_centers_budgets (cost_center_id, budget_id, allocated_amount, used_amount, fiscal_year) VALUES (4, 3, 80000, 60000, 2025)""")

        # ============================================================
        # 5. HR COMPREHENSIVE
        # ============================================================
        print("5. HR Tables...")

        # salary_structures
        ss1 = db.execute(text("""INSERT INTO salary_structures (name, name_en, description, base_type, is_active) 
               VALUES ('هيكل راتب إداري', 'Admin Salary Structure', 'هيكل الرواتب للموظفين الإداريين', 'monthly', true) RETURNING id""")).scalar()
        ss2 = db.execute(text("""INSERT INTO salary_structures (name, name_en, description, base_type, is_active) 
               VALUES ('هيكل راتب فني', 'Technical Salary Structure', 'هيكل الرواتب للفنيين', 'monthly', true) RETURNING id""")).scalar()
        count += 2

        # salary_components
        sc_ids = []
        for comp in [
            ('الراتب الأساسي', 'Basic Salary', 'earning', 'fixed', ss1),
            ('بدل سكن', 'Housing Allowance', 'earning', 'percentage', ss1),
            ('بدل نقل', 'Transport Allowance', 'earning', 'fixed', ss1),
            ('بدل طعام', 'Food Allowance', 'earning', 'fixed', ss2),
            ('خصم تأمينات', 'GOSI Deduction', 'deduction', 'percentage', ss1),
            ('خصم ضريبة', 'Tax Deduction', 'deduction', 'percentage', ss1),
            ('بدل خطر', 'Hazard Allowance', 'earning', 'fixed', ss2),
            ('مكافأة أداء', 'Performance Bonus', 'earning', 'percentage', ss2),
        ]:
            sid = db.execute(text(f"""INSERT INTO salary_components (name, name_en, component_type, calculation_type, is_taxable, is_gosi_applicable, is_active, sort_order, structure_id)
                   VALUES ('{comp[0]}', '{comp[1]}', '{comp[2]}', '{comp[3]}', {str(comp[2]=='earning').lower()}, true, true, {len(sc_ids)+1}, {comp[4]}) RETURNING id""")).scalar()
            sc_ids.append(sid)
            count += 1

        # employee_salary_components
        for eid in EMP_IDS:
            exe(f"""INSERT INTO employee_salary_components (employee_id, component_id, amount, is_active, effective_date) VALUES ({eid}, {sc_ids[0]}, {8000+eid*1000}, true, '2025-01-01')""")
            exe(f"""INSERT INTO employee_salary_components (employee_id, component_id, amount, is_active, effective_date) VALUES ({eid}, {sc_ids[1]}, {2500+eid*500}, true, '2025-01-01')""")
            exe(f"""INSERT INTO employee_salary_components (employee_id, component_id, amount, is_active, effective_date) VALUES ({eid}, {sc_ids[2]}, 1000, true, '2025-01-01')""")

        # gosi_settings
        exe("""INSERT INTO gosi_settings (employee_share_percentage, employer_share_percentage, occupational_hazard_percentage, max_contributable_salary, is_active, effective_date)
               VALUES (9.75, 11.75, 2, 45000, true, '2025-01-01')""")

        # attendance
        for eid in EMP_IDS:
            for d in range(1, 6):
                exe(f"""INSERT INTO attendance (employee_id, date, check_in, check_out, status) 
                        VALUES ({eid}, '2026-02-{d:02d}', '2026-02-{d:02d} 08:00', '2026-02-{d:02d} 17:00', 'present')""")
            exe(f"""INSERT INTO attendance (employee_id, date, status, notes) VALUES ({eid}, '2026-02-06', 'absent', 'غياب بدون عذر')""")
            exe(f"""INSERT INTO attendance (employee_id, date, check_in, check_out, status) VALUES ({eid}, '2026-02-07', '2026-02-07 09:30', '2026-02-07 17:00', 'late')""")

        # leave_requests
        exe("""INSERT INTO leave_requests (employee_id, leave_type, start_date, end_date, reason, status, approved_by)
               VALUES (1, 'annual', '2026-03-01', '2026-03-05', 'إجازة سنوية', 'approved', 1)""")
        exe("""INSERT INTO leave_requests (employee_id, leave_type, start_date, end_date, reason, status)
               VALUES (2, 'sick', '2026-02-10', '2026-02-12', 'إجازة مرضية - التهاب', 'approved')""")
        exe("""INSERT INTO leave_requests (employee_id, leave_type, start_date, end_date, reason, status)
               VALUES (3, 'annual', '2026-04-15', '2026-04-20', 'إجازة عائلية', 'pending')""")
        exe("""INSERT INTO leave_requests (employee_id, leave_type, start_date, end_date, reason, status)
               VALUES (1, 'emergency', '2025-12-25', '2025-12-26', 'ظرف طارئ', 'approved')""")

        # leave_carryover
        for eid in EMP_IDS:
            exe(f"""INSERT INTO leave_carryover (employee_id, leave_type, year, entitled_days, used_days, carried_days, expired_days, max_carryover)
                    VALUES ({eid}, 'annual', 2025, 30, {15+eid*3}, {10-eid}, {2+eid}, 10)""")

        # overtime_requests
        exe("""INSERT INTO overtime_requests (employee_id, request_date, overtime_date, hours, overtime_type, multiplier, calculated_amount, reason, status, approved_by, branch_id)
               VALUES (1, '2026-01-20', '2026-01-22', 4, 'normal', 1.5, 600, 'إنهاء مشروع عاجل', 'approved', 1, 1)""")
        exe("""INSERT INTO overtime_requests (employee_id, request_date, overtime_date, hours, overtime_type, multiplier, calculated_amount, reason, status, branch_id)
               VALUES (2, '2026-02-01', '2026-02-03', 8, 'weekend', 2, 1600, 'صيانة طارئة', 'pending', 1)""")
        exe("""INSERT INTO overtime_requests (employee_id, request_date, overtime_date, hours, overtime_type, multiplier, calculated_amount, reason, status, approved_by, branch_id)
               VALUES (3, '2025-12-15', '2025-12-17', 3, 'holiday', 2.5, 750, 'عمل في العيد', 'approved', 1, 2)""")
        exe("""INSERT INTO overtime_requests (employee_id, request_date, overtime_date, hours, overtime_type, multiplier, calculated_amount, reason, status, branch_id)
               VALUES (1, '2026-02-05', '2026-02-07', 6, 'weekend', 2, 1200, 'جرد نهاية الأسبوع', 'pending', 1)""")

        # employee_loans
        exe("""INSERT INTO employee_loans (employee_id, amount, total_installments, monthly_installment, paid_amount, start_date, status, reason, approved_by, branch_id)
               VALUES (1, 30000, 12, 2500, 7500, '2025-06-01', 'active', 'سلفة شخصية', 1, 1)""")
        exe("""INSERT INTO employee_loans (employee_id, amount, total_installments, monthly_installment, paid_amount, start_date, status, reason, approved_by, branch_id)
               VALUES (2, 15000, 6, 2500, 15000, '2025-03-01', 'completed', 'سلفة لبداية العام الدراسي', 1, 1)""")
        exe("""INSERT INTO employee_loans (employee_id, amount, total_installments, monthly_installment, paid_amount, start_date, status, reason, branch_id)
               VALUES (3, 20000, 10, 2000, 0, '2026-03-01', 'pending', 'سلفة زواج', 2)""")

        # employee_custody
        exe("""INSERT INTO employee_custody (employee_id, item_name, item_type, serial_number, assigned_date, condition_on_assign, value, status)
               VALUES (1, 'لابتوب Dell Latitude', 'laptop', 'DL-2025-001', '2025-01-15', 'new', 4500, 'assigned')""")
        exe("""INSERT INTO employee_custody (employee_id, item_name, item_type, serial_number, assigned_date, condition_on_assign, value, status)
               VALUES (1, 'هاتف iPhone 15', 'mobile', 'IP-2025-001', '2025-02-01', 'new', 3800, 'assigned')""")
        exe("""INSERT INTO employee_custody (employee_id, item_name, item_type, serial_number, assigned_date, return_date, condition_on_assign, condition_on_return, value, status)
               VALUES (2, 'سيارة تويوتا كامري', 'vehicle', 'CAR-2024-001', '2024-06-01', '2025-12-31', 'good', 'good', 85000, 'returned')""")
        exe("""INSERT INTO employee_custody (employee_id, item_name, item_type, assigned_date, condition_on_assign, value, status)
               VALUES (3, 'مفتاح مكتب', 'key', '2025-03-01', 'new', 50, 'assigned')""")

        # employee_documents
        exe("""INSERT INTO employee_documents (employee_id, document_type, document_number, issue_date, expiry_date, issuing_authority, alert_days, status)
               VALUES (1, 'other', '1088776655', '2020-05-15', '2030-05-14', 'الأحوال المدنية', 90, 'valid')""")
        exe("""INSERT INTO employee_documents (employee_id, document_type, document_number, issue_date, expiry_date, issuing_authority, alert_days, status)
               VALUES (1, 'passport', 'A12345678', '2022-01-01', '2027-01-01', 'وزارة الداخلية', 60, 'valid')""")
        exe("""INSERT INTO employee_documents (employee_id, document_type, document_number, issue_date, expiry_date, issuing_authority, alert_days, status)
               VALUES (2, 'iqama', '2345678901', '2024-06-01', '2026-06-01', 'الجوازات', 90, 'expiring_soon')""")
        exe("""INSERT INTO employee_documents (employee_id, document_type, document_number, issue_date, expiry_date, issuing_authority, alert_days, status)
               VALUES (3, 'license', 'DL-998877', '2023-03-01', '2033-03-01', 'المرور', 30, 'valid')""")

        # employee_violations
        exe("""INSERT INTO employee_violations (employee_id, violation_date, violation_type, severity, description, action_taken, penalty_amount, deduct_from_salary, reported_by, status)
               VALUES (2, '2025-11-01', 'late_attendance', 'minor', 'تأخر متكرر عن الحضور صباحاً', 'written_warning', 0, false, 1, 'resolved')""")
        exe("""INSERT INTO employee_violations (employee_id, violation_date, violation_type, severity, description, action_taken, penalty_amount, deduct_from_salary, reported_by, status)
               VALUES (3, '2025-12-15', 'absence', 'major', 'غياب بدون إذن مسبق', 'salary_deduction', 500, true, 1, 'resolved')""")
        exe("""INSERT INTO employee_violations (employee_id, violation_date, violation_type, severity, description, action_taken, penalty_amount, deduct_from_salary, reported_by, status)
               VALUES (1, '2026-01-10', 'policy_violation', 'minor', 'عدم ارتداء الزي الرسمي', 'verbal_warning', 0, false, 1, 'open')""")

        # performance_reviews
        exe("""INSERT INTO performance_reviews (employee_id, reviewer_id, review_period, review_date, review_type, overall_rating, strengths, weaknesses, goals, self_rating, manager_comments, status)
               VALUES (1, 1, '2025-H2', '2025-12-31', 'annual', 4.5, 'التزام عالي وجودة عمل ممتازة', 'يحتاج تحسين في إدارة الوقت', 'قيادة فريق أكبر', 4.2, 'أداء متميز يستحق الترقية', 'completed')""")
        exe("""INSERT INTO performance_reviews (employee_id, reviewer_id, review_period, review_date, review_type, overall_rating, strengths, weaknesses, goals, self_rating, manager_comments, status)
               VALUES (2, 1, '2025-H2', '2025-12-31', 'annual', 3.8, 'مهارات تقنية عالية', 'تحسين التواصل مع الفريق', 'الحصول على شهادة مهنية', 3.5, 'أداء جيد مع فرص للتحسين', 'completed')""")
        exe("""INSERT INTO performance_reviews (employee_id, reviewer_id, review_period, review_date, review_type, overall_rating, strengths, weaknesses, goals, status)
               VALUES (3, 1, '2025-H2', '2026-01-15', 'probation', 3.2, 'حماس وإرادة للتعلم', 'يحتاج تدريب إضافي', 'إتقان الأنظمة المحاسبية', 'draft')""")

        # job_openings
        jo1 = db.execute(text("""INSERT INTO job_openings (title, department_id, position_id, description, requirements, employment_type, vacancies, status, branch_id, closing_date, created_by)
               VALUES ('محاسب أول', 7, 7, 'مطلوب محاسب أول ذو خبرة', 'بكالوريوس محاسبة + 5 سنوات خبرة', 'full_time', 2, 'open', 1, '2026-04-01', 1) RETURNING id""")).scalar()
        jo2 = db.execute(text("""INSERT INTO job_openings (title, department_id, position_id, description, requirements, employment_type, vacancies, status, branch_id, closing_date, created_by)
               VALUES ('مهندس برمجيات', 8, 8, 'مطلوب مطور ويب', 'بكالوريوس حاسب + React/Python', 'full_time', 3, 'open', 1, '2026-05-01', 1) RETURNING id""")).scalar()
        jo3 = db.execute(text("""INSERT INTO job_openings (title, department_id, position_id, description, requirements, employment_type, vacancies, status, branch_id, closing_date, created_by)
               VALUES ('فني صيانة', 9, 9, 'فني صيانة معدات', 'دبلوم فني + سنتين خبرة', 'contract', 1, 'closed', 2, '2025-12-01', 1) RETURNING id""")).scalar()
        count += 3

        # job_applications
        exe(f"""INSERT INTO job_applications (opening_id, applicant_name, email, phone, stage, rating, status)
                VALUES ({jo1}, 'سعد الدوسري', 'saad@email.com', '0551122334', 'interview', 4, 'active')""")
        exe(f"""INSERT INTO job_applications (opening_id, applicant_name, email, phone, stage, rating, status)
                VALUES ({jo1}, 'هدى القرني', 'huda@email.com', '0552233445', 'screening', 3, 'active')""")
        exe(f"""INSERT INTO job_applications (opening_id, applicant_name, email, phone, stage, rating, status)
                VALUES ({jo2}, 'ياسر المطيري', 'yaser@email.com', '0553344556', 'offer', 5, 'active')""")
        exe(f"""INSERT INTO job_applications (opening_id, applicant_name, email, phone, stage, rating, notes, status)
                VALUES ({jo3}, 'عمر الحارثي', 'omar.h@email.com', '0554455667', 'hired', 4, 'تم التعيين', 'hired')""")

        # training_programs
        tp1 = db.execute(text("""INSERT INTO training_programs (name, name_en, description, trainer, location, start_date, end_date, max_participants, cost, status)
               VALUES ('دورة المحاسبة المتقدمة', 'Advanced Accounting', 'دورة في المعايير الدولية', 'د. فهد الأحمدي', 'قاعة التدريب الرئيسية', '2026-03-01', '2026-03-05', 20, 15000, 'planned') RETURNING id""")).scalar()
        tp2 = db.execute(text("""INSERT INTO training_programs (name, name_en, description, trainer, location, start_date, end_date, max_participants, cost, status)
               VALUES ('دورة السلامة المهنية', 'Occupational Safety', 'تدريب على السلامة في بيئة العمل', 'م. سلطان العنزي', 'المصنع', '2025-11-15', '2025-11-16', 30, 5000, 'completed') RETURNING id""")).scalar()
        count += 2

        # training_participants
        exe(f"INSERT INTO training_participants (training_id, employee_id, attendance_status, certificate_issued, score, feedback) VALUES ({tp1}, 1, 'registered', false, NULL, NULL)")
        exe(f"INSERT INTO training_participants (training_id, employee_id, attendance_status, certificate_issued, score, feedback) VALUES ({tp1}, 2, 'registered', false, NULL, NULL)")
        exe(f"INSERT INTO training_participants (training_id, employee_id, attendance_status, certificate_issued, score, feedback) VALUES ({tp2}, 1, 'attended', true, 92, 'دورة مفيدة جداً')")
        exe(f"INSERT INTO training_participants (training_id, employee_id, attendance_status, certificate_issued, score, feedback) VALUES ({tp2}, 3, 'attended', true, 88, 'استفدت كثيراً')")

        # ============================================================
        # 6. PRODUCTS & INVENTORY
        # ============================================================
        print("6. Products & Inventory...")

        # product_categories
        pc_ids = []
        for cat in [
            ('PC-RAW', 'مواد خام', 'Raw Materials', 'مواد أولية للإنتاج'),
            ('PC-FIN', 'منتجات تامة', 'Finished Goods', 'منتجات جاهزة للبيع'),
            ('PC-SPA', 'قطع غيار', 'Spare Parts', 'قطع غيار ومستهلكات'),
            ('PC-PKG', 'مواد تغليف', 'Packaging', 'مواد تغليف وتعبئة'),
        ]:
            cid = db.execute(text(f"""INSERT INTO product_categories (category_code, category_name, category_name_en, description, is_active, sort_order)
                   VALUES ('{cat[0]}', '{cat[1]}', '{cat[2]}', '{cat[3]}', true, {len(pc_ids)+1}) RETURNING id""")).scalar()
            pc_ids.append(cid)
            count += 1

        # product_attributes
        pa1 = db.execute(text("""INSERT INTO product_attributes (attribute_name, attribute_name_en, attribute_type, sort_order, is_active)
               VALUES ('اللون', 'Color', 'select', 1, true) RETURNING id""")).scalar()
        pa2 = db.execute(text("""INSERT INTO product_attributes (attribute_name, attribute_name_en, attribute_type, sort_order, is_active)
               VALUES ('الحجم', 'Size', 'select', 2, true) RETURNING id""")).scalar()
        pa3 = db.execute(text("""INSERT INTO product_attributes (attribute_name, attribute_name_en, attribute_type, sort_order, is_active)
               VALUES ('المادة', 'Material', 'select', 3, true) RETURNING id""")).scalar()
        count += 3

        # product_attribute_values
        pav_ids = []
        for val in [
            (pa1, 'أحمر', 'Red', '#FF0000'), (pa1, 'أزرق', 'Blue', '#0000FF'), (pa1, 'أخضر', 'Green', '#00FF00'),
            (pa2, 'صغير', 'Small', None), (pa2, 'وسط', 'Medium', None), (pa2, 'كبير', 'Large', None),
            (pa3, 'حديد', 'Steel', None), (pa3, 'ألمنيوم', 'Aluminum', None),
        ]:
            cc = f", color_code='{val[3]}'" if val[3] else ""
            vid = db.execute(text(f"""INSERT INTO product_attribute_values (attribute_id, value_name, value_name_en, sort_order, is_active {', color_code' if val[3] else ''})
                   VALUES ({val[0]}, '{val[1]}', '{val[2]}', {len(pav_ids)+1}, true {f", '{val[3]}'" if val[3] else ''}) RETURNING id""")).scalar()
            pav_ids.append(vid)
            count += 1

        # product_variants
        pv_ids = []
        variants_data = [
            (PROD_IDS[0], 'V-001-R', 'متغير أحمر', 'SKU-001-R', 100, 150),
            (PROD_IDS[0], 'V-001-B', 'متغير أزرق', 'SKU-001-B', 100, 150),
            (PROD_IDS[1], 'V-002-S', 'صغير', 'SKU-002-S', 80, 120),
            (PROD_IDS[1], 'V-002-L', 'كبير', 'SKU-002-L', 90, 135),
        ]
        for v in variants_data:
            vid = db.execute(text(f"""INSERT INTO product_variants (product_id, variant_code, variant_name, sku, cost_price, selling_price, is_active)
                   VALUES ({v[0]}, '{v[1]}', '{v[2]}', '{v[3]}', {v[4]}, {v[5]}, true) RETURNING id""")).scalar()
            pv_ids.append(vid)
            count += 1

        # product_variant_attributes
        if len(pv_ids) >= 4 and len(pav_ids) >= 6:
            exe(f"INSERT INTO product_variant_attributes (variant_id, attribute_id, attribute_value_id) VALUES ({pv_ids[0]}, {pa1}, {pav_ids[0]})")
            exe(f"INSERT INTO product_variant_attributes (variant_id, attribute_id, attribute_value_id) VALUES ({pv_ids[1]}, {pa1}, {pav_ids[1]})")
            exe(f"INSERT INTO product_variant_attributes (variant_id, attribute_id, attribute_value_id) VALUES ({pv_ids[2]}, {pa2}, {pav_ids[3]})")
            exe(f"INSERT INTO product_variant_attributes (variant_id, attribute_id, attribute_value_id) VALUES ({pv_ids[3]}, {pa2}, {pav_ids[5]})")

        # product_kits
        pk1 = db.execute(text(f"""INSERT INTO product_kits (product_id, kit_name, kit_type, is_active)
               VALUES ({PROD_IDS[0]}, 'طقم كامل', 'bundle', true) RETURNING id""")).scalar()
        count += 1

        # product_kit_items
        exe(f"INSERT INTO product_kit_items (kit_id, component_product_id, quantity, unit_cost, sort_order) VALUES ({pk1}, {PROD_IDS[1]}, 2, 80, 1)")
        exe(f"INSERT INTO product_kit_items (kit_id, component_product_id, quantity, unit_cost, sort_order) VALUES ({pk1}, {PROD_IDS[2]}, 1, 150, 2)")
        exe(f"INSERT INTO product_kit_items (kit_id, component_product_id, quantity, unit_cost, sort_order, notes) VALUES ({pk1}, {PROD_IDS[3]}, 3, 45, 3, 'مواد تغليف')")

        # product_batches
        pb_ids = []
        for b in [
            (PROD_IDS[0], WH_IDS[0], 'BATCH-2025-001', '2025-01-15', '2026-06-15', 200, 180, 50),
            (PROD_IDS[0], WH_IDS[1], 'BATCH-2025-002', '2025-03-01', '2026-09-01', 150, 120, 52),
            (PROD_IDS[1], WH_IDS[0], 'BATCH-2025-003', '2025-06-01', '2027-06-01', 500, 450, 30),
            (PROD_IDS[2], WH_IDS[2], 'BATCH-2025-004', '2025-08-01', None, 100, 95, 120),
        ]:
            exp = f"'{b[4]}'" if b[4] else 'NULL'
            bid = db.execute(text(f"""INSERT INTO product_batches (product_id, warehouse_id, batch_number, manufacturing_date, expiry_date, quantity, available_quantity, unit_cost, status, created_by)
                   VALUES ({b[0]}, {b[1]}, '{b[2]}', '{b[3]}', {exp}, {b[5]}, {b[6]}, {b[7]}, 'active', 1) RETURNING id""")).scalar()
            pb_ids.append(bid)
            count += 1

        # product_serials
        ps_ids = []
        for s in [
            (PROD_IDS[3], WH_IDS[0], 'SN-2025-0001', 'available', 95),
            (PROD_IDS[3], WH_IDS[0], 'SN-2025-0002', 'available', 95),
            (PROD_IDS[3], WH_IDS[1], 'SN-2025-0003', 'sold', 95),
            (PROD_IDS[4], WH_IDS[0], 'SN-2025-0004', 'available', 200),
            (PROD_IDS[4], WH_IDS[2], 'SN-2025-0005', 'in_warranty', 200),
        ]:
            sid = db.execute(text(f"""INSERT INTO product_serials (product_id, warehouse_id, serial_number, status, purchase_price, created_by)
                   VALUES ({s[0]}, {s[1]}, '{s[2]}', '{s[3]}', {s[4]}, 1) RETURNING id""")).scalar()
            ps_ids.append(sid)
            count += 1

        # bin_locations
        bl_ids = []
        for bl in [
            (WH_IDS[0], 'A-01-01', 'رف A-1-1', 'A', '01', '01', '01', 'storage'),
            (WH_IDS[0], 'A-01-02', 'رف A-1-2', 'A', '01', '01', '02', 'storage'),
            (WH_IDS[0], 'B-01-01', 'رف B-1-1', 'B', '01', '02', '01', 'picking'),
            (WH_IDS[1], 'C-01-01', 'رف C-1-1', 'C', '01', '01', '01', 'storage'),
            (WH_IDS[2], 'D-01-01', 'رف D-1-1', 'D', '01', '01', '01', 'receiving'),
        ]:
            bid = db.execute(text(f"""INSERT INTO bin_locations (warehouse_id, bin_code, bin_name, zone, aisle, rack, shelf, bin_type, is_active)
                   VALUES ({bl[0]}, '{bl[1]}', '{bl[2]}', '{bl[3]}', '{bl[4]}', '{bl[5]}', '{bl[6]}', '{bl[7]}', true) RETURNING id""")).scalar()
            bl_ids.append(bid)
            count += 1

        # bin_inventory
        if len(bl_ids) >= 3:
            exe(f"INSERT INTO bin_inventory (bin_id, product_id, quantity) VALUES ({bl_ids[0]}, {PROD_IDS[0]}, 100)")
            exe(f"INSERT INTO bin_inventory (bin_id, product_id, quantity) VALUES ({bl_ids[1]}, {PROD_IDS[1]}, 200)")
            exe(f"INSERT INTO bin_inventory (bin_id, product_id, quantity) VALUES ({bl_ids[2]}, {PROD_IDS[2]}, 50)")
            exe(f"INSERT INTO bin_inventory (bin_id, product_id, batch_id, quantity) VALUES ({bl_ids[0]}, {PROD_IDS[0]}, {pb_ids[0]}, 80)")

        # batch_serial_movements
        exe(f"""INSERT INTO batch_serial_movements (product_id, batch_id, warehouse_id, movement_type, reference_type, quantity, notes, created_by)
                VALUES ({PROD_IDS[0]}, {pb_ids[0]}, {WH_IDS[0]}, 'in', 'purchase', 200, 'استلام دفعة مشتريات', 1)""")
        exe(f"""INSERT INTO batch_serial_movements (product_id, batch_id, warehouse_id, movement_type, reference_type, quantity, notes, created_by)
                VALUES ({PROD_IDS[0]}, {pb_ids[0]}, {WH_IDS[0]}, 'out', 'sale', 20, 'صرف لأمر بيع', 1)""")
        exe(f"""INSERT INTO batch_serial_movements (product_id, serial_id, warehouse_id, movement_type, reference_type, quantity, notes, created_by)
                VALUES ({PROD_IDS[3]}, {ps_ids[0]}, {WH_IDS[0]}, 'in', 'purchase', 1, 'استلام قطعة بالسيريال', 1)""")

        # cycle_counts
        cc1 = db.execute(text(f"""INSERT INTO cycle_counts (count_number, warehouse_id, count_type, status, scheduled_date, total_items, counted_items, variance_items, created_by)
               VALUES ('CC-2026-001', {WH_IDS[0]}, 'full', 'completed', '2026-01-15', 6, 6, 2, 1) RETURNING id""")).scalar()
        cc2 = db.execute(text(f"""INSERT INTO cycle_counts (count_number, warehouse_id, count_type, status, scheduled_date, total_items, counted_items, variance_items, created_by)
               VALUES ('CC-2026-002', {WH_IDS[1]}, 'abc', 'in_progress', '2026-02-20', 4, 2, 1, 1) RETURNING id""")).scalar()
        count += 2

        # cycle_count_items
        exe(f"INSERT INTO cycle_count_items (cycle_count_id, product_id, system_quantity, counted_quantity, variance, variance_value, unit_cost, status, counted_by) VALUES ({cc1}, {PROD_IDS[0]}, 100, 98, -2, -100, 50, 'counted', 1)")
        exe(f"INSERT INTO cycle_count_items (cycle_count_id, product_id, system_quantity, counted_quantity, variance, variance_value, unit_cost, status, counted_by) VALUES ({cc1}, {PROD_IDS[1]}, 200, 200, 0, 0, 30, 'counted', 1)")
        exe(f"INSERT INTO cycle_count_items (cycle_count_id, product_id, system_quantity, counted_quantity, variance, variance_value, unit_cost, status, counted_by) VALUES ({cc1}, {PROD_IDS[2]}, 50, 52, 2, 240, 120, 'counted', 1)")
        exe(f"INSERT INTO cycle_count_items (cycle_count_id, product_id, system_quantity, counted_quantity, variance, variance_value, unit_cost, status) VALUES ({cc2}, {PROD_IDS[3]}, 80, 78, -2, -190, 95, 'pending')")

        # stock_shipments
        sh1 = db.execute(text(f"""INSERT INTO stock_shipments (shipment_ref, source_warehouse_id, destination_warehouse_id, status, notes, created_by)
               VALUES ('SHP-2026-001', {WH_IDS[0]}, {WH_IDS[1]}, 'received', 'نقل بضاعة للفرع', 1) RETURNING id""")).scalar()
        sh2 = db.execute(text(f"""INSERT INTO stock_shipments (shipment_ref, source_warehouse_id, destination_warehouse_id, status, notes, created_by)
               VALUES ('SHP-2026-002', {WH_IDS[1]}, {WH_IDS[2]}, 'shipped', 'تحويل مخزون', 1) RETURNING id""")).scalar()
        count += 2

        # stock_shipment_items
        exe(f"INSERT INTO stock_shipment_items (shipment_id, product_id, quantity) VALUES ({sh1}, {PROD_IDS[0]}, 30)")
        exe(f"INSERT INTO stock_shipment_items (shipment_id, product_id, quantity) VALUES ({sh1}, {PROD_IDS[1]}, 50)")
        exe(f"INSERT INTO stock_shipment_items (shipment_id, product_id, quantity) VALUES ({sh2}, {PROD_IDS[2]}, 20)")

        # ============================================================
        # 7. MANUFACTURING
        # ============================================================
        print("7. Manufacturing...")

        # bom_outputs
        exe(f"INSERT INTO bom_outputs (bom_id, product_id, quantity, cost_allocation_percentage, notes) VALUES ({BOM_IDS[0]}, {PROD_IDS[4]}, 1, 80, 'منتج رئيسي')")
        exe(f"INSERT INTO bom_outputs (bom_id, product_id, quantity, cost_allocation_percentage, notes) VALUES ({BOM_IDS[0]}, {PROD_IDS[5]}, 0.5, 20, 'منتج ثانوي')")

        # maintenance_logs
        exe(f"""INSERT INTO maintenance_logs (equipment_id, maintenance_type, description, cost, performed_by, maintenance_date, next_due_date, status)
                VALUES ({EQUIP_IDS[0]}, 'preventive', 'صيانة دورية شهرية', 2500, 1, '2026-01-15', '2026-02-15', 'completed')""")
        exe(f"""INSERT INTO maintenance_logs (equipment_id, maintenance_type, description, cost, performed_by, maintenance_date, next_due_date, status)
                VALUES ({EQUIP_IDS[1]}, 'corrective', 'إصلاح عطل في المحرك', 8000, 1, '2026-02-01', '2026-08-01', 'completed')""")
        exe(f"""INSERT INTO maintenance_logs (equipment_id, maintenance_type, description, cost, external_service_provider, maintenance_date, next_due_date, status)
                VALUES ({EQUIP_IDS[0]}, 'inspection', 'فحص سنوي شامل', 1500, 'شركة الفحص المتقدم', '2025-12-01', '2026-12-01', 'completed')""")

        # mfg_qc_checks
        exe(f"""INSERT INTO mfg_qc_checks (production_order_id, check_name, check_type, specification, actual_value, result, checked_by)
                VALUES ({PO_IDS[0]}, 'فحص الأبعاد', 'measurement', 'الطول 100 ± 0.5 سم', '100.2', 'pass', 1)""")
        exe(f"""INSERT INTO mfg_qc_checks (production_order_id, check_name, check_type, specification, actual_value, result, failure_action, checked_by, notes)
                VALUES ({PO_IDS[0]}, 'فحص اللون', 'visual', 'لون موحد بدون عيوب', 'بقعة صغيرة', 'fail', 'warn', 1, 'يحتاج إعادة طلاء')""")
        exe(f"""INSERT INTO mfg_qc_checks (production_order_id, check_name, check_type, specification, actual_value, result, checked_by)
                VALUES ({PO_IDS[0]}, 'فحص الوزن', 'weight', '5 كغ ± 0.1', '5.05', 'pass', 1)""")

        # mrp_plans
        mrp1 = db.execute(text(f"""INSERT INTO mrp_plans (plan_name, production_order_id, status, notes, created_by)
               VALUES ('خطة MRP - فبراير 2026', {PO_IDS[0]}, 'confirmed', 'خطة الاحتياجات المادية الشهرية', 1) RETURNING id""")).scalar()
        count += 1

        # mrp_items
        for pid in PROD_IDS[:4]:
            exe(f"""INSERT INTO mrp_items (mrp_plan_id, product_id, required_quantity, available_quantity, on_hand_quantity, on_order_quantity, shortage_quantity, lead_time_days, suggested_action, status)
                    VALUES ({mrp1}, {pid}, {100+pid*20}, {80+pid*10}, {60+pid*10}, {20}, {max(0, 100+pid*20-80-pid*10)}, {5+pid}, 'purchase', 'planned')""")

        # quality_inspections
        qi1 = db.execute(text(f"""INSERT INTO quality_inspections (inspection_number, inspection_type, product_id, warehouse_id, reference_type, inspected_quantity, accepted_quantity, rejected_quantity, status, inspector_id, inspection_date, created_by)
               VALUES ('QI-2026-001', 'incoming', {PROD_IDS[0]}, {WH_IDS[0]}, 'purchase_order', 200, 195, 5, 'completed', 1, CURRENT_TIMESTAMP, 1) RETURNING id""")).scalar()
        qi2 = db.execute(text(f"""INSERT INTO quality_inspections (inspection_number, inspection_type, product_id, warehouse_id, reference_type, inspected_quantity, accepted_quantity, rejected_quantity, status, inspector_id, inspection_date, created_by)
               VALUES ('QI-2026-002', 'production', {PROD_IDS[1]}, {WH_IDS[1]}, 'production_order', 100, 98, 2, 'completed', 1, CURRENT_TIMESTAMP, 1) RETURNING id""")).scalar()
        qi3 = db.execute(text(f"""INSERT INTO quality_inspections (inspection_number, inspection_type, product_id, warehouse_id, reference_type, inspected_quantity, accepted_quantity, rejected_quantity, status, inspector_id, inspection_date, created_by)
               VALUES ('QI-2026-003', 'outgoing', {PROD_IDS[2]}, {WH_IDS[0]}, 'sales_order', 50, 50, 0, 'passed', 1, CURRENT_TIMESTAMP, 1) RETURNING id""")).scalar()
        count += 3

        # quality_inspection_criteria
        exe(f"INSERT INTO quality_inspection_criteria (inspection_id, criteria_name, expected_value, actual_value, is_passed) VALUES ({qi1}, 'المظهر الخارجي', 'بدون خدوش', 'سليم', true)")
        exe(f"INSERT INTO quality_inspection_criteria (inspection_id, criteria_name, expected_value, actual_value, is_passed, notes) VALUES ({qi1}, 'الوزن', '5 كغ ±5%', '4.6 كغ', false, 'أقل من الحد')")
        exe(f"INSERT INTO quality_inspection_criteria (inspection_id, criteria_name, expected_value, actual_value, is_passed) VALUES ({qi2}, 'التشطيب', 'ناعم', 'ناعم', true)")
        exe(f"INSERT INTO quality_inspection_criteria (inspection_id, criteria_name, expected_value, actual_value, is_passed) VALUES ({qi3}, 'التغليف', 'سليم ومحكم', 'سليم', true)")

        # ============================================================
        # 8. PURCHASES & SALES EXTENSIONS
        # ============================================================
        print("8. Purchases & Sales...")

        # purchase_agreements
        pa_id1 = db.execute(text("""INSERT INTO purchase_agreements (agreement_number, supplier_id, agreement_type, title, start_date, end_date, total_amount, consumed_amount, status, branch_id, created_by)
               VALUES ('PA-2025-001', 1, 'blanket', 'اتفاقية توريد سنوية - مواد خام', '2025-01-01', '2025-12-31', 500000, 320000, 'active', 1, 1) RETURNING id""")).scalar()
        pa_id2 = db.execute(text("""INSERT INTO purchase_agreements (agreement_number, supplier_id, agreement_type, title, start_date, end_date, total_amount, consumed_amount, status, branch_id, created_by)
               VALUES ('PA-2026-001', 2, 'contract', 'عقد صيانة معدات', '2026-01-01', '2026-12-31', 120000, 0, 'active', 1, 1) RETURNING id""")).scalar()
        count += 2

        # purchase_agreement_lines
        exe(f"INSERT INTO purchase_agreement_lines (agreement_id, product_id, product_name, quantity, unit_price, delivered_qty) VALUES ({pa_id1}, {PROD_IDS[0]}, 'مادة خام 1', 1000, 50, 640)")
        exe(f"INSERT INTO purchase_agreement_lines (agreement_id, product_id, product_name, quantity, unit_price, delivered_qty) VALUES ({pa_id1}, {PROD_IDS[1]}, 'مادة خام 2', 2000, 30, 1200)")
        exe(f"INSERT INTO purchase_agreement_lines (agreement_id, product_name, quantity, unit_price, delivered_qty) VALUES ({pa_id2}, 'خدمة صيانة شهرية', 12, 10000, 2)")

        # rfq_lines
        exe(f"INSERT INTO rfq_lines (rfq_id, product_id, product_name, quantity, unit, specifications) VALUES ({RFQ_ID}, {PROD_IDS[0]}, 'حديد مسلح', 500, 'طن', 'مطابق للمواصفات السعودية')")
        exe(f"INSERT INTO rfq_lines (rfq_id, product_id, product_name, quantity, unit, specifications) VALUES ({RFQ_ID}, {PROD_IDS[1]}, 'أسمنت بورتلاندي', 1000, 'كيس', 'نوع I')")
        exe(f"INSERT INTO rfq_lines (rfq_id, product_name, quantity, unit, specifications) VALUES ({RFQ_ID}, 'رمل ناعم', 200, 'متر مكعب', 'نظيف وخالي من الشوائب')")

        # rfq_responses
        exe(f"INSERT INTO rfq_responses (rfq_id, supplier_id, supplier_name, unit_price, total_price, delivery_days, notes, is_selected) VALUES ({RFQ_ID}, 1, 'مؤسسة الأمان', 2500, 1250000, 14, 'نلتزم بالمواصفات', true)")
        exe(f"INSERT INTO rfq_responses (rfq_id, supplier_id, supplier_name, unit_price, total_price, delivery_days, notes, is_selected) VALUES ({RFQ_ID}, 2, 'شركة التقنية', 2700, 1350000, 10, 'توصيل أسرع', false)")
        exe(f"INSERT INTO rfq_responses (rfq_id, supplier_id, supplier_name, unit_price, total_price, delivery_days, notes, is_selected) VALUES ({RFQ_ID}, 3, 'مصنع الخليج', 2400, 1200000, 21, 'سعر تنافسي', false)")

        # receipts (purchase/customer receipts)
        exe("""INSERT INTO receipts (receipt_number, receipt_type, customer_id, receipt_date, amount, currency, exchange_rate, payment_method, reference, notes, status, created_by)
               VALUES ('REC-2025-001', 'customer', 5, '2025-10-15', 50000, 'SAR', 1, 'bank_transfer', 'TRF-001', 'استلام دفعة', 'confirmed', 1)""")
        exe("""INSERT INTO receipts (receipt_number, receipt_type, customer_id, receipt_date, amount, currency, exchange_rate, payment_method, reference, notes, status, created_by)
               VALUES ('REC-2025-002', 'customer', 6, '2025-11-01', 25000, 'SAR', 1, 'cash', 'CASH-001', 'نقدي', 'confirmed', 1)""")
        exe("""INSERT INTO receipts (receipt_number, receipt_type, supplier_id, receipt_date, amount, currency, exchange_rate, payment_method, reference, notes, status, created_by)
               VALUES ('REC-2025-003', 'supplier', 1, '2025-12-01', 80000, 'SAR', 1, 'check', 'CHK-P-001', 'سداد مورد', 'confirmed', 1)""")

        # pending_payables
        exe(f"INSERT INTO pending_payables (supplier_id, invoice_id, invoice_number, due_date, amount, paid_amount, outstanding_amount, days_overdue, status) VALUES (1, {INV_IDS[3]}, 'PINV-2025-010', '2025-12-01', 45000, 30000, 15000, 84, 'overdue')")
        exe(f"INSERT INTO pending_payables (supplier_id, invoice_id, invoice_number, due_date, amount, paid_amount, outstanding_amount, days_overdue, status) VALUES (3, {INV_IDS[4]}, 'PINV-2025-011', '2026-03-01', 22000, 0, 22000, 0, 'pending')")

        # pending_receivables
        exe(f"INSERT INTO pending_receivables (customer_id, invoice_id, invoice_number, due_date, amount, paid_amount, outstanding_amount, days_overdue, status) VALUES (5, {INV_IDS[0]}, 'SINV-2025-001', '2025-11-01', 80000, 50000, 30000, 114, 'overdue')")
        exe(f"INSERT INTO pending_receivables (customer_id, invoice_id, invoice_number, due_date, amount, paid_amount, outstanding_amount, days_overdue, status) VALUES (7, {INV_IDS[1]}, 'SINV-2025-002', '2026-02-28', 35000, 0, 35000, 0, 'pending')")

        # commission_rules
        exe("INSERT INTO commission_rules (name, salesperson_id, rate_type, rate, min_amount, is_active, branch_id) VALUES ('عمولة مبيعات عامة', 1, 'percentage', 5, 1000, true, 1)")
        exe(f"INSERT INTO commission_rules (name, product_id, rate_type, rate, is_active, branch_id) VALUES ('عمولة منتج خاص', {PROD_IDS[0]}, 'fixed', 50, true, 1)")

        # sales_commissions
        exe(f"""INSERT INTO sales_commissions (salesperson_id, salesperson_name, invoice_id, invoice_number, invoice_date, invoice_total, commission_rate, commission_amount, status, branch_id)
                VALUES (1, 'mohammed', {INV_IDS[0]}, 'SINV-001', '2025-09-01', 80000, 5, 4000, 'paid', 1)""")
        exe(f"""INSERT INTO sales_commissions (salesperson_id, salesperson_name, invoice_id, invoice_number, invoice_date, invoice_total, commission_rate, commission_amount, status, branch_id)
                VALUES (1, 'mohammed', {INV_IDS[1]}, 'SINV-002', '2025-10-01', 35000, 5, 1750, 'pending', 1)""")

        # sales_targets
        for m in range(1, 7):
            exe(f"INSERT INTO sales_targets (year, month_number, target_amount, branch_id, salesperson_id, created_by) VALUES (2026, {m}, {100000+m*10000}, 1, 1, 1)")

        # opportunity_activities
        exe(f"INSERT INTO opportunity_activities (opportunity_id, activity_type, title, description, due_date, completed, created_by) VALUES ({OPP_IDS[0]}, 'call', 'اتصال متابعة', 'متابعة العرض المقدم', '2026-02-25', false, 1)")
        exe(f"INSERT INTO opportunity_activities (opportunity_id, activity_type, title, description, due_date, completed, created_by) VALUES ({OPP_IDS[0]}, 'meeting', 'اجتماع عرض', 'تقديم العرض الفني', '2026-02-20', true, 1)")
        exe(f"INSERT INTO opportunity_activities (opportunity_id, activity_type, title, description, due_date, completed, created_by) VALUES ({OPP_IDS[1]}, 'email', 'إرسال عرض سعر', 'إرسال عرض سعر محدث', '2026-02-22', true, 1)")

        # ============================================================
        # 9. SERVICES
        # ============================================================
        print("9. Services...")

        # service_request_costs
        exe(f"INSERT INTO service_request_costs (service_request_id, cost_type, description, amount, created_by) VALUES ({SR_IDS[0]}, 'labor', 'أجور فنيين', 3000, 1)")
        exe(f"INSERT INTO service_request_costs (service_request_id, cost_type, description, amount, created_by) VALUES ({SR_IDS[0]}, 'materials', 'قطع غيار', 1500, 1)")
        exe(f"INSERT INTO service_request_costs (service_request_id, cost_type, description, amount, created_by) VALUES ({SR_IDS[1]}, 'labor', 'أجور صيانة', 2000, 1)")
        exe(f"INSERT INTO service_request_costs (service_request_id, cost_type, description, amount, created_by) VALUES ({SR_IDS[2]}, 'transport', 'مصاريف نقل', 500, 1)")

        # ticket_comments
        exe(f"INSERT INTO ticket_comments (ticket_id, comment, is_internal, created_by) VALUES ({TICKET_IDS[0]}, 'تم فحص المشكلة وتحديد السبب', false, 1)")
        exe(f"INSERT INTO ticket_comments (ticket_id, comment, is_internal, created_by) VALUES ({TICKET_IDS[0]}, 'ملاحظة داخلية: يحتاج قطع غيار', true, 1)")
        exe(f"INSERT INTO ticket_comments (ticket_id, comment, is_internal, created_by) VALUES ({TICKET_IDS[1]}, 'تم حل المشكلة بنجاح', false, 1)")
        exe(f"INSERT INTO ticket_comments (ticket_id, comment, is_internal, created_by) VALUES ({TICKET_IDS[2]}, 'جاري العمل على الطلب', false, 1)")

        # service_documents
        exe("INSERT INTO service_documents (title, description, category, file_name, file_size, mime_type, version, created_by) VALUES ('دليل الصيانة', 'دليل صيانة المعدات', 'manual', 'maintenance_guide.pdf', 2048000, 'application/pdf', 1, 1)")
        exe("INSERT INTO service_documents (title, description, category, file_name, file_size, mime_type, version, created_by) VALUES ('نموذج طلب خدمة', 'نموذج لتقديم طلبات الخدمة', 'form', 'service_request_form.docx', 512000, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 1, 1)")

        # ============================================================
        # 10. DOCUMENTS & ATTACHMENTS
        # ============================================================
        print("10. Documents...")

        # document_types
        exe("INSERT INTO document_types (type_code, type_name, type_name_en, description, allowed_extensions, max_size, is_active) VALUES ('DT-INV', 'فاتورة', 'Invoice', 'مستندات الفواتير', 'pdf,jpg,png', 10, true)")
        exe("INSERT INTO document_types (type_code, type_name, type_name_en, description, allowed_extensions, max_size, is_active) VALUES ('DT-CON', 'عقد', 'Contract', 'عقود واتفاقيات', 'pdf,docx', 20, true)")
        exe("INSERT INTO document_types (type_code, type_name, type_name_en, description, allowed_extensions, max_size, is_active) VALUES ('DT-RPT', 'تقرير', 'Report', 'تقارير متنوعة', 'pdf,xlsx', 15, true)")

        # document_templates
        exe("""INSERT INTO document_templates (template_name, template_type, description, template_content, is_default)
               VALUES ('نموذج فاتورة', 'invoice', 'قالب فاتورة مبيعات', '<html><body><h1>فاتورة</h1><p>{{customer_name}}</p></body></html>', true)""")
        exe("""INSERT INTO document_templates (template_name, template_type, description, template_content, is_default)
               VALUES ('نموذج عقد', 'contract', 'قالب عقد خدمات', '<html><body><h1>عقد خدمات</h1><p>{{party_name}}</p></body></html>', false)""")

        # attachments
        exe(f"INSERT INTO attachments (entity_type, entity_id, file_name, file_path, file_size, file_type, mime_type, description, uploaded_by) VALUES ('invoice', {INV_IDS[0]}, 'invoice_scan.pdf', '/uploads/invoices/inv1.pdf', 1024000, 'pdf', 'application/pdf', 'نسخة ممسوحة', 1)")
        exe(f"INSERT INTO attachments (entity_type, entity_id, file_name, file_path, file_size, file_type, mime_type, description, uploaded_by) VALUES ('contract', {CONTRACT_IDS[0]}, 'contract_signed.pdf', '/uploads/contracts/con1.pdf', 2048000, 'pdf', 'application/pdf', 'عقد موقع', 1)")
        exe(f"INSERT INTO attachments (entity_type, entity_id, file_name, file_path, file_size, file_type, mime_type, description, uploaded_by) VALUES ('expense', {EXP_IDS[0]}, 'receipt.jpg', '/uploads/expenses/exp1.jpg', 512000, 'jpg', 'image/jpeg', 'إيصال المصروف', 1)")

        # ============================================================
        # 11. TAXES & CURRENCIES
        # ============================================================
        print("11. Taxes & Currencies...")

        # exchange_rates
        exe(f"INSERT INTO exchange_rates (currency_id, rate_date, rate, source, created_by) VALUES ({CURR_IDS[1]}, '2026-02-23', 3.75, 'manual', 1)")
        exe(f"INSERT INTO exchange_rates (currency_id, rate_date, rate, source, created_by) VALUES ({CURR_IDS[2]}, '2026-02-23', 4.09, 'manual', 1)")
        exe(f"INSERT INTO exchange_rates (currency_id, rate_date, rate, source, created_by) VALUES ({CURR_IDS[3]}, '2026-02-23', 0.99, 'manual', 1)")
        exe(f"INSERT INTO exchange_rates (currency_id, rate_date, rate, source, created_by) VALUES ({CURR_IDS[1]}, '2026-02-22', 3.75, 'manual', 1)")
        exe(f"INSERT INTO exchange_rates (currency_id, rate_date, rate, source, created_by) VALUES ({CURR_IDS[2]}, '2026-02-22', 4.10, 'manual', 1)")

        # tax_groups
        exe("""INSERT INTO tax_groups (group_code, group_name, group_name_en, description, is_active)
               VALUES ('TG-VAT', 'مجموعة ضريبة القيمة المضافة', 'VAT Group', 'ضريبة القيمة المضافة 15%', true)""")
        exe("""INSERT INTO tax_groups (group_code, group_name, group_name_en, description, is_active)
               VALUES ('TG-WHT', 'مجموعة ضريبة الاستقطاع', 'WHT Group', 'ضريبة الاستقطاع على الخدمات', true)""")
        exe("""INSERT INTO tax_groups (group_code, group_name, group_name_en, description, is_active)
               VALUES ('TG-EXM', 'معفى من الضريبة', 'Tax Exempt', 'معاملات معفاة', true)""")

        # tax_returns
        tr1 = db.execute(text("""INSERT INTO tax_returns (return_number, tax_period, tax_type, taxable_amount, tax_amount, penalty_amount, interest_amount, total_amount, due_date, filed_date, status, branch_id, created_by)
               VALUES ('TR-2025-Q4', '2025-Q4', 'vat', 2500000, 375000, 0, 0, 375000, '2026-01-31', '2026-01-28', 'filed', 1, 1) RETURNING id""")).scalar()
        tr2 = db.execute(text("""INSERT INTO tax_returns (return_number, tax_period, tax_type, taxable_amount, tax_amount, penalty_amount, interest_amount, total_amount, due_date, status, branch_id, created_by)
               VALUES ('TR-2026-Q1', '2026-Q1', 'vat', 1800000, 270000, 0, 0, 270000, '2026-04-30', 'draft', 1, 1) RETURNING id""")).scalar()
        count += 2

        # tax_payments
        exe(f"""INSERT INTO tax_payments (payment_number, tax_return_id, payment_date, amount, payment_method, reference, status, created_by)
                VALUES ('TP-2026-001', {tr1}, '2026-01-28', 375000, 'bank_transfer', 'ZATCA-PAY-001', 'completed', 1)""")
        exe(f"""INSERT INTO tax_payments (payment_number, tax_return_id, payment_date, amount, payment_method, reference, status, created_by)
                VALUES ('TP-2026-002', {tr2}, '2026-04-28', 135000, 'bank_transfer', 'ZATCA-PAY-002', 'pending', 1)""")

        # tax_calendar
        exe("""INSERT INTO tax_calendar (title, tax_type, due_date, is_recurring, recurrence_months, is_completed, notes, created_by)
               VALUES ('إقرار ضريبة القيمة المضافة Q1', 'vat', '2026-04-30', true, 3, false, 'إقرار ربع سنوي', 1)""")
        exe("""INSERT INTO tax_calendar (title, tax_type, due_date, is_recurring, recurrence_months, is_completed, notes, created_by)
               VALUES ('إقرار ضريبة الدخل', 'income_tax', '2026-04-30', true, 12, false, 'إقرار سنوي', 1)""")
        exe("""INSERT INTO tax_calendar (title, tax_type, due_date, is_recurring, recurrence_months, is_completed, notes, created_by)
               VALUES ('إقرار ضريبة الاستقطاع', 'wht', '2026-02-10', true, 1, true, 'إقرار شهري', 1)""")

        # wht_transactions
        exe(f"""INSERT INTO wht_transactions (invoice_id, supplier_id, wht_rate_id, gross_amount, wht_rate, wht_amount, net_amount, certificate_number, status, created_by)
                VALUES ({INV_IDS[3]}, 1, {WHT_IDS[0]}, 100000, 5, 5000, 95000, 'WHT-CERT-001', 'issued', 1)""")
        exe(f"""INSERT INTO wht_transactions (invoice_id, supplier_id, wht_rate_id, gross_amount, wht_rate, wht_amount, net_amount, certificate_number, status, created_by)
                VALUES ({INV_IDS[4]}, 2, {WHT_IDS[1]}, 50000, 15, 7500, 42500, 'WHT-CERT-002', 'issued', 1)""")
        exe(f"""INSERT INTO wht_transactions (invoice_id, supplier_id, wht_rate_id, gross_amount, wht_rate, wht_amount, net_amount, status, created_by)
                VALUES ({INV_IDS[5]}, 3, {WHT_IDS[2]}, 30000, 20, 6000, 24000, 'pending', 1)""")

        # branch_tax_settings
        exe(f"INSERT INTO branch_tax_settings (branch_id, tax_regime_id, is_registered, registration_number, is_active) VALUES (1, {TAX_REG_IDS[0]}, true, '300012345600003', true)")
        exe(f"INSERT INTO branch_tax_settings (branch_id, tax_regime_id, is_registered, registration_number, is_active) VALUES (2, {TAX_REG_IDS[0]}, true, '300012345600004', true)")
        exe(f"INSERT INTO branch_tax_settings (branch_id, tax_regime_id, is_registered, registration_number, is_exempt, exemption_reason, is_active) VALUES (3, {TAX_REG_IDS[0]}, true, '300012345600005', true, 'فرع في منطقة حرة', false)")

        # ============================================================
        # 12. APPROVALS
        # ============================================================
        print("12. Approvals...")

        # approval_requests
        ar1 = db.execute(text(f"""INSERT INTO approval_requests (workflow_id, document_type, document_id, amount, description, current_step, total_steps, status, requested_by)
               VALUES ({WF_IDS[0]}, 'purchase_order', {PUR_IDS[0]}, 150000, 'طلب اعتماد أمر شراء', 2, 2, 'approved', 1) RETURNING id""")).scalar()
        ar2 = db.execute(text(f"""INSERT INTO approval_requests (workflow_id, document_type, document_id, amount, description, current_step, total_steps, status, requested_by)
               VALUES ({WF_IDS[0]}, 'purchase_order', {PUR_IDS[1]}, 85000, 'طلب اعتماد أمر شراء معدات', 1, 2, 'pending', 1) RETURNING id""")).scalar()
        ar3 = db.execute(text(f"""INSERT INTO approval_requests (workflow_id, document_type, document_id, amount, description, current_step, total_steps, status, requested_by)
               VALUES ({WF_IDS[1]}, 'expense', {EXP_IDS[0]}, 5000, 'طلب اعتماد مصروف', 1, 1, 'approved', 1) RETURNING id""")).scalar()
        count += 3

        # approval_actions
        exe(f"INSERT INTO approval_actions (request_id, step, action, actioned_by, notes) VALUES ({ar1}, 1, 'approved', 1, 'موافقة المدير المباشر')")
        exe(f"INSERT INTO approval_actions (request_id, step, action, actioned_by, notes) VALUES ({ar1}, 2, 'approved', 1, 'موافقة المدير المالي')")
        exe(f"INSERT INTO approval_actions (request_id, step, action, actioned_by, notes) VALUES ({ar3}, 1, 'approved', 1, 'موافقة على المصروف')")

        # ============================================================
        # 13. NOTIFICATIONS & MESSAGES
        # ============================================================
        print("13. Notifications & Messages...")

        # notifications
        exe("INSERT INTO notifications (user_id, title, message, link, is_read, type) VALUES (1, 'طلب اعتماد جديد', 'لديك طلب اعتماد أمر شراء بانتظار موافقتك', '/approvals', false, 'approval')")
        exe("INSERT INTO notifications (user_id, title, message, link, is_read, type) VALUES (1, 'تذكير: إقرار ضريبي', 'الموعد النهائي لتقديم إقرار ضريبة القيمة المضافة بعد 30 يوم', '/taxes/returns', false, 'reminder')")
        exe("INSERT INTO notifications (user_id, title, message, link, is_read, type) VALUES (1, 'تم اعتماد أمر الشراء', 'تم اعتماد أمر الشراء PO-2025-001 بنجاح', '/purchases/orders/1', true, 'approval')")
        exe("INSERT INTO notifications (user_id, title, message, link, is_read, type) VALUES (1, 'مخزون منخفض', 'المنتج حديد مسلح وصل للحد الأدنى', '/inventory', false, 'warning')")
        exe("INSERT INTO notifications (user_id, title, message, link, is_read, type) VALUES (1, 'فاتورة متأخرة', 'فاتورة العميل SINV-001 متأخرة 30 يوم', '/invoices/1', false, 'alert')")

        # messages
        exe("INSERT INTO messages (sender_id, receiver_id, subject, body, message_type, is_read) VALUES (1, 1, 'ملاحظات على الميزانية', 'يرجى مراجعة بنود الميزانية للربع الأول', 'internal', true)")
        exe("INSERT INTO messages (sender_id, receiver_id, subject, body, message_type, is_read) VALUES (1, 1, 'اجتماع مراجعة الأداء', 'تذكير باجتماع مراجعة الأداء يوم الأحد', 'notification', false)")
        exe("INSERT INTO messages (sender_id, receiver_id, subject, body, message_type, is_read) VALUES (1, 1, 'تحديث سياسة المصروفات', 'تم تحديث سياسة صرف المصروفات، يرجى الاطلاع', 'announcement', false)")

        # ============================================================
        # 14. RECURRING JOURNALS
        # ============================================================
        print("14. Recurring Journals...")

        rjt1 = db.execute(text("""INSERT INTO recurring_journal_templates (name, description, reference, frequency, start_date, end_date, next_run_date, is_active, auto_post, branch_id, currency, exchange_rate, run_count, max_runs, created_by)
               VALUES ('إيجار شهري', 'قيد إيجار المكتب الشهري', 'RJ-RENT', 'monthly', '2025-01-01', '2025-12-31', '2026-03-01', true, true, 1, 'SAR', 1, 12, 12, 1) RETURNING id""")).scalar()
        rjt2 = db.execute(text("""INSERT INTO recurring_journal_templates (name, description, reference, frequency, start_date, end_date, next_run_date, is_active, auto_post, branch_id, currency, exchange_rate, run_count, max_runs, created_by)
               VALUES ('اشتراك برمجيات', 'قيد اشتراك شهري في البرمجيات', 'RJ-SW', 'monthly', '2025-01-01', '2026-12-31', '2026-03-01', true, false, 1, 'SAR', 1, 14, 24, 1) RETURNING id""")).scalar()
        count += 2

        # recurring_journal_lines
        rent_exp = acct_list[0] if acct_list else 1
        rent_pay = acct_list[1] if len(acct_list) > 1 else 2
        exe(f"INSERT INTO recurring_journal_lines (template_id, account_id, debit, credit, description) VALUES ({rjt1}, {rent_exp}, 15000, 0, 'مصروف إيجار')")
        exe(f"INSERT INTO recurring_journal_lines (template_id, account_id, debit, credit, description) VALUES ({rjt1}, {rent_pay}, 0, 15000, 'دائن - بنك')")
        exe(f"INSERT INTO recurring_journal_lines (template_id, account_id, debit, credit, description) VALUES ({rjt2}, {rent_exp}, 5000, 0, 'مصروف اشتراك برمجيات')")
        exe(f"INSERT INTO recurring_journal_lines (template_id, account_id, debit, credit, description) VALUES ({rjt2}, {rent_pay}, 0, 5000, 'دائن - بنك')")

        # ============================================================
        # 15. POS (Point of Sale)
        # ============================================================
        print("15. POS...")

        # pos_tables
        for t in [
            ('T-01', 'طاولة 1', 'الطابق الأرضي', 4),
            ('T-02', 'طاولة 2', 'الطابق الأرضي', 6),
            ('T-03', 'طاولة 3', 'الطابق العلوي', 2),
            ('T-04', 'طاولة VIP', 'صالة VIP', 8),
        ]:
            exe(f"INSERT INTO pos_tables (table_number, table_name, floor, capacity, status, is_active, branch_id) VALUES ('{t[0]}', '{t[1]}', '{t[2]}', {t[3]}, 'available', true, 1)")

        # pos_promotions
        exe("""INSERT INTO pos_promotions (name, promotion_type, value, min_order_amount, start_date, end_date, is_active, branch_id, created_by)
               VALUES ('خصم بداية الشهر', 'percentage', 10, 100, '2026-02-01', '2026-02-28', true, 1, 1)""")
        exe("""INSERT INTO pos_promotions (name, promotion_type, value, buy_qty, get_qty, start_date, end_date, is_active, branch_id, created_by)
               VALUES ('اشتري 2 واحصل على 1', 'buy_x_get_y', 0, 2, 1, '2026-01-01', '2026-06-30', true, 1, 1)""")

        # pos_loyalty_programs
        lp1 = db.execute(text("""INSERT INTO pos_loyalty_programs (name, points_per_unit, currency_per_point, min_points_redeem, is_active, branch_id)
               VALUES ('برنامج نقاط الولاء', 1, 0.1, 100, true, 1) RETURNING id""")).scalar()
        count += 1

        # pos_loyalty_points
        exe(f"INSERT INTO pos_loyalty_points (program_id, party_id, points_earned, points_redeemed, balance, tier) VALUES ({lp1}, 5, 500, 100, 400, 'silver')")
        exe(f"INSERT INTO pos_loyalty_points (program_id, party_id, points_earned, points_redeemed, balance, tier) VALUES ({lp1}, 6, 1200, 200, 1000, 'gold')")
        exe(f"INSERT INTO pos_loyalty_points (program_id, party_id, points_earned, points_redeemed, balance, tier) VALUES ({lp1}, 7, 150, 0, 150, 'bronze')")

        # pos_sessions
        ps1 = db.execute(text(f"""INSERT INTO pos_sessions (session_code, user_id, warehouse_id, opening_balance, closing_balance, total_sales, total_returns, cash_register_balance, difference, status, opened_at, closed_at, branch_id, treasury_account_id)
               VALUES ('POS-S-001', 1, {WH_IDS[0]}, 1000, 5850, 5200, 350, 5850, 0, 'closed', '2026-02-22 08:00', '2026-02-22 22:00', 1, {TREAS_IDS[0]}) RETURNING id""")).scalar()
        ps2 = db.execute(text(f"""INSERT INTO pos_sessions (session_code, user_id, warehouse_id, opening_balance, total_sales, total_returns, status, opened_at, branch_id, treasury_account_id)
               VALUES ('POS-S-002', 1, {WH_IDS[0]}, 1000, 2800, 0, 'open', '2026-02-23 08:00', 1, {TREAS_IDS[0]}) RETURNING id""")).scalar()
        count += 2

        # pos_orders
        po1 = db.execute(text(f"""INSERT INTO pos_orders (order_number, session_id, customer_id, branch_id, warehouse_id, order_date, status, subtotal, tax_amount, total_amount, paid_amount, change_amount, created_by)
               VALUES ('POS-ORD-001', {ps1}, 5, 1, {WH_IDS[0]}, '2026-02-22 10:30', 'completed', 1200, 180, 1380, 1500, 120, 1) RETURNING id""")).scalar()
        po2 = db.execute(text(f"""INSERT INTO pos_orders (order_number, session_id, walk_in_customer_name, branch_id, warehouse_id, order_date, status, subtotal, tax_amount, total_amount, paid_amount, change_amount, created_by)
               VALUES ('POS-ORD-002', {ps1}, 'عميل زائر', 1, {WH_IDS[0]}, '2026-02-22 14:15', 'completed', 850, 127.5, 977.5, 1000, 22.5, 1) RETURNING id""")).scalar()
        po3 = db.execute(text(f"""INSERT INTO pos_orders (order_number, session_id, customer_id, branch_id, warehouse_id, order_date, status, subtotal, tax_amount, total_amount, paid_amount, change_amount, created_by)
               VALUES ('POS-ORD-003', {ps2}, 6, 1, {WH_IDS[0]}, '2026-02-23 09:45', 'completed', 2300, 345, 2645, 2645, 0, 1) RETURNING id""")).scalar()
        count += 3

        # pos_order_lines
        exe(f"INSERT INTO pos_order_lines (order_id, product_id, description, quantity, original_price, unit_price, tax_rate, tax_amount, subtotal, total, warehouse_id) VALUES ({po1}, {PROD_IDS[0]}, 'منتج 1', 3, 200, 200, 15, 90, 600, 690, {WH_IDS[0]})")
        exe(f"INSERT INTO pos_order_lines (order_id, product_id, description, quantity, original_price, unit_price, tax_rate, tax_amount, subtotal, total, warehouse_id) VALUES ({po1}, {PROD_IDS[1]}, 'منتج 2', 2, 300, 300, 15, 90, 600, 690, {WH_IDS[0]})")
        exe(f"INSERT INTO pos_order_lines (order_id, product_id, description, quantity, original_price, unit_price, tax_rate, tax_amount, subtotal, total, warehouse_id) VALUES ({po2}, {PROD_IDS[2]}, 'منتج 3', 1, 850, 850, 15, 127.5, 850, 977.5, {WH_IDS[0]})")
        exe(f"INSERT INTO pos_order_lines (order_id, product_id, description, quantity, original_price, unit_price, tax_rate, tax_amount, subtotal, total, warehouse_id) VALUES ({po3}, {PROD_IDS[0]}, 'منتج 1', 5, 200, 200, 15, 150, 1000, 1150, {WH_IDS[0]})")
        exe(f"INSERT INTO pos_order_lines (order_id, product_id, description, quantity, original_price, unit_price, tax_rate, tax_amount, subtotal, total, warehouse_id) VALUES ({po3}, {PROD_IDS[3]}, 'منتج 4', 2, 650, 650, 15, 195, 1300, 1495, {WH_IDS[0]})")

        # pos_order_payments
        exe(f"INSERT INTO pos_order_payments (order_id, method, amount, reference) VALUES ({po1}, 'cash', 1500, NULL)")
        exe(f"INSERT INTO pos_order_payments (order_id, method, amount, reference) VALUES ({po2}, 'card', 977.5, 'VISA-4832')")
        exe(f"INSERT INTO pos_order_payments (order_id, method, amount, reference) VALUES ({po3}, 'cash', 1000, NULL)")
        exe(f"INSERT INTO pos_order_payments (order_id, method, amount, reference) VALUES ({po3}, 'card', 1645, 'MADA-9921')")

        # pos_table_orders
        pt_ids = db.execute(text("SELECT id FROM pos_tables ORDER BY id LIMIT 2")).fetchall()
        if len(pt_ids) >= 2:
            exe(f"INSERT INTO pos_table_orders (table_id, order_id, guests, waiter_id, status) VALUES ({pt_ids[0][0]}, {po1}, 3, 1, 'completed')")
            exe(f"INSERT INTO pos_table_orders (table_id, order_id, guests, waiter_id, status) VALUES ({pt_ids[1][0]}, {po3}, 2, 1, 'active')")

        # pos_returns
        pr1 = db.execute(text(f"""INSERT INTO pos_returns (original_order_id, user_id, session_id, refund_amount, refund_method, notes)
               VALUES ({po1}, 1, {ps1}, 690, 'cash', 'إرجاع منتج - عيب تصنيع') RETURNING id""")).scalar()
        count += 1

        # pos_return_items
        po1_lines = db.execute(text(f"SELECT id FROM pos_order_lines WHERE order_id = {po1} LIMIT 1")).fetchone()
        if po1_lines:
            exe(f"INSERT INTO pos_return_items (return_id, original_item_id, quantity, reason) VALUES ({pr1}, {po1_lines[0]}, 1, 'عيب في المنتج')")

        # pos_loyalty_transactions
        lp_ids = db.execute(text("SELECT id FROM pos_loyalty_points ORDER BY id LIMIT 2")).fetchall()
        if len(lp_ids) >= 2:
            exe(f"INSERT INTO pos_loyalty_transactions (loyalty_id, order_id, txn_type, points, description) VALUES ({lp_ids[0][0]}, {po1}, 'earn', 14, 'نقاط من عملية شراء')")
            exe(f"INSERT INTO pos_loyalty_transactions (loyalty_id, order_id, txn_type, points, description) VALUES ({lp_ids[1][0]}, {po3}, 'earn', 26, 'نقاط من عملية شراء')")
            exe(f"INSERT INTO pos_loyalty_transactions (loyalty_id, txn_type, points, description) VALUES ({lp_ids[0][0]}, 'redeem', 50, 'استبدال نقاط')")

        # ============================================================
        # 16. PROJECTS EXTENSIONS
        # ============================================================
        print("16. Projects...")

        # project_budgets
        exe(f"INSERT INTO project_budgets (project_id, budget_type, planned_amount, actual_amount, variance, status) VALUES ({PROJ_IDS[0]}, 'materials', 200000, 180000, 20000, 'active')")
        exe(f"INSERT INTO project_budgets (project_id, budget_type, planned_amount, actual_amount, variance, status) VALUES ({PROJ_IDS[0]}, 'labor', 150000, 140000, 10000, 'active')")
        exe(f"INSERT INTO project_budgets (project_id, budget_type, planned_amount, actual_amount, variance, status) VALUES ({PROJ_IDS[1]}, 'materials', 100000, 60000, 40000, 'active')")
        exe(f"INSERT INTO project_budgets (project_id, budget_type, planned_amount, actual_amount, variance, approved_by, status) VALUES ({PROJ_IDS[2]}, 'total', 500000, 0, 500000, 1, 'draft')")

        # project_change_orders
        exe(f"""INSERT INTO project_change_orders (project_id, change_order_number, title, description, change_type, cost_impact, time_impact_days, status, requested_by, approved_by)
                VALUES ({PROJ_IDS[0]}, 'CO-001', 'تغيير في المواصفات', 'تعديل مواصفات الأرضيات', 'scope_change', 25000, 10, 'approved', 1, 1)""")
        exe(f"""INSERT INTO project_change_orders (project_id, change_order_number, title, description, change_type, cost_impact, time_impact_days, status, requested_by)
                VALUES ({PROJ_IDS[1]}, 'CO-002', 'زيادة كمية', 'زيادة كميات الحديد 20%', 'quantity_change', 40000, 5, 'pending', 1)""")

        # project_documents
        exe(f"INSERT INTO project_documents (project_id, file_name, file_url, file_type, uploaded_by) VALUES ({PROJ_IDS[0]}, 'project_plan.pdf', '/uploads/projects/plan.pdf', 'pdf', 1)")
        exe(f"INSERT INTO project_documents (project_id, file_name, file_url, file_type, uploaded_by) VALUES ({PROJ_IDS[0]}, 'technical_spec.docx', '/uploads/projects/spec.docx', 'docx', 1)")
        exe(f"INSERT INTO project_documents (project_id, file_name, file_url, file_type, uploaded_by) VALUES ({PROJ_IDS[1]}, 'budget_report.xlsx', '/uploads/projects/budget.xlsx', 'xlsx', 1)")

        # project_expenses
        exe(f"INSERT INTO project_expenses (project_id, expense_type, expense_date, amount, description, status, created_by) VALUES ({PROJ_IDS[0]}, 'materials', '2025-10-15', 45000, 'شراء مواد بناء', 'approved', 1)")
        exe(f"INSERT INTO project_expenses (project_id, expense_type, expense_date, amount, description, status, created_by) VALUES ({PROJ_IDS[0]}, 'labor', '2025-11-01', 30000, 'أجور عمال شهر نوفمبر', 'approved', 1)")
        exe(f"INSERT INTO project_expenses (project_id, expense_type, expense_date, amount, description, status, created_by) VALUES ({PROJ_IDS[1]}, 'equipment', '2025-12-01', 15000, 'إيجار معدات', 'pending', 1)")

        # project_revenues
        exe(f"INSERT INTO project_revenues (project_id, revenue_type, revenue_date, amount, description, status, created_by) VALUES ({PROJ_IDS[0]}, 'milestone', '2025-09-30', 100000, 'دفعة إنجاز المرحلة الأولى', 'received', 1)")
        exe(f"INSERT INTO project_revenues (project_id, revenue_type, revenue_date, amount, description, status, created_by) VALUES ({PROJ_IDS[0]}, 'milestone', '2025-12-31', 80000, 'دفعة المرحلة الثانية', 'invoiced', 1)")
        exe(f"INSERT INTO project_revenues (project_id, revenue_type, revenue_date, amount, description, status, created_by) VALUES ({PROJ_IDS[1]}, 'advance', '2025-08-01', 50000, 'دفعة مقدمة', 'received', 1)")

        # project_timesheets
        exe(f"INSERT INTO project_timesheets (employee_id, project_id, task_id, date, hours, description, status) VALUES (1, {PROJ_IDS[0]}, {TASK_IDS[0]}, '2026-02-20', 8, 'عمل على التصميم', 'approved')")
        exe(f"INSERT INTO project_timesheets (employee_id, project_id, task_id, date, hours, description, status) VALUES (1, {PROJ_IDS[0]}, {TASK_IDS[1]}, '2026-02-20', 6, 'مراجعة المخططات', 'approved')")
        exe(f"INSERT INTO project_timesheets (employee_id, project_id, task_id, date, hours, description, status) VALUES (1, {PROJ_IDS[1]}, {TASK_IDS[2]}, '2026-02-21', 4, 'تنفيذ ميداني', 'pending')")
        exe(f"INSERT INTO project_timesheets (employee_id, project_id, task_id, date, hours, description, status) VALUES (1, {PROJ_IDS[0]}, {TASK_IDS[0]}, '2026-02-21', 7.5, 'متابعة التنفيذ', 'draft')")

        # ============================================================
        # 17. REPORTS & SYSTEM
        # ============================================================
        print("17. Reports & System...")

        # financial_reports
        exe("""INSERT INTO financial_reports (report_name, report_type, report_period, generated_date, parameters, data, created_by)
               VALUES ('ميزان المراجعة Q4-2025', 'trial_balance', '2025-Q4', CURRENT_TIMESTAMP, '{"year": 2025, "quarter": 4}'::jsonb, '{"total_debit": 5000000, "total_credit": 5000000}'::jsonb, 1)""")
        exe("""INSERT INTO financial_reports (report_name, report_type, report_period, generated_date, parameters, data, created_by)
               VALUES ('قائمة الدخل 2025', 'income_statement', '2025-FY', CURRENT_TIMESTAMP, '{"year": 2025}'::jsonb, '{"revenue": 3000000, "expenses": 2200000, "net_income": 800000}'::jsonb, 1)""")
        exe("""INSERT INTO financial_reports (report_name, report_type, report_period, generated_date, parameters, data, created_by)
               VALUES ('الميزانية العمومية 2025', 'balance_sheet', '2025-12-31', CURRENT_TIMESTAMP, '{"date": "2025-12-31"}'::jsonb, '{"total_assets": 8000000, "total_liabilities": 3000000, "equity": 5000000}'::jsonb, 1)""")

        # custom_reports
        exe("""INSERT INTO custom_reports (report_name, description, config, created_by)
               VALUES ('تقرير المبيعات الشهري', 'تقرير مبيعات مخصص حسب الفرع والمنتج', '{"type": "sales", "group_by": ["branch", "product"], "period": "monthly"}'::jsonb, 1)""")
        exe("""INSERT INTO custom_reports (report_name, description, config, created_by)
               VALUES ('تقرير المخزون الحرج', 'تقرير المنتجات تحت الحد الأدنى', '{"type": "inventory", "filter": "below_min", "sort": "quantity_asc"}'::jsonb, 1)""")

        # report_templates
        exe("""INSERT INTO report_templates (template_name, template_type, description, is_default)
               VALUES ('قالب كشف حساب', 'account_statement', 'قالب كشف حساب عميل/مورد', true)""")
        exe("""INSERT INTO report_templates (template_name, template_type, description, is_default)
               VALUES ('قالب تقرير مبيعات', 'sales_report', 'قالب تقرير مبيعات شهري', true)""")

        # scheduled_reports
        exe("""INSERT INTO scheduled_reports (report_name, report_type, report_config, frequency, recipients, format, branch_id, next_run_at, is_active, created_by)
               VALUES ('تقرير مبيعات أسبوعي', 'sales_summary', '{"period": "weekly"}'::jsonb, 'weekly', 'manager@company.sa', 'pdf', 1, '2026-03-01', true, 1)""")
        exe("""INSERT INTO scheduled_reports (report_name, report_type, report_config, frequency, recipients, format, branch_id, next_run_at, is_active, created_by)
               VALUES ('تقرير مخزون شهري', 'inventory_summary', '{"include_zero": false}'::jsonb, 'monthly', 'warehouse@company.sa', 'xlsx', 1, '2026-03-01', true, 1)""")

        # shared_reports
        exe("INSERT INTO shared_reports (report_type, report_id, shared_by, shared_with, permission, message) VALUES ('custom', 1, 1, 1, 'view', 'مشاركة التقرير المالي للربع الرابع')")

        # email_templates
        exe("""INSERT INTO email_templates (template_name, subject, body, is_active)
               VALUES ('ترحيب عميل جديد', 'مرحباً بك في شركتنا', '<p>عزيزي {{customer_name}},</p><p>نرحب بك ونتطلع للتعاون.</p>', true)""")
        exe("""INSERT INTO email_templates (template_name, subject, body, is_active)
               VALUES ('تذكير فاتورة', 'تذكير بفاتورة مستحقة', '<p>عزيزي {{customer_name}},</p><p>نود تذكيركم بالفاتورة رقم {{invoice_number}} المستحقة بتاريخ {{due_date}}.</p>', true)""")
        exe("""INSERT INTO email_templates (template_name, subject, body, is_active)
               VALUES ('إشعار شحن', 'تم شحن طلبك', '<p>عزيزي {{customer_name}},</p><p>تم شحن طلبك رقم {{order_number}}.</p>', true)""")

        # dashboard_layouts
        exe("""INSERT INTO dashboard_layouts (user_id, layout_name, widgets, is_active)
               VALUES (1, 'لوحة المدير المالي', '[{"type": "chart", "title": "الإيرادات", "position": {"x": 0, "y": 0}}, {"type": "kpi", "title": "صافي الربح", "position": {"x": 1, "y": 0}}]'::jsonb, true)""")

        # ============================================================
        # 18. COSTING & PAYMENTS
        # ============================================================
        print("18. Costing & Payments...")

        # costing_policy_details
        exe(f"INSERT INTO costing_policy_details (policy_id, setting_key, setting_value) VALUES ({COST_POL_ID}, 'valuation_method', 'weighted_average')")
        exe(f"INSERT INTO costing_policy_details (policy_id, setting_key, setting_value) VALUES ({COST_POL_ID}, 'cost_includes_landed', 'true')")
        exe(f"INSERT INTO costing_policy_details (policy_id, setting_key, setting_value) VALUES ({COST_POL_ID}, 'auto_recalculate', 'true')")

        # costing_policy_history
        exe("""INSERT INTO costing_policy_history (old_policy_type, new_policy_type, change_date, changed_by, reason, affected_products_count, total_cost_impact, status)
               VALUES ('fifo', 'weighted_average', '2025-06-01', 1, 'توحيد سياسة التكلفة لجميع المنتجات', 6, 15000, 'completed')""")

        # payments
        exe("""INSERT INTO payments (payment_number, payment_type, customer_id, payment_date, amount, currency, exchange_rate, payment_method, reference, notes, status, created_by)
               VALUES ('PAY-2025-001', 'received', 5, '2025-10-15', 50000, 'SAR', 1, 'bank_transfer', 'TRF-C-001', 'استلام دفعة من عميل', 'completed', 1)""")
        exe("""INSERT INTO payments (payment_number, payment_type, supplier_id, payment_date, amount, currency, exchange_rate, payment_method, reference, notes, status, created_by)
               VALUES ('PAY-2025-002', 'sent', 1, '2025-11-01', 80000, 'SAR', 1, 'bank_transfer', 'TRF-S-001', 'سداد مورد', 'completed', 1)""")
        exe("""INSERT INTO payments (payment_number, payment_type, customer_id, payment_date, amount, currency, exchange_rate, payment_method, check_number, check_date, notes, status, created_by)
               VALUES ('PAY-2025-003', 'received', 6, '2025-12-01', 15000, 'SAR', 1, 'check', 'CHK-R-002', '2026-02-15', 'شيك مستلم من عميل', 'pending', 1)""")

        # ============================================================
        # 19. SECURITY & SYSTEM
        # ============================================================
        print("19. Security & System...")

        # user_sessions
        exe("INSERT INTO user_sessions (user_id, token_hash, ip_address, user_agent, login_time, last_activity, is_active) VALUES (1, 'hash_abc123', '192.168.1.100', 'Mozilla/5.0 Chrome/120', CURRENT_TIMESTAMP - interval '2 hours', CURRENT_TIMESTAMP, true)")
        exe("INSERT INTO user_sessions (user_id, token_hash, ip_address, user_agent, login_time, last_activity, is_active) VALUES (1, 'hash_def456', '10.0.0.50', 'Mozilla/5.0 Firefox/121', CURRENT_TIMESTAMP - interval '1 day', CURRENT_TIMESTAMP - interval '1 day', false)")

        # password_history
        exe("INSERT INTO password_history (user_id, password_hash) VALUES (1, '$2b$12$old_hash_placeholder_1')")
        exe("INSERT INTO password_history (user_id, password_hash) VALUES (1, '$2b$12$old_hash_placeholder_2')")

        # api_keys
        exe("""INSERT INTO api_keys (name, key_hash, key_prefix, permissions, rate_limit_per_minute, is_active, created_by, notes)
               VALUES ('مفتاح ERP التكامل', 'hashed_key_erp_integration', 'ak_erp_', '["read", "write"]'::jsonb, 60, true, 1, 'مفتاح لتكامل مع نظام خارجي')""")
        exe("""INSERT INTO api_keys (name, key_hash, key_prefix, permissions, rate_limit_per_minute, is_active, created_by, notes)
               VALUES ('مفتاح التقارير', 'hashed_key_reports', 'ak_rpt_', '["read"]'::jsonb, 30, true, 1, 'مفتاح للوصول للتقارير فقط')""")

        # webhooks
        wh1 = db.execute(text("""INSERT INTO webhooks (name, url, secret, events, is_active, retry_count, timeout_seconds, created_by)
               VALUES ('إشعار المبيعات', 'https://hooks.example.com/sales', 'wh_secret_sales', '["invoice.created", "invoice.paid"]'::jsonb, true, 3, 30, 1) RETURNING id""")).scalar()
        wh2 = db.execute(text("""INSERT INTO webhooks (name, url, secret, events, is_active, retry_count, timeout_seconds, created_by)
               VALUES ('إشعار المخزون', 'https://hooks.example.com/inventory', 'wh_secret_inv', '["stock.low", "stock.adjusted"]'::jsonb, true, 3, 30, 1) RETURNING id""")).scalar()
        count += 2

        # webhook_logs
        exe(f"""INSERT INTO webhook_logs (webhook_id, event, payload, response_status, response_body, success, attempt)
                VALUES ({wh1}, 'invoice.created', '{{"invoice_id": 1, "amount": 80000}}'::jsonb, 200, 'OK', true, 1)""")
        exe(f"""INSERT INTO webhook_logs (webhook_id, event, payload, response_status, response_body, success, attempt)
                VALUES ({wh1}, 'invoice.paid', '{{"invoice_id": 1, "paid_amount": 50000}}'::jsonb, 200, 'OK', true, 1)""")
        exe(f"""INSERT INTO webhook_logs (webhook_id, event, payload, response_status, response_body, success, attempt)
                VALUES ({wh2}, 'stock.low', '{{"product_id": 1, "quantity": 5}}'::jsonb, 500, 'Internal Server Error', false, 1)""")

        # user_2fa_settings
        exe("INSERT INTO user_2fa_settings (user_id, secret_key, is_enabled, backup_codes) VALUES (1, 'JBSWY3DPEHPK3PXP', false, 'code1,code2,code3,code4,code5')")

        db.commit()
        print(f"\n=== DONE! Executed {count} INSERT statements ===")

    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"\nERROR at statement #{count}: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run()
