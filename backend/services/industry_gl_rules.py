"""
AMAN ERP — Industry GL Auto-Posting Rules
قواعد الترحيل التلقائي حسب نوع النشاط

يوفر لكل نشاط:
- حسابات افتراضية للعمليات المالية (مبيعات، مشتريات، مخزون...)
- قواعد الترحيل التلقائي للقيود اليومية
"""

import logging

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# القواعد الافتراضية (مشتركة لكل الأنشطة)
# كل قاعدة: {مفتاح_العملية: {debit: كود_حساب, credit: كود_حساب, description_ar, description_en}}
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_GL_RULES = {
    # ──── مبيعات نقدية ────
    "cash_sale": {
        "debit": "11010",   # الصندوق
        "credit": "41001",  # إيرادات المبيعات
        "description_ar": "مبيعات نقدية",
        "description_en": "Cash Sale",
    },
    # ──── مبيعات آجلة ────
    "credit_sale": {
        "debit": "12001",   # العملاء
        "credit": "41001",  # إيرادات المبيعات
        "description_ar": "مبيعات آجلة",
        "description_en": "Credit Sale",
    },
    # ──── تحصيل ذمم عملاء ────
    "customer_payment": {
        "debit": "11020",   # البنك
        "credit": "12001",  # العملاء
        "description_ar": "تحصيل من عميل",
        "description_en": "Customer Payment",
    },
    # ──── مشتريات نقدية ────
    "cash_purchase": {
        "debit": "51001",   # تكلفة البضاعة المباعة
        "credit": "11010",  # الصندوق
        "description_ar": "مشتريات نقدية",
        "description_en": "Cash Purchase",
    },
    # ──── مشتريات آجلة ────
    "credit_purchase": {
        "debit": "51001",   # تكلفة البضاعة المباعة
        "credit": "21001",  # الموردين
        "description_ar": "مشتريات آجلة",
        "description_en": "Credit Purchase",
    },
    # ──── سداد موردين ────
    "supplier_payment": {
        "debit": "21001",   # الموردين
        "credit": "11020",  # البنك
        "description_ar": "سداد مورد",
        "description_en": "Supplier Payment",
    },
    # ──── رواتب ────
    "salary_accrual": {
        "debit": "61001",   # رواتب وأجور
        "credit": "21070",  # رواتب مستحقة
        "description_ar": "استحقاق رواتب",
        "description_en": "Salary Accrual",
    },
    "salary_payment": {
        "debit": "21070",   # رواتب مستحقة
        "credit": "11020",  # البنك
        "description_ar": "صرف رواتب",
        "description_en": "Salary Payment",
    },
    # ──── ضريبة القيمة المضافة ────
    "vat_sale": {
        "debit": "12001",   # العملاء
        "credit": "21040",  # ضريبة مخرجات
        "description_ar": "ضريبة مبيعات",
        "description_en": "Output VAT",
    },
    "vat_purchase": {
        "debit": "15010",   # ضريبة مدخلات
        "credit": "21001",  # الموردين
        "description_ar": "ضريبة مشتريات",
        "description_en": "Input VAT",
    },
    # ──── إهلاك ────
    "depreciation": {
        "debit": "66001",   # إهلاك
        "credit": "18001",  # إهلاك متراكم — أثاث
        "description_ar": "إهلاك أصول",
        "description_en": "Asset Depreciation",
    },
    # ──── مصاريف إيجار ────
    "rent_expense": {
        "debit": "62001",   # إيجار
        "credit": "11020",  # البنك
        "description_ar": "دفع إيجار",
        "description_en": "Rent Payment",
    },
    # ──── GOSI ────
    "gosi_expense": {
        "debit": "61020",   # تأمينات اجتماعية
        "credit": "21060",  # GOSI مستحق
        "description_ar": "قيد تأمينات اجتماعية",
        "description_en": "GOSI Expense",
    },
    # ──── نهاية الخدمة ────
    "eos_provision": {
        "debit": "61010",   # بدلات وعلاوات
        "credit": "22001",  # مخصص نهاية الخدمة
        "description_ar": "مخصص نهاية الخدمة",
        "description_en": "End of Service Provision",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# تخصيصات حسب النشاط — يُدمج مع DEFAULT_GL_RULES
# ═══════════════════════════════════════════════════════════════════════════════

INDUSTRY_GL_OVERRIDES = {
    # ──── 🛍️ التجزئة ────
    "retail": {
        "cash_sale": {
            "credit": "41010",  # مبيعات POS
            "description_ar": "مبيعات تجزئة نقدية POS",
            "description_en": "POS Cash Sale",
        },
        "inventory_purchase": {
            "debit": "13001",   # مخزون بضاعة
            "credit": "21001",  # الموردين
            "description_ar": "شراء بضاعة للمخزون",
            "description_en": "Merchandise Purchase",
        },
        "cogs_sale": {
            "debit": "51010",   # تكلفة بضاعة مباعة — تجزئة
            "credit": "13001",  # مخزون بضاعة
            "description_ar": "تكلفة بضاعة مباعة",
            "description_en": "COGS — Retail",
        },
        "inventory_variance": {
            "debit": "51020",   # فروقات جرد
            "credit": "13001",  # مخزون بضاعة
            "description_ar": "تسوية فروقات جرد",
            "description_en": "Inventory Variance Adjustment",
        },
    },

    # ──── 📦 الجملة ────
    "wholesale": {
        "cash_sale": {
            "credit": "41010",  # مبيعات جملة
            "description_ar": "مبيعات جملة",
            "description_en": "Wholesale Sale",
        },
        "inventory_purchase": {
            "debit": "13001",   # مخزون بضاعة
            "credit": "21001",
            "description_ar": "شراء بضاعة بالجملة",
            "description_en": "Wholesale Purchase",
        },
        "cogs_sale": {
            "debit": "51010",
            "credit": "13001",
            "description_ar": "تكلفة بضاعة مباعة — جملة",
            "description_en": "COGS — Wholesale",
        },
        "agent_commission": {
            "debit": "51020",   # عمولات وكلاء
            "credit": "21001",  # الموردين
            "description_ar": "عمولة وكيل",
            "description_en": "Agent Commission",
        },
    },

    # ──── 🍽️ المطاعم ────
    "restaurant": {
        "cash_sale": {
            "credit": "41010",  # إيرادات مطعم
            "description_ar": "مبيعات مطعم Dine-in",
            "description_en": "Dine-in Sale",
        },
        "delivery_sale": {
            "debit": "12030",   # ذمم بوابات دفع
            "credit": "41020",  # إيرادات توصيل
            "description_ar": "مبيعات توصيل",
            "description_en": "Delivery Sale",
        },
        "food_purchase": {
            "debit": "13001",   # مخزون مواد غذائية
            "credit": "21001",
            "description_ar": "شراء مواد غذائية",
            "description_en": "Food Purchase",
        },
        "food_cost": {
            "debit": "51010",   # تكلفة الطعام
            "credit": "13001",  # مخزون مواد غذائية
            "description_ar": "تكلفة طعام مُباع",
            "description_en": "Food Cost",
        },
        "food_waste": {
            "debit": "51040",   # هالك وتلف غذائي
            "credit": "13001",
            "description_ar": "هالك غذائي",
            "description_en": "Food Waste",
        },
        "delivery_commission": {
            "debit": "64010",   # عمولات تطبيقات التوصيل
            "credit": "21001",
            "description_ar": "عمولة تطبيق توصيل",
            "description_en": "Delivery App Commission",
        },
    },

    # ──── 🏭 التصنيع ────
    "manufacturing": {
        "raw_material_purchase": {
            "debit": "13001",   # مخزون مواد خام
            "credit": "21001",
            "description_ar": "شراء مواد خام",
            "description_en": "Raw Material Purchase",
        },
        "production_start": {
            "debit": "13010",   # WIP
            "credit": "13001",  # مخزون مواد خام
            "description_ar": "صرف مواد للإنتاج",
            "description_en": "Material Issue to Production",
        },
        "production_complete": {
            "debit": "13020",   # مخزون إنتاج تام
            "credit": "13010",  # WIP
            "description_ar": "إنتاج تام",
            "description_en": "Finished Goods to Stock",
        },
        "direct_labor": {
            "debit": "51020",   # أجور عمالة مباشرة
            "credit": "21070",  # رواتب مستحقة
            "description_ar": "أجور عمالة مباشرة",
            "description_en": "Direct Labor Allocation",
        },
        "mfg_overhead": {
            "debit": "51030",   # تكاليف صناعية غير مباشرة
            "credit": "21010",  # مصاريف مستحقة
            "description_ar": "تكاليف صناعية غير مباشرة",
            "description_en": "Manufacturing Overhead",
        },
        "cogs_sale": {
            "debit": "51001",
            "credit": "13020",  # إنتاج تام
            "description_ar": "تكلفة منتجات مباعة",
            "description_en": "COGS — Manufactured Products",
        },
    },

    # ──── 🏗️ المقاولات ────
    "construction": {
        "cash_sale": {
            "credit": "41010",  # إيرادات عقود
            "description_ar": "إيراد عقد إنشاءات",
            "description_en": "Construction Contract Revenue",
        },
        "progress_billing": {
            "debit": "12001",   # العملاء
            "credit": "41020",  # إيرادات مستخلصات
            "description_ar": "مستخلص مشروع",
            "description_en": "Progress Billing",
        },
        "retention_deduction": {
            "debit": "12030",   # محتجزات لدى العملاء
            "credit": "12001",  # العملاء
            "description_ar": "محتجزات — عميل",
            "description_en": "Retention Deduction",
        },
        "subcontractor_cost": {
            "debit": "51030",   # تكلفة مقاولين باطن
            "credit": "21100",  # مقاولين من الباطن
            "description_ar": "تكلفة مقاول باطن",
            "description_en": "Subcontractor Cost",
        },
        "material_issue": {
            "debit": "51010",   # مواد بناء مباشرة
            "credit": "13001",  # مخزون مواد بناء
            "description_ar": "صرف مواد بناء للمشروع",
            "description_en": "Material Issue to Project",
        },
    },

    # ──── 💼 الخدمات ────
    "services": {
        "cash_sale": {
            "credit": "41010",  # إيرادات استشارات
            "description_ar": "إيراد استشارة",
            "description_en": "Consulting Revenue",
        },
        "service_wip": {
            "debit": "15020",   # WIP خدمات
            "credit": "51010",  # ساعات عمل مباشرة
            "description_ar": "أعمال تحت التنفيذ",
            "description_en": "Service WIP Accrual",
        },
    },

    # ──── 💊 الصيدليات ────
    "pharmacy": {
        "cash_sale": {
            "credit": "41010",  # مبيعات أدوية
            "description_ar": "مبيعات أدوية",
            "description_en": "Drug Sale",
        },
        "drug_purchase": {
            "debit": "13001",   # مخزون أدوية
            "credit": "21001",
            "description_ar": "شراء أدوية",
            "description_en": "Drug Purchase",
        },
        "cogs_sale": {
            "debit": "51010",   # تكلفة أدوية
            "credit": "13001",
            "description_ar": "تكلفة أدوية مُباعة",
            "description_en": "COGS — Drugs",
        },
        "drug_expiry_loss": {
            "debit": "51030",   # أدوية منتهية
            "credit": "13030",  # أدوية منتهية للإتلاف
            "description_ar": "خسارة أدوية منتهية",
            "description_en": "Expired Drug Loss",
        },
    },

    # ──── 🔧 الورش ────
    "workshop": {
        "cash_sale": {
            "credit": "41010",  # إيرادات صيانة
            "description_ar": "إيراد صيانة",
            "description_en": "Repair Revenue",
        },
        "parts_sale": {
            "debit": "11010",   # الصندوق
            "credit": "41020",  # إيرادات قطع غيار
            "description_ar": "بيع قطع غيار",
            "description_en": "Parts Sale",
        },
        "parts_cost": {
            "debit": "51010",   # تكلفة قطع غيار
            "credit": "13001",  # مخزون قطع غيار
            "description_ar": "تكلفة قطع غيار مُستخدمة",
            "description_en": "Parts Cost",
        },
    },

    # ──── 🛒 التجارة الإلكترونية ────
    "ecommerce": {
        "cash_sale": {
            "credit": "41010",  # مبيعات أونلاين
            "description_ar": "مبيعات أونلاين",
            "description_en": "Online Sale",
        },
        "gateway_fee": {
            "debit": "64010",   # عمولات بوابات دفع
            "credit": "12030",  # ذمم بوابات الدفع
            "description_ar": "عمولة بوابة دفع",
            "description_en": "Payment Gateway Fee",
        },
        "shipping_cost": {
            "debit": "65040",   # مصاريف شحن
            "credit": "21001",
            "description_ar": "تكلفة شحن",
            "description_en": "Shipping Cost",
        },
        "return_refund": {
            "debit": "41020",   # مردودات
            "credit": "11020",  # البنك
            "description_ar": "مرتجع واسترداد",
            "description_en": "Return & Refund",
        },
    },

    # ──── 🚛 اللوجستيات ────
    "logistics": {
        "cash_sale": {
            "credit": "41010",  # إيرادات نقل
            "description_ar": "إيراد نقل / شحن",
            "description_en": "Freight Revenue",
        },
        "fuel_purchase": {
            "debit": "51010",   # تكلفة وقود مباشر
            "credit": "11010",
            "description_ar": "شراء وقود",
            "description_en": "Fuel Purchase",
        },
        "toll_fee": {
            "debit": "51030",   # رسوم طرق
            "credit": "11010",
            "description_ar": "رسوم طرق وعبور",
            "description_en": "Toll Fee",
        },
    },

    # ──── 🌾 الزراعة ────
    "agriculture": {
        "cash_sale": {
            "credit": "41010",  # إيرادات محاصيل
            "description_ar": "بيع محاصيل",
            "description_en": "Crop Sale",
        },
        "seed_purchase": {
            "debit": "51010",   # بذور ومدخلات
            "credit": "21001",
            "description_ar": "شراء بذور ومدخلات",
            "description_en": "Seed & Input Purchase",
        },
        "feed_purchase": {
            "debit": "51020",   # تكلفة أعلاف
            "credit": "21001",
            "description_ar": "شراء أعلاف",
            "description_en": "Feed Purchase",
        },
        "bio_asset_revalue": {
            "debit": "13030",   # أصول بيولوجية — مواشي
            "credit": "42040",  # تغير القيمة العادلة
            "description_ar": "إعادة تقييم أصول بيولوجية",
            "description_en": "Biological Asset Revaluation",
        },
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Helper functions
# ═══════════════════════════════════════════════════════════════════════════════

def get_gl_rules(industry_key: str) -> dict:
    """
    Return merged GL rules for a given industry.
    Industry-specific rules override defaults.
    """
    from services.industry_coa_templates import normalize_industry_key
    industry_key = normalize_industry_key(industry_key)
    rules = dict(DEFAULT_GL_RULES)
    overrides = INDUSTRY_GL_OVERRIDES.get(industry_key, {})
    
    for op_key, override_fields in overrides.items():
        if op_key in rules:
            # Merge: override partial fields
            rules[op_key] = {**rules[op_key], **override_fields}
        else:
            # New operation specific to industry
            rules[op_key] = override_fields
    
    return rules


def get_default_accounts(industry_key: str) -> dict:
    """
    Return default accounts for quick setup.
    Useful for auto-selection in journal entry forms.
    """
    # normalize_industry_key is called inside get_gl_rules
    rules = get_gl_rules(industry_key)
    
    defaults = {
        "cash_account": "11010",
        "bank_account": "11020",
        "receivable_account": "12001",
        "payable_account": "21001",
        "sales_account": rules.get("cash_sale", {}).get("credit", "41001"),
        "cogs_account": rules.get("cogs_sale", {}).get("debit", "51001"),
        "salary_account": "61001",
        "vat_output": "21040",
        "vat_input": "15010",
        "inventory_account": rules.get("inventory_purchase", {}).get("debit", "13001") if "inventory_purchase" in rules else None,
    }
    
    return {k: v for k, v in defaults.items() if v is not None}


def get_gl_rules_summary(industry_key: str) -> dict:
    """Return a summary for the frontend to display available operations."""
    from services.industry_coa_templates import normalize_industry_key
    industry_key = normalize_industry_key(industry_key)
    rules = get_gl_rules(industry_key)
    summary = []
    for op_key, rule in rules.items():
        summary.append({
            "operation": op_key,
            "name": rule.get("description_en", op_key),
            "debit": rule.get("debit"),
            "credit": rule.get("credit"),
            "description_ar": rule.get("description_ar"),
            "description_en": rule.get("description_en"),
        })
    return {
        "industry_key": industry_key,
        "total_rules": len(summary),
        "rules": summary,
    }
