# Research: Audit HR Module — تدقيق وحدة الموارد البشرية

**Feature**: 015-audit-hr  
**Date**: 2026-04-15  
**Status**: Complete — all unknowns resolved

---

## Research 1: Decimal Migration Pattern for HR Schemas

**Decision**: Use Pydantic `Decimal` type with default values as `Decimal("0")`, matching the pattern already established in `backend/schemas/hr_advanced.py`, `backend/schemas/pos.py`, and `backend/schemas/intercompany.py`.

**Rationale**: The project has a proven pattern in 3+ modules. HR core schemas are the outlier. The migration is mechanical: replace `float` → `Decimal`, replace `= 0` → `= Decimal("0")`.

**Alternatives considered**:
- Custom `MoneyField` type alias — rejected: adds abstraction without 3+ use cases (Constitution VII)
- `condecimal()` Pydantic type — rejected: project doesn't use it anywhere; inconsistent with existing pattern

**Specifics**:
- 31 float fields in `backend/schemas/hr.py` require conversion
- Import: `from decimal import Decimal`
- Pattern: `salary: Decimal = Decimal("0")` for create schemas; `salary: Decimal` for response schemas
- Response serialization: Pydantic v2 serializes Decimal as string by default — no custom serializer needed

---

## Research 2: Router float() → str() Serialization

**Decision**: Replace all `float(row.xxx)` calls in `backend/routers/hr/core.py` with `str(row.xxx)` for monetary fields in response dict construction. Keep Decimal arithmetic where calculations occur.

**Rationale**: The router currently converts DB Decimal values to float for JSON serialization. Replacing with `str()` produces exact string representations. The frontend already parses these as display values via `formatNumber()`.

**Alternatives considered**:
- Return Decimal directly and let FastAPI serialize — works with Pydantic response models but the HR router constructs dicts manually via SQL. `str()` is safer and explicit.
- Use Pydantic response models for all endpoints — ideal but would require significant refactoring beyond audit scope.

**Specifics**:
- 18+ `float()` calls in `core.py` lines 606-878
- Pattern: `"net_salary": str(row.net_salary or 0)` instead of `"net_salary": float(row.net_salary or 0)`
- Loan installment calculation on line 626 should keep Decimal arithmetic, only convert at response boundary

---

## Research 3: EOS Gratuity Decimal Migration

**Decision**: Change `calculate_eos_gratuity()` function signature from `float` to `Decimal` for both inputs and outputs. Internal calculation already uses Decimal — just remove the float boundary conversion.

**Rationale**: The function already does `Decimal(str(total_salary))` internally, which means it loses precision at input (`float` → `str` → `Decimal`). Accepting `Decimal` directly eliminates this.

**Alternatives considered**:
- Accept `Union[float, Decimal]` for backward compatibility — rejected: all callers are in our codebase and can be updated simultaneously

**Specifics**:
- File: `backend/utils/hr_helpers.py`
- Change: `total_salary: float` → `total_salary: Decimal`; `total_years: float` → `total_years: Decimal`
- Return type: `dict` with Decimal values instead of float values
- Callers to update: `routers/hr_wps_compliance.py` (EOS endpoint), `pages/HR/HRHome.jsx` (frontend EOS calculator)

---

## Research 4: PII Masking Strategy

**Decision**: Create a `mask_pii()` utility function in `backend/utils/masking.py` and apply it in HR router responses based on `get_field_restrictions()` from `backend/utils/permissions.py`. Add `hr.pii` permission for full PII access.

**Rationale**: The project already has `DEFAULT_FIELD_RESTRICTIONS` in `permissions.py` that defines restricted fields per role (IBAN, bank_account, gosi_number for 'accountant' and 'user' roles). The framework exists but isn't applied to API responses. Adding a utility function that masks values (show last 4 chars) and calling it in the employee response construction is the minimal-change approach.

**Alternatives considered**:
- Dual Pydantic schemas (`EmployeeResponse` / `EmployeeResponseMasked`) — rejected: doubles schema maintenance; unnecessary since HR router constructs dicts from SQL
- Middleware-level masking — rejected: too broad; masks fields even when full access is needed (e.g., WPS export needs real IBAN)

**Specifics**:
- New file: `backend/utils/masking.py` — single function `mask_pii(value: str, visible_chars: int = 4) -> str`
- New permission: `hr.pii` mapped to `hr.manage` and `hr.payroll` roles
- Fields to mask: `iban`, `national_id`/`social_security`, `gosi_number`, `passport_number`, `iqama_number`
- Mask pattern: `"****1234"` (asterisks + last N chars)
- WPS export endpoint: requires `hr.pii` permission (needs real IBAN for bank file)

---

## Research 5: Toast Pattern Standardization

**Decision**: Use `toastEmitter.emit(message, type)` pattern from `frontend/src/utils/toastEmitter.js` for all HR pages. Replace all `console.error(err)` → `toastEmitter.emit(t('error_key'), 'error')` and remove mixed `toast()` direct calls.

**Rationale**: `toastEmitter` is the project-standard pattern used in the majority of pages. It works both inside and outside React component lifecycle. Some HR pages (like LeaveList.jsx) use `react-hot-toast` directly — these should be normalized.

**Alternatives considered**:
- `useToast()` hook — only works inside React components; `toastEmitter` is more universal and already preferred
- Keep mixed patterns — rejected: Constitution XXVII requires behavioral consistency

**Specifics**:
- 37 `console.error` → `toastEmitter.emit()` replacements
- Import: `import { toastEmitter } from '../../utils/toastEmitter';`
- Message pattern: `toastEmitter.emit(t('hr.xxx.error_loading'), 'error')` (use existing i18n keys where available)
- Pages using `toast` from react-hot-toast directly: normalize to `toastEmitter`

---

## Research 6: formatNumber() Replacement Strategy

**Decision**: Replace all 28 `.toLocaleString()` monetary calls with `formatNumber()` from `frontend/src/utils/format.js`. Import already exists in some HR pages; add import where missing.

**Rationale**: `formatNumber()` reads `decimal_places` from the user's session (set during login) and applies consistent precision across the app. `.toLocaleString()` uses browser defaults which vary by locale and don't respect company settings.

**Alternatives considered**:
- Create HR-specific formatter — rejected: Constitution XIX forbids duplicate calculation/formatting logic
- Add precision parameter to each `.toLocaleString()` call — rejected: duplicates `formatNumber()`'s behavior

**Specifics**:
- 28 `.toLocaleString()` replacements across 12 files
- 3 `.toFixed(2)` replacements in GOSISettings.jsx
- Import: `import { formatNumber } from '../../utils/format';`
- For EOSSettlement.jsx (5 calls), HRHome.jsx (2 calls), WPSExport.jsx (4 calls) — heaviest files

---

## Research 7: Branch Validation Gaps

**Decision**: Add `validate_branch_access(current_user, branch_id)` calls to all HR endpoints that currently lack them: `performance.py` (all endpoints), `hr_wps_compliance.py` (saudization, WPS), `advanced.py` (selected endpoints).

**Rationale**: Constitution IV mandates `validate_branch_access()` on every branch-scoped endpoint. The function already exists in `utils/permissions.py` and is used in `hr/core.py`. The gap is in newer routers (performance, WPS compliance) that were added without the pattern.

**Specifics**:
- `performance.py`: None of the 8 endpoints call `validate_branch_access()` — all need it
- `hr_wps_compliance.py`: Saudization and WPS endpoints missing — 4 endpoints
- `advanced.py`: Selected endpoints need verification — overtime, documents, training
- Pattern: `branch_id = validate_branch_access(current_user, branch_id)` at start of endpoint function

---

## Research 8: Audit Trail Completeness

**Decision**: Verify all HR models inherit `AuditMixin` and add `log_activity()` calls to all write operations that currently lack them.

**Rationale**: Constitution XVII mandates `AuditMixin` on ALL domain models with no exceptions. `log_activity()` from `utils/audit.py` must be called for every state-changing operation.

**Specifics**:
- HR models are defined in `backend/models/domain_models/hr_core_payroll.py` — verify `AuditMixin` inheritance for all ~20 models
- `log_activity()` is already called in `core.py` for employee CRUD and payroll operations
- Gaps likely in: `performance.py` (review submissions), `advanced.py` (document CRUD, training), `self_service.py` (profile updates, leave requests)
- Pattern: `log_activity(db, user_id, username, "action", "resource_type", str(resource_id), details_dict)`
