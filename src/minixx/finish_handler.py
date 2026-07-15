from __future__ import annotations

from .context import AgentContext, AgentResponse, FinishResult
from .patches import apply_patch, save_patch, validate_and_repair_patch
from .protocol import looks_like_patch
from .traces import trace_finish_event
from .tools import run_tests_with_status

INVALID_FINISH_PATCH_MESSAGE = "Finish output must be a unified diff patch."


def _trace_and_raise(stage: str, exc: Exception) -> None:
    trace_finish_event("failed", stage, str(exc))
    raise exc


def handle_finish(
    context: AgentContext,
    agent_response: AgentResponse,
) -> FinishResult:
    workspace_path = context.workspace_path
    patch_text = agent_response.action_input

    if not looks_like_patch(patch_text):
        trace_finish_event(
            "failed",
            "finish_validation",
            INVALID_FINISH_PATCH_MESSAGE,
        )
        raise ValueError(INVALID_FINISH_PATCH_MESSAGE)

    try:
        patch_text = validate_and_repair_patch(workspace_path, patch_text)
        agent_response.action_input = patch_text
    except Exception as exc:  # noqa: BLE001
        _trace_and_raise("patch_validation", exc)

    try:
        save_patch(workspace_path, patch_text)
    except Exception as exc:  # noqa: BLE001
        _trace_and_raise("save_patch", exc)

    try:
        apply_patch(workspace_path)
    except Exception as exc:  # noqa: BLE001
        _trace_and_raise("apply_patch", exc)

    tests_succeeded, test_output = run_tests_with_status(workspace_path)
    if not tests_succeeded:
        trace_finish_event("failed", "post_apply_tests", test_output)
        return FinishResult(
            status="post_apply_tests_failed",
            agent_response=agent_response,
            test_output=test_output,
        )

    context.post_apply_tests_passed = True
    trace_finish_event("completed", "finish")
    return FinishResult(status="applied", agent_response=agent_response)
