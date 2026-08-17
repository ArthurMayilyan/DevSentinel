import html
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReviewRunArtifacts:
    run_id: str
    created_at: str
    run_dir: str
    report_markdown_path: str
    report_html_path: str
    summary_json_path: str
    findings_json_path: str
    reviewed_files_json_path: str
    run_config_json_path: str
    history_path: str


def review_run_artifacts_to_dict(
    artifacts: ReviewRunArtifacts,
) -> dict[str, Any]:
    return asdict(
        artifacts,
    )


def slugify(
    value: str,
) -> str:
    normalized = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        value.strip(),
    )

    normalized = normalized.strip(
        "_",
    )

    return normalized or "review"


def build_review_run_id(
    *,
    project_path: str,
    profile: str,
    reviewer: str,
    now: datetime | None = None,
) -> str:
    current_time = now or datetime.now()

    timestamp = current_time.strftime(
        "%Y%m%d_%H%M%S_%f",
    )

    project_name = Path(
        project_path,
    ).name or "project"

    return "_".join(
        [
            timestamp,
            slugify(
                project_name,
            ),
            slugify(
                profile,
            ),
            slugify(
                reviewer,
            ),
        ]
    )


def write_json(
    *,
    path: Path,
    value: Any,
) -> None:
    path.write_text(
        json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def build_findings_html(
    findings: list[dict[str, Any]],
) -> str:
    if not findings:
        return """
        <tr>
            <td colspan="6">No findings were recorded.</td>
        </tr>
        """

    rows = []

    for finding in findings:
        rows.append(
            f"""
            <tr>
                <td>{html.escape(str(finding.get("file", "")))}</td>
                <td>{html.escape(str(finding.get("severity", "")))}</td>
                <td>{html.escape(str(finding.get("category", "")))}</td>
                <td>{html.escape(str(finding.get("issue", "")))}</td>
                <td>{html.escape(str(finding.get("evidence", "")))}</td>
                <td>{html.escape(str(finding.get("recommendation", "")))}</td>
            </tr>
            """
        )

    return "\n".join(
        rows,
    )


def render_review_html(
    *,
    project_path: str,
    profile: str,
    reviewer: str,
    model: str,
    summary: str,
    findings: list[dict[str, Any]],
    selected_files_count: int,
    skipped_files_count: int,
    created_at: str,
) -> str:
    findings_html = build_findings_html(
        findings,
    )

    model_display = model or "N/A"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>AgentLoop Review Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            line-height: 1.5;
            color: #222;
        }}

        h1, h2 {{
            margin-bottom: 12px;
        }}

        .metadata {{
            margin-bottom: 28px;
        }}

        .metadata dt {{
            font-weight: bold;
        }}

        .metadata dd {{
            margin-bottom: 8px;
        }}

        .summary {{
            padding: 16px;
            border: 1px solid #ccc;
            border-radius: 8px;
            margin-bottom: 28px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th, td {{
            border: 1px solid #ccc;
            padding: 8px;
            vertical-align: top;
            text-align: left;
        }}

        th {{
            background: #f3f3f3;
        }}
    </style>
</head>
<body>
    <h1>AgentLoop Review Report</h1>

    <dl class="metadata">
        <dt>Created</dt>
        <dd>{html.escape(created_at)}</dd>

        <dt>Project</dt>
        <dd>{html.escape(project_path)}</dd>

        <dt>Profile</dt>
        <dd>{html.escape(profile)}</dd>

        <dt>Reviewer</dt>
        <dd>{html.escape(reviewer)}</dd>

        <dt>Model</dt>
        <dd>{html.escape(model_display)}</dd>

        <dt>Selected files</dt>
        <dd>{selected_files_count}</dd>

        <dt>Skipped files</dt>
        <dd>{skipped_files_count}</dd>

        <dt>Findings</dt>
        <dd>{len(findings)}</dd>
    </dl>

    <h2>Summary</h2>

    <div class="summary">
        {html.escape(summary)}
    </div>

    <h2>Findings</h2>

    <table>
        <thead>
            <tr>
                <th>File</th>
                <th>Severity</th>
                <th>Category</th>
                <th>Issue</th>
                <th>Evidence</th>
                <th>Recommendation</th>
            </tr>
        </thead>
        <tbody>
            {findings_html}
        </tbody>
    </table>
</body>
</html>
"""


def read_history(
    *,
    history_path: Path,
) -> list[dict[str, Any]]:
    if not history_path.exists():
        return []

    try:
        value = json.loads(
            history_path.read_text(
                encoding="utf-8",
            )
        )
    except (
        json.JSONDecodeError,
        OSError,
    ):
        return []

    if not isinstance(
        value,
        list,
    ):
        return []

    return [
        item
        for item in value
        if isinstance(
            item,
            dict,
        )
    ]


def update_review_history(
    *,
    history_path: Path,
    entry: dict[str, Any],
) -> None:
    history = read_history(
        history_path=history_path,
    )

    history.append(
        entry,
    )

    write_json(
        path=history_path,
        value=history,
    )


def create_review_run_package(
    *,
    reviews_dir: str,
    project_path: str,
    profile: str,
    reviewer: str,
    model: str,
    status: str,
    summary: str,
    findings: list[dict[str, Any]],
    selected_files: list[str],
    skipped_files: list[str],
    scope: dict[str, Any],
    source_report_path: str,
    run_config: dict[str, Any],
) -> ReviewRunArtifacts:
    reviews_root = Path(
        reviews_dir,
    ).expanduser().resolve()

    reviews_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    created_at_value = datetime.now()
    created_at = created_at_value.astimezone().isoformat()

    run_id = build_review_run_id(
        project_path=project_path,
        profile=profile,
        reviewer=reviewer,
        now=created_at_value,
    )

    run_dir = reviews_root / run_id

    run_dir.mkdir(
        parents=True,
        exist_ok=False,
    )

    report_markdown_path = run_dir / "report.md"
    report_html_path = run_dir / "report.html"
    summary_json_path = run_dir / "summary.json"
    findings_json_path = run_dir / "findings.json"
    reviewed_files_json_path = run_dir / "reviewed_files.json"
    run_config_json_path = run_dir / "run_config.json"
    history_path = reviews_root / "history.json"

    source_report = Path(
        source_report_path,
    )

    if source_report.exists():
        report_markdown = source_report.read_text(
            encoding="utf-8",
        )
    else:
        report_markdown = (
            "# AgentLoop Review Report\n\n"
            f"{summary}\n"
        )

    report_markdown_path.write_text(
        report_markdown,
        encoding="utf-8",
    )

    report_html_path.write_text(
        render_review_html(
            project_path=project_path,
            profile=profile,
            reviewer=reviewer,
            model=model,
            summary=summary,
            findings=findings,
            selected_files_count=len(
                selected_files,
            ),
            skipped_files_count=len(
                skipped_files,
            ),
            created_at=created_at,
        ),
        encoding="utf-8",
    )

    summary_payload = {
        "run_id": run_id,
        "created_at": created_at,
        "status": status,
        "project_path": project_path,
        "profile": profile,
        "reviewer": reviewer,
        "model": model,
        "selected_files_count": len(
            selected_files,
        ),
        "skipped_files_count": len(
            skipped_files,
        ),
        "findings_count": len(
            findings,
        ),
        "summary": summary,
    }

    write_json(
        path=summary_json_path,
        value=summary_payload,
    )

    write_json(
        path=findings_json_path,
        value=findings,
    )

    write_json(
        path=reviewed_files_json_path,
        value={
            "selected_files": selected_files,
            "skipped_files": skipped_files,
            "scope": scope,
        },
    )

    write_json(
        path=run_config_json_path,
        value=run_config,
    )

    history_entry = {
        "run_id": run_id,
        "created_at": created_at,
        "project_path": project_path,
        "profile": profile,
        "reviewer": reviewer,
        "model": model,
        "findings_count": len(
            findings,
        ),
        "run_dir": str(
            run_dir,
        ),
        "report_html_path": str(
            report_html_path,
        ),
    }

    update_review_history(
        history_path=history_path,
        entry=history_entry,
    )

    return ReviewRunArtifacts(
        run_id=run_id,
        created_at=created_at,
        run_dir=str(
            run_dir,
        ),
        report_markdown_path=str(
            report_markdown_path,
        ),
        report_html_path=str(
            report_html_path,
        ),
        summary_json_path=str(
            summary_json_path,
        ),
        findings_json_path=str(
            findings_json_path,
        ),
        reviewed_files_json_path=str(
            reviewed_files_json_path,
        ),
        run_config_json_path=str(
            run_config_json_path,
        ),
        history_path=str(
            history_path,
        ),
    )