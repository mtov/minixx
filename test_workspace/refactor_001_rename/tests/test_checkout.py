from src.checkout import build_checkout_summary, calculate_order_total
from src.discounts import lookup_coupon, normalize_coupon_code


def test_normalize_coupon_code_trims_and_uppercases():
    assert normalize_coupon_code(" save10 ") == "SAVE10"


def test_lookup_coupon_returns_rate():
    assert lookup_coupon("save20") == 0.20


def test_calculate_order_total_uses_coupon_code_argument():
    items = [
        {"sku": "A", "price": 50.0, "quantity": 2},
    ]

    assert calculate_order_total(items, coupon_code="SAVE10") == 90.0


def test_build_checkout_summary_uses_coupon_code_key():
    items = [
        {"sku": "A", "price": 40.0, "quantity": 1},
        {"sku": "B", "price": 10.0, "quantity": 2},
    ]

    assert build_checkout_summary(items, coupon_code=" save10 ") == {
        "subtotal": 60.0,
        "couponCode": "SAVE10",
        "total": 54.0,
    }


def test_build_checkout_summary_keeps_none_for_missing_code():
    items = [
        {"sku": "A", "price": 30.0, "quantity": 1},
    ]

    assert build_checkout_summary(items, coupon_code=None) == {
        "subtotal": 30.0,
        "couponCode": None,
        "total": 30.0,
    }
