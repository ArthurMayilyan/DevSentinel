import copy
import json
from pathlib import Path

from evaluator import evaluate_run


BASE_TRACE_PATH = "traces/trace_20260730_161818.json"
EVAL_CASE_PATH = "eval_cases/security_review_eval.json"


def load_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_baseline():
    trace = load_json(BASE_TRACE_PATH)
    eval_case = load_json(EVAL_CASE_PATH)
    return trace, eval_case


def test_positive_baseline_passes():
    trace, eval_case = load_baseline()

    result = evaluate_run(trace, eval_case)

    assert result["passed"] is True


def test_write_report_with_markdown_fails():
    trace, eval_case = load_baseline()
    trace = copy.deepcopy(trace)

    # Step 10 is write_report in your successful trace
    trace[9]["llm_output"]["arguments"] = {
        "markdown": "LLM should not provide markdown"
    }

    result = evaluate_run(trace, eval_case)

    assert result["passed"] is False
    assert any(
        "write_report" in failure
        for failure in result["failures"]
    )

def test_write_report_with_state_fails():
    trace, eval_case = load_baseline()
    trace = copy.deepcopy(trace)

    # Step 10 is write_report in your successful trace.
    # We simulate bad LLM behavior: it tries to pass internal state.
    trace[9]["llm_output"]["arguments"] = {
        "state": "fake state from LLM"
    }

    result = evaluate_run(trace, eval_case)

    assert result["passed"] is False
    assert any(
        "received forbidden LLM argument: `state`" in failure
        for failure in result["failures"]
    ), result["failures"]    

def test_final_answer_before_report_written_fails():
    trace, eval_case = load_baseline()
    trace = copy.deepcopy(trace)

    # Last step is final_answer.
    # We simulate bad state: final answer was produced before report was written.
    trace[-1]["state_before"]["report_written"] = False
    trace[-1]["state_before"]["report_path"] = None

    result = evaluate_run(trace, eval_case)

    assert result["passed"] is False
    assert any(
        "final_answer was produced before report_written=True" in failure
        for failure in result["failures"]
    ), result["failures"]

def test_required_file_not_inspected_fails():
    trace, eval_case = load_baseline()
    trace = copy.deepcopy(trace)

    # Final state says review is complete, but config.py is missing
    # from inspected_files. Evaluator must catch this.
    final_state = trace[-1]["state_after"]

    final_state["inspected_files"] = [
        path
        for path in final_state["inspected_files"]
        if "config.py" not in path
    ]

    result = evaluate_run(trace, eval_case)

    assert result["passed"] is False
    assert any(
        "Required file was not inspected" in failure
        for failure in result["failures"]
    ), result["failures"]

def test_invalid_severity_fails():
    trace, eval_case = load_baseline()
    trace = copy.deepcopy(trace)

    # Final state contains an invalid severity value.
    # Evaluator must reject it.
    trace[-1]["state_after"]["findings"][0]["severity"] = "CRITICALITY_HIGH"

    result = evaluate_run(trace, eval_case)

    assert result["passed"] is False
    assert any(
        "invalid severity" in failure
        for failure in result["failures"]
    ), result["failures"]    

def test_invalid_category_fails():
    trace, eval_case = load_baseline()
    trace = copy.deepcopy(trace)

    # Final state contains an invalid category value.
    # Evaluator must reject it.
    trace[-1]["state_after"]["findings"][0]["category"] = "Security"

    result = evaluate_run(trace, eval_case)

    assert result["passed"] is False
    assert any(
        "invalid category" in failure
        for failure in result["failures"]
    ), result["failures"]

def test_missing_required_finding_field_fails():
    trace, eval_case = load_baseline()
    trace = copy.deepcopy(trace)

    # Final state contains a finding without required field.
    # Evaluator must reject it.
    del trace[-1]["state_after"]["findings"][0]["recommendation"]

    result = evaluate_run(trace, eval_case)

    assert result["passed"] is False
    assert any(
        "missing fields" in failure
        for failure in result["failures"]
    ), result["failures"]        

def test_add_finding_before_file_inspection_fails():
    trace, eval_case = load_baseline()
    trace = copy.deepcopy(trace)

    # Step 5 is the first add_finding for auth.py.
    # We simulate bad process: auth.py was not inspected before add_finding.
    trace[4]["state_before"]["inspected_files"] = [
        "sample_project\\app.py"
    ]

    result = evaluate_run(trace, eval_case)

    assert result["passed"] is False
    assert any(
        "add_finding was called for" in failure
        for failure in result["failures"]
    ), result["failures"]    

def test_write_report_before_all_files_inspected_fails():
    trace, eval_case = load_baseline()
    trace = copy.deepcopy(trace)

    # Step 10 is write_report.
    # We simulate bad process: config.py was not inspected before writing report.
    write_report_step = trace[9]

    write_report_step["state_before"]["inspected_files"] = [
        path
        for path in write_report_step["state_before"]["inspected_files"]
        if "config.py" not in path
    ]

    result = evaluate_run(trace, eval_case)

    assert result["passed"] is False
    assert any(
        "write_report was called before all required files were inspected" in failure
        for failure in result["failures"]
    ), result["failures"]

def test_last_step_must_be_final_answer_fails():
    trace, eval_case = load_baseline()
    trace = copy.deepcopy(trace)

    # We simulate bad process: the trace ends with a tool_call instead of final_answer.
    trace[-1]["llm_output"] = {
        "type": "tool_call",
        "tool": "write_report",
        "arguments": {}
    }

    result = evaluate_run(trace, eval_case)

    assert result["passed"] is False
    assert any(
        "Last step is not final_answer" in failure
        for failure in result["failures"]
    ), result["failures"]

def test_write_report_before_any_findings_fails():
    trace, eval_case = load_baseline()
    trace = copy.deepcopy(trace)

    # Step 10 is write_report.
    # We simulate bad process: report is written before any findings exist.
    write_report_step = trace[9]

    write_report_step["state_before"]["findings"] = []

    result = evaluate_run(trace, eval_case)

    assert result["passed"] is False
    assert any(
        "write_report was called before any findings were added" in failure
        for failure in result["failures"]
    ), result["failures"]

def test_unknown_tool_call_fails():
    trace, eval_case = load_baseline()
    trace = copy.deepcopy(trace)

    # We simulate bad LLM behavior: it tries to call a tool
    # that does not exist in the allowed tool registry.
    trace[1]["llm_output"] = {
        "type": "tool_call",
        "tool": "delete_project",
        "arguments": {
            "path": "./sample_project"
        }
    }

    result = evaluate_run(trace, eval_case)

    assert result["passed"] is False
    assert any(
        "unknown tool called" in failure
        for failure in result["failures"]
    ), result["failures"]

def test_invalid_llm_output_type_fails():
    trace, eval_case = load_baseline()
    trace = copy.deepcopy(trace)

    # We simulate bad LLM behavior: output type is not tool_call or final_answer.
    trace[1]["llm_output"] = {
        "type": "analysis",
        "text": "I should probably read auth.py next."
    }

    result = evaluate_run(trace, eval_case)

    assert result["passed"] is False
    assert any(
        "invalid LLM output type" in failure
        for failure in result["failures"]
    ), result["failures"]

def test_tool_call_without_tool_name_fails():
    trace, eval_case = load_baseline()
    trace = copy.deepcopy(trace)

    # We simulate bad LLM behavior: tool_call without tool name.
    trace[1]["llm_output"] = {
        "type": "tool_call",
        "arguments": {
            "path": "sample_project\\auth.py"
        }
    }

    result = evaluate_run(trace, eval_case)

    assert result["passed"] is False
    assert any(
        "tool_call is missing tool name" in failure
        for failure in result["failures"]
    ), result["failures"]

def test_final_answer_without_answer_text_fails():
    trace, eval_case = load_baseline()
    trace = copy.deepcopy(trace)

    # We simulate bad LLM behavior: final_answer has no answer text.
    trace[-1]["llm_output"] = {
        "type": "final_answer",
        "answer": ""
    }

    result = evaluate_run(trace, eval_case)

    assert result["passed"] is False
    assert any(
        "final_answer is missing non-empty answer text" in failure
        for failure in result["failures"]
    ), result["failures"]

def test_tool_call_arguments_must_be_dict_fails():
    trace, eval_case = load_baseline()
    trace = copy.deepcopy(trace)

    # We simulate bad LLM behavior: arguments is a string, not a dict.
    trace[1]["llm_output"] = {
        "type": "tool_call",
        "tool": "read_file",
        "arguments": "sample_project\\auth.py"
    }

    result = evaluate_run(trace, eval_case)

    assert result["passed"] is False
    assert any(
        "tool_call arguments must be a dict" in failure
        for failure in result["failures"]
    ), result["failures"]

def test_read_file_missing_path_argument_fails():
    trace, eval_case = load_baseline()
    trace = copy.deepcopy(trace)

    # We simulate bad LLM behavior: read_file is called without required path.
    trace[1]["llm_output"] = {
        "type": "tool_call",
        "tool": "read_file",
        "arguments": {}
    }

    result = evaluate_run(trace, eval_case)

    assert result["passed"] is False
    assert any(
        "tool `read_file` is missing required arguments" in failure
        for failure in result["failures"]
    ), result["failures"]

def test_read_file_unexpected_argument_fails():
    trace, eval_case = load_baseline()
    trace = copy.deepcopy(trace)

    # We simulate bad LLM behavior: read_file receives an argument
    # that is not part of its schema.
    trace[1]["llm_output"] = {
        "type": "tool_call",
        "tool": "read_file",
        "arguments": {
            "path": "sample_project\\auth.py",
            "recursive": True,
        }
    }

    result = evaluate_run(trace, eval_case)

    assert result["passed"] is False
    assert any(
        "tool `read_file` received unexpected arguments" in failure
        for failure in result["failures"]
    ), result["failures"]

def test_trace_state_continuity_broken_fails():
    trace, eval_case = load_baseline()
    trace = copy.deepcopy(trace)

    # We simulate corrupted trace recording:
    # step 6 state_before no longer matches step 5 state_after.
    trace[5]["state_before"]["errors"].append("corrupted trace state")

    result = evaluate_run(trace, eval_case)

    assert result["passed"] is False
    assert any(
        "Trace state continuity broken" in failure
        for failure in result["failures"]
    ), result["failures"]

def test_trace_step_numbers_must_be_sequential_fails():
    trace, eval_case = load_baseline()
    trace = copy.deepcopy(trace)

    # We simulate corrupted trace numbering:
    # step 6 is incorrectly labeled as step 99.
    trace[5]["step"] = 99

    result = evaluate_run(trace, eval_case)

    assert result["passed"] is False
    assert any(
        "Trace step numbering is invalid" in failure
        for failure in result["failures"]
    ), result["failures"]

