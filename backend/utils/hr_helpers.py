"""
AMAN ERP - HR Helper Functions
Shared calculations for End of Service and other HR operations.
Compliant with Saudi Labor Law (Articles 84 & 85).
"""


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
    if total_years <= 0:
        return {
            "full_gratuity": 0.0,
            "resignation_factor": 0.0,
            "final_gratuity": 0.0
        }
    
    # Calculate base gratuity
    if total_years <= 5:
        gratuity = (total_salary / 2) * total_years
    else:
        first_five = (total_salary / 2) * 5
        remaining = total_salary * (total_years - 5)
        gratuity = first_five + remaining
    
    # Apply resignation factor
    resignation_factor = 1.0
    if termination_reason == "resignation":
        if total_years < 2:
            resignation_factor = 0.0
        elif total_years < 5:
            resignation_factor = 1 / 3
        elif total_years < 10:
            resignation_factor = 2 / 3
        else:
            resignation_factor = 1.0
    
    final_gratuity = round(gratuity * resignation_factor, 2)
    
    return {
        "full_gratuity": round(gratuity, 2),
        "resignation_factor": resignation_factor,
        "final_gratuity": final_gratuity
    }
