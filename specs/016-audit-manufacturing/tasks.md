# Tasks: Audit Manufacturing Module — تدقيق وحدة التصنيع

**Input**: Design documents from `/specs/016-audit-manufacturing/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Not requested — no test tasks included.

**Organization**: Tasks grouped by user story. This is an audit-fix spec — no new features, no new tables, no new files. All changes are to existing code.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Exact file paths included in every task description

---

## Phase 1: Setup

**Purpose**: Database migration for SoftDeleteMixin columns

- [x] T001 Create Alembic migration to add `is_deleted BOOLEAN DEFAULT FALSE` column to 9 tables (bill_of_materials, bom_components, bom_outputs, capacity_plans, manufacturing_equipment, manufacturing_operations, manufacturing_routes, mfg_qc_checks, work_centers) in backend/alembic/versions/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Schema and model fixes that MUST be complete before ANY user story work — all query filters, Decimal conversions, and soft-delete behaviors depend on these changes

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 Convert all float fields to Decimal (use `condecimal` / `Field(decimal_places=4)`) for 20+ monetary/quantity fields in backend/schemas/manufacturing_advanced.py — includes quantity, cost, rate, percentage, and time fields per research R1
- [x] T003 [P] Add SoftDeleteMixin to BillOfMaterial, BomComponent, BomOutput, CapacityPlan models in backend/models/domain_models/manufacturing_bom_capacity.py
- [x] T004 [P] Add SoftDeleteMixin to ManufacturingEquipment, ManufacturingOperation, ManufacturingRoute, MfgQcCheck models in backend/models/domain_models/manufacturing_execution.py
- [x] T005 [P] Add SoftDeleteMixin to WorkCenter model in backend/models/domain_models/manufacturing_resources.py
- [x] T006 Add `AND is_deleted = false` filter to all SELECT queries for soft-deleted entities (BOMs, routes, operations, work_centers, equipment, capacity_plans, qc_checks) in backend/routers/manufacturing/core.py
- [x] T007 [P] Add `AND is_deleted = false` filter to all SELECT queries for routes and operations in backend/routers/manufacturing/routing.py
- [x] T008 [P] Add `AND is_deleted = false` filter to all SELECT queries for work_centers and operations in backend/routers/manufacturing/shopfloor.py
- [x] T009 Convert all DELETE endpoints to soft-delete (`UPDATE SET is_deleted = true, updated_at = NOW()`) for BOMs, routes, work_centers, equipment, and QC checks in backend/routers/manufacturing/core.py

**Checkpoint**: Foundation ready — all models have SoftDeleteMixin, schemas use Decimal, queries filter soft-deleted rows, DELETEs are soft. User story implementation can now begin.

---

## Phase 3: User Story 1 — تدقيق أوامر الإنتاج ودورة حياتها (Priority: P1) 🎯 MVP

**Goal**: Ensure production order CRUD and lifecycle endpoints comply with constitution — Decimal precision for cost calculations, pagination, branch isolation, and sanitized error messages.

**Independent Test**: Create a production order, start it, complete it — verify costs are Decimal, branch is validated, pagination works on list, error messages are generic.

### Implementation for User Story 1

- [x] T010 [US1] Replace `float()` with `Decimal(str(...))` in `calculate_production_cost()` function and all cost field assignments (actual_material_cost, actual_labor_cost, actual_overhead_cost, actual_total_cost, standard_cost, variance_amount, variance_percentage) in backend/routers/manufacturing/core.py
- [x] T011 [US1] Add pagination parameters (`offset: int = 0, limit: int = 25`) to GET `/manufacturing/orders` endpoint, add `LIMIT :limit OFFSET :offset` to SQL query, cap limit at 100 in backend/routers/manufacturing/core.py
- [x] T012 [US1] Add `validate_branch_access(current_user, branch_id)` to production order endpoints: POST (create), GET `/{id}` (detail), PUT (update), DELETE, POST `/{id}/start`, POST `/{id}/complete`, POST `/{id}/cancel`, POST `/{id}/calculate-cost` — resolve branch via warehouse_id → branch relationship in backend/routers/manufacturing/core.py
- [x] T013 [US1] Sanitize f-string HTTPException details in production order lifecycle transitions — replace internal state exposure (e.g., `f"Cannot start order with status {order.status}"`) with generic messages, log details via `logger.warning()` in backend/routers/manufacturing/core.py

**Checkpoint**: Production orders fully audited — Decimal costs, paginated list, branch-isolated, safe error messages.

---

## Phase 4: User Story 2 — تدقيق قائمة المواد (BOM) (Priority: P1)

**Goal**: Ensure BOM CRUD endpoints comply with constitution — branch isolation and pagination on list.

**Independent Test**: List BOMs with pagination, verify branch filter applied, verify soft-delete works (DELETE returns 200 but row has is_deleted=true).

### Implementation for User Story 2

- [x] T014 [P] [US2] Add `validate_branch_access(current_user, branch_id)` to BOM endpoints: GET list, POST (create), GET `/{bom_id}` (detail), PUT (update), DELETE — resolve branch via product → warehouse or direct parameter in backend/routers/manufacturing/core.py
- [x] T015 [US2] Add pagination parameters (`offset: int = 0, limit: int = 25`) to GET `/manufacturing/boms` endpoint, add `LIMIT :limit OFFSET :offset` to SQL query, cap limit at 100 in backend/routers/manufacturing/core.py

**Checkpoint**: BOMs fully audited — branch-isolated, paginated, soft-deletable.

---

## Phase 5: User Story 3 — تدقيق تكلفة التصنيع وتحليل الانحرافات (Priority: P1)

**Goal**: Ensure cost variance calculations and report endpoints use Decimal arithmetic and are branch-isolated.

**Independent Test**: Run cost variance report, verify all calculations return Decimal values (serialized as strings), verify branch filter applied.

### Implementation for User Story 3

- [x] T016 [US3] Replace `float()` with `Decimal(str(...))` in cost variance calculations, cost comparison logic, and any remaining cost arithmetic in report endpoints (`/reports/production-cost`, `/cost-variance-report`, `/reports/material-consumption`) in backend/routers/manufacturing/core.py
- [x] T017 [P] [US3] Add `validate_branch_access(current_user, branch_id)` to cost report endpoints: GET `/reports/production-cost`, GET `/cost-variance-report`, GET `/reports/material-consumption` in backend/routers/manufacturing/core.py

**Checkpoint**: Costing fully audited — all calculations use Decimal, reports branch-filtered.

---

## Phase 6: User Story 4 — تدقيق مسارات التصنيع والعمليات (Priority: P2)

**Goal**: Ensure route/operation CRUD endpoints comply with constitution — branch isolation, pagination on routes list, Decimal for routing quantities and times.

**Independent Test**: List routes with pagination, create/view a route with operations, verify branch filter and Decimal values.

### Implementation for User Story 4

- [x] T018 [US4] Add `validate_branch_access(current_user, branch_id)` to route CRUD endpoints: GET list, POST (create), PUT (update), DELETE in backend/routers/manufacturing/core.py
- [x] T019 [US4] Add pagination parameters (`offset: int = 0, limit: int = 25`) to GET `/manufacturing/routes` endpoint, add `LIMIT :limit OFFSET :offset` to SQL query, cap limit at 100 in backend/routers/manufacturing/core.py
- [x] T020 [US4] Add `validate_branch_access(current_user, branch_id)` to GET `/manufacturing/operations` list endpoint and POST operations `/{id}/start`, `/{id}/complete`, `/{id}/pause` endpoints in backend/routers/manufacturing/core.py
- [x] T021 [P] [US4] Replace `float` quantity parameter with `Decimal` in routing estimate/calculation endpoints in backend/routers/manufacturing/routing.py
- [x] T022 [US4] Add `validate_branch_access(current_user, branch_id)` to all routing endpoints: POST, GET list, GET `/{id}`, PUT `/{id}`, GET `/product/{id}` in backend/routers/manufacturing/routing.py

**Checkpoint**: Routes and operations fully audited — branch-isolated, paginated, Decimal quantities.

---

## Phase 7: User Story 5 — تدقيق مراكز العمل والطاقة الإنتاجية (Priority: P2)

**Goal**: Ensure work center and capacity plan endpoints comply with constitution — branch isolation for remaining WC endpoints and all capacity/OEE endpoints.

**Independent Test**: Create/update work center, view capacity plan and OEE report — verify branch filter applied. (Note: GET work_centers list already has branch validation.)

### Implementation for User Story 5

- [x] T023 [P] [US5] Add `validate_branch_access(current_user, branch_id)` to work center POST (create), PUT (update), DELETE endpoints in backend/routers/manufacturing/core.py (GET list already has it)
- [x] T024 [US5] Add `validate_branch_access(current_user, branch_id)` to capacity plan endpoints: GET `/capacity-plans`, POST, PUT `/{id}` and report endpoints: GET `/oee`, GET `/reports/work-center-efficiency` in backend/routers/manufacturing/core.py

**Checkpoint**: Work centers and capacity fully audited — all endpoints branch-isolated.

---

## Phase 8: User Story 6 — تدقيق أرضية المصنع وبطاقات العمل (Priority: P2)

**Goal**: Ensure shop floor endpoints comply with constitution — Decimal for quantities/times, branch isolation, sanitized error messages.

**Independent Test**: Start and complete a shop floor operation — verify quantities are Decimal, branch is validated, error messages are generic.

### Implementation for User Story 6

- [x] T025 [P] [US6] Replace `float()` with `Decimal(str(...))` for `cycle_time`, `quantity`, `output_quantity`, `scrap_quantity`, `downtime_minutes` conversions in backend/routers/manufacturing/shopfloor.py
- [x] T026 [US6] Add `validate_branch_access(current_user, branch_id)` to all shopfloor endpoints: GET `/dashboard`, POST `/start`, POST `/complete`, POST `/pause`, GET `/work-order/{id}` — resolve branch via work_order → production_order → warehouse in backend/routers/manufacturing/shopfloor.py
- [x] T027 [US6] Sanitize f-string HTTPException details in shopfloor error handling — replace internal state exposure with generic messages, log details via `logger.warning()` in backend/routers/manufacturing/shopfloor.py

**Checkpoint**: Shop floor fully audited — Decimal values, branch-isolated, safe error messages.

---

## Phase 9: User Story 9 — تدقيق الترابطات بين التصنيع والوحدات الأخرى (Priority: P2)

**Goal**: Ensure cross-module integration points (QC checks, GL entries, reports) comply with constitution — branch isolation for all remaining endpoints, Decimal for GL journal entries.

**Independent Test**: Complete a production order, verify GL WIP entries use Decimal, verify QC check and report endpoints are branch-filtered.

### Implementation for User Story 9

- [x] T028 [US9] Add `validate_branch_access(current_user, branch_id)` to QC check endpoints: GET `/orders/{id}/qc-checks`, POST `/orders/{id}/qc-checks`, POST `/qc-checks/{id}/record-result` in backend/routers/manufacturing/core.py
- [x] T029 [US9] Verify and fix GL journal entry amounts (WIP debit/credit) in production order start/complete flows to use `Decimal` — ensure `gl_service.py` calls pass Decimal values, not float, in backend/routers/manufacturing/core.py
- [x] T030 [US9] Add `validate_branch_access(current_user, branch_id)` to remaining report endpoints: GET `/reports/direct-labor`, GET `/reports/production-summary` in backend/routers/manufacturing/core.py

**Checkpoint**: Cross-module integration fully audited — GL entries use Decimal, all remaining endpoints branch-filtered.

---

## Phase 10: User Story 10 — التحقق من صحة الواجهات الأمامية وتجربة المستخدم (Priority: P2)

**Goal**: Replace all `console.error` calls with user-visible `toast.error()` / `useToast()` notifications in manufacturing frontend pages (22 instances across 15 files).

**Independent Test**: Trigger an API error in any manufacturing page — verify toast notification appears instead of silent console.error.

### Implementation for User Story 10

- [x] T031 [P] [US10] Replace `console.error` with `toast.error(t('common.error'))` using `useToast` hook in frontend/src/pages/Manufacturing/ProductionOrders.jsx (2 instances) and frontend/src/pages/Manufacturing/BOMs.jsx (2 instances)
- [x] T032 [P] [US10] Replace `console.error` with `toast.error(t('common.error'))` using `useToast` hook in frontend/src/pages/Manufacturing/Routings.jsx (2 instances) and frontend/src/pages/Manufacturing/WorkCenters.jsx (2 instances)
- [x] T033 [P] [US10] Replace `console.error` with `toast.error(t('common.error'))` using `useToast` hook in frontend/src/pages/Manufacturing/DirectLaborReport.jsx (2 instances) and frontend/src/pages/Manufacturing/CapacityPlanning.jsx (1 instance) and frontend/src/pages/Manufacturing/ProductionOrderDetails.jsx (1 instance)
- [x] T034 [P] [US10] Replace `console.error` with `toast.error(t('common.error'))` using `useToast` hook in frontend/src/pages/Manufacturing/EquipmentMaintenance.jsx (3 instances) and frontend/src/pages/Manufacturing/ManufacturingCosting.jsx (1 instance) and frontend/src/pages/Manufacturing/ProductionSchedule.jsx (2 instances)
- [x] T035 [P] [US10] Replace `console.error` with `toast.error(t('common.error'))` using `useToast` hook in frontend/src/pages/Manufacturing/ProductionAnalytics.jsx (1 instance), frontend/src/pages/Manufacturing/WorkOrderStatusReport.jsx (1 instance), frontend/src/pages/Manufacturing/JobCards.jsx (1 instance), frontend/src/pages/ShopFloor/ShopFloorDashboard.jsx (1 instance), and frontend/src/pages/ShopFloor/OperationEntry.jsx (1 instance)

**Checkpoint**: All 22 console.error instances replaced with toast — users see error feedback instead of silent failures.

---

## Phase 11: User Story 7 — تدقيق تخطيط MRP (Priority: P3)

**Goal**: Ensure MRP endpoints comply with constitution — branch isolation and pagination on plans list.

**Independent Test**: List MRP plans with pagination, run MRP calculation — verify branch filter and pagination applied.

### Implementation for User Story 7

- [x] T036 [P] [US7] Add `validate_branch_access(current_user, branch_id)` to MRP endpoints: GET `/mrp/calculate/{order_id}`, GET `/mrp/plans` in backend/routers/manufacturing/core.py
- [x] T037 [US7] Add pagination parameters (`offset: int = 0, limit: int = 25`) to GET `/manufacturing/mrp/plans` endpoint, add `LIMIT :limit OFFSET :offset` to SQL query, cap limit at 100 in backend/routers/manufacturing/core.py

**Checkpoint**: MRP fully audited — branch-isolated, paginated.

---

## Phase 12: User Story 8 — تدقيق صيانة المعدات (Priority: P3)

**Goal**: Ensure equipment and maintenance log endpoints comply with constitution — branch isolation, pagination on both list endpoints.

**Independent Test**: List equipment and maintenance logs with pagination — verify branch filter and pagination applied, verify soft-delete works on equipment.

### Implementation for User Story 8

- [x] T038 [P] [US8] Add `validate_branch_access(current_user, branch_id)` to equipment CRUD endpoints: GET list, POST (create), PUT (update), DELETE and maintenance log endpoints: GET list, POST (create) in backend/routers/manufacturing/core.py
- [x] T039 [US8] Add pagination parameters (`offset: int = 0, limit: int = 25`) to GET `/manufacturing/equipment` endpoint, add `LIMIT :limit OFFSET :offset` to SQL query, cap limit at 100 in backend/routers/manufacturing/core.py
- [x] T040 [US8] Add pagination parameters (`offset: int = 0, limit: int = 25`) to GET `/manufacturing/maintenance-logs` endpoint, add `LIMIT :limit OFFSET :offset` to SQL query, cap limit at 100 in backend/routers/manufacturing/core.py

**Checkpoint**: Equipment and maintenance fully audited — branch-isolated, paginated.

---

## Phase 13: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories

- [x] T041 Run quickstart.md verification checklist — confirm all audit fixes are applied correctly
- [x] T042 Verify Decimal serialization as strings in all API JSON responses — ensure backward compatibility with frontend string parsing
- [x] T043 Verify all soft-deleted entities (BOMs, routes, work_centers, equipment, operations, QC checks) are excluded from dropdown/select options in frontend components

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (migration must exist before model changes) — **BLOCKS all user stories**
- **User Stories (Phases 3–12)**: All depend on Phase 2 completion
  - P1 stories (US1, US2, US3) can proceed in parallel after Phase 2
  - P2 stories (US4, US5, US6, US9, US10) can proceed in parallel after Phase 2
  - P3 stories (US7, US8) can proceed in parallel after Phase 2
- **Polish (Phase 13)**: Depends on all user story phases being complete

### User Story Dependencies

- **US1 (P1)**: After Phase 2 — no dependencies on other stories
- **US2 (P1)**: After Phase 2 — no dependencies on other stories
- **US3 (P1)**: After Phase 2 — references same cost functions as US1 but different endpoints
- **US4 (P2)**: After Phase 2 — no dependencies on P1 stories
- **US5 (P2)**: After Phase 2 — no dependencies on P1 stories
- **US6 (P2)**: After Phase 2 — no dependencies on P1 stories
- **US7 (P3)**: After Phase 2 — no dependencies on P1/P2 stories
- **US8 (P3)**: After Phase 2 — no dependencies on P1/P2 stories
- **US9 (P2)**: After Phase 2 — may reference US1 cost flows but independently testable
- **US10 (P2)**: After Phase 2 — frontend-only, no backend dependencies beyond Phase 2

### Within Each User Story

- Branch validation tasks before error sanitization (same file context)
- Pagination tasks are independent of branch validation
- All [P] tasks within a phase can run in parallel

### File Contention Notes

- **core.py** is modified by US1–US9 — execute these sequentially when targeting core.py
- **routing.py** is only modified by US4 — no contention
- **shopfloor.py** is only modified by US6 — no contention
- **Frontend files** (US10) have zero contention — all tasks are [P]

### Parallel Opportunities

**After Phase 2 completes, maximum parallelism:**

```
Developer A (Backend - core.py):  US1 → US2 → US3 → US4 (core.py parts) → US5 → US7 → US8 → US9
Developer B (Backend - routing.py + shopfloor.py):  US4 (routing.py) → US6
Developer C (Frontend):  US10 (all frontend tasks in parallel)
```

---

## Parallel Example: Foundational Phase

```
# All model changes in parallel (3 different files):
T003: SoftDeleteMixin in manufacturing_bom_capacity.py
T004: SoftDeleteMixin in manufacturing_execution.py
T005: SoftDeleteMixin in manufacturing_resources.py

# Query filter changes in parallel (3 different files):
T007: is_deleted filter in routing.py
T008: is_deleted filter in shopfloor.py
# T006 (core.py) runs before T009 (core.py) — same file
```

## Parallel Example: User Story 10 (Frontend)

```
# ALL frontend tasks run in parallel (different files):
T031: ProductionOrders.jsx + BOMs.jsx
T032: Routings.jsx + WorkCenters.jsx
T033: DirectLaborReport.jsx + CapacityPlanning.jsx + ProductionOrderDetails.jsx
T034: EquipmentMaintenance.jsx + ManufacturingCosting.jsx + ProductionSchedule.jsx
T035: ProductionAnalytics.jsx + WorkOrderStatusReport.jsx + JobCards.jsx + ShopFloor pages
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (1 task — Alembic migration)
2. Complete Phase 2: Foundational (8 tasks — schema + models + query filters + soft-delete)
3. Complete Phase 3: US1 — Production Orders (4 tasks)
4. **STOP and VALIDATE**: Test production order CRUD with Decimal costs, pagination, branch isolation
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready (9 tasks)
2. Add US1 + US2 + US3 → Core manufacturing audited (MVP!) (8 tasks)
3. Add US4 + US5 + US6 → Routes, work centers, shop floor audited (10 tasks)
4. Add US9 → Cross-module integration verified (3 tasks)
5. Add US10 → Frontend error feedback fixed (5 tasks)
6. Add US7 + US8 → MRP and equipment audited (5 tasks)
7. Polish → Final validation (3 tasks)
8. Each increment adds audit coverage without breaking previous fixes

---

## Notes

- **Audit-fix only**: No new features, no new tables, no new files — all changes are corrections to existing code
- **Backward compatible**: Decimal serializes as string in JSON (frontend already parses strings), pagination adds optional params with defaults, branch validation is transparent
- **9 models get SoftDeleteMixin**: BillOfMaterial, BomComponent, BomOutput, CapacityPlan, ManufacturingEquipment, ManufacturingOperation, ManufacturingRoute, MfgQcCheck, WorkCenter
- **6 models excluded from SoftDeleteMixin** (per research R2): ProductionOrder, ProductionOrderOperation (state-machine), MrpPlan, MrpItem (state-machine), ShopFloorLog (append-only), plus junction tables
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
