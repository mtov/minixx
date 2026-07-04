import pytest

from service import build_welcome_message


def test_build_welcome_message_formats_valid_name() -> None:
    assert build_welcome_message("  aLiCe  ") == "Welcome, Alice!"


def test_build_welcome_message_rejects_whitespace_only_name() -> None:
    with pytest.raises(ValueError):
        build_welcome_message("   ")
