PROMOTIONS = {
    "BUY2GET50": "buy_2_get_50",
}


def promotion_discount(items: list[dict], promotion_code: str | None) -> float:
    if not promotion_code:
        return 0.0

    if promotion_code not in PROMOTIONS:
        return 0.0

    return 0.0
