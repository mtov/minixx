def line_total(item: dict) -> float:
    return item["price"] * item["quantity"]


def subtotal(items: list[dict]) -> float:
    return sum(line_total(item) for item in items)


def subtotal_after_coupon(items: list[dict], percent: int) -> float:
    return sum(discounted_line_total(item, percent) for item in items)


def discounted_line_total(item: dict, percent: int) -> float:
    total = line_total(item)
    if percent <= 0 or item.get("is_promotional", False):
        return total

    return total * (1 - percent / 100)
