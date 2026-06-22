# Minixx

Minixx is a didactic Python project for studying how to build a simple code agent.

## Goal

Create a small, clear, and easy-to-understand foundation.

## Run

```bash
python3 main.py
```

## Backend

Minixx currently uses Codex as its backend.

The project runs Codex in headless mode through the local CLI, so these requirements matter:

- the Codex desktop app or CLI must be installed
- the `codex` executable must be available in your shell `PATH`
- the current config expects the `codex` command name directly
- the backend runs in `read-only` sandbox mode

The backend configuration lives in:

```text
./config/config.json
```

The current settings include:

- `codex_command`
- `working_directory`
- `timeout_seconds`

If `python3 main.py` fails with a message like `Codex CLI not found in PATH`, the most likely issue is that the local `codex` executable is not available in your shell environment.

## Current Design

- Codex is the current backend
- a config file
- a configurable Codex command
- a configurable working directory
- a separate system prompt file
- a separate user prompt file
- a minimal ReAct-style loop
- direct output to the terminal

## Files

- `config/config.json` stores runtime settings for the Codex CLI backend.
- `config/system_prompt.txt` stores the agent's behavior instructions.
- `config/prompt.txt` stores the current user prompt.
- `inputs.py` loads the configuration and prompt files.
- `llms.py` handles the headless Codex request.
- `protocol.py` parses and repairs model responses.
- `tools.py` executes agent tools.
- `logs.py` writes request and response traces to `agent.log`.
- `main.py` runs the agent loop.

## Current Tools

- `list_files`
- `read_file`
- `find_text`
- `finish`

## Current Protocol

The model must respond with:

- `Thought`
- `Action`
- `Action Input`

The current system prompt allows these actions:

- `list_files`
- `read_file`
- `find_text`
- `finish`

`find_text` expects this input format:

```text
search text | /path/to/directory
```

## Test Workspace

The default backend working directory is:

```text
./test_workspace
```

This keeps agent runs focused on a small controlled set of files during testing.
