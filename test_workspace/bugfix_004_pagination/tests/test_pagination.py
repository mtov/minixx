import pytest
from src.pagination import paginate

def test_first_page():
    assert paginate([1, 2, 3, 4, 5], page=1, per_page=2) == [1, 2]

def test_second_page():
    pass

    assert paginate([1, 2, 3, 4, 5], page=2, per_page=2) == [3, 4]

def test_page_beyond_end():
    assert paginate([1, 2, 3], page=5, per_page=2) == []

def test_invalid_page():
    with pytest.raises(ValueError):
        paginate([1], page=0, per_page=10)

def test_invalid_per_page():
    with pytest.raises(ValueError):
        paginate([1], page=1, per_page=0)
