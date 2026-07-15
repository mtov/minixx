from __future__ import annotations

import re

from .context import AgentContext, AgentResponse
from .models import call_model
from .traces import trace_repair_attempt

REPAIR_PROMPT = (
    "Your previous response was invalid. "
    "Respond using only: "
    "Thought: ... "
    "Action: ... "
    "Action Input: ... "
    "Do not include Observation."
)
HUNK_HEADER_PATTERN = re.compile(r"^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@")

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


def looks_like_patch(text: str) -> bool:
    has_file_headers = "--- " in text and "+++ " in text
    has_valid_hunk_header = any(
        HUNK_HEADER_PATTERN.match(line) for line in text.splitlines()
    )
    return has_file_headers and has_valid_hunk_header


def repair_response(context: AgentContext, user_message: str, reason: str) -> AgentResponse:
    trace_repair_attempt("Protocol repair", reason)
    repair_message = f"{user_message}\n\n{REPAIR_PROMPT}"
    response = call_model(context, repair_message, "Repair Response")
    return parse_response(response.content)
