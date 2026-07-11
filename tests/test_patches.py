from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from minixx import patches
from minixx.patches import auto_repair_patch_text, validate_patch, validate_and_repair_patch


def write_sample_file(workspace_path: Path) -> None:
    (workspace_path / "hello.txt").write_text("hello\nworld\n", encoding="utf-8")


def test_validate_patch_accepts_clean_patch(tmp_path: Path) -> None:
    write_sample_file(tmp_path)
    patch_text = """--- a/hello.txt
+++ b/hello.txt
@@ -1,2 +1,2 @@
-hello
+hi
 world
"""

    validate_patch(tmp_path, patch_text)


def test_validate_patch_rejects_non_applicable_patch(tmp_path: Path) -> None:
    write_sample_file(tmp_path)
    patch_text = """--- a/hello.txt
+++ b/hello.txt
@@ -1,2 +1,2 @@
-missing
+hi
 world
"""

    with pytest.raises(ValueError, match="Patch does not apply cleanly"):
        validate_patch(tmp_path, patch_text)


def test_auto_repair_patch_text_strips_code_fences_and_prose() -> None:
    patch_text = """Here is the patch:

```diff
--- a/hello.txt
+++ b/hello.txt
@@ -1,2 +1,2 @@
-hello
+hi
 world
```
"""

    repaired = auto_repair_patch_text(patch_text)

    assert repaired == """--- a/hello.txt
+++ b/hello.txt
@@ -1,2 +1,2 @@
-hello
+hi
 world
"""


def test_validate_and_repair_patch_fixes_missing_context_prefix(tmp_path: Path) -> None:
    write_sample_file(tmp_path)
    patch_text = """--- a/hello.txt
+++ b/hello.txt
@@ -1,2 +1,2 @@
-hello
+hi
world
"""

    repaired = validate_and_repair_patch(tmp_path, patch_text)

    assert repaired == """--- a/hello.txt
+++ b/hello.txt
@@ -1,2 +1,2 @@
-hello
+hi
 world
"""


def test_validate_and_repair_patch_recalculates_hunk_header_counts(tmp_path: Path) -> None:
    write_sample_file(tmp_path)
    patch_text = """--- a/hello.txt
+++ b/hello.txt
@@ -1,6 +1,14 @@
-hello
+hi
 world
"""

    repaired = validate_and_repair_patch(tmp_path, patch_text)

    assert repaired == """--- a/hello.txt
+++ b/hello.txt
@@ -1,2 +1,2 @@
-hello
+hi
 world
"""


def test_run_mutating_command_requires_approval(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "n")

    with pytest.raises(PermissionError, match="User rejected command"):
        patches._run_mutating_command(["git", "status"], tmp_path)


def test_run_mutating_command_executes_after_approval(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "y")

    def fake_run(command: list[str], cwd: Path, capture_output: bool, text: bool) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setattr(patches.subprocess, "run", fake_run)

    result = patches._run_mutating_command(["git", "status"], tmp_path)

    assert result.returncode == 0


def test_run_mutating_command_prints_preview_when_provided(capsys, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "n")

    with pytest.raises(PermissionError):
        patches._run_mutating_command(
            ["git", "apply", "patch.txt"],
            tmp_path,
            preview="--- a/file.py\n+++ b/file.py",
        )

    captured = capsys.readouterr()
    assert "Command preview:" in captured.out
    assert "--- a/file.py" in captured.out
