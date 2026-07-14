from __future__ import annotations

from pathlib import Path

from minixx.agentic_loop import (
    INVALID_FINISH_MESSAGE,
    agentic_loop,
    format_failure_message,
    format_success_message,
    patch_target_paths,
    print_final_result,
    summarize_missing_rereads,
    summarize_test_failure_output,
    workspace_relative_read_path,
)
from minixx.context import AgentContext, AgentResponse, ModelConfig
from minixx.finish_handler import PostApplyTestsFailedError


def build_context(post_apply_tests_passed: bool = False) -> AgentContext:
    return AgentContext(
        model_config=ModelConfig(
            model="openai-compatible",
            timeout_seconds=30,
            openai_base_url=None,
            openai_model="gpt-5.4-mini",
            openai_api_key_env="OPENAI_API_KEY",
        ),
        system_prompt="system",
        user_prompt="prompt",
        source_workspace_path=Path("/tmp/source"),
        workspace_path=Path("/tmp/runtime"),
        post_apply_tests_passed=post_apply_tests_passed,
    )


def test_format_success_message_for_unified_diff_patch() -> None:
    result = format_success_message(build_context(), "--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+new\n")

    assert result == "Minixx result: success. Patch applied successfully."


def test_format_success_message_mentions_post_apply_tests_when_available() -> None:
    result = format_success_message(
        build_context(post_apply_tests_passed=True),
        "--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+new\n",
    )

    assert result == "Minixx result: success. Patch applied successfully. Post-apply tests passed."


def test_format_success_message_for_non_patch_results() -> None:
    result = format_success_message(build_context(), "Task completed successfully.")

    assert result == "Minixx result: success. Task completed successfully."


def test_format_success_message_for_empty_results() -> None:
    result = format_success_message(build_context(), "  ")

    assert result == "Minixx result: success."


def test_format_failure_message() -> None:
    result = format_failure_message(ValueError("Post-apply tests failed"))

    assert result == "Minixx result: failed. Post-apply tests failed"


def test_print_final_result_prints_summary_for_unified_diff_patches(capsys) -> None:
    print_final_result(build_context(), "--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+new\n")

    captured = capsys.readouterr()

    assert captured.out == "Minixx result: success. Patch applied successfully.\n"


def test_print_final_result_mentions_post_apply_tests_when_available(capsys) -> None:
    print_final_result(
        build_context(post_apply_tests_passed=True),
        "--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+new\n",
    )

    captured = capsys.readouterr()

    assert captured.out == "Minixx result: success. Patch applied successfully. Post-apply tests passed.\n"


def test_print_final_result_prints_summary_for_non_patch_results(capsys) -> None:
    print_final_result(build_context(), "Task completed successfully.")

    captured = capsys.readouterr()

    assert captured.out == "Minixx result: success. Task completed successfully.\n"


def test_agentic_loop_retries_after_invalid_finish(monkeypatch, capsys) -> None:
    context = build_context()
    responses = iter(
        [
            AgentResponse(thought="need more context", action="finish", action_input="I am done."),
            AgentResponse(
                thought="done",
                action="finish",
                action_input="--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+new\n",
            ),
        ]
    )
    seen_histories: list[str] = []

    def fake_get_agent_response(_context: AgentContext, history: str) -> AgentResponse:
        seen_histories.append(history)
        return next(responses)

    monkeypatch.setattr("minixx.agentic_loop.get_agent_response", fake_get_agent_response)
    monkeypatch.setattr("minixx.agentic_loop.handle_finish", lambda _context, response: response)

    result = agentic_loop(context)
    captured = capsys.readouterr()

    assert result.startswith("--- a/file.py")
    assert "[1] finish" in captured.out
    assert "[2] finish" in captured.out
    assert seen_histories[0] == "No previous steps."
    assert INVALID_FINISH_MESSAGE in seen_histories[1]


def test_agentic_loop_retries_after_post_apply_test_failure(monkeypatch, capsys) -> None:
    context = build_context()
    responses = iter(
        [
            AgentResponse(
                thought="first try",
                action="finish",
                action_input="--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+attempt1\n",
            ),
            AgentResponse(
                thought="refresh",
                action="read_file",
                action_input="/tmp/reset-runtime/file.py",
            ),
            AgentResponse(
                thought="second try",
                action="finish",
                action_input="--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+attempt2\n",
            ),
        ]
    )
    seen_histories: list[str] = []
    reset_calls: list[Path] = []
    finish_attempts = 0

    def fake_get_agent_response(_context: AgentContext, history: str) -> AgentResponse:
        seen_histories.append(history)
        return next(responses)

    def fake_handle_finish(_context: AgentContext, response: AgentResponse) -> AgentResponse:
        nonlocal finish_attempts
        finish_attempts += 1
        if finish_attempts == 1:
            raise PostApplyTestsFailedError("..F\nassert 1 == 2")
        return response

    def fake_prepare_runtime_workspace(source_workspace_path: Path) -> Path:
        reset_calls.append(source_workspace_path)
        return Path("/tmp/reset-runtime")

    monkeypatch.setattr("minixx.agentic_loop.get_agent_response", fake_get_agent_response)
    monkeypatch.setattr("minixx.agentic_loop.handle_finish", fake_handle_finish)
    monkeypatch.setattr("minixx.agentic_loop.prepare_runtime_workspace", fake_prepare_runtime_workspace)
    monkeypatch.setattr("minixx.agentic_loop.run_tool", lambda _response, _workspace: "file contents")

    result = agentic_loop(context)
    captured = capsys.readouterr()

    assert result.endswith("+attempt2\n")
    assert "[1] finish" in captured.out
    assert "[2] read_file" in captured.out
    assert "[3] finish" in captured.out
    assert reset_calls == [Path("/tmp/source")]
    assert context.workspace_path == Path("/tmp/reset-runtime")
    assert "Post-apply tests failed. The runtime workspace has been reset to the original source state." in seen_histories[1]
    assert "Use the failed test details below to produce a different patch." in seen_histories[1]
    assert "..F\nassert 1 == 2" in seen_histories[1]


def test_summarize_test_failure_output_extracts_failed_cases() -> None:
    output = """.....FF                                                                  [100%]
=================================== FAILURES ===================================
_________________ test_multiple_groups_discount_multiple_units _________________

>       assert calculate_order_total(items, "BUY2GET50") == 75.0
E       AssertionError: assert 77.5 == 75.0

tests/test_checkout.py:57: AssertionError
_______________________ test_rounds_only_the_final_total _______________________

>       assert calculate_order_total(items, "BUY2GET50") == 44.97
E       AssertionError: assert 44.98 == 44.97

tests/test_checkout.py:66: AssertionError
=========================== short test summary info ============================
FAILED tests/test_checkout.py::test_multiple_groups_discount_multiple_units - AssertionError: assert 77.5 == 75.0
FAILED tests/test_checkout.py::test_rounds_only_the_final_total - AssertionError: assert 44.98 == 44.97
"""

    summary = summarize_test_failure_output(output)

    assert "Use the failed test details below to produce a different patch." in summary
    assert "- tests/test_checkout.py::test_multiple_groups_discount_multiple_units: AssertionError: assert 77.5 == 75.0" in summary
    assert "- test_multiple_groups_discount_multiple_units: expected 75.0, got 77.5" in summary
    assert "- tests/test_checkout.py::test_rounds_only_the_final_total: AssertionError: assert 44.98 == 44.97" in summary
    assert "- test_rounds_only_the_final_total: expected 44.97, got 44.98" in summary


def test_patch_target_paths_collects_unique_files() -> None:
    patch = """--- a/src/promotions.py
+++ b/src/promotions.py
@@ -1 +1 @@
-old
+new
--- a/tests/test_checkout.py
+++ b/tests/test_checkout.py
@@ -1 +1 @@
-old
+new
"""

    assert patch_target_paths(patch) == {"src/promotions.py", "tests/test_checkout.py"}


def test_workspace_relative_read_path_returns_workspace_relative_path() -> None:
    context = build_context()
    context.workspace_path = Path("/tmp/runtime")

    relative_path = workspace_relative_read_path(context, "/tmp/runtime/src/promotions.py")

    assert relative_path == "src/promotions.py"


def test_summarize_missing_rereads_lists_paths() -> None:
    summary = summarize_missing_rereads({"src/promotions.py", "tests/test_checkout.py"})

    assert "After the workspace reset" in summary
    assert "- src/promotions.py" in summary
    assert "- tests/test_checkout.py" in summary


def test_agentic_loop_requires_reread_of_patched_files_after_reset(monkeypatch, capsys) -> None:
    context = build_context()
    responses = iter(
        [
            AgentResponse(
                thought="first try",
                action="finish",
                action_input="--- a/src/promotions.py\n+++ b/src/promotions.py\n@@ -1 +1 @@\n-old\n+attempt1\n",
            ),
            AgentResponse(
                thought="second try",
                action="finish",
                action_input="--- a/src/promotions.py\n+++ b/src/promotions.py\n@@ -1 +1 @@\n-old\n+attempt2\n",
            ),
            AgentResponse(
                thought="refresh",
                action="read_file",
                action_input="/tmp/reset-runtime/src/promotions.py",
            ),
            AgentResponse(
                thought="final",
                action="finish",
                action_input="--- a/src/promotions.py\n+++ b/src/promotions.py\n@@ -1 +1 @@\n-old\n+attempt3\n",
            ),
        ]
    )
    finish_attempts = 0
    seen_histories: list[str] = []

    def fake_get_agent_response(_context: AgentContext, history: str) -> AgentResponse:
        seen_histories.append(history)
        return next(responses)

    def fake_handle_finish(_context: AgentContext, response: AgentResponse) -> AgentResponse:
        nonlocal finish_attempts
        finish_attempts += 1
        if finish_attempts == 1:
            raise PostApplyTestsFailedError("..F\nassert 1 == 2")
        return response

    monkeypatch.setattr("minixx.agentic_loop.get_agent_response", fake_get_agent_response)
    monkeypatch.setattr("minixx.agentic_loop.handle_finish", fake_handle_finish)
    monkeypatch.setattr("minixx.agentic_loop.prepare_runtime_workspace", lambda _source: Path("/tmp/reset-runtime"))
    monkeypatch.setattr("minixx.agentic_loop.run_tool", lambda _response, _workspace: "file contents")

    result = agentic_loop(context)
    captured = capsys.readouterr()

    assert result.endswith("+attempt3\n")
    assert "[2] finish" in captured.out
    assert "Files to reread:" in seen_histories[2]
    assert "- src/promotions.py" in seen_histories[2]
