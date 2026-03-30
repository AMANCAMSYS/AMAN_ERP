from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import ModelBase


class Message(ModelBase):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender_id: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    receiver_id: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    subject: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str | None] = mapped_column(Text)
    message_type: Mapped[str | None] = mapped_column(String(50), default="internal")
    is_read: Mapped[bool | None] = mapped_column(Boolean, default=False)
    read_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MfgQcCheck(ModelBase):
    __tablename__ = "mfg_qc_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    production_order_id: Mapped[int | None] = mapped_column(ForeignKey("production_orders.id", ondelete="CASCADE"))
    operation_id: Mapped[int | None] = mapped_column(ForeignKey("manufacturing_operations.id"))
    check_name: Mapped[str] = mapped_column(String(200), nullable=False)
    check_type: Mapped[str | None] = mapped_column(String(30), default="visual")
    specification: Mapped[str | None] = mapped_column(Text)
    actual_value: Mapped[str | None] = mapped_column(String(200))
    result: Mapped[str | None] = mapped_column(String(20), default="pending")
    failure_action: Mapped[str | None] = mapped_column(String(20), default="warn")
    checked_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    notes: Mapped[str | None] = mapped_column(Text)
    checked_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MrpPlan(ModelBase):
    __tablename__ = "mrp_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_name: Mapped[str] = mapped_column(String(255), nullable=False)
    production_order_id: Mapped[int | None] = mapped_column(ForeignKey("production_orders.id", ondelete="CASCADE"))
    status: Mapped[str | None] = mapped_column(String(50), default="draft")
    calculated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))


class MrpItem(ModelBase):
    __tablename__ = "mrp_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mrp_plan_id: Mapped[int | None] = mapped_column(ForeignKey("mrp_plans.id", ondelete="CASCADE"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    required_quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    available_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    on_hand_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    on_order_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    shortage_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    lead_time_days: Mapped[int | None] = mapped_column(Integer, default=0)
    suggested_action: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str | None] = mapped_column(String(50), default="pending")


class Notification(ModelBase):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("company_users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    link: Mapped[str | None] = mapped_column(String(500))
    is_read: Mapped[bool | None] = mapped_column(Boolean, default=False)
    notification_type: Mapped[str | None] = mapped_column("type", String(50), default="info")
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    company_id: Mapped[str | None] = mapped_column(String(20))
    entity_id: Mapped[int | None] = mapped_column(Integer)
    entity_type: Mapped[str | None] = mapped_column(String(50))
    priority: Mapped[str | None] = mapped_column(String(20))
    read_at: Mapped[DateTime | None] = mapped_column(DateTime)