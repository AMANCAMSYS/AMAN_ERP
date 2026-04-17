from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase, SoftDeleteMixin


class WorkCenter(SoftDeleteMixin, ModelBase):
    __tablename__ = "work_centers"
    __table_args__ = (UniqueConstraint("code", name="work_centers_code_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(50))
    capacity_per_day: Mapped[float | None] = mapped_column(Numeric(5, 2), default=8.0)
    cost_per_hour: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    location: Mapped[str | None] = mapped_column(String(100))
    cost_center_id: Mapped[int | None] = mapped_column(ForeignKey("cost_centers.id"))
    default_expense_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
    status: Mapped[str | None] = mapped_column(String(20), default="active")
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


__all__ = ["WorkCenter"]
