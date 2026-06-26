from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AgentContext:
    llm_config: dict
    system_prompt: str
    user_prompt: str
    workspace_path: Path


@dataclass
class AgentResponse:
    thought: str
    action: str
    action_input: str


@dataclass
class AgentHistory:
    entries: list[str] = field(default_factory=list)

    def append(self, iteration: int, agent_response: AgentResponse, tool_result: str) -> None:
        entry = (
            f"Iteration {iteration}\n"
            f"Thought: {agent_response.thought}\n"
            f"Action: {agent_response.action}\n"
            f"Action Input: {agent_response.action_input}\n"
            f"Observation: {tool_result}\n"
        )
        self.entries.append(entry)

    def contains_action(self, action: str) -> bool:
        return any(f"Action: {action}" in entry for entry in self.entries)

    def to_text(self) -> str:
        if not self.entries:
            return "No previous steps."
        return "\n".join(self.entries)
