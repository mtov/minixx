# Minixx

<p align="center">
  <img src="minixx.png" alt="Minixx logo" width="128">
</p>

Minixx is a didactic Python project for studying how to build a simple code agent.
It is an ongoing research project developed by [ASERG](https://aserg.labsoft.dcc.ufmg.br/) at DCC/UFMG.

## Design Principles

- Minixx is intended for learning, experimentation, and research.
- Minixx favors a simple architecture that is easy to understand and extend.
- Minixx currently uses OpenAI's Codex as its backend, but the design can be extended to support other models, including Small Language Models.

## Run

Minixx runs against a workspace passed on the command line.
Run the command from the project root.

Each workspace should contain:

- a `prompt.txt` file
- the project files and tests that the agent is allowed to inspect

It may also contain:

- an `AGENTS.md` file with workspace-specific instructions appended to the system prompt

### Example

`prompt.txt`:

```text
Rename the function old_name to new_name in all relevant files and return a unified diff patch.
```

Run command:

```bash
python3 run_minixx.py ./test_workspace/test-rename-refactoring
```

The selected workspace path becomes the backend working directory for the run.
Tool paths are also restricted to that workspace.
If a run finishes with a unified diff patch, Minixx also saves that patch to `patch.txt` inside the selected workspace.


## Demo Workspaces

Discovery:
- `./test_workspace/test-find-secret-key`: file discovery and secret lookup
- `./test_workspace/test-find-symbol`: symbol search and precise location reporting

Refactoring:
- `./test_workspace/test-rename-refactoring`: cross-file refactoring and patch generation

Bug Fixing:
- `./test_workspace/test-fix-failing-test`: test execution, bug diagnosis, and patch generation
- `./test_workspace/test-fix-misleading-bug`: cross-file bug fixing with a misleading first suspicion

Program Creation:
- `./test_workspace/test-create-program`: program creation and test generation as a unified diff patch
- `./test_workspace/test-build-stopwatch`: create a small browser-based JavaScript stopwatch app from prompt only

## Backend and Model

Minixx currently uses OpenAI's Codex as its default backend layer in read-only mode, acting as a bridge to the underlying model.
It can also be configured to use other backend integrations, such as local models served by Ollama.

```mermaid
flowchart LR
    Minixx --> Codex["OpenAI's Codex"]
    Codex --> GPT["GPT Model"]
    Minixx --> Ollama["Ollama backend"]
    Ollama --> Other["Other LLMs"]
```

Requirements:

- the Codex desktop app or CLI must be installed
- the `codex` executable must be available in your shell `PATH`
- the backend configuration lives in `./config/config.json`
- `pytest` must be available in the Python environment used to run Minixx

If the run command fails with a message like `Codex CLI not found in PATH`, the most likely issue is that the local `codex` executable is not available in your shell environment.

## How One Run Works

1. Minixx loads the backend configuration, the global system prompt, and optional workspace instructions from `AGENTS.md`.
2. Minixx loads `prompt.txt` from the selected workspace.
3. Minixx sends the request to the configured backend.
4. Optional extension points can add a plan or review a final answer.
5. The agent chooses a tool, receives the tool result, and updates its history.
6. The loop ends when the agent returns a final `finish` output.

```mermaid
sequenceDiagram
    participant Minixx
    participant BackendLayer as Backend Layer
    participant LLM
    participant Workspace

    Minixx->>Workspace: load AGENTS.md, prompt.txt, and project files
    Minixx->>BackendLayer: request next action
    BackendLayer->>LLM: send prompt
    LLM-->>BackendLayer: generate response
    BackendLayer-->>Minixx: Thought / Action / Action Input / Action Description
    Minixx->>Minixx: optional planning and finish review
    Minixx->>Workspace: run tool
    Workspace-->>Minixx: tool result
    Minixx->>BackendLayer: send updated request
    BackendLayer->>LLM: send updated prompt
    LLM-->>BackendLayer: generate finish response
    BackendLayer-->>Minixx: finish
```

## High-Level Architecture

```mermaid
flowchart TD
    A["Config"]
    B["Core"]
    C["Extension Points"]
    D["Shared Types"]
    E["Tools"]
    F["Backends"]
    G["Logging"]
    H["Safety Guards"]

    B --> A
    B --> C
    B --> D
    B --> E
    B --> F
    B --> G
    E --> H
```

## Core Structure

```mermaid
flowchart TD
    A["agentic_loop.py"]
    B["inputs.py"]
    C["llms.py"]
    D["protocol.py"]
    E["finish_handler.py"]
    F["patches.py"]
    G["history_manager.py"]
    H["planner.py"]
    I["finish_reviewer.py"]

    A --> B
    A --> C
    A --> D
    A --> E
    A --> F
    A --> G
    A --> H
    E --> I
```

Configuration:
- `config/config.json` stores backend settings.
- `config/system_prompt.txt` stores the agent's behavior instructions.

Core:
- `agentic_loop.py` runs the agent loop.
- `inputs.py` parses arguments and prepares the run context.
- `llms.py` selects the backend and performs the LLM request.
- `protocol.py` parses and repairs model responses.
- `finish_handler.py` validates, repairs, reviews, and persists final `finish` outputs.
- `tools.py` executes agent tools.
- `patches.py` saves generated unified diff patches to `patch.txt`.
- `traces.py` writes execution traces to `agent_trace.log`.

Extension Points:
- `planner.py` defines the optional planning step.
- `finish_reviewer.py` defines the optional final review step before accepting `finish`.
- `history_manager.py` encapsulates history creation, update, and serialization.

Shared Types and Safety:
- `context.py` defines `AgentContext` and `AgentResponse`.
- `guards.py` validates and resolves tool paths inside the workspace.

## Data Classes

- `LLMConfig` stores the typed backend configuration used by one run.
- `AgentContext` stores the configuration and stable inputs for one agent run.
- `AgentResponse` stores one parsed model decision: `thought`, `action`, `action_input`, and `action_description`.
- `AgentHistory` stores the accumulated iteration history used in the ReAct loop.

## Tools

- `list_files`
- `read_file`
- `find_text`
- `run_tests`
- `finish`

Minixx can inspect files, search for text, reason about changes, and propose patches.
It does not apply edits directly.
Tool file and directory paths must stay inside the selected workspace.

The model responds with `Thought`, `Action`, and `Action Input`.
It also returns `Action Description`, a short didactic explanation of the current step and its immediate purpose.

`find_text` expects this input format:

```text
search text | /path/to/directory
```

`run_tests` runs the workspace test suite using a fixed `pytest` command.

When a task requires a code change, the agent is expected to return a unified diff patch in the final `finish` response.
The patch should use real unified diff hunk headers with line ranges, such as `@@ -1 +1 @@` or `@@ -0,0 +1,10 @@`.

## Patch Workflow

When a run finishes with a unified diff patch, Minixx saves the same output to `patch.txt` in the selected workspace.

To validate the saved patch manually, run:

```bash
cd ./test_workspace/test-rename-refactoring
git apply --check patch.txt
```

To apply it manually after that, run:

```bash
git apply patch.txt
```

## Tracing

Minixx writes execution traces to `agent_trace.log`.
Because the project is didactic, users are encouraged to inspect this trace to better understand how the agent reasons, chooses actions, and reacts to tool results.

## Security

Minixx is designed to run against a selected workspace.
Tool paths are validated by `guards.py`, which prevents file and directory access outside that workspace.
The `run_tests` tool uses a fixed test command instead of accepting an arbitrary shell command.
This is a simple safety mechanism for local agent experiments, not a complete sandbox.

## Extension Points

Minixx now includes three small extension points for agent features:

- `planner.py`
- `finish_reviewer.py`
- `history_manager.py`

The first versions are intentionally minimal.
`planner.py` and `finish_reviewer.py` currently return `None`, which means no extra behavior is added yet.
They exist as simple places where new features can be plugged in without changing the overall loop structure.

## What to Inspect First

- Start with `agentic_loop.py` to understand the main loop.
- Then read `context.py` to see the core data structures.
- Then read `planner.py`, `finish_reviewer.py`, and `history_manager.py` to see the new extension points.
- Then read `finish_handler.py` to see how final `finish` responses are handled.
- Then read `llms.py` to see how the backend request is made.
- Then read `patches.py` to see how final patches are persisted.
- Then read `tools.py` to understand what actions the agent can perform.

## Current Limitations

- Minixx runs in read-only patch mode and does not apply edits directly.
- The toolset is intentionally small.
- Output validation is simple and protocol-driven.
- File access is restricted to the selected workspace.
