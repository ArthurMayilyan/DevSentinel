import json
import sys
from pathlib import Path
from agent import Agent
from tool_specs import TOOL_SPECS
from agent_config import AgentConfig

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from agent import Agent
from bad_llm import bad_final_answer_too_early_then_recovers
from evaluator import evaluate_run, load_json
from trace import TraceRecorder
from agent_stop_reasons import (
    STOP_REJECTED_FINAL_ANSWERS,
    STOP_REJECTED_TOOL_CALLS,
    STOP_INVALID_LLM_OUTPUTS,
)
from bad_llm import (
    bad_final_answer_too_early_then_recovers,
    bad_unknown_tool_then_recovers,
    bad_write_report_with_markdown_then_completes,
    bad_add_finding_before_read_then_recovers,
    bad_write_report_before_full_inspection_then_recovers,
    bad_add_finding_invalid_severity_then_recovers,
    bad_add_finding_invalid_category_then_recovers,
    bad_tool_arguments_not_dict_then_recovers,
    bad_read_file_missing_path_then_recovers,
    bad_read_file_unexpected_argument_then_recovers,
    bad_empty_final_answer_then_recovers,
    bad_non_string_final_answer_then_recovers,
    bad_tool_call_missing_tool_name_then_recovers,
    bad_tool_name_not_string_then_recovers,
    bad_invalid_output_type_then_recovers,
    bad_missing_output_type_then_recovers,
    bad_llm_output_not_dict_then_recovers,
)

class AlwaysFinalAnswerTooEarlyLLM:
    def complete(self, messages, state=None):
        return {
            "type": "final_answer",
            "answer": "Done too early."
        }

class AlwaysUnknownToolLLM:
    def complete(self, messages, state=None):
        return {
            "type": "tool_call",
            "tool": "delete_project",
            "arguments": {
                "path": "./sample_project"
            },
        }

class AlwaysInvalidLLMOutput:
    def complete(self, messages, state=None):
        return "not a json object"
        

def snapshot_trace_files() -> dict[Path, int]:
    return {
        path: path.stat().st_mtime_ns
        for path in Path("traces").glob("trace_*.json")
    }


def find_new_or_modified_trace(before_snapshot: dict[Path, int]) -> Path:
    candidates = []

    for path in Path("traces").glob("trace_*.json"):
        current_mtime = path.stat().st_mtime_ns
        previous_mtime = before_snapshot.get(path)

        if previous_mtime is None or current_mtime != previous_mtime:
            candidates.append(path)

    assert candidates, "No new or modified trace file was written."

    return max(candidates, key=lambda path: path.stat().st_mtime_ns)

def test_final_answer_too_early_is_rejected_then_agent_recovers():
    llm = bad_final_answer_too_early_then_recovers()
    trace_recorder = TraceRecorder()

    before_snapshot = snapshot_trace_files()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        max_steps=20,
    )

    final_answer = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert final_answer is not None

    latest_trace_path = find_new_or_modified_trace(before_snapshot)

    trace = json.loads(latest_trace_path.read_text(encoding="utf-8"))
    final_state = trace[-1]["state_after"]

    first_step = trace[0]

    assert first_step["llm_output"]["type"] == "final_answer"

    guardrail_result = first_step.get("guardrail_result")

    assert guardrail_result is not None
    assert guardrail_result["allowed"] is False

    assert final_state["rejected_final_answer_count"] >= 1
    assert final_state["report_written"] is True
    assert final_state["report_path"] == "report.md"

def test_unknown_tool_is_rejected_then_agent_recovers():
    llm = bad_unknown_tool_then_recovers()
    trace_recorder = TraceRecorder()

    before_snapshot = snapshot_trace_files()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        max_steps=20,
    )

    final_answer = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert final_answer is not None

    latest_trace_path = find_new_or_modified_trace(before_snapshot)

    trace = json.loads(latest_trace_path.read_text(encoding="utf-8"))
    final_state = trace[-1]["state_after"]

    first_step = trace[0]

    assert first_step["llm_output"]["type"] == "tool_call"
    assert first_step["llm_output"]["tool"] == "delete_project"

    assert first_step.get("error") is not None
    assert "Unknown tool" in first_step["error"] or "unknown tool" in first_step["error"].lower()

    assert final_state["report_written"] is True
    assert final_state["report_path"] == "report.md"
    assert len(final_state["findings"]) >= 1    

def test_write_report_with_markdown_is_rejected_then_recovers():
    llm = bad_write_report_with_markdown_then_completes()
    trace_recorder = TraceRecorder()

    before_snapshot = snapshot_trace_files()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        max_steps=20,
    )

    final_answer = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert final_answer == "Review complete. Report written to report.md."

    latest_trace_path = find_new_or_modified_trace(before_snapshot)

    trace = json.loads(latest_trace_path.read_text(encoding="utf-8"))
    final_state = trace[-1]["state_after"]

    write_report_steps = [
        step
        for step in trace
        if step.get("llm_output", {}).get("tool") == "write_report"
    ]

    assert len(write_report_steps) == 2

    bad_write_report_step = write_report_steps[0]
    good_write_report_step = write_report_steps[1]

    # The first write_report call violated the tool contract.
    assert "markdown" in bad_write_report_step["llm_output"]["arguments"]

    assert bad_write_report_step.get("error") is not None

    error_text = bad_write_report_step["error"].lower()

    assert (
        "unexpected" in error_text
        or "markdown" in error_text
        or "arguments" in error_text
    ), bad_write_report_step["error"]

    # The bad call must not write the report.
    assert bad_write_report_step["tool_result"] is None
    assert bad_write_report_step["state_after"]["report_written"] is False
    assert bad_write_report_step["state_after"]["report_path"] is None

    # The second write_report call is valid.
    assert good_write_report_step["llm_output"]["arguments"] == {}
    assert good_write_report_step["tool_result"] == "report.md"
    assert good_write_report_step["state_after"]["report_written"] is True
    assert good_write_report_step["state_after"]["report_path"] == "report.md"

    # Final state should be successful.
    assert final_state["report_written"] is True
    assert final_state["report_path"] == "report.md"
    assert len(final_state["findings"]) >= 1

    # Evaluator should still fail this trace because the LLM attempted
    # an invalid write_report call first.
    eval_case = load_json("eval_cases/security_review_eval.json")
    result = evaluate_run(trace, eval_case)

    assert result["passed"] is False
    assert any(
        "write_report" in failure and "markdown" in failure
        for failure in result["failures"]
    ), result["failures"]
    
def test_add_finding_before_file_inspection_is_rejected_then_recovers():
    llm = bad_add_finding_before_read_then_recovers()
    trace_recorder = TraceRecorder()

    before_snapshot = snapshot_trace_files()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        max_steps=20,
    )

    final_answer = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert final_answer is not None

    latest_trace_path = find_new_or_modified_trace(before_snapshot)

    trace = json.loads(latest_trace_path.read_text(encoding="utf-8"))
    final_state = trace[-1]["state_after"]

    # Step 2 is the bad add_finding call.
    bad_step = trace[1]

    assert bad_step["llm_output"]["type"] == "tool_call"
    assert bad_step["llm_output"]["tool"] == "add_finding"

    assert bad_step.get("error") is not None
    assert (
        "before" in bad_step["error"].lower()
        or "inspect" in bad_step["error"].lower()
        or "read" in bad_step["error"].lower()
    )

    # The invalid finding should not be added at step 2.
    assert bad_step["state_after"]["findings"] == []

    # But the agent should recover later.
    assert final_state["report_written"] is True
    assert final_state["report_path"] == "report.md"
    assert len(final_state["findings"]) >= 1


def test_write_report_before_full_inspection_is_rejected_then_recovers():
    llm = bad_write_report_before_full_inspection_then_recovers()
    trace_recorder = TraceRecorder()

    before_snapshot = snapshot_trace_files()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        max_steps=20,
    )

    final_answer = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert final_answer is not None

    latest_trace_path = find_new_or_modified_trace(before_snapshot)

    trace = json.loads(latest_trace_path.read_text(encoding="utf-8"))
    final_state = trace[-1]["state_after"]

    # Step 3 is the bad write_report call.
    bad_step = trace[2]

    assert bad_step["llm_output"]["type"] == "tool_call"
    assert bad_step["llm_output"]["tool"] == "write_report"

    assert bad_step.get("error") is not None
    assert (
        "write_report rejected" in bad_step["error"]
        or "not inspected" in bad_step["error"].lower()
        or "findings" in bad_step["error"].lower()
    )

    # The bad write_report call must not mark report as written.
    assert bad_step["state_after"]["report_written"] is False
    assert bad_step["state_after"]["report_path"] is None

    # But agent should recover later.
    assert final_state["report_written"] is True
    assert final_state["report_path"] == "report.md"
    assert len(final_state["findings"]) >= 1    

def test_add_finding_invalid_severity_is_rejected_then_recovers():
    llm = bad_add_finding_invalid_severity_then_recovers()
    trace_recorder = TraceRecorder()

    before_snapshot = snapshot_trace_files()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        max_steps=20,
    )

    final_answer = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert final_answer is not None

    latest_trace_path = find_new_or_modified_trace(before_snapshot)

    trace = json.loads(latest_trace_path.read_text(encoding="utf-8"))
    final_state = trace[-1]["state_after"]

    # Step 5 is the bad add_finding call with invalid severity.
    bad_step = trace[4]

    assert bad_step["llm_output"]["type"] == "tool_call"
    assert bad_step["llm_output"]["tool"] == "add_finding"
    assert bad_step["llm_output"]["arguments"]["severity"] == "CRITICALITY_HIGH"

    assert bad_step.get("error") is not None
    
    error_text = bad_step["error"].lower()

    assert (
        "invalid value" in error_text
        or "severity" in error_text
        or "criticality_high" in error_text
    ), bad_step["error"]

    # The invalid finding must not be added.
    assert bad_step["state_after"]["findings"] == []

    # But the agent should recover later.
    assert final_state["report_written"] is True
    assert final_state["report_path"] == "report.md"
    assert len(final_state["findings"]) >= 1

def test_add_finding_invalid_category_is_rejected_then_recovers():
    llm = bad_add_finding_invalid_category_then_recovers()
    trace_recorder = TraceRecorder()

    before_snapshot = snapshot_trace_files()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        max_steps=20,
    )

    final_answer = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert final_answer is not None

    latest_trace_path = find_new_or_modified_trace(before_snapshot)

    trace = json.loads(latest_trace_path.read_text(encoding="utf-8"))
    final_state = trace[-1]["state_after"]

    # Step 5 is the bad add_finding call with invalid category.
    bad_step = trace[4]

    assert bad_step["llm_output"]["type"] == "tool_call"
    assert bad_step["llm_output"]["tool"] == "add_finding"
    assert bad_step["llm_output"]["arguments"]["category"] == "Security"

    assert bad_step.get("error") is not None

    error_text = bad_step["error"].lower()

    assert (
        "invalid value" in error_text
        or "category" in error_text
        or "security" in error_text
    ), bad_step["error"]

    # The invalid finding must not be added.
    assert bad_step["state_after"]["findings"] == []

    # But the agent should recover later.
    assert final_state["report_written"] is True
    assert final_state["report_path"] == "report.md"
    assert len(final_state["findings"]) >= 1    

def test_tool_arguments_must_be_dict_then_recovers():
    llm = bad_tool_arguments_not_dict_then_recovers()
    trace_recorder = TraceRecorder()

    before_snapshot = snapshot_trace_files()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        max_steps=20,
    )

    final_answer = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert final_answer is not None

    latest_trace_path = find_new_or_modified_trace(before_snapshot)

    trace = json.loads(latest_trace_path.read_text(encoding="utf-8"))
    final_state = trace[-1]["state_after"]

    # Step 2 is the bad read_file call.
    bad_step = trace[1]

    assert bad_step["llm_output"]["type"] == "tool_call"
    assert bad_step["llm_output"]["tool"] == "read_file"
    assert bad_step["llm_output"]["arguments"] == "sample_project\\auth.py"

    assert bad_step.get("error") is not None

    error_text = bad_step["error"].lower()

    assert (
        "arguments" in error_text
        and (
            "dict" in error_text
            or "object" in error_text
        )
    ), bad_step["error"]

    # The bad read_file call must not inspect the file.
    assert "sample_project\\auth.py" not in bad_step["state_after"]["inspected_files"]
    assert "sample_project/auth.py" not in bad_step["state_after"]["inspected_files"]

    # But the agent should recover later.
    assert final_state["report_written"] is True
    assert final_state["report_path"] == "report.md"
    assert len(final_state["findings"]) >= 1    


def test_runtime_accepts_windows_style_read_file_path_after_recovery():
    llm = bad_unknown_tool_then_recovers()
    trace_recorder = TraceRecorder()

    before_snapshot = snapshot_trace_files()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        max_steps=20,
    )

    final_answer = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert final_answer is not None

    latest_trace_path = find_new_or_modified_trace(before_snapshot)
    trace = json.loads(latest_trace_path.read_text(encoding="utf-8"))

    read_file_steps = [
        step
        for step in trace
        if step.get("llm_output", {}).get("tool") == "read_file"
    ]

    assert read_file_steps

    assert any(
        step["state_after"]["inspected_files"]
        for step in read_file_steps
    )

    final_state = trace[-1]["state_after"]

    assert final_state["report_written"] is True
    assert final_state["report_path"] == "report.md"


def test_read_file_missing_required_path_is_rejected_then_recovers():
    llm = bad_read_file_missing_path_then_recovers()
    trace_recorder = TraceRecorder()

    before_snapshot = snapshot_trace_files()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        max_steps=20,
    )

    final_answer = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert final_answer is not None

    latest_trace_path = find_new_or_modified_trace(before_snapshot)

    trace = json.loads(latest_trace_path.read_text(encoding="utf-8"))
    final_state = trace[-1]["state_after"]

    # Step 2 is the bad read_file call.
    bad_step = trace[1]

    assert bad_step["llm_output"]["type"] == "tool_call"
    assert bad_step["llm_output"]["tool"] == "read_file"
    assert bad_step["llm_output"]["arguments"] == {}

    assert bad_step.get("error") is not None

    error_text = bad_step["error"].lower()

    assert (
        "path" in error_text
        or "missing" in error_text
        or "required" in error_text
    ), bad_step["error"]

    # The bad read_file call must not inspect any file.
    assert bad_step["state_after"]["inspected_files"] == []

    # But the agent should recover later.
    assert final_state["report_written"] is True
    assert final_state["report_path"] == "report.md"
    assert len(final_state["findings"]) >= 1    

def test_read_file_unexpected_argument_is_rejected_then_recovers():
    llm = bad_read_file_unexpected_argument_then_recovers()
    trace_recorder = TraceRecorder()

    before_snapshot = snapshot_trace_files()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        max_steps=20,
    )

    final_answer = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert final_answer is not None

    latest_trace_path = find_new_or_modified_trace(before_snapshot)

    trace = json.loads(latest_trace_path.read_text(encoding="utf-8"))
    final_state = trace[-1]["state_after"]

    # Step 2 is the bad read_file call.
    bad_step = trace[1]

    assert bad_step["llm_output"]["type"] == "tool_call"
    assert bad_step["llm_output"]["tool"] == "read_file"
    assert bad_step["llm_output"]["arguments"]["path"] == "sample_project\\auth.py"
    assert bad_step["llm_output"]["arguments"]["mode"] == "unsafe"

    assert bad_step.get("error") is not None

    error_text = bad_step["error"].lower()

    assert (
        "unexpected" in error_text
        or "mode" in error_text
        or "keyword" in error_text
        or "argument" in error_text
    ), bad_step["error"]

    # The bad read_file call must not inspect auth.py yet.
    assert "sample_project\\auth.py" not in bad_step["state_after"]["inspected_files"]
    assert "sample_project/auth.py" not in bad_step["state_after"]["inspected_files"]

    # But the agent should recover later.
    assert final_state["report_written"] is True
    assert final_state["report_path"] == "report.md"
    assert len(final_state["findings"]) >= 1    

def test_empty_final_answer_is_rejected_then_recovers():
    llm = bad_empty_final_answer_then_recovers()
    trace_recorder = TraceRecorder()

    before_snapshot = snapshot_trace_files()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        max_steps=20,
    )

    final_answer = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert final_answer == "Review complete. Report written to report.md."

    latest_trace_path = find_new_or_modified_trace(before_snapshot)

    trace = json.loads(latest_trace_path.read_text(encoding="utf-8"))
    final_state = trace[-1]["state_after"]

    # Step 11 is the bad empty final_answer.
    bad_step = trace[10]

    assert bad_step["llm_output"]["type"] == "final_answer"
    assert bad_step["llm_output"]["answer"] == ""

    guardrail_result = bad_step.get("guardrail_result")

    assert guardrail_result is not None
    assert guardrail_result["allowed"] is False

    reason = guardrail_result["reason"].lower()

    assert (
        "answer" in reason
        or "empty" in reason
        or "final" in reason
    ), guardrail_result["reason"]

    assert final_state["report_written"] is True
    assert final_state["report_path"] == "report.md"
    assert final_state["rejected_final_answer_count"] >= 1

def test_non_string_final_answer_is_rejected_then_recovers():
    llm = bad_non_string_final_answer_then_recovers()
    trace_recorder = TraceRecorder()

    before_snapshot = snapshot_trace_files()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        max_steps=20,
    )

    final_answer = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert final_answer == "Review complete. Report written to report.md."

    latest_trace_path = find_new_or_modified_trace(before_snapshot)

    trace = json.loads(latest_trace_path.read_text(encoding="utf-8"))
    final_state = trace[-1]["state_after"]

    # Step 11 is the bad non-string final_answer.
    bad_step = trace[10]

    assert bad_step["llm_output"]["type"] == "final_answer"
    assert bad_step["llm_output"]["answer"] == {
        "message": "Review complete. Report written to report.md."
    }

    guardrail_result = bad_step.get("guardrail_result")

    assert guardrail_result is not None
    assert guardrail_result["allowed"] is False

    reason = guardrail_result["reason"].lower()

    assert (
        "answer" in reason
        and (
            "string" in reason
            or "str" in reason
        )
    ), guardrail_result["reason"]

    assert final_state["report_written"] is True
    assert final_state["report_path"] == "report.md"
    assert final_state["rejected_final_answer_count"] >= 1

def test_tool_call_missing_tool_name_is_rejected_then_recovers():
    llm = bad_tool_call_missing_tool_name_then_recovers()
    trace_recorder = TraceRecorder()

    before_snapshot = snapshot_trace_files()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        max_steps=20,
    )

    final_answer = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert final_answer == "Review complete. Report written to report.md."

    latest_trace_path = find_new_or_modified_trace(before_snapshot)

    trace = json.loads(latest_trace_path.read_text(encoding="utf-8"))
    final_state = trace[-1]["state_after"]

    # Step 1 is the bad tool_call without tool name.
    bad_step = trace[0]

    assert bad_step["llm_output"]["type"] == "tool_call"
    assert "tool" not in bad_step["llm_output"]

    assert bad_step.get("error") is not None

    error_text = bad_step["error"].lower()

    assert (
        "missing" in error_text
        and (
            "tool" in error_text
            or "name" in error_text
        )
    ), bad_step["error"]

    # Nothing should be discovered or inspected from this bad step.
    assert bad_step["state_after"]["discovered_files"] == []
    assert bad_step["state_after"]["inspected_files"] == []

    # But the agent should recover later.
    assert final_state["report_written"] is True
    assert final_state["report_path"] == "report.md"
    assert len(final_state["findings"]) >= 1

def test_tool_name_must_be_string_then_recovers():
    llm = bad_tool_name_not_string_then_recovers()
    trace_recorder = TraceRecorder()

    before_snapshot = snapshot_trace_files()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        max_steps=20,
    )

    final_answer = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert final_answer == "Review complete. Report written to report.md."

    latest_trace_path = find_new_or_modified_trace(before_snapshot)

    trace = json.loads(latest_trace_path.read_text(encoding="utf-8"))
    final_state = trace[-1]["state_after"]

    # Step 1 is the bad tool_call with non-string tool name.
    bad_step = trace[0]

    assert bad_step["llm_output"]["type"] == "tool_call"
    assert bad_step["llm_output"]["tool"] == 123

    assert bad_step.get("error") is not None

    error_text = bad_step["error"].lower()

    assert (
        "tool" in error_text
        and (
            "string" in error_text
            or "str" in error_text
        )
    ), bad_step["error"]

    # Nothing should be discovered or inspected from this bad step.
    assert bad_step["state_after"]["discovered_files"] == []
    assert bad_step["state_after"]["inspected_files"] == []

    # But the agent should recover later.
    assert final_state["report_written"] is True
    assert final_state["report_path"] == "report.md"
    assert len(final_state["findings"]) >= 1    

def test_invalid_llm_output_type_is_rejected_then_recovers():
    llm = bad_invalid_output_type_then_recovers()
    trace_recorder = TraceRecorder()

    before_snapshot = snapshot_trace_files()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        max_steps=20,
    )

    final_answer = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert final_answer == "Review complete. Report written to report.md."

    latest_trace_path = find_new_or_modified_trace(before_snapshot)

    trace = json.loads(latest_trace_path.read_text(encoding="utf-8"))
    final_state = trace[-1]["state_after"]

    # Step 1 is invalid output type.
    bad_step = trace[0]

    assert bad_step["llm_output"]["type"] == "analysis"

    assert bad_step.get("error") is not None

    error_text = bad_step["error"].lower()

    assert (
        "invalid" in error_text
        and (
            "type" in error_text
            or "tool_call" in error_text
            or "final_answer" in error_text
        )
    ), bad_step["error"]

    # Nothing should happen from invalid output.
    assert bad_step["state_after"]["discovered_files"] == []
    assert bad_step["state_after"]["inspected_files"] == []
    assert bad_step["state_after"]["findings"] == []

    # But the agent should recover later.
    assert final_state["report_written"] is True
    assert final_state["report_path"] == "report.md"
    assert len(final_state["findings"]) >= 1

def test_missing_llm_output_type_is_rejected_then_recovers():
    llm = bad_missing_output_type_then_recovers()
    trace_recorder = TraceRecorder()

    before_snapshot = snapshot_trace_files()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        max_steps=20,
    )

    final_answer = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert final_answer == "Review complete. Report written to report.md."

    latest_trace_path = find_new_or_modified_trace(before_snapshot)

    trace = json.loads(latest_trace_path.read_text(encoding="utf-8"))
    final_state = trace[-1]["state_after"]

    # Step 1 is invalid because "type" is missing.
    bad_step = trace[0]

    assert "type" not in bad_step["llm_output"]
    assert bad_step["llm_output"]["tool"] == "list_files"

    assert bad_step.get("error") is not None

    error_text = bad_step["error"].lower()

    assert (
        "type" in error_text
        and (
            "missing" in error_text
            or "invalid" in error_text
            or "tool_call" in error_text
            or "final_answer" in error_text
        )
    ), bad_step["error"]

    # Nothing should happen from invalid output.
    assert bad_step["state_after"]["discovered_files"] == []
    assert bad_step["state_after"]["inspected_files"] == []
    assert bad_step["state_after"]["findings"] == []

    # But the agent should recover later.
    assert final_state["report_written"] is True
    assert final_state["report_path"] == "report.md"
    assert len(final_state["findings"]) >= 1

def test_llm_output_must_be_dict_then_recovers():
    llm = bad_llm_output_not_dict_then_recovers()
    trace_recorder = TraceRecorder()

    before_snapshot = snapshot_trace_files()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        max_steps=20,
    )

    final_answer = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert final_answer == "Review complete. Report written to report.md."

    latest_trace_path = find_new_or_modified_trace(before_snapshot)

    trace = json.loads(latest_trace_path.read_text(encoding="utf-8"))
    final_state = trace[-1]["state_after"]

    # Step 1 is invalid because llm_output is not a dict.
    bad_step = trace[0]

    assert bad_step["llm_output"] == "not a json object"

    assert bad_step.get("error") is not None

    error_text = bad_step["error"].lower()

    assert (
        "llm output" in error_text
        or "json object" in error_text
        or "dict" in error_text
    ), bad_step["error"]

    # Nothing should happen from invalid output.
    assert bad_step["state_after"]["discovered_files"] == []
    assert bad_step["state_after"]["inspected_files"] == []
    assert bad_step["state_after"]["findings"] == []

    # But the agent should recover later.
    assert final_state["report_written"] is True
    assert final_state["report_path"] == "report.md"
    assert len(final_state["findings"]) >= 1


def test_agent_stops_after_rejected_final_answer_limit():
    llm = AlwaysFinalAnswerTooEarlyLLM()
    trace_recorder = TraceRecorder()

    before_snapshot = snapshot_trace_files()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        config=AgentConfig(
            max_steps=20,
            max_rejected_final_answers=2,
        ),
    )

    final_answer = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert final_answer == STOP_REJECTED_FINAL_ANSWERS

    latest_trace_path = find_new_or_modified_trace(before_snapshot)

    trace = json.loads(latest_trace_path.read_text(encoding="utf-8"))
    final_state = trace[-1]["state_after"]

    assert len(trace) == 2
    assert final_state["rejected_final_answer_count"] == 2
    assert final_state["report_written"] is False

    for step in trace:
        guardrail_result = step.get("guardrail_result")
        assert guardrail_result is not None
        assert guardrail_result["allowed"] is False

def test_agent_stops_after_rejected_tool_call_limit():
    llm = AlwaysUnknownToolLLM()
    trace_recorder = TraceRecorder()

    before_snapshot = snapshot_trace_files()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        config=AgentConfig(
            max_steps=20,
            max_rejected_tool_calls=2,
        ),
    )

    final_answer = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert final_answer == STOP_REJECTED_TOOL_CALLS

    latest_trace_path = find_new_or_modified_trace(before_snapshot)

    trace = json.loads(latest_trace_path.read_text(encoding="utf-8"))
    final_state = trace[-1]["state_after"]

    assert len(trace) == 2
    assert final_state["rejected_tool_call_count"] == 2
    assert final_state["report_written"] is False

    for step in trace:
        assert step["llm_output"]["tool"] == "delete_project"
        assert step.get("error") is not None
        assert "unknown tool" in step["error"].lower()

def test_agent_stops_after_invalid_llm_output_limit():
    llm = AlwaysInvalidLLMOutput()
    trace_recorder = TraceRecorder()

    before_snapshot = snapshot_trace_files()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        config=AgentConfig(
            max_steps=20,
            max_invalid_llm_outputs=2,
        ),
    )

    final_answer = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    assert final_answer == STOP_INVALID_LLM_OUTPUTS

    latest_trace_path = find_new_or_modified_trace(before_snapshot)

    trace = json.loads(latest_trace_path.read_text(encoding="utf-8"))
    final_state = trace[-1]["state_after"]

    assert len(trace) == 2
    assert final_state["invalid_llm_output_count"] == 2
    assert final_state["report_written"] is False

    for step in trace:
        assert step["llm_output"] == "not a json object"
        assert step.get("error") is not None

        error_text = step["error"].lower()

        assert (
            "invalid llm output" in error_text
            or "json object" in error_text
            or "dict" in error_text
        ), step["error"]

