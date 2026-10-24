"""Prices in euros. An item is a dict with "price" (per piece) and "qty"."""

DISCOUNTS = {"WELCOME10": 0.10, "VIP25": 0.25}


def calc_total(items, code=None):
    """Sum of price * qty, minus the discount of the code (if known), rounded to cents."""
    total = sum(item["price"] * item["qty"] for item in items)
    if code in DISCOUNTS:
        total *= 1 - DISCOUNTS[code]
    return round(total, 2)
