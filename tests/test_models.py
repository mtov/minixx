from __future__ import annotations

from types import SimpleNamespace

from minixx.models import extract_gemini_usage, extract_ollama_usage


def test_extract_ollama_usage_uses_prompt_and_eval_counts() -> None:
    response = SimpleNamespace(prompt_eval_count=12, eval_count=8)

    usage = extract_ollama_usage(response)

    assert usage.input_tokens == 12
    assert usage.output_tokens == 8
    assert usage.total_tokens == 20


def test_extract_gemini_usage_uses_usage_metadata() -> None:
    interaction = SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=9,
            candidates_token_count=6,
            total_token_count=15,
        )
    )

    usage = extract_gemini_usage(interaction)

    assert usage.input_tokens == 9
    assert usage.output_tokens == 6
    assert usage.total_tokens == 15


def test_extract_gemini_usage_returns_unavailable_without_metadata() -> None:
    usage = extract_gemini_usage(SimpleNamespace())

    assert usage.input_tokens is None
    assert usage.output_tokens is None
    assert usage.total_tokens is None
