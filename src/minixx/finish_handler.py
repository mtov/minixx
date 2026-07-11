from __future__ import annotations

from collections.abc import Callable

from .context import AgentContext, AgentHistory, AgentResponse
from .patches import apply_patch, save_patch, validate_and_repair_patch
from .protocol import (
    PATCH_REPAIR_PROMPT,
    looks_like_patch,
    repair_response_with_prompt,
)
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


def validate_or_repair(
    *,
    context: AgentContext,
    user_message: str,
    agent_response: AgentResponse,
    validator: Callable[..., None],
    validation_args: tuple[object, ...],
) -> AgentResponse:
    original_response = agent_response

    try:
        validator(*validation_args)
    except ValueError as exc:
        trace_validation_error(str(exc), format_agent_response(agent_response))
        agent_response = repair_response_with_prompt(
            context,
            user_message,
            PATCH_REPAIR_PROMPT,
            "Finish output repair",
            str(exc),
        )
        repaired_args = tuple(
            agent_response if arg is original_response else arg
            for arg in validation_args
        )
        validator(*repaired_args)
    return agent_response


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

    agent_response = validate_or_repair(
        context=context,
        user_message=user_message,
        agent_response=agent_response,
        validator=validate_finish_output,
        validation_args=(agent_response, context.user_prompt),
    )
    agent_response = validate_or_repair(
        context=context,
        user_message=user_message,
        agent_response=agent_response,
        validator=validate_patch_output,
        validation_args=(context, agent_response),
    )

    if looks_like_patch(agent_response.action_input):
        save_patch(context.workspace_path, agent_response.action_input)
        apply_patch(context.workspace_path)
        validate_post_apply_tests(context)

    return agent_response
