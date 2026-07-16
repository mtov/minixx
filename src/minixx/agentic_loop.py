from __future__ import annotations

from pathlib import Path
from time import perf_counter

from .cli_output import (
    print_elapsed_time,
    format_failure_message,
    print_final_result,
    print_iteration_action,
    print_total_tokens,
)
from .context import AgentContext, AgentHistory, AgentResponse, LoopResult
from .finish_handler import handle_finish
from .inputs import parse_args, prepare_run, reset_runtime_workspace
from .models import call_model
from .protocol import looks_like_patch, parse_response, repair_response
from .test_failures import summarize_test_failure_output
from .traces import trace_validation_error
from .tools import run_tool

INVALID_FINISH_MESSAGE = (
    "Finish output must contain only a unified diff patch. "
    "Do not end the run yet; inspect any remaining files you need and then return the patch."
)
MAX_ITERATIONS = 15

def get_agent_response(context: AgentContext, history: AgentHistory) -> AgentResponse:
    user_message = (
        "User task:\n"
        f"{context.user_prompt}\n\n"
        "Agent history:\n"
        f"{history.to_text()}"
    )
    model_response = call_model(context, user_message)

    try:
        return parse_response(model_response.content)
    except ValueError as exc:
        trace_validation_error(str(exc), model_response.content)
        return repair_response(context, user_message, str(exc))


def handle_post_apply_test_failure(
    context: AgentContext,
    history: AgentHistory,
    iteration: int,
    agent_response: AgentResponse,
    test_output: str | None,
) -> None:
    print_iteration_action(iteration, agent_response)
    reset_runtime_workspace(context)
    history.append(
        iteration,
        agent_response,
        summarize_test_failure_output(test_output or ""),
    )


def handle_finish_action(
    context: AgentContext,
    history: AgentHistory,
    iteration: int,
    agent_response: AgentResponse,
) -> str | None:
    if not looks_like_patch(agent_response.action_input):
        print_iteration_action(iteration, agent_response)
        history.append(iteration, agent_response, INVALID_FINISH_MESSAGE)
        return None

    finish_result = handle_finish(context, agent_response)
    if finish_result.status == "post_apply_tests_failed":
        handle_post_apply_test_failure(
            context,
            history,
            iteration,
            agent_response,
            finish_result.test_output,
        )
        return None

    finalized_response = finish_result.agent_response
    print_iteration_action(iteration, finalized_response)
    return finalized_response.action_input


def agentic_loop(context: AgentContext) -> LoopResult:
    history = AgentHistory()

    for iteration in range(1, MAX_ITERATIONS + 1):
        agent_response = get_agent_response(context, history)

        if agent_response.action == "finish":
            finish_output = handle_finish_action(
                context,
                history,
                iteration,
                agent_response,
            )
            if finish_output is None:
                continue
            return LoopResult.success(finish_output)

        print_iteration_action(iteration, agent_response)

        tool_result = run_tool(agent_response, context)
        history.append(iteration, agent_response, tool_result)

    return LoopResult.max_iterations_reached()


def main() -> int:
    args = parse_args()
    start_time = perf_counter()

    try:
        context = prepare_run(args.workspace_path)
        loop_result = agentic_loop(context)
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
    print_final_result(context, loop_result.output or "")
    return 0
