"""Intercompany accounting entities: entity groups, IC transactions, account mappings."""

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..base import AuditMixin, ModelBase, SoftDeleteMixin


class EntityGroup(ModelBase, AuditMixin, SoftDeleteMixin):
    __tablename__ = "entity_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("entity_groups.id", ondelete="SET NULL"), nullable=True
    )
    company_id: Mapped[str] = mapped_column(String(100), nullable=False)
    group_currency: Mapped[str] = mapped_column(String(10), nullable=False, server_default="SAR")
    consolidation_level: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")


class IntercompanyTransactionV2(ModelBase, AuditMixin, SoftDeleteMixin):
    """Structured intercompany transaction with reciprocal JE tracking and elimination."""
    __tablename__ = "intercompany_transactions_v2"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_entity_id: Mapped[int] = mapped_column(
        ForeignKey("entity_groups.id", ondelete="RESTRICT"), nullable=False
    )
    target_entity_id: Mapped[int] = mapped_column(
        ForeignKey("entity_groups.id", ondelete="RESTRICT"), nullable=False
    )
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_amount: Mapped[object] = mapped_column(Numeric(18, 4), nullable=False)
    source_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    target_amount: Mapped[object] = mapped_column(Numeric(18, 4), nullable=False)
    target_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    exchange_rate: Mapped[object] = mapped_column(Numeric(18, 8), nullable=False, server_default="1")
    source_journal_entry_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_journal_entry_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    elimination_status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="pending"
    )
    elimination_journal_entry_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reference_document: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        CheckConstraint("source_entity_id != target_entity_id", name="ck_ic_txn_diff_entities"),
    )


class IntercompanyAccountMapping(ModelBase, AuditMixin, SoftDeleteMixin):
    __tablename__ = "intercompany_account_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_entity_id: Mapped[int] = mapped_column(
        ForeignKey("entity_groups.id", ondelete="CASCADE"), nullable=False
    )
    target_entity_id: Mapped[int] = mapped_column(
        ForeignKey("entity_groups.id", ondelete="CASCADE"), nullable=False
    )
    source_account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    target_account_id: Mapped[int] = mapped_column(Integer, nullable=False)
