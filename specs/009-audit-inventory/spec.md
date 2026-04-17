# Feature Specification: Audit Inventory Module — تدقيق وحدة المخزون

**Feature Branch**: `009-audit-inventory`
**Created**: 2026-04-15
**Status**: Draft
**Input**: User description: "audit-inventory — المخزون — لاتنسى ان تجعل كل شيء مرتبط بالفرونت اند بالشكل الصحيح"

## User Scenarios & Testing

### User Story 1 — Product CRUD, Cost Display & Stock Visibility (Priority: P1) 🎯 MVP

As a warehouse manager, I manage products by creating/editing them, viewing their current stock per warehouse, and checking cost breakdowns — so I can maintain an accurate product catalog with correct pricing and real-time stock awareness.

**Why this priority**: Products are the foundation of the entire inventory module — every other story depends on correct product data, pricing display, and stock visibility.

**Independent Test**: Create a product with selling_price 1,250.75 SAR → verify the product list shows the price formatted correctly (not floating-point artifacts like 1250.7500000000002) → view stock per warehouse → verify quantities/costs display without "undefined" → edit the product → verify changes persist → delete the product → verify removal.

**Acceptance Scenarios**:

1. **Given** a user on the Products page, **When** I create a product with cost_price "500.50" and selling_price "750.25", **Then** the API returns these values as strings (not JSON floats) and the list renders them via `formatNumber()` without precision loss
2. **Given** a product with stock in warehouse A, **When** I view the product's stock details, **Then** the stock quantity, average cost, and total valuation display correctly with no "undefined" or "NaN" values
3. **Given** a product in the list, **When** the API returns monetary fields (selling_price, cost_price, wholesale_price), **Then** all monetary values arrive as string representations of Decimal (not float)
4. **Given** a product with cost breakdown, **When** I expand the cost breakdown view, **Then** all cost components render with `formatNumber()` and the currency symbol
5. **Given** I delete a product, **When** the deletion fails (e.g., product has stock), **Then** I see a user-facing toast error message (not just console.error)

---

### User Story 2 — Stock Movements: Receipts, Deliveries & Movement History (Priority: P1)

As a warehouse operator, I record stock receipts (incoming goods) and deliveries (outgoing goods) and view the full movement history — so I can track every stock change with an audit trail and verify quantities match physical inventory.

**Why this priority**: Stock movements are the core transactional operations of inventory — receipts/deliveries change quantities and costs, and the movement log is the audit trail.

**Independent Test**: Create a stock receipt for Product X (100 units @ 25 SAR) → verify inventory increases by 100 → verify WAC updates → verify an inventory_transaction record created → view Stock Movements page → verify the receipt appears in the list with correct quantity and cost → filter by warehouse → verify list narrows.

**Acceptance Scenarios**:

1. **Given** a stock receipt form, **When** I submit quantities, **Then** the API payload sends quantities as strings (not parseFloat) and the backend processes them correctly with Decimal arithmetic
2. **Given** a stock receipt, **When** it completes, **Then** the system creates an `inventory_transaction` record, updates WAC via `CostingService.update_cost()`, and logs the activity
3. **Given** the Stock Movements page, **When** I filter by warehouse, product, or date range, **Then** the list updates correctly and shows quantities via `formatNumber()`
4. **Given** a stock delivery that would make quantity negative, **When** I submit it, **Then** the backend returns a clear error and the frontend displays it as a toast (not console.error only)
5. **Given** the movements page loads, **When** the API call fails, **Then** a toast error shows to the user (not silent console.error)

---

### User Story 3 — Stock Transfers & Shipments Lifecycle (Priority: P1)

As a logistics coordinator, I transfer stock between warehouses (single or multi-item) and manage shipments through their lifecycle (pending → shipped → received) — so inter-warehouse movements are tracked, costs are recalculated, and GL entries are posted automatically.

**Why this priority**: Transfers and shipments handle inter-warehouse logistics — they require row-level locking, WAC recalculation, and GL posting, making them the most complex inventory operations.

**Independent Test**: Create a stock transfer from Warehouse A to Warehouse B for 50 units of Product X → verify source decreases by 50, destination increases by 50 → verify WAC recalculated on destination → verify GL entry auto-posted → create a shipment → confirm it → verify status changes to "shipped" → verify destination receives notification.

**Acceptance Scenarios**:

1. **Given** the Stock Transfer form, **When** I submit, **Then** the API payload sends `quantity` as a string (not `parseFloat(item.quantity)`) and the backend processes it with Decimal arithmetic
2. **Given** a transfer, **When** it completes, **Then** both source and destination inventory update atomically (within a single transaction with row locking)
3. **Given** a shipment in "pending" status, **When** I confirm it, **Then** status changes to "shipped" and a notification is created for the destination warehouse
4. **Given** a shipment in "shipped" status, **When** I cancel it, **Then** the status changes to "cancelled" and stock is not affected
5. **Given** the Shipment List page, **When** I filter by status (pending/shipped/received), **Then** the list shows only matching shipments and all fields render without "undefined"

---

### User Story 4 — Stock Adjustments with GL Posting (Priority: P1)

As an inventory accountant, I make stock adjustments (increase for found items, decrease for damaged/lost items) that automatically generate balanced GL journal entries — so the inventory ledger stays reconciled with the general ledger.

**Why this priority**: Adjustments bridge inventory and accounting — they must generate correct double-entry GL records to maintain financial integrity.

**Independent Test**: Create a stock adjustment (decrease 10 units of Product X, reason: "damaged") → verify inventory decreases by 10 → verify a balanced GL journal entry posted (Dr. Inventory Loss / Cr. Inventory Asset) → verify fiscal period is checked before posting → view the Adjustments list → verify the adjustment appears with correct status.

**Acceptance Scenarios**:

1. **Given** the Stock Adjustment form, **When** I submit, **Then** the API payload sends `new_quantity` as a string (not `parseFloat(formData.new_quantity)`) and the backend uses Decimal arithmetic
2. **Given** an adjustment, **When** it completes, **Then** the system posts a balanced GL journal entry, and checks that the fiscal period is open beforehand
3. **Given** the Adjustments list page, **When** the API call fails, **Then** a toast error is shown to the user (not silent `console.error`)
4. **Given** an adjustment in a closed fiscal period, **When** I attempt to create it, **Then** the backend rejects it with a clear error message and the frontend displays the error as a toast

---

### User Story 5 — Batch & Serial Tracking (Priority: P2)

As a quality manager, I manage product batches (with expiry dates) and serial numbers — creating batches, looking up serials, viewing expiry alerts, and enforcing batch/serial tracking on designated products — so I can maintain full traceability from receipt to sale.

**Why this priority**: Batch/serial tracking is essential for regulated industries (pharmaceuticals, electronics) but not all products require it, making it P2 after core CRUD and movement operations.

**Independent Test**: Enable batch tracking on a product → create a batch (100 units, expiry 2026-12-31) → verify batch appears in list → create a serial number → verify serial lookup works → view expiry alerts → verify near-expiry batches are highlighted → verify parseFloat violations in batch creation form are fixed.

**Acceptance Scenarios**:

1. **Given** a batch creation form, **When** I submit with quantity "100" and unit_cost "45.50", **Then** the API payload sends these as strings (not `parseFloat(form.quantity)` / `parseFloat(form.unit_cost)`)
2. **Given** a product with batch tracking enabled, **When** I receive stock, **Then** the system enforces batch assignment and creates batch movement records
3. **Given** the expiry alerts endpoint, **When** I request alerts, **Then** near-expiry batches are listed with days remaining and the list is filterable by warehouse
4. **Given** a serial number, **When** I look it up, **Then** I see the full history including current warehouse, batch, and status
5. **Given** bulk serial generation, **When** I generate 50 serials at once, **Then** all 50 are created with unique sequential numbers and all appear in the serials list

---

### User Story 6 — Cycle Counts & Quality Inspections (Priority: P2)

As a warehouse supervisor, I run cycle counts (full or partial inventory audits) and manage quality inspections on received goods — so I can detect and correct stock variances and ensure incoming goods meet quality standards.

**Why this priority**: Cycle counts and QC are control mechanisms that depend on base inventory operations (P1) being correct first.

**Independent Test**: Create a cycle count for Warehouse A → start it → enter counted quantities for 5 products → complete it → verify variances calculated → verify adjustment transactions created for discrepancies → verify GL entries posted for variance values → run a quality inspection → mark criteria pass/fail → complete inspection.

**Acceptance Scenarios**:

1. **Given** a cycle count with variances, **When** I complete it, **Then** the system creates inventory transactions for each variance AND posts balanced GL entries using a single Inventory Variance account (surplus: Dr. Inventory Asset / Cr. Inventory Variance; shortage: reversed) — currently missing GL posting
2. **Given** a cycle count form, **When** I enter counted quantities, **Then** the API payload sends `counted_quantity` as a string (not `parseFloat(item.counted_quantity)`)
3. **Given** a quality inspection form, **When** I enter criteria values (min/max/actual), **Then** the API payload sends these as strings (not `parseFloat(c.min_value)`)
4. **Given** a quality inspection that fails, **When** I complete it with status "failed", **Then** the received goods are quarantined (status changes to "hold") and the warehouse is notified
5. **Given** the Cycle Counts list page, **When** I view counts for my warehouse, **Then** each count shows status, total items, counted items, and variance count

---

### User Story 7 — Inventory Reports, Valuation & Dashboard (Priority: P2)

As a finance manager, I view the inventory dashboard (StockHome), valuation reports, and warehouse-level stock snapshots — so I can monitor inventory health, identify low-stock items, and ensure the inventory valuation matches the GL balance.

**Why this priority**: Reporting consumes data from all other stories — it must work correctly but does not block transactional operations.

**Independent Test**: Open StockHome → verify dashboard cards show correct metrics (product count, total value, low-stock count) → open Inventory Valuation → verify total valuation = Σ(quantity × average_cost) for each product → verify all monetary values display via `formatNumber()` → open warehouse stock snapshot → verify per-warehouse breakdown.

**Acceptance Scenarios**:

1. **Given** the StockHome dashboard, **When** it loads, **Then** summary metrics (product count, inventory value, low-stock count, warehouse count) display correctly via `formatNumber()` for monetary values
2. **Given** the Inventory Valuation report, **When** I view it, **Then** per-product valuation = quantity × average_cost, and the grand total is displayed correctly
3. **Given** the Valuation report, **When** the user lacks `stock.view_cost` permission, **Then** the cost column is hidden (permission gate)
4. **Given** the Stock Reports page, **When** any API call fails, **Then** a toast error shows (not silent console.error)
5. **Given** the warehouse stock snapshot, **When** I view it for a specific warehouse, **Then** I see all products with their quantities, reserved quantities, and available quantities

---

### User Story 8 — Costing Methods, Price Lists & Advanced Features (Priority: P3)

As an inventory controller, I manage costing policies (FIFO/LIFO/WAC), price lists, product variants, product kits (BOMs), and bin locations — so I can configure advanced inventory behaviors per product or warehouse.

**Why this priority**: These are configuration and advanced features — not core transactional operations — and are used only by a subset of businesses.

**Independent Test**: View current costing method → change to FIFO → verify layers are created on next receipt → create a price list → add items to it → verify bulk update works → create a product variant (color/size) → create a kit (BOM) with component products → verify kit structure displays correctly.

**Acceptance Scenarios**:

1. **Given** a costing method change, **When** I switch from WAC to FIFO, **Then** cost layers are initialized from current inventory and future receipts create new layers
2. **Given** a price list, **When** I bulk-update items, **Then** the updated prices persist and the API returns them as strings (not floats)
3. **Given** a product kit (BOM), **When** I view kit details, **Then** all component products display with required quantities and sub-totals
4. **Given** bin locations for a warehouse, **When** I create a bin and assign products, **Then** bin inventory tracks quantities per product per bin

---

### User Story 9 — Dead Notification Endpoints & Service Layer Cleanup (Priority: P1)

As a user navigating inventory pages, I should not encounter silent 404 errors from dead notification endpoints — and the frontend service layer must accurately map to active backend routes.

**Why this priority**: The 4 notification functions in the inventory service call endpoints that were removed from the backend (router unmounted), causing silent 404 errors. This is a P1 functional correctness issue.

**Independent Test**: Call the inventory notification functions → verify they no longer hit dead endpoints (404) → verify they either delegate to the unified notification system or are removed → verify no frontend pages break from the change.

**Acceptance Scenarios**:

1. **Given** the 4 notification functions (`getNotifications`, `getUnreadCount`, `markNotificationRead`, `markAllNotificationsRead`) in the inventory service, **When** the audit is complete, **Then** they are removed entirely and all callers use the unified notification API
2. **Given** any frontend page that previously imported these functions, **When** it needs notifications, **Then** it uses the unified notification hooks/components directly
3. **Given** the inventory service exports, **When** the notification functions are removed, **Then** no remaining import references exist in any component

---

### Edge Cases

- What happens when a delivery is attempted for a quantity exceeding available stock? → Hard-blocked: the system rejects the transaction with a clear error message
- How does the system handle a transfer when the destination warehouse is in a different branch the user does not have access to?
- What happens when a batch-tracked product receives stock without a batch assignment?
- How does the system handle concurrent adjustments to the same product in the same warehouse?
- What happens when a cycle count is completed but the fiscal period is closed?
- How does the system handle a costing method change when there are open (non-exhausted) cost layers?
- What happens when a quality inspection references a receipt that was already reversed?

## Requirements

### Functional Requirements

- **FR-001**: System MUST return all monetary values (cost_price, selling_price, wholesale_price, average_cost, unit_cost, total_cost, valuation, transfer_cost) from inventory API endpoints as string representations of Decimal, not JSON floats
- **FR-002**: Frontend MUST NOT use `parseFloat()` for monetary or quantity values in API payloads — must send as strings and let the backend parse with Decimal
- **FR-003**: All inventory list pages MUST display monetary values using `formatNumber()` utility
- **FR-004**: All frontend fetch operations MUST have `try/catch` error handling with `showToast()` from `useToast` hook — not `console.error` alone
- **FR-005**: System MUST enforce branch-level access control via `validate_branch_access()` on all inventory endpoints that accept `branch_id` or `warehouse_id`
- **FR-006**: Stock adjustments MUST check that the fiscal period is open before processing and MUST post a balanced GL journal entry
- **FR-007**: Stock transfers MUST use row-level locking on both source and destination inventory rows to prevent phantom stock
- **FR-008**: The system MUST recalculate WAC (weighted average cost) on the destination warehouse after every transfer and receipt
- **FR-009**: Cycle count completion MUST post balanced GL entries for variance values (currently missing — only creates inventory transactions). Use a single Inventory Variance account: surplus → Dr. Inventory Asset / Cr. Inventory Variance; shortage → Dr. Inventory Variance / Cr. Inventory Asset
- **FR-010**: The 4 dead notification functions (`getNotifications`, `getUnreadCount`, `markNotificationRead`, `markAllNotificationsRead`) in the inventory service MUST be removed entirely (not redirected). All callers MUST be updated to use the unified notification API directly
- **FR-011**: Product creation/update MUST validate that `product_code` and `sku` are unique across the tenant
- **FR-012**: Batch tracking MUST be enforced on stock receipts for products with batch tracking enabled
- **FR-013**: Serial tracking MUST be enforced on stock receipts for products with serial tracking enabled
- **FR-014**: Shipment lifecycle MUST enforce state transitions: pending → shipped → received (no skip or reverse)
- **FR-015**: Shipment confirmation MUST create a notification for the destination warehouse
- **FR-016**: All inventory write endpoints MUST log the activity for the audit trail
- **FR-017**: Inventory valuation report MUST calculate total = Σ(quantity × average_cost) per product and match the GL balance
- **FR-018**: Quality inspection completion with "failed" status MUST quarantine the inspected goods
- **FR-019**: All SQL queries in inventory endpoints MUST use parameterized queries — no string interpolation of user input
- **FR-020**: Error handling pattern across all inventory frontend pages MUST use `useToast` hook (not `toastEmitter.emit()` or `console.error` alone) for consistency with the rest of the application
- **FR-021**: All inventory frontend pages MUST import and use `useBranch` from `BranchContext` to filter data by the currently selected branch
- **FR-022**: Stock Adjustments list page MUST show a toast error when the API call fails (currently `console.error` only)
- **FR-023**: Cycle counts MUST send `counted_quantity` as string in the API payload (not `parseFloat`)
- **FR-024**: Quality inspections MUST send `min_value`, `max_value`, `actual_value` as strings in the API payload (not `parseFloat`)
- **FR-025**: The Inventory Valuation page MUST gate the cost column behind appropriate view-cost permission
- **FR-026**: Demand forecast generation MUST accept warehouse and product filters and return forecast data with clear period breakdowns
- **FR-027**: All inventory deduction endpoints (delivery, transfer-out, adjustment-decrease, POS deduction) MUST hard-block and reject with a clear error if the transaction would make the product's available quantity negative in that warehouse
- **FR-028**: The `product_categories` table MUST have `created_by` and `updated_by` columns, and the `stock_adjustments` table MUST have `updated_at` and `updated_by` columns added via a lightweight migration to satisfy the AuditMixin requirement

### Key Entities

- **Product**: Core catalog item with pricing (cost, selling, wholesale, min, max), tracking flags (batch, serial, expiry), category, unit, and variant/kit support
- **Warehouse**: Storage location scoped to a branch, containing inventory rows per product
- **Inventory**: Per-product-per-warehouse stock record (quantity, reserved, available, average_cost)
- **Inventory Transaction**: Movement log recording every stock change (type, quantity, cost, reference, before/after balance)
- **Stock Adjustment**: Manual stock correction with reason, linked to GL journal entry
- **Stock Shipment**: Multi-item inter-warehouse movement with lifecycle (pending → shipped → received)
- **Product Batch**: Lot/batch tracking with manufacturing date, expiry date, quantity, and unit cost
- **Product Serial**: Individual item tracking with serial number, warranty dates, and status
- **Cost Layer**: FIFO/LIFO tracking record per receipt, with remaining quantity and unit cost
- **Cycle Count**: Periodic inventory audit with per-item variance tracking and GL adjustment
- **Quality Inspection**: QC gate with pass/fail criteria on received goods
- **Bin Location**: Warehouse sub-location (zone/aisle/rack/shelf) for granular stock placement
- **Price List**: Named pricing scheme with per-product price overrides

## Success Criteria

### Measurable Outcomes

- **SC-001**: All monetary values across inventory API endpoints are returned as strings — zero `float()` casts on monetary fields in API response payloads
- **SC-002**: All 6 identified `parseFloat()` violations in frontend forms are eliminated — API payloads send numeric values as strings
- **SC-003**: All inventory frontend pages (22 pages) use consistent `useToast` error handling — zero `console.error`-only patterns remain
- **SC-004**: The 4 dead notification functions produce zero 404 errors in any user session
- **SC-005**: Cycle count completion generates balanced GL journal entries for all variance values greater than zero
- **SC-006**: All inventory list pages render monetary values via `formatNumber()` with user-configured decimal precision
- **SC-007**: Stock adjustments and transfers successfully post balanced GL entries that reconcile with inventory valuation
- **SC-008**: Zero SQL injection vectors — all queries use parameterized queries
- **SC-009**: Users can complete product CRUD workflow (create → list → edit → delete) with correct pricing display in under 2 minutes
- **SC-010**: Inventory valuation report total matches GL inventory account balance within rounding tolerance (0.01)

## Clarifications

### Session 2026-04-15

- Q: Should this audit also fix issues found in cross-module integration points (Purchases, Sales, POS, Manufacturing, Returns), or only within the inventory module's own files? → A: Inventory module files only (15 routers + 22 pages + services). Cross-module integration issues are deferred to their respective module audits.
- Q: Should the audit enforce a single negative stock prevention policy across all inventory endpoints? → A: Hard-block — reject any transaction that would make available quantity negative. No soft-warn or per-warehouse configuration.
- Q: Which GL accounts should be used for cycle count variance entries (surplus vs shortage)? → A: Single variance account with direction swap. Surplus: Dr. Inventory Asset / Cr. Inventory Variance. Shortage: Dr. Inventory Variance / Cr. Inventory Asset.
- Q: Should the 4 dead notification functions in inventory service be removed entirely or redirected to the unified notification endpoints? → A: Remove entirely. Update all callers to use the unified notification API directly.
- Q: Should missing audit columns (created_by/updated_by on product_categories, updated_at/updated_by on stock_adjustments) be added via migration or documented only? → A: Add via lightweight migration. Audit fields are constitutionally mandated — override the no-migrations assumption for this specific fix.

## Assumptions

- **Scope boundary**: This audit covers only the inventory module's own files (backend/routers/inventory/*, frontend/src/pages/Stock/*, frontend/src/pages/Forecast/*, frontend/src/services/inventory.js, backend/services/costing_service.py, backend/services/forecast_service.py, backend/services/demand_forecast_service.py, backend/models/domain_models/inventory_*). Cross-module files (purchases.py, delivery_orders.py, pos.py, manufacturing/core.py, sales/returns.py) are explicitly out of scope
- The existing database schema (26+ tables across 5 domain model files) is complete and requires no migrations — this is an audit of existing code, not new feature development. **Exception**: missing audit columns on `product_categories` and `stock_adjustments` will be added via a lightweight `ALTER TABLE ADD COLUMN` migration (constitutionally mandated)
- The costing service correctly implements WAC, FIFO, and LIFO — this audit focuses on how it is called, not its internal algorithm
- The GL journal entry service function is correct and tested — this audit verifies it is called where needed
- The unified notification system is functional and can replace the dead inventory notification endpoints
- The `useToast` hook and `formatNumber()` utility are stable and available across all pages — no changes needed to these shared utilities themselves
- The `validate_branch_access()` utility correctly enforces branch-level access — this audit verifies it is called on appropriate endpoints
- Frontend style conventions follow existing project style guide — the audit enforces existing patterns, not new ones
- All 15 backend router files and 22 frontend page files exist and are the complete scope — no hidden files outside these directories
