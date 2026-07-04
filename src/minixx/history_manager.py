from __future__ import annotations

from .context import AgentHistory, AgentResponse


def create_history() -> AgentHistory:
    return AgentHistory()


def update_history(
    history: AgentHistory,
    iteration: int,
    agent_response: AgentResponse,
    tool_result: str,
) -> None:
    history.append(iteration, agent_response, tool_result)


def history_to_text(history: AgentHistory) -> str:
    return history.to_text()
