from validators import validate_name
from formatters import format_name


def build_welcome_message(name: str) -> str:
    validate_name(name)
    formatted_name = format_name(name)
    return f"Welcome, {formatted_name}!"
