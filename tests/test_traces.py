from __future__ import annotations

from pathlib import Path

from minixx.context import TokenUsage
from minixx import traces


def test_trace_response_records_token_usage_and_cumulative_total(
    monkeypatch,
    tmp_path: Path,
) -> None:
    log_path = tmp_path / "agent_trace.log"
    monkeypatch.setattr(traces, "LOG_PATH", log_path)

    traces.clear_trace()
    traces.trace_response(
        "first response",
        token_usage=TokenUsage(input_tokens=10, output_tokens=5, total_tokens=15),
    )
    traces.trace_response(
        "second response",
        token_usage=TokenUsage(input_tokens=4, output_tokens=3, total_tokens=7),
    )

    content = log_path.read_text(encoding="utf-8")

    assert "Response 1" in content
    assert "Token Usage: input=10 output=5 total=15" in content
    assert "Cumulative Tokens: 15" in content
    assert "Response 2" in content
    assert "Token Usage: input=4 output=3 total=7" in content
    assert "Cumulative Tokens: 22" in content


def test_format_token_usage_handles_unavailable_usage() -> None:
    assert traces.format_token_usage(TokenUsage()) == "Token Usage: unavailable"
