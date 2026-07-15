from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

MAX_HISTORY_ENTRIES = 4
MAX_OBSERVATION_CHARS = 1200
RECENT_DUPLICATE_ACTION_WINDOW = 5


@dataclass
class ModelConfig:
    model: str
    timeout_seconds: int
    openai_base_url: str | None
    openai_model: str | None
    openai_api_key_env: str | None


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
    post_apply_tests_passed: bool = False


@dataclass
class AgentResponse:
    thought: str
    action: str
    action_input: str


@dataclass
class FinishResult:
    status: str
    agent_response: AgentResponse
    test_output: str | None = None


@dataclass
class AgentHistory:
    entries: list[tuple[int, AgentResponse, str]] = field(default_factory=list)

    def append(self, iteration: int, agent_response: AgentResponse, tool_result: str) -> None:
        self.entries.append((iteration, agent_response, tool_result))

    def contains_action(self, action: str) -> bool:
        return any(agent_response.action == action for _, agent_response, _ in self.entries)

    def has_recent_duplicate_action_input(self, action: str, action_input: str) -> bool:
        normalized_input = action_input.strip()
        if not normalized_input:
            return False

        inspected_matches = 0
        for _, agent_response, _ in reversed(self.entries):
            if agent_response.action != action:
                continue
            inspected_matches += 1
            if agent_response.action_input.strip() == normalized_input:
                return True
            if inspected_matches >= RECENT_DUPLICATE_ACTION_WINDOW:
                return False

        return False

    def _unique_action_inputs(self, action: str) -> list[str]:
        seen: set[str] = set()
        items: list[str] = []

        for _, agent_response, _ in self.entries:
            if agent_response.action != action:
                continue
            value = agent_response.action_input.strip()
            if not value or value in seen:
                continue
            seen.add(value)
            items.append(value)

        return items

    def to_text(self) -> str:
        if not self.entries:
            return "No previous steps."

        sections: list[str] = []
        read_files = self._unique_action_inputs("read_file")
        find_queries = self._unique_action_inputs("find_text")

        if read_files:
            sections.append(
                "Files already read:\n"
                + "\n".join(f"- {path}" for path in read_files)
            )
        if find_queries:
            sections.append(
                "Searches already run:\n"
                + "\n".join(f"- {query}" for query in find_queries)
            )
        if self.contains_action("run_tests"):
            sections.append("Tests already run: yes")

        formatted_entries = []
        for iteration, agent_response, tool_result in self.entries[-MAX_HISTORY_ENTRIES:]:
            observation = tool_result.strip()
            if len(observation) > MAX_OBSERVATION_CHARS:
                observation = f"{observation[:MAX_OBSERVATION_CHARS].rstrip()}..."
            formatted_entries.append(
                f"Iteration {iteration}\n"
                f"Action: {agent_response.action}\n"
                f"Action Input: {agent_response.action_input}\n"
                f"Observation: {observation}\n"
            )
        sections.append("Recent steps:\n" + "\n".join(formatted_entries))
        return "\n\n".join(sections)
