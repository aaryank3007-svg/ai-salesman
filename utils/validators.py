from typing import Tuple, Optional
from database.db import query_one

def validate_quantity(qty: float) -> Tuple[bool, str]:
    """Validate quantity is positive and within reasonable FMCG ordering thresholds."""
    if qty <= 0:
        return False, "Quantity must be greater than zero."
    if qty > 5000:
        return False, "Quantity exceeds maximum single-order threshold (5,000 units)."
    return True, "Valid"

def validate_sku(sku_id: str) -> Tuple[bool, Optional[dict]]:
    """Validate that SKU exists in the database."""
    product = query_one("SELECT * FROM products WHERE id = ?", (sku_id,))
    if not product:
        return False, None
    return True, product

def validate_unit_for_product(product_id: str, unit_name: str) -> Tuple[bool, Optional[dict]]:
    """Check if unit (carton/box/dozen/piece) is supported for this specific product."""
    unit_row = query_one(
        "SELECT * FROM packaging_units WHERE product_id = ? AND LOWER(unit_name) = LOWER(?) AND is_allowed = 1",
        (product_id, unit_name)
    )
    if not unit_row:
        return False, None
    return True, unit_row

def check_stock_sufficiency(product_id: str, requested_pieces: int) -> Tuple[bool, int]:
    """Check if available stock in pieces can fulfill the order."""
    product = query_one("SELECT stock_pieces FROM products WHERE id = ?", (product_id,))
    if not product:
        return False, 0
    available = product["stock_pieces"]
    return (available >= requested_pieces), available
