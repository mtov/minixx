from __future__ import annotations

from .context import AgentContext, AgentHistory, AgentResponse
from .finish_reviewer import review_finish
from .patches import save_patch
from .protocol import (
    looks_like_patch,
    repair_finish_output,
    repair_finish_preconditions,
    trace_response_validation_error,
    validate_finish_output,
    validate_finish_preconditions,
)


def format_agent_response(agent_response: AgentResponse) -> str:
    return (
        f"Thought: {agent_response.thought}\n"
        f"Action: {agent_response.action}\n"
        f"Action Input: {agent_response.action_input}\n"
        f"Action Description: {agent_response.action_description}"
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
