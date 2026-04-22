"""cpq module Pydantic schemas."""
from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


# ── Option & Group ──
class OptionRead(BaseModel):
    id: int
    group_id: int
    name: str
    price_adjustment: Decimal = Decimal("0")
    is_default: bool = False
    sort_order: int = 0


class OptionGroupRead(BaseModel):
    id: int
    configuration_id: int
    name: str
    is_required: bool = True
    sort_order: int = 0
    options: List[OptionRead] = []


# ── Validation Rule ──
class ValidationRuleRead(BaseModel):
    id: int
    rule_type: str
    source_option_id: int
    target_option_id: int
    error_message: Optional[str] = None


# ── Pricing Rule ──
class PricingRuleRead(BaseModel):
    id: int
    rule_type: str
    min_quantity: Optional[int] = None
    max_quantity: Optional[int] = None
    discount_percent: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    customer_group_id: Optional[int] = None
    priority: int = 0


# ── Configuration ──
class ConfigurationRead(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    name: str
    is_active: bool = True
    groups: List[OptionGroupRead] = []
    rules: List[ValidationRuleRead] = []
    pricing_rules: List[PricingRuleRead] = []


# ── Validate ──
class ValidateConfigRequest(BaseModel):
    configuration_id: int
    selected_option_ids: List[int]


class ValidationError(BaseModel):
    rule_type: str
    source_option: str
    target_option: str
    message: str


class ValidateConfigResponse(BaseModel):
    valid: bool
    errors: List[ValidationError] = []


# ── Price ──
class PriceLineRequest(BaseModel):
    product_id: int
    configuration_id: int
    selected_option_ids: List[int]
    quantity: Decimal = Decimal("1")


class PriceCalculationRequest(BaseModel):
    lines: List[PriceLineRequest]
    customer_id: Optional[int] = None


class PriceLineResponse(BaseModel):
    product_id: int
    base_unit_price: Decimal
    option_adjustments: Decimal
    discount_applied: Decimal
    final_unit_price: Decimal
    quantity: Decimal
    line_total: Decimal


class PriceCalculationResponse(BaseModel):
    lines: List[PriceLineResponse]
    total_amount: Decimal
    discount_total: Decimal
    final_amount: Decimal


# ── Quote ──
class QuoteLineCreate(BaseModel):
    product_id: int
    configuration_id: int
    selected_option_ids: List[int]
    quantity: Decimal = Decimal("1")


class QuoteCreate(BaseModel):
    customer_id: int
    valid_until: date
    lines: List[QuoteLineCreate]


class QuoteLineRead(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    selected_options: Optional[list] = None
    quantity: Decimal
    base_unit_price: Decimal
    option_adjustments: Decimal
    discount_applied: Decimal
    final_unit_price: Decimal
    line_total: Decimal


class QuoteRead(BaseModel):
    id: int
    customer_id: int
    customer_name: Optional[str] = None
    quotation_id: Optional[int] = None
    total_amount: Decimal
    discount_total: Decimal
    final_amount: Decimal
    pdf_path: Optional[str] = None
    status: str
    valid_until: Optional[date] = None
    lines: List[QuoteLineRead] = []
    created_at: Optional[str] = None
