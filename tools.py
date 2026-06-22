from __future__ import annotations

from pathlib import Path

MAX_FIND_TEXT_MATCHES = 20
SKIPPED_DIRECTORIES = {".git", ".venv", "__pycache__"}


def list_files(action_input: str) -> str:
    path = Path(action_input.strip())

    if not path.exists():
        return f"Path not found: {path}"
    if not path.is_dir():
        return f"Path is not a directory: {path}"

    entries = sorted(item.name for item in path.iterdir())
    if not entries:
        return f"Directory is empty: {path}"

    return "\n".join(entries)


def read_file(action_input: str) -> str:
    path = Path(action_input.strip())

    if not path.exists():
        return f"File not found: {path}"
    if not path.is_file():
        return f"Path is not a file: {path}"

    return path.read_text(encoding="utf-8")


def find_text(action_input: str) -> str:
    try:
        query, directory = action_input.split("|", maxsplit=1)
    except ValueError:
        return "Invalid input. Use: search text | /path/to/directory"

    query = query.strip()
    path = Path(directory.strip())

    if not query:
        return "Search text cannot be empty."
    if not path.exists():
        return f"Path not found: {path}"
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


def run_tool(action: str, action_input: str) -> str:
    if action == "list_files":
        return list_files(action_input)
    if action == "read_file":
        return read_file(action_input)
    if action == "find_text":
        return find_text(action_input)

    return f"Unsupported action '{action}'. Use list_files, read_file, find_text, or finish."
