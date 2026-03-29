"""
Quantity validation utilities for unit-of-measure enforcement.

Discrete units (piece, box, carton) require integer quantities.
Continuous units (kg, meter, liter) allow decimal quantities.
"""

from sqlalchemy import text
from fastapi import HTTPException

# Units that require integer (whole number) quantities
DISCRETE_UNITS = {"قطعة", "علبة", "كرتون", "piece", "box", "carton", "unit"}


def is_discrete_unit(unit_name: str) -> bool:
    """Check if a unit name represents a discrete (countable) unit."""
    if not unit_name:
        return True  # Default to discrete for safety
    return unit_name.strip().lower() in {u.lower() for u in DISCRETE_UNITS}


def validate_quantity_for_product(db, product_id: int, quantity: float) -> None:
    """
    Validate that quantity is an integer if the product's unit is discrete.
    Raises HTTPException(400) if validation fails.
    """
    row = db.execute(text("""
        SELECT u.unit_name
        FROM products p
        LEFT JOIN product_units u ON p.unit_id = u.id
        WHERE p.id = :pid
    """), {"pid": product_id}).fetchone()

    if not row or not row.unit_name:
        return  # No unit info — skip validation

    if is_discrete_unit(row.unit_name):
        if quantity != int(quantity):
            raise HTTPException(
                status_code=400,
                detail=f"الكمية يجب أن تكون عدداً صحيحاً للمنتج بوحدة '{row.unit_name}'. القيمة المدخلة: {quantity}"
            )
