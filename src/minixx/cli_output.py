from __future__ import annotations

from math import floor
from pathlib import Path

from .context import AgentAction, AgentContext
from .protocol import looks_like_patch
from .traces import get_total_tokens


def format_iteration_action(action: AgentAction) -> str:
    if action.tool == "list_files":
        path = action.tool_args.strip() or "."
        return f"{action.tool} {path}"

    if action.tool == "read_file":
        return f"{action.tool} {Path(action.tool_args).name}"

    if action.tool == "find_text":
        query = action.tool_args.split("|", maxsplit=1)[0].strip()
        if query:
            return f'{action.tool} "{query}"'

    return action.tool


def print_iteration_action(iteration: int, action: AgentAction) -> None:
    print(f"[{iteration}] {format_iteration_action(action)}", flush=True)


def print_total_tokens() -> None:
    total_tokens = get_total_tokens()
    if total_tokens is not None:
        print(f"Total tokens: {total_tokens}")


def format_elapsed_time(elapsed_seconds: float) -> str:
    total_seconds = max(0.0, elapsed_seconds)
    if total_seconds < 60:
        return f"Elapsed time: {total_seconds:.2f}s"

    minutes = floor(total_seconds / 60)
    seconds = total_seconds - (minutes * 60)
    return f"Elapsed time: {minutes}m {seconds:.2f}s"


def print_elapsed_time(elapsed_seconds: float) -> None:
    print(format_elapsed_time(elapsed_seconds))


def format_success_message(context: AgentContext, result: str) -> str:
    if looks_like_patch(result):
        if context.post_apply_tests_passed:
            return "Minixx result: success. Patch applied successfully. Post-apply tests passed."
        return "Minixx result: success. Patch applied successfully."

    normalized_result = result.strip()
    if not normalized_result:
        return "Minixx result: success."

    return f"Minixx result: success. {normalized_result}"


def format_failure_message(error: Exception) -> str:
    return f"Minixx result: failed. {error}"


def print_final_result(context: AgentContext, result: str) -> None:
    print(format_success_message(context, result))
