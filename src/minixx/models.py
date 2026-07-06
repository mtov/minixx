from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import os
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


def require_config_value(value: str | None, key: str, model_name: str) -> str:
    if not value:
        raise ValueError(f"Missing {key} for {model_name} model.")
    return value


def call_codex(context: AgentContext, user_prompt: str) -> str:
    codex_command = require_config_value(context.model_config.codex_command, "codex_command", "Codex")
    working_directory = context.model_config.working_directory
    prompt = build_codex_prompt(context.system_prompt, user_prompt)

    if shutil.which(codex_command) is None:
        raise RuntimeError(f"Codex CLI not found in PATH: {codex_command}")

    try:
        result = subprocess.run(
            [codex_command, "exec", "--sandbox", "read-only", "--skip-git-repo-check", prompt],
            cwd=working_directory,
            capture_output=True,
            text=True,
            timeout=context.model_config.timeout_seconds,
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

    ollama_url = require_config_value(context.model_config.ollama_url, "ollama_url", "Ollama")
    ollama_model = require_config_value(context.model_config.ollama_model, "ollama_model", "Ollama")
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
            response = future.result(timeout=context.model_config.timeout_seconds)
    except FuturesTimeoutError as exc:
        raise RuntimeError(f"Ollama request timed out after {context.model_config.timeout_seconds} seconds.") from exc
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Could not connect to Ollama at {ollama_url}.") from exc

    return extract_ollama_content(response)


def call_gemini(context: AgentContext, user_prompt: str) -> str:
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError(
            "Google GenAI Python package not installed. Run pip install -r requirements.txt."
        ) from exc

    gemini_api_key = require_config_value(
        os.environ.get("GEMINI_API_KEY"),
        "GEMINI_API_KEY",
        "Gemini",
    )
    gemini_model = require_config_value(
        context.model_config.gemini_model,
        "gemini_model",
        "Gemini",
    )
    client = genai.Client(api_key=gemini_api_key)

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                client.interactions.create,
                model=gemini_model,
                system_instruction=context.system_prompt,
                input=user_prompt,
            )
            interaction = future.result(timeout=context.model_config.timeout_seconds)
    except FuturesTimeoutError as exc:
        raise RuntimeError(
            f"Gemini request timed out after {context.model_config.timeout_seconds} seconds."
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("Could not execute Gemini request.") from exc

    content = getattr(interaction, "output_text", None)
    if content:
        return content.strip()

    raise ValueError("Gemini returned a response without output_text.")


def call_model(context: AgentContext, user_prompt: str, response_label: str = "Response") -> str:
    model = context.model_config.model

    if model == "codex":
        response = call_codex(context, user_prompt)
    elif model == "gemini":
        response = call_gemini(context, user_prompt)
    elif model == "ollama":
        response = call_ollama(context, user_prompt)
    else:
        raise ValueError(f"Unsupported model: {model}")

    trace_response(response, response_label)
    return response
