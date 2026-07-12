from __future__ import annotations

from .context import AgentContext, AgentResponse
from .patches import apply_patch, save_patch, validate_and_repair_patch
from .protocol import looks_like_patch
from .tools import run_tests

CODE_CHANGE_KEYWORDS = ("rename", "refactor", "change", "update", "modify", "fix", "create", "implement")
BUG_FIX_KEYWORDS = ("bug", "fix", "failing test", "tests pass")


def is_code_change_task(prompt: str) -> bool:
    return any(keyword in prompt for keyword in CODE_CHANGE_KEYWORDS)


def is_bug_fix_task(prompt: str) -> bool:
    return any(keyword in prompt for keyword in BUG_FIX_KEYWORDS)


def tests_passed(test_output: str) -> bool:
    return "passed" in test_output.lower()


def handle_finish(
    context: AgentContext,
    agent_response: AgentResponse,
) -> AgentResponse:
    prompt = context.user_prompt.lower()
    if looks_like_patch(agent_response.action_input):
        agent_response.action_input = validate_and_repair_patch(context.workspace_path, agent_response.action_input)
        save_patch(context.workspace_path, agent_response.action_input)
        apply_patch(context.workspace_path)
        if is_bug_fix_task(prompt):
            test_output = run_tests(context.workspace_path)
            if not tests_passed(test_output):
                raise ValueError(f"Post-apply tests failed:\n{test_output}")
    elif is_code_change_task(prompt):
        raise ValueError("Finish output must be a unified diff patch for code-change tasks.")

    return agent_response
