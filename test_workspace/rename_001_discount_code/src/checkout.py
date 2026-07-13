from src.discounts import lookup_coupon, normalize_coupon_code


def subtotal(items: list[dict]) -> float:
    return sum(item["price"] * item["quantity"] for item in items)


def calculate_order_total(items: list[dict], coupon_code: str | None = None) -> float:
    amount = subtotal(items)
    discount_rate = lookup_coupon(coupon_code)
    return round(amount * (1 - discount_rate), 2)


def build_checkout_summary(items: list[dict], coupon_code: str | None = None) -> dict:
    normalized_coupon = normalize_coupon_code(coupon_code)
    return {
        "subtotal": round(subtotal(items), 2),
        "couponCode": normalized_coupon,
        "total": calculate_order_total(items, coupon_code),
    }
