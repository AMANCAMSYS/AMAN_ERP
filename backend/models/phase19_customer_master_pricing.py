from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import ModelBase


class Customer(ModelBase):
    __tablename__ = "customers"
    __table_args__ = (UniqueConstraint("customer_code", name="customers_customer_code_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_code: Mapped[str | None] = mapped_column(String(50))
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_name_en: Mapped[str | None] = mapped_column(String(255))
    customer_type: Mapped[str | None] = mapped_column(String(50), default="individual")
    tax_number: Mapped[str | None] = mapped_column(String(50))
    commercial_register: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    mobile: Mapped[str | None] = mapped_column(String(50))
    fax: Mapped[str | None] = mapped_column(String(50))
    website: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    customer_group_id: Mapped[int | None] = mapped_column(ForeignKey("customer_groups.id"))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    payment_terms: Mapped[str | None] = mapped_column(String(100))
    credit_limit: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    current_balance: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    currency: Mapped[str | None] = mapped_column(String(3))
    price_list_id: Mapped[int | None] = mapped_column(ForeignKey("customer_price_lists.id", ondelete="SET NULL"))
    tax_exempt: Mapped[bool | None] = mapped_column(Boolean, default=False)
    status: Mapped[str | None] = mapped_column(String(20), default="active")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CustomerContact(ModelBase):
    __tablename__ = "customer_contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"))
    contact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_name_en: Mapped[str | None] = mapped_column(String(255))
    position: Mapped[str | None] = mapped_column(String(100))
    department: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    mobile: Mapped[str | None] = mapped_column(String(50))
    is_primary: Mapped[bool | None] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CustomerBankAccount(ModelBase):
    __tablename__ = "customer_bank_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"))
    bank_name: Mapped[str] = mapped_column(String(255), nullable=False)
    bank_name_en: Mapped[str | None] = mapped_column(String(255))
    account_number: Mapped[str | None] = mapped_column(String(50))
    iban: Mapped[str | None] = mapped_column(String(50))
    swift_code: Mapped[str | None] = mapped_column(String(20))
    branch_name: Mapped[str | None] = mapped_column(String(255))
    account_holder: Mapped[str | None] = mapped_column(String(255))
    is_default: Mapped[bool | None] = mapped_column(Boolean, default=False)
    status: Mapped[str | None] = mapped_column(String(20), default="active")
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CustomerPriceList(ModelBase):
    __tablename__ = "customer_price_lists"
    __table_args__ = (UniqueConstraint("price_list_code", name="customer_price_lists_price_list_code_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    price_list_code: Mapped[str | None] = mapped_column(String(50))
    price_list_name: Mapped[str] = mapped_column(String(255), nullable=False)
    price_list_name_en: Mapped[str | None] = mapped_column(String(255))
    customer_group_id: Mapped[int | None] = mapped_column(ForeignKey("customer_groups.id"))
    currency: Mapped[str | None] = mapped_column(String(3))
    discount_type: Mapped[str | None] = mapped_column(String(20), default="percentage")
    discount_value: Mapped[float | None] = mapped_column(Numeric(10, 4), default=0)
    valid_from: Mapped[Date | None] = mapped_column(Date)
    valid_to: Mapped[Date | None] = mapped_column(Date)
    status: Mapped[str | None] = mapped_column(String(20), default="active")
    is_default: Mapped[bool | None] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CustomerPriceListItem(ModelBase):
    __tablename__ = "customer_price_list_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    price_list_id: Mapped[int] = mapped_column(ForeignKey("customer_price_lists.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
