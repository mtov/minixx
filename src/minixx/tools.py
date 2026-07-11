from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from .context import AgentResponse
from .guards import resolve_tool_path

MAX_FIND_TEXT_MATCHES = 20
SKIPPED_DIRECTORIES = {".git", ".venv", "__pycache__"}
TEST_COMMAND = (sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider")
TEST_TIMEOUT_SECONDS = 30


def list_files(action_input: str, workspace_path: Path) -> str:
    try:
        path = resolve_tool_path(action_input, workspace_path)
    except ValueError as exc:
        return str(exc)

    if not path.exists():
        return f"Directory not found inside the workspace: {path}"
    if not path.is_dir():
        return f"Path is not a directory: {path}"

    entries = sorted(item.name for item in path.iterdir())
    if not entries:
        return f"Directory is empty: {path}"

    return "\n".join(entries)


def read_file(action_input: str, workspace_path: Path) -> str:
    try:
        path = resolve_tool_path(action_input, workspace_path)
    except ValueError as exc:
        return str(exc)

    if not path.exists():
        return f"File not found inside the workspace: {path}"
    if not path.is_file():
        return f"Path is not a file: {path}"

    print(f"Reading file: {path.name}", flush=True)
    return path.read_text(encoding="utf-8")


def parse_find_text_input(action_input: str) -> tuple[str, str] | str:
    try:
        query, directory = action_input.split("|", maxsplit=1)
    except ValueError:
        return "Invalid input. Use: search text | /path/to/directory"

    query = query.strip()
    directory = directory.strip()

    if not query:
        return "Search text cannot be empty."
    if not directory:
        return "Directory path cannot be empty."

    return query, directory


def find_text(action_input: str, workspace_path: Path) -> str:
    parsed_input = parse_find_text_input(action_input)
    if isinstance(parsed_input, str):
        return parsed_input

    query, directory = parsed_input

    try:
        path = resolve_tool_path(directory, workspace_path)
    except ValueError as exc:
        return str(exc)

    if not path.exists():
        return f"Directory not found inside the workspace: {path}"
    if not path.is_dir():
        return f"Path is not a directory: {path}"

    matches: list[str] = []

    for file_path in sorted(path.rglob("*")):
        if any(part in SKIPPED_DIRECTORIES for part in file_path.parts):
            continue
        if not file_path.is_file():
            continue

        try:
            with file_path.open("r", encoding="utf-8") as file:
                for line_number, line in enumerate(file, start=1):
                    if query in line:
                        matches.append(f"{file_path}:{line_number}: {line.rstrip()}")
                        if len(matches) >= MAX_FIND_TEXT_MATCHES:
                            return "\n".join(matches)
        except (OSError, UnicodeDecodeError):
            continue

    if not matches:
        return f"No matches found for: {query}"

    return "\n".join(matches)


def run_tests(workspace_path: Path) -> str:
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}

    try:
        result = subprocess.run(
            TEST_COMMAND,
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=TEST_TIMEOUT_SECONDS,
            env=environment,
        )
    except Exception as exc:  # noqa: BLE001
        return f"Could not run tests: {exc}"

    output_parts = [result.stdout.strip(), result.stderr.strip()]
    output = "\n".join(part for part in output_parts if part).strip()

    if not output and result.returncode == 0:
        return "Tests passed."
    if not output:
        return f"Tests failed with exit code {result.returncode}."

    return output


def run_tool(agent_response: AgentResponse, workspace_path: Path) -> str:
    if agent_response.action == "list_files":
        return list_files(agent_response.action_input, workspace_path)
    if agent_response.action == "read_file":
        return read_file(agent_response.action_input, workspace_path)
    if agent_response.action == "find_text":
        return find_text(agent_response.action_input, workspace_path)
    if agent_response.action == "run_tests":
        return run_tests(workspace_path)

    return f"Unsupported action '{agent_response.action}'. Use list_files, read_file, find_text, run_tests, or finish."
