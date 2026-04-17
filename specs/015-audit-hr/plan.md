# Implementation Plan: Audit HR Module — تدقيق وحدة الموارد البشرية

**Branch**: `015-audit-hr` | **Date**: 2026-04-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/015-audit-hr/spec.md`

## Summary

Audit and fix the HR module across backend schemas, routers, utilities, and 46+ frontend pages to enforce financial precision (Decimal instead of float), consistent formatting (formatNumber), user-visible error handling (toastEmitter), branch access validation, PII masking, and audit trail completeness. Addresses 31 float schema fields, 18+ float() router calls, 37 console.error instances, and 28 toLocaleString() calls.

## Technical Context

**Language/Version**: Python 3.12 (backend), React 18 / Vite (frontend)  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 (SQL-first via `text()`), Pydantic, i18next, React Router  
**Storage**: PostgreSQL 15 (multi-tenant `aman_{company_id}` + system `aman_system`)  
**Testing**: pytest (backend), Vitest (frontend)  
**Target Platform**: Linux server (Docker + Nginx)  
**Project Type**: Web application (ERP)  
**Performance Goals**: N/A — this is an audit/fix spec, not new functionality  
**Constraints**: Zero breaking changes to existing API contracts; Decimal serialization as strings preserves backward compatibility  
**Scale/Scope**: 5 backend router files, 2 schema files, 1 utility file, 1 model file, 46+ frontend pages across HR/, SelfService/, Performance/, TimeTracking/

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Rule | Status | Notes |
|---|---|---|
| I. Financial Precision ⛔ | **VIOLATION → FIX** | `backend/schemas/hr.py` uses `float` for 31 monetary fields; `hr_helpers.py` accepts/returns `float`; 18+ `float()` calls in routers. This audit fixes all. |
| II. Multi-Tenant Isolation ⛔ | ✅ PASS | HR uses `get_db_connection(company_id)` throughout |
| III. Double-Entry Integrity ⛔ | ✅ PASS | Payroll GL posting via `gl_service.py` (out of scope — covered by 006-audit-accounting) |
| IV. Security & Access Control ⛔ | **VIOLATION → FIX** | Performance, saudization, WPS endpoints missing `validate_branch_access()`. PII fields exposed without role filtering. |
| V. Regulatory Compliance — Saudi ⛔ | **VIOLATION → FIX** | GOSI/WPS monetary values use `float` → Decimal fix required; EOS calculation loses precision at boundary |
| VII. Simplicity & Maintainability | ✅ PASS | SQL-first pattern maintained |
| XI. HR & Payroll Compliance | ✅ PASS | Salary formula, payroll status machine, leave/EOS rules already implemented correctly in logic |
| XVII. Observability & Audit Trail | **VIOLATION → FIX** | Some HR write operations missing `log_activity()` calls; `AuditMixin` inheritance needs verification |
| XIX. Calculation Centralization ⛔ | ✅ PASS | No duplicated calculation logic detected |
| XXII. Transaction Validation Pipeline | ✅ PASS | HR endpoints follow Pydantic → permission → business rules → persist flow |
| XXVI. Calculation Traceability | ✅ PASS | Payroll stores per-employee breakdown (basic, allowances, deductions, GOSI shares, net) |
| XXVII. UI/UX Behavioral Consistency ⛔ | **VIOLATION → FIX** | 37 console.error (should be toast); mixed toast patterns; 28 raw toLocaleString (should be formatNumber) |
| XXVIII. Schema Definition Synchronization ⛔ | N/A | No new tables/columns being added (audit fixes existing code) |

## Project Structure

### Documentation (this feature)

```text
specs/015-audit-hr/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (files to modify)

```text
backend/
├── schemas/
│   └── hr.py                        # 31 float → Decimal conversions
├── routers/
│   └── hr/
│       ├── core.py                  # 18+ float() → str() + branch validation + log_activity gaps
│       ├── advanced.py              # EOS float return + branch validation
│       ├── performance.py           # Branch validation gaps
│       └── self_service.py          # Minor fixes
│   └── hr_wps_compliance.py         # float → Decimal + branch validation
├── utils/
│   └── hr_helpers.py                # float → Decimal in calculate_eos_gratuity()
└── models/
    └── domains/
        └── hr.py                    # Verify AuditMixin + SoftDeleteMixin inheritance

frontend/src/
├── pages/
│   ├── HR/                          # 26 pages — console.error → toast, toLocaleString → formatNumber
│   │   ├── Employees.jsx            # 4 console.error, 2 toLocaleString
│   │   ├── PayrollList.jsx          # 1 console.error
│   │   ├── EOSSettlement.jsx        # 5 toLocaleString
│   │   ├── GOSISettings.jsx         # 4 toLocaleString
│   │   ├── WPSExport.jsx            # 4 toLocaleString
│   │   ├── HRHome.jsx               # 2 toLocaleString
│   │   ├── Violations.jsx           # 2 console.error, 1 toLocaleString
│   │   ├── SalaryStructures.jsx     # 1 toLocaleString
│   │   └── [18 more pages]          # console.error fixes
│   ├── SelfService/                 # 6 pages — 5 console.error, 6 toLocaleString
│   ├── Performance/                 # 7 pages — 6 console.error
│   └── TimeTracking/               # 3 pages — 5 console.error, 3 toLocaleString
└── Settings/tabs/
    └── HRSettings.jsx               # No issues (clean)
```

**Structure Decision**: This is an audit-fix affecting existing files only — no new files, directories, or modules are created.

## Complexity Tracking

No constitution violations requiring justification — all violations are being **fixed** (not justified) by this audit.
