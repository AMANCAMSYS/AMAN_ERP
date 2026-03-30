from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import ModelBase


class CostCenter(ModelBase):
    __tablename__ = "cost_centers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    center_code: Mapped[str | None] = mapped_column(String(50), unique=True)
    center_name: Mapped[str] = mapped_column(String(255), nullable=False)
    center_name_en: Mapped[str | None] = mapped_column(String(255))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    budget: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    currency: Mapped[str | None] = mapped_column(String(3))
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CostCenterBudget(ModelBase):
    __tablename__ = "cost_centers_budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cost_center_id: Mapped[int | None] = mapped_column(ForeignKey("cost_centers.id"))
    budget_id: Mapped[int | None] = mapped_column(ForeignKey("budgets.id"))
    allocated_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    used_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    fiscal_year: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CostingPolicy(ModelBase):
    __tablename__ = "costing_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    policy_name: Mapped[str] = mapped_column(String(100), nullable=False)
    policy_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[int | None] = mapped_column(Integer)
    updated_by: Mapped[int | None] = mapped_column(Integer)


class CostingPolicyDetail(ModelBase):
    __tablename__ = "costing_policy_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    policy_id: Mapped[int] = mapped_column(ForeignKey("costing_policies.id", ondelete="CASCADE"), nullable=False)
    setting_key: Mapped[str] = mapped_column(String(100), nullable=False)
    setting_value: Mapped[str | None] = mapped_column(String(500))


class CostingPolicyHistory(ModelBase):
    __tablename__ = "costing_policy_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    old_policy_type: Mapped[str | None] = mapped_column(String(50))
    new_policy_type: Mapped[str | None] = mapped_column(String(50))
    change_date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    changed_by: Mapped[int | None] = mapped_column(Integer)
    reason: Mapped[str | None] = mapped_column(Text)
    affected_products_count: Mapped[int | None] = mapped_column(Integer)
    total_cost_impact: Mapped[float | None] = mapped_column(Numeric(18, 4))
    status: Mapped[str | None] = mapped_column(String(20), default="completed")


class InventoryCostSnapshot(ModelBase):
    __tablename__ = "inventory_cost_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id", ondelete="SET NULL"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"))
    average_cost: Mapped[float | None] = mapped_column(Numeric(18, 4))
    quantity: Mapped[float | None] = mapped_column(Numeric(18, 4))
    policy_type: Mapped[str | None] = mapped_column(String(50))
    snapshot_date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
