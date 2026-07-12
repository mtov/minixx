from src.inventory import reserve_items


def test_successful_reservation():
    inventory = {"book": 5, "pen": 2}
    assert reserve_items(inventory, {"book": 3}) is True
    assert inventory == {"book": 2, "pen": 2}


def test_successful_reservation_can_reduce_stock_to_zero():
    inventory = {"book": 3, "pen": 2}
    assert reserve_items(inventory, {"book": 3, "pen": 2}) is True
    assert inventory == {"book": 0, "pen": 0}


def test_failed_reservation_does_not_change_inventory():
    inventory = {"book": 5, "pen": 2}
    assert reserve_items(inventory, {"book": 3, "pen": 5}) is False
    assert inventory == {"book": 5, "pen": 2}

def test_missing_item_fails_without_changes():
    inventory = {"book": 5}
    assert reserve_items(inventory, {"book": 1, "notebook": 1}) is False
    assert inventory == {"book": 5}


def test_empty_order_succeeds_without_changes():
    inventory = {"book": 5}
    assert reserve_items(inventory, {}) is True
    assert inventory == {"book": 5}
