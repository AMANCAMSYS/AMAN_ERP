"""
Reset Company Data Script
=========================
Deletes ALL transactional and master data for a company,
keeping only: accounts, roles, settings, branches, warehouses, units, taxes, COA mappings.

Usage: python3 reset_company_data.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reset_data")

COMPANY_ID = "be67ce39"

# Tables to TRUNCATE in dependency order (children first, parents last)
# CASCADE handles FK references automatically
TABLES_TO_TRUNCATE = [
    # === POS (children first) ===
    "pos_order_items",
    "pos_order_payments",
    "pos_orders",
    "pos_sessions",
    
    # === Manufacturing (children first) ===
    "production_order_operations",
    "production_order_materials",
    "manufacturing_orders",
    "manufacturing_bom_items",
    "manufacturing_boms",
    "manufacturing_work_center_routes",
    "manufacturing_routes",
    "manufacturing_work_centers",
    "maintenance_logs",
    "equipment",
    
    # === Sales (children first) ===
    "sales_return_lines",
    "sales_returns",
    "credit_note_lines",
    "credit_notes",
    "sales_order_lines",
    "sales_orders",
    "sales_quotation_lines",
    "sales_quotations",
    
    # === Purchases (children first) ===
    "purchase_order_lines",
    "purchase_orders",
    
    # === Invoices & Payments ===
    "invoice_lines",
    "invoices",
    "payment_vouchers",
    
    # === Accounting (children first) ===
    "journal_lines",
    "journal_entries",
    "recurring_journal_lines",
    "recurring_journal_templates",
    "bank_statement_lines",
    "reconciliation_matches",
    "reconciliation_lines",
    "reconciliation_statements",
    
    # === Treasury / Checks / Notes ===
    "checks_receivable",
    "checks_payable",
    "notes_receivable",
    "notes_payable",
    "treasury_accounts",
    
    # === Inventory ===
    "inventory_transactions",
    "stock_adjustments",
    "stock_shipment_items",
    "stock_shipments",
    "inventory",
    "product_batches",
    "inventory_transfer_items",
    "inventory_transfers",
    "price_list_items",
    "price_lists",
    
    # === Products & Categories ===
    "products",
    "product_categories",
    
    # === Parties / Customers / Suppliers ===
    "party_transactions",
    "customer_contacts",
    "customer_bank_accounts",
    "customer_transactions",
    "customer_receipts",
    "customer_price_lists",
    "customers",
    "customer_groups",
    "supplier_contacts",
    "supplier_bank_accounts",
    "supplier_transactions",
    "supplier_payments",
    "suppliers",
    "supplier_groups",
    "parties",
    "party_groups",
    
    # === HR (children first) ===
    "payslip_items",
    "payslips",
    "payroll_runs",
    "attendance",
    "leave_requests",
    "employee_loans",
    "employee_salary_components",
    "employees",
    "departments",
    "salary_components",
    "salary_structures",
    "salary_structure_components",
    
    # === Expenses ===
    "expenses",
    
    # === Assets ===
    "asset_depreciation_schedule",
    "asset_maintenance",
    "asset_disposal",
    "assets",
    "asset_categories",
    
    # === Budgets ===
    "budget_lines",
    "cost_centers_budgets",
    "budgets",
    "financial_reports",
    "report_templates",
    
    # === Contracts / Projects ===
    "contract_installments",
    "contracts",
    "project_tasks",
    "project_resource_allocations",
    "project_milestones",
    "project_budgets",
    "project_time_entries",
    "projects",
    
    # === Approvals ===
    "approval_actions",
    "approval_requests",
    "approval_workflow_steps",
    "approval_workflows",
    
    # === Misc ===
    "notifications",
    "audit_trail",
    "custom_reports",
    "scheduled_reports",
    "fiscal_periods",
    "fiscal_years",
    "pending_receivables",
    "pending_payables",
    "cost_centers",
]


def reset_company(company_id: str):
    """Reset all transactional + master data for a company."""
    url = settings.get_company_database_url(company_id)
    engine = create_engine(url)
    
    success = 0
    skipped = 0
    errors = 0
    
    try:
        with engine.connect() as conn:
            for table in TABLES_TO_TRUNCATE:
                try:
                    # Check if table exists
                    exists = conn.execute(text(
                        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = :t)"
                    ), {"t": table}).scalar()
                    
                    if not exists:
                        skipped += 1
                        continue
                    
                    # Count rows before
                    count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    
                    if count == 0:
                        skipped += 1
                        continue
                    
                    # TRUNCATE with CASCADE
                    conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
                    logger.info(f"  🗑️  {table}: {count} rows deleted")
                    success += 1
                    
                except Exception as e:
                    logger.warning(f"  ⚠️  {table}: {e}")
                    errors += 1
            
            # Reset account balances to zero
            logger.info("\n  🔄 Resetting account balances to zero...")
            conn.execute(text("""
                UPDATE accounts SET 
                    balance = 0,
                    balance_currency = 0
            """))
            
            # Reset sequences
            logger.info("  🔄 Resetting table sequences...")
            for table in TABLES_TO_TRUNCATE:
                try:
                    exists = conn.execute(text(
                        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = :t)"
                    ), {"t": table}).scalar()
                    if exists:
                        conn.execute(text(f"ALTER SEQUENCE IF EXISTS {table}_id_seq RESTART WITH 1"))
                except:
                    pass
            
            conn.commit()
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return False
    finally:
        engine.dispose()
    
    logger.info(f"\n  ✅ Tables cleared: {success}")
    logger.info(f"  ⏭️  Tables skipped (empty/missing): {skipped}")
    if errors:
        logger.info(f"  ⚠️  Errors: {errors}")
    
    return True


def main():
    logger.info("=" * 60)
    logger.info(f"🗑️  RESET COMPANY DATA: {COMPANY_ID}")
    logger.info("=" * 60)
    logger.info("  Keeping: accounts, roles, settings, branches, warehouses,")
    logger.info("           units, taxes, currencies, COA mappings")
    logger.info("  Deleting: ALL transactions, products, parties, employees,")
    logger.info("            invoices, journal entries, POS, manufacturing, etc.")
    logger.info("=" * 60)
    
    confirm = input("\n⚠️  This will DELETE all data. Type 'YES' to confirm: ")
    if confirm != "YES":
        logger.info("❌ Cancelled.")
        return
    
    if reset_company(COMPANY_ID):
        logger.info(f"\n{'=' * 60}")
        logger.info(f"✅ Company {COMPANY_ID} data has been reset successfully!")
        logger.info("=" * 60)
    else:
        logger.info(f"\n❌ Reset failed for company {COMPANY_ID}")


if __name__ == "__main__":
    main()
