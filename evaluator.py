import json
from pathlib import Path
from typing import Any

from tool_specs import IssueCategory, IssueSeverity


ALLOWED_SEVERITIES = {item.value for item in IssueSeverity}
ALLOWED_CATEGORIES = {item.value for item in IssueCategory}


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


def evaluate_run(state: dict, eval_case: dict) -> dict:
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

    # 4. Report path exists in state
    if not state.get("report_path"):
        failures.append("report_path is missing.")

    # 5. Finding required fields
    required_finding_fields = {
        "file",
        "severity",
        "category",
        "issue",
        "evidence",
        "recommendation",
    }

    for index, finding in enumerate(findings, start=1):
        missing_fields = [
            field
            for field in required_finding_fields
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
        expected_file = normalize_path(expected["file"])
        expected_issue_contains = expected["issue_contains"].lower()
        expected_severity = expected["severity"]
        expected_category = expected["category"]

        matched = False

        for finding in findings:
            finding_file = normalize_path(finding.get("file", ""))
            finding_issue = finding.get("issue", "").lower()
            finding_severity = finding.get("severity")
            finding_category = finding.get("category")

            if (
                finding_file == expected_file
                and expected_issue_contains in finding_issue
                and finding_severity == expected_severity
                and finding_category == expected_category
            ):
                matched = True
                break

        if not matched:
            failures.append(
                "Expected finding not found: "
                f"file={expected['file']}, "
                f"issue_contains={expected['issue_contains']}, "
                f"severity={expected['severity']}, "
                f"category={expected['category']}"
            )

    return {
        "passed": len(failures) == 0,
        "failure_count": len(failures),
        "failures": failures,
        "summary": {
            "inspected_files_count": len(inspected_files),
            "tools_used": sorted(tools_used),
            "findings_count": len(findings),
            "report_written": state.get("report_written"),
            "report_path": state.get("report_path"),
        },
    }


def main():
    trace = load_json("traces/trace_20260708_161150.json")
    eval_case = load_json("eval_cases/security_review_eval.json")

    final_state = get_final_state_from_trace(trace)
    result = evaluate_run(final_state, eval_case)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()