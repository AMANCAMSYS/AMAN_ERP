# Data Model: Audit HR Module — تدقيق وحدة الموارد البشرية

**Feature**: 015-audit-hr  
**Date**: 2026-04-15

---

## Overview

This audit does **not** add new tables or columns. It fixes field types and enforcement patterns on existing entities. The data model below documents the **changes** to existing schemas and models.

---

## Schema Changes: `backend/schemas/hr.py`

### LoanCreate / LoanResponse

| Field | Before | After |
|-------|--------|-------|
| `amount` | `float` | `Decimal` |
| `monthly_installment` | `float` | `Decimal` |
| `paid_amount` | `float` | `Decimal` |

### EmployeeCreate / EmployeeUpdate

| Field | Before | After |
|-------|--------|-------|
| `salary` | `float = 0` | `Decimal = Decimal("0")` |
| `housing_allowance` | `float = 0` | `Decimal = Decimal("0")` |
| `transport_allowance` | `float = 0` | `Decimal = Decimal("0")` |
| `other_allowances` | `float = 0` | `Decimal = Decimal("0")` |
| `hourly_cost` | `float = 0` | `Decimal = Decimal("0")` |

### EmployeeResponse

| Field | Before | After |
|-------|--------|-------|
| `hourly_cost` | `float` | `Decimal` |

### PayrollEntryResponse

| Field | Before | After |
|-------|--------|-------|
| `basic_salary` | `float` | `Decimal` |
| `housing_allowance` | `float` | `Decimal` |
| `transport_allowance` | `float` | `Decimal` |
| `other_allowances` | `float` | `Decimal` |
| `deductions` | `float` | `Decimal` |
| `net_salary` | `float` | `Decimal` |
| `exchange_rate` | `float` | `Decimal` |
| `net_salary_base` | `float` | `Decimal` |
| `gosi_employee_share` | `float` | `Decimal` |
| `gosi_employer_share` | `float` | `Decimal` |
| `overtime_amount` | `float` | `Decimal` |
| `violation_deduction` | `float` | `Decimal` |
| `loan_deduction` | `float` | `Decimal` |
| `salary_components_earning` | `float` | `Decimal` |
| `salary_components_deduction` | `float` | `Decimal` |

### PayrollPeriodResponse

| Field | Before | After |
|-------|--------|-------|
| `total_net` | `float` | `Decimal` |

**Total**: 31 fields migrated from `float` to `Decimal`

---

## Utility Changes: `backend/utils/hr_helpers.py`

### `calculate_eos_gratuity()` Signature

| Parameter | Before | After |
|-----------|--------|-------|
| `total_salary` | `float` | `Decimal` |
| `total_years` | `float` | `Decimal` |
| Return dict values | `float` | `Decimal` |

---

## New Utility: `backend/utils/masking.py`

### `mask_pii(value, visible_chars=4) -> str`

| Input | Output |
|-------|--------|
| `"SA1234567890123456"` | `"**************3456"` |
| `"1234567890"` | `"******7890"` |
| `None` | `None` |
| `"123"` (shorter than visible_chars) | `"123"` (no masking) |

### New Permission: `hr.pii`

- Added to `PERMISSION_ALIASES` in `backend/utils/permissions.py`
- Granted to roles: `admin`, `system_admin`, `manager`, `hr_admin`, `payroll_manager`
- Required by: WPS export (needs real IBAN), employee detail view (full PII)

### PII Fields Subject to Masking

| Field | Mask When | Source |
|-------|-----------|--------|
| `iban` / `bank_account` | User lacks `hr.pii` | Employee record |
| `social_security` / `national_id` | User lacks `hr.pii` | Employee record |
| `gosi_number` | User lacks `hr.pii` | Employee record |
| `passport_number` | User lacks `hr.pii` | Employee record |
| `iqama_number` | User lacks `hr.pii` | Employee record |

---

## Model Verification: `backend/models/domains/hr.py`

All HR models must inherit `AuditMixin` and (where applicable) `SoftDeleteMixin`:

| Model | AuditMixin | SoftDeleteMixin | Notes |
|-------|-----------|----------------|-------|
| `Employee` | Verify | Verify | Core entity — both required |
| `Department` | Verify | Verify | Organizational unit |
| `EmployeePosition` | Verify | Verify | Position definitions |
| `PayrollPeriod` | Verify | N/A | Append-only (draft→calculated→locked) |
| `PayrollEntry` | Verify | N/A | Tied to period lifecycle |
| `LeaveRequest` | Verify | Verify | Status-tracked |
| `LeaveCarryover` | Verify | N/A | Periodic record |
| `EmployeeLoan` | Verify | Verify | Active/completed lifecycle |
| `Attendance` | Verify | N/A | Append-only daily records |
| `OvertimeRequest` | Verify | Verify | Approval workflow |
| `SalaryStructure` | Verify | Verify | Template entity |
| `SalaryComponent` | Verify | Verify | Template component |
| `EmployeeSalaryComponent` | Verify | N/A | Junction table |
| `PerformanceReview` | Verify | N/A | Status-tracked |
| `EmployeeDocument` | Verify | Verify | Document lifecycle |
| `EmployeeViolation` | Verify | Verify | Disciplinary record |
| `EmployeeCustody` | Verify | Verify | Asset tracking |
| `TrainingProgram` | Verify | Verify | Program lifecycle |
| `TrainingParticipant` | Verify | N/A | Junction table |
| `JobOpening` | Verify | Verify | Recruitment lifecycle |
| `JobApplication` | Verify | Verify | Application pipeline |

---

## Router Serialization Changes: `backend/routers/hr/core.py`

All `float(row.xxx)` calls in response construction replaced with `str(row.xxx or 0)`:

| Line Range | Before Pattern | After Pattern |
|-----------|----------------|---------------|
| 606-614 | `float(row.exchange_rate)` | `str(row.exchange_rate or 0)` |
| 875-878 | `float(basic)`, `float(housing)`, etc. | `str(basic or 0)`, `str(housing or 0)`, etc. |

---

## Frontend Change Inventory

### Files requiring `formatNumber()` import addition

| File | Current Pattern | Replacement |
|------|----------------|-------------|
| `HR/Violations.jsx` | `v.deduction_amount?.toLocaleString()` | `formatNumber(v.deduction_amount)` |
| `HR/EOSSettlement.jsx` | `Number(result.xxx).toLocaleString()` × 5 | `formatNumber(result.xxx)` |
| `HR/GOSISettings.jsx` | `c.basic_salary?.toLocaleString()` × 4 | `formatNumber(c.basic_salary)` |
| `HR/WPSExport.jsx` | `Number(e.xxx).toLocaleString()` × 4 | `formatNumber(e.xxx)` |
| `HR/HRHome.jsx` | `(eosResult.xxx).toLocaleString()` × 2 | `formatNumber(eosResult.xxx)` |
| `HR/Employees.jsx` | salary `.toLocaleString()` × 2 | `formatNumber(salary)` |
| `HR/SalaryStructures.jsx` | `c.default_amount?.toLocaleString()` | `formatNumber(c.default_amount)` |
| `SelfService/EmployeeDashboard.jsx` | `Number(ps.net_salary).toLocaleString()` | `formatNumber(ps.net_salary)` |
| `SelfService/PayslipList.jsx` | `Number(ps.xxx).toLocaleString()` × 3 | `formatNumber(ps.xxx)` |
| `SelfService/PayslipDetail.jsx` | `const fmt = (v) => Number(v).toLocaleString()` | `const fmt = formatNumber` |
| `TimeTracking/ProjectProfitability.jsx` | `d.revenue.toLocaleString(...)` × 3 | `formatNumber(d.revenue)` |

### Files requiring `console.error` → `toastEmitter` conversion

**37 total replacements** across:
- HR/ (21 instances in 11 files)
- SelfService/ (5 instances in 5 files)
- Performance/ (6 instances in 6 files)
- TimeTracking/ (5 instances in 3 files)
