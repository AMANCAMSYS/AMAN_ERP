from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase


class BatchSerialMovement(ModelBase):
    __tablename__ = "batch_serial_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("product_batches.id"))
    serial_id: Mapped[int | None] = mapped_column(ForeignKey("product_serials.id"))
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    movement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(50))
    reference_id: Mapped[int | None] = mapped_column(Integer)
    quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=1)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CycleCount(ModelBase):
    __tablename__ = "cycle_counts"
    __table_args__ = (UniqueConstraint("count_number", name="cycle_counts_count_number_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    count_number: Mapped[str | None] = mapped_column(String(50))
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
    count_type: Mapped[str | None] = mapped_column(String(50), default="full")
    status: Mapped[str | None] = mapped_column(String(20), default="draft")
    scheduled_date: Mapped[Date | None] = mapped_column(Date)
    start_date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    total_items: Mapped[int | None] = mapped_column(Integer, default=0)
    counted_items: Mapped[int | None] = mapped_column(Integer, default=0)
    variance_items: Mapped[int | None] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CycleCountItem(ModelBase):
    __tablename__ = "cycle_count_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cycle_count_id: Mapped[int] = mapped_column(ForeignKey("cycle_counts.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("product_batches.id"))
    system_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    counted_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4))
    variance: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    variance_value: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    unit_cost: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    counted_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    counted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)


class BinLocation(ModelBase):
    __tablename__ = "bin_locations"
    __table_args__ = (UniqueConstraint("warehouse_id", "bin_code", name="bin_locations_warehouse_id_bin_code_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)
    bin_code: Mapped[str] = mapped_column(String(50), nullable=False)
    bin_name: Mapped[str | None] = mapped_column(String(100))
    zone: Mapped[str | None] = mapped_column(String(50))
    aisle: Mapped[str | None] = mapped_column(String(20))
    rack: Mapped[str | None] = mapped_column(String(20))
    shelf: Mapped[str | None] = mapped_column(String(20))
    position: Mapped[str | None] = mapped_column(String(20))
    bin_type: Mapped[str | None] = mapped_column(String(30), default="storage")
    max_weight: Mapped[float | None] = mapped_column(Numeric(10, 2))
    max_volume: Mapped[float | None] = mapped_column(Numeric(10, 2))
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BinInventory(ModelBase):
    __tablename__ = "bin_inventory"
    __table_args__ = (
        UniqueConstraint("bin_id", "product_id", "batch_id", name="bin_inventory_bin_id_product_id_batch_id_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bin_id: Mapped[int] = mapped_column(ForeignKey("bin_locations.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("product_batches.id"))
    quantity: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


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


class ProductBatch(ModelBase):
    __tablename__ = "product_batches"
    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "warehouse_id",
            "batch_number",
            name="product_batches_product_id_warehouse_id_batch_number_key",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
    batch_number: Mapped[str] = mapped_column(String(100), nullable=False)
    manufacturing_date: Mapped[Date | None] = mapped_column(Date)
    expiry_date: Mapped[Date | None] = mapped_column(Date)
    quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    available_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    unit_cost: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id", ondelete="SET NULL"))
    reference_type: Mapped[str | None] = mapped_column(String(50))
    reference_id: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str | None] = mapped_column(String(20), default="active")
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProductSerial(ModelBase):
    __tablename__ = "product_serials"
    __table_args__ = (
        UniqueConstraint("product_id", "serial_number", name="product_serials_product_id_serial_number_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    serial_number: Mapped[str] = mapped_column(String(200), nullable=False)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("product_batches.id"))
    status: Mapped[str | None] = mapped_column(String(20), default="available")
    purchase_date: Mapped[Date | None] = mapped_column(Date)
    purchase_reference: Mapped[str | None] = mapped_column(String(100))
    purchase_price: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    sale_date: Mapped[Date | None] = mapped_column(Date)
    sale_reference: Mapped[str | None] = mapped_column(String(100))
    sale_price: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"))
    warranty_start: Mapped[Date | None] = mapped_column(Date)
    warranty_end: Mapped[Date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class QualityInspection(ModelBase):
    __tablename__ = "quality_inspections"
    __table_args__ = (UniqueConstraint("inspection_number", name="quality_inspections_inspection_number_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inspection_number: Mapped[str | None] = mapped_column(String(50))
    inspection_type: Mapped[str] = mapped_column(String(50), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("product_batches.id"))
    reference_type: Mapped[str | None] = mapped_column(String(50))
    reference_id: Mapped[int | None] = mapped_column(Integer)
    inspected_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    accepted_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    rejected_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    result_notes: Mapped[str | None] = mapped_column(Text)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    inspector_id: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    inspection_date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class QualityInspectionCriteria(ModelBase):
    __tablename__ = "quality_inspection_criteria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inspection_id: Mapped[int] = mapped_column(ForeignKey("quality_inspections.id", ondelete="CASCADE"), nullable=False)
    criteria_name: Mapped[str] = mapped_column(String(255), nullable=False)
    expected_value: Mapped[str | None] = mapped_column(String(255))
    actual_value: Mapped[str | None] = mapped_column(String(255))
    is_passed: Mapped[bool | None] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)


class ProductKitItem(ModelBase):
    __tablename__ = "product_kit_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kit_id: Mapped[int] = mapped_column(ForeignKey("product_kits.id", ondelete="CASCADE"), nullable=False)
    component_product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False, default=1)
    unit_cost: Mapped[float | None] = mapped_column(Numeric(15, 2))
    sort_order: Mapped[int | None] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text)


__all__ = [
    "BatchSerialMovement",
    "BinInventory",
    "BinLocation",
    "CycleCount",
    "CycleCountItem",
    "ProductAttribute",
    "ProductAttributeValue",
    "ProductBatch",
    "ProductKit",
    "ProductKitItem",
    "ProductSerial",
    "ProductVariant",
    "ProductVariantAttribute",
    "QualityInspection",
    "QualityInspectionCriteria",
]
