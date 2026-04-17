"""
AMAN ERP - PII Masking Utility
Masks sensitive personally identifiable information (PII) fields
for users without explicit PII access permission.
"""


def mask_pii(value: str, visible_chars: int = 4) -> str:
    """
    Mask a PII string, showing only the last `visible_chars` characters.

    Args:
        value: The sensitive value to mask.
        visible_chars: Number of trailing characters to keep visible.

    Returns:
        Masked string with asterisks replacing hidden characters,
        or the original value if it's None/empty or shorter than visible_chars.

    Examples:
        mask_pii("SA1234567890123456") → "**************3456"
        mask_pii("1234567890")         → "******7890"
        mask_pii(None)                 → None
        mask_pii("123")               → "123"
    """
    if not value:
        return value
    value_str = str(value)
    if len(value_str) <= visible_chars:
        return value_str
    masked_len = len(value_str) - visible_chars
    return "*" * masked_len + value_str[-visible_chars:]
