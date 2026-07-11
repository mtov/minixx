import re

def slugify(title: str) -> str:
    value = title.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")
