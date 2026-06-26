from __future__ import annotations

from context import AgentContext, AgentResponse
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
def parse_response(text: str) -> AgentResponse:
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
    return AgentResponse(thought=thought, action=action, action_input=action_input)


def is_code_change_task(user_prompt: str) -> bool:
    prompt = user_prompt.lower()
    return any(keyword in prompt for keyword in ("rename", "refactor", "change", "update", "modify", "fix", "create", "implement"))


def is_bug_fix_task(user_prompt: str) -> bool:
    prompt = user_prompt.lower()
    return any(keyword in prompt for keyword in ("bug", "fix", "failing test", "tests pass"))


def looks_like_patch(text: str) -> bool:
    return "--- " in text and "+++ " in text and "@@" in text


def validate_finish_preconditions(agent_response: AgentResponse, user_prompt: str, agent_history: str) -> None:
    if not is_bug_fix_task(user_prompt):
        return
    if "Action: run_tests" not in agent_history:
        raise ValueError("Bug-fixing tasks must use run_tests before finish.")


def validate_finish_output(agent_response: AgentResponse, user_prompt: str) -> None:
    if not is_code_change_task(user_prompt):
        return
    if not looks_like_patch(agent_response.action_input):
        raise ValueError("Finish output must be a unified diff patch for code-change tasks.")


def repair_with_prompt(context: AgentContext, user_message: str, repair_prompt: str) -> AgentResponse:
    repair_message = f"{user_message}\n\n{repair_prompt}"
    response = call_llm(context, repair_message)
    return parse_response(response)


def repair_response(context: AgentContext, user_message: str) -> AgentResponse:
    return repair_with_prompt(context, user_message, REPAIR_PROMPT)


def repair_finish_output(context: AgentContext, user_message: str) -> AgentResponse:
    return repair_with_prompt(context, user_message, PATCH_REPAIR_PROMPT)


def repair_finish_preconditions(context: AgentContext, user_message: str) -> AgentResponse:
    return repair_with_prompt(context, user_message, PRECONDITION_REPAIR_PROMPT)
