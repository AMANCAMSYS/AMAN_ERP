from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, Boolean, String, func
from datetime import datetime
from typing import Optional


class ModelBase(DeclarativeBase):
    """Base class for ORM models used by Alembic autogenerate."""


class AuditMixin:
    """Mixin that adds created_at, updated_at timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class SoftDeleteMixin:
    """Mixin that adds soft-delete support."""
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False, index=True
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def soft_delete(self, user: str = None):
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by = user

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None

    @classmethod
    def active(cls):
        return cls.is_deleted == False

