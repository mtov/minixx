from src.discounts import calculate_discount
from src.pricing import discountable_subtotal, subtotal

FREE_SHIPPING_THRESHOLD = 100.0
SHIPPING_FEE = 15.0


def calculate_order_total(items: list[dict], coupon_code: str | None = None) -> float:
    subtotal_amount = subtotal(items)
    eligible_amount = discountable_subtotal(items)
    discount = calculate_discount(eligible_amount, coupon_code)

    discounted_subtotal = subtotal_amount - discount
    shipping = 0.0 if discounted_subtotal >= FREE_SHIPPING_THRESHOLD else SHIPPING_FEE

    return round(discounted_subtotal + shipping, 2)
