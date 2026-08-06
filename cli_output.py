from pathlib import Path
from typing import Any

from agent_run_result import AgentRunResult


def format_cli_output(
    *,
    result: AgentRunResult,
    trace_path: Path | str,
    summary_path: Path | str | None = None,
) -> dict[str, Any]:
    if not isinstance(result, AgentRunResult):
        raise ValueError("format_cli_output requires an AgentRunResult.")

    output = result.to_dict()

    output["trace_path"] = str(trace_path)
    output["summary_path"] = str(summary_path) if summary_path is not None else None

    return output