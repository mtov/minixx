def subtotal(items: list[dict]) -> float:
    return sum(item["price"] * item["quantity"] for item in items)


def discountable_subtotal(items: list[dict]) -> float:
    return sum(
        item["price"] * item["quantity"]
        for item in items
        if not item.get("is_promotional", False)
    )
