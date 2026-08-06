from pathlib import Path
from typing import Any

from agent_run_result import AgentRunResult


def format_cli_output(
    *,
    result: AgentRunResult,
    trace_path: Path | str,
    summary_path: Path | str | None = None,
    run_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(result, AgentRunResult):
        raise ValueError("result must be an AgentRunResult.")

    if run_metadata is not None and not isinstance(run_metadata, dict):
        raise ValueError("run_metadata must be a dictionary or None.")

    output = result.to_dict()
    output["trace_path"] = str(trace_path)
    output["summary_path"] = str(summary_path) if summary_path is not None else None

    if run_metadata is not None:
        output["run"] = run_metadata

    return output


def format_task_preview_output(*, task: str) -> dict[str, Any]:
    return {
        "status": "task_preview",
        "task": task,
    }

