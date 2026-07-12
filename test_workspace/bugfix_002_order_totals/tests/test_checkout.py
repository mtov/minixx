from src.checkout import calculate_order_total


def test_no_coupon_keeps_original_total():
    items = [
        {"sku": "A", "price": 40.0, "quantity": 2, "is_promotional": False},
    ]

    assert calculate_order_total(items, None) == 80.0


def test_percentage_coupon_is_applied_once():
    items = [
        {"sku": "A", "price": 50.0, "quantity": 2, "is_promotional": False},
    ]

    assert calculate_order_total(items, "SAVE10") == 90.0


def test_coupon_excludes_promotional_items():
    items = [
        {"sku": "A", "price": 80.0, "quantity": 1, "is_promotional": False},
        {"sku": "B", "price": 20.0, "quantity": 1, "is_promotional": True},
    ]

    assert calculate_order_total(items, "SAVE10") == 92.0


def test_invalid_coupon_is_ignored():
    items = [
        {"sku": "A", "price": 35.0, "quantity": 2, "is_promotional": False},
    ]

    assert calculate_order_total(items, "NOPE") == 70.0


def test_rounds_only_the_final_total():
    items = [
        {"sku": "A", "price": 19.99, "quantity": 3, "is_promotional": False},
    ]

    assert calculate_order_total(items, "SAVE25") == 44.98
