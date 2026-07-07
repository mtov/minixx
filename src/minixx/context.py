from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ModelConfig:
    model: str
    timeout_seconds: int
    codex_command: str | None
    gemini_model: str | None
    ollama_url: str | None
    ollama_model: str | None
    working_directory: Path


@dataclass
class TokenUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


@dataclass
class ModelResponse:
    content: str
    token_usage: TokenUsage


@dataclass
class AgentContext:
    model_config: ModelConfig
    system_prompt: str
    user_prompt: str
    workspace_path: Path


@dataclass
class AgentResponse:
    thought: str
    action: str
    action_input: str
    action_description: str


@dataclass
class AgentHistory:
    entries: list[str] = field(default_factory=list)

    def append(self, iteration: int, agent_response: AgentResponse, tool_result: str) -> None:
        entry = (
            f"Iteration {iteration}\n"
            f"Thought: {agent_response.thought}\n"
            f"Action: {agent_response.action}\n"
            f"Action Input: {agent_response.action_input}\n"
            f"Action Description: {agent_response.action_description}\n"
            f"Observation: {tool_result}\n"
        )
        self.entries.append(entry)

    def contains_action(self, action: str) -> bool:
        return any(f"Action: {action}" in entry for entry in self.entries)

    def to_text(self) -> str:
        if not self.entries:
            return "No previous steps."
        return "\n".join(self.entries)
