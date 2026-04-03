"""Three-way matching models: PO ↔ GRN ↔ Invoice."""

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import AuditMixin, ModelBase, SoftDeleteMixin


class MatchTolerance(ModelBase, AuditMixin, SoftDeleteMixin):
    __tablename__ = "match_tolerances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity_percent: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    quantity_absolute: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    price_percent: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    price_absolute: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id", ondelete="SET NULL"), nullable=True)
    product_category_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class ThreeWayMatch(ModelBase, AuditMixin, SoftDeleteMixin):
    __tablename__ = "three_way_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id", ondelete="RESTRICT"), nullable=False)
    invoice_id: Mapped[int] = mapped_column(Integer, nullable=False)
    match_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="matched"
    )  # matched | held | approved_with_exception | rejected
    matched_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    matched_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exception_approved_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exception_notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ThreeWayMatchLine(ModelBase, AuditMixin, SoftDeleteMixin):
    __tablename__ = "three_way_match_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("three_way_matches.id", ondelete="CASCADE"), nullable=False)
    po_line_id: Mapped[int] = mapped_column(ForeignKey("purchase_order_lines.id", ondelete="RESTRICT"), nullable=False)
    grn_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    invoice_line_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    po_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    received_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    invoiced_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    po_unit_price: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    invoiced_unit_price: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    quantity_variance_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    quantity_variance_abs: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    price_variance_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    price_variance_abs: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    tolerance_id: Mapped[int | None] = mapped_column(ForeignKey("match_tolerances.id", ondelete="SET NULL"), nullable=True)
    line_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="matched"
    )  # matched | quantity_mismatch | price_mismatch | both_mismatch


__all__ = [
    "MatchTolerance",
    "ThreeWayMatch",
    "ThreeWayMatchLine",
]
