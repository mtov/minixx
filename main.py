from __future__ import annotations

from inputs import load_llm_config, load_system_prompt, load_user_prompt, parse_args, resolve_workspace_path
from llms import call_llm
from logs import clear_log, log_request
from protocol import parse_response, repair_finish_output, repair_response, validate_finish_output
from tools import run_tool

MAX_ITERATIONS = 10


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


def get_valid_response(llm_config: dict, system_prompt: str, user_message: str) -> tuple[str, str, str]:
    response = call_llm(llm_config, system_prompt, user_message)

    try:
        return parse_response(response)
    except ValueError:
        return repair_response(llm_config, system_prompt, user_message)


def handle_finish(llm_config: dict, system_prompt: str, user_prompt: str, user_message: str, action: str, action_input: str) -> str:
    try:
        validate_finish_output(action, action_input, user_prompt)
    except ValueError:
        thought, action, action_input = repair_finish_output(llm_config, system_prompt, user_message)
        validate_finish_output(action, action_input, user_prompt)

    print()
    print()
    return action_input


def agentic_loop(llm_config: dict, system_prompt: str, user_prompt: str, max_steps: int) -> str:
    agent_history = "No previous steps."
    print("Iteration:", end=" ", flush=True)

    for iteration in range(1, max_steps + 1):
        print(iteration, end=" ", flush=True)
        user_message = build_user_message(user_prompt, agent_history)
        thought, action, action_input = get_valid_response(llm_config, system_prompt, user_message)

        if action == "finish":
            return handle_finish(llm_config, system_prompt, user_prompt, user_message, action, action_input)

        tool_result = run_tool(action, action_input)
        agent_history = update_agent_history(agent_history, iteration, thought, action, action_input, tool_result)

    print()
    print()
    raise ValueError("Agent stopped after reaching the maximum number of steps.")


def main() -> int:
    args = parse_args()

    try:
        clear_log()
        workspace_path = resolve_workspace_path(args.workspace_path)
        llm_config = load_llm_config()
        llm_config["working_directory"] = str(workspace_path)
        system_prompt = load_system_prompt()
        user_prompt = load_user_prompt(workspace_path)
        log_request(user_prompt)
        text = agentic_loop(llm_config, system_prompt, user_prompt, MAX_ITERATIONS)
    except Exception as exc:  # noqa: BLE001
        print(f"Error executing Codex: {exc}")
        return 1

    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
