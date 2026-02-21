#!/bin/bash
# سكريبت تشغيل اختبارات الأمان فقط
# AMAN ERP - Security Tests Runner

set -e

echo "🔒 تشغيل اختبارات الأمان..."

cd "$(dirname "$0")/.." || exit 1

# تفعيل virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# متغيرات البيئة
export AMAN_TEST_USER="${AMAN_TEST_USER:-zzzz}"
export AMAN_TEST_PASSWORD="${AMAN_TEST_PASSWORD:-As123321}"

pytest tests/test_security_authentication.py \
    tests/test_security_authorization.py \
    tests/test_security_injection.py \
    -v --tb=short --color=yes

echo "✅ اكتملت اختبارات الأمان!"
