from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func, text as sa_text
from sqlalchemy.orm import Mapped, mapped_column
from decimal import Decimal

from ..base import ModelBase


class Project(ModelBase):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_code: Mapped[str | None] = mapped_column(String(50), unique=True)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    project_name_en: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    customer_id: Mapped[int | None] = mapped_column(Integer)
    party_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id"))
    project_type: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str | None] = mapped_column(String(20), default="planning")
    start_date: Mapped[Date | None] = mapped_column(Date)
    end_date: Mapped[Date | None] = mapped_column(Date)
    planned_budget: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), default=0)
    actual_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), default=0)
    progress_percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=0)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    contract_type: Mapped[str | None] = mapped_column(String(30), default="fixed_price")
    retainer_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), default=0)
    billing_cycle: Mapped[str | None] = mapped_column(String(20), default="monthly")
    last_billed_date: Mapped[Date | None] = mapped_column(Date)
    next_billing_date: Mapped[Date | None] = mapped_column(Date)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=sa_text("1"))


class ProjectTask(ModelBase):
    __tablename__ = "project_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    task_name: Mapped[str] = mapped_column(String(255), nullable=False)
    task_name_en: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    parent_task_id: Mapped[int | None] = mapped_column(ForeignKey("project_tasks.id"))
    start_date: Mapped[Date | None] = mapped_column(Date)
    end_date: Mapped[Date | None] = mapped_column(Date)
    planned_hours: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), default=0)
    actual_hours: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), default=0)
    progress: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=0)
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    assigned_to: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=sa_text("1"))


class ProjectBudget(ModelBase):
    __tablename__ = "project_budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    budget_type: Mapped[str] = mapped_column(String(50), nullable=False)
    planned_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), default=0)
    actual_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), default=0)
    variance: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), default=0)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProjectExpense(ModelBase):
    __tablename__ = "project_expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    expense_type: Mapped[str] = mapped_column(String(50), nullable=False)
    expense_date: Mapped[Date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    receipt_id: Mapped[int | None] = mapped_column(Integer)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProjectRevenue(ModelBase):
    __tablename__ = "project_revenues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    revenue_type: Mapped[str] = mapped_column(String(50), nullable=False)
    revenue_date: Mapped[Date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id", ondelete="SET NULL"))
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProjectDocument(ModelBase):
    __tablename__ = "project_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    file_type: Mapped[str | None] = mapped_column(String(50))
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProjectChangeOrder(ModelBase):
    __tablename__ = "project_change_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    change_order_number: Mapped[str | None] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    change_type: Mapped[str | None] = mapped_column(String(50), default="scope")
    cost_impact: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), default=0)
    time_impact_days: Mapped[int | None] = mapped_column(Integer, default=0)
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    requested_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    approved_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


__all__ = [
    "Project",
    "ProjectBudget",
    "ProjectChangeOrder",
    "ProjectDocument",
    "ProjectExpense",
    "ProjectRevenue",
    "ProjectTask",
]
