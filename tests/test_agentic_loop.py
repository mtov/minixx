from __future__ import annotations

from pathlib import Path

from minixx.agentic_loop import format_failure_message, format_success_message, print_final_result
from minixx.context import AgentContext, ModelConfig


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
