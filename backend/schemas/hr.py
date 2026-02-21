"""HR module Pydantic schemas."""
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date, datetime


class LoanCreate(BaseModel):
    employee_id: int
    amount: float
    total_installments: int
    start_date: date
    reason: Optional[str] = None


class LoanResponse(LoanCreate):
    id: int
    monthly_installment: float
    paid_amount: float
    status: str
    created_at: datetime
    employee_name: Optional[str] = None


class EmployeeCreate(BaseModel):
    employee_code: Optional[str] = None
    first_name: str
    last_name: str
    first_name_en: Optional[str] = None
    last_name_en: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    position_title: Optional[str] = None
    department_name: Optional[str] = None
    salary: float = 0
    housing_allowance: float = 0
    transport_allowance: float = 0
    other_allowances: float = 0
    hourly_cost: float = 0
    hire_date: Optional[date] = None
    create_user: bool = False
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    create_ledger: bool = False
    branch_id: Optional[int] = None
    allowed_branch_ids: Optional[List[int]] = None


class EmployeeUpdate(BaseModel):
    employee_code: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    position_title: Optional[str] = None
    department_name: Optional[str] = None
    salary: Optional[float] = None
    housing_allowance: Optional[float] = None
    transport_allowance: Optional[float] = None
    other_allowances: Optional[float] = None
    hourly_cost: Optional[float] = None
    branch_id: Optional[int] = None
    allowed_branch_ids: Optional[List[int]] = None
    role: Optional[str] = None


class EmployeeResponse(BaseModel):
    id: int
    employee_code: Optional[str] = None
    first_name: str
    last_name: str
    position: Optional[str] = None
    department: Optional[str] = None
    status: str
    user_id: Optional[int] = None
    account_id: Optional[int] = None
    branch_id: Optional[int] = None
    allowed_branches: List[int] = []
    role: Optional[str] = None
    hourly_cost: float = 0


class DepartmentCreate(BaseModel):
    department_name: str


class DepartmentResponse(BaseModel):
    id: int
    department_name: str


class PositionCreate(BaseModel):
    position_name: str
    department_id: Optional[int] = None


class PositionResponse(BaseModel):
    id: int
    position_name: str
    department_id: Optional[int] = None
    department_name: Optional[str] = None


class PayrollPeriodCreate(BaseModel):
    start_date: date
    end_date: date
    payment_date: Optional[date] = None
    name: str


class PayrollGenerate(BaseModel):
    period_id: int


class PayrollEntryResponse(BaseModel):
    id: int
    employee_name: str
    position: Optional[str] = None
    basic_salary: float
    housing_allowance: float
    transport_allowance: float
    other_allowances: float
    deductions: float
    net_salary: float
    status: Optional[str] = None


class PayrollPeriodResponse(BaseModel):
    id: int
    name: str
    start_date: date
    end_date: date
    status: str
    total_net: float = 0
    created_at: datetime


class AttendanceResponse(BaseModel):
    id: int
    employee_id: int
    date: date
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LeaveRequestCreate(BaseModel):
    employee_id: Optional[int] = None
    leave_type: str
    start_date: date
    end_date: date
    reason: Optional[str] = None
    attachment_url: Optional[str] = None


class LeaveRequestResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    leave_type: str
    start_date: date
    end_date: date
    reason: Optional[str] = None
    status: str
    created_at: datetime


class EndOfServiceRequest(BaseModel):
    employee_id: int
    termination_date: Optional[date] = None
    termination_reason: str = "resignation"
