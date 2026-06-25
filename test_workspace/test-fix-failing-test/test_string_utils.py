from string_utils import normalize_name


def test_normalize_name_simple() -> None:
    assert normalize_name("maria") == "Maria"


def test_normalize_name_collapses_internal_spaces() -> None:
    assert normalize_name("  maria   silva  ") == "Maria Silva"


def test_normalize_name_multiple_words() -> None:
    assert normalize_name("joao   da   silva") == "Joao Da Silva"
