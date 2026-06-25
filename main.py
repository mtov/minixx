from __future__ import annotations

from context import AgentContext
from inputs import load_llm_config, load_system_prompt, load_user_prompt, parse_args, resolve_workspace_path
from llms import call_llm
from logs import clear_log, log_request
from protocol import parse_response, repair_finish_output, repair_finish_preconditions, repair_response, validate_finish_output, validate_finish_preconditions
from tools import run_tool


def build_user_message(user_prompt: str, agent_history: str) -> str:
    return f"""User task:
{user_prompt}

Agent history:
{agent_history}"""


def update_agent_history(agent_history: str, iteration: int, thought: str, action: str, action_input: str, tool_result: str) -> str:
    iteration_history = (
        f"Iteration {iteration}\n"
        f"Thought: {thought}\n"
        f"Action: {action}\n"
        f"Action Input: {action_input}\n"
        f"Observation: {tool_result}\n"
    )
    if agent_history == "No previous steps.":
        return iteration_history
    return f"{agent_history}\n{iteration_history}"


def get_valid_response(context: AgentContext, user_message: str) -> tuple[str, str, str]:
    response = call_llm(context.llm_config, context.system_prompt, user_message)

    try:
        return parse_response(response)
    except ValueError:
        return repair_response(context.llm_config, context.system_prompt, user_message)


def get_valid_finish_response(
    context: AgentContext,
    user_message: str,
    agent_history: str,
    thought: str,
    action: str,
    action_input: str,
) -> tuple[str, str, str]:
    try:
        validate_finish_preconditions(action, context.user_prompt, agent_history)
    except ValueError:
        thought, action, action_input = repair_finish_preconditions(context.llm_config, context.system_prompt, user_message)
        validate_finish_preconditions(action, context.user_prompt, agent_history)

    return thought, action, action_input


def handle_finish(context: AgentContext, user_message: str, action: str, action_input: str) -> str:
    try:
        validate_finish_output(action, action_input, context.user_prompt)
    except ValueError:
        thought, action, action_input = repair_finish_output(context.llm_config, context.system_prompt, user_message)
        validate_finish_output(action, action_input, context.user_prompt)

    print("\n")
    return action_input


def agentic_loop(context: AgentContext) -> str:
    max_iterations = 10
    agent_history = "No previous steps."
    print("Iteration:", end=" ", flush=True)

    for iteration in range(1, max_iterations + 1):
        print(iteration, end=" ", flush=True)
        user_message = build_user_message(context.user_prompt, agent_history)
        thought, action, action_input = get_valid_response(context, user_message)

        if action == "finish":
            thought, action, action_input = get_valid_finish_response(
                context, user_message, agent_history, thought, action, action_input
            )
            if action == "finish":
                return handle_finish(context, user_message, action, action_input)

        tool_result = run_tool(action, action_input, context.workspace_path)
        agent_history = update_agent_history(agent_history, iteration, thought, action, action_input, tool_result)

    print("\n")
    raise ValueError("Agent stopped after reaching the maximum number of steps.")


def prepare_run(workspace_path_arg: str) -> AgentContext:
    clear_log()
    workspace_path = resolve_workspace_path(workspace_path_arg)
    llm_config = load_llm_config()
    llm_config["working_directory"] = str(workspace_path)
    system_prompt = load_system_prompt()
    user_prompt = load_user_prompt(workspace_path)
    log_request(user_prompt)
    return AgentContext(llm_config=llm_config, system_prompt=system_prompt, user_prompt=user_prompt, workspace_path=workspace_path)


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
