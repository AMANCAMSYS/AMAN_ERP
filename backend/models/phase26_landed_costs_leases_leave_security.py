from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import ModelBase


class LandedCost(ModelBase):
    __tablename__ = "landed_costs"
    __table_args__ = (UniqueConstraint("lc_number", name="landed_costs_lc_number_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lc_number: Mapped[str] = mapped_column(String(50), nullable=False)
    lc_date: Mapped[Date] = mapped_column(Date, nullable=False)
    purchase_order_id: Mapped[int | None] = mapped_column(ForeignKey("purchase_orders.id"))
    grn_id: Mapped[int | None] = mapped_column(Integer)
    reference: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    total_amount: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    allocation_method: Mapped[str | None] = mapped_column(String(30), default="by_value")
    status: Mapped[str | None] = mapped_column(String(20), default="draft")
    currency: Mapped[str | None] = mapped_column(String(10), default="SAR")
    notes: Mapped[str | None] = mapped_column(Text)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    journal_entry_id: Mapped[int | None] = mapped_column(ForeignKey("journal_entries.id", ondelete="SET NULL"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LandedCostItem(ModelBase):
    __tablename__ = "landed_cost_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    landed_cost_id: Mapped[int] = mapped_column(ForeignKey("landed_costs.id", ondelete="CASCADE"), nullable=False)
    cost_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    amount: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False, default=0)
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id"))
    invoice_ref: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LeaseContract(ModelBase):
    __tablename__ = "lease_contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id", ondelete="SET NULL"))
    description: Mapped[str | None] = mapped_column(Text)
    lessor_name: Mapped[str | None] = mapped_column(String(200))
    lease_type: Mapped[str | None] = mapped_column(String(30), default="operating")
    start_date: Mapped[Date | None] = mapped_column(Date)
    end_date: Mapped[Date | None] = mapped_column(Date)
    monthly_payment: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    total_payments: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    discount_rate: Mapped[float | None] = mapped_column(Numeric(8, 4), default=5.0)
    right_of_use_value: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    lease_liability: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    accumulated_depreciation: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    status: Mapped[str | None] = mapped_column(String(20), default="active")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LeaveCarryover(ModelBase):
    __tablename__ = "leave_carryover"
    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "leave_type",
            "year",
            name="leave_carryover_employee_id_leave_type_year_key",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    leave_type: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    entitled_days: Mapped[float | None] = mapped_column(Numeric(6, 1), default=0)
    used_days: Mapped[float | None] = mapped_column(Numeric(6, 1), default=0)
    carried_days: Mapped[float | None] = mapped_column(Numeric(6, 1), default=0)
    expired_days: Mapped[float | None] = mapped_column(Numeric(6, 1), default=0)
    max_carryover: Mapped[float | None] = mapped_column(Numeric(6, 1), default=5)
    calculated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LoginAttempt(ModelBase):
    __tablename__ = "login_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    username: Mapped[str | None] = mapped_column(String(100))
    success: Mapped[bool | None] = mapped_column(Boolean, default=False)
    attempted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())