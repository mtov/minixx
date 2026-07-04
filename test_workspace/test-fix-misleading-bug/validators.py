def validate_name(name: str) -> None:
    if not name:
        raise ValueError("Name must not be empty.")
