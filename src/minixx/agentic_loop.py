from __future__ import annotations

import re
from pathlib import Path

from .cli_output import format_failure_message, print_final_result, print_iteration_action, print_total_tokens
from .context import AgentContext, AgentHistory, AgentResponse
from .finish_handler import PostApplyTestsFailedError, handle_finish
from .inputs import parse_args, prepare_run, prepare_runtime_workspace
from .models import call_model
from .protocol import looks_like_patch, parse_response, repair_response
from .traces import trace_validation_error
from .tools import run_tool

INVALID_FINISH_MESSAGE = (
    "Finish output must contain only a unified diff patch. "
    "Do not end the run yet; inspect any remaining files you need and then return the patch."
)
FAILED_TEST_LINE = re.compile(r"^FAILED\s+(.+?)\s+-\s+(.+)$")
ASSERT_EQUALS_LINE = re.compile(r"^E\s+AssertionError:\s+assert\s+(.+?)\s+==\s+(.+)$")
FAILED_TEST_HEADER = re.compile(r"^_+\s+([A-Za-z0-9_]+)\s+_+$")

def get_agent_response(context: AgentContext, agent_history: str) -> AgentResponse:
    user_message = f"""User task:
{context.user_prompt}

Agent history:
{agent_history}"""
    model_response = call_model(context, user_message)

    try:
        return parse_response(model_response.content)
    except ValueError as exc:
        trace_validation_error(str(exc), model_response.content)
        return repair_response(context, user_message, str(exc))


def reset_runtime_workspace(context: AgentContext) -> None:
    context.workspace_path = prepare_runtime_workspace(context.source_workspace_path)
    context.post_apply_tests_passed = False


def summarize_test_failure_output(test_output: str) -> str:
    summary_lines = [
        "Post-apply tests failed. The runtime workspace has been reset to the original source state.",
        "Use the failed test details below to produce a different patch.",
    ]
    failed_cases: list[str] = []
    current_test: str | None = None

    for raw_line in test_output.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        header_match = FAILED_TEST_HEADER.match(line)
        if header_match:
            current_test = header_match.group(1)
            continue

        failed_match = FAILED_TEST_LINE.match(line)
        if failed_match:
            current_test = failed_match.group(1)
            failed_cases.append(f"- {current_test}: {failed_match.group(2)}")
            continue

        if current_test is None:
            continue

        assertion_match = ASSERT_EQUALS_LINE.match(line)
        if assertion_match:
            got_value = assertion_match.group(1)
            expected_value = assertion_match.group(2)
            failed_cases.append(f"- {current_test}: expected {expected_value}, got {got_value}")
            current_test = None

    if failed_cases:
        summary_lines.extend(failed_cases)
    else:
        summary_lines.append(test_output.strip())

    return "\n".join(summary_lines)


def agentic_loop(context: AgentContext) -> str:
    max_iterations = 15
    agent_history = AgentHistory()

    for iteration in range(1, max_iterations + 1):
        agent_response = get_agent_response(context, agent_history.to_text())

        if agent_response.action == "finish":
            if not looks_like_patch(agent_response.action_input):
                print_iteration_action(iteration, agent_response)
                agent_history.append(iteration, agent_response, INVALID_FINISH_MESSAGE)
                continue
            try:
                agent_response = handle_finish(context, agent_response)
            except PostApplyTestsFailedError as exc:
                print_iteration_action(iteration, agent_response)
                reset_runtime_workspace(context)
                agent_history.append(
                    iteration,
                    agent_response,
                    summarize_test_failure_output(exc.test_output),
                )
                continue
            print_iteration_action(iteration, agent_response)
            return agent_response.action_input

        print_iteration_action(iteration, agent_response)

        tool_result = run_tool(agent_response, context.workspace_path)
        agent_history.append(iteration, agent_response, tool_result)

    raise ValueError("Agent stopped after reaching the maximum number of steps.")


def main() -> int:
    args = parse_args()

    try:
        context = prepare_run(args.workspace_path)
        result = agentic_loop(context)
    except Exception as exc:  # noqa: BLE001
        print_total_tokens()
        print(format_failure_message(exc))
        return 1

    print_total_tokens()
    print_final_result(context, result)
    return 0
