import json
from pathlib import Path

from agent import Agent
from cli_config import build_agent_config_from_args, build_arg_parser
from cli_output import format_cli_output
from demo_llm import DemoCodeReviewLLM
from trace import TraceRecorder


def build_summary_path(trace_recorder: TraceRecorder) -> Path:
    return Path("run_summaries") / f"{trace_recorder.trace_path.stem}_summary.json"


def run_agent_from_args(argv: list[str] | None = None) -> dict:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    config = build_agent_config_from_args(args)
    trace_recorder = TraceRecorder()

    agent = Agent(
        llm=DemoCodeReviewLLM(),
        trace_recorder=trace_recorder,
        config=config,
    )

    result = agent.run_with_result(args.task)

    return format_cli_output(
        result=result,
        trace_path=trace_recorder.trace_path,
        summary_path=build_summary_path(trace_recorder),
    )


def main() -> None:
    output = run_agent_from_args()
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

    