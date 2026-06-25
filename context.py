from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class AgentContext:
    llm_config: dict
    system_prompt: str
    user_prompt: str
    workspace_path: Path
