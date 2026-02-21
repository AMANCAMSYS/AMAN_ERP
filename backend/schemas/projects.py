"""Projects module Pydantic schemas."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class ProjectCreate(BaseModel):
    project_name: str
    project_code: Optional[str] = None
    project_name_en: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[str] = "internal"
    customer_id: Optional[int] = None
    manager_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    planned_budget: float = 0
    status: str = "planning"
    branch_id: Optional[int] = None
    contract_type: Optional[str] = "fixed_price"


class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    project_name_en: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[str] = None
    customer_id: Optional[int] = None
    manager_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    planned_budget: Optional[float] = None
    status: Optional[str] = None
    progress_percentage: Optional[float] = None


class TaskCreate(BaseModel):
    task_name: str
    task_name_en: Optional[str] = None
    description: Optional[str] = None
    parent_task_id: Optional[int] = None
    assigned_to: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    planned_hours: float = 0
    status: str = "pending"


class TaskUpdate(BaseModel):
    task_name: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    planned_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    progress: Optional[float] = None
    status: Optional[str] = None


class ProjectExpenseCreate(BaseModel):
    expense_type: str
    expense_date: date
    amount: float
    description: Optional[str] = None
    treasury_id: Optional[int] = None
    expense_account_id: Optional[int] = None


class ProjectRevenueCreate(BaseModel):
    revenue_type: str
    revenue_date: date
    amount: float
    description: Optional[str] = None
    invoice_id: Optional[int] = None


class TimesheetCreate(BaseModel):
    project_id: int
    task_id: Optional[int] = None
    date: date
    hours: float
    description: Optional[str] = None
    status: str = "draft"


class TimesheetUpdate(BaseModel):
    task_id: Optional[int] = None
    date: Optional[date] = None
    hours: Optional[float] = None
    description: Optional[str] = None
    status: Optional[str] = None


class TimesheetApprove(BaseModel):
    timesheet_ids: List[int]


class ProjectDocumentCreate(BaseModel):
    file_name: str
    file_type: str


class ProjectInvoiceItem(BaseModel):
    product_id: Optional[int] = None
    description: str
    quantity: float = 1.0
    unit_price: float
    tax_rate: float = 0.0
    discount: float = 0.0


class ProjectInvoiceCreate(BaseModel):
    customer_id: int
    warehouse_id: Optional[int] = None
    invoice_date: date
    due_date: date
    items: List[ProjectInvoiceItem]
    notes: Optional[str] = None
    payment_method: Optional[str] = "credit"
    currency: Optional[str] = "SAR"
    exchange_rate: Optional[float] = 1.0


class ChangeOrderCreate(BaseModel):
    title: str
    description: Optional[str] = None
    change_type: str = "scope"      # scope, budget, timeline, requirement
    cost_impact: float = 0
    time_impact_days: int = 0


class ChangeOrderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    change_type: Optional[str] = None
    cost_impact: Optional[float] = None
    time_impact_days: Optional[int] = None
    status: Optional[str] = None


class ProjectCloseRequest(BaseModel):
    close_date: Optional[date] = None
    notes: Optional[str] = None
