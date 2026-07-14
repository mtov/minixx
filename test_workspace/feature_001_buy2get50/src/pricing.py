def line_total(item: dict) -> float:
    return item["price"] * item["quantity"]


def subtotal(items: list[dict]) -> float:
    return sum(line_total(item) for item in items)


def eligible_unit_prices(items: list[dict]) -> list[float]:
    unit_prices: list[float] = []
    for item in items:
        if not item.get("is_eligible", False):
            continue
        if item.get("is_clearance", False):
            continue
        unit_prices.extend([item["price"]] * item["quantity"])
    return unit_prices
