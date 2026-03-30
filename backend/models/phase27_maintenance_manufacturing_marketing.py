from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import ModelBase


class MaintenanceLog(ModelBase):
    __tablename__ = "maintenance_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    equipment_id: Mapped[int | None] = mapped_column(ForeignKey("manufacturing_equipment.id", ondelete="CASCADE"))
    maintenance_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    cost: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    performed_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    external_service_provider: Mapped[str | None] = mapped_column(String(255))
    maintenance_date: Mapped[Date] = mapped_column(Date, nullable=False)
    next_due_date: Mapped[Date | None] = mapped_column(Date)
    status: Mapped[str | None] = mapped_column(String(20), default="completed")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ManufacturingEquipment(ModelBase):
    __tablename__ = "manufacturing_equipment"
    __table_args__ = (UniqueConstraint("code", name="manufacturing_equipment_code_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(50))
    work_center_id: Mapped[int | None] = mapped_column(ForeignKey("work_centers.id"))
    status: Mapped[str | None] = mapped_column(String(20), default="active")
    purchase_date: Mapped[Date | None] = mapped_column(Date)
    last_maintenance_date: Mapped[Date | None] = mapped_column(Date)
    next_maintenance_date: Mapped[Date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ManufacturingOperation(ModelBase):
    __tablename__ = "manufacturing_operations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route_id: Mapped[int | None] = mapped_column(ForeignKey("manufacturing_routes.id", ondelete="CASCADE"))
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    work_center_id: Mapped[int | None] = mapped_column(ForeignKey("work_centers.id"))
    description: Mapped[str | None] = mapped_column(String(255))
    setup_time: Mapped[float | None] = mapped_column(Numeric(8, 2), default=0)
    cycle_time: Mapped[float | None] = mapped_column(Numeric(8, 2), default=0)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ManufacturingRoute(ModelBase):
    __tablename__ = "manufacturing_routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MarketingCampaign(ModelBase):
    __tablename__ = "marketing_campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    campaign_type: Mapped[str | None] = mapped_column(String(50), default="email")
    status: Mapped[str | None] = mapped_column(String(50), default="draft")
    start_date: Mapped[Date | None] = mapped_column(Date)
    end_date: Mapped[Date | None] = mapped_column(Date)
    budget: Mapped[float | None] = mapped_column(Numeric(15, 2), default=0)
    spent: Mapped[float | None] = mapped_column(Numeric(15, 2), default=0)
    target_audience: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    sent_count: Mapped[int | None] = mapped_column(Integer, default=0)
    open_count: Mapped[int | None] = mapped_column(Integer, default=0)
    click_count: Mapped[int | None] = mapped_column(Integer, default=0)
    conversion_count: Mapped[int | None] = mapped_column(Integer, default=0)
    branch_id: Mapped[int | None] = mapped_column(Integer)
    created_by: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())