# Research: Audit Manufacturing Module

**Feature**: 016-audit-manufacturing  
**Date**: 2026-04-16  
**Status**: Complete

## Research Tasks

### R1: Float → Decimal migration strategy for manufacturing schemas

**Decision**: Convert all `float` fields in `schemas/manufacturing_advanced.py` to `Decimal` using Pydantic's `condecimal` / `Field(decimal_places=4)`. In routers, replace `float()` calls with `Decimal(str(value))` for safe conversion.

**Rationale**: Constitution I mandates `decimal.Decimal` + `ROUND_HALF_UP` for all monetary values. Manufacturing has 20+ float fields across schemas and 6+ `float()` calls in routers. The existing WAC cost update formula and `calculate_production_cost()` function accumulate precision errors with float arithmetic.

**Alternatives considered**:
- Leave as float with rounding at boundaries → Rejected: violates constitution, accumulates errors in multi-step cost calculations
- Use Python `int` (cents) → Rejected: inconsistent with rest of codebase which uses Decimal

### R2: SoftDeleteMixin addition for 9 manufacturing models

**Decision**: Add `SoftDeleteMixin` to all 9 manufacturing domain models (BillOfMaterial, BomComponent, BomOutput, CapacityPlan, ManufacturingEquipment, ManufacturingOperation, ManufacturingRoute, MfgQcCheck, WorkCenter). Create an Alembic migration to add `is_deleted BOOLEAN DEFAULT FALSE` column. Update all SELECT queries to filter `is_deleted = false`. Convert DELETE operations to `UPDATE SET is_deleted = true`.

**Rationale**: Constitution XVII mandates SoftDeleteMixin on ALL business-entity models. The 9 manufacturing models currently use physical DELETE, which is unrecoverable and violates audit trail requirements. Three exception cases (pure junction tables, append-only logs) do NOT apply here — these are all business entities.

**Exceptions considered**:
- `BomComponent` / `BomOutput` → These ARE junction-like but contain business data (quantities, cost allocations) — SoftDeleteMixin required
- `ShopFloorLog` → Already append-only (no DELETE endpoint) — SoftDeleteMixin NOT needed
- `ProductionOrder`, `ProductionOrderOperation`, `MrpPlan`, `MrpItem` → Already have their own lifecycle (status-based, no DELETE) — SoftDeleteMixin NOT needed for state-machine entities

### R3: Branch validation strategy for manufacturing endpoints

**Decision**: Add `validate_branch_access(current_user, branch_id)` to the 16+ endpoints that lack it. For endpoints that don't directly reference a branch_id, resolve via warehouse → branch relationship using `resolve_warehouse_branch()`. For list endpoints, add branch_id filtering to query WHERE clause.

**Rationale**: Constitution IV requires branch filtering on every branch-scoped endpoint. Currently only 2 of 18+ endpoints validate branch access.

**Alternatives considered**:
- Add branch validation at middleware level → Rejected: manufacturing endpoints need granular warehouse→branch resolution, not blanket filtering
- Skip for read-only endpoints → Rejected: constitution says "every branch-scoped endpoint"

### R4: Pagination for list endpoints

**Decision**: Add `offset: int = 0, limit: int = 25` parameters to the 6 list endpoints that lack them. Add `LIMIT :limit OFFSET :offset` to SQL queries. Cap `limit` at 100 per constitution.

**Rationale**: Constitution VII requires "Default 25 rows, max 100" pagination. The 6 list endpoints (routes, BOMs, production orders, MRP plans, equipment, maintenance logs) currently return ALL rows.

**Alternatives considered**:
- Cursor-based pagination → Rejected: overcomplicated for current scale; consistent with rest of codebase using offset/limit

### R5: Error message sanitization in manufacturing routers

**Decision**: Replace f-string HTTPException details that expose internal state (e.g., `f"Cannot start order with status {order.status}"`) with generic user-facing messages. Log detailed info via `logger.exception()`.

**Rationale**: Constitution IV forbids `raise HTTPException(detail=str(e))` and exposing internal state. While the manufacturing routers don't use `str(e)` directly, they DO expose internal status values and operation sequences in error details.

**Alternatives considered**:
- Keep f-strings for better debugging → Rejected: security risk per constitution; logging covers debug needs

### R6: console.error → toast migration in frontend

**Decision**: Replace 22 `console.error` instances across 15 frontend files with proper `useToast()` or `toastEmitter` calls. Pattern: `catch (err) { console.error(...) }` → `catch (err) { toast.error(t('common.error')) }`.

**Rationale**: Constitution XXVII mandates user-visible error feedback. `console.error` is invisible to users and provides no actionable information in the UI.

**Alternatives considered**:
- Add toast alongside console.error → Rejected: console.error in production code is forbidden per constitution VII (`print()` analog)

### R7: Frontend completeness verification

**Decision**: All 22 manufacturing frontend pages exist with proper routing in App.jsx, proper lazy loading, proper permission gates (`PrivateRoute permission="manufacturing.view"`), proper i18next translation via `t()` function, and proper RTL support via `i18n.language === 'ar'`. The `formatNumber()` utility is correctly used for monetary display. No hardcoded strings found. WebSocket integration in ShopFloor is functional with proper error handling.

**Rationale**: Spec FR-027 through FR-031 require frontend completeness verification. Investigation confirms compliance in RTL, i18n, permissions, navigation, and formatNumber usage.

**No action needed** for: translation, RTL layout, formatNumber, permissions routing, WebSocket.
