from __future__ import annotations

from .context import AgentContext, AgentHistory, AgentResponse
from .patches import apply_patch, save_patch, validate_and_repair_patch
from .protocol import looks_like_patch
from .traces import trace_validation_error
from .tools import run_tests


def format_agent_response(agent_response: AgentResponse) -> str:
    return (
        f"Thought: {agent_response.thought}\n"
        f"Action: {agent_response.action}\n"
        f"Action Input: {agent_response.action_input}"
    )


def is_code_change_task(user_prompt: str) -> bool:
    prompt = user_prompt.lower()
    return any(keyword in prompt for keyword in ("rename", "refactor", "change", "update", "modify", "fix", "create", "implement"))


def is_bug_fix_task(user_prompt: str) -> bool:
    prompt = user_prompt.lower()
    return any(keyword in prompt for keyword in ("bug", "fix", "failing test", "tests pass"))


def is_retrieval_task(user_prompt: str) -> bool:
    prompt = user_prompt.lower()
    return any(
        keyword in prompt
        for keyword in (
            "read",
            "find",
            "locate",
            "inspect",
            "secret",
            "symbol",
            "file",
        )
    )


def validate_finish_output(agent_response: AgentResponse, user_prompt: str) -> None:
    if not is_code_change_task(user_prompt):
        return
    if not looks_like_patch(agent_response.action_input):
        raise ValueError("Finish output must be a unified diff patch for code-change tasks.")


def validate_patch_output(context: AgentContext, agent_response: AgentResponse) -> None:
    if not looks_like_patch(agent_response.action_input):
        return
    repaired_patch = validate_and_repair_patch(context.workspace_path, agent_response.action_input)
    if repaired_patch != agent_response.action_input:
        agent_response.action_input = repaired_patch


def validate_post_apply_tests(context: AgentContext) -> None:
    if not is_bug_fix_task(context.user_prompt):
        return

    print("Running tests after applying patch...", flush=True)
    test_output = run_tests(context.workspace_path)
    if "passed" not in test_output.lower():
        raise ValueError(f"Post-apply tests failed:\n{test_output}")


def handle_finish(
    context: AgentContext,
    user_message: str,
    agent_history: AgentHistory,
    agent_response: AgentResponse,
) -> AgentResponse:
    if agent_response.action != "finish":
        return agent_response

    if is_retrieval_task(context.user_prompt) and not any(
        agent_history.contains_action(action)
        for action in ("read_file", "find_text")
    ):
        raise ValueError("Retrieval tasks must use read_file or find_text before finish.")

    try:
        validate_finish_output(agent_response, context.user_prompt)
    except ValueError as exc:
        trace_validation_error(str(exc), format_agent_response(agent_response))
        raise

    if looks_like_patch(agent_response.action_input):
        validate_patch_output(context, agent_response)
        save_patch(context.workspace_path, agent_response.action_input)
        apply_patch(context.workspace_path)
        validate_post_apply_tests(context)

    return agent_response
