from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func, text as sa_text
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase, AuditMixin, SoftDeleteMixin


class PayrollPeriod(AuditMixin, ModelBase):
    __tablename__ = "payroll_periods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Date] = mapped_column(Date, nullable=False)
    payment_date: Mapped[Date | None] = mapped_column(Date)
    status: Mapped[str | None] = mapped_column(String(20), default="draft")


class Department(AuditMixin, SoftDeleteMixin, ModelBase):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    department_code: Mapped[str | None] = mapped_column(String(50), unique=True)
    department_name: Mapped[str] = mapped_column(String(255), nullable=False)
    department_name_en: Mapped[str | None] = mapped_column(String(255))
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    manager_id: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)


class EmployeePosition(AuditMixin, SoftDeleteMixin, ModelBase):
    __tablename__ = "employee_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    position_code: Mapped[str | None] = mapped_column(String(50), unique=True)
    position_name: Mapped[str] = mapped_column(String(255), nullable=False)
    position_name_en: Mapped[str | None] = mapped_column(String(255))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    description: Mapped[str | None] = mapped_column(Text)
    level: Mapped[int | None] = mapped_column(Integer, default=1)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)


class Employee(AuditMixin, SoftDeleteMixin, ModelBase):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_code: Mapped[str | None] = mapped_column(String(50), unique=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    first_name_en: Mapped[str | None] = mapped_column(String(100))
    last_name_en: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    mobile: Mapped[str | None] = mapped_column(String(50))
    gender: Mapped[str | None] = mapped_column(String(10))
    birth_date: Mapped[Date | None] = mapped_column(Date)
    hire_date: Mapped[Date | None] = mapped_column(Date)
    termination_date: Mapped[Date | None] = mapped_column(Date)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    position_id: Mapped[int | None] = mapped_column(ForeignKey("employee_positions.id"))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    employment_type: Mapped[str | None] = mapped_column(String(50), default="full_time")
    status: Mapped[str | None] = mapped_column(String(20), default="active")
    salary: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    housing_allowance: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    transport_allowance: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    other_allowances: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    hourly_cost: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    currency: Mapped[str | None] = mapped_column(String(3))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
    bank_account_id: Mapped[int | None] = mapped_column(ForeignKey("treasury_accounts.id", ondelete="SET NULL"))
    tax_id: Mapped[str | None] = mapped_column(String(50))
    social_security: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(Text)
    emergency_contact: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    nationality: Mapped[str | None] = mapped_column(String(100))
    is_saudi: Mapped[bool | None] = mapped_column(Boolean, default=False)
    eos_eligible: Mapped[bool | None] = mapped_column(Boolean, default=True)
    eos_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    iqama_number: Mapped[str | None] = mapped_column(String(50))
    iqama_expiry: Mapped[Date | None] = mapped_column(Date)
    passport_number: Mapped[str | None] = mapped_column(String(50))
    sponsor: Mapped[str | None] = mapped_column(String(255))
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=sa_text("1"))


class Attendance(AuditMixin, ModelBase):
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    date: Mapped[Date] = mapped_column(Date, nullable=False)
    check_in: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    check_out: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str | None] = mapped_column(String(20), default="present")
    notes: Mapped[str | None] = mapped_column(Text)


class EmployeeLoan(AuditMixin, SoftDeleteMixin, ModelBase):
    __tablename__ = "employee_loans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    total_installments: Mapped[int | None] = mapped_column(Integer, default=1)
    monthly_installment: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    paid_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    start_date: Mapped[Date | None] = mapped_column(Date)
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    reason: Mapped[str | None] = mapped_column(Text)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))


class LeaveRequest(AuditMixin, SoftDeleteMixin, ModelBase):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    leave_type: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Date] = mapped_column(Date, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    attachment_url: Mapped[str | None] = mapped_column(Text)


class SalaryStructure(AuditMixin, SoftDeleteMixin, ModelBase):
    __tablename__ = "salary_structures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    base_type: Mapped[str | None] = mapped_column(String(50), default="monthly")
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)


class SalaryComponent(AuditMixin, SoftDeleteMixin, ModelBase):
    __tablename__ = "salary_components"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(255))
    component_type: Mapped[str] = mapped_column(String(20), nullable=False)
    calculation_type: Mapped[str] = mapped_column(String(20), nullable=False, default="fixed")
    percentage_of: Mapped[str | None] = mapped_column(String(50))
    percentage_value: Mapped[float | None] = mapped_column(Numeric(8, 4), default=0)
    formula: Mapped[str | None] = mapped_column(Text)
    is_taxable: Mapped[bool | None] = mapped_column(Boolean, default=True)
    is_gosi_applicable: Mapped[bool | None] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int | None] = mapped_column(Integer, default=0)
    structure_id: Mapped[int | None] = mapped_column(ForeignKey("salary_structures.id", ondelete="SET NULL"))


class EmployeeSalaryComponent(AuditMixin, ModelBase):
    __tablename__ = "employee_salary_components"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"))
    component_id: Mapped[int | None] = mapped_column(ForeignKey("salary_components.id", ondelete="CASCADE"))
    amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    effective_date: Mapped[Date | None] = mapped_column(Date)


class PayrollEntry(AuditMixin, ModelBase):
    __tablename__ = "payroll_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    period_id: Mapped[int | None] = mapped_column(ForeignKey("payroll_periods.id", ondelete="CASCADE"))
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    basic_salary: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    housing_allowance: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    transport_allowance: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    other_allowances: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    salary_components_earning: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    salary_components_deduction: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    overtime_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    gosi_employee_share: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    gosi_employer_share: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    violation_deduction: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    loan_deduction: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    deductions: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    net_salary: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    currency: Mapped[str | None] = mapped_column(String(3))
    exchange_rate: Mapped[float | None] = mapped_column(Numeric(18, 6), default=1.0)
    net_salary_base: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    status: Mapped[str | None] = mapped_column(String(20), default="draft")


__all__ = [
    "Attendance",
    "Department",
    "Employee",
    "EmployeeLoan",
    "EmployeePosition",
    "EmployeeSalaryComponent",
    "LeaveRequest",
    "PayrollEntry",
    "PayrollPeriod",
    "SalaryComponent",
    "SalaryStructure",
]
