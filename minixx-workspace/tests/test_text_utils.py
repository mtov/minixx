from src.text_utils import slugify

def test_basic_slug():
    assert slugify("Hello World") == "hello-world"

def test_accents_are_removed():
    assert slugify("Manutenção de Software") == "manutencao-de-software"

def test_multiple_accents_are_normalized():
    assert slugify("ÁéÍóÚ ç ãõ") == "aeiou-c-ao"

def test_repeated_separators():
    assert slugify("  A---B___C!!! ") == "a-b-c"

def test_empty_slug_fallback():
    assert slugify("!!!") == "item"

def test_empty_slug_fallback_after_normalization():
    assert slugify("___---   !!!") == "item"
