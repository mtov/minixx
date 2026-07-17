from __future__ import annotations

from time import perf_counter

from .cli_output import (
    format_failure_message,
    print_elapsed_time,
    print_final_result,
    print_iteration_action,
    print_total_tokens,
)
from .context import AgentConfig, LoopResult, Memory, ToolRequest
from .finish_handler import handle_finish
from .inputs import parse_args, prepare_run, reset_runtime_workspace
from .models import call_model
from .protocol import looks_like_patch, parse_response, repair_response
from .test_failures import summarize_test_failure_output
from .tools import run_tool
from .traces import trace_validation_error

INVALID_FINISH_MESSAGE = (
    "Finish output must contain only a unified diff patch. "
    "Do not end the run yet; inspect any remaining files you need and then return the patch."
)
MAX_ITERATIONS = 15

def get_next_tool_request(config: AgentConfig, memory: Memory) -> ToolRequest:
    user_message = (
        "User task:\n"
        f"{config.user_prompt}\n\n"
        "Agent history:\n"
        f"{memory.to_text()}"
    )
    model_response = call_model(config, user_message)

    try:
        return parse_response(model_response.content)
    except ValueError as exc:
        trace_validation_error(str(exc), model_response.content)
        return repair_response(config, user_message, str(exc))


def handle_post_apply_test_failure(
    config: AgentConfig,
    memory: Memory,
    iteration: int,
    tool_request: ToolRequest,
    test_output: str | None,
) -> None:
    print_iteration_action(iteration, tool_request)
    reset_runtime_workspace(config)
    memory.append(
        iteration,
        tool_request,
        summarize_test_failure_output(test_output or ""),
    )


def handle_finish_action(
    config: AgentConfig,
    memory: Memory,
    iteration: int,
    tool_request: ToolRequest,
) -> str | None:
    if not looks_like_patch(tool_request.args):
        print_iteration_action(iteration, tool_request)
        memory.append(iteration, tool_request, INVALID_FINISH_MESSAGE)
        return None

    finish_result = handle_finish(config, tool_request)
    if finish_result.status == "post_apply_tests_failed":
        handle_post_apply_test_failure(
            config,
            memory,
            iteration,
            tool_request,
            finish_result.test_output,
        )
        return None

    tool_request = finish_result.request
    print_iteration_action(iteration, tool_request)
    return tool_request.args


def agentic_loop(config: AgentConfig) -> LoopResult:
    memory = Memory()

    for iteration in range(1, MAX_ITERATIONS + 1):
        tool_request = get_next_tool_request(config, memory)

        if tool_request.name == "finish":
            finish_output = handle_finish_action(config, memory, iteration, tool_request)
            if finish_output is None:
                continue
            return LoopResult.success(finish_output)

        print_iteration_action(iteration, tool_request)

        tool_result = run_tool(tool_request, config)
        memory.append(iteration, tool_request, tool_result)

    return LoopResult.max_iterations_reached()


def main() -> int:
    args = parse_args()
    start_time = perf_counter()

    try:
        config = prepare_run(args.workspace_path)
        loop_result = agentic_loop(config)
    except Exception as exc:  # noqa: BLE001
        print_total_tokens()
        print_elapsed_time(perf_counter() - start_time)
        print(format_failure_message(exc))
        return 1

    if loop_result.status != "success":
        print_total_tokens()
        print_elapsed_time(perf_counter() - start_time)
        print(format_failure_message(ValueError(loop_result.error or "Unknown error.")))
        return 1

    print_total_tokens()
    print_elapsed_time(perf_counter() - start_time)
    print_final_result(config, loop_result.output or "")
    return 0
