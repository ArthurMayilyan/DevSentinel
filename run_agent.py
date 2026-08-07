import json
from pathlib import Path

from agent import Agent
from cli_config import build_agent_config_from_args, build_arg_parser
from cli_output import format_cli_output, format_task_preview_output
from trace import TraceRecorder
from cli_llm import build_llm_from_args
from cli_task import build_task_from_args
from cli_run_metadata import build_run_metadata
from rag_loader import load_rag_store_from_path


def build_summary_path(trace_recorder: TraceRecorder) -> Path:
    return Path("run_summaries") / f"{trace_recorder.trace_path.stem}_summary.json"


def run_agent_from_args(
    argv: list[str] | None = None,
    *,
    openai_client_class=None,
) -> dict:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    task = build_task_from_args(args)

    if args.print_task:
        return format_task_preview_output(task=task)

    config = build_agent_config_from_args(args)
    run_metadata = build_run_metadata(
        args=args,
        task=task,
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

    result = agent.run_with_result(task)

    return format_cli_output(
        result=result,
        trace_path=trace_recorder.trace_path,
        summary_path=build_summary_path(trace_recorder),
        run_metadata=run_metadata,
    )


def main() -> None:
    try:
        output = run_agent_from_args()
    except KeyboardInterrupt:
        error_output = {
            "status": "interrupted",
            "error": "Interrupted by user.",
        }

        print(json.dumps(error_output, indent=2))
        raise SystemExit(130)
    except Exception as exc:
        error_output = {
            "status": "error",
            "error": str(exc),
        }

        print(json.dumps(error_output, indent=2))
        raise SystemExit(1) from exc

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

    