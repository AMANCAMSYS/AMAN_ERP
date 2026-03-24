#!/usr/bin/env python3
"""
Smoke regression for critical O2C/P2P paths.

Usage:
  export AMAN_BASE_URL=http://localhost:8000
  export AMAN_TOKEN=<bearer_token>
  export AMAN_CUSTOMER_ID=1
  export AMAN_SUPPLIER_ID=1
  export AMAN_PRODUCT_ID=1
  /home/omar/Desktop/aman/.venv/bin/python backend/scripts/smoke_o2c_p2p.py

Notes:
- Creates low-volume test transactions.
- Best run in staging/test data.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date

import requests


def fail(msg: str, code: int = 1) -> None:
    print(f"[FAIL] {msg}")
    sys.exit(code)


def ok(msg: str) -> None:
    print(f"[OK] {msg}")


def main() -> None:
    base_url = os.getenv("AMAN_BASE_URL", "http://localhost:8000").rstrip("/")
    token = os.getenv("AMAN_TOKEN")
    customer_id = int(os.getenv("AMAN_CUSTOMER_ID", "1"))
    supplier_id = int(os.getenv("AMAN_SUPPLIER_ID", "1"))
    product_id = int(os.getenv("AMAN_PRODUCT_ID", "1"))
    today = str(date.today())

    if not token:
        fail("AMAN_TOKEN is required")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    failures: list[str] = []

    # 0) auth check
    r = requests.get(f"{base_url}/api/auth/me", headers=headers, timeout=20)
    if r.status_code != 200:
        fail(f"Auth check failed: {r.status_code} {r.text[:200]}")
    ok("Authentication check passed")

    # 1) O2C: create sales order
    order_payload = {
        "customer_id": customer_id,
        "order_date": today,
        "items": [
            {
                "product_id": product_id,
                "description": "SMOKE O2C item",
                "quantity": 1,
                "unit_price": 10,
                "tax_rate": 0,
                "discount": 0,
            }
        ],
        "notes": "SMOKE O2C order",
    }
    order_id = None
    r = requests.post(f"{base_url}/api/sales/orders", headers=headers, data=json.dumps(order_payload), timeout=30)
    if r.status_code not in (200, 201):
        failures.append(f"O2C order create failed: {r.status_code} {r.text[:300]}")
    else:
        order_data = r.json()
        order_id = order_data.get("id") or order_data.get("order_id")
        if not order_id:
            failures.append(f"O2C order id missing in response: {order_data}")
        else:
            ok(f"O2C order created (id={order_id})")

    # 2) O2C: create invoice directly
    inv_payload = {
        "customer_id": customer_id,
        "invoice_date": today,
        "items": [
            {
                "product_id": product_id,
                "description": "SMOKE O2C invoice line",
                "quantity": 1,
                "unit_price": 10,
                "tax_rate": 0,
                "discount": 0,
            }
        ],
        "payment_method": "credit",
        "paid_amount": 0,
        "sales_order_id": order_id,
    }
    if order_id:
        r = requests.post(f"{base_url}/api/sales/invoices", headers=headers, data=json.dumps(inv_payload), timeout=30)
        if r.status_code not in (200, 201):
            failures.append(f"O2C invoice create failed: {r.status_code} {r.text[:300]}")
        else:
            inv_data = r.json()
            invoice_id = inv_data.get("id") or inv_data.get("invoice_id")
            if not invoice_id:
                failures.append(f"O2C invoice id missing in response: {inv_data}")
            else:
                ok(f"O2C invoice created (id={invoice_id})")
    else:
        failures.append("O2C invoice skipped because order creation failed")

    # 3) P2P: create purchase invoice (credit)
    p2p_payload = {
        "supplier_id": supplier_id,
        "invoice_date": today,
        "items": [
            {
                "product_id": product_id,
                "description": "SMOKE P2P line",
                "quantity": 1,
                "unit_price": 15,
                "tax_rate": 0,
                "discount": 0,
            }
        ],
        "payment_method": "credit",
        "paid_amount": 0,
    }
    p2p_invoice_id = None
    r = requests.post(f"{base_url}/api/buying/invoices", headers=headers, data=json.dumps(p2p_payload), timeout=30)
    if r.status_code not in (200, 201):
        failures.append(f"P2P invoice create failed: {r.status_code} {r.text[:300]}")
    else:
        p2p_inv_data = r.json()
        p2p_invoice_id = p2p_inv_data.get("invoice_id") or p2p_inv_data.get("id")
        if not p2p_invoice_id:
            failures.append(f"P2P invoice id missing in response: {p2p_inv_data}")
        else:
            ok(f"P2P invoice created (id={p2p_invoice_id})")

    # 4) P2P: attempt over-allocation payment (must be rejected)
    overpay_payload = {
        "supplier_id": supplier_id,
        "voucher_date": today,
        "amount": 100,
        "payment_method": "cash",
        "voucher_type": "payment",
        "allocations": [
            {
                "invoice_id": p2p_invoice_id,
                "allocated_amount": 100,
            }
        ],
    }
    if p2p_invoice_id:
        r = requests.post(f"{base_url}/api/buying/payments", headers=headers, data=json.dumps(overpay_payload), timeout=30)
        if r.status_code not in (400, 422):
            failures.append(f"P2P overpayment guard failed, expected 400/422 got {r.status_code}: {r.text[:300]}")
        else:
            ok("P2P overpayment guard is active")
    else:
        failures.append("P2P overpayment check skipped because purchase invoice was not created")

    if failures:
        print("[DONE] Smoke regression completed with failures:")
        for item in failures:
            print(f"- {item}")
        sys.exit(1)

    print("[DONE] Smoke regression completed successfully")


if __name__ == "__main__":
    main()
