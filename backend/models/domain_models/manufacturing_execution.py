from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase, SoftDeleteMixin


class ManufacturingEquipment(SoftDeleteMixin, ModelBase):
    __tablename__ = "manufacturing_equipment"
    __table_args__ = (UniqueConstraint("code", name="manufacturing_equipment_code_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(50))
    work_center_id: Mapped[int | None] = mapped_column(ForeignKey("work_centers.id"))
    status: Mapped[str | None] = mapped_column(String(20), default="active")
    purchase_date: Mapped[Date | None] = mapped_column(Date)
    last_maintenance_date: Mapped[Date | None] = mapped_column(Date)
    next_maintenance_date: Mapped[Date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ManufacturingOperation(SoftDeleteMixin, ModelBase):
    __tablename__ = "manufacturing_operations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route_id: Mapped[int | None] = mapped_column(ForeignKey("manufacturing_routes.id", ondelete="CASCADE"))
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    work_center_id: Mapped[int | None] = mapped_column(ForeignKey("work_centers.id"))
    description: Mapped[str | None] = mapped_column(String(255))
    setup_time: Mapped[float | None] = mapped_column(Numeric(10, 2), default=0)
    cycle_time: Mapped[float | None] = mapped_column(Numeric(10, 2), default=0)
    labor_rate_per_hour: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ManufacturingRoute(SoftDeleteMixin, ModelBase):
    __tablename__ = "manufacturing_routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    bom_id: Mapped[int | None] = mapped_column(ForeignKey("bill_of_materials.id"))
    is_default: Mapped[bool | None] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MfgQcCheck(SoftDeleteMixin, ModelBase):
    __tablename__ = "mfg_qc_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    production_order_id: Mapped[int | None] = mapped_column(ForeignKey("production_orders.id", ondelete="CASCADE"))
    operation_id: Mapped[int | None] = mapped_column(ForeignKey("manufacturing_operations.id"))
    check_name: Mapped[str] = mapped_column(String(200), nullable=False)
    check_type: Mapped[str | None] = mapped_column(String(30), default="visual")
    specification: Mapped[str | None] = mapped_column(Text)
    actual_value: Mapped[str | None] = mapped_column(String(200))
    result: Mapped[str | None] = mapped_column(String(20), default="pending")
    failure_action: Mapped[str | None] = mapped_column(String(20), default="warn")
    checked_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    notes: Mapped[str | None] = mapped_column(Text)
    checked_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MrpPlan(ModelBase):
    __tablename__ = "mrp_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_name: Mapped[str] = mapped_column(String(255), nullable=False)
    production_order_id: Mapped[int | None] = mapped_column(ForeignKey("production_orders.id", ondelete="CASCADE"))
    status: Mapped[str | None] = mapped_column(String(50), default="draft")
    calculated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))


class MrpItem(ModelBase):
    __tablename__ = "mrp_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mrp_plan_id: Mapped[int | None] = mapped_column(ForeignKey("mrp_plans.id", ondelete="CASCADE"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    required_quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    available_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    on_hand_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    on_order_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    shortage_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    lead_time_days: Mapped[int | None] = mapped_column(Integer, default=0)
    suggested_action: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str | None] = mapped_column(String(50), default="pending")


class ProductionOrderOperation(ModelBase):
    __tablename__ = "production_order_operations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    production_order_id: Mapped[int | None] = mapped_column(ForeignKey("production_orders.id", ondelete="CASCADE"))
    operation_id: Mapped[int | None] = mapped_column(ForeignKey("manufacturing_operations.id"))
    work_center_id: Mapped[int | None] = mapped_column(ForeignKey("work_centers.id"))
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    worker_id: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    actual_setup_time: Mapped[float | None] = mapped_column(Numeric(8, 2), default=0)
    actual_run_time: Mapped[float | None] = mapped_column(Numeric(8, 2), default=0)
    completed_quantity: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    scrapped_quantity: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    planned_start_time: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    planned_end_time: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    start_time: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sequence: Mapped[int | None] = mapped_column(Integer)


class ProductionOrder(ModelBase):
    __tablename__ = "production_orders"
    __table_args__ = (UniqueConstraint("order_number", name="production_orders_order_number_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_number: Mapped[str | None] = mapped_column(String(50))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    bom_id: Mapped[int | None] = mapped_column(ForeignKey("bill_of_materials.id"))
    route_id: Mapped[int | None] = mapped_column(ForeignKey("manufacturing_routes.id"))
    quantity: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    produced_quantity: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    scrapped_quantity: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    status: Mapped[str | None] = mapped_column(String(20), default="draft")
    start_date: Mapped[Date | None] = mapped_column(Date)
    due_date: Mapped[Date | None] = mapped_column(Date)
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    destination_warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actual_material_cost: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    actual_labor_cost: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    actual_overhead_cost: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    actual_total_cost: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    standard_cost: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    variance_amount: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    variance_percentage: Mapped[float | None] = mapped_column(Numeric(8, 4), default=0)
    costing_status: Mapped[str | None] = mapped_column(String(20), default="pending")


class ShopFloorLog(ModelBase):
    __tablename__ = "shop_floor_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_order_id: Mapped[int] = mapped_column(ForeignKey("production_orders.id", ondelete="CASCADE"), nullable=False)
    routing_operation_id: Mapped[int] = mapped_column(ForeignKey("manufacturing_operations.id"), nullable=False)
    operator_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    output_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    scrap_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    downtime_minutes: Mapped[float | None] = mapped_column(Numeric(10, 2), default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="in_progress")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


__all__ = [
    "ManufacturingEquipment",
    "ManufacturingOperation",
    "ManufacturingRoute",
    "MfgQcCheck",
    "MrpPlan",
    "MrpItem",
    "ProductionOrderOperation",
    "ProductionOrder",
    "ShopFloorLog",
]
