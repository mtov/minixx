from copy import deepcopy

from src.config_loader import load_config


def test_preserves_defaults_when_no_overrides():
    defaults = {"debug": False, "port": 8080}
    assert load_config(defaults, {}) == {"debug": False, "port": 8080}


def test_overrides_scalar_values():
    defaults = {"debug": False, "port": 8080}
    overrides = {"debug": True}
    assert load_config(defaults, overrides) == {"debug": True, "port": 8080}


def test_merges_nested_sections_recursively():
    defaults = {
        "server": {"host": "localhost", "port": 8080},
        "logging": {"level": "info"},
    }
    overrides = {"server": {"port": 9090}}
    assert load_config(defaults, overrides) == {
        "server": {"host": "localhost", "port": 9090},
        "logging": {"level": "info"},
    }


def test_merges_deeply_nested_sections_recursively():
    defaults = {
        "features": {
            "search": {"enabled": True, "timeout": 3},
            "ui": {"theme": "light"},
        }
    }
    overrides = {
        "features": {
            "search": {"timeout": 10},
        }
    }
    assert load_config(defaults, overrides) == {
        "features": {
            "search": {"enabled": True, "timeout": 10},
            "ui": {"theme": "light"},
        }
    }


def test_inputs_are_not_mutated():
    defaults = {"server": {"host": "localhost", "port": 8080}}
    overrides = {"server": {"port": 9090}}
    defaults_snapshot = deepcopy(defaults)
    overrides_snapshot = deepcopy(overrides)

    load_config(defaults, overrides)

    assert defaults == defaults_snapshot
    assert overrides == overrides_snapshot


def test_result_does_not_share_nested_dicts_with_inputs():
    defaults = {"server": {"host": "localhost", "port": 8080}}
    merged = load_config(defaults, {})

    merged["server"]["port"] = 9999

    assert defaults == {"server": {"host": "localhost", "port": 8080}}
