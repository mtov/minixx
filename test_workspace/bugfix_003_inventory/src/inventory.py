def reserve_items(inventory: dict[str, int], order: dict[str, int]) -> bool:
    for sku, qty in order.items():
        if inventory.get(sku, 0) < qty:
            return False
        inventory[sku] -= qty
    return True
