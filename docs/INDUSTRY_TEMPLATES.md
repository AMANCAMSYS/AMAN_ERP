# AMAN ERP — Industry Templates

AMAN supports 12 industry types. Each industry activates a specific
set of modules via `INDUSTRY_FEATURES[industry_type]`.

| Code | Industry | Special Capabilities |
|------|----------|---------------------|
| RT | Retail | POS, loyalty, UOM variants, bin management |
| WS | Wholesale | Volume discounts, bulk orders |
| FB | Food & Beverage | Table management, KDS, meal combos |
| MF | Manufacturing | BOM, routings, MRP, capacity planning |
| CN | Construction | Job costing, progress billing, equipment |
| SV | Services | Time tracking, expense claims, retainers |
| PH | Pharmacy | Batch/serial tracking, expiry dates |
| WK | Wholesale Dealer | Net terms, volume tiers, distributor pricing |
| EC | E-Commerce | Multi-channel, dropshipping, fulfillment |
| LG | Logistics | Fleet management, shipment tracking |
| AG | Agriculture | Seasonal cycles, crop management, yield |
| GN | Generic | All modules enabled, no restrictions |

## Configuration Rules

- Industry selection at company creation MUST configure the correct
  module flags. Changing industry type after initial setup MUST be
  treated as a major configuration change requiring data review.
- Industry-specific GL account mappings MUST follow rules in
  `services/industry_gl_rules.py`.
- Industry-specific KPI calculations MUST use
  `services/industry_kpi_service.py`.
- Chart of accounts templates MUST be scaffolded per industry via
  `services/industry_coa_templates.py`.
