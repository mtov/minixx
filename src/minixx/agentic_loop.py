from __future__ import annotations

from .context import AgentContext, AgentResponse
from .inputs import parse_args, prepare_run
from .llms import call_llm
from .protocol import parse_response, repair_finish_output, repair_finish_preconditions, repair_response, validate_finish_output, validate_finish_preconditions
from .tools import run_tool

NO_PREVIOUS_STEPS = "No previous steps."


def build_user_message(user_prompt: str, agent_history: str) -> str:
    return f"""User task:
{user_prompt}

Agent history:
{agent_history}"""


def update_agent_history(agent_history: str, iteration: int, agent_response: AgentResponse, tool_result: str) -> str:
    iteration_history = (
        f"Iteration {iteration}\n"
        f"Thought: {agent_response.thought}\n"
        f"Action: {agent_response.action}\n"
        f"Action Input: {agent_response.action_input}\n"
        f"Observation: {tool_result}\n"
    )
    if agent_history == NO_PREVIOUS_STEPS:
        return iteration_history
    return f"{agent_history}\n{iteration_history}"


def get_agent_response(context: AgentContext, user_message: str) -> AgentResponse:
    response = call_llm(context, user_message)

    try:
        return parse_response(response)
    except ValueError:
        return repair_response(context, user_message)


def handle_finish_action(context: AgentContext, user_message: str, agent_history: str, agent_response: AgentResponse) -> AgentResponse:
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
    agent_history = NO_PREVIOUS_STEPS
    print("Iteration:", end=" ", flush=True)

    for iteration in range(1, max_iterations + 1):
        print(iteration, end=" ", flush=True)
        user_message = build_user_message(context.user_prompt, agent_history)
        agent_response = get_agent_response(context, user_message)

        if agent_response.action == "finish":
            agent_response = handle_finish_action(context, user_message, agent_history, agent_response)
            if agent_response.action == "finish":
                print("\n")
                return agent_response.action_input

        tool_result = run_tool(agent_response.action, agent_response.action_input, context.workspace_path)
        agent_history = update_agent_history(agent_history, iteration, agent_response, tool_result)

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
