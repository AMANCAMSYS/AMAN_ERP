"""Cash flow forecast models."""

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..base import AuditMixin, ModelBase, SoftDeleteMixin


class CashFlowForecast(ModelBase, AuditMixin, SoftDeleteMixin):
    __tablename__ = "cashflow_forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    forecast_date: Mapped[Date] = mapped_column(Date, nullable=False, server_default=func.current_date())
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="90")
    mode: Mapped[str] = mapped_column(String(20), nullable=False, server_default="'contractual'")
    generated_by: Mapped[int | None] = mapped_column(
        ForeignKey("company_users.id", ondelete="SET NULL"), nullable=True
    )


class CashFlowForecastLine(ModelBase, AuditMixin, SoftDeleteMixin):
    __tablename__ = "cashflow_forecast_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    forecast_id: Mapped[int] = mapped_column(
        ForeignKey("cashflow_forecasts.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[Date] = mapped_column(Date, nullable=False)
    bank_account_id: Mapped[int | None] = mapped_column(
        ForeignKey("treasury_accounts.id", ondelete="SET NULL"), nullable=True
    )
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_document_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    projected_inflow: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, server_default="0")
    projected_outflow: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, server_default="0")
    projected_balance: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, server_default="0")


__all__ = [
    "CashFlowForecast",
    "CashFlowForecastLine",
]
