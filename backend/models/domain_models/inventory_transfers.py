from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase


class StockShipmentItem(ModelBase):
    __tablename__ = "stock_shipment_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shipment_id: Mapped[int | None] = mapped_column(ForeignKey("stock_shipments.id", ondelete="CASCADE"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)


class StockShipment(ModelBase):
    __tablename__ = "stock_shipments"
    __table_args__ = (UniqueConstraint("shipment_ref", name="stock_shipments_shipment_ref_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shipment_ref: Mapped[str | None] = mapped_column(String(50))
    source_warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    destination_warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    shipped_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    received_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))


class StockTransferLog(ModelBase):
    __tablename__ = "stock_transfer_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shipment_id: Mapped[int | None] = mapped_column(ForeignKey("stock_shipments.id", ondelete="SET NULL"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    from_warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    to_warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    transfer_cost: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    from_avg_cost_before: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    to_avg_cost_before: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    to_avg_cost_after: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


__all__ = [
    "StockShipmentItem",
    "StockShipment",
    "StockTransferLog",
]
