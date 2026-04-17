# Data Model: Audit Purchases Module

**Feature**: 011-audit-purchases | **Date**: 2026-04-15

## Entity Overview

This audit does NOT create new tables — it fixes existing procurement tables for constitution compliance. The changes are:
1. Adding missing audit columns to 11 tables
2. Changing Pydantic schema field types from `float` to `Decimal`
3. Adding `AuditMixin` inheritance to domain models

## Audit Column Additions

### Tables requiring `updated_by` only (5 tables)

These already have `created_at`, `updated_at` (or equivalent), `created_by`:

| Table | DDL Line | Addition |
|-------|----------|----------|
| `purchase_orders` | L885 | `updated_by INTEGER REFERENCES users(id)` |
| `request_for_quotations` | L1147 | `updated_by INTEGER REFERENCES users(id)` |
| `landed_costs` | L5172 | `updated_by INTEGER REFERENCES users(id)` |

### Tables requiring multiple columns (6 tables)

| Table | DDL Line | Missing columns |
|-------|----------|----------------|
| `purchase_order_lines` | L906 | `updated_at`, `created_by`, `updated_by` |
| `rfq_lines` | L1160 | ALL 4: `created_at`, `updated_at`, `created_by`, `updated_by` |
| `rfq_responses` | L1170 | `created_at` (has `submitted_at`), `updated_at`, `created_by`, `updated_by` |
| `purchase_agreements` | L1199 | `updated_at`, `updated_by` |
| `purchase_agreement_lines` | L1215 | ALL 4: `created_at`, `updated_at`, `created_by`, `updated_by` |
| `supplier_ratings` | L1184 | `created_at` (has `rated_at`), `updated_at`, `updated_by` |

### Tables requiring 3 columns (2 tables)

| Table | DDL Line | Missing columns |
|-------|----------|----------------|
| `landed_cost_items` | L5192 | `updated_at`, `created_by`, `updated_by` |
| `landed_cost_allocations` | L5203 | `updated_at`, `created_by`, `updated_by` |

### Column specifications

| Column | Type | Default | Nullable | FK |
|--------|------|---------|----------|-----|
| `created_at` | `TIMESTAMP` | `NOW()` | NO | — |
| `updated_at` | `TIMESTAMP` | `NOW()` | NO | — |
| `created_by` | `INTEGER` | `NULL` | YES | `REFERENCES users(id)` |
| `updated_by` | `INTEGER` | `NULL` | YES | `REFERENCES users(id)` |

## Domain Model Changes

### Models to add `AuditMixin` inheritance

All models currently inherit only `ModelBase`. They need to also inherit `AuditMixin`:

| Model class | File | Current base | New base |
|------------|------|-------------|----------|
| `PurchaseOrder` | `procurement_orders.py` | `ModelBase` | `ModelBase, AuditMixin` |
| `PurchaseOrderLine` | `procurement_orders.py` | `ModelBase` | `ModelBase, AuditMixin` |
| `LandedCost` | `procurement_costs.py` | `ModelBase` | `ModelBase, AuditMixin` |
| `LandedCostItem` | `procurement_costs.py` | `ModelBase` | `ModelBase, AuditMixin` |
| `LandedCostAllocation` | `shared_dashboard_fiscal_intercompany.py` | `ModelBase` | `ModelBase, AuditMixin` |
| `PurchaseAgreement` | `procurement_costs.py` | `ModelBase` | `ModelBase, AuditMixin` |
| `PurchaseAgreementLine` | `procurement_costs.py` | `ModelBase` | `ModelBase, AuditMixin` |
| `SupplierRating` | `procurement_suppliers.py` | `ModelBase` | `ModelBase, AuditMixin` |

Note: `BlanketPurchaseOrder` and `BlanketPOReleaseOrder` already inherit `AuditMixin` — no change needed.

## Pydantic Schema Changes

### `schemas/purchases.py` — 16 float→Decimal

| Class | Field | Current | New |
|-------|-------|---------|-----|
| `PurchaseLineItem` | `quantity` | `float` | `Decimal` |
| `PurchaseLineItem` | `unit_price` | `float` | `Decimal` |
| `PurchaseLineItem` | `tax_rate` | `float` | `Decimal` |
| `PurchaseLineItem` | `discount` | `float = 0.0` | `Decimal = Decimal("0")` |
| `PurchaseLineItem` | `markup` | `float = 0.0` | `Decimal = Decimal("0")` |
| `PurchaseCreate` | `paid_amount` | `float = 0.0` | `Decimal = Decimal("0")` |
| `PurchaseCreate` | `effect_percentage` | `float = 0.0` | `Decimal = Decimal("0")` |
| `PurchaseCreate` | `markup_amount` | `float = 0.0` | `Decimal = Decimal("0")` |
| `PurchaseCreate` | `exchange_rate` | `Optional[float]` | `Optional[Decimal]` |
| `SupplierGroupCreate` | `discount_percentage` | `float = 0.0` | `Decimal = Decimal("0")` |
| `POCreate` | `effect_percentage` | `float = 0.0` | `Decimal = Decimal("0")` |
| `POCreate` | `markup_amount` | `float = 0.0` | `Decimal = Decimal("0")` |
| `POCreate` | `exchange_rate` | `Optional[float]` | `Optional[Decimal]` |
| `ReceiveItem` | `received_quantity` | `float` | `Decimal` |
| `PaymentAllocationSchema` | `allocated_amount` | `float` | `Decimal` |
| `SupplierPaymentCreate` | `amount` | `float` | `Decimal` |

### `schemas/matching.py` — 12 float→Decimal

| Class | Field | Current | New |
|-------|-------|---------|-----|
| `MatchToleranceCreate` | `quantity_percent` | `float = 0` | `Decimal = Decimal("0")` |
| `MatchToleranceCreate` | `quantity_absolute` | `float = 0` | `Decimal = Decimal("0")` |
| `MatchToleranceCreate` | `price_percent` | `float = 0` | `Decimal = Decimal("0")` |
| `MatchToleranceCreate` | `price_absolute` | `float = 0` | `Decimal = Decimal("0")` |
| `MatchToleranceRead` | `quantity_percent` | `float` | `Decimal` |
| `MatchToleranceRead` | `quantity_absolute` | `float` | `Decimal` |
| `MatchToleranceRead` | `price_percent` | `float` | `Decimal` |
| `MatchToleranceRead` | `price_absolute` | `float` | `Decimal` |
| `ThreeWayMatchLineRead` | 4 fields | `float` | `Decimal` |

### `routers/matching.py` inline schema — 4 float→Decimal

| Class | Field | Line | Current | New |
|-------|-------|------|---------|-----|
| `ToleranceSave` | `quantity_percent` | L39 | `float = 0` | `Decimal = Decimal("0")` |
| `ToleranceSave` | `quantity_absolute` | L40 | `float = 0` | `Decimal = Decimal("0")` |
| `ToleranceSave` | `price_percent` | L41 | `float = 0` | `Decimal = Decimal("0")` |
| `ToleranceSave` | `price_absolute` | L42 | `float = 0` | `Decimal = Decimal("0")` |

## Relationships

No new relationships. All existing FK relationships are preserved. The audit columns add FK references to the `users` table for `created_by` and `updated_by`.

## State Transitions

No changes to any state machine or workflow. Existing PO status transitions (`draft → submitted → approved → received → completed`) are unaffected.

## Validation Rules

No new validation rules. Existing validation continues to work — Pydantic `Decimal` type accepts both string and numeric JSON input, so no API contract breaking change.
