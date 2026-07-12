from src.money import format_brl

def test_zero():
    assert format_brl(0) == "R$ 0,00"

def test_positive_value():
    assert format_brl(123456) == "R$ 1.234,56"

def test_small_value():
    assert format_brl(5) == "R$ 0,05"

def test_negative_value():
    assert format_brl(-987) == "-R$ 9,87"
