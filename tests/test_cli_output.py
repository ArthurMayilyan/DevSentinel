import pytest

from agent_run_result import AgentRunResult
from agent_stop_reasons import (
    STOP_CODE_MAX_STEPS,
    STOP_MAX_STEPS,
)
from cli_output import format_cli_output


def test_format_cli_output_for_completed_result():
    result = AgentRunResult.completed("Done.")

    output = format_cli_output(
        result=result,
        trace_path="traces/trace_1.json",
        summary_path="run_summaries/trace_1_summary.json",
    )

    assert output == {
        "status": "completed",
        "answer": "Done.",
        "stop_reason": None,
        "stop_reason_code": None,
        "trace_path": "traces/trace_1.json",
        "summary_path": "run_summaries/trace_1_summary.json",
    }


def test_format_cli_output_for_stopped_result():
    result = AgentRunResult.stopped_with_code(STOP_CODE_MAX_STEPS)

    output = format_cli_output(
        result=result,
        trace_path="traces/trace_1.json",
        summary_path="run_summaries/trace_1_summary.json",
    )

    assert output == {
        "status": "stopped",
        "answer": None,
        "stop_reason": STOP_MAX_STEPS,
        "stop_reason_code": STOP_CODE_MAX_STEPS,
        "trace_path": "traces/trace_1.json",
        "summary_path": "run_summaries/trace_1_summary.json",
    }


def test_format_cli_output_accepts_missing_summary_path():
    result = AgentRunResult.completed("Done.")

    output = format_cli_output(
        result=result,
        trace_path="traces/trace_1.json",
        summary_path=None,
    )

    assert output["summary_path"] is None


def test_format_cli_output_rejects_non_result_input():
    with pytest.raises(ValueError):
        format_cli_output(
            result="not a result",
            trace_path="traces/trace_1.json",
        )