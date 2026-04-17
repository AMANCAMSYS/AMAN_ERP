# Feature Specification: Audit HR Module — تدقيق وحدة الموارد البشرية

**Feature Branch**: `015-audit-hr`  
**Created**: 2026-04-15  
**Status**: Draft  
**Input**: User description: "audit-hr — الموارد البشرية. لاتنسى ان تجعل كل شيء مرتبط بالفرونت اند بالشكل الصحيح"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Numeric Precision Across All HR/Payroll Endpoints (Priority: P1) 🎯 MVP

An auditor reviewing payroll data must see exact monetary values (e.g., "5000.00") rather than floating-point approximations (e.g., "4999.9999999999"). All backend HR endpoints must serialize monetary fields using `str()` instead of `float()`, and all Pydantic schemas in `backend/schemas/hr.py` must use `Decimal` instead of `float` for salary, allowance, deduction, loan, and all monetary/rate fields. The advanced schemas (`hr_advanced.py`) already use `Decimal` correctly — the core schemas must be brought to the same standard.

**Why this priority**: Payroll involves real money flowing to employees. Floating-point errors in salary calculations, GOSI contributions, or EOS gratuity directly affect employees' income and the company's legal compliance. This is the most fundamental audit deficiency.

**Independent Test**: `grep -rn ": float" backend/schemas/hr.py | wc -l` → 0; all monetary values in API responses return string-serialized decimals.

**Acceptance Scenarios**:

1. **Given** an employee with salary 5000.75 and housing allowance 1500.25, **When** the employee details endpoint returns the employee, **Then** `salary` is `"5000.75"` (not `5000.75000000001`)
2. **Given** a payroll entry with basic_salary 8000, housing 3000, deductions 975, **When** the payroll entry is retrieved, **Then** `net_salary` is `"10025.00"`, not a floating-point approximation
3. **Given** `EmployeeCreate` schema receives `salary: "7500.50"`, **When** Pydantic parses it, **Then** it stores as `Decimal("7500.50")`, not `float(7500.5)`
4. **Given** a loan with amount 10000 and monthly_installment 833.33, **When** the loan record is retrieved, **Then** both values are string-serialized Decimals

---

### User Story 2 — Frontend Uses formatNumber() for All Monetary Display (Priority: P1)

All HR, SelfService, Performance, and TimeTracking frontend pages must use the centralized `formatNumber()` utility for displaying monetary values (salaries, deductions, allowances, GOSI contributions, loan amounts, EOS gratuity). Raw `.toLocaleString()` and `.toFixed()` bypass the company's configured decimal precision and must be replaced.

**Why this priority**: Inconsistent number formatting creates confusion in payroll reports, payslips, and GOSI exports. The `formatNumber()` utility already respects company-specific decimal places — using `.toLocaleString()` bypasses this, showing different precision on different pages.

**Independent Test**: `grep -rn "toLocaleString\|\.toFixed" frontend/src/pages/HR/ frontend/src/pages/SelfService/ frontend/src/pages/Performance/ frontend/src/pages/TimeTracking/ | grep -v "date\|Date\|time\|Time" | wc -l` → 0 for monetary values

**Acceptance Scenarios**:

1. **Given** a company configured with 3 decimal places, **When** GOSISettings displays an employee's basic_salary of 8000, **Then** it shows "8,000.000" (3 decimals via `formatNumber()`), not "8,000" (browser default `.toLocaleString()`)
2. **Given** WPSExport displays salary/allowance columns, **When** the preview table renders, **Then** all amounts use `formatNumber()` instead of `Number(val).toLocaleString()`
3. **Given** Violations page displays a deduction_amount, **When** the table renders, **Then** it uses `formatNumber(v.deduction_amount)` instead of `v.deduction_amount?.toLocaleString()`
4. **Given** SelfService EmployeeDashboard shows payslip amounts, **When** the recent payslips table renders, **Then** all amounts use `formatNumber()`

---

### User Story 3 — User-Visible Error Handling via Toast Notifications (Priority: P1)

When an HR operation fails (employee fetch, payroll generation, leave request, GOSI export, document upload), the user sees a clear toast notification instead of the error being silently logged to `console.error`. All `console.error` calls in HR-related frontend files must be replaced with toast notifications. Leftover `console.log` debug statements must also be removed.

**Why this priority**: In HR operations, silent failures can result in unpaid employees, missing GOSI submissions, or unprocessed leave requests. HR staff and employees need immediate visual feedback when something goes wrong.

**Independent Test**: `grep -rn "console\.error\|console\.log" frontend/src/pages/HR/ frontend/src/pages/SelfService/ frontend/src/pages/Performance/ frontend/src/pages/TimeTracking/ | wc -l` → 0

**Acceptance Scenarios**:

1. **Given** a network error occurs during employee list fetch in Employees.jsx, **When** the API call fails, **Then** the HR user sees a toast notification with an error message (not silent `console.error`)
2. **Given** payroll generation fails in PayrollList.jsx, **When** the error is caught, **Then** a toast is shown (not only `console.error(err)`)
3. **Given** GOSI settings save fails in GOSISettings.jsx, **When** the 3 `console.error(e)` instances trigger, **Then** each shows a toast notification instead
4. **Given** document upload fails in EmployeeDocuments.jsx, **When** the error is caught, **Then** a user-visible toast appears

---

### User Story 4 — EOS Gratuity Calculation Precision (Priority: P1)

The `calculate_eos_gratuity()` function in `backend/utils/hr_helpers.py` currently accepts `float` inputs and returns `float` outputs, despite using internal `Decimal` conversion. The function must accept and return `Decimal` values throughout to prevent precision loss in end-of-service settlements, which are legally mandated calculations under Saudi Labor Law Articles 84/85.

**Why this priority**: EOS gratuity is a legal obligation. A rounding error of even 0.01 SAR multiplied across years of service can result in underpayment or overpayment, exposing the company to labor disputes.

**Independent Test**: `grep -n "float" backend/utils/hr_helpers.py | wc -l` → 0 for function signatures

**Acceptance Scenarios**:

1. **Given** an employee with total_salary 15000.75 and 7.5 years of service (resignation), **When** EOS is calculated, **Then** the gratuity is returned as `Decimal` with exact value, not a float approximation
2. **Given** termination_reason is "resignation" and years < 2, **When** EOS is calculated, **Then** gratuity is exactly `Decimal("0")`
3. **Given** an employee with 12 years and salary 20000, **When** EOS is calculated for "end_of_contract", **Then** the result matches: first 5 years (0.5 × 20000 × 5) + remaining 7 years (1 × 20000 × 7) = `Decimal("190000.00")`

---

### User Story 5 — Frontend Sends Correct Data Types to Backend (Priority: P1)

HR frontend pages that submit monetary values (employee creation, loan creation, payroll adjustments, overtime requests, GOSI settings) must send numeric values as strings in API payloads to ensure the backend receives exact values parseable into `Decimal`. Pages that use `parseFloat()` for form input parsing should convert to `String()` before API submission.

**Why this priority**: If the frontend sends `parseFloat("8333.33")` = `8333.329999...`, the backend stores an incorrect salary or loan installment. This directly affects payroll accuracy.

**Independent Test**: All API payloads from HR pages send monetary values as string types.

**Acceptance Scenarios**:

1. **Given** an HR user creates an employee with salary 7500.50, **When** the form submits, **Then** the API payload contains `salary: "7500.50"` (string), not `salary: 7500.5` (float)
2. **Given** GOSI settings are saved with max_contributable_salary 45000, **When** the form submits, **Then** the value is sent as `"45000"` (string)
3. **Given** a loan is created with amount 10000 and monthly_installment 833.33, **When** the form submits, **Then** both values are sent as strings

---

### User Story 6 — Consistent Toast Notification System (Priority: P2)

HR frontend pages use a mix of notification approaches: some use `toast.success()`/`toast.error()` from react-hot-toast directly, some use `toastEmitter.emit()`, and some use neither. All HR pages must use a single consistent notification pattern as established in the project conventions.

**Why this priority**: Inconsistent notification patterns create maintenance burden and inconsistent UX. HR employees see different notification styles on different pages, which degrades trust in the system.

**Independent Test**: All HR pages use the same toast pattern; no mixed `toast()` + `toastEmitter` usage in the same file.

**Acceptance Scenarios**:

1. **Given** a leave is approved in LeaveList.jsx, **When** the approval succeeds, **Then** the success notification uses the same pattern as Employees.jsx
2. **Given** an error occurs in any HR page, **When** the catch block executes, **Then** it uses the project-standard toast pattern (not `toast.error()` in one page and `toastEmitter.emit()` in another)

---

### User Story 7 — Branch Access Validation on All HR Endpoints (Priority: P2)

Several HR backend endpoints (performance reviews, saudization dashboard, WPS export) and frontend pages do not explicitly validate branch access. All HR endpoints that handle branch-scoped data must call `validate_branch_access()`, and all frontend pages must pass `branch_id` from the `useBranch()` context to API calls.

**Why this priority**: Without branch validation, a user assigned to Branch A could potentially view or modify HR data (employees, payroll, leave requests) belonging to Branch B. This is a data isolation violation in a multi-branch environment.

**Independent Test**: All HR router endpoints include `validate_branch_access()` calls; all frontend HR pages pass `branch_id` in API requests.

**Acceptance Scenarios**:

1. **Given** a performance review cycle, **When** the cycle is launched, **Then** only employees in the user's authorized branch(es) receive reviews
2. **Given** the saudization dashboard is accessed, **When** the API returns data, **Then** it is filtered by the user's branch access permissions
3. **Given** a user without Branch B access, **When** they attempt to view Branch B's WPS export, **Then** the request is rejected with a 403 error

---

### User Story 8 — Audit Trail Columns on All HR Tables (Priority: P2)

All HR domain models must include consistent audit columns (`created_at`, `updated_at`, `created_by`, `updated_by`). The `log_activity()` calls in HR routers must capture all create/update/delete operations across employees, payroll, leaves, loans, overtime, GOSI, documents, training, performance reviews, violations, and custody.

**Why this priority**: Without complete audit trails, there is no way to trace who modified an employee's salary, who approved a leave request, or who generated a payroll batch. This is a compliance requirement for HR systems handling financial data.

**Independent Test**: All HR models inherit `AuditMixin`; `log_activity()` is called for all write operations.

**Acceptance Scenarios**:

1. **Given** an employee's salary is updated by user "hr_admin", **When** the update completes, **Then** `updated_by` = "hr_admin" and `updated_at` is set
2. **Given** a payroll period is posted, **When** the posting completes, **Then** an audit log entry records who posted it and when
3. **Given** a leave request is approved, **When** the approval completes, **Then** the approval action is logged with the approver's identity

---

### User Story 9 — GOSI/WPS Monetary Formatting Compliance (Priority: P2)

GOSI contribution displays and WPS export previews must use exact decimal formatting. Currently GOSISettings.jsx uses `.toLocaleString()` and `.toFixed(2)` for GOSI calculations, and WPSExport.jsx uses `Number(val).toLocaleString()` for salary columns. These must be replaced with `formatNumber()` for display and string-serialized Decimals for export data.

**Why this priority**: GOSI submissions and WPS bank files are regulatory documents. Incorrect formatting or rounding in these files can cause bank rejections or GOSI compliance violations.

**Independent Test**: No `.toLocaleString()` or `.toFixed()` for monetary values in GOSISettings.jsx or WPSExport.jsx.

**Acceptance Scenarios**:

1. **Given** GOSI calculation shows employee share of 975.75, **When** the table renders, **Then** it displays via `formatNumber(975.75)` not `(975.75).toLocaleString()`
2. **Given** WPS preview shows basic_salary 8000.50, **When** the preview table renders, **Then** it uses `formatNumber(8000.50)` not `Number("8000.50").toLocaleString()`

---

### User Story 10 — Self-Service Portal Data Formatting (Priority: P3)

The Employee Self-Service portal (EmployeeDashboard, PayslipList, PayslipDetail, LeaveRequestForm) must consistently use `formatNumber()` for all monetary displays. Currently, EmployeeDashboard uses `.toLocaleString()` for payslip amounts.

**Why this priority**: Employees rely on the self-service portal to verify their pay, leave balances, and payslip details. Inconsistent formatting reduces trust in the system's accuracy.

**Independent Test**: No `.toLocaleString()` for monetary values in frontend/src/pages/SelfService/.

**Acceptance Scenarios**:

1. **Given** an employee views recent payslips on EmployeeDashboard, **When** the payslip table renders, **Then** net_salary uses `formatNumber()` instead of `.toLocaleString()`
2. **Given** an employee views PayslipDetail, **When** the detailed breakdown renders, **Then** all amounts (basic, allowances, deductions, net) use `formatNumber()`

---

### Edge Cases

- What happens when an employee has zero salary (unpaid internship) — does payroll generation handle `Decimal("0")` correctly?
- How does EOS calculation handle an employee with exactly 2 years or exactly 5 years of service (boundary conditions)?
- What happens when WPS export is attempted for a non-Saudi company (country_code ≠ 'SA')?
- How does the system handle leave carryover when the employee has a negative leave balance (taken more than entitled)?
- What happens when GOSI settings are updated mid-payroll-period — does the current period use old or new rates?
- How does the system handle overtime calculation when an employee has no defined hourly rate?
- What happens when a performance review cycle is launched but no active employees exist in the branch?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST use `Decimal` type for all monetary fields in HR core schemas (`backend/schemas/hr.py`): salary, housing_allowance, transport_allowance, other_allowances, hourly_cost, basic_salary, deductions, net_salary, loan amount, monthly_installment
- **FR-002**: System MUST serialize all monetary values in HR API responses using `str()` instead of `float()` to preserve precision
- **FR-003**: `calculate_eos_gratuity()` in `backend/utils/hr_helpers.py` MUST accept `Decimal` inputs and return `Decimal` outputs (no `float` at boundaries)
- **FR-004**: All HR frontend pages (HR/, SelfService/, Performance/, TimeTracking/) MUST use `formatNumber()` for displaying monetary values instead of `.toLocaleString()` or `.toFixed()`
- **FR-005**: All HR frontend pages MUST replace `console.error()` with toast notifications for user-visible error handling
- **FR-006**: All HR frontend pages MUST remove `console.log()` debug statements from production code
- **FR-007**: All HR frontend pages MUST send monetary values as strings (not floats) in API payloads
- **FR-008**: All HR backend router endpoints MUST validate branch access using `validate_branch_access()` for branch-scoped data
- **FR-009**: All HR domain models MUST include audit columns (`created_at`, `updated_at`, `created_by`, `updated_by`)
- **FR-010**: All HR write operations (create/update/delete) MUST call `log_activity()` for audit logging
- **FR-011**: All HR frontend pages MUST use a single consistent toast notification pattern (no mixed `toast()` and `toastEmitter` patterns)
- **FR-012**: GOSISettings.jsx MUST replace all `.toLocaleString()` and `.toFixed(2)` calls with `formatNumber()` for monetary display
- **FR-013**: WPSExport.jsx MUST replace all `Number(val).toLocaleString()` calls with `formatNumber()` for monetary display
- **FR-014**: Violations.jsx MUST replace `v.deduction_amount?.toLocaleString()` with `formatNumber(v.deduction_amount)`
- **FR-015**: SelfService EmployeeDashboard.jsx MUST replace `.toLocaleString()` for payslip amounts with `formatNumber()`
- **FR-016**: Performance review endpoints MUST include explicit branch validation to prevent cross-branch data access
- **FR-017**: Saudization dashboard endpoint MUST validate branch access before returning Nitaqat metrics
- **FR-018**: HR API endpoints MUST mask sensitive PII fields (IBAN, national ID, GOSI number) in responses for roles without explicit PII access permission — full values visible only to roles with HR-admin or payroll-manager level access

### Key Entities

- **Employee**: Core entity — salary, allowances, department, position, branch assignment, documents, custody items. Monetary fields must be Decimal. Sensitive PII fields (national_id, iban, gosi_number) must be masked in API responses for non-privileged roles.
- **PayrollPeriod / PayrollEntry**: Batch payroll processing — basic salary, allowances, deductions, net salary. All monetary fields must be Decimal. Links to GL via journal entries.
- **LeaveRequest / LeaveCarryover**: Leave management — balance tracking, overlap detection, carryover rules. Connected to approval workflows.
- **EmployeeLoan**: Loan tracking — amount, monthly installment, remaining balance. Deducted from payroll. Monetary fields must be Decimal.
- **OvertimeRequest**: Overtime tracking — hours, multiplier, calculated amount. Connected to approval workflows and payroll.
- **SalaryStructure / SalaryComponent / EmployeeSalaryComponent**: Salary template system — component percentages and fixed amounts. Advanced schemas already use Decimal correctly.
- **PerformanceReview**: Goal-based review cycles — self-assessment and manager assessment with Decimal ratings.
- **EmployeeDocument**: Document management — expiry tracking, alerts.
- **EmployeeViolation**: Disciplinary tracking — violation type, deduction amount. Monetary field must be Decimal.
- **EmployeeCustody**: Asset custody — items assigned to employees.
- **TrainingProgram / TrainingParticipant**: Training management — programs, enrollment, completion tracking.
- **JobOpening / JobApplication**: Recruitment pipeline — openings, applications, status tracking.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero floating-point monetary values appear in any HR API response — all monetary fields are string-serialized Decimals
- **SC-002**: All HR frontend pages use `formatNumber()` for monetary display — zero instances of `.toLocaleString()` or `.toFixed()` on monetary values
- **SC-003**: Zero `console.error` or `console.log` statements remain in HR/SelfService/Performance/TimeTracking frontend pages
- **SC-004**: 100% of HR write operations (employee CRUD, payroll, leaves, loans, overtime, GOSI, documents, training, performance, violations, custody) produce audit log entries
- **SC-005**: 100% of branch-scoped HR endpoints validate branch access — no cross-branch data leakage possible
- **SC-006**: EOS gratuity calculations produce identical results to manual calculation per Saudi Labor Law Articles 84/85 for all service duration brackets (0-2y, 2-5y, 5-10y, 10+y) and all termination reasons
- **SC-007**: All HR frontend pages use a single consistent toast notification pattern
- **SC-008**: WPS export preview and GOSI calculation displays use `formatNumber()` — regulatory data shows consistent precision
- **SC-009**: All HR Pydantic schemas use `Decimal` for monetary fields — zero `float` type annotations for monetary/rate fields in `backend/schemas/hr.py`
- **SC-010**: Sensitive PII fields (IBAN, national ID, GOSI number) are masked in API responses for roles without explicit PII access — only last 4 characters visible

## Clarifications

### Session 2026-04-15

- Q: Should payroll batch processing enforce timeout/chunking for large employee counts? → A: No batch performance requirement needed — defer to planning phase if scaling issues arise.
- Q: Should the audit add PII masking for sensitive employee fields (IBAN, national ID, salary, GOSI number) based on caller role? → A: Yes — API MUST mask sensitive fields for roles without explicit PII access permission.
- Q: Should this audit verify GL account mappings for payroll posting, or is that covered by the accounting audit? → A: GL account mapping validation is out of scope — already covered by accounting audit (006). This audit only verifies Decimal precision in GL service calls.

## Assumptions

- Payroll batch performance is not a spec-level concern — the current synchronous approach is sufficient for typical SME branch sizes; optimization deferred to planning if scaling issues arise
- The project uses `formatNumber()` from a shared utility as the standard for number formatting — this is already used in PayrollList.jsx, PayrollDetails.jsx, and LoanList.jsx
- The project's standard toast pattern (either `useToast` hook or `toastEmitter.emit()`) is already established in other modules — HR pages will adopt whichever is the current project standard
- `validate_branch_access()` is an existing utility already used in `routers/hr/core.py` — it just needs to be added to endpoints that currently lack it
- `AuditMixin` is an existing model mixin already used in other modules — HR models will adopt the same pattern
- `log_activity()` is an existing utility from `utils/audit.py` already called in some HR operations — it just needs to be consistently applied to all write operations
- The advanced schemas (`backend/schemas/hr_advanced.py`) already use `Decimal` correctly and serve as the reference pattern for fixing core schemas
- `gl_service.py` integration for payroll GL posting is already functional — this audit focuses on data precision in GL calls, not GL account mapping logic (covered by 006-audit-accounting)
- Saudi-specific features (WPS, GOSI, Saudization, EOS) are region-locked to Saudi Arabia and will continue to be conditionally displayed
- All i18n translations (`useTranslation()`) are already present in HR pages — no missing translation issues were detected
- Frontend routing for all HR pages already exists and is correctly configured in App.jsx
