import argparse
import json
from pathlib import Path
from typing import Any

from tool_specs import IssueCategory, IssueSeverity


ALLOWED_SEVERITIES = {item.value for item in IssueSeverity}
ALLOWED_CATEGORIES = {item.value for item in IssueCategory}

FORBIDDEN_TOOL_ARGUMENTS = {
    "write_report": {"state", "markdown"},
}

TOOLS_REQUIRING_EMPTY_ARGUMENTS = {
    "write_report",
}

REQUIRED_FINDING_FIELDS = {
    "file",
    "severity",
    "category",
    "issue",
    "evidence",
    "recommendation",
}

ALLOWED_TOOLS = {
    "list_files",
    "read_file",
    "search_in_files",
    "add_finding",
    "write_report",
}

VALID_LLM_OUTPUT_TYPES = {
    "tool_call",
    "final_answer",
}

TOOL_REQUIRED_ARGUMENTS = {
    "list_files": {"path"},
    "read_file": {"path"},
    "search_in_files": {"query", "path"},
    "add_finding": {
        "file",
        "severity",
        "category",
        "issue",
        "evidence",
        "recommendation",
    },
    "write_report": set(),
}

TOOL_ALLOWED_ARGUMENTS = {
    "list_files": {"path"},
    "read_file": {"path"},
    "search_in_files": {"query", "path"},
    "add_finding": {
        "file",
        "severity",
        "category",
        "issue",
        "evidence",
        "recommendation",
    },
    "write_report": set(),
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

def expected_match_description(expected: dict) -> str:
    if "match_any" in expected:
        return f"match_any={expected['match_any']}"

    if "issue_contains" in expected:
        return f"issue_contains={expected['issue_contains']}"

    return "missing issue_contains/match_any"


def expected_file_description(expected: dict) -> str:
    if "file_any" in expected:
        return f"file_any={expected['file_any']}"

    if "file" in expected:
        return f"file={expected['file']}"

    return "missing file/file_any"

def expected_text_matches(combined_text: str, expected: dict) -> bool:
    if "match_any" in expected:
        return any(
            item.lower() in combined_text
            for item in expected["match_any"]
        )

    if "issue_contains" in expected:
        return expected["issue_contains"].lower() in combined_text

    raise ValueError(
        "Expected finding must contain either 'issue_contains' or 'match_any'."
    )

def evaluate_trace_state_continuity(trace: list[dict]) -> list[str]:
    failures: list[str] = []

    for index in range(1, len(trace)):
        previous_step = trace[index - 1]
        current_step = trace[index]

        previous_step_number = previous_step.get("step")
        current_step_number = current_step.get("step")

        previous_state_after = previous_step.get("state_after")
        current_state_before = current_step.get("state_before")

        if previous_state_after != current_state_before:
            failures.append(
                "Trace state continuity broken: "
                f"step {previous_step_number} state_after does not match "
                f"step {current_step_number} state_before."
            )

    return failures

def evaluate_trace_step_numbers(trace: list[dict]) -> list[str]:
    failures: list[str] = []

    for index, step in enumerate(trace, start=1):
        actual_step_number = step.get("step")

        if actual_step_number != index:
            failures.append(
                f"Trace step numbering is invalid: expected step {index}, "
                f"but got {actual_step_number}."
            )

    return failures

def finding_matches_expected(finding: dict, expected: dict) -> bool:
    finding_file = normalize_path(finding.get("file", ""))
    expected_file = normalize_path(expected["file"])

    combined_text = finding_combined_text(finding)

    return (
        finding_file == expected_file
        and expected_text_matches(combined_text, expected)
        and finding.get("severity") == expected["severity"]
        and finding.get("category") == expected["category"]
    )

def evaluate_trace_process(trace: list[dict], eval_case: dict) -> list[str]:
    failures: list[str] = []

    required_files = {
        normalize_path(path)
        for path in eval_case["must_inspect_files"]
    }

    for step in trace:
        step_number = step.get("step")
        llm_output = step.get("llm_output", {})
        state_before = step.get("state_before", {}) or {}

        output_type = llm_output.get("type")

        if output_type not in VALID_LLM_OUTPUT_TYPES:
            failures.append(
                f"Step {step_number}: invalid LLM output type: `{output_type}`"
            )
            continue

        if output_type == "tool_call":
            tool = llm_output.get("tool")
            arguments = llm_output.get("arguments", {})

            if arguments is None:
                arguments = {}

            if not isinstance(arguments, dict):
                failures.append(
                    f"Step {step_number}: tool_call arguments must be a dict, "
                    f"but got {type(arguments).__name__}."
                )
                continue

            required_args = TOOL_REQUIRED_ARGUMENTS.get(tool)

            if required_args is not None:
                missing_args = [
                    arg
                    for arg in required_args
                    if not arguments.get(arg)
                ]

                if missing_args:
                    failures.append(
                        f"Step {step_number}: tool `{tool}` is missing required "
                        f"arguments: {missing_args}"
                    )

            allowed_args = TOOL_ALLOWED_ARGUMENTS.get(tool)

            if allowed_args is not None:
                unexpected_args = [
                    arg
                    for arg in arguments
                    if arg not in allowed_args
                ]

                if unexpected_args:
                    failures.append(
                        f"Step {step_number}: tool `{tool}` received unexpected "
                        f"arguments: {unexpected_args}"
                    )

            if not tool:
                failures.append(
                    f"Step {step_number}: tool_call is missing tool name."
                )
                continue

            # 0. Not allowed tools
            if tool not in ALLOWED_TOOLS:
                failures.append(
                    f"Step {step_number}: unknown tool called: `{tool}`"
                )

            # 1. Forbidden arguments
            forbidden_args = FORBIDDEN_TOOL_ARGUMENTS.get(tool, set())

            for forbidden_arg in forbidden_args:
                if forbidden_arg in arguments:
                    failures.append(
                        f"Step {step_number}: tool `{tool}` received forbidden "
                        f"LLM argument: `{forbidden_arg}`"
                    )

            # 2. Tools that must receive empty arguments
            if tool in TOOLS_REQUIRING_EMPTY_ARGUMENTS and arguments:
                argument_keys = sorted(arguments.keys())

                failures.append(
                    f"Step {step_number}: tool `{tool}` must be called with empty arguments, "
                    f"but received argument keys: {argument_keys}"
                )

            # 3. add_finding should be called only after reading that file
            if tool == "add_finding":
                finding_file = normalize_path(arguments.get("file", ""))

                inspected_before = {
                    normalize_path(path)
                    for path in state_before.get("inspected_files", [])
                }

                if finding_file and finding_file not in inspected_before:
                    failures.append(
                        f"Step {step_number}: add_finding was called for "
                        f"`{finding_file}` before that file was inspected."
                    )

            # 4. write_report should be called only after all required files inspected
            if tool == "write_report":
                inspected_before = {
                    normalize_path(path)
                    for path in state_before.get("inspected_files", [])
                }

                missing_files = sorted(required_files - inspected_before)

                if missing_files:
                    failures.append(
                        f"Step {step_number}: write_report was called before "
                        f"all required files were inspected. Missing: {missing_files}"
                    )

                if not state_before.get("findings"):
                    failures.append(
                        f"Step {step_number}: write_report was called before "
                        f"any findings were added."
                    )

        elif output_type == "final_answer":
            answer = llm_output.get("answer")

            if not isinstance(answer, str) or not answer.strip():
                failures.append(
                    f"Step {step_number}: final_answer is missing non-empty answer text."
                )

            # 5. final_answer should be allowed only after report was written
            if not state_before.get("report_written"):
                failures.append(
                    f"Step {step_number}: final_answer was produced before "
                    f"report_written=True."
                )

            if not state_before.get("report_path"):
                failures.append(
                    f"Step {step_number}: final_answer was produced before "
                    f"report_path was set."
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
                f"{expected_file_description(expected)}, "
                f"{expected_match_description(expected)}, "
                f"severity={expected['severity']}, "
                f"category={expected['category']}"
            )

    return failures


def render_eval_report(result: dict, trace_path: str, eval_case_path: str) -> str:
    lines = []

    status = "PASSED" if result["passed"] else "FAILED"

    lines.append("# Evaluation Report")
    lines.append("")
    lines.append(f"Status: **{status}**")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"- Trace: `{trace_path}`")
    lines.append(f"- Eval case: `{eval_case_path}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")

    summary = result.get("summary", {})

    for key, value in summary.items():
        lines.append(f"- **{key}:** {value}")

    lines.append("")
    lines.append("## Failures")
    lines.append("")

    failures = result.get("failures", [])

    if not failures:
        lines.append("No failures.")
    else:
        for index, failure in enumerate(failures, start=1):
            lines.append(f"{index}. {failure}")

    lines.append("")

    return "\n".join(lines)

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

    failures.extend(evaluate_trace_step_numbers(trace))
    failures.extend(evaluate_trace_state_continuity(trace))
    failures.extend(evaluate_trace_process(trace, eval_case))
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

def render_eval_report(result: dict, trace_path: str, eval_case_path: str) -> str:
    lines = []

    status = "PASSED" if result["passed"] else "FAILED"

    lines.append("# Evaluation Report")
    lines.append("")
    lines.append(f"Status: **{status}**")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"- **Trace:** `{trace_path}`")
    lines.append(f"- **Eval case:** `{eval_case_path}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")

    summary = result.get("summary", {})

    if summary:
        for key, value in summary.items():
            lines.append(f"- **{key}:** {value}")
    else:
        lines.append("No summary available.")

    lines.append("")
    lines.append("## Failures")
    lines.append("")

    failures = result.get("failures", [])

    if failures:
        for index, failure in enumerate(failures, start=1):
            lines.append(f"{index}. {failure}")
    else:
        lines.append("No failures.")

    lines.append("")

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "trace_path",
        nargs="?",
        default="traces/trace_20260730_161818.json",
        help="Path to trace JSON file."
    )

    parser.add_argument(
        "eval_case_path",
        nargs="?",
        default="eval_cases/security_review_eval.json",
        help="Path to eval case JSON file."
    )

    parser.add_argument(
        "--report",
        default=None,
        help="Optional path to write markdown evaluation report."
    )

    args = parser.parse_args()

    trace = load_json(args.trace_path)
    eval_case = load_json(args.eval_case_path)

    result = evaluate_run(trace, eval_case)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.report:
        markdown_report = render_eval_report(
            result=result,
            trace_path=args.trace_path,
            eval_case_path=args.eval_case_path,
        )

        Path(args.report).write_text(markdown_report, encoding="utf-8")

        print(f"\nEvaluation report written to: {args.report}")

if __name__ == "__main__":
    main()