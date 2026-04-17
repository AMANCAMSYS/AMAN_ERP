# Data Model: Audit Sales Module

**Feature**: 012-audit-sales | **Date**: 2026-04-15

> This audit does not create new entities. It modifies existing entities to add audit infrastructure and fix type correctness.

## Entity Changes

### 1. Sales-Exclusive Models — Add AuditMixin

All models in `backend/models/domain_models/sales_rfq.py` that are sales-exclusive:

| Entity | Fields Added | Notes |
|--------|-------------|-------|
| SalesCommission | updated_at, created_by, updated_by | already has created_at |
| SalesOpportunity | updated_at, updated_by | already has created_at, may have created_by |
| SalesOrder | updated_at, updated_by | already has created_at, created_by |
| SalesOrderLine | created_at, updated_at, created_by, updated_by | no audit fields |
| SalesQuotation | updated_at, updated_by | already has created_at, created_by |
| SalesQuotationLine | created_at, updated_at, created_by, updated_by | no audit fields |
| SalesReturn | updated_at, updated_by | already has created_at, created_by |
| SalesReturnLine | created_at, updated_at, created_by, updated_by | no audit fields |
| SalesTarget | updated_at, updated_by | already has created_at |
| RequestForQuotation | updated_by | already has created_at, updated_at, created_by |
| RfqLine | created_at, updated_at, created_by, updated_by | no audit fields |
| RfqResponse | created_at, updated_at, created_by, updated_by | only has submitted_at |

### 2. Database Tables — Add Missing Audit Columns

All changes in `backend/database.py` CREATE TABLE statements:

| Table | Add updated_at | Add created_by | Add updated_by | Add created_at |
|-------|---------------|---------------|---------------|---------------|
| invoices | — | — | ✓ | — |
| invoice_lines | ✓ | ✓ | ✓ | — |
| sales_quotations | ✓ | — | ✓ | — |
| sales_quotation_lines | ✓ | ✓ | ✓ | ✓ |
| sales_orders | ✓ | — | ✓ | — |
| sales_order_lines | ✓ | ✓ | ✓ | ✓ |
| sales_returns | ✓ | — | ✓ | — |
| sales_return_lines | ✓ | ✓ | ✓ | ✓ |
| payment_vouchers | ✓ | ✓ | ✓ | — |
| sales_commissions | ✓ | ✓ | ✓ | — |

### 3. Pydantic Schema Type Changes

| Schema File | Field | From | To |
|-------------|-------|------|-----|
| schemas/sales_credit_notes.py | SalesNoteLine.quantity | `float = 1` | `Decimal = Decimal("1")` |
| routers/sales/schemas.py | (all monetary/qty fields) | `float` | `Decimal` |
| schemas/sales_improvements.py | (monetary fields) | `float` | `Decimal` |
| schemas/cpq.py | (verify completeness) | mostly Decimal already | verify no float remains |

## Relationships (Unchanged)

No relationship changes. All existing FK relationships remain intact:
- SalesQuotation → SalesOrder → Invoice → DeliveryOrder (conversion chain)
- Invoice → InvoiceLine (parent-child)
- SalesReturn → SalesReturnLine (parent-child)
- SalesCommission → Invoice (FK: invoice_id)
- CustomerReceipt → Invoice (allocation)
- DeliveryOrder → DeliveryOrderLine (parent-child)

## Validation Rules (Unchanged)

No new validation rules. Existing validations remain:
- Fiscal period check before GL posting (already in place)
- UOM quantity validation (already in place)
- Credit limit check at SO posting (already in place)

## State Transitions (Unchanged)

No changes to state machines:
- Quotation → SO → Delivery → Invoice → Receipt (sales pipeline)
- Commission: pending → approved → paid
