from src.pricing import subtotal
from src.promotions import promotion_discount


def calculate_order_total(items: list[dict], promotion_code: str | None = None) -> float:
    base_total = subtotal(items)
    discount = promotion_discount(items, promotion_code)
    return round(base_total - discount, 2)
