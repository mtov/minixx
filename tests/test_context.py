from __future__ import annotations

from minixx.context import (
    AgentAction,
    AgentHistory,
    MAX_HISTORY_ENTRIES,
    MAX_OBSERVATION_CHARS,
)


def test_agent_history_to_text_omits_thought_and_limits_entries() -> None:
    history = AgentHistory()

    for iteration in range(1, MAX_HISTORY_ENTRIES + 3):
        history.append(
            iteration,
            AgentAction(thought=f"thought {iteration}", tool="read_file", tool_args=f"file_{iteration}.py"),
            f"contents {iteration}",
        )

    text = history.to_text()

    assert "Thought:" not in text
    assert "Iteration 1" not in text
    assert f"Iteration {MAX_HISTORY_ENTRIES + 2}" in text
    assert "Files already read:" in text
    assert f"- file_{MAX_HISTORY_ENTRIES + 2}.py" in text


def test_agent_history_to_text_truncates_long_observations() -> None:
    history = AgentHistory()
    long_observation = "x" * (MAX_OBSERVATION_CHARS + 50)
    history.append(
        1,
        AgentAction(thought="inspect", tool="read_file", tool_args="demo.py"),
        long_observation,
    )

    text = history.to_text()

    assert "Observation: " in text
    assert long_observation not in text
    assert "..." in text


def test_agent_history_to_text_summarizes_unique_reads_and_searches() -> None:
    history = AgentHistory()
    history.append(1, AgentAction(thought="inspect", tool="read_file", tool_args="src/a.py"), "a")
    history.append(2, AgentAction(thought="repeat", tool="read_file", tool_args="src/a.py"), "a")
    history.append(3, AgentAction(thought="search", tool="find_text", tool_args="coupon | src"), "match")
    history.append(4, AgentAction(thought="test", tool="run_tests", tool_args=""), "passed")

    text = history.to_text()

    assert text.count("- src/a.py") == 1
    assert "Searches already run:" in text
    assert "- coupon | src" in text
    assert "Tests already run: yes" in text


def test_agent_history_contains_tool_uses_structured_entries() -> None:
    history = AgentHistory()
    history.append(1, AgentAction(thought="inspect", tool="find_text", tool_args="needle | ."), "match")

    assert history.contains_tool("find_text") is True
    assert history.contains_tool("run_tests") is False
