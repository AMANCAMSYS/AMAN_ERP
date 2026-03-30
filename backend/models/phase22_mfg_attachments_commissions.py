from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import ModelBase


class Attachment(ModelBase):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer, default=0)
    file_type: Mapped[str | None] = mapped_column(String(50))
    mime_type: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BillOfMaterial(ModelBase):
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


class BomOutput(ModelBase):
    __tablename__ = "bom_outputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bom_id: Mapped[int | None] = mapped_column(ForeignKey("bill_of_materials.id", ondelete="CASCADE"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    cost_allocation_percentage: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CheckStatusLog(ModelBase):
    __tablename__ = "check_status_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    check_type: Mapped[str] = mapped_column(String(20), nullable=False)
    check_id: Mapped[int] = mapped_column(Integer, nullable=False)
    old_status: Mapped[str | None] = mapped_column(String(30))
    new_status: Mapped[str] = mapped_column(String(30), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    changed_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    changed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommissionRule(ModelBase):
    __tablename__ = "commission_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    salesperson_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id", ondelete="SET NULL"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("product_categories.id", ondelete="SET NULL"))
    rate_type: Mapped[str | None] = mapped_column(String(20), default="percentage")
    rate: Mapped[float | None] = mapped_column(Numeric(10, 4), default=0)
    min_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    max_amount: Mapped[float | None] = mapped_column(Numeric(18, 4))
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
