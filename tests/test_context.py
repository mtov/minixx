from __future__ import annotations

from minixx.context import (
    AgentHistory,
    AgentResponse,
    MAX_HISTORY_ENTRIES,
    MAX_OBSERVATION_CHARS,
    RECENT_DUPLICATE_ACTION_WINDOW,
)


def test_agent_history_to_text_omits_thought_and_limits_entries() -> None:
    history = AgentHistory()

    for iteration in range(1, MAX_HISTORY_ENTRIES + 3):
        history.append(
            iteration,
            AgentResponse(thought=f"thought {iteration}", action="read_file", action_input=f"file_{iteration}.py"),
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
        AgentResponse(thought="inspect", action="read_file", action_input="demo.py"),
        long_observation,
    )

    text = history.to_text()

    assert "Observation: " in text
    assert long_observation not in text
    assert "..." in text


def test_agent_history_to_text_summarizes_unique_reads_and_searches() -> None:
    history = AgentHistory()
    history.append(1, AgentResponse(thought="inspect", action="read_file", action_input="src/a.py"), "a")
    history.append(2, AgentResponse(thought="repeat", action="read_file", action_input="src/a.py"), "a")
    history.append(3, AgentResponse(thought="search", action="find_text", action_input="coupon | src"), "match")
    history.append(4, AgentResponse(thought="test", action="run_tests", action_input=""), "passed")

    text = history.to_text()

    assert text.count("- src/a.py") == 1
    assert "Searches already run:" in text
    assert "- coupon | src" in text
    assert "Tests already run: yes" in text


def test_agent_history_contains_action_uses_structured_entries() -> None:
    history = AgentHistory()
    history.append(1, AgentResponse(thought="inspect", action="find_text", action_input="needle | ."), "match")

    assert history.contains_action("find_text") is True
    assert history.contains_action("run_tests") is False


def test_agent_history_detects_recent_duplicate_action_input() -> None:
    history = AgentHistory()
    history.append(1, AgentResponse(thought="inspect", action="read_file", action_input="src/a.py"), "a")
    history.append(2, AgentResponse(thought="search", action="find_text", action_input="needle | src"), "match")
    history.append(3, AgentResponse(thought="inspect other", action="read_file", action_input="src/b.py"), "b")

    assert history.has_recent_duplicate_action_input("read_file", "src/a.py") is True
    assert history.has_recent_duplicate_action_input("find_text", "needle | src") is True
    assert history.has_recent_duplicate_action_input("read_file", "src/b.py") is True
    assert history.has_recent_duplicate_action_input("read_file", "src/c.py") is False
    assert history.has_recent_duplicate_action_input("run_tests", "") is False


def test_agent_history_ignores_duplicates_outside_recent_action_window() -> None:
    history = AgentHistory()

    history.append(1, AgentResponse(thought="target", action="read_file", action_input="src/target.py"), "target")
    for index in range(RECENT_DUPLICATE_ACTION_WINDOW, 0, -1):
        history.append(
            RECENT_DUPLICATE_ACTION_WINDOW - index + 2,
            AgentResponse(
                thought=f"other {index}",
                action="read_file",
                action_input=f"src/other_{index}.py",
            ),
            f"other {index}",
        )

    assert history.has_recent_duplicate_action_input("read_file", "src/target.py") is False
