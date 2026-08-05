import pytest

from agent_run_result import AgentRunResult
from agent_run_summary import AgentRunSummary, build_agent_run_summary
from agent_stop_reasons import (
    STOP_CODE_MAX_STEPS,
    STOP_MAX_STEPS,
)


def test_run_summary_contains_result_steps_count_and_final_state():
    result = AgentRunResult.completed("Done.")

    summary = AgentRunSummary(
        result=result,
        steps_count=3,
        final_state={
            "report_written": True,
            "findings": [],
        },
    )

    assert summary.result == result
    assert summary.steps_count == 3
    assert summary.final_state == {
        "report_written": True,
        "findings": [],
    }


def test_run_summary_can_be_serialized_to_dict():
    result = AgentRunResult.completed("Done.")

    summary = AgentRunSummary(
        result=result,
        steps_count=1,
        final_state={"report_written": True},
    )

    assert summary.to_dict() == {
        "result": {
            "status": "completed",
            "answer": "Done.",
            "stop_reason": None,
            "stop_reason_code": None,
        },
        "steps_count": 1,
        "final_state": {
            "report_written": True,
        },
    }


def test_run_summary_can_be_restored_from_dict():
    summary = AgentRunSummary.from_dict({
        "result": {
            "status": "stopped",
            "answer": None,
            "stop_reason": STOP_MAX_STEPS,
            "stop_reason_code": STOP_CODE_MAX_STEPS,
        },
        "steps_count": 2,
        "final_state": {
            "report_written": False,
        },
    })

    assert summary.result == AgentRunResult.stopped_with_code(STOP_CODE_MAX_STEPS)
    assert summary.steps_count == 2
    assert summary.final_state == {
        "report_written": False,
    }


def test_run_summary_round_trip():
    original = AgentRunSummary(
        result=AgentRunResult.stopped_with_code(STOP_CODE_MAX_STEPS),
        steps_count=2,
        final_state={"report_written": False},
    )

    restored = AgentRunSummary.from_dict(original.to_dict())

    assert restored == original


def test_run_summary_rejects_negative_steps_count():
    with pytest.raises(ValueError):
        AgentRunSummary(
            result=AgentRunResult.completed("Done."),
            steps_count=-1,
            final_state={},
        )


def test_run_summary_rejects_non_dict_final_state():
    with pytest.raises(ValueError):
        AgentRunSummary(
            result=AgentRunResult.completed("Done."),
            steps_count=1,
            final_state="not a dict",
        )


def test_build_agent_run_summary_uses_last_trace_state_after():
    result = AgentRunResult.completed("Done.")

    trace_steps = [
        {
            "step": 1,
            "state_after": {
                "report_written": False,
            },
        },
        {
            "step": 2,
            "state_after": {
                "report_written": True,
                "report_path": "report.md",
            },
        },
    ]

    summary = build_agent_run_summary(
        result=result,
        trace_steps=trace_steps,
    )

    assert summary.result == result
    assert summary.steps_count == 2
    assert summary.final_state == {
        "report_written": True,
        "report_path": "report.md",
    }


def test_build_agent_run_summary_handles_empty_trace_steps():
    result = AgentRunResult.stopped_with_code(STOP_CODE_MAX_STEPS)

    summary = build_agent_run_summary(
        result=result,
        trace_steps=[],
    )

    assert summary.result == result
    assert summary.steps_count == 0
    assert summary.final_state == {}


def test_build_agent_run_summary_rejects_non_list_trace_steps():
    with pytest.raises(ValueError):
        build_agent_run_summary(
            result=AgentRunResult.completed("Done."),
            trace_steps="not a list",
        )

        