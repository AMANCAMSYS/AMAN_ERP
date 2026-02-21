# AMAN ERP - Enterprise Resource Planning System

نظام إدارة موارد المؤسسات (ERP) المتكامل - نظام "أمان"

## 📂 هيكل التوثيق (Documentation Structure)

تم تنظيم التوثيق في المجلد `docs/` لتسهيل الوصول إليه:

### 🧪 [الاختبارات (Testing)](docs/testing/)
- **[خطة الاختبار (PLAN.md)](docs/testing/PLAN.md)**: استراتيجية الاختبار الكاملة.
- **[دليل التشغيل (GUIDE.md)](docs/testing/GUIDE.md)**: كيفية تشغيل الاختبارات المختلفة.
- **[تقارير الاختبار (REPORTS.md)](docs/testing/REPORTS.md)**: نتائج اختبارات الأمان، الأداء، والجهد.

### 📊 [بيانات النظام (Data Management)](docs/data_management/)
- **[البيانات الضخمة (MASSIVE_DATA.md)](docs/data_management/MASSIVE_DATA.md)**: دليل إنشاء وإدارة البيانات الضخمة لاختبار الجهد.

### 🔍 [التحليل والمهام (Analysis & Tasks)](docs/analysis/)
- **[تقرير تحليل النظام (ERP_ANALYSIS_REPORT.md)](docs/analysis/ERP_ANALYSIS_REPORT.md)**: نظرة شاملة على بنية النظام.
- **[الفجوات والمهام (SYSTEM_GAPS.md)](docs/analysis/SYSTEM_GAPS.md)**: الفجوات الحالية والمهام المطلوبة.
- **[سجل المهام (TASKS.md)](docs/analysis/TASKS.md)**: متابعة سير العمل.

---

## 🚀 كيفية البدء (Quick Start)

### 1. تهيئة النظام
```bash
./backend/start.sh
```

### 2. تهيئة بيانات اختبار الجهد (Load Testing)
لإنشاء شركات ومستخدمين وحفظ بيانات الاعتماد في مجلد `test_data`:
```bash
./.venv/bin/python backend/scripts/prepare_load_test.py --companies 5 --users-per-company 10
```

---
💡 جميع بيانات الاعتماد المولّدة لاختبار الجهد تجدها في: `test_data/load_test_credentials.json`
# AMAN_ERP
