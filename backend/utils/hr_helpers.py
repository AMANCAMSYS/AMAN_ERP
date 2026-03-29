"""
AMAN ERP - HR Helper Functions
Shared calculations for End of Service and other HR operations.
Compliant with Saudi Labor Law (Articles 84 & 85).
"""

from decimal import Decimal, ROUND_HALF_UP

_D2 = Decimal('0.01')


def _dec(v):
    return Decimal(str(v or 0))


def calculate_eos_gratuity(total_salary: float, total_years: float, termination_reason: str = "termination") -> dict:
    """
    Calculate End of Service gratuity per Saudi Labor Law Art. 84/85.
    
    Saudi Labor Law Rules:
    - First 5 years: half month salary per year of service
    - After 5 years: full month salary per year of service
    
    Resignation adjustments (Art. 85):
    - < 2 years:  0% (no entitlement)
    - 2-5 years:  1/3 of total
    - 5-10 years: 2/3 of total
    - > 10 years: 100% (full amount)
    
    Termination, retirement, contract_end: 100% (full amount)
    
    Args:
        total_salary: Monthly salary including all allowances (basic + housing + transport)
        total_years: Years of service (fractional)
        termination_reason: One of: termination, resignation, retirement, contract_end
    
    Returns:
        dict with full_gratuity, resignation_factor, final_gratuity
    """
    salary = _dec(total_salary)
    years = _dec(total_years)

    if years <= 0:
        return {
            "full_gratuity": 0.0,
            "resignation_factor": 0.0,
            "final_gratuity": 0.0
        }

    # Calculate base gratuity
    if years <= 5:
        gratuity = (salary / Decimal('2')) * years
    else:
        first_five = (salary / Decimal('2')) * Decimal('5')
        remaining = salary * (years - Decimal('5'))
        gratuity = first_five + remaining

    # Apply resignation factor
    resignation_factor = Decimal('1')
    if termination_reason == "resignation":
        if years < 2:
            resignation_factor = Decimal('0')
        elif years < 5:
            resignation_factor = Decimal('1') / Decimal('3')
        elif years < 10:
            resignation_factor = Decimal('2') / Decimal('3')
        else:
            resignation_factor = Decimal('1')

    full_gratuity = gratuity.quantize(_D2, ROUND_HALF_UP)
    final_gratuity = (gratuity * resignation_factor).quantize(_D2, ROUND_HALF_UP)

    return {
        "full_gratuity": float(full_gratuity),
        "resignation_factor": float(resignation_factor.quantize(_D2, ROUND_HALF_UP)),
        "final_gratuity": float(final_gratuity)
    }
