from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase


class TaskDependency(ModelBase):
    __tablename__ = "task_dependencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey("project_tasks.id", ondelete="CASCADE"), nullable=False)
    depends_on_task_id: Mapped[int] = mapped_column(ForeignKey("project_tasks.id", ondelete="CASCADE"), nullable=False)
    dependency_type: Mapped[str | None] = mapped_column(String(20), default="finish_to_start")
    lag_days: Mapped[int | None] = mapped_column(Integer, default=0)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


__all__ = ["TaskDependency"]
