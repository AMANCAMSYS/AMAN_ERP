"""add analytics dashboard tables and materialized views

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = 'a1b2c3d4e5f6'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    # ── Analytics Dashboard tables ──
    op.create_table(
        'analytics_dashboards',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('is_system', sa.Boolean, server_default='false', nullable=False),
        sa.Column('access_roles', JSONB, server_default='[]'),
        sa.Column('branch_scope', sa.String(20), server_default='all', nullable=False),
        sa.Column('refresh_interval_minutes', sa.Integer, server_default='15', nullable=False),
        sa.Column('created_by', sa.String(100)),
        sa.Column('updated_by', sa.String(100)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'analytics_dashboard_widgets',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('dashboard_id', sa.Integer, sa.ForeignKey('analytics_dashboards.id', ondelete='CASCADE'), nullable=False),
        sa.Column('widget_type', sa.String(30), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('data_source', sa.String(50), nullable=False),
        sa.Column('filters', JSONB, server_default='{}'),
        sa.Column('position', JSONB, server_default='{}'),
        sa.Column('sort_order', sa.Integer, server_default='0', nullable=False),
        sa.Column('created_by', sa.String(100)),
        sa.Column('updated_by', sa.String(100)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_analytics_widgets_dashboard', 'analytics_dashboard_widgets', ['dashboard_id'])

    # ── Materialized views for KPI data sources ──
    # These are refreshed every 15 minutes by the scheduler.
    # We use CREATE MATERIALIZED VIEW IF NOT EXISTS via raw SQL.

    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_revenue_summary AS
        SELECT
            DATE_TRUNC('month', je.entry_date) AS period,
            je.branch_id,
            SUM(jl.credit - jl.debit) AS total_revenue
        FROM journal_entries je
        JOIN journal_lines jl ON jl.journal_entry_id = je.id
        JOIN accounts a ON a.id = jl.account_id
        WHERE a.account_type = 'income'
          AND je.is_posted = true
        GROUP BY DATE_TRUNC('month', je.entry_date), je.branch_id
        WITH DATA;
    """)

    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_expense_summary AS
        SELECT
            DATE_TRUNC('month', je.entry_date) AS period,
            je.branch_id,
            SUM(jl.debit - jl.credit) AS total_expenses
        FROM journal_entries je
        JOIN journal_lines jl ON jl.journal_entry_id = je.id
        JOIN accounts a ON a.id = jl.account_id
        WHERE a.account_type = 'expense'
          AND je.is_posted = true
        GROUP BY DATE_TRUNC('month', je.entry_date), je.branch_id
        WITH DATA;
    """)

    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cash_position AS
        SELECT
            a.id AS account_id,
            a.name AS account_name,
            a.account_number,
            COALESCE(SUM(jl.debit - jl.credit), 0) AS balance
        FROM accounts a
        LEFT JOIN journal_lines jl ON jl.account_id = a.id
        LEFT JOIN journal_entries je ON je.id = jl.journal_entry_id AND je.is_posted = true
        WHERE a.account_type IN ('asset')
          AND a.account_number LIKE '1%'
          AND (a.name ILIKE '%cash%' OR a.name ILIKE '%bank%' OR a.name ILIKE '%نقد%' OR a.name ILIKE '%بنك%')
        GROUP BY a.id, a.name, a.account_number
        WITH DATA;
    """)

    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_top_customers AS
        SELECT
            i.party_id,
            p.name AS customer_name,
            COUNT(i.id) AS invoice_count,
            SUM(i.total_amount) AS total_amount
        FROM invoices i
        JOIN parties p ON p.id = i.party_id
        WHERE i.invoice_type = 'sales'
        GROUP BY i.party_id, p.name
        ORDER BY total_amount DESC
        LIMIT 20
        WITH DATA;
    """)

    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_ar_aging AS
        SELECT
            p.id AS party_id,
            p.name AS customer_name,
            SUM(CASE WHEN CURRENT_DATE - i.due_date <= 30 THEN i.total_amount - COALESCE(i.paid_amount, 0) ELSE 0 END) AS current_bucket,
            SUM(CASE WHEN CURRENT_DATE - i.due_date BETWEEN 31 AND 60 THEN i.total_amount - COALESCE(i.paid_amount, 0) ELSE 0 END) AS days_31_60,
            SUM(CASE WHEN CURRENT_DATE - i.due_date BETWEEN 61 AND 90 THEN i.total_amount - COALESCE(i.paid_amount, 0) ELSE 0 END) AS days_61_90,
            SUM(CASE WHEN CURRENT_DATE - i.due_date > 90 THEN i.total_amount - COALESCE(i.paid_amount, 0) ELSE 0 END) AS days_over_90
        FROM invoices i
        JOIN parties p ON p.id = i.party_id
        WHERE i.invoice_type = 'sales'
          AND i.status != 'paid'
        GROUP BY p.id, p.name
        WITH DATA;
    """)

    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_ap_aging AS
        SELECT
            p.id AS party_id,
            p.name AS supplier_name,
            SUM(CASE WHEN CURRENT_DATE - i.due_date <= 30 THEN i.total_amount - COALESCE(i.paid_amount, 0) ELSE 0 END) AS current_bucket,
            SUM(CASE WHEN CURRENT_DATE - i.due_date BETWEEN 31 AND 60 THEN i.total_amount - COALESCE(i.paid_amount, 0) ELSE 0 END) AS days_31_60,
            SUM(CASE WHEN CURRENT_DATE - i.due_date BETWEEN 61 AND 90 THEN i.total_amount - COALESCE(i.paid_amount, 0) ELSE 0 END) AS days_61_90,
            SUM(CASE WHEN CURRENT_DATE - i.due_date > 90 THEN i.total_amount - COALESCE(i.paid_amount, 0) ELSE 0 END) AS days_over_90
        FROM invoices i
        JOIN parties p ON p.id = i.party_id
        WHERE i.invoice_type = 'purchase'
          AND i.status != 'paid'
        GROUP BY p.id, p.name
        WITH DATA;
    """)

    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_inventory_turnover AS
        SELECT
            p.id AS product_id,
            p.name AS product_name,
            COALESCE(SUM(CASE WHEN it.transaction_type IN ('sale', 'out') THEN ABS(it.quantity) ELSE 0 END), 0) AS total_sold,
            COALESCE(inv.quantity, 0) AS current_stock,
            CASE
                WHEN COALESCE(inv.quantity, 0) > 0
                THEN ROUND(COALESCE(SUM(CASE WHEN it.transaction_type IN ('sale', 'out') THEN ABS(it.quantity) ELSE 0 END), 0)::numeric / inv.quantity, 2)
                ELSE 0
            END AS turnover_ratio
        FROM products p
        LEFT JOIN inventory_transactions it ON it.product_id = p.id
        LEFT JOIN inventory inv ON inv.product_id = p.id
        GROUP BY p.id, p.name, inv.quantity
        WITH DATA;
    """)

    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_sales_pipeline AS
        SELECT
            o.stage AS stage,
            COUNT(o.id) AS deal_count,
            SUM(o.expected_revenue) AS total_value,
            AVG(o.probability) AS avg_probability
        FROM crm_opportunities o
        WHERE o.stage NOT IN ('won', 'lost')
        GROUP BY o.stage
        WITH DATA;
    """)

    # Create unique indexes for concurrent refresh
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_revenue_summary ON mv_revenue_summary (period, branch_id);")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_expense_summary ON mv_expense_summary (period, branch_id);")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_cash_position ON mv_cash_position (account_id);")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_top_customers ON mv_top_customers (party_id);")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_ar_aging ON mv_ar_aging (party_id);")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_ap_aging ON mv_ap_aging (party_id);")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_inventory_turnover ON mv_inventory_turnover (product_id);")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_sales_pipeline ON mv_sales_pipeline (stage);")

    # Seed a default system dashboard with common widgets
    op.execute("""
        INSERT INTO analytics_dashboards (name, description, is_system, access_roles, branch_scope, refresh_interval_minutes, created_by)
        VALUES (
            'Executive Overview',
            'Pre-built executive dashboard with key financial and operational KPIs',
            true,
            '["admin", "manager", "accountant"]',
            'all',
            15,
            'system'
        );
    """)

    op.execute("""
        INSERT INTO analytics_dashboard_widgets (dashboard_id, widget_type, title, data_source, position, sort_order, created_by)
        SELECT d.id, w.widget_type, w.title, w.data_source, w.position::jsonb, w.sort_order, 'system'
        FROM analytics_dashboards d,
        (VALUES
            ('kpi_card', 'Total Revenue', 'revenue', '{"row":0,"col":0,"width":3,"height":1}', 1),
            ('kpi_card', 'Total Expenses', 'expenses', '{"row":0,"col":3,"width":3,"height":1}', 2),
            ('kpi_card', 'Cash Position', 'cash_position', '{"row":0,"col":6,"width":3,"height":1}', 3),
            ('bar_chart', 'Revenue vs Expenses', 'revenue', '{"row":1,"col":0,"width":6,"height":2}', 4),
            ('pie_chart', 'AR Aging', 'ar_aging', '{"row":1,"col":6,"width":6,"height":2}', 5),
            ('table', 'Top Customers', 'top_customers', '{"row":3,"col":0,"width":6,"height":2}', 6),
            ('gauge', 'Inventory Turnover', 'inventory_turnover', '{"row":3,"col":6,"width":3,"height":2}', 7),
            ('line_chart', 'Sales Pipeline', 'sales_pipeline', '{"row":3,"col":9,"width":3,"height":2}', 8)
        ) AS w(widget_type, title, data_source, position, sort_order)
        WHERE d.is_system = true AND d.name = 'Executive Overview';
    """)


def downgrade():
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_sales_pipeline CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_inventory_turnover CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_ap_aging CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_ar_aging CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_top_customers CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_cash_position CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_expense_summary CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_revenue_summary CASCADE;")
    op.drop_table('analytics_dashboard_widgets')
    op.drop_table('analytics_dashboards')
