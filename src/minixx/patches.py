from __future__ import annotations

from pathlib import Path


def save_patch(workspace_path: Path, patch_text: str) -> None:
    patch_path = workspace_path / "patch.txt"
    patch_path.write_text(patch_text, encoding="utf-8")
