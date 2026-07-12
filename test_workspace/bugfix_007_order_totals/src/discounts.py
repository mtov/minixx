COUPONS = {
    "SAVE10": {"percent_off": 10, "minimum_subtotal": 100.0},
    "SAVE20": {"percent_off": 20, "minimum_subtotal": 200.0},
}


def calculate_discount(subtotal_amount: float, coupon_code: str | None) -> float:
    if not coupon_code:
        return 0.0

    coupon = COUPONS.get(coupon_code)
    if coupon is None:
        return 0.0

    if subtotal_amount < coupon["minimum_subtotal"]:
        return 0.0

    return subtotal_amount * (coupon["percent_off"] / 100)
