# AMAN ERP — Frontend Style Guide

This document defines mandatory frontend component patterns,
cell rendering standards, and page checklists for all AMAN ERP pages.

## Component Mandates

All new frontend pages MUST follow the established design system.
Non-compliance is a blocking defect.

### Page Layout

- Root element MUST be `<div className="workspace fade-in">`.
- Header MUST use `<div className="workspace-header">` containing
  title in `<h1 className="workspace-title">` and optional subtitle
  in `<p className="workspace-subtitle">`.
- Using `module-container`, `page-container`, or bare `<h2>` headers
  is forbidden.

### List Pages

- MUST use `DataTable` from `../../components/common/DataTable`.
- Raw `<table>` elements are forbidden on pages that display tabular
  data. DataTable provides built-in pagination, loading state, empty
  state, and consistent styling.

### Search & Filter

- MUST use `SearchFilter` from `../../components/common/SearchFilter`.
- Custom bare `<select>` or `<input>` filter elements outside
  SearchFilter are forbidden.

### Form Pages

- All form inputs MUST use `FormField` from
  `../../components/common/FormField`.
- Raw `<label>/<input>` pairs without FormField are forbidden.
- All `<input>` and `<select>` elements MUST have
  `className="form-input"`.

### Navigation

- Every page (except top-level dashboards) MUST include `BackButton`
  from `../../components/common/BackButton` inside the
  `workspace-header` div.

### Loading State

- MUST use the shared `PageLoading` component (or DataTable's
  built-in loading).
- Plain `<p>Loading...</p>` or Bootstrap spinners are forbidden.

### API Client

- All API calls MUST use the shared instance from `../../utils/api`.
- Importing from `../../services/apiClient` or creating custom axios
  instances is forbidden.

### Number Formatting

- Monetary and numeric display MUST use `formatNumber()` from utils.
- Raw `parseFloat().toLocaleString()` is forbidden.

### Status Badges

- MUST use `badge badge-success`, `badge badge-warning`,
  `badge badge-danger`, `badge badge-info` CSS classes.
- Hardcoded hex color values in badge styles are forbidden.

### RTL Support

- Spacing MUST use CSS logical properties (`marginInlineStart`,
  `marginInlineEnd`, `paddingInlineStart`, `insetInlineStart`).
- Physical `marginLeft`, `marginRight`, `paddingLeft`, `left`,
  `right` are forbidden.

### i18n Discipline

- All user-facing strings MUST use `t()` from `useTranslation()`
  with keys defined in both `en.json` and `ar.json`.
- Hardcoded English fallback arguments (e.g., `t('key', 'Fallback')`)
  are forbidden.

### User Feedback

- MUST use `useToast()` for success/error messages.
- `window.alert()` and `window.confirm()` are forbidden.

---

## Cell & Column Rendering Standards

All DataTable column `render` functions MUST follow these patterns.
Inline styles for cell content are forbidden; use CSS utility classes.

| Cell Type | Standard | Forbidden |
|-----------|----------|-----------|
| **Status/Badge** | `STATUS_BADGE_MAP` in `utils/constants` → `badge badge-{variant}` | Inline `backgroundColor`/`color` styles |
| **Currency/Monetary** | `formatNumber(value)` + currency in `<small>` tag, right-aligned (`textAlign: 'end'`) | `parseFloat().toLocaleString()` |
| **Code/ID** | `className="code-cell"` (monospace + background) | Manual `fontFamily: 'monospace'` inline styles |
| **Date** | `formatShortDate()` or `formatDate()` from utils | `new Date().toLocaleDateString()` |
| **Action** | Last column, `className="btn-icon"`, icon buttons with `title` attrs | Inline `onClick` with `window.confirm()` |
| **Boolean/Toggle** | Status badges with translated labels | Raw "true"/"false" strings |
| **Empty/Null** | `—` (em-dash) | Blank cells or "N/A" |
| **Column Widths** | Defined as percentages in column config | Auto-sizing for tables with 5+ columns |

---

## Page Checklist

For every new page, verify:

- [ ] `workspace fade-in` root element
- [ ] `DataTable` on list pages
- [ ] `FormField` on form pages
- [ ] `SearchFilter` on list pages
- [ ] `BackButton` in header
- [ ] `PageLoading` for loading state
- [ ] API from `../../utils/api`
- [ ] `formatNumber()` for numeric values
- [ ] `badge-*` classes for status
- [ ] CSS logical properties for spacing
- [ ] No `t()` fallback strings
- [ ] No `alert()` or `confirm()`
- [ ] All status values in `STATUS_BADGE_MAP`
- [ ] No raw `<table>` elements
