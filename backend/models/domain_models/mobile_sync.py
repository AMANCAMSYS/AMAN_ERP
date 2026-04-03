"""Mobile sync models: offline sync queue and conflict tracking."""

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import AuditMixin, ModelBase


class SyncQueue(ModelBase, AuditMixin):
    __tablename__ = "sync_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # quotation | sales_order | approval | inventory_adjustment
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    operation: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # create | update
    payload: Mapped[dict | None] = mapped_column(JSONB, default={})
    device_timestamp: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    server_timestamp: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sync_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending | synced | conflict | resolved
    conflict_resolution: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
