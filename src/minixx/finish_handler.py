from __future__ import annotations

from .context import AgentContext, AgentHistory, AgentResponse
from .patches import apply_patch, save_patch, validate_and_repair_patch
from .protocol import (
    PATCH_REPAIR_PROMPT,
    PRECONDITION_REPAIR_PROMPT,
    looks_like_patch,
    repair_response_with_prompt,
    trace_response_validation_error,
)
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


def has_observation_action(agent_history: AgentHistory) -> bool:
    return any(
        agent_history.contains_action(action)
        for action in ("list_files", "read_file", "find_text")
    )


def has_content_observation_action(agent_history: AgentHistory) -> bool:
    return any(
        agent_history.contains_action(action)
        for action in ("read_file", "find_text")
    )


def validate_finish_preconditions(
    agent_response: AgentResponse,
    user_prompt: str,
    agent_history: AgentHistory,
) -> None:
    if agent_response.action != "finish":
        return

    if is_bug_fix_task(user_prompt) and not agent_history.contains_action("run_tests"):
        raise ValueError("Bug-fixing tasks must use run_tests before finish.")
    if is_retrieval_task(user_prompt) and not has_content_observation_action(agent_history):
        raise ValueError("Retrieval tasks must use read_file or find_text before finish.")


def validate_finish_output(agent_response: AgentResponse, user_prompt: str) -> None:
    if not is_code_change_task(user_prompt):
        return
    if not looks_like_patch(agent_response.action_input):
        raise ValueError("Finish output must be a unified diff patch for code-change tasks.")


def validate_patch_output(context: AgentContext, agent_response: AgentResponse, user_prompt: str) -> None:
    if not is_code_change_task(user_prompt):
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


def repair_finish_output(context: AgentContext, user_message: str, reason: str) -> AgentResponse:
    return repair_response_with_prompt(
        context,
        user_message,
        PATCH_REPAIR_PROMPT,
        "Finish output repair",
        reason,
    )


def repair_finish_preconditions(
    context: AgentContext,
    user_message: str,
    reason: str,
) -> AgentResponse:
    return repair_response_with_prompt(
        context,
        user_message,
        PRECONDITION_REPAIR_PROMPT,
        "Finish precondition repair",
        reason,
    )


def handle_finish(
    context: AgentContext,
    user_message: str,
    agent_history: AgentHistory,
    agent_response: AgentResponse,
) -> AgentResponse:
    try:
        validate_finish_preconditions(agent_response, context.user_prompt, agent_history)
    except ValueError as exc:
        trace_response_validation_error(str(exc), format_agent_response(agent_response))
        agent_response = repair_finish_preconditions(context, user_message, str(exc))
        validate_finish_preconditions(agent_response, context.user_prompt, agent_history)

    if agent_response.action != "finish":
        return agent_response

    try:
        validate_finish_output(agent_response, context.user_prompt)
    except ValueError as exc:
        trace_response_validation_error(str(exc), format_agent_response(agent_response))
        agent_response = repair_finish_output(context, user_message, str(exc))
        validate_finish_output(agent_response, context.user_prompt)

    try:
        validate_patch_output(context, agent_response, context.user_prompt)
    except ValueError as exc:
        trace_response_validation_error(str(exc), format_agent_response(agent_response))
        agent_response = repair_finish_output(context, user_message, str(exc))
        validate_finish_output(agent_response, context.user_prompt)
        validate_patch_output(context, agent_response, context.user_prompt)

    if looks_like_patch(agent_response.action_input):
        save_patch(context.workspace_path, agent_response.action_input)
        apply_patch(context.workspace_path)
        validate_post_apply_tests(context)

    return agent_response
