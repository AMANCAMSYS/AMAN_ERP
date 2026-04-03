from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase


class CrmLeadScoringRule(ModelBase):
    __tablename__ = "crm_lead_scoring_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_name: Mapped[str] = mapped_column(String(100), nullable=False)
    field_name: Mapped[str] = mapped_column(String(50), nullable=False)
    operator: Mapped[str] = mapped_column(String(20), nullable=False, default="equals")
    field_value: Mapped[str | None] = mapped_column(String(200))
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_by: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CrmLeadScore(ModelBase):
    __tablename__ = "crm_lead_scores"
    __table_args__ = (UniqueConstraint("opportunity_id", name="crm_lead_scores_opportunity_id_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("sales_opportunities.id", ondelete="CASCADE"))
    total_score: Mapped[int | None] = mapped_column(Integer, default=0)
    grade: Mapped[str | None] = mapped_column(String(1), default="C")
    scoring_details: Mapped[list | None] = mapped_column(JSONB, default=list)
    last_scored_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CrmCustomerSegment(ModelBase):
    __tablename__ = "crm_customer_segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    criteria: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    color: Mapped[str | None] = mapped_column(String(20), default="#3B82F6")
    auto_assign: Mapped[bool | None] = mapped_column(Boolean, default=False)
    customer_count: Mapped[int | None] = mapped_column(Integer, default=0)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_by: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CrmCustomerSegmentMember(ModelBase):
    __tablename__ = "crm_customer_segment_members"
    __table_args__ = (
        UniqueConstraint("segment_id", "customer_id", name="crm_customer_segment_members_segment_id_customer_id_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    segment_id: Mapped[int | None] = mapped_column(ForeignKey("crm_customer_segments.id", ondelete="CASCADE"))
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"))
    added_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CrmSalesForecast(ModelBase):
    __tablename__ = "crm_sales_forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    period: Mapped[str] = mapped_column(String(7), nullable=False)
    forecast_type: Mapped[str | None] = mapped_column(String(30), default="revenue")
    predicted_value: Mapped[float | None] = mapped_column(Numeric(18, 2), default=0)
    actual_value: Mapped[float | None] = mapped_column(Numeric(18, 2), default=0)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    method: Mapped[str | None] = mapped_column(String(30), default="weighted_pipeline")
    details: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    branch_id: Mapped[int | None] = mapped_column(Integer)
    created_by: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
