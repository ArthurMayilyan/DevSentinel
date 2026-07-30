from pathlib import Path

from agent_state import AgentState


def list_files(path: str) -> list[str]:
    base_path = Path(path)

    if not base_path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    if not base_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")

    return [
        str(file)
        for file in base_path.rglob("*")
        if file.is_file()
    ]


def read_file(path: str) -> str:
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    return file_path.read_text(encoding="utf-8")


def search_in_files(query: str, path: str) -> list[dict]:
    base_path = Path(path)

    if not base_path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    results = []

    for file_path in base_path.rglob("*"):
        if not file_path.is_file():
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for line_number, line in enumerate(content.splitlines(), start=1):
            if query in line:
                results.append({
                    "file": str(file_path),
                    "line": line_number,
                    "text": line.strip()
                })

    return results

def render_report_from_state(state: AgentState) -> str:
    lines = []

    lines.append("# Code Review Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")

    findings_count = len(state.findings)

    lines.append(
        f"Reviewed the project and found {findings_count} issue(s)."
    )
    lines.append("")

    if state.inspected_files:
        lines.append("## Inspected Files")
        lines.append("")

        for file in state.inspected_files:
            lines.append(f"- `{file}`")

        lines.append("")

    lines.append("## Findings")
    lines.append("")

    if not state.findings:
        lines.append("No findings were recorded.")
        lines.append("")
    else:
        for index, finding in enumerate(state.findings, start=1):
            lines.append(f"### {index}. {finding['issue']}")
            lines.append("")
            lines.append(f"- **File:** `{finding['file']}`")
            lines.append(f"- **Severity:** {finding['severity']}")
            lines.append(f"- **Category:** {finding['category']}")
            lines.append(f"- **Evidence:** {finding['evidence']}")
            lines.append(f"- **Recommendation:** {finding['recommendation']}")
            lines.append("")

    if state.errors:
        lines.append("## Errors")
        lines.append("")

        for error in state.errors:
            lines.append(f"- {error}")

        lines.append("")

    lines.append("## Overall Recommendation")
    lines.append("")

    if state.findings:
        lines.append(
            "Prioritize HIGH severity findings first, especially security issues "
            "related to authentication, secrets, and access control."
        )
    else:
        lines.append(
            "No issues were recorded by the agent. Review evaluator results to confirm coverage."
        )

    lines.append("")

    return "\n".join(lines)


def write_report(state: AgentState) -> str:
    markdown = render_report_from_state(state)

    report_path = Path("report.md")
    report_path.write_text(markdown, encoding="utf-8")

    state.report_written = True
    state.report_path = str(report_path)

    return str(report_path)