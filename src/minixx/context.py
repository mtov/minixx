from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

MAX_HISTORY_ENTRIES = 4
MAX_OBSERVATION_CHARS = 1200
MAX_ITERATIONS_REACHED_MESSAGE = "Agent stopped after reaching the maximum number of steps."


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
class ToolRequest:
    thought: str
    name: str
    args: str


@dataclass
class FinishResult:
    status: str
    request: ToolRequest
    test_output: str | None = None


@dataclass
class LoopResult:
    status: str
    output: str | None = None
    error: str | None = None

    @classmethod
    def success(cls, output: str) -> LoopResult:
        return cls(status="success", output=output)

    @classmethod
    def error(cls, message: str, *, status: str = "error") -> LoopResult:
        return cls(status=status, error=message)

    @classmethod
    def max_iterations_reached(cls) -> LoopResult:
        return cls(
            status="max_iterations_reached",
            error=MAX_ITERATIONS_REACHED_MESSAGE,
        )


@dataclass
class AgentHistory:
    entries: list[tuple[int, ToolRequest, str]] = field(default_factory=list)

    def append(self, iteration: int, request: ToolRequest, tool_result: str) -> None:
        self.entries.append((iteration, request, tool_result))

    def contains_tool(self, name: str) -> bool:
        return any(request.name == name for _, request, _ in self.entries)

    def _unique_tool_args(self, name: str) -> list[str]:
        seen: set[str] = set()
        items: list[str] = []

        for _, request, _ in self.entries:
            if request.name != name:
                continue
            value = request.args.strip()
            if not value or value in seen:
                continue
            seen.add(value)
            items.append(value)

        return items

    def to_text(self) -> str:
        if not self.entries:
            return "No previous steps."

        sections: list[str] = []
        read_files = self._unique_tool_args("read_file")
        find_queries = self._unique_tool_args("find_text")

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
        if self.contains_tool("run_tests"):
            sections.append("Tests already run: yes")

        formatted_entries = []
        for iteration, request, tool_result in self.entries[-MAX_HISTORY_ENTRIES:]:
            observation = tool_result.strip()
            if len(observation) > MAX_OBSERVATION_CHARS:
                observation = f"{observation[:MAX_OBSERVATION_CHARS].rstrip()}..."
            formatted_entries.append(
                f"Iteration {iteration}\n"
                f"Tool: {request.name}\n"
                f"Tool Args: {request.args}\n"
                f"Observation: {observation}\n"
            )
        sections.append("Recent steps:\n" + "\n".join(formatted_entries))
        return "\n\n".join(sections)
