from __future__ import annotations

import re

from .context import AgentContext, AgentHistory, AgentResponse
from .llms import call_llm
from .traces import log_repair_attempt, log_validation_error

REPAIR_PROMPT = (
    "Your previous response was invalid. "
    "Respond using only: "
    "Thought: ... "
    "Action: ... "
    "Action Input: ... "
    "Action Description: ... "
    "Do not include Observation."
)
PATCH_REPAIR_PROMPT = (
    "Your previous finish output was invalid. "
    "For this code-change task, respond using only: "
    "Thought: ... "
    "Action: finish "
    "Action Input: a unified diff patch "
    "Action Description: ... "
    "Do not include Observation."
)
PRECONDITION_REPAIR_PROMPT = (
    "Your previous response was invalid. "
    "For bug-fixing tasks, you must use run_tests before finish. "
    "Respond using only: "
    "Thought: ... "
    "Action: ... "
    "Action Input: ... "
    "Action Description: ... "
    "Do not include Observation."
)


# Parse one model turn in the ReAct-style protocol used by Minixx.
# The model must return a single action decision, not a simulated multi-step trace,
# so this parser rejects responses that include Observation or more than one action block.
def parse_response(text: str) -> AgentResponse:
    thought = ""
    action = ""
    action_input_lines: list[str] = []
    action_description = ""
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
        elif line.startswith("Action Description:"):
            action_description = line.removeprefix("Action Description:").strip()
            current_section = None
        elif line.startswith("Observation:"):
            raise ValueError("Model response must not contain Observation.")
        elif current_section == "action_input":
            action_input_lines.append(line)

    if not action:
        raise ValueError("Model response is missing the required Action field.")
    if not action_description:
        raise ValueError("Model response is missing the required Action Description field.")

    action_input = "\n".join(action_input_lines).strip()
    return AgentResponse(
        thought=thought,
        action=action,
        action_input=action_input,
        action_description=action_description,
    )


def is_code_change_task(user_prompt: str) -> bool:
    prompt = user_prompt.lower()
    return any(keyword in prompt for keyword in ("rename", "refactor", "change", "update", "modify", "fix", "create", "implement"))


def is_bug_fix_task(user_prompt: str) -> bool:
    prompt = user_prompt.lower()
    return any(keyword in prompt for keyword in ("bug", "fix", "failing test", "tests pass"))


def looks_like_patch(text: str) -> bool:
    hunk_header_pattern = re.compile(r"^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@")
    has_file_headers = "--- " in text and "+++ " in text
    has_valid_hunk_header = any(
        hunk_header_pattern.match(line) for line in text.splitlines()
    )
    return has_file_headers and has_valid_hunk_header


def validate_finish_preconditions(agent_response: AgentResponse, user_prompt: str, agent_history: AgentHistory) -> None:
    if not is_bug_fix_task(user_prompt):
        return
    if not agent_history.contains_action("run_tests"):
        raise ValueError("Bug-fixing tasks must use run_tests before finish.")


def validate_finish_output(agent_response: AgentResponse, user_prompt: str) -> None:
    if not is_code_change_task(user_prompt):
        return
    if not looks_like_patch(agent_response.action_input):
        raise ValueError("Finish output must be a unified diff patch for code-change tasks.")


def repair_with_prompt(context: AgentContext, user_message: str, repair_prompt: str, repair_kind: str, reason: str) -> AgentResponse:
    log_repair_attempt(repair_kind, reason)
    repair_message = f"{user_message}\n\n{repair_prompt}"
    response = call_llm(context, repair_message, "Repair Response")
    return parse_response(response)


def log_response_validation_error(reason: str, response: str) -> None:
    log_validation_error(reason, response)


def repair_response(context: AgentContext, user_message: str, reason: str) -> AgentResponse:
    return repair_with_prompt(context, user_message, REPAIR_PROMPT, "Protocol repair", reason)


def repair_finish_output(context: AgentContext, user_message: str, reason: str) -> AgentResponse:
    return repair_with_prompt(context, user_message, PATCH_REPAIR_PROMPT, "Finish output repair", reason)


def repair_finish_preconditions(context: AgentContext, user_message: str, reason: str) -> AgentResponse:
    return repair_with_prompt(context, user_message, PRECONDITION_REPAIR_PROMPT, "Finish precondition repair", reason)
