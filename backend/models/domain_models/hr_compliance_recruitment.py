from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase


class EmployeeDocument(ModelBase):
    __tablename__ = "employee_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"))
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    document_number: Mapped[str | None] = mapped_column(String(100))
    issue_date: Mapped[Date | None] = mapped_column(Date)
    expiry_date: Mapped[Date | None] = mapped_column(Date)
    issuing_authority: Mapped[str | None] = mapped_column(String(255))
    file_url: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    alert_days: Mapped[int | None] = mapped_column(Integer, default=30)
    status: Mapped[str | None] = mapped_column(String(20), default="valid")
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EmployeeViolation(ModelBase):
    __tablename__ = "employee_violations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"))
    violation_date: Mapped[Date] = mapped_column(Date, nullable=False)
    violation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str | None] = mapped_column(String(20), default="minor")
    description: Mapped[str | None] = mapped_column(Text)
    action_taken: Mapped[str | None] = mapped_column(String(100))
    penalty_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    deduct_from_salary: Mapped[bool | None] = mapped_column(Boolean, default=False)
    payroll_period_id: Mapped[int | None] = mapped_column(ForeignKey("payroll_periods.id"))
    reported_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    status: Mapped[str | None] = mapped_column(String(20), default="open")
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EmployeeCustody(ModelBase):
    __tablename__ = "employee_custody"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"))
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    item_type: Mapped[str | None] = mapped_column(String(50))
    serial_number: Mapped[str | None] = mapped_column(String(100))
    assigned_date: Mapped[Date] = mapped_column(Date, nullable=False)
    return_date: Mapped[Date | None] = mapped_column(Date)
    condition_on_assign: Mapped[str | None] = mapped_column(String(50), default="new")
    condition_on_return: Mapped[str | None] = mapped_column(String(50))
    value: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(20), default="assigned")
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class JobOpening(ModelBase):
    __tablename__ = "job_openings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    position_id: Mapped[int | None] = mapped_column(ForeignKey("employee_positions.id", ondelete="SET NULL"))
    description: Mapped[str | None] = mapped_column(Text)
    requirements: Mapped[str | None] = mapped_column(Text)
    employment_type: Mapped[str | None] = mapped_column(String(50), default="full_time")
    vacancies: Mapped[int | None] = mapped_column(Integer, default=1)
    status: Mapped[str | None] = mapped_column(String(30), default="open")
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    published_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    closing_date: Mapped[Date | None] = mapped_column(Date)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class JobApplication(ModelBase):
    __tablename__ = "job_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opening_id: Mapped[int | None] = mapped_column(ForeignKey("job_openings.id"))
    applicant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    resume_url: Mapped[str | None] = mapped_column(Text)
    cover_letter: Mapped[str | None] = mapped_column(Text)
    stage: Mapped[str | None] = mapped_column(String(50), default="applied")
    rating: Mapped[int | None] = mapped_column(Integer, default=0)
    interview_date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    interviewer_id: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(30), default="pending")
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


__all__ = [
    "EmployeeCustody",
    "EmployeeDocument",
    "EmployeeViolation",
    "JobApplication",
    "JobOpening",
]
