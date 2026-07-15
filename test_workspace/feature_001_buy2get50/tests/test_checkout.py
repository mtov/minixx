from src.checkout import calculate_order_total


def test_no_promotion_keeps_original_total():
    items = [
        {"sku": "A", "price": 30.0, "quantity": 2, "is_eligible": True, "is_clearance": False},
    ]

    assert calculate_order_total(items, None) == 60.0


def test_invalid_promotion_is_ignored():
    items = [
        {"sku": "A", "price": 25.0, "quantity": 3, "is_eligible": True, "is_clearance": False},
    ]

    assert calculate_order_total(items, "NOPE") == 75.0


def test_applies_half_off_to_cheapest_unit_in_group_of_three():
    items = [
        {"sku": "A", "price": 40.0, "quantity": 1, "is_eligible": True, "is_clearance": False},
        {"sku": "B", "price": 25.0, "quantity": 1, "is_eligible": True, "is_clearance": False},
        {"sku": "C", "price": 10.0, "quantity": 1, "is_eligible": True, "is_clearance": False},
    ]

    assert calculate_order_total(items, "BUY2GET50") == 70.0


def test_quantities_count_as_repeated_units():
    items = [
        {"sku": "A", "price": 12.0, "quantity": 2, "is_eligible": True, "is_clearance": False},
        {"sku": "B", "price": 8.0, "quantity": 1, "is_eligible": True, "is_clearance": False},
    ]

    assert calculate_order_total(items, "BUY2GET50") == 28.0


def test_clearance_and_ineligible_items_do_not_participate():
    items = [
        {"sku": "A", "price": 30.0, "quantity": 1, "is_eligible": True, "is_clearance": False},
        {"sku": "B", "price": 20.0, "quantity": 1, "is_eligible": False, "is_clearance": False},
        {"sku": "C", "price": 10.0, "quantity": 2, "is_eligible": True, "is_clearance": True},
        {"sku": "D", "price": 15.0, "quantity": 2, "is_eligible": True, "is_clearance": False},
    ]

    assert calculate_order_total(items, "BUY2GET50") == 92.5


def test_multiple_groups_discount_multiple_units():
    items = [
        {"sku": "A", "price": 20.0, "quantity": 2, "is_eligible": True, "is_clearance": False},
        {"sku": "B", "price": 15.0, "quantity": 2, "is_eligible": True, "is_clearance": False},
        {"sku": "C", "price": 10.0, "quantity": 2, "is_eligible": True, "is_clearance": False},
    ]

    assert calculate_order_total(items, "BUY2GET50") == 77.5


def test_rounds_only_the_final_total():
    items = [
        {"sku": "A", "price": 19.99, "quantity": 2, "is_eligible": True, "is_clearance": False},
        {"sku": "B", "price": 9.99, "quantity": 1, "is_eligible": True, "is_clearance": False},
    ]

    assert calculate_order_total(items, "BUY2GET50") == 44.98
