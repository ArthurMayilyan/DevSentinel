from argparse import Namespace
from pathlib import Path
from typing import Any

from agent import Agent
from agent_config import AgentConfig
from cli_config import build_agent_config_from_args
from cli_llm import build_llm_from_args
from cli_output import format_cli_output
from cli_run_metadata import build_run_metadata
from cli_task import build_task_from_args
from rag_loader import load_rag_store_from_path
from task_presets import DEFAULT_CODE_REVIEW_MAX_FINDINGS
from trace import TraceRecorder


SUPPORTED_CODE_REVIEW_LLMS = {
    "demo",
    "openai",
}


def build_summary_path(
    trace_recorder: TraceRecorder,
) -> Path:
    return Path("run_summaries") / f"{trace_recorder.trace_path.stem}_summary.json"


def build_code_review_args(
    *,
    task: str = "",
    preset: str = "",
    path: str = "",
    knowledge_path: str = "",
    llm_name: str = "demo",
    model: str = "gpt-5",
    max_steps: int | None = None,
    max_findings: int = DEFAULT_CODE_REVIEW_MAX_FINDINGS,
    max_rejected_final_answers: int = AgentConfig().max_rejected_final_answers,
    max_rejected_tool_calls: int = AgentConfig().max_rejected_tool_calls,
    max_invalid_llm_outputs: int = AgentConfig().max_invalid_llm_outputs,
    max_output_tokens: int | None = None,
    request_timeout_seconds: float | None = None,
) -> Namespace:
    return Namespace(
        task=task or None,
        preset=preset or None,
        path=path or None,
        knowledge_path=knowledge_path or None,
        max_findings=max_findings,
        print_task=False,
        max_steps=max_steps,
        max_rejected_final_answers=max_rejected_final_answers,
        max_rejected_tool_calls=max_rejected_tool_calls,
        max_invalid_llm_outputs=max_invalid_llm_outputs,
        llm=llm_name,
        model=model,
        max_output_tokens=max_output_tokens,
        request_timeout_seconds=request_timeout_seconds,
    )


def validate_code_review_llm(
    llm_name: str,
) -> None:
    if llm_name not in SUPPORTED_CODE_REVIEW_LLMS:
        supported = ", ".join(
            sorted(
                SUPPORTED_CODE_REVIEW_LLMS,
            )
        )

        raise ValueError(
            f"unsupported code_review LLM: {llm_name}. Supported LLMs: {supported}"
        )


def run_code_review_agent(
    *,
    task: str = "",
    preset: str = "",
    path: str = "",
    knowledge_path: str = "",
    llm_name: str = "demo",
    model: str = "gpt-5",
    max_steps: int | None = None,
    max_findings: int = DEFAULT_CODE_REVIEW_MAX_FINDINGS,
    max_rejected_final_answers: int = AgentConfig().max_rejected_final_answers,
    max_rejected_tool_calls: int = AgentConfig().max_rejected_tool_calls,
    max_invalid_llm_outputs: int = AgentConfig().max_invalid_llm_outputs,
    max_output_tokens: int | None = None,
    request_timeout_seconds: float | None = None,
    openai_client_class: Any = None,
) -> dict[str, Any]:
    validate_code_review_llm(
        llm_name,
    )

    args = build_code_review_args(
        task=task,
        preset=preset,
        path=path,
        knowledge_path=knowledge_path,
        llm_name=llm_name,
        model=model,
        max_steps=max_steps,
        max_findings=max_findings,
        max_rejected_final_answers=max_rejected_final_answers,
        max_rejected_tool_calls=max_rejected_tool_calls,
        max_invalid_llm_outputs=max_invalid_llm_outputs,
        max_output_tokens=max_output_tokens,
        request_timeout_seconds=request_timeout_seconds,
    )

    resolved_task = build_task_from_args(
        args,
    )

    config = build_agent_config_from_args(
        args,
    )

    run_metadata = build_run_metadata(
        args=args,
        task=resolved_task,
        config=config,
    )

    rag_store = None

    if args.knowledge_path:
        rag_store = load_rag_store_from_path(
            path=args.knowledge_path,
        )

    trace_recorder = TraceRecorder()

    llm = build_llm_from_args(
        args,
        openai_client_class=openai_client_class,
    )

    agent = Agent(
        llm=llm,
        config=config,
        trace_recorder=trace_recorder,
        run_metadata=run_metadata,
        rag_store=rag_store,
    )

    result = agent.run_with_result(
        resolved_task,
    )

    return format_cli_output(
        result=result,
        trace_path=trace_recorder.trace_path,
        summary_path=build_summary_path(
            trace_recorder,
        ),
        run_metadata=run_metadata,
    )


def format_code_review_markdown_report(
    output: dict[str, Any],
) -> str:
    lines = [
        "# Code Review Agent Run Report",
        "",
        "## Result",
        "",
        f"Status: `{output.get('status')}`",
        f"Answer: `{output.get('answer')}`",
        f"Stop reason code: `{output.get('stop_reason_code')}`",
        "",
        "## Run",
        "",
    ]

    run_metadata = output.get(
        "run",
        {},
    )

    if isinstance(run_metadata, dict):
        for key in sorted(
            run_metadata,
        ):
            lines.append(
                f"- {key}: `{run_metadata[key]}`"
            )

    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"Trace path: `{output.get('trace_path')}`",
            f"Summary path: `{output.get('summary_path')}`",
        ]
    )

    return "\n".join(
        lines,
    )