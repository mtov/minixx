from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from minixx import command_runner


def test_run_mutating_command_requires_approval(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "n")

    with pytest.raises(PermissionError, match="User rejected command"):
        command_runner.run_mutating_command(["git", "status"], tmp_path)


def test_run_mutating_command_executes_after_approval(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "y")

    def fake_run(command: list[str], cwd: Path, capture_output: bool, text: bool) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setattr(command_runner.subprocess, "run", fake_run)

    result = command_runner.run_mutating_command(["git", "status"], tmp_path)

    assert result.returncode == 0


def test_run_mutating_command_prints_preview_when_provided(capsys, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "n")

    with pytest.raises(PermissionError):
        command_runner.run_mutating_command(
            ["git", "apply", "patch.txt"],
            tmp_path,
            preview="--- a/file.py\n+++ b/file.py",
        )

    captured = capsys.readouterr()
    assert "Command preview:" in captured.out
    assert "--- a/file.py" in captured.out
