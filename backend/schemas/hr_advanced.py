"""
Pydantic schemas for Advanced HR module (Phase 4)
هياكل الرواتب، مكونات الراتب، العمل الإضافي، GOSI، المستندات، تقييم الأداء، التدريب، المخالفات، العهد
"""

from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


# ===== هياكل الرواتب =====

class SalaryStructureCreate(BaseModel):
    name: str
    name_en: Optional[str] = None
    description: Optional[str] = None
    base_type: str = "monthly"

class SalaryStructureUpdate(BaseModel):
    name: Optional[str] = None
    name_en: Optional[str] = None
    description: Optional[str] = None
    base_type: Optional[str] = None
    is_active: Optional[bool] = None

class SalaryStructureResponse(BaseModel):
    id: int
    name: str
    name_en: Optional[str] = None
    description: Optional[str] = None
    base_type: str
    is_active: bool
    created_at: Optional[datetime] = None


# ===== مكونات الراتب =====

class SalaryComponentCreate(BaseModel):
    name: str
    name_en: Optional[str] = None
    component_type: str  # earning / deduction
    calculation_type: str = "fixed"  # fixed / percentage / formula
    percentage_of: Optional[str] = None
    percentage_value: Optional[Decimal] = 0
    formula: Optional[str] = None
    is_taxable: bool = True
    is_gosi_applicable: bool = False
    sort_order: int = 0
    structure_id: Optional[int] = None

class SalaryComponentUpdate(BaseModel):
    name: Optional[str] = None
    name_en: Optional[str] = None
    component_type: Optional[str] = None
    calculation_type: Optional[str] = None
    percentage_of: Optional[str] = None
    percentage_value: Optional[Decimal] = None
    formula: Optional[str] = None
    is_taxable: Optional[bool] = None
    is_gosi_applicable: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    structure_id: Optional[int] = None

class SalaryComponentResponse(BaseModel):
    id: int
    name: str
    name_en: Optional[str] = None
    component_type: str
    calculation_type: str
    percentage_of: Optional[str] = None
    percentage_value: Optional[Decimal] = None
    formula: Optional[str] = None
    is_taxable: bool
    is_gosi_applicable: bool
    is_active: bool
    sort_order: int
    structure_id: Optional[int] = None
    created_at: Optional[datetime] = None


# ===== ربط مكونات الراتب بالموظفين =====

class EmployeeSalaryComponentCreate(BaseModel):
    employee_id: int
    component_id: int
    amount: Decimal = 0
    is_active: bool = True
    effective_date: Optional[date] = None

class EmployeeSalaryComponentResponse(BaseModel):
    id: int
    employee_id: int
    component_id: int
    amount: Decimal
    is_active: bool
    effective_date: Optional[date] = None
    component_name: Optional[str] = None
    component_type: Optional[str] = None


# ===== العمل الإضافي =====

class OvertimeRequestCreate(BaseModel):
    employee_id: int
    overtime_date: date
    hours: Decimal
    overtime_type: str = "normal"  # normal / holiday / weekend
    multiplier: Optional[Decimal] = None
    reason: Optional[str] = None
    branch_id: Optional[int] = None

class OvertimeRequestUpdate(BaseModel):
    status: str  # approved / rejected
    approved_by: Optional[int] = None

class OvertimeRequestResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    request_date: Optional[date] = None
    overtime_date: date
    hours: Decimal
    overtime_type: str
    multiplier: Decimal
    calculated_amount: Decimal
    reason: Optional[str] = None
    status: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


# ===== إعدادات GOSI =====

class GOSISettingsCreate(BaseModel):
    employee_share_percentage: Decimal = Decimal("9.75")
    employer_share_percentage: Decimal = Decimal("11.75")
    occupational_hazard_percentage: Decimal = Decimal("2.0")
    max_contributable_salary: Decimal = Decimal("45000")
    effective_date: Optional[date] = None

class GOSISettingsUpdate(BaseModel):
    employee_share_percentage: Optional[Decimal] = None
    employer_share_percentage: Optional[Decimal] = None
    occupational_hazard_percentage: Optional[Decimal] = None
    max_contributable_salary: Optional[Decimal] = None
    is_active: Optional[bool] = None

class GOSISettingsResponse(BaseModel):
    id: int
    employee_share_percentage: Decimal
    employer_share_percentage: Decimal
    occupational_hazard_percentage: Decimal
    max_contributable_salary: Decimal
    is_active: bool
    effective_date: Optional[date] = None
    created_at: Optional[datetime] = None

class GOSICalculationResponse(BaseModel):
    employee_id: int
    employee_name: str
    basic_salary: Decimal
    housing_allowance: Decimal
    contributable_salary: Decimal
    employee_share: Decimal
    employer_share: Decimal
    occupational_hazard: Decimal
    total_contribution: Decimal


# ===== مستندات الموظفين =====

class EmployeeDocumentCreate(BaseModel):
    employee_id: int
    document_type: str  # passport / iqama / license / certificate / contract / other
    document_number: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    issuing_authority: Optional[str] = None
    file_url: Optional[str] = None
    notes: Optional[str] = None
    alert_days: int = 30

class EmployeeDocumentUpdate(BaseModel):
    document_number: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    issuing_authority: Optional[str] = None
    file_url: Optional[str] = None
    notes: Optional[str] = None
    alert_days: Optional[int] = None

class EmployeeDocumentResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    document_type: str
    document_number: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    issuing_authority: Optional[str] = None
    file_url: Optional[str] = None
    notes: Optional[str] = None
    alert_days: int
    status: str
    created_at: Optional[datetime] = None


# ===== تقييم الأداء =====

class PerformanceReviewCreate(BaseModel):
    employee_id: int
    reviewer_id: Optional[int] = None
    review_period: str
    review_date: date
    review_type: str = "annual"  # quarterly / semi_annual / annual / probation
    overall_rating: Optional[Decimal] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    goals: Optional[str] = None

class PerformanceReviewUpdate(BaseModel):
    overall_rating: Optional[Decimal] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    goals: Optional[str] = None
    self_rating: Optional[Decimal] = None
    self_comments: Optional[str] = None
    manager_comments: Optional[str] = None
    status: Optional[str] = None

class PerformanceReviewResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    reviewer_id: Optional[int] = None
    reviewer_name: Optional[str] = None
    review_period: str
    review_date: date
    review_type: str
    overall_rating: Optional[Decimal] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    goals: Optional[str] = None
    self_rating: Optional[Decimal] = None
    self_comments: Optional[str] = None
    manager_comments: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None


# ===== برامج التدريب =====

class TrainingProgramCreate(BaseModel):
    name: str
    name_en: Optional[str] = None
    description: Optional[str] = None
    trainer: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    max_participants: Optional[int] = None
    cost: Decimal = 0

class TrainingProgramUpdate(BaseModel):
    name: Optional[str] = None
    name_en: Optional[str] = None
    description: Optional[str] = None
    trainer: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    max_participants: Optional[int] = None
    cost: Optional[Decimal] = None
    status: Optional[str] = None

class TrainingProgramResponse(BaseModel):
    id: int
    name: str
    name_en: Optional[str] = None
    description: Optional[str] = None
    trainer: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    max_participants: Optional[int] = None
    cost: Decimal
    status: str
    participant_count: Optional[int] = None
    created_at: Optional[datetime] = None


class TrainingParticipantCreate(BaseModel):
    training_id: int
    employee_id: int

class TrainingParticipantUpdate(BaseModel):
    attendance_status: Optional[str] = None  # registered / attended / absent / completed
    certificate_issued: Optional[bool] = None
    score: Optional[Decimal] = None
    feedback: Optional[str] = None

class TrainingParticipantResponse(BaseModel):
    id: int
    training_id: int
    employee_id: int
    employee_name: Optional[str] = None
    attendance_status: str
    certificate_issued: bool
    score: Optional[Decimal] = None
    feedback: Optional[str] = None
    created_at: Optional[datetime] = None


# ===== المخالفات =====

class ViolationCreate(BaseModel):
    employee_id: int
    violation_date: date
    violation_type: str
    severity: str = "minor"  # minor / major / critical
    description: Optional[str] = None
    action_taken: Optional[str] = None
    penalty_amount: Decimal = 0
    deduct_from_salary: bool = False
    reported_by: Optional[int] = None

class ViolationUpdate(BaseModel):
    action_taken: Optional[str] = None
    penalty_amount: Optional[Decimal] = None
    deduct_from_salary: Optional[bool] = None
    status: Optional[str] = None

class ViolationResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    violation_date: date
    violation_type: str
    severity: str
    description: Optional[str] = None
    action_taken: Optional[str] = None
    penalty_amount: Decimal
    deduct_from_salary: bool
    status: str
    reported_by: Optional[int] = None
    created_at: Optional[datetime] = None


# ===== العهد =====

class CustodyCreate(BaseModel):
    employee_id: int
    item_name: str
    item_type: Optional[str] = None  # mobile / laptop / vehicle / key / equipment / other
    serial_number: Optional[str] = None
    assigned_date: date
    condition_on_assign: str = "new"
    value: Decimal = 0
    notes: Optional[str] = None

class CustodyUpdate(BaseModel):
    return_date: Optional[date] = None
    condition_on_return: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class CustodyResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    item_name: str
    item_type: Optional[str] = None
    serial_number: Optional[str] = None
    assigned_date: date
    return_date: Optional[date] = None
    condition_on_assign: str
    condition_on_return: Optional[str] = None
    value: Decimal
    notes: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
