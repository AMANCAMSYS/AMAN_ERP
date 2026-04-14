from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase


class ProductConfiguration(ModelBase):
    __tablename__ = "product_configurations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ConfigOptionGroup(ModelBase):
    __tablename__ = "config_option_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    configuration_id: Mapped[int] = mapped_column(ForeignKey("product_configurations.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class ConfigOption(ModelBase):
    __tablename__ = "config_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("config_option_groups.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price_adjustment: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class ConfigValidationRule(ModelBase):
    __tablename__ = "config_validation_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    configuration_id: Mapped[int] = mapped_column(ForeignKey("product_configurations.id", ondelete="CASCADE"), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(20), nullable=False)  # requires, excludes
    source_option_id: Mapped[int] = mapped_column(ForeignKey("config_options.id", ondelete="CASCADE"), nullable=False)
    target_option_id: Mapped[int] = mapped_column(ForeignKey("config_options.id", ondelete="CASCADE"), nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(500))


class CpqPricingRule(ModelBase):
    __tablename__ = "cpq_pricing_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    configuration_id: Mapped[int] = mapped_column(ForeignKey("product_configurations.id", ondelete="CASCADE"), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(30), nullable=False)  # volume_discount, customer_discount, bundle_discount
    min_quantity: Mapped[int | None] = mapped_column(Integer)
    max_quantity: Mapped[int | None] = mapped_column(Integer)
    discount_percent: Mapped[float | None] = mapped_column(Numeric(5, 2))
    discount_amount: Mapped[float | None] = mapped_column(Numeric(18, 4))
    customer_group_id: Mapped[int | None] = mapped_column(ForeignKey("party_groups.id", ondelete="SET NULL"))
    priority: Mapped[int] = mapped_column(Integer, default=0)


class CpqQuote(ModelBase):
    __tablename__ = "cpq_quotes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("parties.id"), nullable=False)
    quotation_id: Mapped[int | None] = mapped_column(ForeignKey("sales_quotations.id", ondelete="SET NULL"))
    total_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    discount_total: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    final_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    pdf_path: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft, sent, accepted, expired, rejected
    valid_until: Mapped[str | None] = mapped_column(Date)


class CpqQuoteLine(ModelBase):
    __tablename__ = "cpq_quote_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quote_id: Mapped[int] = mapped_column(ForeignKey("cpq_quotes.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    selected_options: Mapped[dict | None] = mapped_column(JSONB)
    quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=1)
    base_unit_price: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    option_adjustments: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    discount_applied: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    final_unit_price: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    line_total: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)


__all__ = [
    "ProductConfiguration",
    "ConfigOptionGroup",
    "ConfigOption",
    "ConfigValidationRule",
    "CpqPricingRule",
    "CpqQuote",
    "CpqQuoteLine",
]
