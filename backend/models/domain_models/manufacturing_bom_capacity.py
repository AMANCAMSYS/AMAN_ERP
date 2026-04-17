from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase, SoftDeleteMixin


class BillOfMaterial(SoftDeleteMixin, ModelBase):
    __tablename__ = "bill_of_materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    code: Mapped[str | None] = mapped_column(String(50))
    name: Mapped[str | None] = mapped_column(String(255))
    yield_quantity: Mapped[float | None] = mapped_column(Numeric(15, 4), default=1.0)
    route_id: Mapped[int | None] = mapped_column(ForeignKey("manufacturing_routes.id"))
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BomOutput(SoftDeleteMixin, ModelBase):
    __tablename__ = "bom_outputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bom_id: Mapped[int | None] = mapped_column(ForeignKey("bill_of_materials.id", ondelete="CASCADE"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    cost_allocation_percentage: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BomComponent(SoftDeleteMixin, ModelBase):
    __tablename__ = "bom_components"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bom_id: Mapped[int | None] = mapped_column(ForeignKey("bill_of_materials.id", ondelete="CASCADE"))
    component_product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    waste_percentage: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    cost_share_percentage: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    is_percentage: Mapped[bool | None] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CapacityPlan(SoftDeleteMixin, ModelBase):
    __tablename__ = "capacity_plans"
    __table_args__ = (UniqueConstraint("work_center_id", "plan_date", name="capacity_plans_work_center_id_plan_date_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_center_id: Mapped[int | None] = mapped_column(ForeignKey("work_centers.id", ondelete="CASCADE"))
    plan_date: Mapped[Date] = mapped_column(Date, nullable=False)
    available_hours: Mapped[float | None] = mapped_column(Numeric(10, 2), default=8)
    planned_hours: Mapped[float | None] = mapped_column(Numeric(10, 2), default=0)
    actual_hours: Mapped[float | None] = mapped_column(Numeric(10, 2), default=0)
    efficiency_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


__all__ = [
    "BillOfMaterial",
    "BomComponent",
    "BomOutput",
    "CapacityPlan",
]
