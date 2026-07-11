from __future__ import annotations

import re
import shlex
import subprocess
import tempfile
from pathlib import Path

from .traces import trace_command_event


def save_patch(workspace_path: Path, patch_text: str) -> None:
    patch_path = workspace_path / "patch.txt"
    patch_path.write_text(patch_text, encoding="utf-8")


def _strip_code_fences(text: str) -> str:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    return "\n".join(line for line in lines if not line.strip().startswith("```")).strip()


def _extract_patch_block(text: str) -> str:
    lines = text.splitlines()
    start = None

    for index, line in enumerate(lines):
        if line.startswith("--- ") or line.startswith("diff --git "):
            start = index
            break

    if start is None:
        return text.strip()

    return "\n".join(lines[start:]).strip()


def _normalize_hunk_lines(text: str) -> str:
    normalized_lines: list[str] = []
    in_hunk = False

    for line in text.splitlines():
        if line.startswith("@@ "):
            in_hunk = True
            normalized_lines.append(line)
            continue

        if line.startswith("--- ") or line.startswith("+++ ") or line.startswith("diff --git "):
            in_hunk = False
            normalized_lines.append(line)
            continue

        if not in_hunk:
            normalized_lines.append(line)
            continue

        if line.startswith(("+", "-", " ", "\\")):
            normalized_lines.append(line)
            continue

        # Unified diff hunks require every payload line to carry a prefix.
        normalized_lines.append(f" {line}")

    return "\n".join(normalized_lines).strip()


def _format_hunk_range(start: int, count: int) -> str:
    if count == 1:
        return str(start)
    return f"{start},{count}"


def _recalculate_hunk_headers(text: str) -> str:
    lines = text.splitlines()
    recalculated_lines: list[str] = []
    index = 0
    hunk_header_pattern = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")

    while index < len(lines):
        line = lines[index]
        match = hunk_header_pattern.match(line)
        if match is None:
            recalculated_lines.append(line)
            index += 1
            continue

        old_start = int(match.group(1))
        new_start = int(match.group(2))
        hunk_lines: list[str] = []
        index += 1

        while index < len(lines):
            candidate = lines[index]
            if candidate.startswith(("@@ ", "--- ", "+++ ", "diff --git ")):
                break
            hunk_lines.append(candidate)
            index += 1

        old_count = sum(1 for hunk_line in hunk_lines if not hunk_line.startswith(("+", "\\")))
        new_count = sum(1 for hunk_line in hunk_lines if not hunk_line.startswith(("-", "\\")))

        recalculated_lines.append(
            f"@@ -{_format_hunk_range(old_start, old_count)} +{_format_hunk_range(new_start, new_count)} @@"
        )
        recalculated_lines.extend(hunk_lines)

    return "\n".join(recalculated_lines).strip()


def auto_repair_patch_text(patch_text: str) -> str:
    repaired = _strip_code_fences(patch_text)
    repaired = _extract_patch_block(repaired)
    repaired = _normalize_hunk_lines(repaired)
    repaired = _recalculate_hunk_headers(repaired)
    if repaired and not repaired.endswith("\n"):
        repaired = f"{repaired}\n"
    return repaired


def validate_patch(workspace_path: Path, patch_text: str) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".patch", delete=False) as file:
        file.write(patch_text)
        temp_patch_path = Path(file.name)

    try:
        result = subprocess.run(
            ["git", "apply", "--check", str(temp_patch_path)],
            cwd=workspace_path,
            capture_output=True,
            text=True,
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Could not validate patch: {exc}") from exc
    finally:
        temp_patch_path.unlink(missing_ok=True)

    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip() or "git apply --check failed."
        raise ValueError(f"Patch does not apply cleanly: {details}")


def validate_and_repair_patch(workspace_path: Path, patch_text: str) -> str:
    repaired_patch = auto_repair_patch_text(patch_text)
    validate_patch(workspace_path, repaired_patch)
    return repaired_patch


def _format_command(command: list[str]) -> str:
    return shlex.join(command)


def _request_command_approval(command: list[str], cwd: Path, preview: str | None = None) -> bool:
    formatted_command = _format_command(command)
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


def _run_mutating_command(
    command: list[str],
    cwd: Path,
    preview: str | None = None,
) -> subprocess.CompletedProcess[str]:
    formatted_command = _format_command(command)
    if not _request_command_approval(command, cwd, preview):
        raise PermissionError(f"User rejected command: {formatted_command}")

    print(f"Executing command: {formatted_command}")
    trace_command_event("executed", formatted_command, cwd)
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def apply_patch(workspace_path: Path) -> None:
    patch_path = workspace_path / "patch.txt"
    patch_text = patch_path.read_text(encoding="utf-8")
    result = _run_mutating_command(
        ["git", "apply", patch_path.name],
        workspace_path,
        preview=patch_text,
    )

    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip() or "git apply failed."
        raise ValueError(f"Patch could not be applied: {details}")
