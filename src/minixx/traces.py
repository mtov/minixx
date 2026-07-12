from __future__ import annotations

from pathlib import Path

from .context import TokenUsage

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = PROJECT_ROOT / "agent_trace.log"
CALL_COUNT = 0
TOTAL_TOKENS = 0


def _append_trace(text: str) -> None:
    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(text)


def clear_trace() -> None:
    global CALL_COUNT, TOTAL_TOKENS
    CALL_COUNT = 0
    TOTAL_TOKENS = 0
    LOG_PATH.write_text("", encoding="utf-8")


def trace_request(user_prompt: str) -> None:
    _append_trace(f"[request]\n{user_prompt}\n\n")


def format_token_usage(token_usage: TokenUsage) -> str:
    if token_usage.total_tokens is None:
        return "tokens: unavailable"
    return (
        "tokens: "
        f"input={token_usage.input_tokens if token_usage.input_tokens is not None else '?'} "
        f"output={token_usage.output_tokens if token_usage.output_tokens is not None else '?'} "
        f"total={token_usage.total_tokens}"
    )


def get_total_tokens() -> int | None:
    return TOTAL_TOKENS or None


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

    cumulative_tokens = (
        f"cumulative_tokens: {TOTAL_TOKENS}\n"
        if usage.total_tokens is not None
        else ""
    )
    _append_trace(
        f"[{label.lower().replace(' ', '_')} {CALL_COUNT}]\n"
        f"{format_token_usage(usage)}\n"
        f"{cumulative_tokens}"
        f"{response}\n\n"
    )


def trace_validation_error(reason: str, response: str) -> None:
    _append_trace(
        "[validation_error]\n"
        f"reason: {reason}\n"
        "response:\n"
        f"{response}\n\n"
    )


def trace_repair_attempt(repair_kind: str, reason: str) -> None:
    _append_trace(
        "[repair_attempt]\n"
        f"kind: {repair_kind}\n"
        f"reason: {reason}\n\n"
    )


def trace_command_event(status: str, command: str, cwd: Path) -> None:
    _append_trace(
        "[command]\n"
        f"status: {status}\n"
        f"command: {command}\n"
        f"cwd: {cwd}\n\n"
    )
