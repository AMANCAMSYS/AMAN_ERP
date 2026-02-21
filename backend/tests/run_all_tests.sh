#!/bin/bash
# سكريبت تشغيل جميع الاختبارات
# AMAN ERP - Test Runner

set -e

echo "═══════════════════════════════════════════════════════════"
echo "🧪 تشغيل اختبارات نظام أمان ERP"
echo "═══════════════════════════════════════════════════════════"
echo ""

# الألوان
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# الانتقال لمجلد backend
cd "$(dirname "$0")/.." || exit 1

# التحقق من وجود virtual environment
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment غير موجود. إنشاء واحد جديد...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        source .venv/bin/activate
    fi
fi

# تثبيت dependencies إذا لزم الأمر
echo -e "${YELLOW}📦 التحقق من المتطلبات...${NC}"
pip install -q pytest pytest-cov pytest-asyncio httpx

# متغيرات البيئة
export AMAN_TEST_USER="${AMAN_TEST_USER:-zzzz}"
export AMAN_TEST_PASSWORD="${AMAN_TEST_PASSWORD:-As123321}"
export AMAN_ADMIN_PASSWORD="${AMAN_ADMIN_PASSWORD:-admin}"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "1️⃣  اختبارات الوحدة (Unit Tests)"
echo "═══════════════════════════════════════════════════════════"
pytest tests/test_01_auth.py tests/test_02_accounting.py \
    tests/test_03_sales.py tests/test_04_purchases.py \
    tests/test_05_inventory.py tests/test_06_treasury.py \
    tests/test_07_hr.py tests/test_08_reports.py \
    -v --tb=short

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "2️⃣  اختبارات التكامل (Integration Tests)"
echo "═══════════════════════════════════════════════════════════"
pytest tests/test_09_integration.py tests/test_22_integration_workflow.py \
    tests/test_34_complete_business_cycles.py \
    -v --tb=short

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "3️⃣  اختبارات الأمان (Security Tests)"
echo "═══════════════════════════════════════════════════════════"
pytest tests/test_security_authentication.py \
    tests/test_security_authorization.py \
    tests/test_security_injection.py \
    -v --tb=short

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "4️⃣  اختبارات الأداء (Performance Tests)"
echo "═══════════════════════════════════════════════════════════"
pytest tests/test_performance_api.py \
    -v --tb=short -m "not slow"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "5️⃣  اختبارات سلامة البيانات (Data Integrity Tests)"
echo "═══════════════════════════════════════════════════════════"
pytest tests/test_data_integrity_accounting.py \
    -v --tb=short

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "6️⃣  اختبارات التحميل (Load Tests)"
echo "═══════════════════════════════════════════════════════════"
pytest tests/test_load_concurrent.py \
    -v --tb=short -m "not slow"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ اكتملت جميع الاختبارات!"
echo "═══════════════════════════════════════════════════════════"
