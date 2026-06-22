# Minixx

Minixx is a didactic Python project for studying how to build a simple code agent.

## Goal

Create a small, clear, and easy-to-understand foundation.

## Initial structure

This repository starts with only the minimum configuration files.

## First step

The project now includes a minimal headless Codex example.

```bash
python3 main.py
```

The current version uses:

- a config file
- a configurable Codex command
- a configurable working directory
- a separate system prompt file
- a separate user prompt file
- a minimal ReAct-style loop
- direct output to the terminal

## Files

- `config.json` stores runtime settings for the Codex CLI backend.
- `system_prompt.txt` stores the agent's behavior instructions.
- `prompt.txt` stores the current user prompt.
- `inputs.py` loads the configuration and prompt files.
- `llms.py` handles the headless Codex request.
- `main.py` runs the agent loop.

## Current agent behavior

- The model must respond with `Thought`, `Action`, and `Action Input`.
- The supported actions are `read_file` and `finish`.
- The loop reads a local file when the model returns `Action: read_file`.
- The loop stops when the model returns `Action: finish`.
