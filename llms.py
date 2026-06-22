from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from logs import log_response


def build_codex_prompt(system_prompt: str, user_prompt: str) -> str:
    return f"""{system_prompt}

Use only the explicit context in this prompt.
Do not rely on previous conversation state or hidden context.

{user_prompt}"""


def call_codex(llm_config: dict, system_prompt: str, user_prompt: str) -> str:
    codex_command = llm_config["codex_command"]
    working_directory = Path(llm_config["working_directory"])
    prompt = build_codex_prompt(system_prompt, user_prompt)

    if shutil.which(codex_command) is None:
        raise RuntimeError(f"Codex CLI not found in PATH: {codex_command}")

    try:
        result = subprocess.run(
            [codex_command, "exec", "--sandbox", "read-only", "--skip-git-repo-check", prompt],
            cwd=working_directory,
            capture_output=True,
            text=True,
            timeout=llm_config["timeout_seconds"],
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Could not execute Codex in {working_directory}.") from exc

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Codex returned an error.")

    content = result.stdout.strip()
    if not content:
        raise ValueError("Codex returned an empty response.")

    return content


def call_llm(llm_config: dict, system_prompt: str, user_prompt: str) -> str:
    backend = llm_config["backend"]

    if backend == "codex":
        response = call_codex(llm_config, system_prompt, user_prompt)
    else:
        raise ValueError(f"Unsupported backend: {backend}")

    log_response(response)
    return response
