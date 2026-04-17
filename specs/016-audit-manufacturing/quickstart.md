# Quickstart: Audit Manufacturing Module

**Feature**: 016-audit-manufacturing  
**Date**: 2026-04-16

## Prerequisites

- Python 3.12+ with virtual environment activated
- PostgreSQL 15 running with tenant database(s)
- Node.js 18+ for frontend
- Redis running (for rate limiting)

## Setup

```bash
# Backend
cd /home/omar/Desktop/aman
source .venv/bin/activate
cd backend

# Frontend
cd /home/omar/Desktop/aman/frontend
npm install
```

## Running the Application

```bash
# From project root
./start-local.sh
```

## Key Files to Audit (by priority)

### Priority 1 — Financial Precision (float → Decimal)

```bash
# Schema file (20+ float fields)
backend/schemas/manufacturing_advanced.py

# Router files (float() calls)
backend/routers/manufacturing/core.py        # calculate_production_cost(), cost calculations
backend/routers/manufacturing/routing.py     # quantity parameter
backend/routers/manufacturing/shopfloor.py   # cycle_time/quantity conversions
```

### Priority 2 — SoftDeleteMixin (9 models)

```bash
# Model files needing SoftDeleteMixin
backend/models/domain_models/manufacturing_bom_capacity.py   # BillOfMaterial, BomComponent, BomOutput, CapacityPlan
backend/models/domain_models/manufacturing_execution.py      # ManufacturingEquipment, ManufacturingOperation, ManufacturingRoute, MfgQcCheck
backend/models/domain_models/manufacturing_resources.py      # WorkCenter
```

### Priority 3 — Branch Validation & Pagination

```bash
# All in core.py — 16 endpoints missing branch validation, 6 missing pagination
backend/routers/manufacturing/core.py
```

### Priority 4 — Frontend console.error → toast

```bash
# 22 instances across 15 files
frontend/src/pages/Manufacturing/*.jsx    # 20 instances
frontend/src/pages/ShopFloor/*.jsx        # 2 instances
```

## Testing

```bash
# Backend tests
cd backend && python -m pytest tests/ -v

# Frontend tests
cd frontend && npm test

# Lint
cd backend && ruff check .
```

## Verification Checklist

1. All `float` fields in `manufacturing_advanced.py` → `Decimal`
2. All `float()` calls in routers → `Decimal(str(value))`
3. All 9 models inherit `SoftDeleteMixin`
4. Migration adds `is_deleted` column to 9 tables
5. All queries filter `is_deleted = false`
6. DELETE operations → `UPDATE SET is_deleted = true`
7. 16+ endpoints have `validate_branch_access()`
8. 6 list endpoints have `LIMIT/OFFSET` pagination
9. Error messages sanitized (no internal state in HTTPException details)
10. 22 `console.error` → `toast.error()` in frontend
