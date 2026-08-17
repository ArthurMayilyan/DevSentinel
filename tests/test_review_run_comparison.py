import json
from pathlib import Path

from review_run_comparison import (
    compare_findings,
    compare_review_runs,
)


def make_finding(
    *,
    file: str,
    issue: str,
    severity: str,
) -> dict:
    return {
        "file": file,
        "severity": severity,
        "category": "SECURITY",
        "issue": issue,
        "evidence": f"Evidence for {issue}",
        "recommendation": f"Fix {issue}",
    }


def create_run(
    *,
    root: Path,
    run_id: str,
    findings: list[dict],
) -> Path:
    run_dir = root / run_id

    run_dir.mkdir(
        parents=True,
    )

    (run_dir / "summary.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "status": "completed",
            }
        ),
        encoding="utf-8",
    )

    (run_dir / "findings.json").write_text(
        json.dumps(
            findings,
        ),
        encoding="utf-8",
    )

    return run_dir


def test_compare_findings_detects_new_resolved_unchanged_and_severity_change():
    old_findings = [
        make_finding(
            file="app.py",
            issue="Old issue",
            severity="HIGH",
        ),
        make_finding(
            file="auth.py",
            issue="Shared issue",
            severity="HIGH",
        ),
        make_finding(
            file="config.py",
            issue="Severity issue",
            severity="HIGH",
        ),
    ]

    new_findings = [
        make_finding(
            file="auth.py",
            issue="Shared issue",
            severity="HIGH",
        ),
        make_finding(
            file="config.py",
            issue="Severity issue",
            severity="CRITICAL",
        ),
        make_finding(
            file="new.py",
            issue="New issue",
            severity="MEDIUM",
        ),
    ]

    (
        added,
        resolved,
        unchanged,
        severity_changes,
    ) = compare_findings(
        old_findings=old_findings,
        new_findings=new_findings,
    )

    assert len(
        added,
    ) == 1

    assert added[0]["issue"] == "New issue"

    assert len(
        resolved,
    ) == 1

    assert resolved[0]["issue"] == "Old issue"

    assert len(
        unchanged,
    ) == 1

    assert unchanged[0]["issue"] == "Shared issue"

    assert severity_changes == [
        {
            "file": "config.py",
            "category": "SECURITY",
            "issue": "Severity issue",
            "old_severity": "HIGH",
            "new_severity": "CRITICAL",
        }
    ]


def test_compare_review_runs_creates_comparison_artifacts(tmp_path):
    old_run = create_run(
        root=tmp_path,
        run_id="old_run",
        findings=[
            make_finding(
                file="app.py",
                issue="Old issue",
                severity="HIGH",
            )
        ],
    )

    new_run = create_run(
        root=tmp_path,
        run_id="new_run",
        findings=[
            make_finding(
                file="app.py",
                issue="New issue",
                severity="CRITICAL",
            )
        ],
    )

    result = compare_review_runs(
        old_run_dir=str(
            old_run,
        ),
        new_run_dir=str(
            new_run,
        ),
    )

    assert result.old_run_id == "old_run"
    assert result.new_run_id == "new_run"

    assert len(
        result.new_findings,
    ) == 1

    assert len(
        result.resolved_findings,
    ) == 1

    assert Path(
        result.comparison_json_path,
    ).exists()

    assert Path(
        result.comparison_markdown_path,
    ).exists()

    assert Path(
        result.comparison_html_path,
    ).exists()

    assert "New: 1" in result.summary
    assert "resolved: 1" in result.summary