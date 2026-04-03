"""FIFO/LIFO cost layer models for inventory costing."""

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..base import AuditMixin, ModelBase, SoftDeleteMixin


class CostLayer(ModelBase, AuditMixin, SoftDeleteMixin):
    __tablename__ = "cost_layers"
    __table_args__ = (
        CheckConstraint("remaining_quantity >= 0", name="ck_cost_layers_remaining_qty_non_negative"),
        Index("ix_cost_layers_product_wh_exhausted_date", "product_id", "warehouse_id", "is_exhausted", "purchase_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False)
    costing_method: Mapped[str] = mapped_column(String(10), nullable=False)  # "fifo" or "lifo"
    purchase_date: Mapped[Date] = mapped_column(Date, nullable=False)
    original_quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    remaining_quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    source_document_type: Mapped[str] = mapped_column(String(30), nullable=False)  # purchase_invoice, opening_balance, return, adjustment
    source_document_id: Mapped[int | None] = mapped_column(Integer)
    is_exhausted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


class CostLayerConsumption(ModelBase, AuditMixin, SoftDeleteMixin):
    __tablename__ = "cost_layer_consumptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cost_layer_id: Mapped[int] = mapped_column(ForeignKey("cost_layers.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity_consumed: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    sale_document_type: Mapped[str] = mapped_column(String(30), nullable=False)  # sales_invoice, pos_order, adjustment
    sale_document_id: Mapped[int | None] = mapped_column(Integer)
    consumed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


__all__ = [
    "CostLayer",
    "CostLayerConsumption",
]
