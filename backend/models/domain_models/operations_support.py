from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase


class LeaseContract(ModelBase):
    __tablename__ = "lease_contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id", ondelete="SET NULL"))
    description: Mapped[str | None] = mapped_column(Text)
    lessor_name: Mapped[str | None] = mapped_column(String(200))
    lease_type: Mapped[str | None] = mapped_column(String(30), default="operating")
    start_date: Mapped[Date | None] = mapped_column(Date)
    end_date: Mapped[Date | None] = mapped_column(Date)
    monthly_payment: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    total_payments: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    discount_rate: Mapped[float | None] = mapped_column(Numeric(8, 4), default=5.0)
    right_of_use_value: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    lease_liability: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    accumulated_depreciation: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    status: Mapped[str | None] = mapped_column(String(20), default="active")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


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


__all__ = [
    "LeaseContract",
    "MaintenanceLog",
    "MarketingCampaign",
]
