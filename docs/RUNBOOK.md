# 📋 AMAN ERP — دليل الطوارئ التشغيلي (Runbook)

> **الإصدار:** 1.0  
> **آخر تحديث:** 2025  
> **المسؤول:** فريق DevOps / مدير النظام

---

## الفهرس

1. [معلومات الاتصال والتصعيد](#1-معلومات-الاتصال-والتصعيد)
2. [الوصول للبنية التحتية](#2-الوصول-للبنية-التحتية)
3. [إجراءات الطوارئ السريعة](#3-إجراءات-الطوارئ-السريعة)
4. [استكشاف الأخطاء — Backend](#4-استكشاف-الأخطاء--backend)
5. [استكشاف الأخطاء — Database](#5-استكشاف-الأخطاء--database)
6. [استكشاف الأخطاء — Redis](#6-استكشاف-الأخطاء--redis)
7. [النسخ الاحتياطي والاستعادة](#7-النسخ-الاحتياطي-والاستعادة)
8. [النشر والترقيات](#8-النشر-والترقيات)
9. [الأمان — الاستجابة للحوادث](#9-الأمان--الاستجابة-للحوادث)
10. [الصيانة الدورية](#10-الصيانة-الدورية)
11. [تدوير الأسرار + Smoke Regression](#11-تدوير-الأسرار--smoke-regression)

---

## 1. معلومات الاتصال والتصعيد

| المستوى | المسؤول | طريقة التواصل | وقت الاستجابة |
|---------|---------|---------------|---------------|
| L1 | مهندس DevOps | Slack #ops-alerts | 15 دقيقة |
| L2 | مدير التقنية (CTO) | هاتف + Slack | 30 دقيقة |
| L3 | مطور رئيسي | هاتف | 1 ساعة |

### تصنيف الحوادث

| الخطورة | الوصف | مثال | وقت الحل المستهدف |
|---------|-------|------|-------------------|
| **P1 — حرج** | النظام متوقف بالكامل | DB down, no backend | 30 دقيقة |
| **P2 — عالي** | وظيفة رئيسية معطلة | لا يمكن إنشاء فواتير | 2 ساعة |
| **P3 — متوسط** | تدهور أداء | بطء ملحوظ | 4 ساعات |
| **P4 — منخفض** | مشكلة تجميلية | خطأ في ترجمة | يوم عمل |

---

## 2. الوصول للبنية التحتية

### الخوادم

```bash
# الإنتاج
ssh deploy@erp.yourdomain.com

# المسارات الهامة
/opt/aman/                     # مجلد التطبيق
/opt/aman/backend/.env         # متغيرات البيئة
/opt/aman/backups/             # النسخ الاحتياطية
/var/log/aman/                 # السجلات
```

### Docker

```bash
# حالة الخدمات
docker compose ps

# سجلات الخدمة
docker compose logs -f backend --tail=100
docker compose logs -f db --tail=50

# الدخول لحاوية
docker compose exec backend bash
docker compose exec db psql -U aman -d postgres
```

### قواعد البيانات

```bash
# الاتصال بقاعدة البيانات الرئيسية
psql -h localhost -U aman -d postgres

# الاتصال بقاعدة شركة محددة
psql -h localhost -U aman -d aman_<company_id>

# قائمة قواعد بيانات الشركات
psql -U aman -d postgres -c "SELECT id, company_name, database_name, status FROM system_companies;"
```

---

## 3. إجراءات الطوارئ السريعة

### 🔴 النظام متوقف بالكامل

```bash
# 1. تحقق من حالة Docker
docker compose ps

# 2. أعد تشغيل جميع الخدمات
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 3. تحقق من الصحة
curl -s http://localhost:8000/health | python3 -m json.tool

# 4. راقب السجلات
docker compose logs -f --tail=50
```

### 🔴 قاعدة البيانات لا تستجيب

```bash
# 1. تحقق من حالة PostgreSQL
docker compose exec db pg_isready -U aman

# 2. تحقق من المساحة
docker compose exec db df -h /var/lib/postgresql/data

# 3. أعد تشغيل PostgreSQL فقط
docker compose restart db

# 4. انتظر حتى يصبح جاهزاً ثم أعد تشغيل Backend
sleep 10
docker compose restart backend

# 5. تحقق من الاتصالات المعلقة
docker compose exec db psql -U aman -c "SELECT count(*) FROM pg_stat_activity;"
```

### 🔴 ذاكرة الخادم ممتلئة

```bash
# 1. تحقق من الاستخدام
free -h
docker stats --no-stream

# 2. أوقف الخدمات غير الحرجة مؤقتاً
docker compose stop grafana prometheus

# 3. امسح ذاكرة Redis
docker compose exec redis redis-cli FLUSHDB

# 4. أعد تشغيل Backend (يحرر الذاكرة)
docker compose restart backend
```

### 🟡 بطء شديد في الاستجابة

```bash
# 1. تحقق من P95 latency
curl -s http://localhost:8000/metrics | grep http_request_duration

# 2. تحقق من استعلامات بطيئة
docker compose exec db psql -U aman -c "
  SELECT pid, now()-query_start AS duration, query 
  FROM pg_stat_activity 
  WHERE state = 'active' AND now()-query_start > interval '5 seconds'
  ORDER BY duration DESC LIMIT 10;"

# 3. ألغِ الاستعلامات المعلقة (> 5 دقائق)
docker compose exec db psql -U aman -c "
  SELECT pg_terminate_backend(pid) 
  FROM pg_stat_activity 
  WHERE state = 'active' AND now()-query_start > interval '5 minutes'
  AND pid <> pg_backend_pid();"

# 4. VACUUM للجداول الكبيرة
docker compose exec db psql -U aman -d aman_<company_id> -c "VACUUM ANALYZE;"
```

---

## 4. استكشاف الأخطاء — Backend

### Backend لا يبدأ

```bash
# 1. تحقق من السجلات
docker compose logs backend --tail=100

# 2. تحقق من متغيرات البيئة
docker compose exec backend env | grep -E "(POSTGRES|REDIS|SECRET)"

# 3. تحقق من صحة الكود
docker compose exec backend python -c "import ast; ast.parse(open('main.py').read()); print('OK')"

# 4. تشغيل يدوي للتشخيص
docker compose exec backend python -c "from config import settings; print(settings.DATABASE_URL)"
```

### أخطاء 500 متكررة

```bash
# 1. ابحث في سجلات JSON
docker compose logs backend --since=10m | grep '"level": "ERROR"'

# 2. تحقق من request_id محدد
docker compose logs backend | grep '<request_id>'

# 3. تحقق من اتصال DB
docker compose exec backend python -c "
from database import engine
from sqlalchemy import text
with engine.connect() as c:
    print(c.execute(text('SELECT 1')).scalar())
"
```

### ارتفاع استخدام CPU

```bash
# 1. حدد العمليات الثقيلة
docker compose top backend

# 2. قلل عدد Workers مؤقتاً
docker compose exec backend kill -HUP 1  # Gunicorn graceful reload

# 3. أو أعد التشغيل بعمال أقل
GUNICORN_WORKERS=2 docker compose up -d backend
```

---

## 5. استكشاف الأخطاء — Database

### مساحة القرص ممتلئة

```bash
# 1. تحقق من حجم كل قاعدة بيانات
docker compose exec db psql -U aman -c "
  SELECT datname, pg_size_pretty(pg_database_size(datname)) AS size 
  FROM pg_database ORDER BY pg_database_size(datname) DESC;"

# 2. حدد أكبر الجداول
docker compose exec db psql -U aman -d aman_<company_id> -c "
  SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) AS size
  FROM pg_catalog.pg_statio_user_tables 
  ORDER BY pg_total_relation_size(relid) DESC LIMIT 20;"

# 3. نظف سجلات المراجعة القديمة (> 6 أشهر)
docker compose exec db psql -U aman -d aman_<company_id> -c "
  DELETE FROM audit_log WHERE created_at < NOW() - INTERVAL '6 months';"

# 4. VACUUM FULL (⚠️ يقفل الجدول)
docker compose exec db psql -U aman -d aman_<company_id> -c "VACUUM FULL ANALYZE;"
```

### Deadlocks

```bash
# 1. تحقق من deadlocks
docker compose exec db psql -U aman -c "
  SELECT datname, deadlocks FROM pg_stat_database WHERE deadlocks > 0;"

# 2. تحقق من الأقفال الحالية
docker compose exec db psql -U aman -c "
  SELECT blocked.pid AS blocked_pid,
         blocking.pid AS blocking_pid,
         blocked.query AS blocked_query
  FROM pg_stat_activity blocked
  JOIN pg_locks bl ON bl.pid = blocked.pid
  JOIN pg_locks bk ON bk.locktype = bl.locktype 
       AND bk.database IS NOT DISTINCT FROM bl.database
       AND bk.relation IS NOT DISTINCT FROM bl.relation
  JOIN pg_stat_activity blocking ON bk.pid = blocking.pid
  WHERE NOT bl.granted AND bl.pid <> bk.pid;"
```

### استعادة من اتصال مقطوع

```bash
# أعد تعيين الاتصالات المعلقة
docker compose exec db psql -U aman -c "
  SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
  WHERE state = 'idle in transaction' AND now()-state_change > interval '10 minutes';"
```

---

## 6. استكشاف الأخطاء — Redis

```bash
# حالة Redis
docker compose exec redis redis-cli INFO server | head -20

# الذاكرة
docker compose exec redis redis-cli INFO memory

# عدد المفاتيح
docker compose exec redis redis-cli DBSIZE

# مسح ذاكرة التخزين المؤقت (آمن — البيانات تُعاد بنائها)
docker compose exec redis redis-cli FLUSHDB

# مسح rate limiter فقط
docker compose exec redis redis-cli --scan --pattern 'rl:*' | xargs -r redis-cli DEL
```

---

## 7. النسخ الاحتياطي والاستعادة

### تشغيل نسخة احتياطية يدوية

```bash
./scripts/backup.sh
```

### استعادة من نسخة احتياطية

```bash
# 1. أوقف Backend أولاً
docker compose stop backend

# 2. استعد قاعدة البيانات الرئيسية
gunzip -c backups/20250101_020000_system.sql.gz | \
  psql -h localhost -U aman -d postgres

# 3. استعد قاعدة شركة
gunzip -c backups/20250101_020000_aman_be67ce39.sql.gz | \
  psql -h localhost -U aman -d aman_be67ce39

# 4. أعد تشغيل Backend
docker compose start backend

# 5. تحقق
curl -s http://localhost:8000/health | python3 -m json.tool
```

### Point-in-Time Recovery (PITR)

```bash
# يتطلب تفعيل WAL archiving في postgresql.conf:
# wal_level = replica
# archive_mode = on
# archive_command = 'cp %p /var/lib/postgresql/wal_archive/%f'

# للاستعادة إلى نقطة زمنية:
# 1. أوقف PostgreSQL
# 2. أنشئ recovery.conf:
echo "restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
recovery_target_time = '2025-01-15 14:30:00'" > recovery.conf

# 3. أعد تشغيل PostgreSQL
```

---

## 8. النشر والترقيات

### ⚠️ تحذير مهم جداً — منع فقدان البيانات

```
❌ لا تستخدم هذه الأوامر أبداً (تحذف قاعدة البيانات كاملاً):
   docker compose down -v
   docker volume rm aman_db_data
   docker system prune -a --volumes

✅ استخدم دائماً:
   docker compose stop        # يوقف الحاويات ويحفظ البيانات
   docker compose start       # يعيد تشغيل الخدمات المتوقفة
   docker compose up -d       # يشغّل الخدمات مع إنشاء أي غير موجودة
```

### إيقاف السيرفر بأمان (قبل Power Off من DigitalOcean)

```bash
# الطريقة الآمنة — تأخذ نسخة احتياطية قبل الإيقاف
bash /opt/aman/safe-stop.sh

# أو يدوياً:
bash /opt/aman/scripts/backup.sh          # نسخة احتياطية أولاً
docker compose -f docker-compose.yml -f docker-compose.prod.yml stop   # إيقاف آمن
```

### إعادة تشغيل السيرفر بعد Power On

```bash
# بعد إعادة التشغيل من DigitalOcean، Docker يبدأ الحاويات تلقائياً
# إذا لم تبدأ تلقائياً:
bash /opt/aman/safe-start.sh

# أو يدوياً:
cd /opt/aman && docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
sleep 30
curl -s http://localhost:8000/health | python3 -m json.tool
```

### النسخ الاحتياطي اليدوي

```bash
bash /opt/aman/scripts/backup.sh
# النسخ تُحفظ في: /opt/aman/backups/
# النسخ التلقائية: كل يوم الساعة 02:00 صباحاً
# لعرض آخر النسخ:
ls -lh /opt/aman/backups/ | tail -10
```

### النشر العادي (Zero-downtime)

```bash
# 1. اسحب آخر الكود
cd /opt/aman && git pull origin main

# 2. أنشئ الحاويات الجديدة
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# 3. شغّل الهجرات
docker compose exec backend alembic upgrade head

# 4. أعد النشر (rolling update)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps backend

# 5. تحقق من الصحة
sleep 10
curl -s http://localhost:8000/health | python3 -m json.tool

# 6. راقب الأخطاء (5 دقائق)
docker compose logs -f backend --since=5m | grep -i error
```

### التراجع (Rollback)

```bash
# 1. ارجع للإصدار السابق
git checkout HEAD~1

# 2. أعد البناء والنشر
docker compose -f docker-compose.yml -f docker-compose.prod.yml build backend
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps backend

# 3. تراجع عن آخر هجرة (إن لزم)
docker compose exec backend alembic downgrade -1
```

### تحديث Frontend فقط

```bash
docker compose build frontend
docker compose up -d --no-deps frontend
```

---

## 9. الأمان — الاستجابة للحوادث

### 🔴 اشتباه اختراق حساب

```bash
# 1. عطّل المستخدم فوراً
psql -U aman -d aman_<company_id> -c "
  UPDATE company_users SET is_active = false WHERE username = '<username>';"

# 2. أبطل جميع التوكنات (أضف للقائمة السوداء)
# من خلال واجهة الإدارة أو API:
curl -X POST http://localhost:8000/api/auth/force-logout/<user_id> \
  -H "Authorization: Bearer <admin_token>"

# 3. راجع سجل المراجعة
psql -U aman -d aman_<company_id> -c "
  SELECT * FROM audit_log 
  WHERE performed_by = '<username>' 
  ORDER BY created_at DESC LIMIT 50;"

# 4. تحقق من IPs المشبوهة
psql -U aman -d postgres -c "
  SELECT * FROM system_activity_log 
  WHERE performed_by = '<username>'
  ORDER BY created_at DESC LIMIT 20;"
```

### 🔴 تسريب SECRET_KEY

```bash
# 1. أنشئ مفتاح جديد فوراً
python3 -c "import secrets; print(secrets.token_hex(32))"

# 2. حدّث .env
nano /opt/aman/backend/.env  # غيّر SECRET_KEY

# 3. أعد تشغيل Backend (يُبطل جميع التوكنات)
docker compose restart backend

# ⚠️ جميع المستخدمين سيحتاجون لإعادة تسجيل الدخول
```

### 🔴 هجوم Brute Force

```bash
# 1. تحقق من محاولات الدخول الفاشلة
docker compose logs backend --since=1h | grep "failed_login\|rate_limit\|429"

# 2. احجب IP على مستوى Nginx
echo "deny <IP_ADDRESS>;" >> /etc/nginx/conf.d/blocked_ips.conf
nginx -t && nginx -s reload

# 3. أو احجب على مستوى الجدار الناري
ufw deny from <IP_ADDRESS>
```

---

## 10. الصيانة الدورية

### يومياً (تلقائي عبر cron)
- ✅ النسخ الاحتياطي: `0 2 * * * /opt/aman/scripts/backup.sh`
- ✅ تنظيف التوكنات المنتهية: تلقائي في التطبيق (كل ساعة)

### أسبوعياً
```bash
# 1. تحقق من مساحة القرص
df -h
docker system df

# 2. نظف حاويات Docker القديمة
docker system prune -f

# 3. تحقق من سجلات الأخطاء
docker compose logs backend --since=7d | grep -c '"level": "ERROR"'

# 4. حدّث الأمان
apt-get update && apt-get upgrade -y --security-only
```

### شهرياً
```bash
# 1. VACUUM ANALYZE لجميع قواعد البيانات
for db in $(psql -U aman -t -A -c "SELECT datname FROM pg_database WHERE datname LIKE 'aman_%'"); do
  echo "VACUUM ANALYZE on $db..."
  psql -U aman -d "$db" -c "VACUUM ANALYZE;"
done

# 2. تحقق من حجم النسخ الاحتياطية
du -sh /opt/aman/backups/

# 3. اختبر الاستعادة على بيئة اختبار
# (استعد آخر نسخة على خادم اختبار وتحقق)

# 4. حدّث شهادات SSL (إن لزم)
certbot renew --dry-run

# 5. راجع التنبيهات والمقاييس في Grafana
```

### ربع سنوي
```bash
# 1. حدّث packages Python
pip list --outdated
# حدّث بحذر وافحص

# 2. حدّث Docker images
docker compose pull
docker compose up -d

# 3. مراجعة أمنية
# - راجع الصلاحيات والأدوار
# - راجع مفاتيح API النشطة
# - حدّث كلمات المرور الداخلية
```

---

## 11. تدوير الأسرار + Smoke Regression

### 11.1 تدوير الأسرار (تشغيلي)

استخدم سكربت المساعدة التالي للتحقق من الجاهزية وطباعة القيم المقترحة:

```bash
cd /opt/aman
./scripts/ops/rotate_secrets_checklist.sh
```

مخرجات السكربت:
1. يتحقق من المفاتيح الأساسية في `backend/.env`.
2. يتحقق من وجود `SECRET_KEY` ضعيف/افتراضي.
3. يطبع قيم قوية مقترحة لتدوير `SECRET_KEY` وكلمات المرور.
4. يوضح أهداف التدوير (GitHub Secrets + server env + providers).
5. يطبع أوامر تحقق ما بعد التدوير.

### 11.2 Smoke Regression لمسارات `O2C/P2P`

بعد التدوير أو أي تعديل حساس، نفذ:

```bash
cd /opt/aman
export AMAN_BASE_URL=http://localhost:8000
export AMAN_TOKEN=<fresh_bearer_token>
export AMAN_CUSTOMER_ID=1
export AMAN_SUPPLIER_ID=1
export AMAN_PRODUCT_ID=1
/home/omar/Desktop/aman/.venv/bin/python backend/scripts/smoke_o2c_p2p.py
```

نتيجة النجاح المتوقعة:
1. نجاح `auth/me`.
2. نجاح إنشاء order + sales invoice في `O2C`.
3. نجاح إنشاء purchase invoice في `P2P`.
4. رفض محاولة overpayment في `P2P` (كود `400/422`).

### 11.3 قرار الاستعداد

لا يتم اعتماد الجاهزية النهائية إلا بعد:
1. تنفيذ تدوير الأسرار فعليا.
2. نجاح smoke regression بدون أعطال حرجة.
3. تثبيت أن CI يمر عبر secret-scan gate.

## ملحق: أوامر مفيدة

```bash
# عدد المستخدمين النشطين
psql -U aman -d aman_<company_id> -c "SELECT count(*) FROM company_users WHERE is_active = true;"

# آخر عمليات تسجيل دخول
psql -U aman -d postgres -c "SELECT * FROM system_activity_log WHERE action_type = 'login' ORDER BY created_at DESC LIMIT 10;"

# إحصائيات API
curl -s http://localhost:8000/metrics | grep http_requests_total | head -20

# حجم الملفات المرفوعة
du -sh /opt/aman/backend/uploads/

# استهلاك الحاويات
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```
