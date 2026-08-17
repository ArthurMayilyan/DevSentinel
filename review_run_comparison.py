import html
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from finding_types import (
    FINDING_TYPE_SECURITY_OTHER,
    normalize_finding_type,
)
from app_settings import get_app_settings


@dataclass(frozen=True)
class ReviewRunComparison:
    comparison_id: str
    old_run_dir: str
    new_run_dir: str
    old_run_id: str
    new_run_id: str
    new_findings: list[dict[str, Any]]
    resolved_findings: list[dict[str, Any]]
    unchanged_findings: list[dict[str, Any]]
    severity_changes: list[dict[str, Any]]
    comparison_dir: str
    comparison_json_path: str
    comparison_markdown_path: str
    comparison_html_path: str
    summary: str


def review_run_comparison_to_dict(
    result: ReviewRunComparison,
) -> dict[str, Any]:
    return asdict(
        result,
    )


def read_json_file(
    path: Path,
) -> Any:
    if not path.exists():
        raise ValueError(
            f"Required review artifact does not exist: {path}"
        )

    try:
        return json.loads(
            path.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON artifact: {path}"
        ) from exc


def load_review_run(
    run_dir: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    resolved_run_dir = Path(
        run_dir,
    ).expanduser().resolve()

    if not resolved_run_dir.exists():
        raise ValueError(
            f"Review run directory does not exist: {resolved_run_dir}"
        )

    if not resolved_run_dir.is_dir():
        raise ValueError(
            f"Review run path must be a directory: {resolved_run_dir}"
        )

    summary = read_json_file(
        resolved_run_dir / "summary.json",
    )

    findings = read_json_file(
        resolved_run_dir / "findings.json",
    )

    if not isinstance(
        summary,
        dict,
    ):
        raise ValueError(
            f"summary.json must contain an object: {resolved_run_dir}"
        )

    if not isinstance(
        findings,
        list,
    ):
        raise ValueError(
            f"findings.json must contain a list: {resolved_run_dir}"
        )

    return summary, findings


def normalized_file_name(
    value: str,
) -> str:
    return Path(
        value,
    ).name.lower()


def finding_identity(
    finding: dict[str, Any],
) -> tuple[str, str]:
    file_identity = normalized_file_name(
        str(
            finding.get(
                "file",
                "",
            )
        )
    )

    finding_type = normalize_finding_type(
        str(
            finding.get(
                "finding_type",
                "",
            )
        ),
        issue=str(
            finding.get(
                "issue",
                "",
            )
        ),
        evidence=str(
            finding.get(
                "evidence",
                "",
            )
        ),
    )

    if finding_type != FINDING_TYPE_SECURITY_OTHER:
        return (
            file_identity,
            finding_type,
        )

    category = str(
        finding.get(
            "category",
            "",
        )
    ).upper()

    issue = str(
        finding.get(
            "issue",
            "",
        )
    ).strip().lower()

    return (
        file_identity,
        f"legacy:{category}:{issue}",
    )


def build_findings_map(
    findings: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        finding_identity(
            finding,
        ): finding
        for finding in findings
        if isinstance(
            finding,
            dict,
        )
    }


def compare_findings(
    *,
    old_findings: list[dict[str, Any]],
    new_findings: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    old_map = build_findings_map(
        old_findings,
    )

    new_map = build_findings_map(
        new_findings,
    )

    old_keys = set(
        old_map,
    )

    new_keys = set(
        new_map,
    )

    new_items = [
        new_map[key]
        for key in sorted(
            new_keys - old_keys,
        )
    ]

    resolved_items = [
        old_map[key]
        for key in sorted(
            old_keys - new_keys,
        )
    ]

    unchanged_items = []
    severity_changes = []

    for key in sorted(
        old_keys & new_keys,
    ):
        old_finding = old_map[key]
        new_finding = new_map[key]

        old_severity = str(
            old_finding.get(
                "severity",
                "",
            )
        ).upper()

        new_severity = str(
            new_finding.get(
                "severity",
                "",
            )
        ).upper()

        if old_severity != new_severity:
            severity_changes.append(
                {
                    "finding_type": normalize_finding_type(
                        str(
                            new_finding.get(
                                "finding_type",
                                "",
                            )
                        ),
                        issue=str(
                            new_finding.get(
                                "issue",
                                "",
                            )
                        ),
                        evidence=str(
                            new_finding.get(
                                "evidence",
                                "",
                            )
                        ),
                    ),
                    "file": new_finding.get(
                        "file",
                        "",
                    ),
                    "category": new_finding.get(
                        "category",
                        "",
                    ),
                    "issue": new_finding.get(
                        "issue",
                        "",
                    ),
                    "old_severity": old_severity,
                    "new_severity": new_severity,
                }
            )
        else:
            unchanged_items.append(
                new_finding,
            )

    return (
        new_items,
        resolved_items,
        unchanged_items,
        severity_changes,
    )


def build_comparison_summary(
    *,
    new_findings_count: int,
    resolved_findings_count: int,
    unchanged_findings_count: int,
    severity_changes_count: int,
) -> str:
    return (
        "Review comparison completed. "
        f"New: {new_findings_count}, "
        f"resolved: {resolved_findings_count}, "
        f"unchanged: {unchanged_findings_count}, "
        f"severity changes: {severity_changes_count}."
    )


def render_findings_markdown(
    *,
    title: str,
    findings: list[dict[str, Any]],
) -> str:
    lines = [
        f"## {title}",
        "",
    ]

    if not findings:
        lines.extend(
            [
                "None.",
                "",
            ]
        )

        return "\n".join(
            lines,
        )

    for finding in findings:
        lines.extend(
            [
                f"### {finding.get('issue', '')}",
                "",
                f"- **File:** `{finding.get('file', '')}`",
                f"- **Severity:** {finding.get('severity', '')}",
                f"- **Category:** {finding.get('category', '')}",
                f"- **Evidence:** {finding.get('evidence', '')}",
                f"- **Recommendation:** {finding.get('recommendation', '')}",
                "",
            ]
        )

    return "\n".join(
        lines,
    )


def render_comparison_markdown(
    *,
    comparison_id: str,
    old_run_id: str,
    new_run_id: str,
    summary: str,
    new_findings: list[dict[str, Any]],
    resolved_findings: list[dict[str, Any]],
    unchanged_findings: list[dict[str, Any]],
    severity_changes: list[dict[str, Any]],
) -> str:
    parts = [
        "# AgentLoop Review Comparison",
        "",
        f"- **Comparison:** `{comparison_id}`",
        f"- **Old run:** `{old_run_id}`",
        f"- **New run:** `{new_run_id}`",
        "",
        "## Summary",
        "",
        summary,
        "",
        render_findings_markdown(
            title="New Findings",
            findings=new_findings,
        ),
        render_findings_markdown(
            title="Resolved Findings",
            findings=resolved_findings,
        ),
        render_findings_markdown(
            title="Unchanged Findings",
            findings=unchanged_findings,
        ),
        "## Severity Changes",
        "",
    ]

    if not severity_changes:
        parts.extend(
            [
                "None.",
                "",
            ]
        )
    else:
        for item in severity_changes:
            parts.extend(
                [
                    f"### {item.get('issue', '')}",
                    "",
                    f"- **File:** `{item.get('file', '')}`",
                    f"- **Category:** {item.get('category', '')}",
                    f"- **Old severity:** {item.get('old_severity', '')}",
                    f"- **New severity:** {item.get('new_severity', '')}",
                    "",
                ]
            )

    return "\n".join(
        parts,
    )


def render_comparison_html(
    *,
    old_run_id: str,
    new_run_id: str,
    summary: str,
    new_findings: list[dict[str, Any]],
    resolved_findings: list[dict[str, Any]],
    unchanged_findings: list[dict[str, Any]],
    severity_changes: list[dict[str, Any]],
) -> str:
    def render_table_rows(
        findings: list[dict[str, Any]],
    ) -> str:
        if not findings:
            return '<tr><td colspan="4">None</td></tr>'

        rows = []

        for finding in findings:
            rows.append(
                "<tr>"
                f"<td>{html.escape(str(finding.get('file', '')))}</td>"
                f"<td>{html.escape(str(finding.get('severity', '')))}</td>"
                f"<td>{html.escape(str(finding.get('category', '')))}</td>"
                f"<td>{html.escape(str(finding.get('issue', '')))}</td>"
                "</tr>"
            )

        return "\n".join(
            rows,
        )

    severity_rows = []

    for item in severity_changes:
        severity_rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('file', '')))}</td>"
            f"<td>{html.escape(str(item.get('issue', '')))}</td>"
            f"<td>{html.escape(str(item.get('old_severity', '')))}</td>"
            f"<td>{html.escape(str(item.get('new_severity', '')))}</td>"
            "</tr>"
        )

    if not severity_rows:
        severity_rows.append(
            '<tr><td colspan="4">None</td></tr>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>AgentLoop Review Comparison</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            line-height: 1.5;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }}

        th, td {{
            border: 1px solid #ccc;
            padding: 8px;
            text-align: left;
            vertical-align: top;
        }}

        th {{
            background: #f3f3f3;
        }}
    </style>
</head>
<body>
    <h1>AgentLoop Review Comparison</h1>

    <p><strong>Old run:</strong> {html.escape(old_run_id)}</p>
    <p><strong>New run:</strong> {html.escape(new_run_id)}</p>

    <h2>Summary</h2>
    <p>{html.escape(summary)}</p>

    <h2>New Findings</h2>
    <table>
        <tr><th>File</th><th>Severity</th><th>Category</th><th>Issue</th></tr>
        {render_table_rows(new_findings)}
    </table>

    <h2>Resolved Findings</h2>
    <table>
        <tr><th>File</th><th>Severity</th><th>Category</th><th>Issue</th></tr>
        {render_table_rows(resolved_findings)}
    </table>

    <h2>Unchanged Findings</h2>
    <table>
        <tr><th>File</th><th>Severity</th><th>Category</th><th>Issue</th></tr>
        {render_table_rows(unchanged_findings)}
    </table>

    <h2>Severity Changes</h2>
    <table>
        <tr><th>File</th><th>Issue</th><th>Old</th><th>New</th></tr>
        {''.join(severity_rows)}
    </table>
</body>
</html>
"""


def compare_review_runs(
    *,
    old_run_dir: str,
    new_run_dir: str,
    comparisons_dir: str = "",
) -> ReviewRunComparison:
    old_summary, old_findings = load_review_run(
        old_run_dir,
    )

    new_summary, new_findings = load_review_run(
        new_run_dir,
    )

    (
        added,
        resolved,
        unchanged,
        severity_changes,
    ) = compare_findings(
        old_findings=old_findings,
        new_findings=new_findings,
    )

    old_run_id = str(
        old_summary.get(
            "run_id",
            Path(
                old_run_dir,
            ).name,
        )
    )

    new_run_id = str(
        new_summary.get(
            "run_id",
            Path(
                new_run_dir,
            ).name,
        )
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f",
    )

    comparison_id = (
        f"{timestamp}_{old_run_id}_vs_{new_run_id}"
    )

    if comparisons_dir:
        root = Path(
            comparisons_dir,
        ).expanduser().resolve()
    else:
        settings = get_app_settings()

        root = (
            Path(
                new_run_dir,
            )
            .expanduser()
            .resolve()
            .parent
            / settings.artifacts.comparisons_dir_name
        )

    root.mkdir(
        parents=True,
        exist_ok=True,
    )

    comparison_dir = root / comparison_id

    comparison_dir.mkdir(
        parents=True,
        exist_ok=False,
    )

    summary = build_comparison_summary(
        new_findings_count=len(
            added,
        ),
        resolved_findings_count=len(
            resolved,
        ),
        unchanged_findings_count=len(
            unchanged,
        ),
        severity_changes_count=len(
            severity_changes,
        ),
    )

    comparison_json_path = comparison_dir / "comparison.json"
    comparison_markdown_path = comparison_dir / "comparison.md"
    comparison_html_path = comparison_dir / "comparison.html"

    json_payload = {
        "comparison_id": comparison_id,
        "old_run_id": old_run_id,
        "new_run_id": new_run_id,
        "summary": summary,
        "new_findings": added,
        "resolved_findings": resolved,
        "unchanged_findings": unchanged,
        "severity_changes": severity_changes,
    }

    comparison_json_path.write_text(
        json.dumps(
            json_payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    comparison_markdown_path.write_text(
        render_comparison_markdown(
            comparison_id=comparison_id,
            old_run_id=old_run_id,
            new_run_id=new_run_id,
            summary=summary,
            new_findings=added,
            resolved_findings=resolved,
            unchanged_findings=unchanged,
            severity_changes=severity_changes,
        ),
        encoding="utf-8",
    )

    comparison_html_path.write_text(
        render_comparison_html(
            old_run_id=old_run_id,
            new_run_id=new_run_id,
            summary=summary,
            new_findings=added,
            resolved_findings=resolved,
            unchanged_findings=unchanged,
            severity_changes=severity_changes,
        ),
        encoding="utf-8",
    )

    return ReviewRunComparison(
        comparison_id=comparison_id,
        old_run_dir=str(
            Path(
                old_run_dir,
            ).resolve(),
        ),
        new_run_dir=str(
            Path(
                new_run_dir,
            ).resolve(),
        ),
        old_run_id=old_run_id,
        new_run_id=new_run_id,
        new_findings=added,
        resolved_findings=resolved,
        unchanged_findings=unchanged,
        severity_changes=severity_changes,
        comparison_dir=str(
            comparison_dir,
        ),
        comparison_json_path=str(
            comparison_json_path,
        ),
        comparison_markdown_path=str(
            comparison_markdown_path,
        ),
        comparison_html_path=str(
            comparison_html_path,
        ),
        summary=summary,
    )