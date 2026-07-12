from src.merge_utils import merge_dicts


def load_config(defaults: dict, overrides: dict | None = None) -> dict:
    overrides = overrides or {}
    return merge_dicts(defaults, overrides)
