from __future__ import annotations

from pathlib import Path

import pytest

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
