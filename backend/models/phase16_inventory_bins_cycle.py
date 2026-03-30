from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import ModelBase


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
