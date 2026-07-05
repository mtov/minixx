from __future__ import annotations

from .context import AgentContext, AgentHistory, AgentResponse
from .finish_reviewer import review_finish
from .patches import save_patch
from .protocol import (
    PATCH_REPAIR_PROMPT,
    PRECONDITION_REPAIR_PROMPT,
    looks_like_patch,
    parse_response,
    trace_response_validation_error,
)
from .traces import trace_repair_attempt
from .llms import call_llm


def format_agent_response(agent_response: AgentResponse) -> str:
    return (
        f"Thought: {agent_response.thought}\n"
        f"Action: {agent_response.action}\n"
        f"Action Input: {agent_response.action_input}\n"
        f"Action Description: {agent_response.action_description}"
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


def validate_finish_preconditions(
    agent_response: AgentResponse,
    user_prompt: str,
    agent_history: AgentHistory,
) -> None:
    if is_bug_fix_task(user_prompt) and not agent_history.contains_action("run_tests"):
        raise ValueError("Bug-fixing tasks must use run_tests before finish.")
    if is_retrieval_task(user_prompt) and not has_observation_action(agent_history):
        raise ValueError("Retrieval tasks must use list_files, read_file, or find_text before finish.")


def validate_finish_output(agent_response: AgentResponse, user_prompt: str) -> None:
    if not is_code_change_task(user_prompt):
        return
    if not looks_like_patch(agent_response.action_input):
        raise ValueError("Finish output must be a unified diff patch for code-change tasks.")


def repair_finish_with_prompt(
    context: AgentContext,
    user_message: str,
    repair_prompt: str,
    repair_kind: str,
    reason: str,
) -> AgentResponse:
    trace_repair_attempt(repair_kind, reason)
    repair_message = f"{user_message}\n\n{repair_prompt}"
    response = call_llm(context, repair_message, "Repair Response")
    return parse_response(response)


def repair_finish_output(context: AgentContext, user_message: str, reason: str) -> AgentResponse:
    return repair_finish_with_prompt(
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
    return repair_finish_with_prompt(
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
    reviewed_response = review_finish(context, user_message, agent_history, agent_response)
    if reviewed_response is not None:
        agent_response = reviewed_response

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

    if looks_like_patch(agent_response.action_input):
        save_patch(context.workspace_path, agent_response.action_input)

    return agent_response
