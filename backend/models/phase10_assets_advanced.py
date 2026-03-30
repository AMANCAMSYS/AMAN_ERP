from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import ModelBase


class AssetDepreciationSchedule(ModelBase):
    __tablename__ = "asset_depreciation_schedule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"))
    fiscal_year: Mapped[int | None] = mapped_column(Integer)
    date: Mapped[Date | None] = mapped_column(Date)
    amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    accumulated_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    book_value: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    posted: Mapped[bool | None] = mapped_column(Boolean, default=False)
    journal_entry_id: Mapped[int | None] = mapped_column(ForeignKey("journal_entries.id", ondelete="SET NULL"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AssetDisposal(ModelBase):
    __tablename__ = "asset_disposals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"))
    disposal_date: Mapped[Date] = mapped_column(Date, nullable=False)
    disposal_method: Mapped[str | None] = mapped_column(String(50))
    disposal_value: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    disposal_reason: Mapped[str | None] = mapped_column(Text)
    buyer_name: Mapped[str | None] = mapped_column(String(255))
    buyer_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id", ondelete="SET NULL"))
    notes: Mapped[str | None] = mapped_column(Text)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id", ondelete="SET NULL"))
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AssetRevaluation(ModelBase):
    __tablename__ = "asset_revaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"))
    revaluation_date: Mapped[Date] = mapped_column(Date, nullable=False)
    old_value: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    new_value: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    difference: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    journal_entry_id: Mapped[int | None] = mapped_column(ForeignKey("journal_entries.id", ondelete="SET NULL"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AssetInsurance(ModelBase):
    __tablename__ = "asset_insurance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"))
    policy_number: Mapped[str | None] = mapped_column(String(100))
    insurer: Mapped[str | None] = mapped_column(String(255))
    coverage_type: Mapped[str | None] = mapped_column(String(100))
    premium_amount: Mapped[float | None] = mapped_column(Numeric(15, 2), default=0)
    coverage_amount: Mapped[float | None] = mapped_column(Numeric(15, 2), default=0)
    start_date: Mapped[Date | None] = mapped_column(Date)
    end_date: Mapped[Date | None] = mapped_column(Date)
    status: Mapped[str | None] = mapped_column(String(30), default="active")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AssetMaintenance(ModelBase):
    __tablename__ = "asset_maintenance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"))
    maintenance_type: Mapped[str | None] = mapped_column(String(50), default="preventive")
    description: Mapped[str | None] = mapped_column(Text)
    scheduled_date: Mapped[Date | None] = mapped_column(Date)
    completed_date: Mapped[Date | None] = mapped_column(Date)
    cost: Mapped[float | None] = mapped_column(Numeric(15, 2), default=0)
    vendor: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str | None] = mapped_column(String(30), default="scheduled")
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AssetImpairment(ModelBase):
    __tablename__ = "asset_impairments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    test_date: Mapped[Date] = mapped_column(Date, nullable=False)
    carrying_amount: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    recoverable_amount: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    impairment_loss: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    reason: Mapped[str | None] = mapped_column(Text)
    journal_entry_id: Mapped[int | None] = mapped_column(ForeignKey("journal_entries.id", ondelete="SET NULL"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
