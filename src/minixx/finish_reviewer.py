from __future__ import annotations

from .context import AgentContext, AgentHistory, AgentResponse


def review_finish(
    context: AgentContext,
    user_message: str,
    agent_history: AgentHistory,
    agent_response: AgentResponse,
) -> AgentResponse | None:
    del context, user_message, agent_history, agent_response
    return None
