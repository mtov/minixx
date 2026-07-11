from __future__ import annotations

from pathlib import Path

from minixx import inputs


def test_prepare_runtime_workspace_recreates_fixed_directory(tmp_path: Path, monkeypatch) -> None:
    source_workspace = tmp_path / "source"
    source_workspace.mkdir()
    (source_workspace / "prompt.txt").write_text("first prompt", encoding="utf-8")

    runtime_workspace = tmp_path / "minixx-workspace"
    monkeypatch.setattr(inputs, "RUNTIME_WORKSPACE_PATH", runtime_workspace)

    prepared_workspace = inputs.prepare_runtime_workspace(source_workspace)

    assert prepared_workspace == runtime_workspace
    assert (runtime_workspace / "prompt.txt").read_text(encoding="utf-8") == "first prompt"

    (runtime_workspace / "stale.txt").write_text("stale", encoding="utf-8")
    (source_workspace / "prompt.txt").write_text("second prompt", encoding="utf-8")

    prepared_workspace = inputs.prepare_runtime_workspace(source_workspace)

    assert prepared_workspace == runtime_workspace
    assert not (runtime_workspace / "stale.txt").exists()
    assert (runtime_workspace / "prompt.txt").read_text(encoding="utf-8") == "second prompt"
