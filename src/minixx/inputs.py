from __future__ import annotations

import argparse
import json
from pathlib import Path

from .context import AgentContext
from .logs import clear_log, log_request

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
CONFIG_PATH = CONFIG_DIR / "config.json"
SYSTEM_PROMPT_PATH = CONFIG_DIR / "system_prompt.txt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Minixx")
    parser.add_argument("workspace_path", help="Path to the test workspace directory")
    return parser.parse_args()


def load_llm_config() -> dict:
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}") from exc
    except OSError as exc:
        raise OSError(f"Could not read config file: {CONFIG_PATH}") from exc


def load_system_prompt() -> str:
    try:
        prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"System prompt file not found: {SYSTEM_PROMPT_PATH}") from exc
    except OSError as exc:
        raise OSError(f"Could not read system prompt file: {SYSTEM_PROMPT_PATH}") from exc

    if not prompt:
        raise ValueError("System prompt file is empty.")
    return prompt


def resolve_workspace_path(raw_path: str) -> Path:
    workspace_path = Path(raw_path).expanduser().resolve()
    if not workspace_path.exists():
        raise FileNotFoundError(f"Workspace path not found: {workspace_path}")
    if not workspace_path.is_dir():
        raise NotADirectoryError(f"Workspace path is not a directory: {workspace_path}")
    return workspace_path


def load_user_prompt(workspace_path: Path) -> str:
    prompt_path = workspace_path / "prompt.txt"

    try:
        prompt = prompt_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"User prompt file not found: {prompt_path}") from exc
    except OSError as exc:
        raise OSError(f"Could not read user prompt file: {prompt_path}") from exc

    if not prompt:
        raise ValueError("User prompt file is empty.")
    return prompt


def prepare_run(workspace_path_arg: str) -> AgentContext:
    clear_log()
    workspace_path = resolve_workspace_path(workspace_path_arg)
    llm_config = load_llm_config()
    llm_config["working_directory"] = str(workspace_path)
    system_prompt = load_system_prompt()
    user_prompt = load_user_prompt(workspace_path)
    log_request(user_prompt)
    return AgentContext(llm_config=llm_config, system_prompt=system_prompt, user_prompt=user_prompt, workspace_path=workspace_path)
