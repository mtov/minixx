from __future__ import annotations

from .context import AgentContext, AgentHistory, AgentResponse
from .finish_handler import handle_finish
from .inputs import parse_args, prepare_run
from .models import call_model
from .protocol import parse_response, repair_response
from .traces import get_total_tokens, trace_validation_error
from .tools import run_tool


def print_iteration_action(iteration: int, action: str) -> None:
    print(f"[{iteration}] {action}", flush=True)


def print_total_tokens() -> None:
    total_tokens = get_total_tokens()
    if total_tokens is not None:
        print(f"Total tokens: {total_tokens}")


def get_agent_response(context: AgentContext, agent_history: str) -> AgentResponse:
    user_message = f"""User task:
{context.user_prompt}

Agent history:
{agent_history}"""
    model_response = call_model(context, user_message)

    try:
        return parse_response(model_response.content)
    except ValueError as exc:
        trace_validation_error(str(exc), model_response.content)
        return repair_response(context, user_message, str(exc))


def agentic_loop(context: AgentContext) -> str:
    max_iterations = 10
    agent_history = AgentHistory()

    for iteration in range(1, max_iterations + 1):
        agent_response = get_agent_response(context, agent_history.to_text())

        if agent_response.action == "finish":
            agent_response = handle_finish(context, agent_response)
            print_iteration_action(iteration, agent_response.action)
            return agent_response.action_input

        print_iteration_action(iteration, agent_response.action)

        tool_result = run_tool(agent_response, context.workspace_path)
        agent_history.append(iteration, agent_response, tool_result)

    raise ValueError("Agent stopped after reaching the maximum number of steps.")


def main() -> int:
    args = parse_args()

    try:
        context = prepare_run(args.workspace_path)
        result = agentic_loop(context)
    except Exception as exc:  # noqa: BLE001
        print_total_tokens()
        print(f"Error executing Minixx: {exc}")
        return 1

    print_total_tokens()
    print(result)
    return 0
