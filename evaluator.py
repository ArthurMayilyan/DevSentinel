import argparse
import json
from pathlib import Path
from typing import Any

from tool_specs import IssueCategory, IssueSeverity


ALLOWED_SEVERITIES = {item.value for item in IssueSeverity}
ALLOWED_CATEGORIES = {item.value for item in IssueCategory}

FORBIDDEN_TOOL_ARGUMENTS = {
    "write_report": {"state"},
}

REQUIRED_FINDING_FIELDS = {
    "file",
    "severity",
    "category",
    "issue",
    "evidence",
    "recommendation",
}


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip()


def load_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def get_final_state_from_trace(trace: list[dict]) -> dict:
    if not trace:
        raise ValueError("Trace is empty.")

    last_step = trace[-1]

    if "state_after" not in last_step:
        raise ValueError("Last trace step does not contain state_after.")

    return last_step["state_after"]


def finding_combined_text(finding: dict) -> str:
    return " ".join([
        finding.get("issue", ""),
        finding.get("evidence", ""),
        finding.get("recommendation", ""),
    ]).lower()


def finding_matches_expected(finding: dict, expected: dict) -> bool:
    finding_file = normalize_path(finding.get("file", ""))
    expected_file = normalize_path(expected["file"])

    combined_text = finding_combined_text(finding)

    return (
        finding_file == expected_file
        and expected["issue_contains"].lower() in combined_text
        and finding.get("severity") == expected["severity"]
        and finding.get("category") == expected["category"]
    )


def evaluate_trace_process(trace: list[dict]) -> list[str]:
    failures: list[str] = []

    for step in trace:
        step_number = step.get("step")
        llm_output = step.get("llm_output", {})

        if llm_output.get("type") != "tool_call":
            continue

        tool = llm_output.get("tool")
        arguments = llm_output.get("arguments", {}) or {}

        forbidden_args = FORBIDDEN_TOOL_ARGUMENTS.get(tool, set())

        for forbidden_arg in forbidden_args:
            if forbidden_arg in arguments:
                failures.append(
                    f"Step {step_number}: tool `{tool}` received forbidden "
                    f"LLM argument: `{forbidden_arg}`"
                )

    last_step = trace[-1]
    last_output = last_step.get("llm_output", {})

    if last_output.get("type") != "final_answer":
        failures.append("Last step is not final_answer.")

    if last_step.get("error"):
        failures.append(f"Last step has error: {last_step['error']}")

    return failures


def evaluate_final_state(state: dict, eval_case: dict) -> list[str]:
    failures: list[str] = []

    inspected_files = {
        normalize_path(path)
        for path in state.get("inspected_files", [])
    }

    tools_used = set(state.get("tools_used", []))
    findings = state.get("findings", [])

    # 1. Required files inspected
    for required_file in eval_case["must_inspect_files"]:
        normalized_required_file = normalize_path(required_file)

        if normalized_required_file not in inspected_files:
            failures.append(f"Required file was not inspected: {required_file}")

    # 2. Required tools used
    for required_tool in eval_case["must_use_tools"]:
        if required_tool not in tools_used:
            failures.append(f"Required tool was not used: {required_tool}")

    # 3. Report written
    if not state.get("report_written"):
        failures.append("Report was not written.")

    # 4. Report path exists
    if not state.get("report_path"):
        failures.append("report_path is missing.")

    # 5. Finding required fields + enum validation
    for index, finding in enumerate(findings, start=1):
        missing_fields = [
            field
            for field in REQUIRED_FINDING_FIELDS
            if not finding.get(field)
        ]

        if missing_fields:
            failures.append(
                f"Finding #{index} is missing fields: {missing_fields}"
            )

        severity = finding.get("severity")
        if severity not in ALLOWED_SEVERITIES:
            failures.append(
                f"Finding #{index} has invalid severity: {severity}"
            )

        category = finding.get("category")
        if category not in ALLOWED_CATEGORIES:
            failures.append(
                f"Finding #{index} has invalid category: {category}"
            )

    # 6. Expected findings
    for expected in eval_case["expected_findings"]:
        matched = any(
            finding_matches_expected(finding, expected)
            for finding in findings
        )

        if not matched:
            failures.append(
                "Expected finding not found: "
                f"file={expected['file']}, "
                f"issue_contains={expected['issue_contains']}, "
                f"severity={expected['severity']}, "
                f"category={expected['category']}"
            )

    return failures


def evaluate_run(trace: list[dict], eval_case: dict) -> dict:
    failures: list[str] = []

    try:
        final_state = get_final_state_from_trace(trace)
    except ValueError as error:
        return {
            "passed": False,
            "failure_count": 1,
            "failures": [str(error)],
            "summary": {},
        }

    failures.extend(evaluate_trace_process(trace))
    failures.extend(evaluate_final_state(final_state, eval_case))

    inspected_files = {
        normalize_path(path)
        for path in final_state.get("inspected_files", [])
    }

    tools_used = set(final_state.get("tools_used", []))
    findings = final_state.get("findings", [])

    return {
        "passed": len(failures) == 0,
        "failure_count": len(failures),
        "failures": failures,
        "summary": {
            "steps_count": len(trace),
            "inspected_files_count": len(inspected_files),
            "tools_used": sorted(tools_used),
            "findings_count": len(findings),
            "report_written": final_state.get("report_written"),
            "report_path": final_state.get("report_path"),
            "rejected_final_answer_count": final_state.get(
                "rejected_final_answer_count"
            ),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("trace_path")
    parser.add_argument("eval_case_path")

    args = parser.parse_args()

    trace = load_json(args.trace_path)
    eval_case = load_json(args.eval_case_path)

    result = evaluate_run(trace, eval_case)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()