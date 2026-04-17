from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase, AuditMixin, SoftDeleteMixin


class TrainingParticipant(AuditMixin, ModelBase):
    __tablename__ = "training_participants"
    __table_args__ = (UniqueConstraint("training_id", "employee_id", name="training_participants_training_id_employee_id_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    training_id: Mapped[int | None] = mapped_column(ForeignKey("training_programs.id", ondelete="CASCADE"))
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"))
    attendance_status: Mapped[str | None] = mapped_column(String(20), default="registered")
    certificate_issued: Mapped[bool | None] = mapped_column(Boolean, default=False)
    score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    feedback: Mapped[str | None] = mapped_column(Text)


class TrainingProgram(AuditMixin, SoftDeleteMixin, ModelBase):
    __tablename__ = "training_programs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    trainer: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))
    start_date: Mapped[Date | None] = mapped_column(Date)
    end_date: Mapped[Date | None] = mapped_column(Date)
    max_participants: Mapped[int | None] = mapped_column(Integer)
    cost: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    status: Mapped[str | None] = mapped_column(String(20), default="planned")


__all__ = [
    "TrainingParticipant",
    "TrainingProgram",
]
