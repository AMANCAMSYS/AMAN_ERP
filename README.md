# AMAN ERP - Enterprise Resource Planning System

نظام إدارة موارد المؤسسات (ERP) المتكامل - نظام "أمان"

> **الإصدار:** 2.0.0 | **الاختبارات:** 911 ناجح ✅ | **الجداول:** 178+ | **الصفحات:** 161

## 🏗️ التقنيات

| الطبقة | التقنية | التفاصيل |
|--------|---------|----------|
| **Backend** | FastAPI (Python 3.12) | 37 راوتر، 515+ endpoint |
| **Frontend** | React 18 + Vite 5 | 161 صفحة، i18n (عربي/إنجليزي) |
| **Database** | PostgreSQL | Multi-Tenant، 178+ جدول لكل شركة |
| **Auth** | JWT + 2FA (pyotp) | Rate Limiting (slowapi)، CORS، CSP |
| **Real-time** | WebSocket | إشعارات فورية |

## 📂 هيكل المشروع

```
aman/
├── backend/
│   ├── main.py              ← FastAPI app + middleware
│   ├── database.py          ← SQLAlchemy + 178 table definitions
│   ├── config.py            ← Environment settings
│   ├── routers/             ← API endpoints
│   │   ├── auth.py, companies.py, ...  (17 core routers)
│   │   ├── finance/         ← accounting, treasury, taxes, ... (12 files)
│   │   ├── hr/              ← core + advanced (2 files)
│   │   ├── manufacturing/   ← production (1 file)
│   │   ├── inventory/       ← products, warehouses, ... (14 files)
│   │   └── sales/           ← invoices, orders, ... (9 files)
│   ├── schemas/             ← Pydantic models
│   ├── services/            ← Business logic
│   ├── utils/               ← Helpers (limiter, permissions, security)
│   ├── migrations/          ← DB migration scripts
│   └── tests/               ← 984 tests (911 passed, 73 skipped)
├── frontend/
│   ├── src/
│   │   ├── pages/           ← 161 React pages
│   │   ├── components/      ← Reusable UI components
│   │   ├── services/        ← 18 API service files + apiClient.js
│   │   ├── hooks/           ← Custom hooks (WebSocket, etc.)
│   │   ├── utils/           ← dateUtils, requestManager, etc.
│   │   └── locales/         ← ar.json, en.json
│   └── vite.config.js
├── docs/                    ← Documentation
│   ├── AUDIT_REPORT.md      ← Comprehensive system audit
│   ├── DATABASE_ERD.md      ← Database schema & ERD
│   ├── API_GUIDE.md         ← API documentation
│   └── ...
└── tests/                   ← Integration tests
```

## 📂 هيكل التوثيق (Documentation)

| الملف | الوصف |
|-------|-------|
| [docs/AUDIT_REPORT.md](docs/AUDIT_REPORT.md) | تقرير الفحص الشامل — حالة كل وحدة |
| [docs/DATABASE_ERD.md](docs/DATABASE_ERD.md) | مخطط قاعدة البيانات (ERD) — 178+ جدول |
| [docs/API_GUIDE.md](docs/API_GUIDE.md) | دليل API — أمثلة لكل وحدة |
| [docs/testing/](docs/testing/) | خطة الاختبار ونتائجها |
| [docs/analysis/](docs/analysis/) | تحليل النظام والفجوات |

## 🚀 التشغيل السريع

### المتطلبات
- Python 3.12+
- Node.js 18+
- PostgreSQL 15+

### 1. تهيئة الباكند
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # عدّل إعدادات قاعدة البيانات
```

### 2. تشغيل النظام
```bash
./backend/start.sh
```
- **Backend:** http://localhost:8000
- **Frontend:** http://localhost:5173
- **API Docs (Swagger):** http://localhost:8000/api/docs
- **API Docs (ReDoc):** http://localhost:8000/api/redoc

### 3. تشغيل الاختبارات
```bash
cd backend
python3 -m pytest tests/ -q
```

## 🔐 المصادقة

```bash
# تسجيل الدخول
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# استخدام التوكن
curl http://localhost:8000/api/accounting/accounts \
  -H "Authorization: Bearer <token>"
```

## 📊 الوحدات الرئيسية

| الوحدة | Endpoints | الصفحات | الوصف |
|--------|-----------|---------|-------|
| المحاسبة | 32 | 20 | دليل حسابات، قيود، تقارير مالية |
| المبيعات | 28 | 28 | فواتير، أوامر بيع، عروض أسعار |
| المشتريات | 26 | 22 | أوامر شراء، RFQ، تقييم موردين |
| المخزون | 35 | 20 | منتجات، مستودعات، دفعات |
| الخزينة | 8 | 12 | بنوك، تسويات، شيكات، سندات |
| الموارد البشرية | 40 | 20 | موظفين، رواتب، حضور، إجازات |
| التصنيع | 14 | 11 | BOM، أوامر إنتاج، MRP |
| نقاط البيع | 20 | 7 | POS، عروض، ولاء |
| المشاريع | 10 | 5 | مشاريع، مهام، موارد |
| التقارير | 18 | 3 | تقارير مالية وتشغيلية |

---
💡 جميع بيانات الاعتماد المولّدة لاختبار الجهد تجدها في: `test_data/load_test_credentials.json`
