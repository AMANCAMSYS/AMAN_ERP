#!/usr/bin/env python3
"""
Fix hardcoded Arabic strings in Treasury files by replacing them with t() calls.
Based on actual file content analysis.
"""
import re, os, json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TREASURY = os.path.join(BASE, "frontend", "src", "pages", "Treasury")
LOCALES = os.path.join(BASE, "frontend", "src", "locales")

def add_needed_keys():
    """Add a few missing translation keys needed for the rewrite."""
    new_keys = {
        "checks": {
            "receivable": {
                "checkNumberTitle": {"en": "Check No:", "ar": "شيك رقم:"},
                "dueDateShort": {"en": "Due Date", "ar": "الاستحقاق"},
                "bouncePlaceholder": {"en": "Insufficient funds, signature mismatch...", "ar": "رصيد غير كافٍ، توقيع غير مطابق..."},
            },
            "payable": {
                "checkNumberTitle": {"en": "Check No:", "ar": "شيك رقم:"},
                "dueDateShort": {"en": "Due Date", "ar": "الاستحقاق"},
                "bouncePlaceholder": {"en": "Insufficient funds, signature mismatch...", "ar": "رصيد غير كافٍ، توقيع غير مطابق..."},
            }
        },
        "notesPayable": {
            "beneficiaryName": {"en": "Beneficiary Name", "ar": "اسم المستفيد"},
        }
    }
    
    for lang in ['en', 'ar']:
        path = os.path.join(LOCALES, f"{lang}.json")
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        count = 0
        for top_key, sub in new_keys.items():
            if top_key == "checks":
                if "checks" not in data:
                    data["checks"] = {}
                for mid_key, items in sub.items():
                    if mid_key not in data["checks"]:
                        data["checks"][mid_key] = {}
                    for key, vals in items.items():
                        if key not in data["checks"][mid_key]:
                            data["checks"][mid_key][key] = vals[lang]
                            count += 1
            else:
                if top_key not in data:
                    data[top_key] = {}
                for key, vals in sub.items():
                    if key not in data[top_key]:
                        data[top_key][key] = vals[lang]
                        count += 1
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  {lang}.json: added {count} new keys")


def count_arabic(content):
    return len(re.findall(r'[\u0600-\u06FF]', content))


def fix_notes_receivable():
    path = os.path.join(TREASURY, "NotesReceivable.jsx")
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()
    before = count_arabic(c)
    ns = "notesReceivable"
    
    # Status badge labels (singular)
    c = c.replace(
        "const labels = { pending: 'معلق', collected: 'محصل', protested: 'مرفوض' };",
        f"const labels = {{ pending: t('{ns}.pending'), collected: t('{ns}.collected'), protested: t('{ns}.protested') }};"
    )
    
    # Page header
    c = c.replace('>📜 أوراق القبض</h1>', f">📜 {{t('{ns}.title')}}</h1>")
    c = c.replace('>إدارة وتتبع أوراق القبض (الكمبيالات / السندات لأمر)</p>', f">{{t('{ns}.subtitle')}}</p>")
    
    # Create button
    c = c.replace('/> إنشاء ورقة قبض', f"/> {{t('{ns}.create')}}")
    
    # Stat cards
    c = c.replace('>معلقة</div>', f">{{t('{ns}.pending')}}</div>")
    c = c.replace('>محصلة</div>', f">{{t('{ns}.collected')}}</div>")
    c = c.replace('>مرفوضة</div>', f">{{t('{ns}.protested')}}</div>")
    c = c.replace('>متأخرة</div>', f">{{t('{ns}.overdue')}}</div>")
    
    # Filter options
    c = c.replace('>جميع الحالات</option>', f">{{t('{ns}.allStatuses')}}</option>")
    c = c.replace('value="pending">معلقة</option>', f'value="pending">{{t(\'{ns}.pending\')}}</option>')
    c = c.replace('value="collected">محصلة</option>', f'value="collected">{{t(\'{ns}.collected\')}}</option>')
    c = c.replace('value="protested">مرفوضة</option>', f'value="protested">{{t(\'{ns}.protested\')}}</option>')
    
    # Note count
    c = c.replace('{notes.length} ورقة', f"{{notes.length}} {{t('{ns}.noteCount')}}")
    
    # Table headers
    c = c.replace('<th>رقم الورقة</th>', f"<th>{{t('{ns}.noteNumber')}}</th>")
    c = c.replace('<th>الساحب</th>', f"<th>{{t('{ns}.drawerName')}}</th>")
    c = c.replace('<th>العميل</th>', f"<th>{{t('{ns}.customer')}}</th>")
    c = c.replace('<th>البنك</th>', f"<th>{{t('{ns}.bank')}}</th>")
    c = c.replace('<th className="text-end">المبلغ</th>', f'<th className="text-end">{{t(\'{ns}.amount\')}}</th>')
    c = c.replace('<th>تاريخ الاستحقاق</th>', f"<th>{{t('{ns}.dueDate')}}</th>")
    c = c.replace('<th>الحالة</th>', f"<th>{{t('{ns}.status')}}</th>")
    c = c.replace('<th>إجراءات</th>', f"<th>{{t('{ns}.actions')}}</th>")
    
    # Empty table
    c = c.replace('>لا توجد أوراق قبض</td>', f">{{t('{ns}.noNotes')}}</td>")
    
    # Overdue badge
    c = c.replace('>متأخر</span>', f">{{t('{ns}.overdue')}}</span>")
    
    # Action button titles
    c = c.replace('title="عرض"', f"title={{t('{ns}.view')}}")
    c = c.replace('title="تحصيل"', f"title={{t('{ns}.collect')}}")
    c = c.replace('title="رفض"', f"title={{t('{ns}.protest')}}")
    
    # Create modal header
    c = c.replace('<h3>إنشاء ورقة قبض</h3>', f"<h3>{{t('{ns}.create')}}</h3>")
    
    # Form labels
    c = c.replace('>رقم الورقة *</label>', f">{{t('{ns}.noteNumber')}} *</label>")
    c = c.replace('>المبلغ *</label>', f">{{t('{ns}.amount')}} *</label>")
    c = c.replace('>اسم الساحب</label>', f">{{t('{ns}.drawerName')}}</label>")
    c = c.replace('>البنك</label>', f">{{t('{ns}.bank')}}</label>")
    c = c.replace('>تاريخ الإصدار</label>', f">{{t('{ns}.issueDate')}}</label>")
    c = c.replace('>تاريخ الاستحقاق *</label>', f">{{t('{ns}.dueDate')}} *</label>")
    c = c.replace('>العميل</label>', f">{{t('{ns}.customer')}}</label>")
    c = c.replace('>حساب الخزينة</label>', f">{{t('{ns}.treasuryAccount')}}</label>")
    c = c.replace('>ملاحظات</label>', f">{{t('{ns}.notes')}}</label>")
    
    # Select placeholders
    c = c.replace('>-- اختر --</option>', f">{{t('{ns}.select')}}</option>")
    
    # Modal buttons
    c = c.replace('>إلغاء</button>', f">{{t('{ns}.cancel')}}</button>")
    c = c.replace('>إنشاء</button>', f">{{t('{ns}.createBtn')}}</button>")
    
    # Detail modal
    c = c.replace('<h3>تفاصيل ورقة القبض</h3>', f"<h3>{{t('{ns}.noteDetail')}}</h3>")
    
    # Detail labels array
    c = c.replace("['رقم الورقة',", f"[t('{ns}.noteNumber'),")
    c = c.replace("['المبلغ',", f"[t('{ns}.amount'),")
    c = c.replace("['الساحب',", f"[t('{ns}.drawerName'),")
    c = c.replace("['البنك',", f"[t('{ns}.bank'),")
    c = c.replace("['العميل',", f"[t('{ns}.customer'),")
    c = c.replace("['تاريخ الإصدار',", f"[t('{ns}.issueDate'),")
    c = c.replace("['تاريخ الاستحقاق',", f"[t('{ns}.dueDate'),")
    c = c.replace("['الحالة',", f"[t('{ns}.status'),")
    c = c.replace("['تاريخ التحصيل',", f"[t('{ns}.collectionDate'),")
    c = c.replace("['تاريخ الرفض',", f"[t('{ns}.protestDate'),")
    c = c.replace("['سبب الرفض',", f"[t('{ns}.protestReason'),")
    
    # Notes span in detail
    c = c.replace('>ملاحظات</span>', f">{{t('{ns}.notes')}}</span>")
    
    # Close button
    c = c.replace('>إغلاق</button>', f">{{t('{ns}.close')}}</button>")
    
    # Collect modal
    c = c.replace('<h3>تحصيل ورقة القبض</h3>', f"<h3>{{t('{ns}.collect')}}</h3>")
    c = c.replace(
        '<p>ورقة رقم <strong>{showCollect.note_number}</strong> بمبلغ <strong>{fmt(showCollect.amount)}</strong></p>',
        f"<p>{{t('{ns}.noteInfo', {{ number: showCollect.note_number, amount: fmt(showCollect.amount) }})}}</p>"
    )
    c = c.replace('>تاريخ التحصيل</label>', f">{{t('{ns}.collectionDate')}}</label>")
    c = c.replace('>حساب البنك</label>', f">{{t('{ns}.bankAccount')}}</label>")
    c = c.replace('>تأكيد التحصيل</button>', f">{{t('{ns}.confirmCollect')}}</button>")
    
    # Protest modal
    c = c.replace('<h3>رفض ورقة القبض</h3>', f"<h3>{{t('{ns}.protest')}}</h3>")
    c = c.replace(
        '<p>ورقة رقم <strong>{showProtest.note_number}</strong> بمبلغ <strong>{fmt(showProtest.amount)}</strong></p>',
        f"<p>{{t('{ns}.noteInfo', {{ number: showProtest.note_number, amount: fmt(showProtest.amount) }})}}</p>"
    )
    c = c.replace('>تاريخ الرفض</label>', f">{{t('{ns}.protestDate')}}</label>")
    c = c.replace('>سبب الرفض</label>', f">{{t('{ns}.protestReason')}}</label>")
    c = c.replace('>تأكيد الرفض</button>', f">{{t('{ns}.confirmProtest')}}</button>")
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    after = count_arabic(c)
    print(f"NotesReceivable.jsx: {before} -> {after} Arabic chars")


def fix_notes_payable():
    path = os.path.join(TREASURY, "NotesPayable.jsx")
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()
    before = count_arabic(c)
    ns = "notesPayable"
    
    # Status badge labels
    c = c.replace(
        "const labels = { issued: 'صادرة', paid: 'مسددة', protested: 'مرفوضة' };",
        f"const labels = {{ issued: t('{ns}.issued'), paid: t('{ns}.paid'), protested: t('{ns}.protested') }};"
    )
    
    # Page header
    c = c.replace('>📜 أوراق الدفع</h1>', f">📜 {{t('{ns}.title')}}</h1>")
    c = c.replace('>إدارة وتتبع أوراق الدفع (الكمبيالات / السندات لأمر)</p>', f">{{t('{ns}.subtitle')}}</p>")
    
    # Create button
    c = c.replace('/> إنشاء ورقة دفع', f"/> {{t('{ns}.create')}}")
    
    # Stat cards
    c = c.replace('>صادرة</div>', f">{{t('{ns}.issued')}}</div>")
    c = c.replace('>مسددة</div>', f">{{t('{ns}.paid')}}</div>")
    c = c.replace('>مرفوضة</div>', f">{{t('{ns}.protested')}}</div>")
    c = c.replace('>متأخرة</div>', f">{{t('{ns}.overdue')}}</div>")
    
    # Filter options
    c = c.replace('>جميع الحالات</option>', f">{{t('{ns}.allStatuses')}}</option>")
    c = c.replace('value="issued">صادرة</option>', f'value="issued">{{t(\'{ns}.issued\')}}</option>')
    c = c.replace('value="paid">مسددة</option>', f'value="paid">{{t(\'{ns}.paid\')}}</option>')
    c = c.replace('value="protested">مرفوضة</option>', f'value="protested">{{t(\'{ns}.protested\')}}</option>')
    
    # Note count
    c = c.replace('{notes.length} ورقة', f"{{notes.length}} {{t('{ns}.noteCount')}}")
    
    # Table headers
    c = c.replace('<th>رقم الورقة</th>', f"<th>{{t('{ns}.noteNumber')}}</th>")
    c = c.replace('<th>المستفيد</th>', f"<th>{{t('{ns}.beneficiary')}}</th>")
    c = c.replace('<th>المورد</th>', f"<th>{{t('{ns}.supplier')}}</th>")
    c = c.replace('<th>البنك</th>', f"<th>{{t('{ns}.bank')}}</th>")
    c = c.replace('<th className="text-end">المبلغ</th>', f'<th className="text-end">{{t(\'{ns}.amount\')}}</th>')
    c = c.replace('<th>تاريخ الاستحقاق</th>', f"<th>{{t('{ns}.dueDate')}}</th>")
    c = c.replace('<th>الحالة</th>', f"<th>{{t('{ns}.status')}}</th>")
    c = c.replace('<th>إجراءات</th>', f"<th>{{t('{ns}.actions')}}</th>")
    
    # Empty table
    c = c.replace('>لا توجد أوراق دفع</td>', f">{{t('{ns}.noNotes')}}</td>")
    
    # Overdue badge
    c = c.replace('>متأخر</span>', f">{{t('{ns}.overdue')}}</span>")
    
    # Action button titles  
    c = c.replace('title="عرض"', f"title={{t('{ns}.view')}}")
    c = c.replace('title="سداد"', f"title={{t('{ns}.pay')}}")
    c = c.replace('title="رفض"', f"title={{t('{ns}.protest')}}")
    
    # Create modal
    c = c.replace('<h3>إنشاء ورقة دفع</h3>', f"<h3>{{t('{ns}.create')}}</h3>")
    
    # Form labels
    c = c.replace('>رقم الورقة *</label>', f">{{t('{ns}.noteNumber')}} *</label>")
    c = c.replace('>المبلغ *</label>', f">{{t('{ns}.amount')}} *</label>")
    c = c.replace('>اسم المستفيد</label>', f">{{t('{ns}.beneficiaryName')}}</label>")
    c = c.replace('>البنك</label>', f">{{t('{ns}.bank')}}</label>")
    c = c.replace('>تاريخ الإصدار</label>', f">{{t('{ns}.issueDate')}}</label>")
    c = c.replace('>تاريخ الاستحقاق *</label>', f">{{t('{ns}.dueDate')}} *</label>")
    c = c.replace('>المورد</label>', f">{{t('{ns}.supplier')}}</label>")
    c = c.replace('>حساب الخزينة</label>', f">{{t('{ns}.treasuryAccount')}}</label>")
    c = c.replace('>ملاحظات</label>', f">{{t('{ns}.notes')}}</label>")
    
    # Select
    c = c.replace('>-- اختر --</option>', f">{{t('{ns}.select')}}</option>")
    
    # Modal buttons
    c = c.replace('>إلغاء</button>', f">{{t('{ns}.cancel')}}</button>")
    c = c.replace('>إنشاء</button>', f">{{t('{ns}.createBtn')}}</button>")
    
    # Detail modal
    c = c.replace('<h3>تفاصيل ورقة الدفع</h3>', f"<h3>{{t('{ns}.noteDetail')}}</h3>")
    
    # Detail labels
    c = c.replace("['رقم الورقة',", f"[t('{ns}.noteNumber'),")
    c = c.replace("['المبلغ',", f"[t('{ns}.amount'),")
    c = c.replace("['المستفيد',", f"[t('{ns}.beneficiary'),")
    c = c.replace("['البنك',", f"[t('{ns}.bank'),")
    c = c.replace("['المورد',", f"[t('{ns}.supplier'),")
    c = c.replace("['تاريخ الإصدار',", f"[t('{ns}.issueDate'),")
    c = c.replace("['تاريخ الاستحقاق',", f"[t('{ns}.dueDate'),")
    c = c.replace("['الحالة',", f"[t('{ns}.status'),")
    c = c.replace("['تاريخ السداد',", f"[t('{ns}.paymentDate'),")
    c = c.replace("['تاريخ الرفض',", f"[t('{ns}.protestDate'),")
    c = c.replace("['سبب الرفض',", f"[t('{ns}.protestReason'),")
    
    # Notes span
    c = c.replace('>ملاحظات</span>', f">{{t('{ns}.notes')}}</span>")
    
    # Close
    c = c.replace('>إغلاق</button>', f">{{t('{ns}.close')}}</button>")
    
    # Pay modal
    c = c.replace('<h3>سداد ورقة الدفع</h3>', f"<h3>{{t('{ns}.pay')}}</h3>")
    c = c.replace(
        '<p>ورقة رقم <strong>{showPay.note_number}</strong> بمبلغ <strong>{fmt(showPay.amount)}</strong></p>',
        f"<p>{{t('{ns}.noteInfo', {{ number: showPay.note_number, amount: fmt(showPay.amount) }})}}</p>"
    )
    c = c.replace('>تاريخ السداد</label>', f">{{t('{ns}.paymentDate')}}</label>")
    c = c.replace('>حساب البنك</label>', f">{{t('{ns}.bankAccount')}}</label>")
    c = c.replace('>تأكيد السداد</button>', f">{{t('{ns}.confirmPay')}}</button>")
    
    # Protest modal
    c = c.replace('<h3>رفض ورقة الدفع</h3>', f"<h3>{{t('{ns}.protest')}}</h3>")
    c = c.replace(
        '<p>ورقة رقم <strong>{showProtest.note_number}</strong> بمبلغ <strong>{fmt(showProtest.amount)}</strong></p>',
        f"<p>{{t('{ns}.noteInfo', {{ number: showProtest.note_number, amount: fmt(showProtest.amount) }})}}</p>"
    )
    c = c.replace('>تاريخ الرفض</label>', f">{{t('{ns}.protestDate')}}</label>")
    c = c.replace('>سبب الرفض</label>', f">{{t('{ns}.protestReason')}}</label>")
    c = c.replace('>تأكيد الرفض</button>', f">{{t('{ns}.confirmProtest')}}</button>")
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    after = count_arabic(c)
    print(f"NotesPayable.jsx: {before} -> {after} Arabic chars")


def fix_checks_receivable():
    path = os.path.join(TREASURY, "ChecksReceivable.jsx")
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()
    before = count_arabic(c)
    ns = "checks.receivable"
    
    # Status badge labels  
    c = c.replace(
        "const labels = { pending: '\u0645\u0639\u0644\u0642', collected: '\u0645\u062d\u0635\u0651\u0644', bounced: '\u0645\u0631\u062a\u062c\u0639' }",
        f"const labels = {{ pending: t('{ns}.pending'), collected: t('{ns}.collected'), bounced: t('{ns}.bounced') }}"
    )
    
    # Alert validation
    c = c.replace(
        "return alert('\u064a\u062c\u0628 \u062a\u0639\u0628\u0626\u0629 \u0631\u0642\u0645 \u0627\u0644\u0634\u064a\u0643 \u0648\u0627\u0644\u0645\u0628\u0644\u063a \u0648\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0627\u0633\u062a\u062d\u0642\u0627\u0642')",
        f"return alert(t('{ns}.requiredFields'))"
    )
    
    # Alert errors in catch blocks
    c = c.replace(
        "alert(err.response?.data?.detail || '\u062d\u062f\u062b \u062e\u0637\u0623')",
        f"alert(err.response?.data?.detail || t('{ns}.error'))"
    )
    
    # Page header
    c = c.replace('>\u0634\u064a\u0643\u0627\u062a \u062a\u062d\u062a \u0627\u0644\u062a\u062d\u0635\u064a\u0644</h1>', f">{{t('{ns}.title')}}</h1>")
    c = c.replace('>Checks Receivable - \u0625\u062f\u0627\u0631\u0629 \u0627\u0644\u0634\u064a\u0643\u0627\u062a \u0627\u0644\u0648\u0627\u0631\u062f\u0629</p>', f">{{t('{ns}.subtitle')}}</p>")
    
    # Create button
    c = c.replace('>+ \u062a\u0633\u062c\u064a\u0644 \u0634\u064a\u0643 \u0648\u0627\u0631\u062f</button>', f">+ {{t('{ns}.create')}}</button>")
    
    # Stats cards
    c = c.replace('>\u0645\u0639\u0644\u0642</div>', f">{{t('{ns}.pending')}}</div>")
    c = c.replace('>\u0645\u062d\u0635\u0651\u0644</div>', f">{{t('{ns}.collected')}}</div>")
    c = c.replace('>\u0645\u0631\u062a\u062c\u0639</div>', f">{{t('{ns}.bounced')}}</div>")
    c = c.replace('>\u0645\u0633\u062a\u062d\u0642 \u0627\u0644\u064a\u0648\u0645</div>', f">{{t('{ns}.overdueToday')}}</div>")
    
    # Search placeholder
    c = c.replace(
        'placeholder="\u0628\u062d\u062b \u0628\u0631\u0642\u0645 \u0627\u0644\u0634\u064a\u0643 \u0623\u0648 \u0627\u0644\u0633\u0627\u062d\u0628..."',
        f"placeholder={{t('{ns}.searchPlaceholder')}}"
    )
    
    # Filter options
    c = c.replace('>\u062c\u0645\u064a\u0639 \u0627\u0644\u062d\u0627\u0644\u0627\u062a</option>', f">{{t('{ns}.allStatuses')}}</option>")
    c = c.replace('value="pending">\u0645\u0639\u0644\u0642</option>', f'value="pending">{{t(\'{ns}.pending\')}}</option>')
    c = c.replace('value="collected">\u0645\u062d\u0635\u0651\u0644</option>', f'value="collected">{{t(\'{ns}.collected\')}}</option>')
    c = c.replace('value="bounced">\u0645\u0631\u062a\u062c\u0639</option>', f'value="bounced">{{t(\'{ns}.bounced\')}}</option>')
    
    # Total label
    c = c.replace('>\u0627\u0644\u0625\u062c\u0645\u0627\u0644\u064a: {total}</div>', f">{{t('{ns}.total')}}: {{total}}</div>")
    
    # Table headers
    c = c.replace('<th>\u0631\u0642\u0645 \u0627\u0644\u0634\u064a\u0643</th>', f"<th>{{t('{ns}.checkNumber')}}</th>")
    c = c.replace('<th>\u0627\u0644\u0633\u0627\u062d\u0628</th>', f"<th>{{t('{ns}.drawer')}}</th>")
    c = c.replace('<th>\u0627\u0644\u0628\u0646\u0643</th>', f"<th>{{t('{ns}.bank')}}</th>")
    c = c.replace('<th>\u0627\u0644\u0645\u0628\u0644\u063a</th>', f"<th>{{t('{ns}.amount')}}</th>")
    c = c.replace('<th>\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0627\u0633\u062a\u062d\u0642\u0627\u0642</th>', f"<th>{{t('{ns}.dueDate')}}</th>")
    c = c.replace('<th>\u0627\u0644\u062d\u0627\u0644\u0629</th>', f"<th>{{t('{ns}.status')}}</th>")
    
    # Empty table
    c = c.replace('>\u0644\u0627 \u062a\u0648\u062c\u062f \u0634\u064a\u0643\u0627\u062a</td>', f">{{t('{ns}.noChecks')}}</td>")
    
    # Create modal header
    c = c.replace('<h2>\u062a\u0633\u062c\u064a\u0644 \u0634\u064a\u0643 \u0648\u0627\u0631\u062f</h2>', f"<h2>{{t('{ns}.create')}}</h2>")
    
    # Form labels
    c = c.replace('>\u0631\u0642\u0645 \u0627\u0644\u0634\u064a\u0643 *</label>', f">{{t('{ns}.checkNumber')}} *</label>")
    c = c.replace('>\u0627\u0644\u0645\u0628\u0644\u063a *</label>', f">{{t('{ns}.amount')}} *</label>")
    c = c.replace('>\u0627\u0633\u0645 \u0627\u0644\u0633\u0627\u062d\u0628</label>', f">{{t('{ns}.drawerName')}}</label>")
    c = c.replace('>\u0627\u0644\u0628\u0646\u0643</label>', f">{{t('{ns}.bank')}}</label>")
    c = c.replace('>\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0625\u0635\u062f\u0627\u0631</label>', f">{{t('{ns}.issueDate')}}</label>")
    c = c.replace('>\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0627\u0633\u062a\u062d\u0642\u0627\u0642 *</label>', f">{{t('{ns}.dueDate')}} *</label>")
    c = c.replace('>\u0627\u0644\u0639\u0645\u064a\u0644</label>', f">{{t('{ns}.customer')}}</label>")
    c = c.replace('>\u062d\u0633\u0627\u0628 \u0627\u0644\u062e\u0632\u064a\u0646\u0629</label>', f">{{t('{ns}.treasuryAccount')}}</label>")
    c = c.replace('>\u0645\u0644\u0627\u062d\u0638\u0627\u062a</label>', f">{{t('{ns}.notes')}}</label>")
    
    # Select options
    c = c.replace('>\u0627\u062e\u062a\u0631 \u0627\u0644\u0639\u0645\u064a\u0644</option>', f">{{t('{ns}.selectCustomer')}}</option>")
    c = c.replace('>\u0627\u062e\u062a\u0631 \u0627\u0644\u062e\u0632\u064a\u0646\u0629</option>', f">{{t('{ns}.selectTreasury')}}</option>")
    
    # Create modal buttons
    c = c.replace('>\u0625\u0644\u063a\u0627\u0621</button>', f">{{t('notesReceivable.cancel')}}</button>")
    # Saving ternary
    c = c.replace(
        "{saving ? '\u062c\u0627\u0631\u064a \u0627\u0644\u062d\u0641\u0638...' : '\u062a\u0633\u062c\u064a\u0644 \u0627\u0644\u0634\u064a\u0643'}",
        f"{{saving ? t('{ns}.saving') : t('{ns}.registerCheck')}}"
    )
    
    # Detail modal header
    c = c.replace(
        '<h2>\u0634\u064a\u0643 \u0631\u0642\u0645: {detailItem.check_number}</h2>',
        f"<h2>{{t('{ns}.checkNumberTitle')}} {{detailItem.check_number}}</h2>"
    )
    
    # Detail metric labels
    c = c.replace(
        '>\u0627\u0644\u0645\u0628\u0644\u063a</div><div className="metric-value text-primary"',
        f">{{t('{ns}.amount')}}</div><div className=\"metric-value text-primary\""
    )
    c = c.replace(
        '>\u0627\u0644\u062d\u0627\u0644\u0629</div><div className="metric-value"',
        f">{{t('{ns}.status')}}</div><div className=\"metric-value\""
    )
    c = c.replace(
        '>\u0627\u0644\u0627\u0633\u062a\u062d\u0642\u0627\u0642</div><div className="metric-value"',
        f">{{t('{ns}.dueDateShort')}}</div><div className=\"metric-value\""
    )
    
    # Detail strong labels
    c = c.replace('<strong>\u0627\u0644\u0633\u0627\u062d\u0628:</strong>', f"<strong>{{t('{ns}.drawer')}}:</strong>")
    c = c.replace('<strong>\u0627\u0644\u0628\u0646\u0643:</strong>', f"<strong>{{t('{ns}.bank')}}:</strong>")
    c = c.replace('<strong>\u0627\u0644\u0639\u0645\u064a\u0644:</strong>', f"<strong>{{t('{ns}.customer')}}:</strong>")
    c = c.replace('<strong>\u0627\u0644\u062e\u0632\u064a\u0646\u0629:</strong>', f"<strong>{{t('{ns}.treasury')}}:</strong>")
    c = c.replace('<strong>\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0625\u0635\u062f\u0627\u0631:</strong>', f"<strong>{{t('{ns}.issueDate')}}:</strong>")
    c = c.replace('<strong>\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u062a\u062d\u0635\u064a\u0644:</strong>', f"<strong>{{t('{ns}.collectionDate')}}:</strong>")
    c = c.replace('<strong>\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0627\u0631\u062a\u062c\u0627\u0639:</strong>', f"<strong>{{t('{ns}.bounceDate')}}:</strong>")
    c = c.replace('<strong>\u0633\u0628\u0628 \u0627\u0644\u0627\u0631\u062a\u062c\u0627\u0639:</strong>', f"<strong>{{t('{ns}.bounceReason')}}:</strong>")
    
    # Action buttons in detail
    c = c.replace('>\u2705 \u062a\u062d\u0635\u064a\u0644 \u0627\u0644\u0634\u064a\u0643</button>', f">\u2705 {{t('{ns}.collect')}}</button>")
    c = c.replace('>\u274c \u0634\u064a\u0643 \u0645\u0631\u062a\u062c\u0639</button>', f">\u274c {{t('{ns}.bounce')}}</button>")
    
    # Collect modal
    c = c.replace('<h2>\u062a\u062d\u0635\u064a\u0644 \u0627\u0644\u0634\u064a\u0643</h2>', f"<h2>{{t('{ns}.collect')}}</h2>")
    c = c.replace('>\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u062a\u062d\u0635\u064a\u0644</label>', f">{{t('{ns}.collectionDate')}}</label>")
    c = c.replace('>\u062d\u0633\u0627\u0628 \u0627\u0644\u062e\u0632\u064a\u0646\u0629 (\u0627\u0644\u0628\u0646\u0643)</label>', f">{{t('{ns}.treasuryBank')}}</label>")
    # Saving ternary in collect
    c = c.replace(
        "{saving ? '\u062c\u0627\u0631\u064a...' : '\u062a\u0623\u0643\u064a\u062f \u0627\u0644\u062a\u062d\u0635\u064a\u0644'}",
        f"{{saving ? t('{ns}.processing') : t('{ns}.confirmCollect')}}"
    )
    
    # Bounce modal
    c = c.replace('<h2>\u062a\u0633\u062c\u064a\u0644 \u0634\u064a\u0643 \u0645\u0631\u062a\u062c\u0639</h2>', f"<h2>{{t('{ns}.bounce')}}</h2>")
    c = c.replace('>\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0627\u0631\u062a\u062c\u0627\u0639</label>', f">{{t('{ns}.bounceDate')}}</label>")
    c = c.replace('>\u0633\u0628\u0628 \u0627\u0644\u0627\u0631\u062a\u062c\u0627\u0639</label>', f">{{t('{ns}.bounceReason')}}</label>")
    c = c.replace(
        'placeholder="\u0631\u0635\u064a\u062f \u063a\u064a\u0631 \u0643\u0627\u0641\u064d\u060c \u062a\u0648\u0642\u064a\u0639 \u063a\u064a\u0631 \u0645\u0637\u0627\u0628\u0642..."',
        f"placeholder={{t('{ns}.bouncePlaceholder')}}"
    )
    # Saving ternary in bounce
    c = c.replace(
        "{saving ? '\u062c\u0627\u0631\u064a...' : '\u062a\u0623\u0643\u064a\u062f \u0627\u0644\u0627\u0631\u062a\u062c\u0627\u0639'}",
        f"{{saving ? t('{ns}.processing') : t('{ns}.confirmBounce')}}"
    )
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    after = count_arabic(c)
    print(f"ChecksReceivable.jsx: {before} -> {after} Arabic chars")


def fix_checks_payable():
    path = os.path.join(TREASURY, "ChecksPayable.jsx")
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()
    before = count_arabic(c)
    ns = "checks.payable"
    
    # Status badge  
    c = c.replace(
        "const labels = { issued: '\u0635\u0627\u062f\u0631', cleared: '\u0645\u0635\u0631\u0648\u0641', bounced: '\u0645\u0631\u062a\u062c\u0639' }",
        f"const labels = {{ issued: t('{ns}.issued'), cleared: t('{ns}.cleared'), bounced: t('{ns}.bounced') }}"
    )
    
    # Alert validation
    c = c.replace(
        "return alert('\u064a\u062c\u0628 \u062a\u0639\u0628\u0626\u0629 \u0631\u0642\u0645 \u0627\u0644\u0634\u064a\u0643 \u0648\u0627\u0644\u0645\u0628\u0644\u063a \u0648\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0625\u0635\u062f\u0627\u0631 \u0648\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0627\u0633\u062a\u062d\u0642\u0627\u0642')",
        f"return alert(t('{ns}.requiredFields'))"
    )
    
    # Alert errors
    c = c.replace(
        "alert(err.response?.data?.detail || '\u062d\u062f\u062b \u062e\u0637\u0623')",
        f"alert(err.response?.data?.detail || t('{ns}.error'))"
    )
    
    # Page header
    c = c.replace('>\u0634\u064a\u0643\u0627\u062a \u062a\u062d\u062a \u0627\u0644\u062f\u0641\u0639</h1>', f">{{t('{ns}.title')}}</h1>")
    c = c.replace('>Checks Payable - \u0625\u062f\u0627\u0631\u0629 \u0627\u0644\u0634\u064a\u0643\u0627\u062a \u0627\u0644\u0635\u0627\u062f\u0631\u0629</p>', f">{{t('{ns}.subtitle')}}</p>")
    
    # Create button
    c = c.replace('>+ \u0625\u0635\u062f\u0627\u0631 \u0634\u064a\u0643</button>', f">+ {{t('{ns}.create')}}</button>")
    
    # Stats
    c = c.replace('>\u0635\u0627\u062f\u0631</div>', f">{{t('{ns}.issued')}}</div>")
    c = c.replace('>\u0645\u0635\u0631\u0648\u0641</div>', f">{{t('{ns}.cleared')}}</div>")
    c = c.replace('>\u0645\u0631\u062a\u062c\u0639</div>', f">{{t('{ns}.bounced')}}</div>")
    c = c.replace('>\u0645\u0633\u062a\u062d\u0642 \u0627\u0644\u064a\u0648\u0645</div>', f">{{t('{ns}.overdueToday')}}</div>")
    
    # Search
    c = c.replace(
        'placeholder="\u0628\u062d\u062b \u0628\u0631\u0642\u0645 \u0627\u0644\u0634\u064a\u0643 \u0623\u0648 \u0627\u0644\u0645\u0633\u062a\u0641\u064a\u062f..."',
        f"placeholder={{t('{ns}.searchPlaceholder')}}"
    )
    
    # Filter options
    c = c.replace('>\u062c\u0645\u064a\u0639 \u0627\u0644\u062d\u0627\u0644\u0627\u062a</option>', f">{{t('{ns}.allStatuses')}}</option>")
    c = c.replace('value="issued">\u0635\u0627\u062f\u0631</option>', f'value="issued">{{t(\'{ns}.issued\')}}</option>')
    c = c.replace('value="cleared">\u0645\u0635\u0631\u0648\u0641</option>', f'value="cleared">{{t(\'{ns}.cleared\')}}</option>')
    c = c.replace('value="bounced">\u0645\u0631\u062a\u062c\u0639</option>', f'value="bounced">{{t(\'{ns}.bounced\')}}</option>')
    
    # Total
    c = c.replace('>\u0627\u0644\u0625\u062c\u0645\u0627\u0644\u064a: {total}</div>', f">{{t('{ns}.total')}}: {{total}}</div>")
    
    # Table headers
    c = c.replace('<th>\u0631\u0642\u0645 \u0627\u0644\u0634\u064a\u0643</th>', f"<th>{{t('{ns}.checkNumber')}}</th>")
    c = c.replace('<th>\u0627\u0644\u0645\u0633\u062a\u0641\u064a\u062f</th>', f"<th>{{t('{ns}.beneficiary')}}</th>")
    c = c.replace('<th>\u0627\u0644\u0628\u0646\u0643</th>', f"<th>{{t('{ns}.bank')}}</th>")
    c = c.replace('<th>\u0627\u0644\u0645\u0628\u0644\u063a</th>', f"<th>{{t('{ns}.amount')}}</th>")
    c = c.replace('<th>\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0627\u0633\u062a\u062d\u0642\u0627\u0642</th>', f"<th>{{t('{ns}.dueDate')}}</th>")
    c = c.replace('<th>\u0627\u0644\u062d\u0627\u0644\u0629</th>', f"<th>{{t('{ns}.status')}}</th>")
    
    # Empty table
    c = c.replace('>\u0644\u0627 \u062a\u0648\u062c\u062f \u0634\u064a\u0643\u0627\u062a</td>', f">{{t('{ns}.noChecks')}}</td>")
    
    # Create modal
    c = c.replace('<h2>\u0625\u0635\u062f\u0627\u0631 \u0634\u064a\u0643</h2>', f"<h2>{{t('{ns}.create')}}</h2>")
    
    # Form labels
    c = c.replace('>\u0631\u0642\u0645 \u0627\u0644\u0634\u064a\u0643 *</label>', f">{{t('{ns}.checkNumber')}} *</label>")
    c = c.replace('>\u0627\u0644\u0645\u0628\u0644\u063a *</label>', f">{{t('{ns}.amount')}} *</label>")
    c = c.replace('>\u0627\u0633\u0645 \u0627\u0644\u0645\u0633\u062a\u0641\u064a\u062f</label>', f">{{t('{ns}.beneficiary')}}</label>")
    c = c.replace('>\u0627\u0644\u0628\u0646\u0643</label>', f">{{t('{ns}.bank')}}</label>")
    c = c.replace('>\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0625\u0635\u062f\u0627\u0631 *</label>', f">{{t('{ns}.issueDate')}} *</label>")
    c = c.replace('>\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0627\u0633\u062a\u062d\u0642\u0627\u0642 *</label>', f">{{t('{ns}.dueDate')}} *</label>")
    c = c.replace('>\u0627\u0644\u0645\u0648\u0631\u062f</label>', f">{{t('{ns}.supplier')}}</label>")
    c = c.replace('>\u062d\u0633\u0627\u0628 \u0627\u0644\u062e\u0632\u064a\u0646\u0629</label>', f">{{t('{ns}.treasuryAccount')}}</label>")
    c = c.replace('>\u0645\u0644\u0627\u062d\u0638\u0627\u062a</label>', f">{{t('{ns}.notes')}}</label>")
    
    # Select options
    c = c.replace('>\u0627\u062e\u062a\u0631 \u0627\u0644\u0645\u0648\u0631\u062f</option>', f">{{t('{ns}.selectSupplier')}}</option>")
    c = c.replace('>\u0627\u062e\u062a\u0631 \u0627\u0644\u062e\u0632\u064a\u0646\u0629</option>', f">{{t('{ns}.selectTreasury')}}</option>")
    
    # Modal buttons
    c = c.replace('>\u0625\u0644\u063a\u0627\u0621</button>', f">{{t('notesReceivable.cancel')}}</button>")
    # Saving ternary
    c = c.replace(
        "{saving ? '\u062c\u0627\u0631\u064a \u0627\u0644\u062d\u0641\u0638...' : '\u0625\u0635\u062f\u0627\u0631 \u0627\u0644\u0634\u064a\u0643'}",
        f"{{saving ? t('{ns}.saving') : t('{ns}.issueCheck')}}"
    )
    
    # Detail modal
    c = c.replace(
        '<h2>\u0634\u064a\u0643 \u0631\u0642\u0645: {detailItem.check_number}</h2>',
        f"<h2>{{t('{ns}.checkNumberTitle')}} {{detailItem.check_number}}</h2>"
    )
    
    # Metric labels
    c = c.replace(
        '>\u0627\u0644\u0645\u0628\u0644\u063a</div><div className="metric-value text-primary"',
        f">{{t('{ns}.amount')}}</div><div className=\"metric-value text-primary\""
    )
    c = c.replace(
        '>\u0627\u0644\u062d\u0627\u0644\u0629</div><div className="metric-value"',
        f">{{t('{ns}.status')}}</div><div className=\"metric-value\""
    )
    c = c.replace(
        '>\u0627\u0644\u0627\u0633\u062a\u062d\u0642\u0627\u0642</div><div className="metric-value"',
        f">{{t('{ns}.dueDateShort')}}</div><div className=\"metric-value\""
    )
    
    # Detail strong labels
    c = c.replace('<strong>\u0627\u0644\u0645\u0633\u062a\u0641\u064a\u062f:</strong>', f"<strong>{{t('{ns}.beneficiary')}}:</strong>")
    c = c.replace('<strong>\u0627\u0644\u0628\u0646\u0643:</strong>', f"<strong>{{t('{ns}.bank')}}:</strong>")
    c = c.replace('<strong>\u0627\u0644\u0645\u0648\u0631\u062f:</strong>', f"<strong>{{t('{ns}.supplier')}}:</strong>")
    c = c.replace('<strong>\u0627\u0644\u062e\u0632\u064a\u0646\u0629:</strong>', f"<strong>{{t('{ns}.treasuryAccount')}}:</strong>")
    c = c.replace('<strong>\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0625\u0635\u062f\u0627\u0631:</strong>', f"<strong>{{t('{ns}.issueDate')}}:</strong>")
    c = c.replace('<strong>\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0635\u0631\u0641:</strong>', f"<strong>{{t('{ns}.clearanceDate')}}:</strong>")
    c = c.replace('<strong>\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0627\u0631\u062a\u062c\u0627\u0639:</strong>', f"<strong>{{t('{ns}.bounceDate')}}:</strong>")
    c = c.replace('<strong>\u0633\u0628\u0628 \u0627\u0644\u0627\u0631\u062a\u062c\u0627\u0639:</strong>', f"<strong>{{t('{ns}.bounceReason')}}:</strong>")
    
    # Action buttons
    c = c.replace('>\u2705 \u0635\u0631\u0641 \u0627\u0644\u0634\u064a\u0643</button>', f">\u2705 {{t('{ns}.clear')}}</button>")
    c = c.replace('>\u274c \u0634\u064a\u0643 \u0645\u0631\u062a\u062c\u0639</button>', f">\u274c {{t('{ns}.bounce')}}</button>")
    
    # Clear modal
    c = c.replace('<h2>\u0635\u0631\u0641 \u0627\u0644\u0634\u064a\u0643</h2>', f"<h2>{{t('{ns}.clear')}}</h2>")
    c = c.replace('>\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0635\u0631\u0641</label>', f">{{t('{ns}.clearanceDate')}}</label>")
    c = c.replace('>\u062d\u0633\u0627\u0628 \u0627\u0644\u062e\u0632\u064a\u0646\u0629 (\u0627\u0644\u0628\u0646\u0643)</label>', f">{{t('{ns}.treasuryBank')}}</label>")
    c = c.replace(
        "{saving ? '\u062c\u0627\u0631\u064a...' : '\u062a\u0623\u0643\u064a\u062f \u0627\u0644\u0635\u0631\u0641'}",
        f"{{saving ? t('{ns}.processing') : t('{ns}.confirmClear')}}"
    )
    
    # Bounce modal
    c = c.replace('<h2>\u062a\u0633\u062c\u064a\u0644 \u0634\u064a\u0643 \u0645\u0631\u062a\u062c\u0639</h2>', f"<h2>{{t('{ns}.bounce')}}</h2>")
    c = c.replace('>\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0627\u0631\u062a\u062c\u0627\u0639</label>', f">{{t('{ns}.bounceDate')}}</label>")
    c = c.replace('>\u0633\u0628\u0628 \u0627\u0644\u0627\u0631\u062a\u062c\u0627\u0639</label>', f">{{t('{ns}.bounceReason')}}</label>")
    c = c.replace(
        'placeholder="\u0631\u0635\u064a\u062f \u063a\u064a\u0631 \u0643\u0627\u0641\u064d\u060c \u062a\u0648\u0642\u064a\u0639 \u063a\u064a\u0631 \u0645\u0637\u0627\u0628\u0642..."',
        f"placeholder={{t('{ns}.bouncePlaceholder')}}"
    )
    c = c.replace(
        "{saving ? '\u062c\u0627\u0631\u064a...' : '\u062a\u0623\u0643\u064a\u062f \u0627\u0644\u0627\u0631\u062a\u062c\u0627\u0639'}",
        f"{{saving ? t('{ns}.processing') : t('{ns}.confirmBounce')}}"
    )
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    after = count_arabic(c)
    print(f"ChecksPayable.jsx: {before} -> {after} Arabic chars")


if __name__ == "__main__":
    print("Adding needed translation keys...")
    add_needed_keys()
    print("\nFixing Treasury files...")
    fix_notes_receivable()
    fix_notes_payable()
    fix_checks_receivable()
    fix_checks_payable()
    print("\nDone! All 4 Treasury files fixed.")
