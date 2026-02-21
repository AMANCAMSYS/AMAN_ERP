# Frontend — AMAN ERP

React 18 + Vite 5 frontend for the AMAN ERP system.

## التقنيات

- **Framework:** React 18 (JSX)
- **Build Tool:** Vite 5
- **HTTP Client:** Axios (with interceptors)
- **Date Handling:** dayjs (UTC + timezone plugins)
- **i18n:** Arabic + English (ar.json, en.json)
- **Real-time:** WebSocket for notifications

## 📁 هيكل المجلدات

```
frontend/
├── index.html
├── package.json
├── vite.config.js            ← Dev proxy: /api → localhost:8000
├── .env                      ← VITE_API_URL=/api
│
└── src/
    ├── App.jsx               ← Root component + routing
    ├── main.jsx              ← Entry point
    │
    ├── pages/                ← 161 page components
    │   ├── Dashboard/
    │   ├── Accounting/       ← 20 pages
    │   ├── Sales/            ← 28 pages
    │   ├── Buying/           ← 22 pages
    │   ├── Stock/            ← 20 pages
    │   ├── Treasury/         ← 12 pages
    │   ├── HR/               ← 20 pages
    │   ├── Manufacturing/    ← 11 pages
    │   ├── POS/              ← 7 pages
    │   ├── Projects/         ← 5 pages
    │   ├── CRM/              ← 3 pages
    │   ├── Reports/          ← 3 pages
    │   ├── Settings/         ← 5+19 tabs
    │   └── ...
    │
    ├── components/           ← Reusable UI components
    │   ├── Sidebar.jsx       ← Navigation (27 items)
    │   ├── Topbar.jsx        ← Header + notifications
    │   ├── LoadingStates.jsx ← PageSkeleton, TableSkeleton, Spinner
    │   └── ...
    │
    ├── services/             ← API service layer (18 files)
    │   ├── apiClient.js      ← Shared axios instance + interceptors
    │   ├── auth.js           ← authAPI
    │   ├── accounting.js     ← accountingAPI
    │   ├── sales.js          ← salesAPI
    │   ├── purchases.js      ← purchasesAPI
    │   ├── inventory.js      ← inventoryAPI
    │   ├── hr.js             ← hrAPI, hrAdvancedAPI
    │   ├── treasury.js       ← treasuryAPI, reconciliationAPI
    │   ├── manufacturing.js  ← manufacturingAPI
    │   ├── ...               ← 10 more service files
    │   └── index.js          ← Barrel re-export
    │
    ├── hooks/                ← Custom React hooks
    │   ├── useNotificationSocket.js  ← WebSocket notifications
    │   └── ...
    │
    ├── utils/
    │   ├── api.js            ← Backward-compatible barrel (76 lines)
    │   ├── dateUtils.js      ← Timezone-aware date formatting (dayjs)
    │   └── requestManager.js ← AbortController for route changes
    │
    └── locales/
        ├── ar.json           ← Arabic translations
        └── en.json           ← English translations
```

## التشغيل

```bash
# تثبيت الحزم
npm install

# بيئة التطوير
npm run dev
# → http://localhost:5173

# بناء الإنتاج
npm run build

# معاينة البناء
npm run preview
```

## Vite Proxy

في بيئة التطوير، Vite يوجه طلبات `/api` إلى الباكند:

```js
// vite.config.js
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    ws: true  // WebSocket support
  }
}
```

## API Services Pattern

```jsx
// استيراد من services مباشرةً
import { salesAPI } from '../services/sales'

// أو من الـ barrel (backward-compatible)
import { salesAPI } from '../utils/api'

// الاستخدام
const { data } = await salesAPI.getInvoices({ page: 1, status: 'posted' })
```

## Date Handling

```jsx
import { formatDate, formatDateTime, getCompanyTimezone } from '../utils/dateUtils'

// يعتمد على timezone الشركة من localStorage
formatDate('2026-02-21T10:30:00Z')     // "21/02/2026"
formatDateTime('2026-02-21T10:30:00Z') // "21/02/2026 01:30 PM" (Asia/Riyadh)
```
