# Data Model: Audit Manufacturing Module

**Feature**: 016-audit-manufacturing  
**Date**: 2026-04-16  
**Status**: Complete

## Existing Tables (No Schema Changes)

This is an audit-fix spec. All database tables already exist and are migrated. The data model below documents the existing schema for reference during audit fixes.

### production_orders
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| order_number | VARCHAR(50) UNIQUE | Format: `PO-{yymmddHHMMSS}` |
| product_id | INTEGER FK → products(id) | Finished good |
| bom_id | INTEGER FK → bill_of_materials(id) | Recipe |
| route_id | INTEGER FK → manufacturing_routes(id) | Process path |
| quantity | NUMERIC(15,4) | Ordered qty |
| produced_quantity | NUMERIC(15,4) DEFAULT 0 | Completed qty |
| scrapped_quantity | NUMERIC(15,4) DEFAULT 0 | Waste qty |
| status | VARCHAR(20) DEFAULT 'draft' | draft→confirmed→in_progress→completed→cancelled |
| start_date, due_date | DATE | Plan dates |
| warehouse_id | INTEGER FK → warehouses(id) | Source (raw materials) |
| destination_warehouse_id | INTEGER FK → warehouses(id) | Destination (finished goods) |
| actual_material_cost | NUMERIC(15,4) | Actual material cost |
| actual_labor_cost | NUMERIC(15,4) | Actual labor cost |
| actual_overhead_cost | NUMERIC(15,4) | Actual overhead cost |
| actual_total_cost | NUMERIC(15,4) | Sum of all actuals |
| standard_cost | NUMERIC(15,4) | Expected cost from BOM |
| variance_amount | NUMERIC(15,4) | actual - standard |
| variance_percentage | NUMERIC(8,4) | % variance |
| costing_status | VARCHAR(20) DEFAULT 'pending' | pending→calculated |
| created_by | INTEGER FK → company_users(id) | Creator |
| created_at, updated_at | TIMESTAMP WITH TZ | Audit timestamps |

### bill_of_materials
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| product_id | INTEGER FK → products(id) | Output product |
| code | VARCHAR(50) | BOM code |
| name | VARCHAR(255) | BOM name |
| yield_quantity | NUMERIC(15,4) DEFAULT 1.0 | Output qty per run |
| route_id | INTEGER FK → manufacturing_routes(id) | Linked route |
| is_active | BOOLEAN DEFAULT TRUE | Active flag |
| notes | TEXT | |
| created_at, updated_at | TIMESTAMP WITH TZ | |

### bom_components
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| bom_id | INTEGER FK → bill_of_materials(id) CASCADE | Parent BOM |
| component_product_id | INTEGER FK → products(id) | Raw material |
| quantity | NUMERIC(15,4) | Required qty |
| waste_percentage | NUMERIC(5,2) DEFAULT 0 | Scrap allowance |
| cost_share_percentage | NUMERIC(5,2) DEFAULT 0 | Cost allocation |
| is_percentage | BOOLEAN DEFAULT FALSE | Variable BOM: qty = % of order qty |
| notes | TEXT | |

### bom_outputs
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| bom_id | INTEGER FK → bill_of_materials(id) CASCADE | Parent BOM |
| product_id | INTEGER FK → products(id) | By-product |
| quantity | NUMERIC(15,4) | By-product qty |
| cost_allocation_percentage | NUMERIC(5,2) DEFAULT 0 | Cost split |
| notes | TEXT | |

### manufacturing_routes
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| name | VARCHAR(255) | Route name |
| product_id | INTEGER FK → products(id) | Product |
| bom_id | INTEGER FK → bill_of_materials(id) | Linked BOM |
| is_default | BOOLEAN DEFAULT FALSE | Default route flag |
| is_active | BOOLEAN DEFAULT TRUE | |
| description | TEXT | |
| created_at, updated_at | TIMESTAMP WITH TZ | |

### manufacturing_operations
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| route_id | INTEGER FK → manufacturing_routes(id) CASCADE | Parent route |
| sequence | INTEGER | Step order |
| name | VARCHAR(255) | Operation name |
| work_center_id | INTEGER FK → work_centers(id) | Assigned WC |
| setup_time | NUMERIC(10,2) DEFAULT 0 | Setup minutes |
| cycle_time | NUMERIC(10,2) DEFAULT 0 | Minutes per unit |
| labor_rate_per_hour | NUMERIC(18,4) DEFAULT 0 | Labor cost/hour |
| created_at, updated_at | TIMESTAMP WITH TZ | |

### work_centers
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| name | VARCHAR(255) | |
| code | VARCHAR(50) UNIQUE | |
| capacity_per_day | NUMERIC(5,2) DEFAULT 8.0 | Hours/day |
| cost_per_hour | NUMERIC(18,4) DEFAULT 0 | Labor cost |
| location | VARCHAR(100) | |
| cost_center_id | INTEGER FK → cost_centers(id) | GL mapping |
| default_expense_account_id | INTEGER FK → accounts(id) | Labor posting |
| status | VARCHAR(20) DEFAULT 'active' | active/inactive/decommissioned |
| created_at, updated_at | TIMESTAMP WITH TZ | |

### production_order_operations
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| production_order_id | INTEGER FK → production_orders(id) CASCADE | |
| operation_id | INTEGER FK → manufacturing_operations(id) | Template op |
| work_center_id | INTEGER FK → work_centers(id) | |
| status | VARCHAR(20) DEFAULT 'pending' | pending/in_progress/paused/completed |
| worker_id | INTEGER FK → company_users(id) | Operator |
| actual_setup_time | NUMERIC(8,2) DEFAULT 0 | |
| actual_run_time | NUMERIC(8,2) DEFAULT 0 | Minutes |
| completed_quantity | NUMERIC(15,4) DEFAULT 0 | |
| scrapped_quantity | NUMERIC(15,4) DEFAULT 0 | |
| planned_start_time, planned_end_time | TIMESTAMP WITH TZ | |
| start_time, end_time | TIMESTAMP WITH TZ | |
| sequence | INTEGER | |
| created_at, updated_at | TIMESTAMP WITH TZ | |

### shop_floor_logs
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| work_order_id | INTEGER FK → production_orders(id) CASCADE | |
| routing_operation_id | INTEGER FK → manufacturing_operations(id) | |
| operator_id | INTEGER FK → employees(id) | |
| started_at, completed_at | TIMESTAMP WITH TZ | |
| output_quantity | NUMERIC(18,4) DEFAULT 0 | |
| scrap_quantity | NUMERIC(18,4) DEFAULT 0 | |
| downtime_minutes | NUMERIC(10,2) DEFAULT 0 | |
| status | VARCHAR(20) DEFAULT 'in_progress' | in_progress/paused/completed |
| notes | TEXT | |
| INDEX: work_order_id, status | | |

### capacity_plans
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| work_center_id | INTEGER FK → work_centers(id) CASCADE | |
| plan_date | DATE | UNIQUE(work_center_id, plan_date) |
| available_hours | NUMERIC(10,2) DEFAULT 8 | |
| planned_hours | NUMERIC(10,2) DEFAULT 0 | |
| actual_hours | NUMERIC(10,2) DEFAULT 0 | |
| efficiency_pct | NUMERIC(5,2) DEFAULT 0 | |
| created_by | INTEGER FK → company_users(id) | |

### manufacturing_equipment
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| name | VARCHAR(255) | |
| code | VARCHAR(50) UNIQUE | |
| work_center_id | INTEGER FK → work_centers(id) | |
| status | VARCHAR(20) DEFAULT 'active' | active/under_maintenance/decommissioned |
| purchase_date | DATE | |
| last_maintenance_date, next_maintenance_date | DATE | |
| created_at, updated_at | TIMESTAMP WITH TZ | |

### mrp_plans / mrp_items
| Column | Type | Notes |
|--------|------|-------|
| mrp_plans: id, plan_name, production_order_id FK, status, calculated_at, created_by | | |
| mrp_items: id, mrp_plan_id FK CASCADE, product_id FK, required_quantity, available_quantity, on_hand_quantity, on_order_quantity, shortage_quantity (all NUMERIC(18,4)), lead_time_days, suggested_action | | |

### mfg_qc_checks
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| production_order_id | INTEGER FK → production_orders(id) CASCADE | |
| operation_id | INTEGER FK → manufacturing_operations(id) | |
| check_name | VARCHAR(200) | |
| check_type | VARCHAR(30) DEFAULT 'visual' | |
| specification | TEXT | |
| actual_value | VARCHAR(200) | |
| result | VARCHAR(20) DEFAULT 'pending' | pending/pass/fail/warning |
| failure_action | VARCHAR(20) DEFAULT 'warn' | warn/stop |
| checked_by | INTEGER FK → company_users(id) | |

## Schema Changes Required (Audit Fixes)

### Migration: Add SoftDeleteMixin columns

**Tables requiring `is_deleted BOOLEAN DEFAULT FALSE` column:**

1. `bill_of_materials`
2. `bom_components`
3. `bom_outputs`
4. `capacity_plans`
5. `manufacturing_equipment`
6. `manufacturing_operations`
7. `manufacturing_routes`
8. `mfg_qc_checks`
9. `work_centers`

**NOT requiring SoftDeleteMixin** (exempt per constitution):
- `shop_floor_logs` — append-only log table
- `production_orders` — state-machine (status-based lifecycle, no DELETE)
- `production_order_operations` — tied to production order lifecycle
- `mrp_plans` / `mrp_items` — state-machine / child of state-machine

### Pydantic Schema Changes

All `float` fields in `backend/schemas/manufacturing_advanced.py` → `Decimal`:
- `cost_per_hour`, `capacity_per_day` (WorkCenter)
- `setup_time`, `cycle_time`, `labor_rate_per_hour` (Operation)
- `quantity`, `waste_percentage`, `cost_share_percentage` (BomComponent)
- `yield_quantity` (BOM)
- `quantity`, `cost_allocation_percentage` (BomOutput)
- `quantity`, `produced_quantity`, `scrapped_quantity` (ProductionOrder)
- All cost fields in ProductionOrder responses

## Entity Relationships

```
products ←──── bill_of_materials ←── bom_components ──→ products (raw materials)
    │                │                                   
    │                ├── bom_outputs ──→ products (by-products)
    │                │
    │          manufacturing_routes ←── manufacturing_operations ──→ work_centers
    │                │                                                    │
    │          production_orders ←── production_order_operations           │
    │                │                       │                            │
    │                ├── shop_floor_logs      └──→ manufacturing_operations │
    │                │                                                    │
    │                ├── mrp_plans ←── mrp_items ──→ products             │
    │                │                                                    │
    │                └── mfg_qc_checks                                    │
    │                                                                     │
    └──────────────── manufacturing_equipment ────────────────────────────┘

work_centers ──→ cost_centers (GL mapping)
work_centers ──→ accounts (expense account)
work_centers ←── capacity_plans
```
