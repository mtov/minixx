COUPONS = {
    "SAVE10": 10,
    "SAVE25": 25,
}


def coupon_percent(coupon_code: str | None) -> int:
    if not coupon_code:
        return 0

    return COUPONS.get(coupon_code, 0)


def discount_amount(subtotal_amount: float, coupon_code: str | None) -> float:
    percent = coupon_percent(coupon_code)
    if percent == 0:
        return 0.0

    return subtotal_amount * (percent / 100)
