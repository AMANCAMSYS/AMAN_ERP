from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import ModelBase


class ProductCategory(ModelBase):
    __tablename__ = "product_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_code: Mapped[str | None] = mapped_column(String(50), unique=True)
    category_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category_name_en: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("product_categories.id"))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    image_url: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int | None] = mapped_column(Integer, default=0)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProductUnit(ModelBase):
    __tablename__ = "product_units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unit_code: Mapped[str | None] = mapped_column(String(20), unique=True)
    unit_name: Mapped[str] = mapped_column(String(100), nullable=False)
    unit_name_en: Mapped[str | None] = mapped_column(String(100))
    abbreviation: Mapped[str | None] = mapped_column(String(10))
    base_unit_id: Mapped[int | None] = mapped_column(ForeignKey("product_units.id"))
    conversion_factor: Mapped[float | None] = mapped_column(Numeric(10, 6), default=1)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Product(ModelBase):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_code: Mapped[str | None] = mapped_column(String(50), unique=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_name_en: Mapped[str | None] = mapped_column(String(255))
    product_type: Mapped[str | None] = mapped_column(String(50), default="product")
    category_id: Mapped[int | None] = mapped_column(ForeignKey("product_categories.id"))
    unit_id: Mapped[int | None] = mapped_column(ForeignKey("product_units.id"))
    barcode: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    short_description: Mapped[str | None] = mapped_column(String(500))
    brand: Mapped[str | None] = mapped_column(String(100))
    manufacturer: Mapped[str | None] = mapped_column(String(100))
    origin_country: Mapped[str | None] = mapped_column(String(100))
    weight: Mapped[float | None] = mapped_column(Numeric(10, 4))
    volume: Mapped[float | None] = mapped_column(Numeric(10, 4))
    dimensions: Mapped[str | None] = mapped_column(String(100))
    cost_price: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    last_purchase_price: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    selling_price: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    wholesale_price: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    min_price: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    max_price: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    sku: Mapped[str | None] = mapped_column(String(100), unique=True)
    tax_rate: Mapped[float | None] = mapped_column(Numeric(5, 2), default=15)
    is_taxable: Mapped[bool | None] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    is_track_inventory: Mapped[bool | None] = mapped_column(Boolean, default=True)
    reorder_level: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    reorder_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    image_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    has_batch_tracking: Mapped[bool | None] = mapped_column(Boolean, default=False)
    has_serial_tracking: Mapped[bool | None] = mapped_column(Boolean, default=False)
    has_expiry_tracking: Mapped[bool | None] = mapped_column(Boolean, default=False)
    shelf_life_days: Mapped[int | None] = mapped_column(Integer, default=0)
    expiry_alert_days: Mapped[int | None] = mapped_column(Integer, default=30)
    has_variants: Mapped[bool | None] = mapped_column(Boolean, default=False)
    is_kit: Mapped[bool | None] = mapped_column(Boolean, default=False)


class Inventory(ModelBase):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    reserved_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    available_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    average_cost: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    policy_version: Mapped[int | None] = mapped_column(Integer, default=1)
    last_costing_update: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_movement_date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InventoryTransaction(ModelBase):
    __tablename__ = "inventory_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(50))
    reference_id: Mapped[int | None] = mapped_column(Integer)
    reference_document: Mapped[str | None] = mapped_column(String(100))
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    balance_before: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    balance_after: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    unit_cost: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    total_cost: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class StockAdjustment(ModelBase):
    __tablename__ = "stock_adjustments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    adjustment_number: Mapped[str | None] = mapped_column(String(50), unique=True)
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    adjustment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    old_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    new_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    difference: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PurchaseOrder(ModelBase):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    po_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    party_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id"))
    supplier_id: Mapped[int | None] = mapped_column(Integer)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    order_date: Mapped[Date] = mapped_column(Date, nullable=False)
    expected_date: Mapped[Date | None] = mapped_column(Date)
    subtotal: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    tax_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    discount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    total: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    status: Mapped[str | None] = mapped_column(String(20), default="draft")
    notes: Mapped[str | None] = mapped_column(Text)
    currency: Mapped[str | None] = mapped_column(String(3), default="SAR")
    exchange_rate: Mapped[float | None] = mapped_column(Numeric(18, 6), default=1.0)
    effect_type: Mapped[str | None] = mapped_column(String(20), default="discount")
    effect_percentage: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    markup_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PurchaseOrderLine(ModelBase):
    __tablename__ = "purchase_order_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    po_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    description: Mapped[str | None] = mapped_column(String(500))
    quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=1)
    unit_price: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    tax_rate: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    discount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    total: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    received_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PayrollPeriod(ModelBase):
    __tablename__ = "payroll_periods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Date] = mapped_column(Date, nullable=False)
    payment_date: Mapped[Date | None] = mapped_column(Date)
    status: Mapped[str | None] = mapped_column(String(20), default="draft")
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Department(ModelBase):
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
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EmployeePosition(ModelBase):
    __tablename__ = "employee_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    position_code: Mapped[str | None] = mapped_column(String(50), unique=True)
    position_name: Mapped[str] = mapped_column(String(255), nullable=False)
    position_name_en: Mapped[str | None] = mapped_column(String(255))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    description: Mapped[str | None] = mapped_column(Text)
    level: Mapped[int | None] = mapped_column(Integer, default=1)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Employee(ModelBase):
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
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Attendance(ModelBase):
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    date: Mapped[Date] = mapped_column(Date, nullable=False)
    check_in: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    check_out: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str | None] = mapped_column(String(20), default="present")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EmployeeLoan(ModelBase):
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
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LeaveRequest(ModelBase):
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
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SalaryStructure(ModelBase):
    __tablename__ = "salary_structures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    base_type: Mapped[str | None] = mapped_column(String(50), default="monthly")
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SalaryComponent(ModelBase):
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
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EmployeeSalaryComponent(ModelBase):
    __tablename__ = "employee_salary_components"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"))
    component_id: Mapped[int | None] = mapped_column(ForeignKey("salary_components.id", ondelete="CASCADE"))
    amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    effective_date: Mapped[Date | None] = mapped_column(Date)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PayrollEntry(ModelBase):
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
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
