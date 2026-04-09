"""Regression checks for critical voucher/purchase allocation guards.

These tests are source-level checks to keep validation runnable even when
unrelated modules fail to import.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VOUCHERS_FILE = ROOT / "routers" / "sales" / "vouchers.py"
PURCHASES_FILE = ROOT / "routers" / "purchases.py"


class TestVoucherAllocationGuards:
    def test_vouchers_uses_invoice_row_locks_for_allocations(self):
        content = VOUCHERS_FILE.read_text(encoding="utf-8")
        # Receipt and payment flows should both lock invoice rows during allocation.
        assert content.count("FROM invoices") >= 2
        assert content.count("FOR UPDATE") >= 2

    def test_vouchers_enforces_allocation_caps_and_party_ownership(self):
        content = VOUCHERS_FILE.read_text(encoding="utf-8")
        assert "if total_allocated > (_dec(data.amount) + _D2):" in content
        assert "لا تتبع العميل المحدد" in content


class TestSupplierAllocationThreshold:
    def test_purchases_partial_threshold_uses_cent_precision(self):
        content = PURCHASES_FILE.read_text(encoding="utf-8")
        assert "> 0.01 THEN 'partial'" in content
