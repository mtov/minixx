from __future__ import annotations

from context import AgentContext, AgentResponse
from inputs import parse_args
from llms import call_llm
from protocol import parse_response, repair_finish_output, repair_finish_preconditions, repair_response, validate_finish_output, validate_finish_preconditions
from setup import prepare_run
from tools import run_tool


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
    if agent_history == "No previous steps.":
        return iteration_history
    return f"{agent_history}\n{iteration_history}"


def get_response(context: AgentContext, user_message: str) -> AgentResponse:
    response = call_llm(context, user_message)

    try:
        return parse_response(response)
    except ValueError:
        return repair_response(context, user_message)


def get_valid_finish_response(
    context: AgentContext,
    user_message: str,
    agent_history: str,
    agent_response: AgentResponse,
) -> AgentResponse:
    try:
        validate_finish_preconditions(agent_response, context.user_prompt, agent_history)
    except ValueError:
        agent_response = repair_finish_preconditions(context, user_message)
        validate_finish_preconditions(agent_response, context.user_prompt, agent_history)

    return agent_response


def handle_finish(context: AgentContext, user_message: str, agent_response: AgentResponse) -> str:
    try:
        validate_finish_output(agent_response, context.user_prompt)
    except ValueError:
        agent_response = repair_finish_output(context, user_message)
        validate_finish_output(agent_response, context.user_prompt)

    print("\n")
    return agent_response.action_input


def handle_finish_action(context: AgentContext, user_message: str, agent_history: str, agent_response: AgentResponse) -> tuple[AgentResponse, str | None]:
    if agent_response.action != "finish":
        return agent_response, None

    agent_response = get_valid_finish_response(context, user_message, agent_history, agent_response)
    if agent_response.action == "finish":
        return agent_response, handle_finish(context, user_message, agent_response)

    return agent_response, None


def agentic_loop(context: AgentContext) -> str:
    max_iterations = 10
    agent_history = "No previous steps."
    print("Iteration:", end=" ", flush=True)

    for iteration in range(1, max_iterations + 1):
        print(iteration, end=" ", flush=True)
        user_message = build_user_message(context.user_prompt, agent_history)
        agent_response = get_response(context, user_message)
        agent_response, finish_output = handle_finish_action(context, user_message, agent_history, agent_response)
        if finish_output is not None:
            return finish_output

        tool_result = run_tool(agent_response.action, agent_response.action_input, context.workspace_path)
        agent_history = update_agent_history(agent_history, iteration, agent_response, tool_result)

    print("\n")
    raise ValueError("Agent stopped after reaching the maximum number of steps.")

def main() -> int:
    args = parse_args()

    try:
        context = prepare_run(args.workspace_path)
        text = agentic_loop(context)
    except Exception as exc:  # noqa: BLE001
        print(f"Error executing Codex: {exc}")
        return 1

    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
