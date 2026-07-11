from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import os
import shutil
import subprocess

from .context import AgentContext, ModelResponse, TokenUsage
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


def build_model_response(content: str, token_usage: TokenUsage | None = None) -> ModelResponse:
    return ModelResponse(content=content, token_usage=token_usage or TokenUsage())


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


def extract_openai_content(response: object) -> str:
    choices = getattr(response, "choices", None)
    if choices is None and isinstance(response, dict):
        choices = response.get("choices")

    if not choices:
        raise ValueError("OpenAI-compatible model returned a response without choices.")

    first_choice = choices[0]
    message = getattr(first_choice, "message", None)
    if message is None and isinstance(first_choice, dict):
        message = first_choice.get("message", {})

    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content")

    if isinstance(content, str) and content.strip():
        return content.strip()

    if isinstance(content, list):
        text_parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
                continue
            if isinstance(part, dict) and part.get("type") == "text" and part.get("text"):
                text_parts.append(str(part["text"]))
                continue
            text = getattr(part, "text", None)
            if text:
                text_parts.append(str(text))
        joined = "".join(text_parts).strip()
        if joined:
            return joined

    raise ValueError("OpenAI-compatible model returned a response without message content.")


def extract_openai_usage(response: object) -> TokenUsage:
    usage = getattr(response, "usage", None)
    if usage is None and isinstance(response, dict):
        usage = response.get("usage")
    if usage is None:
        return TokenUsage()

    prompt_tokens = getattr(usage, "prompt_tokens", None)
    output_tokens = getattr(usage, "completion_tokens", None)
    total_tokens = getattr(usage, "total_tokens", None)

    if isinstance(usage, dict):
        prompt_tokens = usage.get("prompt_tokens", prompt_tokens)
        output_tokens = usage.get("completion_tokens", output_tokens)
        total_tokens = usage.get("total_tokens", total_tokens)

    if total_tokens is None and (prompt_tokens is not None or output_tokens is not None):
        total_tokens = (prompt_tokens or 0) + (output_tokens or 0)

    return TokenUsage(
        input_tokens=prompt_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
    )


def resolve_openai_api_key(context: AgentContext) -> str:
    api_key_env = context.model_config.openai_api_key_env
    if api_key_env:
        return require_config_value(
            os.environ.get(api_key_env),
            api_key_env,
            "OpenAI-compatible",
        )

    return os.environ.get("OPENAI_API_KEY", "minixx")


def call_openai_compatible(context: AgentContext, user_prompt: str) -> ModelResponse:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("OpenAI Python package not installed. Run pip install -r requirements.txt.") from exc

    openai_model = require_config_value(
        context.model_config.openai_model,
        "openai_model",
        "OpenAI-compatible",
    )
    client = OpenAI(
        api_key=resolve_openai_api_key(context),
        base_url=context.model_config.openai_base_url,
    )

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                client.chat.completions.create,
                model=openai_model,
                messages=[
                    {"role": "system", "content": context.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            response = future.result(timeout=context.model_config.timeout_seconds)
    except FuturesTimeoutError as exc:
        raise RuntimeError(
            f"OpenAI-compatible request timed out after {context.model_config.timeout_seconds} seconds."
        ) from exc
    except Exception as exc:  # noqa: BLE001
        base_url = context.model_config.openai_base_url or "default OpenAI endpoint"
        raise RuntimeError(
            f"OpenAI-compatible request failed for {base_url}: {exc.__class__.__name__}: {exc}"
        ) from exc

    return build_model_response(
        extract_openai_content(response),
        extract_openai_usage(response),
    )


def call_model(
    context: AgentContext,
    user_prompt: str,
    response_label: str = "Response",
) -> ModelResponse:
    model = context.model_config.model

    if model == "codex":
        response = call_codex(context, user_prompt)
    elif model == "openai-compatible":
        response = call_openai_compatible(context, user_prompt)
    else:
        raise ValueError(f"Unsupported model: {model}")

    trace_response(response.content, response_label, response.token_usage)
    return response
