import json

from agent_run_result import AgentRunResult
from agent_run_summary import build_agent_run_summary
from trace import TraceRecorder


def test_trace_recorder_writes_run_summary_file():
    trace_recorder = TraceRecorder()

    trace_recorder.record({
        "step": 1,
        "state_after": {
            "report_written": False,
        },
    })

    trace_recorder.record({
        "step": 2,
        "state_after": {
            "report_written": True,
            "report_path": "report.md",
        },
    })

    summary = build_agent_run_summary(
        result=AgentRunResult.completed("Done."),
        trace_steps=[
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
        ],
    )

    summary_path = trace_recorder.write_summary(summary)

    assert summary_path.exists()
    assert summary_path.parent.name == "run_summaries"
    assert summary_path.name.endswith("_summary.json")

    data = json.loads(summary_path.read_text(encoding="utf-8"))

    assert data == {
        "result": {
            "status": "completed",
            "answer": "Done.",
            "stop_reason": None,
            "stop_reason_code": None,
        },
        "steps_count": 2,
        "final_state": {
            "report_written": True,
            "report_path": "report.md",
        },
    }


def test_trace_recorder_summary_file_uses_trace_file_stem():
    trace_recorder = TraceRecorder()

    summary = build_agent_run_summary(
        result=AgentRunResult.completed("Done."),
        trace_steps=[],
    )

    summary_path = trace_recorder.write_summary(summary)

    assert summary_path.stem == f"{trace_recorder.trace_path.stem}_summary"

def test_trace_recorder_reads_recorded_steps():
    trace_recorder = TraceRecorder()

    first_step = {
        "step": 1,
        "state_after": {
            "report_written": False,
        },
    }

    second_step = {
        "step": 2,
        "state_after": {
            "report_written": True,
            "report_path": "report.md",
        },
    }

    trace_recorder.record(first_step)
    trace_recorder.record(second_step)

    assert trace_recorder.read_steps() == [
        first_step,
        second_step,
    ]


def test_trace_recorder_read_steps_returns_empty_list_for_new_trace():
    trace_recorder = TraceRecorder()

    assert trace_recorder.read_steps() == []

        