import pytest
import json
from pathlib import Path

from agent import Agent
from agent_config import AgentConfig
from agent_run_result import AgentRunResult
from agent_stop_reasons import (
    STOP_CODE_INVALID_LLM_OUTPUTS,
    STOP_CODE_MAX_STEPS,
    STOP_INVALID_LLM_OUTPUTS,
    STOP_MAX_STEPS,
)
from trace import TraceRecorder


class AlwaysInvalidLLMOutput:
    def complete(self, messages, state=None):
        return "not a json object"


class NeverCompletesLLM:
    def complete(self, messages, state=None):
        return {
            "type": "tool_call",
            "tool": "list_files",
            "arguments": {
                "path": "./sample_project",
            },
        }


class CompleteReviewLLM:
    def complete(self, messages, state=None):
        if not state.discovered_files:
            return {
                "type": "tool_call",
                "tool": "list_files",
                "arguments": {
                    "path": "./sample_project",
                },
            }

        python_files = sorted(
            file_path
            for file_path in state.discovered_files
            if file_path.endswith(".py")
        )

        for file_path in python_files:
            if file_path not in state.inspected_files:
                return {
                    "type": "tool_call",
                    "tool": "read_file",
                    "arguments": {
                        "path": file_path,
                    },
                }

        if not state.findings:
            return {
                "type": "tool_call",
                "tool": "add_finding",
                "arguments": {
                    "file": python_files[0],
                    "severity": "HIGH",
                    "category": "SECURITY",
                    "issue": "Hardcoded credential risk.",
                    "evidence": "A sensitive value appears directly in source code.",
                    "recommendation": "Move sensitive values to secure configuration.",
                },
            }

        if not state.report_written:
            return {
                "type": "tool_call",
                "tool": "write_report",
                "arguments": {},
            }

        return {
            "type": "final_answer",
            "answer": "Review complete. Report written to report.md.",
        }


def test_run_with_result_returns_completed_result():
    agent = Agent(
        llm=CompleteReviewLLM(),
        trace_recorder=TraceRecorder(),
        config=AgentConfig(max_steps=20),
    )

    result = agent.run_with_result(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert isinstance(result, AgentRunResult)
    assert result.is_completed is True
    assert result.status == "completed"
    assert result.answer == "Review complete. Report written to report.md."
    assert result.stop_reason is None


def test_run_with_result_returns_stopped_result():
    agent = Agent(
        llm=AlwaysInvalidLLMOutput(),
        trace_recorder=TraceRecorder(),
        config=AgentConfig(
            max_steps=20,
            max_invalid_llm_outputs=2,
        ),
    )

    result = agent.run_with_result(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert isinstance(result, AgentRunResult)
    assert result.is_stopped is True
    assert result.status == "stopped"
    assert result.answer is None
    assert result.stop_reason == STOP_INVALID_LLM_OUTPUTS
    assert result.stop_reason_code == STOP_CODE_INVALID_LLM_OUTPUTS

def test_run_remains_backward_compatible_for_completed_result():
    agent = Agent(
        llm=CompleteReviewLLM(),
        trace_recorder=TraceRecorder(),
        config=AgentConfig(max_steps=20),
    )

    answer = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert answer == "Review complete. Report written to report.md."


def test_run_remains_backward_compatible_for_stopped_result():
    agent = Agent(
        llm=NeverCompletesLLM(),
        trace_recorder=TraceRecorder(),
        config=AgentConfig(max_steps=1),
    )

    answer = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert answer == STOP_MAX_STEPS

def test_result_round_trip_for_completed_result():
    original = AgentRunResult.completed("Done.")

    restored = AgentRunResult.from_dict(original.to_dict())

    assert restored == original


def test_result_round_trip_for_stopped_result():
    original = AgentRunResult.stopped(STOP_MAX_STEPS, STOP_CODE_MAX_STEPS)

    restored = AgentRunResult.from_dict(original.to_dict())

    assert restored == original


def test_from_dict_rejects_non_dict_input():
    with pytest.raises(ValueError):
        AgentRunResult.from_dict("not a dict")



def test_stopped_result_requires_non_empty_stop_reason_code():
    with pytest.raises(ValueError):
        AgentRunResult.stopped(STOP_MAX_STEPS, "")


def test_completed_result_rejects_stop_reason_code():
    with pytest.raises(ValueError):
        AgentRunResult(
            status="completed",
            answer="Done.",
            stop_reason=None,
            stop_reason_code=STOP_CODE_MAX_STEPS,
        )


def test_from_dict_rejects_missing_stop_reason_code_field():
    with pytest.raises(ValueError):
        AgentRunResult.from_dict({
            "status": "stopped",
            "answer": None,
            "stop_reason": STOP_MAX_STEPS,
        })            

def test_run_with_result_writes_summary_for_completed_result():
    trace_recorder = TraceRecorder()

    agent = Agent(
        llm=CompleteReviewLLM(),
        trace_recorder=trace_recorder,
        config=AgentConfig(max_steps=20),
    )

    result = agent.run_with_result(
        "Review the sample project and find possible security or maintainability issues."
    )

    summary_path = (
        Path("run_summaries") / f"{trace_recorder.trace_path.stem}_summary.json"
    )

    assert summary_path.exists()

    summary_data = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary_data["result"] == result.to_dict()
    assert summary_data["result"]["status"] == "completed"
    assert summary_data["result"]["answer"] == "Review complete. Report written to report.md."
    assert summary_data["steps_count"] > 0
    assert summary_data["final_state"]["report_written"] is True


def test_run_with_result_writes_summary_for_stopped_result():
    trace_recorder = TraceRecorder()

    agent = Agent(
        llm=AlwaysInvalidLLMOutput(),
        trace_recorder=trace_recorder,
        config=AgentConfig(
            max_steps=20,
            max_invalid_llm_outputs=2,
        ),
    )

    result = agent.run_with_result(
        "Review the sample project and find possible security or maintainability issues."
    )

    summary_path = (
        Path("run_summaries") / f"{trace_recorder.trace_path.stem}_summary.json"
    )

    assert summary_path.exists()

    summary_data = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary_data["result"] == result.to_dict()
    assert summary_data["result"]["status"] == "stopped"
    assert summary_data["result"]["stop_reason_code"] == STOP_CODE_INVALID_LLM_OUTPUTS
    assert summary_data["steps_count"] == 2
    assert summary_data["final_state"]["invalid_llm_output_count"] == 2        