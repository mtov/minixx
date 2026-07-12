from src.text_utils import slugify


def test_basic_slug() -> None:
    assert slugify("Hello World") == "hello-world"


def test_accents_are_removed() -> None:
    assert slugify("Software Maintenance") == "software-maintenance"
    assert slugify("ação") == "acao"


def test_multiple_accents_are_normalized() -> None:
    assert slugify("ÁéÍóÚ ç ãõ") == "aeiou-c-ao"


def test_repeated_separators() -> None:
    assert slugify("  A---B___C!!! ") == "a-b-c"


def test_numbers_are_preserved() -> None:
    assert slugify("Version 2.0 Release 15") == "version-2-0-release-15"


def test_empty_slug_fallback() -> None:
    assert slugify("!!!") == "item"


def test_empty_slug_fallback_after_normalization() -> None:
    assert slugify("___---   !!!") == "item"


def test_leading_and_trailing_separators_are_removed_after_normalization() -> None:
    assert slugify("___ação___") == "acao"
