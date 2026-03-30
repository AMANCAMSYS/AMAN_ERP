"""bulk_drift_normalization

Revision ID: c1f4e8d9b2a6
Revises: a4b2c9d8e6f1
Create Date: 2026-03-30 16:55:00.000000

Normalize structural drift across remaining non-modeled tables by:
- adding missing columns (idempotent)
- widening/changing column types where needed
- relaxing/enforcing nullability when safe
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c1f4e8d9b2a6"
down_revision: Union[str, None] = "a4b2c9d8e6f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA_TARGETS = {
    "capacity_plans": {
        "actual_hours": {"type": "NUMERIC(10, 2)", "nullable": True},
        "available_hours": {"type": "NUMERIC(10, 2)", "nullable": True},
        "created_by": {"type": "INTEGER", "nullable": True},
        "planned_hours": {"type": "NUMERIC(10, 2)", "nullable": True},
        "work_center_id": {"type": "INTEGER", "nullable": True},
    },
    "commission_rules": {
        "max_amount": {"type": "NUMERIC(18, 4)", "nullable": True},
        "min_amount": {"type": "NUMERIC(18, 4)", "nullable": True},
        "rate": {"type": "NUMERIC(10, 4)", "nullable": True},
    },
    "contract_amendments": {
        "created_by": {"type": "INTEGER", "nullable": True},
    },
    "crm_knowledge_base": {
        "helpful_count": {"type": "INTEGER", "nullable": True},
        "tags": {"type": "TEXT", "nullable": True},
        "title": {"type": "VARCHAR(500)", "nullable": False},
    },
    "customer_groups": {
        "application_scope": {"type": "VARCHAR(20)", "nullable": True},
        "effect_type": {"type": "VARCHAR(20)", "nullable": True},
    },
    "dashboard_layouts": {
        "layout_name": {"type": "VARCHAR(255)", "nullable": True},
        "user_id": {"type": "INTEGER", "nullable": True},
    },
    "fiscal_periods": {
        "fiscal_year_id": {"type": "INTEGER", "nullable": True},
    },
    "lease_contracts": {
        "accumulated_depreciation": {"type": "NUMERIC(15, 4)", "nullable": True},
        "created_by": {"type": "INTEGER", "nullable": True},
        "description": {"type": "TEXT", "nullable": True},
        "discount_rate": {"type": "NUMERIC(8, 4)", "nullable": True},
        "end_date": {"type": "DATE", "nullable": True},
        "lease_liability": {"type": "NUMERIC(15, 4)", "nullable": True},
        "lease_type": {"type": "VARCHAR(30)", "nullable": True},
        "monthly_payment": {"type": "NUMERIC(15, 4)", "nullable": True},
        "right_of_use_value": {"type": "NUMERIC(15, 4)", "nullable": True},
        "start_date": {"type": "DATE", "nullable": True},
        "total_payments": {"type": "NUMERIC(15, 4)", "nullable": True},
    },
    "leave_carryover": {
        "employee_id": {"type": "INTEGER", "nullable": True},
    },
    "marketing_campaigns": {
        "name": {"type": "VARCHAR(255)", "nullable": False},
        "spent": {"type": "NUMERIC(15, 2)", "nullable": True},
        "status": {"type": "VARCHAR(50)", "nullable": True},
    },
    "notifications": {
        "company_id": {"type": "VARCHAR(20)", "nullable": True},
        "entity_id": {"type": "INTEGER", "nullable": True},
        "entity_type": {"type": "VARCHAR(50)", "nullable": True},
        "link": {"type": "VARCHAR(500)", "nullable": True},
        "priority": {"type": "VARCHAR(20)", "nullable": True},
        "read_at": {"type": "TIMESTAMP", "nullable": True},
        "type": {"type": "VARCHAR(50)", "nullable": True},
    },
    "opportunity_activities": {
        "activity_type": {"type": "VARCHAR(30)", "nullable": True},
        "completed_at": {"type": "TIMESTAMP", "nullable": True},
        "due_date": {"type": "TIMESTAMP", "nullable": True},
    },
    "pos_orders": {
        "coupon_code": {"type": "VARCHAR(100)", "nullable": True},
        "loyalty_points_earned": {"type": "NUMERIC(12, 2)", "nullable": True},
        "loyalty_points_redeemed": {"type": "NUMERIC(12, 2)", "nullable": True},
        "party_id": {"type": "INTEGER", "nullable": True},
        "promotion_id": {"type": "INTEGER", "nullable": True},
        "table_id": {"type": "INTEGER", "nullable": True},
        "updated_at": {"type": "TIMESTAMP", "nullable": True},
    },
    "pos_sessions": {
        "updated_at": {"type": "TIMESTAMP", "nullable": True},
    },
    "production_order_operations": {
        "sequence": {"type": "INTEGER", "nullable": True},
    },
    "project_risks": {
        "created_by": {"type": "INTEGER", "nullable": True},
        "impact": {"type": "VARCHAR(20)", "nullable": True},
        "probability": {"type": "VARCHAR(20)", "nullable": True},
        "risk_score": {"type": "NUMERIC(5, 4)", "nullable": True},
        "status": {"type": "VARCHAR(30)", "nullable": True},
        "updated_at": {"type": "TIMESTAMP", "nullable": True},
    },
    "sales_commissions": {
        "commission_amount": {"type": "NUMERIC(18, 4)", "nullable": True},
        "commission_rate": {"type": "NUMERIC(10, 4)", "nullable": True},
        "invoice_number": {"type": "VARCHAR(100)", "nullable": True},
        "invoice_total": {"type": "NUMERIC(18, 4)", "nullable": True},
        "salesperson_id": {"type": "INTEGER", "nullable": True},
        "status": {"type": "VARCHAR(30)", "nullable": True},
    },
    "sales_opportunities": {
        "contact_email": {"type": "VARCHAR(150)", "nullable": True},
        "contact_phone": {"type": "VARCHAR(50)", "nullable": True},
        "currency": {"type": "VARCHAR(10)", "nullable": True},
        "expected_value": {"type": "NUMERIC(18, 2)", "nullable": True},
    },
    "sales_orders": {
        "source_quotation_id": {"type": "INTEGER", "nullable": True},
    },
    "sales_quotations": {
        "conversion_date": {"type": "TIMESTAMP", "nullable": True},
        "converted_to_order_id": {"type": "INTEGER", "nullable": True},
    },
    "sales_returns": {
        "currency": {"type": "VARCHAR(10)", "nullable": True},
    },
    "supplier_groups": {
        "application_scope": {"type": "VARCHAR(20)", "nullable": True},
        "effect_type": {"type": "VARCHAR(20)", "nullable": True},
    },
    "task_dependencies": {
        "dependency_type": {"type": "VARCHAR(20)", "nullable": True},
    },
    "tax_calendar": {
        "created_by": {"type": "INTEGER", "nullable": True},
        "is_completed": {"type": "BOOLEAN", "nullable": True},
        "recurrence_months": {"type": "INTEGER", "nullable": True},
        "recurrence_pattern": {"type": "VARCHAR(20)", "nullable": True},
        "status": {"type": "VARCHAR(20)", "nullable": True},
        "tax_type": {"type": "VARCHAR(50)", "nullable": True},
    },
    "user_2fa_settings": {
        "backup_codes_used": {"type": "INTEGER", "nullable": True},
    },
    "webhook_logs": {
        "error_message": {"type": "TEXT", "nullable": True},
        "event": {"type": "VARCHAR(100)", "nullable": True},
    },
    "wht_transactions": {
        "gross_amount": {"type": "NUMERIC(18, 2)", "nullable": False},
        "journal_entry_id": {"type": "INTEGER", "nullable": True},
        "net_amount": {"type": "NUMERIC(18, 2)", "nullable": False},
        "period_date": {"type": "DATE", "nullable": True},
        "status": {"type": "VARCHAR(20)", "nullable": True},
        "supplier_id": {"type": "INTEGER", "nullable": True},
        "wht_amount": {"type": "NUMERIC(18, 2)", "nullable": False},
    },
}


def _q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _normalize_type(type_sql: str) -> str:
    t = type_sql.upper().strip()
    t = t.replace("CHARACTER VARYING", "VARCHAR")
    t = t.replace("WITHOUT TIME ZONE", "")
    t = t.replace(" WITH TIME ZONE", "")
    t = " ".join(t.split())
    return t


def _column_exists(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(c["name"] == column_name for c in inspector.get_columns(table_name, schema="public"))


def _get_column(inspector: sa.Inspector, table_name: str, column_name: str) -> dict | None:
    for col in inspector.get_columns(table_name, schema="public"):
        if col["name"] == column_name:
            return col
    return None


def _cast_expression(column_name: str, target_type: str) -> str:
    # Generic cast is sufficient for this drift set (widening + nullable alignment).
    return f"{_q(column_name)}::{target_type}"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names(schema="public"))

    for table_name, columns in SCHEMA_TARGETS.items():
        if table_name not in existing_tables:
            continue

        for column_name, spec in columns.items():
            target_type = spec["type"]
            target_nullable = bool(spec["nullable"])

            if not _column_exists(inspector, table_name, column_name):
                op.execute(
                    sa.text(
                        f"ALTER TABLE {_q(table_name)} "
                        f"ADD COLUMN IF NOT EXISTS {_q(column_name)} {target_type}"
                    )
                )
                # Refresh inspector state after DDL changes.
                inspector = sa.inspect(bind)
                continue

            current = _get_column(inspector, table_name, column_name)
            if current is None:
                continue

            current_type = _normalize_type(str(current["type"]))
            wanted_type = _normalize_type(target_type)
            if current_type != wanted_type:
                op.execute(
                    sa.text(
                        f"ALTER TABLE {_q(table_name)} "
                        f"ALTER COLUMN {_q(column_name)} TYPE {target_type} "
                        f"USING {_cast_expression(column_name, target_type)}"
                    )
                )
                inspector = sa.inspect(bind)
                current = _get_column(inspector, table_name, column_name)
                if current is None:
                    continue

            current_nullable = bool(current.get("nullable", True))
            if current_nullable != target_nullable:
                if target_nullable:
                    op.execute(
                        sa.text(
                            f"ALTER TABLE {_q(table_name)} "
                            f"ALTER COLUMN {_q(column_name)} DROP NOT NULL"
                        )
                    )
                else:
                    null_count = bind.execute(
                        sa.text(
                            f"SELECT COUNT(*) FROM {_q(table_name)} "
                            f"WHERE {_q(column_name)} IS NULL"
                        )
                    ).scalar()
                    if int(null_count or 0) == 0:
                        op.execute(
                            sa.text(
                                f"ALTER TABLE {_q(table_name)} "
                                f"ALTER COLUMN {_q(column_name)} SET NOT NULL"
                            )
                        )


def downgrade() -> None:
    # Intentional no-op:
    # This normalization migration is additive/standardizing across tenants.
    # Reversing could re-introduce schema drift.
    pass
