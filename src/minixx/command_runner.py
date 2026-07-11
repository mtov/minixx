from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from .traces import trace_command_event


def format_command(command: list[str]) -> str:
    return shlex.join(command)


def request_command_approval(command: list[str], cwd: Path, preview: str | None = None) -> bool:
    formatted_command = format_command(command)
    print(f"Proposed command: {formatted_command}")
    print(f"Working directory: {cwd}")
    if preview is not None:
        print("Command preview:")
        print(preview)
    trace_command_event("proposed", formatted_command, cwd)
    answer = input("Authorize command? [y/N]: ").strip().lower()
    approved = answer in {"y", "yes"}
    trace_command_event("approved" if approved else "rejected", formatted_command, cwd)
    return approved


def run_mutating_command(
    command: list[str],
    cwd: Path,
    preview: str | None = None,
) -> subprocess.CompletedProcess[str]:
    formatted_command = format_command(command)
    if not request_command_approval(command, cwd, preview):
        raise PermissionError(f"User rejected command: {formatted_command}")

    print(f"Executing command: {formatted_command}")
    trace_command_event("executed", formatted_command, cwd)
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
