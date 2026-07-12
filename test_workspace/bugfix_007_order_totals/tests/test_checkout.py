from src.checkout import calculate_order_total


def test_no_coupon_and_free_shipping_from_subtotal():
    items = [
        {"sku": "A", "price": 40.0, "quantity": 1, "is_promotional": False},
        {"sku": "B", "price": 30.0, "quantity": 2, "is_promotional": True},
    ]

    assert calculate_order_total(items, None) == 100.0


def test_coupon_applies_only_to_non_promotional_items():
    items = [
        {"sku": "A", "price": 80.0, "quantity": 1, "is_promotional": False},
        {"sku": "B", "price": 30.0, "quantity": 1, "is_promotional": True},
    ]

    assert calculate_order_total(items, "SAVE10") == 102.0


def test_coupon_eligibility_uses_pre_discount_subtotal():
    items = [
        {"sku": "A", "price": 100.0, "quantity": 1, "is_promotional": False},
    ]

    assert calculate_order_total(items, "SAVE10") == 90.0


def test_free_shipping_uses_pre_discount_subtotal():
    items = [
        {"sku": "A", "price": 100.0, "quantity": 1, "is_promotional": False},
    ]

    assert calculate_order_total(items, "SAVE20") == 100.0


def test_invalid_coupon_is_ignored():
    items = [
        {"sku": "A", "price": 40.0, "quantity": 1, "is_promotional": False},
    ]

    assert calculate_order_total(items, "NOPE") == 55.0


def test_rounds_only_the_final_total():
    items = [
        {"sku": "A", "price": 33.335, "quantity": 3, "is_promotional": False},
    ]

    assert calculate_order_total(items, "SAVE10") == 90.0
