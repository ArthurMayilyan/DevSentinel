import json
import pytest
from pathlib import Path

from run_agent import build_summary_path, run_agent_from_args
from trace import TraceRecorder


def test_build_summary_path_uses_trace_path_stem():
    trace_recorder = TraceRecorder()

    summary_path = build_summary_path(trace_recorder)

    assert summary_path == (
        Path("run_summaries") / f"{trace_recorder.trace_path.stem}_summary.json"
    )


def test_run_agent_from_args_returns_completed_cli_output():
    output = run_agent_from_args([
        "--task",
        "Review the sample project.",
        "--max-steps",
        "20",
    ])

    assert output["status"] == "completed"
    assert output["answer"] == "Review complete. Report written to report.md."
    assert output["stop_reason"] is None
    assert output["stop_reason_code"] is None

    assert output["trace_path"].startswith("traces")
    assert output["summary_path"].startswith("run_summaries")

    assert Path(output["trace_path"]).exists()
    assert Path(output["summary_path"]).exists()


def test_run_agent_from_args_summary_matches_output_result():
    output = run_agent_from_args([
        "--task",
        "Review the sample project.",
        "--max-steps",
        "20",
    ])

    summary_data = json.loads(
        Path(output["summary_path"]).read_text(encoding="utf-8")
    )

    assert summary_data["result"] == {
        "status": output["status"],
        "answer": output["answer"],
        "stop_reason": output["stop_reason"],
        "stop_reason_code": output["stop_reason_code"],
    }

    assert summary_data["steps_count"] > 0
    assert summary_data["final_state"]["report_written"] is True


def test_run_agent_from_args_respects_max_steps_limit():
    output = run_agent_from_args([
        "--task",
        "Review the sample project.",
        "--max-steps",
        "1",
    ])

    assert output["status"] == "stopped"
    assert output["stop_reason_code"] == "max_steps"
    assert output["answer"] is None

def test_run_agent_from_args_accepts_explicit_demo_llm():
    output = run_agent_from_args([
        "--task",
        "Review the sample project.",
        "--llm",
        "demo",
        "--max-steps",
        "20",
    ])

    assert output["status"] == "completed"
    assert output["answer"] == "Review complete. Report written to report.md."    

def test_main_prints_json_error_and_exits(monkeypatch, capsys):
    import run_agent

    def fake_run_agent_from_args():
        raise ValueError("Something went wrong.")

    monkeypatch.setattr(
        run_agent,
        "run_agent_from_args",
        fake_run_agent_from_args,
    )

    with pytest.raises(SystemExit) as exc_info:
        run_agent.main()

    assert exc_info.value.code == 1

    captured = capsys.readouterr()

    assert json.loads(captured.out) == {
        "status": "error",
        "error": "Something went wrong.",
    }

def test_main_prints_json_interrupted_output_and_exits(monkeypatch, capsys):
    import run_agent

    def fake_run_agent_from_args():
        raise KeyboardInterrupt()

    monkeypatch.setattr(
        run_agent,
        "run_agent_from_args",
        fake_run_agent_from_args,
    )

    with pytest.raises(SystemExit) as exc_info:
        run_agent.main()

    assert exc_info.value.code == 130

    captured = capsys.readouterr()

    assert json.loads(captured.out) == {
        "status": "interrupted",
        "error": "Interrupted by user.",
    }

            