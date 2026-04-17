from uuid import UUID as PyUUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase, AuditMixin


class DashboardLayout(ModelBase):
    __tablename__ = "dashboard_layouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    layout_name: Mapped[str | None] = mapped_column(String(255), default="default")
    widgets: Mapped[list | None] = mapped_column(JSONB, default=list)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FiscalPeriod(ModelBase):
    __tablename__ = "fiscal_periods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Date] = mapped_column(Date, nullable=False)
    fiscal_year: Mapped[int | None] = mapped_column(Integer)
    is_closed: Mapped[bool | None] = mapped_column(Boolean, default=False)
    closed_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    closed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    fiscal_year_id: Mapped[int | None] = mapped_column(Integer)


class GosiSetting(ModelBase):
    __tablename__ = "gosi_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_share_percentage: Mapped[float | None] = mapped_column(Numeric(5, 2), default=9.75)
    employer_share_percentage: Mapped[float | None] = mapped_column(Numeric(5, 2), default=11.75)
    occupational_hazard_percentage: Mapped[float | None] = mapped_column(Numeric(5, 2), default=2.0)
    max_contributable_salary: Mapped[float | None] = mapped_column(Numeric(18, 4), default=45000)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    effective_date: Mapped[Date | None] = mapped_column(Date)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IntercompanyTransaction(ModelBase):
    __tablename__ = "intercompany_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    target_company_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(10), default="SAR")
    source_journal_id: Mapped[int | None] = mapped_column(Integer)
    target_journal_id: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    created_by: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))


class LandedCostAllocation(ModelBase, AuditMixin):
    __tablename__ = "landed_cost_allocations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    landed_cost_id: Mapped[int] = mapped_column(ForeignKey("landed_costs.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    po_line_id: Mapped[int | None] = mapped_column(ForeignKey("purchase_order_lines.id", ondelete="SET NULL"))
    original_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    allocated_amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    new_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    allocation_basis: Mapped[float | None] = mapped_column(Numeric(15, 6), default=0)
    allocation_share: Mapped[float | None] = mapped_column(Numeric(15, 6), default=0)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AnalyticsDashboard(ModelBase):
    """BI analytics dashboard with pre-built or custom KPI widgets."""
    __tablename__ = "analytics_dashboards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    access_roles: Mapped[list | None] = mapped_column(JSONB, default=list)
    branch_scope: Mapped[str] = mapped_column(String(20), default="all", server_default="all")
    refresh_interval_minutes: Mapped[int] = mapped_column(Integer, default=15, server_default="15")
    created_by: Mapped[str | None] = mapped_column(String(100))
    updated_by: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AnalyticsDashboardWidget(ModelBase):
    """Individual widget on an analytics dashboard."""
    __tablename__ = "analytics_dashboard_widgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dashboard_id: Mapped[int] = mapped_column(ForeignKey("analytics_dashboards.id", ondelete="CASCADE"), nullable=False)
    widget_type: Mapped[str] = mapped_column(String(30), nullable=False)  # kpi_card, bar_chart, line_chart, pie_chart, table, gauge
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    data_source: Mapped[str] = mapped_column(String(50), nullable=False)  # revenue, expenses, cash_position, top_customers, inventory_turnover, ar_aging, ap_aging, sales_pipeline, custom_query
    filters: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    position: Mapped[dict | None] = mapped_column(JSONB, default=dict)  # {row, col, width, height}
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_by: Mapped[str | None] = mapped_column(String(100))
    updated_by: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())