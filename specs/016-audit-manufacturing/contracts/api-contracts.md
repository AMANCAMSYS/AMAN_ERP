# API Contracts: Manufacturing Module

**Feature**: 016-audit-manufacturing  
**Date**: 2026-04-16  
**Status**: Complete — documents EXISTING endpoints (no changes to contracts)

This audit does NOT change API contracts. All endpoints preserve backward compatibility.
The only changes are internal: float→Decimal (serialized as string — compatible), pagination parameters (additive), branch validation (transparent to callers).

## Existing Endpoints (Reference)

### Work Centers

| Method | Path | Permission | Pagination | Branch Filter |
|--------|------|------------|------------|--------------|
| GET | `/manufacturing/work-centers` | manufacturing.view | ✅ (existing) | ✅ (existing) |
| POST | `/manufacturing/work-centers` | manufacturing.manage + manufacturing.create | N/A | **ADD** |
| PUT | `/manufacturing/work-centers/{wc_id}` | manufacturing.manage | N/A | **ADD** |
| DELETE | `/manufacturing/work-centers/{wc_id}` | manufacturing.manage + manufacturing.delete | N/A | **ADD** |

### BOMs

| Method | Path | Permission | Pagination | Branch Filter |
|--------|------|------------|------------|--------------|
| GET | `/manufacturing/boms` | manufacturing.view | **ADD** | **ADD** |
| POST | `/manufacturing/boms` | manufacturing.manage + manufacturing.create | N/A | **ADD** |
| GET | `/manufacturing/boms/{bom_id}` | manufacturing.view | N/A | **ADD** |
| PUT | `/manufacturing/boms/{bom_id}` | manufacturing.manage | N/A | **ADD** |
| DELETE | `/manufacturing/boms/{bom_id}` | manufacturing.manage + manufacturing.delete | N/A | **ADD** |
| GET | `/manufacturing/boms/{bom_id}/compute-materials` | manufacturing.view | N/A | N/A |

### Routes

| Method | Path | Permission | Pagination | Branch Filter |
|--------|------|------------|------------|--------------|
| GET | `/manufacturing/routes` | manufacturing.view | **ADD** | **ADD** |
| POST | `/manufacturing/routes` | manufacturing.manage + manufacturing.create | N/A | **ADD** |
| PUT | `/manufacturing/routes/{route_id}` | manufacturing.manage | N/A | **ADD** |
| DELETE | `/manufacturing/routes/{route_id}` | manufacturing.manage + manufacturing.delete | N/A | **ADD** |

### Production Orders

| Method | Path | Permission | Pagination | Branch Filter |
|--------|------|------------|------------|--------------|
| GET | `/manufacturing/orders` | manufacturing.view | **ADD** | ✅ (existing) |
| POST | `/manufacturing/orders` | manufacturing.manage + manufacturing.create | N/A | **ADD** |
| GET | `/manufacturing/orders/{id}` | manufacturing.view | N/A | **ADD** |
| PUT | `/manufacturing/orders/{id}` | manufacturing.manage | N/A | **ADD** |
| DELETE | `/manufacturing/orders/{id}` | manufacturing.manage + manufacturing.delete | N/A | **ADD** |
| POST | `/manufacturing/orders/{id}/start` | manufacturing.manage | N/A | **ADD** |
| POST | `/manufacturing/orders/{id}/complete` | manufacturing.manage | N/A | **ADD** |
| POST | `/manufacturing/orders/{id}/cancel` | manufacturing.manage | N/A | **ADD** |
| POST | `/manufacturing/orders/{id}/calculate-cost` | manufacturing.manage | N/A | **ADD** |

### Operations

| Method | Path | Permission | Pagination | Branch Filter |
|--------|------|------------|------------|--------------|
| GET | `/manufacturing/operations` | manufacturing.view | ✅ (existing) | **ADD** |
| POST | `/manufacturing/operations/{id}/start` | manufacturing.manage | N/A | **ADD** |
| POST | `/manufacturing/operations/{id}/complete` | manufacturing.manage | N/A | **ADD** |
| POST | `/manufacturing/operations/{id}/pause` | manufacturing.manage | N/A | **ADD** |

### MRP

| Method | Path | Permission | Pagination | Branch Filter |
|--------|------|------------|------------|--------------|
| GET | `/manufacturing/mrp/calculate/{order_id}` | manufacturing.manage | N/A | **ADD** |
| GET | `/manufacturing/mrp/plans` | manufacturing.view | **ADD** | **ADD** |

### Equipment & Maintenance

| Method | Path | Permission | Pagination | Branch Filter |
|--------|------|------------|------------|--------------|
| GET | `/manufacturing/equipment` | manufacturing.view | **ADD** | **ADD** |
| POST | `/manufacturing/equipment` | manufacturing.manage + manufacturing.create | N/A | **ADD** |
| PUT | `/manufacturing/equipment/{id}` | manufacturing.manage | N/A | **ADD** |
| DELETE | `/manufacturing/equipment/{id}` | manufacturing.manage + manufacturing.delete | N/A | **ADD** |
| GET | `/manufacturing/maintenance-logs` | manufacturing.view | **ADD** | **ADD** |
| POST | `/manufacturing/maintenance-logs` | manufacturing.manage | N/A | **ADD** |

### QC Checks

| Method | Path | Permission | Pagination | Branch Filter |
|--------|------|------------|------------|--------------|
| GET | `/manufacturing/orders/{id}/qc-checks` | manufacturing.view | N/A | **ADD** |
| POST | `/manufacturing/orders/{id}/qc-checks` | manufacturing.manage | N/A | **ADD** |
| POST | `/manufacturing/qc-checks/{id}/record-result` | manufacturing.manage | N/A | **ADD** |

### Reports

| Method | Path | Permission | Pagination | Branch Filter |
|--------|------|------------|------------|--------------|
| GET | `/manufacturing/reports/direct-labor` | manufacturing.view | N/A | **ADD** |
| GET | `/manufacturing/reports/production-cost` | manufacturing.view | N/A | **ADD** |
| GET | `/manufacturing/reports/work-center-efficiency` | manufacturing.view | N/A | **ADD** |
| GET | `/manufacturing/reports/production-summary` | manufacturing.view | N/A | **ADD** |
| GET | `/manufacturing/reports/material-consumption` | manufacturing.view | N/A | **ADD** |
| GET | `/manufacturing/cost-variance-report` | manufacturing.view | N/A | **ADD** |
| GET | `/manufacturing/oee` | manufacturing.view | N/A | **ADD** |

### Capacity Plans

| Method | Path | Permission | Pagination | Branch Filter |
|--------|------|------------|------------|--------------|
| GET | `/manufacturing/capacity-plans` | manufacturing.view | N/A | **ADD** |
| POST | `/manufacturing/capacity-plans` | manufacturing.manage | N/A | **ADD** |
| PUT | `/manufacturing/capacity-plans/{id}` | manufacturing.manage | N/A | **ADD** |

### Shop Floor (Separate Router)

| Method | Path | Permission | Branch Filter |
|--------|------|------------|--------------|
| GET | `/manufacturing/shopfloor/dashboard` | manufacturing.shopfloor_view | **ADD** |
| POST | `/manufacturing/shopfloor/start` | manufacturing.shopfloor_operate | **ADD** |
| POST | `/manufacturing/shopfloor/complete` | manufacturing.shopfloor_operate | **ADD** |
| POST | `/manufacturing/shopfloor/pause` | manufacturing.shopfloor_operate | **ADD** |
| GET | `/manufacturing/shopfloor/work-order/{id}` | manufacturing.shopfloor_view | **ADD** |
| WS | `/manufacturing/shopfloor/ws` | N/A | N/A |

### Routing (Separate Router)

| Method | Path | Permission | Branch Filter |
|--------|------|------------|--------------|
| POST | `/manufacturing/routing` | manufacturing.routing_manage | **ADD** |
| GET | `/manufacturing/routing` | manufacturing.routing_view | **ADD** |
| GET | `/manufacturing/routing/{id}` | manufacturing.routing_view | **ADD** |
| PUT | `/manufacturing/routing/{id}` | manufacturing.routing_manage | **ADD** |
| GET | `/manufacturing/routing/product/{id}` | manufacturing.routing_view | **ADD** |
| GET | `/manufacturing/routing/{id}/estimate` | manufacturing.routing_view | N/A |

## Additive Changes Summary

1. **Pagination** (6 endpoints): Add optional `offset` (default 0) and `limit` (default 25, max 100) query parameters
2. **Branch validation**: Add `branch_id` filtering transparently — no change to response format
3. **Decimal serialization**: Float values will serialize as strings in JSON — backward compatible for frontend (already uses string parsing)
