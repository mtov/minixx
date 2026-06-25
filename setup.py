from __future__ import annotations

from context import AgentContext
from inputs import load_llm_config, load_system_prompt, load_user_prompt, resolve_workspace_path
from logs import clear_log, log_request


def prepare_run(workspace_path_arg: str) -> AgentContext:
    clear_log()
    workspace_path = resolve_workspace_path(workspace_path_arg)
    llm_config = load_llm_config()
    llm_config["working_directory"] = str(workspace_path)
    system_prompt = load_system_prompt()
    user_prompt = load_user_prompt(workspace_path)
    log_request(user_prompt)
    return AgentContext(llm_config=llm_config, system_prompt=system_prompt, user_prompt=user_prompt, workspace_path=workspace_path)
