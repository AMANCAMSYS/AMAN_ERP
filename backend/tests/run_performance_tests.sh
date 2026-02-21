#!/bin/bash
# سكريبت تشغيل اختبارات الأداء
# AMAN ERP - Performance Tests Runner

set -e

echo "⚡ تشغيل اختبارات الأداء..."

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

echo "📊 اختبارات أداء API..."
pytest tests/test_performance_api.py -v --tb=short

echo ""
echo "⚡ اختبارات التحميل..."
pytest tests/test_load_concurrent.py -v --tb=short

echo "✅ اكتملت اختبارات الأداء!"
