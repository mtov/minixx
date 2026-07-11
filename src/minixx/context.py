from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

MAX_HISTORY_ENTRIES = 4
MAX_OBSERVATION_CHARS = 1200


@dataclass
class ModelConfig:
    model: str
    timeout_seconds: int
    openai_base_url: str | None
    openai_model: str | None
    openai_api_key_env: str | None
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
    source_workspace_path: Path
    workspace_path: Path


@dataclass
class AgentResponse:
    thought: str
    action: str
    action_input: str


@dataclass
class AgentHistory:
    entries: list[tuple[int, AgentResponse, str]] = field(default_factory=list)

    def _format_observation(self, tool_result: str) -> str:
        observation = tool_result.strip()
        if len(observation) <= MAX_OBSERVATION_CHARS:
            return observation
        return f"{observation[:MAX_OBSERVATION_CHARS].rstrip()}..."

    def append(self, iteration: int, agent_response: AgentResponse, tool_result: str) -> None:
        self.entries.append((iteration, agent_response, tool_result))

    def contains_action(self, action: str) -> bool:
        return any(agent_response.action == action for _, agent_response, _ in self.entries)

    def to_text(self) -> str:
        if not self.entries:
            return "No previous steps."
        formatted_entries = []
        for iteration, agent_response, tool_result in self.entries[-MAX_HISTORY_ENTRIES:]:
            formatted_entries.append(
                f"Iteration {iteration}\n"
                f"Action: {agent_response.action}\n"
                f"Action Input: {agent_response.action_input}\n"
                f"Observation: {self._format_observation(tool_result)}\n"
            )
        return "\n".join(formatted_entries)
