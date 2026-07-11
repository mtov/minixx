from __future__ import annotations

from pathlib import Path

from minixx import tools


def test_read_file_prints_the_file_name(capsys, tmp_path: Path) -> None:
    file_path = tmp_path / "example.txt"
    file_path.write_text("hello", encoding="utf-8")

    content = tools.read_file("example.txt", tmp_path)

    captured = capsys.readouterr()
    assert content == "hello"
    assert "Reading file: example.txt" in captured.out
