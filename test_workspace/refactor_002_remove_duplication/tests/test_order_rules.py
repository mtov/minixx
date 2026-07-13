from src.order_rules import (
    eligible_subtotal,
    order_snapshot,
    qualifying_item_count,
    reward_points,
    subtotal,
)


def test_subtotal_includes_all_non_filtered_math():
    items = [
        {"sku": "A", "price": 20.0, "quantity": 2, "is_promotional": False},
        {"sku": "B", "price": 5.0, "quantity": 1, "is_promotional": True},
    ]

    assert subtotal(items) == 45.0


def test_eligible_subtotal_skips_promotional_and_cancelled_items():
    items = [
        {"sku": "A", "price": 20.0, "quantity": 2, "is_promotional": False},
        {"sku": "B", "price": 5.0, "quantity": 3, "is_promotional": True},
        {"sku": "C", "price": 9.0, "quantity": 1, "is_cancelled": True},
    ]

    assert eligible_subtotal(items) == 40.0


def test_reward_points_use_only_eligible_items():
    items = [
        {"sku": "A", "price": 26.0, "quantity": 2, "is_promotional": False},
        {"sku": "B", "price": 10.0, "quantity": 1, "is_promotional": True},
        {"sku": "C", "price": 9.0, "quantity": 1, "is_cancelled": True},
    ]

    assert reward_points(items) == 5


def test_qualifying_item_count_uses_only_eligible_items():
    items = [
        {"sku": "A", "price": 10.0, "quantity": 3, "is_promotional": False},
        {"sku": "B", "price": 8.0, "quantity": 4, "is_promotional": True},
        {"sku": "C", "price": 7.0, "quantity": 2, "is_cancelled": True},
    ]

    assert qualifying_item_count(items) == 3


def test_order_snapshot_stays_consistent():
    items = [
        {"sku": "A", "price": 20.0, "quantity": 2, "is_promotional": False},
        {"sku": "B", "price": 5.0, "quantity": 3, "is_promotional": True},
        {"sku": "C", "price": 15.0, "quantity": 1, "is_cancelled": True},
    ]

    assert order_snapshot(items) == {
        "subtotal": 70.0,
        "eligibleSubtotal": 40.0,
        "rewardPoints": 4,
        "qualifyingItemCount": 2,
    }
