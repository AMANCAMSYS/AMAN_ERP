from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import ModelBase


class Budget(ModelBase):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    budget_code: Mapped[str | None] = mapped_column(String(50), unique=True)
    budget_name: Mapped[str | None] = mapped_column(String(255))
    budget_name_en: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    fiscal_year: Mapped[int | None] = mapped_column(Integer)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    cost_center_id: Mapped[int | None] = mapped_column(ForeignKey("cost_centers.id"))
    budget_type: Mapped[str | None] = mapped_column(String(30), default="annual")
    status: Mapped[str | None] = mapped_column(String(20), default="draft")
    total_budget: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    used_budget: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    remaining_budget: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    start_date: Mapped[Date | None] = mapped_column(Date)
    end_date: Mapped[Date | None] = mapped_column(Date)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BudgetItem(ModelBase):
    __tablename__ = "budget_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    budget_id: Mapped[int | None] = mapped_column(ForeignKey("budgets.id", ondelete="CASCADE"))
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
    planned_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    actual_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BudgetLine(ModelBase):
    __tablename__ = "budget_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    budget_id: Mapped[int | None] = mapped_column(ForeignKey("budgets.id", ondelete="CASCADE"))
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
    budget_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    used_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    remaining_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    percentage: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
