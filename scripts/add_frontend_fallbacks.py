#!/usr/bin/env python3
import json
from pathlib import Path

FE = Path(__file__).resolve().parent.parent / "frontend" / "src"
AR_F = FE / "locales" / "ar.json"
EN_F = FE / "locales" / "en.json"

def set_nested(d, key, val):
    parts = key.split(".")
    for p in parts[:-1]:
        if p in d:
            if isinstance(d[p], str):
                d[p] = {"_self": d[p]}
            d = d[p]
        else:
            d[p] = {}
            d = d[p]
    if True:
        d[parts[-1]] = val
        return True
    return False

FE_FALLBACKS = {
    # Common UI
    "common.active": {"ar": "نشط", "en": "Active"},
    "common.draft": {"ar": "مسودة", "en": "Draft"},
    "common.pending": {"ar": "قيد الانتظار", "en": "Pending"},
    "common.cancelled": {"ar": "ملغي", "en": "Cancelled"},
    "common.completed": {"ar": "مكتمل", "en": "Completed"},
    "common.admin": {"ar": "مسؤول", "en": "Admin"},
    "common.system": {"ar": "النظام", "en": "System"},
    "common.basic": {"ar": "أساسي", "en": "Basic"},
    "common.standard": {"ar": "قياسي", "en": "Standard"},
    "common.premium": {"ar": "مميز", "en": "Premium"},
    "common.days": {"ar": "أيام", "en": "Days"},
    "common.month": {"ar": "شهر", "en": "Month"},
    "common.year": {"ar": "سنة", "en": "Year"},
    "common.status": {"ar": "الحالة", "en": "Status"},
    "common.device": {"ar": "الجهاز", "en": "Device"},
    "common.ip_address": {"ar": "عنوان IP", "en": "IP Address"},
    "common.last_active": {"ar": "آخر نشاط", "en": "Last Active"},
    
    # Dates
    "common.date_format": {"ar": "YYYY/MM/DD", "en": "YYYY/MM/DD"},
    
    # Page specific / Module specific
    "data_import.wizard": {"ar": "معالج استيراد البيانات", "en": "Data Import Wizard"},
    "data_import.preview_validate": {"ar": "معاينة وتحقق", "en": "Preview & Validate"},
    "data_import.chart_of_accounts": {"ar": "دليل الحسابات", "en": "Chart of Accounts"},
    "data_import.parties": {"ar": "الأطراف (عملاء/موردين)", "en": "Parties (Customers/Suppliers)"},
    "data_import.products": {"ar": "المنتجات", "en": "Products"},
    "data_import.employees": {"ar": "الموظفين", "en": "Employees"},
    
    # Financials
    "financials.exchange_rate": {"ar": "سعر الصرف", "en": "Exchange Rate"},
    "financials.total_base": {"ar": "الإجمالي بالعملة الأساسية", "en": "Total in Base"},
    "financials.transfer": {"ar": "تحويل", "en": "Transfer"},
    "financials.expense": {"ar": "مصروف", "en": "Expense"},
    
    # Security (already done mostly but double checking)
    "security.sessions.terminate_all": {"ar": "إنهاء الكل", "en": "Terminate All"},
    "security.sessions.active_sessions": {"ar": "الجلسات النشطة", "en": "Active Sessions"},
}

with open(AR_F, "r", encoding="utf-8") as f: ar = json.load(f)
with open(EN_F, "r", encoding="utf-8") as f: en = json.load(f)

count = 0
for key, vals in FE_FALLBACKS.items():
    if set_nested(ar, key, vals["ar"]): count += 1
    if set_nested(en, key, vals["en"]): pass

with open(AR_F, "w", encoding="utf-8") as f:
    json.dump(ar, f, ensure_ascii=False, indent=2)
    f.write("\n")
with open(EN_F, "w", encoding="utf-8") as f:
    json.dump(en, f, ensure_ascii=False, indent=2)
    f.write("\n")

print(f"Added {count} frontend common translations.")
