DISCOUNTS = {
    "SAVE10": 0.10,
    "SAVE20": 0.20,
}


def normalize_coupon_code(coupon_code: str | None) -> str | None:
    if coupon_code is None:
        return None
    normalized = coupon_code.strip().upper()
    return normalized or None


def lookup_coupon(coupon_code: str | None) -> float:
    normalized = normalize_coupon_code(coupon_code)
    if normalized is None:
        return 0.0
    return DISCOUNTS.get(normalized, 0.0)
