from __future__ import annotations

from .context import AgentContext, AgentHistory, AgentResponse
from .inputs import parse_args, prepare_run
from .llms import call_llm
from .protocol import log_response_validation_error, parse_response, repair_finish_output, repair_finish_preconditions, repair_response, validate_finish_output, validate_finish_preconditions
from .tools import run_tool


def build_user_message(context: AgentContext, agent_history: str) -> str:
    return f"""User task:
{context.user_prompt}

Agent history:
{agent_history}"""


def print_iteration_action(iteration: int, action_description: str) -> None:
    print(f"[{iteration}] {action_description}", flush=True)


def format_agent_response(agent_response: AgentResponse) -> str:
    return (
        f"Thought: {agent_response.thought}\n"
        f"Action: {agent_response.action}\n"
        f"Action Input: {agent_response.action_input}\n"
        f"Action Description: {agent_response.action_description}"
    )


def get_agent_response(context: AgentContext, user_message: str) -> AgentResponse:
    response = call_llm(context, user_message)

    try:
        return parse_response(response)
    except ValueError as exc:
        log_response_validation_error(str(exc), response)
        return repair_response(context, user_message, str(exc))


def handle_finish_action(context: AgentContext, user_message: str, agent_history: AgentHistory, agent_response: AgentResponse) -> AgentResponse:
    try:
        validate_finish_preconditions(agent_response, context.user_prompt, agent_history)
    except ValueError as exc:
        log_response_validation_error(str(exc), format_agent_response(agent_response))
        agent_response = repair_finish_preconditions(context, user_message, str(exc))
        validate_finish_preconditions(agent_response, context.user_prompt, agent_history)

    if agent_response.action != "finish":
        return agent_response

    try:
        validate_finish_output(agent_response, context.user_prompt)
    except ValueError as exc:
        log_response_validation_error(str(exc), format_agent_response(agent_response))
        agent_response = repair_finish_output(context, user_message, str(exc))
        validate_finish_output(agent_response, context.user_prompt)

    return agent_response


def agentic_loop(context: AgentContext) -> str:
    max_iterations = 10
    agent_history = AgentHistory()

    for iteration in range(1, max_iterations + 1):
        user_message = build_user_message(context, agent_history.to_text())
        agent_response = get_agent_response(context, user_message)

        if agent_response.action == "finish":
            agent_response = handle_finish_action(context, user_message, agent_history, agent_response)

        print_iteration_action(iteration, agent_response.action_description)

        if agent_response.action == "finish":
            print()
            return agent_response.action_input

        tool_result = run_tool(agent_response, context.workspace_path)
        agent_history.append(iteration, agent_response, tool_result)

    print()
    raise ValueError("Agent stopped after reaching the maximum number of steps.")


def main() -> int:
    args = parse_args()

    try:
        context = prepare_run(args.workspace_path)
        result = agentic_loop(context)
    except Exception as exc:  # noqa: BLE001
        print(f"Error executing Codex: {exc}")
        return 1

    print(result)
    return 0
