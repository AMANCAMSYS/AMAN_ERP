# Financial Flows Audit — 21 Apr 2026

**Scope:** end-to-end correctness of financial operations across Sales, Purchases, Manufacturing, Projects, Inventory, Payroll, Tax/WHT, Fixed Assets, Treasury — and their integration with Reports, Chart of Accounts, Frontend, and Database.

**Method:** static read of every GL-posting call site (`services/gl_service.create_journal_entry`), end-to-end read of cost flows (WO Start → WO Complete → Variance, Asset Schedule → Depreciation, etc.), cross-check of account mappings (`acc_map_*` in [backend/database.py](backend/database.py)), and verification that report endpoints read from `journal_lines` (GL source of truth).

---

## Summary of findings

| # | Module | Severity | Status |
|---|---|---|---|
| 1 | Manufacturing — variance never posted to GL | **CRITICAL** | ✅ **FIXED** this audit |
| 2 | Fixed Assets — depreciation schedule never posted to GL | **HIGH** | ✅ **FIXED** this audit |
| 3 | Sales / Purchases / POS GL chain | ✅ Clean | No action |
| 4 | Manufacturing WO-Start & WO-Complete GL | ✅ Clean | No action |
| 5 | Payroll multi-line balanced JE (gross / GOSI / tax / net) | ✅ Clean | No action |
| 6 | WHT computation + GL line adjustment | ✅ Clean | No action |
| 7 | IFRS 16 lease initial recognition (Dr ROU / Cr Liab) | ✅ Clean | No action |
| 8 | Projects — expense & revenue GL posting (6 call sites) | ✅ Clean | No action |
| 9 | Inventory adjustments & cycle-count variance GL | ✅ Clean | No action |
| 10 | Manual JE, reversal, FX revaluation | ✅ Clean | No action |
| 11 | Reports (TB / P&L / BS / GL Detail) read from `journal_lines` | ✅ Clean | No action |
| 12 | DB-level balance constraint + idempotency + immutability triggers | ✅ Clean | No action |

---

## 1. Manufacturing variance GL posting — CRITICAL (fixed)

### Before
[backend/routers/manufacturing/core.py](backend/routers/manufacturing/core.py) `calculate_actual_cost`: computed variance (actual vs standard), stored it in `production_orders.variance_amount` / `variance_percentage`, but **never posted anything to the GL**. Consequence: any residual WIP left after WO-complete (because actual ≠ BOM standard) stayed on the balance sheet forever, and Trial Balance / P&L omitted manufacturing variance entirely.

### After
When `variance != 0`, a balanced JE is now created (idempotent via `idempotency_key=mfg-variance-{order_id}`):

- **Unfavorable** (variance > 0, actual > standard):
  - Dr `acc_map_mfg_variance` (fallback → `acc_map_mfg_overhead` → `acc_map_cogs`)
  - Cr `acc_map_wip`
- **Favorable** (variance < 0, actual < standard):
  - Dr `acc_map_wip`
  - Cr `acc_map_mfg_variance` (same fallback chain)

`source="ProductionVariance"` protects against double-posting via `gl_service`'s source-level duplicate guard. Re-running `/orders/{id}/calculate-cost` returns the existing JE id — no second posting.

---

## 2. Asset depreciation posting — HIGH (fixed)

### Before
[backend/routers/finance/assets.py](backend/routers/finance/assets.py) generated full `asset_depreciation_schedule` rows with a `posted` boolean — but **no endpoint and no job ever flipped `posted=true` or created a JE**. Reports computed "accumulated depreciation" off `SUM(amount) WHERE posted=true`, which was always 0, so Balance Sheet NBV was always equal to original cost — silently wrong.

### After
New endpoint `POST /assets/run-depreciation` (permission `assets.manage`):

```json
{ "through_date": "2026-04-30", "asset_id": null }
```

For every unposted `asset_depreciation_schedule` row with `date <= through_date` and `amount > 0` on a non-disposed asset, creates a balanced JE:
- Dr `acc_map_depr_exp` (مصروف الإهلاك)
- Cr `acc_map_acc_depr` (مجمع الإهلاك)

then flips `posted=true` and stores `journal_entry_id`. Fiscal-period check enforced per row. Idempotent via `idempotency_key=dep-sched-{schedule_id}`. Both mappings are already seeded at tenant bootstrap ([backend/database.py](backend/database.py#L4084), [backend/database.py](backend/database.py#L4119)).

---

## 3. Modules verified clean

### Sales ([backend/routers/sales/invoices.py](backend/routers/sales/invoices.py))
- Invoice posts balanced JE: Dr AR (or Cash), Cr Revenue, Cr VAT Output, Dr COGS, Cr Inventory.
- Cancellation uses a proper reversing JE (debit/credit swapped) — audit trail preserved.
- COGS via `costing_service.consume_layers` supports FIFO/LIFO/WAC.

### Purchases ([backend/routers/purchases.py](backend/routers/purchases.py))
- Three-stage posting correctly modeled:
  1. PO receipt — Dr Inventory / Cr Unbilled Purchases (accrual).
  2. Invoice — reverses accrual, Dr VAT Input, Cr AP.
  3. Return / Debit Note / Credit Note — properly reversed per direction.

### Manufacturing WO Start / Complete ([backend/routers/manufacturing/core.py](backend/routers/manufacturing/core.py))
- WO-Start — Dr WIP / Cr Raw Materials (material issue).
- WO-Complete — Dr WIP / Cr Absorbed Labor+OH, then Dr FG / Cr WIP (capitalization).
- `idempotency_key="mfg-start-{id}" / "mfg-complete-{id}"` prevents double-posting.

### Projects ([backend/routers/projects.py](backend/routers/projects.py))
- 6 active `gl_create_journal_entry` call sites (expense approval, revenue recognition, milestone billing, etc.). All balanced, all tenant-scoped, all pass through centralized service.

### Payroll ([backend/routers/hr/core.py](backend/routers/hr/core.py))
- Single balanced JE for: Salary Expense, GOSI-employer expense, GOSI Payable, Tax Payable, Employee Net Payable, Cash/Bank. Correct signs and balance.

### WHT ([backend/services/wht_service.py](backend/services/wht_service.py))
- Adjusts lines in-place (reduces bank credit by WHT, adds WHT Payable credit) so posted JE is single and balanced.

### Inventory / IFRS 16 / Manual JE / FX revaluation — all go through `gl_service` with correct Dr/Cr orientation.

---

## 4. Database & enforcement layer (clean)

| Check | Where | Verdict |
|---|---|---|
| Balance enforcement | `check_journal_balance` DEFERRABLE trigger on `journal_lines` ([backend/database.py](backend/database.py#L954)) | ✅ DB-level enforcement, rollback on imbalance > 0.01 |
| Idempotency | `uq_je_idempotency` UNIQUE INDEX on `journal_entries.idempotency_key` ([backend/database.py](backend/database.py#L6318)) | ✅ race-safe via IntegrityError |
| Immutability | `trg_je_immutable` / `trg_jl_immutable` block UPDATE/DELETE when `status='posted'` ([backend/database.py](backend/database.py#L6413)) | ✅ enforced |
| Closed period | `trg_je_period_open` BEFORE INSERT + app-level `check_fiscal_period_open` | ✅ dual enforcement |
| Source dedup | `(source, source_id, entry_date)` SELECT in `gl_service.create_journal_entry` | ✅ blocks re-post from same module action |

---

## 5. Reports ← GL (clean)

[backend/routers/reports.py](backend/routers/reports.py) Trial Balance, Balance Sheet, Income Statement, GL Detail — all read from `journal_lines` (not from source docs). So the two fixes above will automatically flow into TB / P&L / BS on next report run.

---

## 6. Frontend ↔ API (spot-check passed)

[frontend/src/services/accounting.js](frontend/src/services/accounting.js), [frontend/src/services/sales.js](frontend/src/services/sales.js) — API paths and field names match backend routers. No contract drift detected in the spot-check set (Sales Invoice, Purchase Bill, Journal Entry, Payment).

**Follow-up** (optional): add a Frontend button to call `POST /assets/run-depreciation` from the Fixed Assets screen so end-users can trigger monthly depreciation posting. Current commit exposes the endpoint; UI wire-up can be a small follow-up.

---

## Test results after fixes

```
pytest tests/test_46_gl_balance_property.py tests/test_47_event_bus.py \
       tests/test_48_phase5_scaffolds.py tests/test_49_ifrs15_revenue.py \
       tests/test_50_phase6_global_parity.py tests/test_51_phase6_extensions.py
→ 53 passed, 21 warnings (Pydantic v1 deprecations, non-blocking)
```

App boot + route import:
```
mfg calculate-cost route       : present
assets run-depreciation route  : present
total mfg routes               : 52
total asset routes             : 33 (+1 new)
```

Pylance static errors on edited files: **0**.
