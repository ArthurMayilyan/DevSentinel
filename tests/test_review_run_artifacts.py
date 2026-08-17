import json
from datetime import datetime
from pathlib import Path

from review_run_artifacts import (
    build_review_run_id,
    create_review_run_package,
)


def test_build_review_run_id_contains_project_profile_and_reviewer():
    run_id = build_review_run_id(
        project_path="D:/Projects/sample_project",
        profile="security",
        reviewer="openai",
        now=datetime(
            2026,
            8,
            16,
            17,
            45,
            30,
            123456,
        ),
    )

    assert run_id == (
        "20260816_174530_123456_"
        "sample_project_security_openai"
    )


def test_create_review_run_package_writes_all_artifacts(tmp_path):
    source_report_path = tmp_path / "source_report.md"

    source_report_path.write_text(
        "# Code Review Report\n\nTest report.",
        encoding="utf-8",
    )

    reviews_dir = tmp_path / "reviews"

    findings = [
        {
            "file": "app.py",
            "severity": "HIGH",
            "category": "SECURITY",
            "issue": "Hardcoded credential risk.",
            "evidence": 'PASSWORD = "secret"',
            "recommendation": "Move credentials to secure configuration.",
        }
    ]

    artifacts = create_review_run_package(
        reviews_dir=str(
            reviews_dir,
        ),
        project_path=str(
            tmp_path / "sample_project",
        ),
        profile="security",
        reviewer="openai",
        model="gpt-5.6-luna",
        status="completed",
        summary="Security review completed.",
        findings=findings,
        selected_files=[
            "app.py",
        ],
        skipped_files=[
            "README.md",
        ],
        scope={
            "include_globs": [
                "**/*.py",
            ]
        },
        source_report_path=str(
            source_report_path,
        ),
        run_config={
            "reviewer": "openai",
            "model": "gpt-5.6-luna",
        },
    )

    assert Path(
        artifacts.run_dir,
    ).exists()

    assert Path(
        artifacts.report_markdown_path,
    ).exists()

    assert Path(
        artifacts.report_html_path,
    ).exists()

    assert Path(
        artifacts.summary_json_path,
    ).exists()

    assert Path(
        artifacts.findings_json_path,
    ).exists()

    assert Path(
        artifacts.reviewed_files_json_path,
    ).exists()

    assert Path(
        artifacts.run_config_json_path,
    ).exists()

    assert Path(
        artifacts.history_path,
    ).exists()

    html_content = Path(
        artifacts.report_html_path,
    ).read_text(
        encoding="utf-8",
    )

    assert "AgentLoop Review Report" in html_content
    assert "Hardcoded credential risk." in html_content
    assert "gpt-5.6-luna" in html_content

    findings_payload = json.loads(
        Path(
            artifacts.findings_json_path,
        ).read_text(
            encoding="utf-8",
        )
    )

    assert findings_payload == findings

    history_payload = json.loads(
        Path(
            artifacts.history_path,
        ).read_text(
            encoding="utf-8",
        )
    )

    assert len(
        history_payload,
    ) == 1

    assert history_payload[0]["run_id"] == artifacts.run_id
    assert history_payload[0]["reviewer"] == "openai"