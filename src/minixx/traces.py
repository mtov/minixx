from __future__ import annotations

from pathlib import Path

from .context import TokenUsage

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = PROJECT_ROOT / "agent_trace.log"
CALL_COUNT = 0
TOTAL_TOKENS = 0


def clear_trace() -> None:
    global CALL_COUNT, TOTAL_TOKENS
    CALL_COUNT = 0
    TOTAL_TOKENS = 0
    with LOG_PATH.open("w", encoding="utf-8"):
        pass


def trace_request(user_prompt: str) -> None:
    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write("Request:\n")
        file.write(f"{user_prompt}\n")
        file.write("\n===\n\n")


def format_token_usage(token_usage: TokenUsage) -> str:
    if token_usage.total_tokens is None:
        return "Token Usage: unavailable"
    return (
        "Token Usage: "
        f"input={token_usage.input_tokens if token_usage.input_tokens is not None else '?'} "
        f"output={token_usage.output_tokens if token_usage.output_tokens is not None else '?'} "
        f"total={token_usage.total_tokens}"
    )


def get_total_tokens() -> int | None:
    if TOTAL_TOKENS == 0:
        return None
    return TOTAL_TOKENS


def trace_response(
    response: str,
    label: str = "Response",
    token_usage: TokenUsage | None = None,
) -> None:
    global CALL_COUNT, TOTAL_TOKENS
    CALL_COUNT += 1
    usage = token_usage or TokenUsage()
    if usage.total_tokens is not None:
        TOTAL_TOKENS += usage.total_tokens

    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(f"{label} {CALL_COUNT}\n")
        file.write(f"{format_token_usage(usage)}\n")
        if usage.total_tokens is not None:
            file.write(f"Cumulative Tokens: {TOTAL_TOKENS}\n")
        file.write(f"{response}\n\n")


def trace_validation_error(reason: str, response: str) -> None:
    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write("Validation Error\n")
        file.write(f"Reason: {reason}\n")
        file.write("Response:\n")
        file.write(f"{response}\n\n")


def trace_repair_attempt(repair_kind: str, reason: str) -> None:
    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write("Repair Attempt\n")
        file.write(f"Kind: {repair_kind}\n")
        file.write(f"Reason: {reason}\n\n")
