from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import ModelBase


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
