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


# Parse one model turn in the ReAct-style protocol used by Minixx.
# The model must return a single action decision, not a simulated multi-step trace,
# so this parser rejects responses that include Observation or more than one action block.
def parse_response(text: str) -> tuple[str, str, str]:
    thought = ""
    action = ""
    action_input = ""

    for line in text.splitlines():
        if line.startswith("Thought:"):
            thought = line.removeprefix("Thought:").strip()
        elif line.startswith("Action:"):
            action = line.removeprefix("Action:").strip()
        elif line.startswith("Action Input:"):
            action_input = line.removeprefix("Action Input:").strip()
        elif line.startswith("Observation:"):
            raise ValueError("Model response must not contain Observation.")

    if not action:
        raise ValueError("Model response is missing the required Action field.")

    return thought, action, action_input


def repair_response(llm_config: dict, system_prompt: str, user_message: str) -> tuple[str, str, str]:
    repair_message = f"{user_message}\n\n{REPAIR_PROMPT}"
    repair_response = call_llm(llm_config, system_prompt, repair_message)
    return parse_response(repair_response)
