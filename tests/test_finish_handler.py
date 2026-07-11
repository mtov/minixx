from __future__ import annotations

from pathlib import Path

import pytest

from minixx.context import AgentContext, AgentHistory, AgentResponse, ModelConfig
from minixx.finish_handler import handle_finish


def build_context(tmp_path: Path, user_prompt: str) -> AgentContext:
    return AgentContext(
        model_config=ModelConfig(
            model="openai-compatible",
            timeout_seconds=30,
            codex_command=None,
            openai_base_url=None,
            openai_model="gpt-5.4-mini",
            openai_api_key_env="OPENAI_API_KEY",
            working_directory=tmp_path,
        ),
        system_prompt="system",
        user_prompt=user_prompt,
        source_workspace_path=tmp_path,
        workspace_path=tmp_path,
    )


def build_history() -> AgentHistory:
    history = AgentHistory()
    history.append(
        1,
        AgentResponse(thought="inspect", action="run_tests", action_input=""),
        "1 passed",
    )
    return history


def test_handle_finish_runs_post_apply_tests_for_bug_fix(monkeypatch, tmp_path: Path) -> None:
    context = build_context(tmp_path, "Fix the bug in slugify and make tests pass.")
    history = build_history()
    response = AgentResponse(
        thought="done",
        action="finish",
        action_input="--- a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-old\n+new\n",
    )
    calls: list[str] = []

    monkeypatch.setattr("minixx.finish_handler.review_finish", lambda *args: None)
    monkeypatch.setattr("minixx.finish_handler.validate_and_repair_patch", lambda *_args: response.action_input)
    monkeypatch.setattr("minixx.finish_handler.save_patch", lambda *_args: calls.append("save_patch"))
    monkeypatch.setattr("minixx.finish_handler.apply_patch", lambda *_args: calls.append("apply_patch"))
    monkeypatch.setattr("minixx.finish_handler.run_tests", lambda *_args: "1 passed")

    result = handle_finish(context, "user message", history, response)

    assert result is response
    assert calls == ["save_patch", "apply_patch"]


def test_handle_finish_raises_when_post_apply_tests_fail(monkeypatch, tmp_path: Path) -> None:
    context = build_context(tmp_path, "Fix the bug in slugify and make tests pass.")
    history = build_history()
    response = AgentResponse(
        thought="done",
        action="finish",
        action_input="--- a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-old\n+new\n",
    )

    monkeypatch.setattr("minixx.finish_handler.review_finish", lambda *args: None)
    monkeypatch.setattr("minixx.finish_handler.validate_and_repair_patch", lambda *_args: response.action_input)
    monkeypatch.setattr("minixx.finish_handler.save_patch", lambda *_args: None)
    monkeypatch.setattr("minixx.finish_handler.apply_patch", lambda *_args: None)
    monkeypatch.setattr("minixx.finish_handler.run_tests", lambda *_args: "1 failed")

    with pytest.raises(ValueError, match="Post-apply tests failed"):
        handle_finish(context, "user message", history, response)


def test_handle_finish_skips_post_apply_tests_for_non_bug_fix(monkeypatch, tmp_path: Path) -> None:
    context = build_context(tmp_path, "Update the README wording.")
    history = AgentHistory()
    history.append(
        1,
        AgentResponse(thought="inspect", action="read_file", action_input="README.md"),
        "Current README contents",
    )
    response = AgentResponse(
        thought="done",
        action="finish",
        action_input="--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old\n+new\n",
    )
    run_tests_called = False

    def fake_run_tests(*_args):
        nonlocal run_tests_called
        run_tests_called = True
        return "1 passed"

    monkeypatch.setattr("minixx.finish_handler.review_finish", lambda *args: None)
    monkeypatch.setattr("minixx.finish_handler.validate_and_repair_patch", lambda *_args: response.action_input)
    monkeypatch.setattr("minixx.finish_handler.save_patch", lambda *_args: None)
    monkeypatch.setattr("minixx.finish_handler.apply_patch", lambda *_args: None)
    monkeypatch.setattr("minixx.finish_handler.run_tests", fake_run_tests)

    result = handle_finish(context, "user message", history, response)

    assert result is response
    assert run_tests_called is False
