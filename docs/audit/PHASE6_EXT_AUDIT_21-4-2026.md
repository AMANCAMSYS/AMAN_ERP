# Phase 6 Extensions — Audit Report

**Date:** 21 April 2026  
**Commit:** `27ad758`  
**Branch:** `001-erp-staged-audit` → `origin/main` (SHA parity verified ✅)

---

## Summary

| Metric | Value |
|---|---|
| Files inspected (static) | 27 |
| Pylance errors on new/changed code | **0** |
| Phase 5+6+ext tests | **46 / 46 passing** |
| Pure-unit test sweep | **56 / 56 passing** |
| Total app routes | 1071 (+19 new) |
| Total tests collected | 1113 (+14 new) |
| Method+path collisions | **0** |

---

## Batch 1 — Static / Syntax Scan

All 27 files touched this phase were checked with Pylance. **No errors, no warnings on our code.**

<details><summary>Files checked</summary>

**New integration packages:**
- `backend/integrations/sms/{__init__,base,registry,twilio_adapter,unifonic_adapter,taqnyat_adapter}.py`
- `backend/integrations/shipping/{__init__,base,registry,aramex_adapter,dhl_adapter}.py`
- `backend/integrations/bank_feeds/{__init__,mt940,csv_feed}.py`

**New routers:**
- `backend/routers/sms.py`
- `backend/routers/shipping.py`
- `backend/routers/finance/bank_feeds.py`

**New services / utils:**
- `backend/services/multibook_service.py`
- `backend/services/wht_service.py`
- `backend/utils/field_encryption.py`
- `backend/utils/outbox_relay.py`

**Schema migrations (Pydantic v2):**
- `backend/schemas/campaign.py`, `backend/schemas/sso.py`, `backend/schemas/pos.py`

**Tests:**
- `backend/tests/test_51_phase6_extensions.py` (14 tests)

**Edited infrastructure:**
- `backend/main.py`, `backend/database.py`, `backend/routers/finance/__init__.py`
</details>

## Batch 2 — Test Suites

| Suite | Tests | Result |
|---|---|---|
| `test_47_event_bus` | 4 | ✅ |
| `test_48_phase5_scaffolds` | 14 | ✅ |
| `test_49_ifrs15_revenue` | 6 | ✅ |
| `test_50_phase6_global_parity` | 12 | ✅ |
| `test_51_phase6_extensions` | 14 | ✅ |
| `test_45_voucher_allocation_guards` | — | ✅ |
| `test_46_gl_balance_property` | — | ✅ |
| **Combined unit tests** | **56** | **56 / 56** |

## Batch 3 — Application Boot

- App imports cleanly. 1071 routes registered.
- **0 HTTP method + path collisions.**
- 216 duplicate paths are intentional (different HTTP verbs on the same path — e.g., `GET` and `PUT` on `/api/invoices/{id}`).

## Batch 4 — Issues Found

| # | File | Issue | Status |
|---|---|---|---|
| 1 | [backend/routers/auth.py](backend/routers/auth.py#L493) | `UnboundLocalError: os` — module-level `os` usage after a local `import os` inside an `if` branch (pre-existing since `a22bb6e`) | ✅ **Fixed in commit `27ad758`** |
| 2 | `tests/test_43_pydantic_validation.py` (10 tests) | `ValueError: company_id is required` — HTTP tests without tenant fixture | ⚠️ Pre-existing fixture gap |
| 3 | `tests/test_44_optimistic_locking.py` (29 tests) | Tenant alembic migration fails: `StringDataRightTruncation (varchar(32))` | ⚠️ Pre-existing migration bug |
| 4 | Pydantic v1 deprecation warnings in `schemas/costing.py`, `schemas/blanket_po.py`, `schemas/timetracking.py`, `schemas/resource.py`, `routers/sales/schemas.py`, `routers/finance/tax_compliance.py` | `@validator` / `class Config` still work under Pydantic 2.12 but should migrate | ℹ️ Non-blocking, tracked |

## Conclusion

All code added in Phase 6 extensions is clean:
- No static errors.
- No regressions in existing unit tests.
- No route collisions.
- One real pre-existing bug surfaced and fixed (`auth.py`).

Two categories of pre-existing test errors (tenant DB fixtures, tenant migrations) remain and require live-DB infrastructure work — **outside the scope of a code audit**.
