from __future__ import annotations

from .context import AgentContext, AgentResponse
from .patches import apply_patch, save_patch, validate_and_repair_patch
from .protocol import looks_like_patch
from .traces import trace_finish_event
from .tools import run_tests_with_status

CODE_CHANGE_KEYWORDS = (
    "rename",
    "refactor",
    "change",
    "update",
    "modify",
    "fix",
    "create",
    "implement",
)


def is_code_change_task(prompt: str) -> bool:
    return any(keyword in prompt for keyword in CODE_CHANGE_KEYWORDS)


class PostApplyTestsFailedError(ValueError):
    def __init__(self, test_output: str) -> None:
        super().__init__(f"Post-apply tests failed:\n{test_output}")
        self.test_output = test_output


def handle_finish(
    context: AgentContext,
    agent_response: AgentResponse,
) -> AgentResponse:
    if looks_like_patch(agent_response.action_input):
        try:
            agent_response.action_input = validate_and_repair_patch(
                context.workspace_path,
                agent_response.action_input,
            )
        except Exception as exc:  # noqa: BLE001
            trace_finish_event("failed", "patch_validation", str(exc))
            raise

        try:
            save_patch(context.workspace_path, agent_response.action_input)
        except Exception as exc:  # noqa: BLE001
            trace_finish_event("failed", "save_patch", str(exc))
            raise

        try:
            apply_patch(context.workspace_path)
        except Exception as exc:  # noqa: BLE001
            trace_finish_event("failed", "apply_patch", str(exc))
            raise

        tests_succeeded, test_output = run_tests_with_status(context.workspace_path)
        if not tests_succeeded:
            trace_finish_event("failed", "post_apply_tests", test_output)
            raise PostApplyTestsFailedError(test_output)
        context.post_apply_tests_passed = True
        trace_finish_event("completed", "finish")
    elif is_code_change_task(context.user_prompt.lower()):
        trace_finish_event(
            "failed",
            "finish_validation",
            "Finish output must be a unified diff patch for code-change tasks.",
        )
        raise ValueError("Finish output must be a unified diff patch for code-change tasks.")

    return agent_response
