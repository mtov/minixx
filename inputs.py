from __future__ import annotations

import json
from pathlib import Path

CONFIG_DIR = Path("config")
CONFIG_PATH = CONFIG_DIR / "config.json"
SYSTEM_PROMPT_PATH = CONFIG_DIR / "system_prompt.txt"
USER_PROMPT_PATH = CONFIG_DIR / "prompt.txt"


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


def load_user_prompt() -> str:
    try:
        prompt = USER_PROMPT_PATH.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"User prompt file not found: {USER_PROMPT_PATH}") from exc
    except OSError as exc:
        raise OSError(f"Could not read user prompt file: {USER_PROMPT_PATH}") from exc

    if not prompt:
        raise ValueError("User prompt file is empty.")
    return prompt
