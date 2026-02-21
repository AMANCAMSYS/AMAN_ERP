# طريقة تشغيل نظام أمان (AMAN ERP)

## المتطلبات الأساسية
1. **Python 3.12+**
2. **PostgreSQL**
3. **Node.js 18+**

## خطوات التشغيل

### 1. إعداد قاعدة البيانات
تأكد من تشغيل خدمة PostgreSQL وإنشاء مستخدم `aman`:
```bash
sudo -u postgres psql
CREATE USER aman WITH PASSWORD 'YourPassword123!@#';
ALTER USER aman CREATEDB;
\q
```

### 2. تشغيل الواجهة الخلفية (Backend)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./start.sh
```
*سيعمل السيرفر على الرابط: http://localhost:8000*

### 3. تشغيل الواجهة الأمامية (Frontend)
```bash
cd frontend
npm install
npm run dev
```
*سيعمل التطبيق على الرابط: http://localhost:5173*

## ملاحظات هامة
- عند أول تشغيل، سيقوم النظام بطلب إنشاء حساب "مدير النظام".
- بيانات الدخول الافتراضية لقاعدة البيانات موجودة في ملف `backend/.env`.
