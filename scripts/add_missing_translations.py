#!/usr/bin/env python3
"""
Add missing translation keys to ar.json and en.json.
Covers:
 - SecuritySettings hardcoded strings (2FA modal, sessions, etc.)
 - Backend error messages
 - Various || fallback strings across frontend
"""
import json
from pathlib import Path
from copy import deepcopy

FE = Path(__file__).resolve().parent.parent / "frontend" / "src"
AR_F = FE / "locales" / "ar.json"
EN_F = FE / "locales" / "en.json"

def set_nested(d, key, val):
    """Set a dot-notation key in a nested dict."""
    parts = key.split(".")
    for p in parts[:-1]:
        d = d.setdefault(p, {})
    if parts[-1] not in d:
        d[parts[-1]] = val
        return True
    return False

# ── Missing keys to add ──
NEW_KEYS = {
    # ── SecuritySettings 2FA modal ──
    "security_page.two_factor.setup_title": {
        "ar": "إعداد المصادقة الثنائية",
        "en": "Setup 2FA"
    },
    "security_page.two_factor.disable_title": {
        "ar": "تعطيل المصادقة الثنائية",
        "en": "Disable 2FA"
    },
    "security_page.two_factor.enabled_title": {
        "ar": "تم تفعيل المصادقة الثنائية",
        "en": "2FA Enabled"
    },
    "security_page.two_factor.secret_key": {
        "ar": "المفتاح السري:",
        "en": "Secret Key:"
    },
    "security_page.two_factor.enter_key_hint": {
        "ar": "أدخل هذا المفتاح يدوياً في تطبيق المصادقة (Google Authenticator، Authy، إلخ.)",
        "en": "Enter this key manually in your authenticator app (Google Authenticator, Authy, etc.)"
    },
    "security_page.two_factor.verification_code": {
        "ar": "رمز التحقق",
        "en": "Verification Code"
    },
    "security_page.two_factor.verifying": {
        "ar": "جارٍ التحقق...",
        "en": "Verifying..."
    },
    "security_page.two_factor.verify_enable": {
        "ar": "تحقق وتفعيل",
        "en": "Verify & Enable"
    },
    "security_page.two_factor.disable_hint": {
        "ar": "لتعطيل المصادقة الثنائية، يرجى إدخال الرمز من تطبيق المصادقة.",
        "en": "To disable 2FA, please enter the code from your authenticator app."
    },
    "security_page.two_factor.disable_btn": {
        "ar": "تعطيل المصادقة الثنائية",
        "en": "Disable 2FA"
    },
    "security_page.two_factor.enabled_success": {
        "ar": "تم تفعيل المصادقة الثنائية بنجاح!",
        "en": "2FA Enabled Successfully!"
    },
    "security_page.two_factor.backup_codes_warning": {
        "ar": "احفظ هذه الرموز في مكان آمن. يمكنك استخدامها لاستعادة الوصول إذا فقدت جهازك.",
        "en": "Save these codes in a safe place. You can use them to recover access if you lose your device."
    },
    "security_page.two_factor.done": {
        "ar": "تم",
        "en": "Done"
    },
    "security_page.two_factor.setup_failed": {
        "ar": "فشل في إعداد المصادقة الثنائية",
        "en": "Failed to start 2FA setup"
    },
    "security_page.two_factor.verification_failed": {
        "ar": "فشل التحقق",
        "en": "Verification failed"
    },
    "security_page.two_factor.protect_desc": {
        "ar": "حماية حسابك بطبقة إضافية من الأمان",
        "en": "Protect your account with an extra layer of security"
    },
    "security_page.sessions.no_sessions": {
        "ar": "لا توجد جلسات نشطة",
        "en": "No active sessions"
    },
    "security_page.sessions.unknown_device": {
        "ar": "جهاز غير معروف",
        "en": "Unknown Device"
    },

    # ── Backend error messages (key-based for frontend display) ──
    "backend_errors.access_denied": {
        "ar": "غير مصرح بالوصول",
        "en": "Access Denied"
    },
    "backend_errors.not_found": {
        "ar": "غير موجود",
        "en": "Not found"
    },
    "backend_errors.forbidden": {
        "ar": "ممنوع: ليس لديك صلاحية للقيام بهذا الإجراء",
        "en": "Forbidden"
    },
    "backend_errors.internal_error": {
        "ar": "حدث خطأ في الخادم",
        "en": "Internal server error"
    },
    "backend_errors.invalid_credentials": {
        "ar": "لم نتمكن من التحقق من بيانات الاعتماد",
        "en": "Could not validate credentials"
    },
    "backend_errors.company_not_found": {
        "ar": "الشركة غير موجودة",
        "en": "Company not found"
    },
    "backend_errors.employee_not_found": {
        "ar": "الموظف غير موجود",
        "en": "Employee not found"
    },
    "backend_errors.user_not_found": {
        "ar": "المستخدم غير موجود",
        "en": "User not found"
    },
    "backend_errors.unauthorized": {
        "ar": "غير مصرح",
        "en": "Not authorized"
    },

    # ── Data Import Page ──
    "data_import.title": {
        "ar": "معالج استيراد البيانات",
        "en": "Data Import Wizard"
    },
    "data_import.preview_validate": {
        "ar": "معاينة والتحقق",
        "en": "Preview & Validate"
    },
    "data_import.targets.chart_of_accounts": {
        "ar": "دليل الحسابات",
        "en": "Chart of Accounts"
    },
    "data_import.targets.parties": {
        "ar": "الأطراف (العملاء/الموردين)",
        "en": "Parties (Customers/Suppliers)"
    },
    "data_import.targets.products": {
        "ar": "المنتجات",
        "en": "Products"
    },
    "data_import.targets.employees": {
        "ar": "الموظفين",
        "en": "Employees"
    },

    # ── Dashboard Charts ──
    "dashboard.charts.sales": {
        "ar": "المبيعات",
        "en": "Sales"
    },
    "dashboard.charts.expenses": {
        "ar": "المصروفات",
        "en": "Expenses"
    },
    "dashboard.charts.financial_overview": {
        "ar": "نظرة مالية عامة",
        "en": "Financial Overview"
    },
    "dashboard.charts.top_products": {
        "ar": "أكثر المنتجات مبيعاً",
        "en": "Top Selling Products"
    },

    # ── Treasury ──
    "treasury.transfer.same_account_error": {
        "ar": "لا يمكن أن يكون حساب المصدر والوجهة متماثلين",
        "en": "Source and destination accounts cannot be the same"
    },

    # ── Buying ──
    "buying.select_product_all_lines": {
        "ar": "يرجى اختيار منتج لجميع عناصر الأسطر",
        "en": "Please select a product for all line items"
    },

    # ── Manufacturing ──
    "manufacturing.load_failed": {
        "ar": "فشل في التحميل",
        "en": "Load failed"
    },

    # ── CRM / Performance common error ──
    "common.error_fallback": {
        "ar": "خطأ",
        "en": "Error"
    },

    # ── Auth (login page) ──
    "auth.sso_login_failed": {
        "ar": "فشل تسجيل الدخول عبر SSO",
        "en": "SSO login failed"
    },
    "auth.2fa_invalid": {
        "ar": "رمز المصادقة الثنائية غير صحيح",
        "en": "Invalid 2FA code"
    },

    # ── POS ──
    "pos.offline.time": {
        "ar": "الوقت",
        "en": "Time"
    },
    "pos.offline.details": {
        "ar": "التفاصيل",
        "en": "Details"
    },

    # ── Various missing settings keys ──
    "settings.notifications.test_failed": {
        "ar": "فشل إرسال الإشعار التجريبي",
        "en": "Test notification failed"
    },

    # ── Subscription ──
    "subscription.detail.status": {
        "ar": "الحالة",
        "en": "Status"
    },
    "subscription.detail.enrolled": {
        "ar": "تاريخ التسجيل",
        "en": "Enrolled Date"
    },
    "subscription.detail.next_billing": {
        "ar": "الفوترة التالية",
        "en": "Next Billing"
    },
    "subscription.detail.trial_end": {
        "ar": "نهاية الفترة التجريبية",
        "en": "Trial End"
    },
    "subscription.detail.failed_payments": {
        "ar": "الدفعات الفاشلة",
        "en": "Failed Payments"
    },
}

# ── Load, merge, save ──
with open(AR_F) as f:
    ar = json.load(f)
with open(EN_F) as f:
    en = json.load(f)

added_ar = 0
added_en = 0

for key, vals in NEW_KEYS.items():
    if set_nested(ar, key, vals["ar"]):
        added_ar += 1
    if set_nested(en, key, vals["en"]):
        added_en += 1

with open(AR_F, "w", encoding="utf-8") as f:
    json.dump(ar, f, ensure_ascii=False, indent=2)
    f.write("\n")

with open(EN_F, "w", encoding="utf-8") as f:
    json.dump(en, f, ensure_ascii=False, indent=2)
    f.write("\n")

print(f"✅ Added {added_ar} new keys to ar.json")
print(f"✅ Added {added_en} new keys to en.json")
print(f"ℹ️  {len(NEW_KEYS) - added_ar} keys already existed in ar.json")
print(f"ℹ️  {len(NEW_KEYS) - added_en} keys already existed in en.json")
