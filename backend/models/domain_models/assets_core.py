from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func, text as sa_text
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase


class AssetCategory(ModelBase):
    __tablename__ = "asset_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_code: Mapped[str | None] = mapped_column(String(50), unique=True)
    category_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category_name_en: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    depreciation_rate: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    useful_life: Mapped[int | None] = mapped_column(Integer, default=0)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("asset_categories.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Asset(ModelBase):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[str | None] = mapped_column(String(100))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(50), unique=True)
    type: Mapped[str | None] = mapped_column(String(50))
    purchase_date: Mapped[Date | None] = mapped_column(Date)
    cost: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    residual_value: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    life_years: Mapped[int | None] = mapped_column(Integer, default=0)
    currency: Mapped[str | None] = mapped_column(String(3))
    depreciation_method: Mapped[str | None] = mapped_column(String(50), default="straight_line")
    status: Mapped[str | None] = mapped_column(String(20), default="active")
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=sa_text("1"))


class AssetTransfer(ModelBase):
    __tablename__ = "asset_transfers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"))
    from_branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    to_branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    transfer_date: Mapped[Date] = mapped_column(Date, nullable=False, server_default=func.current_date())
    reason: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    book_value_at_transfer: Mapped[float | None] = mapped_column(Numeric(15, 2), default=0)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id", ondelete="SET NULL"))
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id", ondelete="SET NULL"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
