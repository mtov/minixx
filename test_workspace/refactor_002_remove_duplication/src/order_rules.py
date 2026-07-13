from __future__ import annotations


def subtotal(items: list[dict]) -> float:
    return round(sum(item["price"] * item["quantity"] for item in items), 2)


def eligible_subtotal(items: list[dict]) -> float:
    eligible_items = []
    for item in items:
        if item.get("is_cancelled", False):
            continue
        if item.get("is_promotional", False):
            continue
        eligible_items.append(item)

    return round(
        sum(item["price"] * item["quantity"] for item in eligible_items),
        2,
    )


def reward_points(items: list[dict]) -> int:
    eligible_items = []
    for item in items:
        if item.get("is_cancelled", False):
            continue
        if item.get("is_promotional", False):
            continue
        eligible_items.append(item)

    points = sum(int(item["price"] * item["quantity"]) for item in eligible_items)
    return points // 10


def qualifying_item_count(items: list[dict]) -> int:
    eligible_items = []
    for item in items:
        if item.get("is_cancelled", False):
            continue
        if item.get("is_promotional", False):
            continue
        eligible_items.append(item)

    return sum(item["quantity"] for item in eligible_items)


def order_snapshot(items: list[dict]) -> dict:
    return {
        "subtotal": subtotal(items),
        "eligibleSubtotal": eligible_subtotal(items),
        "rewardPoints": reward_points(items),
        "qualifyingItemCount": qualifying_item_count(items),
    }
