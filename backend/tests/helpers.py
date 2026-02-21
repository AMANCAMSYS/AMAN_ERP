"""
AMAN ERP - Helper functions for tests
دوال مساعدة للاختبارات
"""


def assert_valid_response(response, expected_status=200):
    """تأكيد أن الاستجابة صحيحة"""
    assert response.status_code == expected_status, \
        f"Expected {expected_status}, got {response.status_code}: {response.text[:300]}"


def assert_error_response(response, expected_status):
    """تأكيد أن الاستجابة خطأ متوقع"""
    assert response.status_code == expected_status, \
        f"Expected error {expected_status}, got {response.status_code}: {response.text[:300]}"


def assert_balance_equation(assets, liabilities, equity):
    """
    ✅ قاعدة محاسبية أساسية:
    الأصول = الخصوم + حقوق الملكية
    """
    diff = abs(assets - (liabilities + equity))
    assert diff < 0.01, \
        f"⚠️ معادلة الميزانية غير متوازنة! الأصول={assets}, الخصوم={liabilities}, حقوق الملكية={equity}, الفرق={diff}"


def assert_journal_balanced(debit_total, credit_total):
    """
    ✅ القيد المحاسبي يجب أن يكون متوازن
    """
    diff = abs(debit_total - credit_total)
    assert diff < 0.01, \
        f"⚠️ القيد غير متوازن! المدين={debit_total}, الدائن={credit_total}, الفرق={diff}"


def assert_positive_amount(amount, field_name="المبلغ"):
    """تأكيد أن المبلغ غير سالب"""
    assert amount >= 0, f"⚠️ {field_name} لا يمكن أن يكون سالباً: {amount}"
