import json
from pathlib import Path

from devsentinel.core.agent import Agent
from devsentinel.cli.cli_config import build_agent_config_from_args, build_arg_parser
from devsentinel.cli.cli_output import format_cli_output, format_task_preview_output
from devsentinel.core.trace import TraceRecorder
from devsentinel.cli.cli_llm import build_llm_from_args
from devsentinel.cli.cli_task import build_task_from_args
from devsentinel.cli.cli_run_metadata import build_run_metadata
from devsentinel.rag.rag_loader import load_rag_store_from_path
from devsentinel.cli.cli_project_scope import build_cli_project_scope


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
    project_scope = build_cli_project_scope(
        project_root=args.project_root,
        path=args.path,
        launch_dir=Path.cwd(),
    )
    run_metadata = build_run_metadata(
        args=args,
        task=task,
        config=config,
    )
    run_metadata["project_root"] = str(project_scope.root)

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
        project_scope=project_scope,
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

    