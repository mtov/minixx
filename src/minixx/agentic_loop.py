from __future__ import annotations

from .context import AgentContext, AgentHistory, AgentResponse
from .inputs import parse_args, prepare_run
from .llms import call_llm
from .protocol import parse_response, repair_finish_output, repair_finish_preconditions, repair_response, validate_finish_output, validate_finish_preconditions
from .tools import run_tool


def build_user_message(user_prompt: str, agent_history: str) -> str:
    return f"""User task:
{user_prompt}

Agent history:
{agent_history}"""


def print_iteration(iteration: int) -> None:
    print(iteration, end=" ", flush=True)


def print_iteration_header() -> None:
    print("Iteration:", end=" ", flush=True)


def get_agent_response(context: AgentContext, user_message: str) -> AgentResponse:
    response = call_llm(context, user_message)

    try:
        return parse_response(response)
    except ValueError:
        return repair_response(context, user_message)


def handle_finish_action(context: AgentContext, user_message: str, agent_history: AgentHistory, agent_response: AgentResponse) -> AgentResponse:
    try:
        validate_finish_preconditions(agent_response, context.user_prompt, agent_history)
    except ValueError:
        agent_response = repair_finish_preconditions(context, user_message)
        validate_finish_preconditions(agent_response, context.user_prompt, agent_history)

    if agent_response.action != "finish":
        return agent_response

    try:
        validate_finish_output(agent_response, context.user_prompt)
    except ValueError:
        agent_response = repair_finish_output(context, user_message)
        validate_finish_output(agent_response, context.user_prompt)

    return agent_response


def agentic_loop(context: AgentContext) -> str:
    max_iterations = 10
    agent_history = AgentHistory()
    print_iteration_header()

    for iteration in range(1, max_iterations + 1):
        print_iteration(iteration)
        user_message = build_user_message(context.user_prompt, agent_history.to_text())
        agent_response = get_agent_response(context, user_message)

        if agent_response.action == "finish":
            agent_response = handle_finish_action(context, user_message, agent_history, agent_response)
            if agent_response.action == "finish":
                print("\n")
                return agent_response.action_input

        tool_result = run_tool(agent_response, context.workspace_path)
        agent_history.append(iteration, agent_response, tool_result)

    print("\n")
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
