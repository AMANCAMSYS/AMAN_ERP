# Data Model: Audit POS Module — تدقيق وحدة نقاط البيع

**Feature**: 013-audit-pos | **Date**: 2026-04-15

## Overview

This audit does NOT create new tables or entities. It adds `AuditMixin` columns to 14 existing POS tables and changes Pydantic schema types from `float` to `Decimal`.

## Model Changes (AuditMixin Addition)

All models in `backend/models/domain_models/sales_pos.py` will change from:
```python
from ..base import ModelBase
```
to:
```python
from ..base import AuditMixin, ModelBase
```

### Models Receiving AuditMixin

| # | Model | Table | Columns to Remove (overlap with AuditMixin) |
|---|-------|-------|---------------------------------------------|
| 1 | PosSession | pos_sessions | `updated_at` (manual) |
| 2 | PosOrder | pos_orders | `created_at`, `updated_at`, `created_by` (manual, INTEGER FK) |
| 3 | PosOrderLine | pos_order_lines | None (no timestamps exist) |
| 4 | PosPayment | pos_payments | `created_at` (manual) |
| 5 | PosOrderPayment | pos_order_payments | `created_at` (manual) |
| 6 | PosReturn | pos_returns | `created_at` (manual) |
| 7 | PosReturnItem | pos_return_items | `created_at` (manual) |
| 8 | PosPromotion | pos_promotions | `created_at`, `updated_at`, `created_by` (manual, INTEGER FK) |
| 9 | PosLoyaltyProgram | pos_loyalty_programs | `created_at` (manual) |
| 10 | PosLoyaltyPoint | pos_loyalty_points | `created_at` (manual) |
| 11 | PosLoyaltyTransaction | pos_loyalty_transactions | `created_at` (manual) |
| 12 | PosTable | pos_tables | `created_at` (manual) |
| 13 | PosTableOrder | pos_table_orders | None (no timestamps exist) |
| 14 | PosKitchenOrder | pos_kitchen_orders | None (has sent_at/accepted_at/ready_at/served_at — domain-specific, keep) |
| 15 | PendingReceivable | pending_receivables | `created_at` (manual) |
| 16 | Receipt | receipts | `created_at`, `created_by` (manual, INTEGER FK) |

**AuditMixin provides**: `created_at` (DateTime with timezone, server_default=now), `updated_at` (DateTime with timezone, onupdate=now), `created_by` (String(100)), `updated_by` (String(100))

**Conflict**: Models with `created_by` as `INTEGER` FK (PosOrder, PosPromotion, Receipt) must have this column removed — AuditMixin uses `String(100)` which matches all other modules.

## Database Column Additions (sync_essential_columns)

New entries in `backend/database.py` → `sync_essential_columns()`:

| Table | Column | Type |
|-------|--------|------|
| pos_sessions | created_at | TIMESTAMP WITH TIME ZONE DEFAULT NOW() |
| pos_sessions | updated_by | VARCHAR(100) |
| pos_sessions | created_by | VARCHAR(100) |
| pos_orders | updated_by | VARCHAR(100) |
| pos_order_lines | created_at | TIMESTAMP WITH TIME ZONE DEFAULT NOW() |
| pos_order_lines | updated_at | TIMESTAMP WITH TIME ZONE DEFAULT NOW() |
| pos_order_lines | created_by | VARCHAR(100) |
| pos_order_lines | updated_by | VARCHAR(100) |
| pos_payments | updated_at | TIMESTAMP WITH TIME ZONE DEFAULT NOW() |
| pos_payments | created_by | VARCHAR(100) |
| pos_payments | updated_by | VARCHAR(100) |
| pos_order_payments | updated_at | TIMESTAMP WITH TIME ZONE DEFAULT NOW() |
| pos_order_payments | created_by | VARCHAR(100) |
| pos_order_payments | updated_by | VARCHAR(100) |
| pos_returns | updated_at | TIMESTAMP WITH TIME ZONE DEFAULT NOW() |
| pos_returns | created_by | VARCHAR(100) |
| pos_returns | updated_by | VARCHAR(100) |
| pos_return_items | updated_at | TIMESTAMP WITH TIME ZONE DEFAULT NOW() |
| pos_return_items | created_by | VARCHAR(100) |
| pos_return_items | updated_by | VARCHAR(100) |
| pos_promotions | updated_by | VARCHAR(100) |
| pos_loyalty_programs | updated_at | TIMESTAMP WITH TIME ZONE DEFAULT NOW() |
| pos_loyalty_programs | created_by | VARCHAR(100) |
| pos_loyalty_programs | updated_by | VARCHAR(100) |
| pos_loyalty_points | updated_at | TIMESTAMP WITH TIME ZONE DEFAULT NOW() |
| pos_loyalty_points | created_by | VARCHAR(100) |
| pos_loyalty_points | updated_by | VARCHAR(100) |
| pos_loyalty_transactions | updated_at | TIMESTAMP WITH TIME ZONE DEFAULT NOW() |
| pos_loyalty_transactions | created_by | VARCHAR(100) |
| pos_loyalty_transactions | updated_by | VARCHAR(100) |
| pos_tables | updated_at | TIMESTAMP WITH TIME ZONE DEFAULT NOW() |
| pos_tables | created_by | VARCHAR(100) |
| pos_tables | updated_by | VARCHAR(100) |
| pos_table_orders | created_at | TIMESTAMP WITH TIME ZONE DEFAULT NOW() |
| pos_table_orders | updated_at | TIMESTAMP WITH TIME ZONE DEFAULT NOW() |
| pos_table_orders | created_by | VARCHAR(100) |
| pos_table_orders | updated_by | VARCHAR(100) |
| pos_kitchen_orders | created_at | TIMESTAMP WITH TIME ZONE DEFAULT NOW() |
| pos_kitchen_orders | updated_at | TIMESTAMP WITH TIME ZONE DEFAULT NOW() |
| pos_kitchen_orders | created_by | VARCHAR(100) |
| pos_kitchen_orders | updated_by | VARCHAR(100) |

## Schema Type Changes (Pydantic)

All changes in `backend/schemas/pos.py`:

| Class | Field | Before | After |
|-------|-------|--------|-------|
| SessionCreate | opening_balance | `float = 0.0` | `Decimal = Decimal("0")` |
| SessionClose | closing_balance | `float` | `Decimal` |
| SessionClose | cash_register_balance | `float` | `Decimal` |
| SessionResponse | opening_balance | `float = 0.0` | `Decimal = Decimal("0")` |
| SessionResponse | closing_balance | `Optional[float] = 0.0` | `Optional[Decimal] = Decimal("0")` |
| SessionResponse | total_sales | `Optional[float] = 0.0` | `Optional[Decimal] = Decimal("0")` |
| SessionResponse | total_cash | `Optional[float] = 0.0` | `Optional[Decimal] = Decimal("0")` |
| SessionResponse | total_bank | `Optional[float] = 0.0` | `Optional[Decimal] = Decimal("0")` |
| SessionResponse | total_returns | `Optional[float] = 0.0` | `Optional[Decimal] = Decimal("0")` |
| SessionResponse | total_returns_cash | `Optional[float] = 0.0` | `Optional[Decimal] = Decimal("0")` |
| SessionResponse | difference | `Optional[float] = 0.0` | `Optional[Decimal] = Decimal("0")` |
| POSProductResponse | price | `float` | `Decimal` |
| POSProductResponse | stock_quantity | `float` | `Decimal` |
| POSProductResponse | tax_rate | `Optional[float] = 0.0` | `Optional[Decimal] = Decimal("0")` |
| OrderLineCreate | quantity | `float` | `Decimal` |
| OrderLineCreate | unit_price | `float` | `Decimal` |
| OrderLineCreate | discount_amount | `float = 0` | `Decimal = Decimal("0")` |
| OrderLineCreate | tax_rate | `float = 0` | `Decimal = Decimal("0")` |
| OrderPaymentCreate | amount | `float` | `Decimal` |
| OrderCreate | discount_amount | `float = 0` | `Decimal = Decimal("0")` |
| OrderCreate | paid_amount | `float = 0` | `Decimal = Decimal("0")` |
| OrderResponse | total_amount | `float` | `Decimal` |
| ReturnItemCreate | quantity | `float` | `Decimal` |

## Relationships

No new relationships. All existing FK relationships are preserved. The only change is `created_by` column type on PosOrder, PosPromotion, and Receipt changing from INTEGER FK to VARCHAR(100) string — this removes the FK constraint but matches the AuditMixin convention used across all other modules.
