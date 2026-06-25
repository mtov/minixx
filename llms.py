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


def require_config_value(llm_config: dict, key: str, backend_name: str) -> str:
    value = llm_config.get(key)
    if not value:
        raise ValueError(f"Missing {key} for {backend_name} backend.")
    return value


def call_codex(llm_config: dict, system_prompt: str, user_prompt: str) -> str:
    codex_command = require_config_value(llm_config, "codex_command", "Codex")
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


def extract_ollama_content(response: object) -> str:
    message = getattr(response, "message", None)
    if message is not None:
        content = getattr(message, "content", None)
        if content:
            return content.strip()

    if isinstance(response, dict):
        message = response.get("message", {})
        content = message.get("content")
        if content:
            return content.strip()

    raise ValueError("Ollama returned a response without message content.")


def call_ollama(llm_config: dict, system_prompt: str, user_prompt: str) -> str:
    try:
        from ollama import Client
    except ImportError as exc:
        raise RuntimeError("Ollama Python package not installed. Run pip install -r requirements.txt.") from exc

    ollama_url = require_config_value(llm_config, "ollama_url", "Ollama")
    ollama_model = require_config_value(llm_config, "ollama_model", "Ollama")
    client = Client(host=ollama_url)

    try:
        response = client.chat(
            model=ollama_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Could not connect to Ollama at {ollama_url}.") from exc

    return extract_ollama_content(response)


def call_llm(llm_config: dict, system_prompt: str, user_prompt: str) -> str:
    backend = llm_config["backend"]

    if backend == "codex":
        response = call_codex(llm_config, system_prompt, user_prompt)
    elif backend == "ollama":
        response = call_ollama(llm_config, system_prompt, user_prompt)
    else:
        raise ValueError(f"Unsupported backend: {backend}")

    log_response(response)
    return response
