from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import os
import shutil
import subprocess
from pathlib import Path

from .context import AgentContext, ModelResponse, TokenUsage
from .traces import format_token_usage, trace_response


def build_codex_prompt(system_prompt: str, user_prompt: str) -> str:
    return f"""{system_prompt}

Use only the explicit context in this prompt.
Do not rely on previous conversation state or hidden context.

{user_prompt}"""


def require_config_value(value: str | None, key: str, model_name: str) -> str:
    if not value:
        raise ValueError(f"Missing {key} for {model_name} model.")
    return value


def build_model_response(content: str, token_usage: TokenUsage | None = None) -> ModelResponse:
    return ModelResponse(content=content, token_usage=token_usage or TokenUsage())


def print_token_usage(label: str, token_usage: TokenUsage) -> None:
    print(f"[tokens] {label}: {format_token_usage(token_usage)}", flush=True)


def call_codex(context: AgentContext, user_prompt: str) -> ModelResponse:
    codex_command = require_config_value(context.model_config.codex_command, "codex_command", "Codex")
    working_directory = context.model_config.working_directory
    prompt = build_codex_prompt(context.system_prompt, user_prompt)

    if shutil.which(codex_command) is None:
        raise RuntimeError(f"Codex CLI not found in PATH: {codex_command}.")

    try:
        result = subprocess.run(
            [codex_command, "exec", "--sandbox", "read-only", "--skip-git-repo-check", prompt],
            cwd=working_directory,
            capture_output=True,
            text=True,
            timeout=context.model_config.timeout_seconds,
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            f"Codex request failed in {working_directory}: {exc.__class__.__name__}: {exc}"
        ) from exc

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or result.stdout.strip() or "Codex request failed."
        )

    content = result.stdout.strip()
    if not content:
        raise ValueError("Codex returned an empty response.")

    return build_model_response(content)


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


def extract_ollama_usage(response: object) -> TokenUsage:
    prompt_tokens = getattr(response, "prompt_eval_count", None)
    output_tokens = getattr(response, "eval_count", None)

    if isinstance(response, dict):
        prompt_tokens = response.get("prompt_eval_count", prompt_tokens)
        output_tokens = response.get("eval_count", output_tokens)

    total_tokens = None
    if prompt_tokens is not None or output_tokens is not None:
        total_tokens = (prompt_tokens or 0) + (output_tokens or 0)

    return TokenUsage(
        input_tokens=prompt_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
    )


def call_ollama(context: AgentContext, user_prompt: str) -> ModelResponse:
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
        raise RuntimeError(
            f"Ollama request timed out after {context.model_config.timeout_seconds} seconds."
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            f"Ollama request failed for {ollama_url}: {exc.__class__.__name__}: {exc}"
        ) from exc

    return build_model_response(
        extract_ollama_content(response),
        extract_ollama_usage(response),
    )


def extract_gemini_usage(interaction: object) -> TokenUsage:
    usage_metadata = getattr(interaction, "usage_metadata", None)
    if usage_metadata is None:
        return TokenUsage()

    prompt_tokens = getattr(usage_metadata, "prompt_token_count", None)
    output_tokens = getattr(usage_metadata, "candidates_token_count", None)
    total_tokens = getattr(usage_metadata, "total_token_count", None)

    if total_tokens is None and (prompt_tokens is not None or output_tokens is not None):
        total_tokens = (prompt_tokens or 0) + (output_tokens or 0)

    return TokenUsage(
        input_tokens=prompt_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
    )


def call_gemini(context: AgentContext, user_prompt: str) -> ModelResponse:
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
        if exc.__class__.__name__ == "RateLimitError":
            raise RuntimeError(
                "Gemini quota exceeded or rate limited. "
                "Check your API quota/billing, wait and retry, or switch to another model."
            ) from exc
        raise RuntimeError(
            f"Gemini request failed: {exc.__class__.__name__}: {exc}"
        ) from exc

    content = getattr(interaction, "output_text", None)
    if content:
        return build_model_response(content.strip(), extract_gemini_usage(interaction))

    raise ValueError("Gemini returned a response without output_text.")


def call_model(
    context: AgentContext,
    user_prompt: str,
    response_label: str = "Response",
) -> ModelResponse:
    model = context.model_config.model

    if model == "codex":
        response = call_codex(context, user_prompt)
    elif model == "gemini":
        response = call_gemini(context, user_prompt)
    elif model == "ollama":
        response = call_ollama(context, user_prompt)
    else:
        raise ValueError(f"Unsupported model: {model}")

    trace_response(response.content, response_label, response.token_usage)
    print_token_usage(response_label, response.token_usage)
    return response
