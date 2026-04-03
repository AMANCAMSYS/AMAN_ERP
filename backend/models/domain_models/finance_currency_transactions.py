from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase


class CurrencyTransaction(ModelBase):
    __tablename__ = "currency_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    transaction_id: Mapped[int] = mapped_column(Integer, nullable=False)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    exchange_rate: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    amount_fc: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    amount_bc: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


__all__ = ["CurrencyTransaction"]
