from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from .context import AgentContext, ModelConfig
from .traces import clear_trace, trace_request

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_WORKSPACE_PATH = PROJECT_ROOT / "minixx-workspace"
CONFIG_DIR = PROJECT_ROOT / "config"
CONFIG_PATH = CONFIG_DIR / "config.json"
SYSTEM_PROMPT_PATH = CONFIG_DIR / "system_prompt.txt"
WORKSPACE_INSTRUCTIONS_PATH = "AGENTS.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Minixx")
    parser.add_argument("workspace_path", help="Path to the test workspace directory")
    return parser.parse_args()


def load_model_config(working_directory: Path) -> ModelConfig:
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as file:
            raw_config = json.load(file)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}") from exc
    except OSError as exc:
        raise OSError(f"Could not read config file: {CONFIG_PATH}") from exc

    selected_model = raw_config.get("model")
    if selected_model is None:
        raise KeyError("Config file must define 'model'.")

    return ModelConfig(
        model=selected_model,
        timeout_seconds=raw_config["timeout_seconds"],
        openai_base_url=raw_config.get("openai_base_url"),
        openai_model=raw_config.get("openai_model"),
        openai_api_key_env=raw_config.get("openai_api_key_env"),
        working_directory=working_directory,
    )


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


def load_workspace_instructions(workspace_path: Path) -> str | None:
    instructions_path = workspace_path / WORKSPACE_INSTRUCTIONS_PATH
    if not instructions_path.exists():
        return None

    try:
        instructions = instructions_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise OSError(
            f"Could not read workspace instructions file: {instructions_path}"
        ) from exc

    if not instructions:
        return None
    return instructions


def resolve_workspace_path(raw_path: str) -> Path:
    workspace_path = Path(raw_path).expanduser().resolve()
    if not workspace_path.exists():
        raise FileNotFoundError(f"Workspace path not found: {workspace_path}")
    if not workspace_path.is_dir():
        raise NotADirectoryError(f"Workspace path is not a directory: {workspace_path}")
    return workspace_path


def prepare_runtime_workspace(source_workspace_path: Path) -> Path:
    if RUNTIME_WORKSPACE_PATH.exists():
        shutil.rmtree(RUNTIME_WORKSPACE_PATH)

    shutil.copytree(source_workspace_path, RUNTIME_WORKSPACE_PATH)
    return RUNTIME_WORKSPACE_PATH


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


def print_model_summary(model_config: ModelConfig) -> None:
    model_name = model_config.openai_model or model_config.model
    print(f"Using model: {model_config.model} ({model_name})")


def print_user_prompt(user_prompt: str) -> None:
    print("Prompt:")
    print(user_prompt)


def prepare_run(workspace_path_arg: str) -> AgentContext:
    clear_trace()
    source_workspace_path = resolve_workspace_path(workspace_path_arg)
    workspace_path = prepare_runtime_workspace(source_workspace_path)
    model_config = load_model_config(workspace_path)
    print_model_summary(model_config)
    system_prompt = load_system_prompt()
    system_prompt = (
        f"{system_prompt}\n\n"
        "Source workspace root:\n"
        f"{source_workspace_path}\n\n"
        "Runtime workspace root:\n"
        f"{workspace_path}"
    )
    workspace_instructions = load_workspace_instructions(workspace_path)
    if workspace_instructions is not None:
        print("Loading AGENTS.md")
        system_prompt = (
            f"{system_prompt}\n\n"
            "Workspace instructions:\n"
            f"{workspace_instructions}"
        )
    user_prompt = load_user_prompt(workspace_path)
    print_user_prompt(user_prompt)
    trace_request(user_prompt)
    return AgentContext(
        model_config=model_config,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        source_workspace_path=source_workspace_path,
        workspace_path=workspace_path,
    )
