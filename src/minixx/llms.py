from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import shutil
import subprocess
from pathlib import Path

from .context import AgentContext
from .traces import trace_response


def build_codex_prompt(system_prompt: str, user_prompt: str) -> str:
    return f"""{system_prompt}

Use only the explicit context in this prompt.
Do not rely on previous conversation state or hidden context.

{user_prompt}"""


def require_config_value(value: str | None, key: str, backend_name: str) -> str:
    if not value:
        raise ValueError(f"Missing {key} for {backend_name} backend.")
    return value


def call_codex(context: AgentContext, user_prompt: str) -> str:
    codex_command = require_config_value(context.llm_config.codex_command, "codex_command", "Codex")
    working_directory = context.llm_config.working_directory
    prompt = build_codex_prompt(context.system_prompt, user_prompt)

    if shutil.which(codex_command) is None:
        raise RuntimeError(f"Codex CLI not found in PATH: {codex_command}")

    try:
        result = subprocess.run(
            [codex_command, "exec", "--sandbox", "read-only", "--skip-git-repo-check", prompt],
            cwd=working_directory,
            capture_output=True,
            text=True,
            timeout=context.llm_config.timeout_seconds,
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


def call_ollama(context: AgentContext, user_prompt: str) -> str:
    try:
        from ollama import Client
    except ImportError as exc:
        raise RuntimeError("Ollama Python package not installed. Run pip install -r requirements.txt.") from exc

    ollama_url = require_config_value(context.llm_config.ollama_url, "ollama_url", "Ollama")
    ollama_model = require_config_value(context.llm_config.ollama_model, "ollama_model", "Ollama")
    client = Client(host=ollama_url)

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                client.chat,
                model=ollama_model,
                messages=[
                    {"role": "system", "content": context.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            response = future.result(timeout=context.llm_config.timeout_seconds)
    except FuturesTimeoutError as exc:
        raise RuntimeError(f"Ollama request timed out after {context.llm_config.timeout_seconds} seconds.") from exc
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Could not connect to Ollama at {ollama_url}.") from exc

    return extract_ollama_content(response)


def call_llm(context: AgentContext, user_prompt: str, response_label: str = "Response") -> str:
    backend = context.llm_config.backend

    if backend == "codex":
        response = call_codex(context, user_prompt)
    elif backend == "ollama":
        response = call_ollama(context, user_prompt)
    else:
        raise ValueError(f"Unsupported backend: {backend}")

    trace_response(response, response_label)
    return response
