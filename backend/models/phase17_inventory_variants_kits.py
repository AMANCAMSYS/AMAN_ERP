from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import ModelBase


class ProductAttribute(ModelBase):
    __tablename__ = "product_attributes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attribute_name: Mapped[str] = mapped_column(String(100), nullable=False)
    attribute_name_en: Mapped[str | None] = mapped_column(String(100))
    attribute_type: Mapped[str | None] = mapped_column(String(50), default="select")
    sort_order: Mapped[int | None] = mapped_column(Integer, default=0)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProductAttributeValue(ModelBase):
    __tablename__ = "product_attribute_values"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attribute_id: Mapped[int] = mapped_column(ForeignKey("product_attributes.id", ondelete="CASCADE"), nullable=False)
    value_name: Mapped[str] = mapped_column(String(100), nullable=False)
    value_name_en: Mapped[str | None] = mapped_column(String(100))
    color_code: Mapped[str | None] = mapped_column(String(20))
    sort_order: Mapped[int | None] = mapped_column(Integer, default=0)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProductVariant(ModelBase):
    __tablename__ = "product_variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    variant_code: Mapped[str | None] = mapped_column(String(100))
    variant_name: Mapped[str | None] = mapped_column(String(255))
    sku: Mapped[str | None] = mapped_column(String(100))
    barcode: Mapped[str | None] = mapped_column(String(100))
    cost_price: Mapped[float | None] = mapped_column(Numeric(15, 2), default=0)
    selling_price: Mapped[float | None] = mapped_column(Numeric(15, 2), default=0)
    weight: Mapped[float | None] = mapped_column(Numeric(10, 3))
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProductVariantAttribute(ModelBase):
    __tablename__ = "product_variant_attributes"
    __table_args__ = (
        UniqueConstraint("variant_id", "attribute_id", name="product_variant_attributes_variant_id_attribute_id_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False)
    attribute_id: Mapped[int] = mapped_column(ForeignKey("product_attributes.id"), nullable=False)
    attribute_value_id: Mapped[int] = mapped_column(ForeignKey("product_attribute_values.id"), nullable=False)


class ProductKit(ModelBase):
    __tablename__ = "product_kits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    kit_name: Mapped[str | None] = mapped_column(String(200))
    kit_type: Mapped[str | None] = mapped_column(String(30), default="fixed")
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
