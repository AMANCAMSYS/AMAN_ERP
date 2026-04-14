from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase


class DemandForecast(ModelBase):
    __tablename__ = "demand_forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"), nullable=True)
    forecast_method: Mapped[str] = mapped_column(String(50), nullable=False)
    generated_date: Mapped[object] = mapped_column(Date, nullable=False)
    generated_by: Mapped[int] = mapped_column(ForeignKey("company_users.id"), nullable=False)
    history_months_used: Mapped[int] = mapped_column(Integer, nullable=False)


class DemandForecastPeriod(ModelBase):
    __tablename__ = "demand_forecast_periods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    forecast_id: Mapped[int] = mapped_column(ForeignKey("demand_forecasts.id", ondelete="CASCADE"), nullable=False)
    period_start: Mapped[object] = mapped_column(Date, nullable=False)
    period_end: Mapped[object] = mapped_column(Date, nullable=False)
    projected_quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    confidence_lower: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    confidence_upper: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    manual_adjustment: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    adjusted_quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
