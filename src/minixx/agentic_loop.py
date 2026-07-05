from __future__ import annotations

from .context import AgentContext, AgentHistory, AgentResponse
from .finish_handler import handle_finish
from .history_manager import create_history, history_to_text, update_history
from .inputs import parse_args, prepare_run
from .llms import call_llm
from .planner import create_plan
from .protocol import parse_response, repair_response, trace_response_validation_error
from .tools import run_tool


def build_user_message(
    context: AgentContext,
    agent_history: str,
    plan: str | None,
) -> str:
    message = f"""User task:
{context.user_prompt}

Agent history:
{agent_history}"""
    if plan is None:
        return message
    return f"""{message}

Plan:
{plan}"""


def print_iteration_action(iteration: int, action_description: str) -> None:
    print(f"[{iteration}] {action_description}", flush=True)


def get_agent_response(context: AgentContext, user_message: str) -> AgentResponse:
    response = call_llm(context, user_message)

    try:
        return parse_response(response)
    except ValueError as exc:
        trace_response_validation_error(str(exc), response)
        return repair_response(context, user_message, str(exc))


def agentic_loop(context: AgentContext) -> str:
    max_iterations = 10
    agent_history = create_history()
    plan = create_plan(context)

    for iteration in range(1, max_iterations + 1):
        user_message = build_user_message(context, history_to_text(agent_history), plan)
        agent_response = get_agent_response(context, user_message)

        if agent_response.action == "finish":
            agent_response = handle_finish(context, user_message, agent_history, agent_response)

        print_iteration_action(iteration, agent_response.action_description)

        if agent_response.action == "finish":
            print()
            return agent_response.action_input

        tool_result = run_tool(agent_response, context.workspace_path)
        update_history(agent_history, iteration, agent_response, tool_result)

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
