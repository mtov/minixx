from __future__ import annotations

from llms import call_llm

REPAIR_PROMPT = (
    "Your previous response was invalid. "
    "Respond using only: "
    "Thought: ... "
    "Action: ... "
    "Action Input: ... "
    "Do not include Observation."
)
PATCH_REPAIR_PROMPT = (
    "Your previous finish output was invalid. "
    "For this code-change task, respond using only: "
    "Thought: ... "
    "Action: finish "
    "Action Input: a unified diff patch "
    "Do not include Observation."
)
PRECONDITION_REPAIR_PROMPT = (
    "Your previous response was invalid. "
    "For bug-fixing tasks, you must use run_tests before finish. "
    "Respond using only: "
    "Thought: ... "
    "Action: ... "
    "Action Input: ... "
    "Do not include Observation."
)


# Parse one model turn in the ReAct-style protocol used by Minixx.
# The model must return a single action decision, not a simulated multi-step trace,
# so this parser rejects responses that include Observation or more than one action block.
def parse_response(text: str) -> tuple[str, str, str]:
    thought = ""
    action = ""
    action_input_lines: list[str] = []
    current_section = None

    for line in text.splitlines():
        if line.startswith("Thought:"):
            thought = line.removeprefix("Thought:").strip()
            current_section = None
        elif line.startswith("Action:"):
            action = line.removeprefix("Action:").strip()
            current_section = None
        elif line.startswith("Action Input:"):
            action_input_lines = [line.removeprefix("Action Input:").strip()]
            current_section = "action_input"
        elif line.startswith("Observation:"):
            raise ValueError("Model response must not contain Observation.")
        elif current_section == "action_input":
            action_input_lines.append(line)

    if not action:
        raise ValueError("Model response is missing the required Action field.")

    action_input = "\n".join(action_input_lines).strip()
    return thought, action, action_input


def is_code_change_task(user_prompt: str) -> bool:
    prompt = user_prompt.lower()
    return any(keyword in prompt for keyword in ("rename", "refactor", "change", "update", "modify", "fix", "create", "implement"))


def is_bug_fix_task(user_prompt: str) -> bool:
    prompt = user_prompt.lower()
    return any(keyword in prompt for keyword in ("bug", "fix", "failing test", "tests pass"))


def looks_like_patch(text: str) -> bool:
    return "--- " in text and "+++ " in text and "@@" in text


def validate_finish_preconditions(action: str, user_prompt: str, agent_history: str) -> None:
    if action != "finish":
        return
    if not is_bug_fix_task(user_prompt):
        return
    if "Action: run_tests" not in agent_history:
        raise ValueError("Bug-fixing tasks must use run_tests before finish.")


def validate_finish_output(action: str, action_input: str, user_prompt: str) -> None:
    if action != "finish":
        return
    if not is_code_change_task(user_prompt):
        return
    if not looks_like_patch(action_input):
        raise ValueError("Finish output must be a unified diff patch for code-change tasks.")


def repair_response(llm_config: dict, system_prompt: str, user_message: str) -> tuple[str, str, str]:
    repair_message = f"{user_message}\n\n{REPAIR_PROMPT}"
    repair_response = call_llm(llm_config, system_prompt, repair_message)
    return parse_response(repair_response)


def repair_finish_output(llm_config: dict, system_prompt: str, user_message: str) -> tuple[str, str, str]:
    repair_message = f"{user_message}\n\n{PATCH_REPAIR_PROMPT}"
    repair_response = call_llm(llm_config, system_prompt, repair_message)
    return parse_response(repair_response)


def repair_finish_preconditions(llm_config: dict, system_prompt: str, user_message: str) -> tuple[str, str, str]:
    repair_message = f"{user_message}\n\n{PRECONDITION_REPAIR_PROMPT}"
    repair_response = call_llm(llm_config, system_prompt, repair_message)
    return parse_response(repair_response)
