from src.discounts import coupon_percent, discount_amount
from src.pricing import subtotal, subtotal_after_coupon


def calculate_order_total(items: list[dict], coupon_code: str | None = None) -> float:
    percent = coupon_percent(coupon_code)
    discounted_subtotal = subtotal_after_coupon(items, percent)
    extra_discount = discount_amount(subtotal(items), coupon_code)
    return round(discounted_subtotal - extra_discount, 2)
