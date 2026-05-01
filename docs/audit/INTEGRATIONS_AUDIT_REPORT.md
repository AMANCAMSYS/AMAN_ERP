# تقرير التدقيق الشامل للتكاملات وملفات تعريف API (Integrations & APIs)
# Comprehensive Integrations, Adapters & API Audit Report

> **التاريخ**: 2026-04-28
> **النطاق**: Payment Gateways, E-Invoicing, Bank Feeds, SMS, Email, Shipping, SSO, Webhooks, API Docs, Security
> **المراجع**: مهندس تكامل أنظمة (Integration Architect)

---

## 1. بوابات الدفع (Payment Gateways)

| # | الملف | السطر | الخطورة | التفصيل |
|---|-------|-------|---------|---------|
| **1.1 Stripe Adapter** ||||
| 1.1.1 | `stripe_adapter.py` | 86-118 | ✅ سليم | `verify_webhook()`: HMAC-SHA256 مع `hmac.compare_digest()` (مقاوم لهجمات التوقيت). يتحقق من توقيع `Stripe-Signature` header بصيغة `t=...,v1=...` ✅ |
| 1.1.2 | `stripe_adapter.py` | 42 | 🟡 تحذير | `api_base = "https://api.stripe.com"` — صلب لكنه افتراضي قابل للتجاوز |
| 1.1.3 | `stripe_adapter.py` | 31-35 | ✅ سليم | تحويل صحيح للعملات الصفرية الأرقام (JPY, VND, KRW إلخ) إلى وحدات minor/integer ✓ |
| 1.1.4 | `stripe_adapter.py` | — | 🟠 P2 | **لا يوجد retry على مستوى الـ adapter**: إذا فشل طلب `create_charge`، يُرجع `ChargeResult(status="failed")` بدون إعادة محاولة |
| **1.2 Tap Adapter** ||||
| 1.2.1 | `tap_adapter.py` | — | ✅ سليم | `verify_webhook()`: HMAC-SHA256 مع `HMAC-SIG` header. يقارن عبر `hmac.compare_digest()` ✅ |
| 1.2.2 | `tap_adapter.py` | 29 | 🟡 تحذير | `endpoint = "https://api.tap.company/v2"` — صلب |
| **1.3 PayTabs Adapter** ||||
| 1.3.1 | `paytabs_adapter.py` | — | ✅ سليم | `verify_webhook()`: HMAC-SHA256 على sorted key-values في الـ IPN body. `hmac.compare_digest()` ✅ |
| 1.3.2 | `paytabs_adapter.py` | 31 | 🟡 تحذير | `base_url = "https://secure.paytabs.sa"` — صلب |
| **1.4 معالجة Webhook المدفوعات** ||||
| 1.4.1 | `payments.py` | 43-64 | ✅ سليم | Rate limiting: 120 hit/60s لكل IP+Provider — sliding window. يحمي من DoS قبل التحقق من التوقيع ✅ |
| 1.4.2 | `payments.py` | — | ✅ سليم | Webhook endpoint عام (`/finance/payments/webhook/{provider}/{company_id}`) — غير محمي بـ JWT لكن محمي بالتوقيع ✅ |
| 1.4.3 | `payments.py` | — | 🟠 P2 | **التوقيع اختياري**: إذا فشل `verify_webhook` (أو webhook_secret غير موجود)، يتم تجاهل الحدث بدون خطأ صريح |

---

## 2. التكامل الضريبي (E-Invoicing: ZATCA/FTA)

| # | الملف | السطر | الخطورة | التفصيل |
|---|-------|-------|---------|---------|
| **2.1 ZATCA (السعودية) — منفذ بالكامل** ||||
| 2.1.1 | `zatca_adapter.py` | 58-100 | ✅ سليم | `build_qr_payload`: ترميز TLV للوسوم 1-9. يدعم Phase 2 extensions (hash, signature, public key) ✅ |
| 2.1.2 | `zatca_adapter.py` | — | ✅ سليم | UBL 2.1 XML skeleton متوافق مع قاموس بيانات ZATCA ✅ |
| 2.1.3 | `zatca.py` | 130-143 | ✅ سليم | SHA-256 invoice hash مع تسلسل (Previous Invoice Hash chaining) ✅ |
| 2.1.4 | `zatca.py` | 172-191 | ✅ سليم | توقيع RSA-2048 مع SHA-256 و PKCS1v15 padding ✅ |
| 2.1.5 | `zatca_adapter.py` | — | ✅ سليم | **Retry مع Exponential Backoff**: 3 محاولات (base 1.5s) على أخطاء 408/429/5xx وأخطاء الشبكة ✅ |
| **2.2 ZATCA — ثغرات** ||||
| 2.2.1 | `zatca_adapter.py` | 270-278 | 🔴 P1 | **وضع عدم الاتصال (offline mode)**: إذا لم تتوفر PCSID/secret، يعيد `offline: True` مع artifacts. لكنه **لا يُسجل الطلب في outbox لإعادة المحاولة لاحقًا**. الفاتورة قد لا تُرسل أبدًا |
| 2.2.2 | `zatca_adapter.py` | 24-29 | 🔴 P1 | **إدارة CSID غير موجودة**: الـ adapter يفترض أن PCSID/secret موجودان مسبقًا. لا يوجد تدفق onboarding، لا تجديد شهادة، لا كشف انتهاء صلاحية |
| 2.2.3 | `invoices.py` | 667-672 | 🔴 P1 | **ZATCA غير إلزامي**: `process_invoice_for_zatca` ملفوف في `try/except` صامت. الفاتورة تُنشأ حتى لو فشل ZATCA تمامًا |
| 2.2.4 | `zatca_adapter.py` | 17-19 | 🟡 تحذير | XMLDSig detached signature "implemented as a hook" — يعتمد على حقن signer callback خارجي. إذا لم يُحقن، لا يوجد توقيع XML |
| **2.3 ETA (مصر) و FTA (الإمارات) — Stubs** ||||
| 2.3.1 | `eta_adapter.py` / `uae_fta_adapter.py` | — | 🔴 P1 | **غير منفذين**: كلا المحولين stubs مع `dry_run: True`. ETA يحتاج OAuth + USB token signing. FTA يحتاج Peppol PINT AE عبر ASP |
| 2.3.2 | `eta_adapter.py` | 33 | 🟡 تحذير | `base_url = "https://api.invoicing.eta.gov.eg"` — صلب مع fallback من `ETA_BASE_URL` env |
| **2.4 E-Invoice Outbox Relay** ||||
| 2.4.1 | `accounting_depth.py` | 510-610 | ✅ سليم | `POST /einvoice/outbox/relay`: نظام outbox مع MAX_OUTBOX_ATTEMPTS=6. يعيد إرسال الفواتير المعلقة ✅ |

---

## 3. تغذية البنوك (Bank Feeds / MT940)

| # | الملف | السطر | الخطورة | التفصيل |
|---|-------|-------|---------|---------|
| **3.1 MT940 Parser** ||||
| 3.1.1 | `mt940.py` | 88-178 | ✅ سليم | محلل SWIFT MT940 كامل: الوسوم :20:, :25:, :28C:, :60F/M:, :61:, :86:, :62F/M:, :64:. يعالج تواريخ YYMMDD (محور 70) ✅ |
| 3.1.2 | `mt940.py` | 64-72 | ✅ سليم | Regex صحيح لتحليل سطر :61: — value date + entry date + D/C + amount + transaction type + reference ✅ |
| 3.1.3 | `mt940.py` | 52-58 | ✅ سليم | معالجة تواريخ YYMMDD بذكاء (pivot year 70: ≥70 → 19xx, <70 → 20xx) ✅ |
| 3.1.4 | `mt940.py` | 34 | ✅ سليم | المبالغ موقعة (±): credit موجب، debit سالب ✓ |
| **3.2 CSV Feed Parser** ||||
| 3.2.1 | `csv_feed.py` | 1-81 | ✅ سليم | محلل CSV عام: يدعم أعمدة debit/credit منفصلة، صيغ تاريخ متعددة، فواصل عشرية/آلاف مخصصة |
| **3.3 ثغرات** ||||
| 3.3.1 | — | — | 🔴 P1 | **لا يوجد CAMT.053 parser**: ISO 20022 هو المعيار الحديث للبنوك. معظم البنوك الأوروبية وبعض الخليجية تستخدم CAMT.053 بدل MT940. غياب هذا المحلل يمنع التكامل مع هذه البنوك |
| 3.3.2 | `mt940.py` | — | 🟠 P2 | **لا يوجد استيراد تلقائي**: الـ parser موجود لكن لا يوجد endpoint يقوم باستيراد ملف MT940 ويُطابق المعاملات تلقائيًا مع `bank_statement_lines` |
| 3.3.3 | `csv_feed.py` | — | 🟡 تحذير | لا يوجد auto-detection لتنسيق CSV — يجب تكوينه يدويًا لكل بنك |

---

## 4. وثائق API (Swagger/OpenAPI)

| # | الملف | السطر | الخطورة | التفصيل |
|---|-------|-------|---------|---------|
| 4.1 | `main.py` | 340-342 | ✅ سليم | Swagger UI على `/api/docs` + ReDoc على `/api/redoc` — توليد تلقائي من FastAPI ✅ |
| 4.2 | — | — | 🟠 P2 | **لا يوجد OpenAPI spec مخصص**: كل التوثيق معتمد على التوليد التلقائي من Pydantic schemas و docstrings. لا توجد أمثلة (examples) ولا أوصاف مفصلة للـ endpoints |
| 4.3 | — | — | 🟠 P2 | **نقص `response_model`**: بعض الـ endpoints ترجع `dict` بدون Pydantic model محدد — لا يظهر شكل response في Swagger |
| 4.4 | — | — | 🟡 تحذير | لا يوجد `summary` أو `description` على معظم الـ routes — يعتمد على docstring التلقائي |
| 4.5 | — | — | 🟡 تحذير | ReDoc و Swagger UI متاحان في production بدون حماية — يجب تقييدهما بكلمة مرور أو تعطيلهما في production |

---

## 5. تحمل الأخطاء (Fault Tolerance & Retry)

| # | النظام | آلية إعادة المحاولة | التقييم |
|---|--------|---------------------|---------|
| **5.1 ZATCA Adapter** ||||
| 5.1.1 | `zatca_adapter.py` | Exponential backoff: 3 محاولات، base 1.5s. يعيد المحاولة على 408/429/5xx وأخطاء الشبكة | ✅ ممتاز |
| **5.2 E-Invoice Outbox** ||||
| 5.2.1 | `accounting_depth.py` | MAX_OUTBOX_ATTEMPTS = 6 | ✅ ممتاز |
| **5.3 Outbound Webhooks** ||||
| 5.3.1 | `webhooks.py:154-207` | Exponential backoff: `base^attempt` مع cap (افتراضي 60s). قابل للتكوين عبر env vars | ✅ ممتاز |
| 5.3.2 | `webhooks.py:232-251` | تنفيذ في background threads (غير معطل للـ request) ✅ | ✅ |
| **5.4 Payment Gateways** ||||
| 5.4.1 | Stripe/Tap/PayTabs | **لا يوجد retry على مستوى الـ adapter** — الفشل يُرجع مباشرة | 🔴 P1 |
| **5.5 SMS Gateways** ||||
| 5.5.1 | Twilio/Unifonic/Taqnyat | **لا يوجد retry** — إرسال واحد فقط | 🟠 P2 |
| **5.6 Email Service** ||||
| 5.6.1 | `email_service.py` | **لا يوجد retry** على مستوى الإرسال. الاعتماد على طبقة الإشعارات للـ retry | 🟠 P2 |
| **5.7 API Client (Frontend)** ||||
| 5.7.1 | `apiClient.js:159-166` | **429 Rate Limit**: إعادة محاولة واحدة مع backoff (retry-after header أو 2s افتراضي) ✅ | ✅ |
| 5.7.2 | `apiClient.js:64-94` | **Proactive Token Refresh**: قبل 60s من انتهاء JWT ✅ | ✅ |

### أنماط Circuit Breaker / Resilience

| النمط | موجود؟ | التفصيل |
|--------|--------|---------|
| Circuit Breaker | ❌ لا | لا يوجد قطع دائرة — النظام سيستمر في محاولة الاتصال حتى لو فشل الطرف الآخر تمامًا |
| Bulkhead | ❌ لا | لا يوجد عزل للموارد بين المكونات |
| Timeout | ✅ نعم | 30s افتراضي لـ Stripe، 10s لـ webhooks |
| Fallback | جزئي | ZATCA offline mode فقط (يعيد artifacts بدون API call) |
| Rate Limiting | ✅ نعم | slowapi مع Redis/in-memory + sliding window للـ webhooks |
| Idempotency | ✅ نعم | مفتاح idempotency في كل العمليات المالية |

---

## 6. الأمان في التكاملات (Integration Security)

| # | الملف | التفصيل | التقييم |
|---|-------|---------|---------|
| 6.1 | `webhooks.py:56-103` | **SSRF Protection**: `validate_webhook_url()` يمنع IPs الخاصة (127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 169.254.0.0/16, ::1, fc00::/7). مع hostname allowlist اختياري | ✅ ممتاز |
| 6.2 | `webhooks.py:35-42` | **تشفير الأسرار**: Fernet encryption لـ webhook secrets في قاعدة البيانات | ✅ |
| 6.3 | `csrf_middleware.py` | **CSRF**: Double-submit cookie pattern مع 3 مستويات (off/permissive/strict) | ✅ |
| 6.4 | `security_middleware.py` | **XSS Detection + HTTPS + CSP + HSTS**: كشف أنماط XSS في query params, paths, JSON bodies | ✅ |
| 6.5 | `field_encryption.py` | **AES-256-GCM**: تشفير PII مع HKDF لاشتقاق مفاتيح لكل مستأجر | ✅ |
| 6.6 | `payments.py:52-64` | **Rate Limiting before Signature Verification**: حماية من DoS قبل التحقق المكلف من التوقيع | ✅ |
| 6.7 | Stripe/Tap/PayTabs | **`hmac.compare_digest()`** في جميع محولات الدفع — مقاومة لهجمات التوقيت (timing attacks) | ✅ |
| 6.8 | `sso_service.py` | One-time SSO ticket exchange pattern — يمنع replay attacks | ✅ |

---

## 7. التكاملات الأخرى (Other Integrations)

| # | النظام | الملفات | الحالة |
|---|--------|---------|--------|
| **7.1 SMS Gateways** ||||
| 7.1 | Twilio | `integrations/sms/twilio_adapter.py` (70 سطر) | ✅ منفذ بالكامل |
| 7.2 | Unifonic (MENA) | `integrations/sms/unifonic_adapter.py` (63 سطر) | ✅ مع `get_balance()` |
| 7.3 | Taqnyat (السعودية) | `integrations/sms/taqnyat_adapter.py` (66 سطر) | ✅ مع `get_balance()` |
| **7.4 Shipping Carriers** ||||
| 7.4 | Aramex | `integrations/shipping/aramex_adapter.py` (155 سطر) | ✅ منفذ بالكامل |
| 7.5 | DHL Express | `integrations/shipping/dhl_adapter.py` (129 سطر) | ✅ منفذ بالكامل |
| **7.6 Email** ||||
| 7.6 | SMTP | `services/email_service.py` (334 سطر) | ✅ منفذ بالكامل — لكن بدون retry |
| **7.7 SSO / Authentication** ||||
| 7.7 | SAML 2.0 | `services/sso_service.py` (572 سطر) | ✅ SP-initiated flow مع OneLogin |
| 7.8 | LDAP | `services/sso_service.py` | ✅ LDAPS/TLS مع bind auth |
| 7.9 | API Keys | `routers/external.py` | ✅ SHA-256 hashed مع rate limiting |
| **7.8 Notifications** ||||
| 7.9 | Firebase FCM | `services/notification_service.py` | ✅ Push notifications |
| 7.10 | In-App | `services/notification_service.py` | ✅ DB + WebSocket |
| 7.11 | Delivery Retry | `services/scheduler.py` | ✅ Exponential backoff 1/5/30min |

---

## 8. ثغرات أمنية مشتركة بين جميع المحولات

| # | الثغرة | التفصيل | الخطورة |
|---|--------|---------|---------|
| 8.1 | **اعتماد API Keys/Secrets من `company_settings` مباشرة**: يتم استعلام قاعدة البيانات في كل مرة. إذا تسربت قاعدة البيانات، تتسرب جميع المفاتيح | 🟠 P2 |
| 8.2 | **لا يوجد تناوب للمفاتيح (Key Rotation)**: لا آلية لتحديث API keys بشكل دوري أو إبطال المفاتيح القديمة تلقائيًا | 🟠 P2 |
| 8.3 | **تخزين المفاتيح كنص واضح**: ZATCA private key و certificate مخزنان في `company_settings` كنص واضح | 🟠 P2 |
| 8.4 | **لا يوجد Health Check موحد**: كل محول مستقل ولا يوجد endpoint واحد لفحص صحة جميع التكاملات | 🟡 تحذير |
| 8.5 | **لا يوجد Metrics/Logging موحد**: كل محول يسجل بشكل مستقل. لا يوجد تتبع مركزي لأداء التكاملات | 🟡 تحذير |

---

## 9. ملخص التغطية (Coverage Matrix)

| فئة التكامل | المحولات المنفذة | Stubs/غير مكتمل | Webhook Verify | Retry | Fallback |
|------------|-----------------|-----------------|----------------|-------|----------|
| E-Invoicing | ZATCA ✅ | ETA ❌, UAE FTA ❌ | N/A (sign) | ✅ (exp backoff) | جزئي (offline) |
| Payment Gateways | Stripe ✅, Tap ✅, PayTabs ✅ | — | ✅ (3/3 HMAC) | ❌ | ❌ |
| Bank Feeds | MT940 ✅, CSV ✅ | CAMT.053 ❌ | N/A | N/A | N/A |
| SMS | Twilio ✅, Unifonic ✅, Taqnyat ✅ | — | N/A (outbound) | ❌ | ❌ |
| Shipping | Aramex ✅, DHL ✅ | — | ❌ | ❌ | ❌ |
| Email | SMTP ✅ | — | N/A | ❌ (notification layer) | ❌ |
| SSO | SAML ✅, LDAP ✅ | — | ✅ (ticket exchange) | N/A | ✅ (fallback admin) |
| Webhooks (out) | Full ✅ | — | ✅ (HMAC sign) | ✅ (exp backoff) | ❌ |
| API Keys | Full ✅ | — | N/A | ✅ (rate limit) | N/A |

---

## ملخص الخلل حسب الخطورة

### 🔴 P1 — عالي (قد يؤدي لفشل التكامل أو خرق أمني)
1. **ZATCA: لا يوجد تدفق CSID onboarding** — PCSID/secret يفترض وجودهم (`zatca_adapter.py`)
2. **ZATCA offline mode لا يسجل في outbox** — الفاتورة قد لا ترسل أبدًا (`zatca_adapter.py:270`)
3. **ZATCA غير إلزامي عند إنشاء الفاتورة** — try/except صامت (`invoices.py:667`)
4. **ETA/FTA غير منفذين** — stubs فقط لمصر والإمارات
5. **لا يوجد CAMT.053 parser** — معظم البنوك الحديثة تستخدم ISO 20022
6. **Payment gateways لا retry** — فشل واحد = فشل نهائي

### 🟠 P2 — متوسط
7. استيراد MT940/CSV لا يتم تلقائيًا — لا يوجد endpoint يطابق المعاملات
8. Swagger UI مكشوف في production بدون حماية
9. نقص `response_model` في بعض الـ endpoints
10. مفاتيح API Secrets مخزنة كنص واضح في `company_settings`
11. لا يوجد Key Rotation أو Health Check موحد
12. SMS Gateways لا retry
13. توقيع webhook المدفوعات اختياري (صامت عند الفشل)

---

## توصيات التصحيح (حسب الأولوية)

1. **فوري (امتثال)**: تنفيذ تدفق ZATCA CSID onboarding الكامل + تجديد تلقائي للشهادة
2. **فوري (امتثال)**: جعل ZATCA إلزاميًا عند إنشاء الفاتورة في وضع production
3. **عاجل (مرونة)**: إضافة retry logic لمحولات الدفع (Stripe/Tap/PayTabs) — 3 محاولات مع exponential backoff
4. **عاجل (تكامل)**: تنفيذ CAMT.053 parser لتغطية البنوك الحديثة
5. **عاجل (تكامل)**: إنشاء endpoint استيراد تلقائي لملفات MT940/CSV مع مطابقة المعاملات
6. **هام (أمن)**: تشفير API keys و ZATCA secrets في `company_settings` باستخدام `field_encryption`
7. **هام (مرونة)**: إضافة Circuit Breaker pattern للتكاملات الخارجية
8. **هام (توثيق)**: حماية Swagger UI/ReDoc في production أو تعطيلها
9. **مستحسن (مرونة)**: إنشاء Health Check endpoint موحد لجميع التكاملات
10. **مستحسن (مراقبة)**: مركزية logging/metrics للتكاملات مع alerting عند الفشل المتكرر
