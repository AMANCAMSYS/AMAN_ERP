from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase


class ContractAmendment(ModelBase):
    __tablename__ = "contract_amendments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_id: Mapped[int | None] = mapped_column(ForeignKey("contracts.id", ondelete="CASCADE"))
    amendment_type: Mapped[str | None] = mapped_column(String(50), default="value_change")
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    effective_date: Mapped[Date | None] = mapped_column(Date)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CrmContact(ModelBase):
    __tablename__ = "crm_contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"))
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100))
    job_title: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(150))
    phone: Mapped[str | None] = mapped_column(String(30))
    mobile: Mapped[str | None] = mapped_column(String(30))
    department: Mapped[str | None] = mapped_column(String(100))
    is_primary: Mapped[bool | None] = mapped_column(Boolean, default=False)
    is_decision_maker: Mapped[bool | None] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CrmKnowledgeBase(ModelBase):
    __tablename__ = "crm_knowledge_base"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), default="general")
    content: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[str | None] = mapped_column(Text)
    is_published: Mapped[bool | None] = mapped_column(Boolean, default=False)
    views: Mapped[int | None] = mapped_column(Integer, default=0)
    helpful_count: Mapped[int | None] = mapped_column(Integer, default=0)
    created_by: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CustomerGroup(ModelBase):
    __tablename__ = "customer_groups"
    __table_args__ = (UniqueConstraint("group_code", name="customer_groups_group_code_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_code: Mapped[str | None] = mapped_column(String(50))
    group_name: Mapped[str] = mapped_column(String(255), nullable=False)
    group_name_en: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("customer_groups.id"))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    discount_percentage: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    effect_type: Mapped[str | None] = mapped_column(String(20), default="discount")
    application_scope: Mapped[str | None] = mapped_column(String(20), default="total")
    price_list_id: Mapped[int | None] = mapped_column(ForeignKey("customer_price_lists.id", ondelete="SET NULL"))
    payment_days: Mapped[int | None] = mapped_column(Integer, default=30)
    status: Mapped[str | None] = mapped_column(String(20), default="active")
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


__all__ = [
    "ContractAmendment",
    "CrmContact",
    "CrmKnowledgeBase",
    "CustomerGroup",
]
