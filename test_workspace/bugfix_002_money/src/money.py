def format_brl(cents: int) -> str:
    amount = cents / 100
    return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
