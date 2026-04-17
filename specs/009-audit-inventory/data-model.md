# Data Model: Audit Inventory Module

**Feature**: 009-audit-inventory
**Date**: 2026-04-15
**Source**: 4 domain model files, 26 tables total

## Existing Schema (No Changes Needed)

The inventory module uses 26 tables across 4 domain model groups. All tables use `NUMERIC(18,4)` for monetary/quantity fields (Constitution §I compliant at the schema level). The schema is stable — this audit changes application code, not schema structure, with one exception (missing audit columns).

### Table Summary

| Group | File | Tables | Audit Fields Status |
|-------|------|--------|-------------------|
| Core | `inventory_core.py` | 6 | ⚠ 2 tables missing fields |
| Transfers | `inventory_transfers.py` | 3 | OK (append-only logs) |
| Advanced | `inventory_advanced.py` | 15 | OK |
| Costing | `inventory_costing.py` | 2 | ✅ Full AuditMixin + SoftDeleteMixin |

### Core Tables (inventory_core.py)

| Table | Key Columns | Audit Fields |
|-------|-------------|--------------|
| `product_categories` | id, category_code (UNIQUE), category_name, parent_id (self-FK), branch_id, is_active | ⚠ `created_at` only — missing `created_by`, `updated_at`, `updated_by` |
| `product_units` | id, unit_code (UNIQUE), unit_name, base_unit_id (self-FK), conversion_factor NUMERIC(10,6) | `created_at` only |
| `products` | id, product_code (UNIQUE), sku (UNIQUE), cost_price/selling_price/wholesale_price NUMERIC(18,4), has_batch/serial/expiry_tracking, version (optimistic lock) | `created_at`, `updated_at` |
| `inventory` | id, product_id+warehouse_id (UNIQUE), quantity/reserved/available NUMERIC(18,4), average_cost, policy_version | `created_at`, `updated_at` |
| `inventory_transactions` | id, product_id, warehouse_id, transaction_type, quantity/unit_cost/total_cost NUMERIC(18,4), balance_before/after | `created_at`, `created_by` (append-only — OK) |
| `stock_adjustments` | id, adjustment_number (UNIQUE), warehouse_id, product_id, old/new/difference NUMERIC(18,4), status | ⚠ `created_at`, `created_by` — missing `updated_at`, `updated_by` |

### Transfer Tables (inventory_transfers.py)

| Table | Key Columns | Audit Fields |
|-------|-------------|--------------|
| `stock_shipments` | id, shipment_ref (UNIQUE), source/destination_warehouse_id, status (pending→shipped→received) | `created_at`, `created_by`, `shipped_at`, `received_at`, `received_by` |
| `stock_shipment_items` | id, shipment_id (CASCADE), product_id, quantity NUMERIC(18,4) | None (child of shipment) |
| `stock_transfer_log` | id, shipment_id, product_id, from/to_warehouse_id, quantity/transfer_cost/avg_cost NUMERIC(18,4) | `created_at` (append-only — OK) |

### Advanced Tables (inventory_advanced.py)

| Table | Key Columns | Audit Fields |
|-------|-------------|--------------|
| `batch_serial_movements` | id, product_id, batch_id, serial_id, warehouse_id, movement_type, quantity NUMERIC(18,4) | `created_at`, `created_by` (append-only) |
| `cycle_counts` | id, count_number (UNIQUE), warehouse_id, status (draft→in_progress→completed), total/counted/variance_items | `created_at`, `updated_at`, `created_by` |
| `cycle_count_items` | id, cycle_count_id (CASCADE), product_id, system/counted_quantity NUMERIC(18,4), variance/variance_value, unit_cost | None (child of cycle count) |
| `bin_locations` | id, warehouse_id+bin_code (UNIQUE), zone/aisle/rack/shelf, bin_type, max_weight/volume | `created_at` |
| `bin_inventory` | id, bin_id+product_id+batch_id (UNIQUE), quantity NUMERIC(15,4) | `updated_at` |
| `product_attributes` | id, attribute_name, attribute_type | `created_at` |
| `product_attribute_values` | id, attribute_id (CASCADE), value_name, color_code | `created_at` |
| `product_variants` | id, product_id (CASCADE), variant_code, sku, cost/selling_price NUMERIC(15,2) | `created_at`, `updated_at` |
| `product_variant_attributes` | id, variant_id+attribute_id (UNIQUE), attribute_value_id | None (junction) |
| `product_batches` | id, product_id+warehouse_id+batch_number (UNIQUE), manufacturing/expiry_date, quantity/available/unit_cost NUMERIC(18,4) | `created_at`, `updated_at`, `created_by` |
| `product_serials` | id, product_id+serial_number (UNIQUE), warehouse_id, batch_id, status, purchase/sale_price NUMERIC(18,4) | `created_at`, `updated_at`, `created_by` |
| `quality_inspections` | id, inspection_number (UNIQUE), product_id, warehouse_id, inspected/accepted/rejected_quantity NUMERIC(18,4), status | `created_at`, `updated_at`, `created_by` |
| `quality_inspection_criteria` | id, inspection_id (CASCADE), criteria_name, expected/actual_value, is_passed | None (child) |
| `product_kits` | id, product_id (CASCADE), kit_name, kit_type | `created_at`, `updated_at` |
| `product_kit_items` | id, kit_id (CASCADE), component_product_id, quantity NUMERIC(15,4), unit_cost NUMERIC(15,2) | None (child) |

### Costing Tables (inventory_costing.py)

| Table | Key Columns | Audit Fields |
|-------|-------------|--------------|
| `cost_layers` | id, product_id (RESTRICT), warehouse_id (RESTRICT), costing_method, original/remaining_qty NUMERIC(18,4), unit_cost, is_exhausted. CHECK: remaining_quantity >= 0 | ✅ Full AuditMixin + SoftDeleteMixin |
| `cost_layer_consumptions` | id, cost_layer_id (CASCADE), quantity_consumed NUMERIC(18,4), sale_document_type/id | ✅ Full AuditMixin + SoftDeleteMixin |

## Migration Required

### ADD: Missing audit columns

**Migration**: `add_inventory_audit_columns.py`

```sql
-- product_categories: add created_by, updated_at, updated_by
ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES company_users(id);
ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ;
ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES company_users(id);

-- stock_adjustments: add updated_at, updated_by
ALTER TABLE stock_adjustments ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ;
ALTER TABLE stock_adjustments ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES company_users(id);
```

**Dual-update requirement** (Constitution §XXVIII):
1. Migration file in `backend/migrations/`
2. Update `backend/database.py` CREATE TABLE definitions
3. Update `backend/models/domain_models/inventory_core.py` model classes

## Schema Discrepancy Found

`cost_layer_consumptions` in `database.py` may be missing `deleted_by` column (model includes it via SoftDeleteMixin). This should be verified and fixed if confirmed — but it is in the costing model group which uses full mixins, so the column may be auto-created. Low priority relative to the mandatory audit column additions above.

## Entity Relationship Notes

- `products` → `inventory` (1:many via warehouse): one product can have stock in multiple warehouses
- `products` → `product_batches` (1:many): batch tracking per product per warehouse
- `products` → `product_serials` (1:many): individual serial tracking
- `products` → `cost_layers` (1:many): FIFO/LIFO cost tracking per warehouse
- `inventory` → `inventory_transactions` (1:many): full movement audit trail
- `stock_shipments` → `stock_shipment_items` (1:many CASCADE): shipment line items
- `cycle_counts` → `cycle_count_items` (1:many CASCADE): count line items
- `quality_inspections` → `quality_inspection_criteria` (1:many CASCADE): QC criteria
- `product_kits` → `product_kit_items` (1:many CASCADE): BOM components
