from pathlib import Path

from mcp_server_context import build_agent_loop_mcp_context
from review_project_workflow import (
    detect_security_findings_for_file,
    review_project,
    review_project_result_to_dict,
)


def create_security_project(tmp_path):
    project_path = tmp_path / "project"
    project_path.mkdir()

    config_path = project_path / "config.py"
    config_path.write_text(
        'SECRET_KEY = "dev-secret"\nDEBUG = True\n',
        encoding="utf-8",
    )

    auth_path = project_path / "auth.py"
    auth_path.write_text(
        '''
def create_token(user):
    token = "token-" + user
    return token

def verify_token(token):
    return bool(token)

def login(username, password):
    if username == "admin" and password == "admin":
        return create_token(username)
    return None
''',
        encoding="utf-8",
    )

    app_path = project_path / "app.py"
    app_path.write_text(
        '''
from config import DEBUG

def health():
    return {"ok": True, "debug": DEBUG}
''',
        encoding="utf-8",
    )

    return project_path


def test_detect_security_findings_for_file_detects_secret_key_and_debug():
    findings = detect_security_findings_for_file(
        file_path="config.py",
        content='SECRET_KEY = "dev-secret"\nDEBUG = True\n',
    )

    issues = [
        finding["issue"]
        for finding in findings
    ]

    assert "Hardcoded SECRET_KEY." in issues
    assert "Debug mode enabled." in issues


def test_review_project_runs_security_workflow_and_writes_report(tmp_path):
    project_path = create_security_project(
        tmp_path,
    )

    report_path = tmp_path / "review.md"

    context = build_agent_loop_mcp_context(
        report_path=str(
            report_path,
        )
    )

    result = review_project(
        context=context,
        project_path=str(
            project_path,
        ),
        profile="security",
    )

    assert result.status == "completed"
    assert result.profile == "security"
    assert result.inspected_files_count == 3
    assert result.findings_count >= 5
    assert result.report_path == str(
        report_path,
    )
    assert "review completed" in result.summary
    assert report_path.exists()

    report = report_path.read_text(
        encoding="utf-8",
    )

    assert "Hardcoded SECRET_KEY." in report
    assert "Hardcoded admin credentials." in report
    assert "Token validation is incomplete." in report


def test_review_project_result_to_dict_serializes_result(tmp_path):
    project_path = create_security_project(
        tmp_path,
    )

    report_path = tmp_path / "review.md"

    context = build_agent_loop_mcp_context(
        report_path=str(
            report_path,
        )
    )

    result = review_project(
        context=context,
        project_path=str(
            project_path,
        ),
        profile="security",
    )

    payload = review_project_result_to_dict(
        result,
    )

    assert payload["status"] == "completed"
    assert payload["profile"] == "security"
    assert payload["report_path"] == str(
        report_path,
    )


def test_review_project_supports_report_dir_and_scope_options(tmp_path):
    project_path = create_security_project(
        tmp_path,
    )

    report_dir = tmp_path / "reviews"

    context = build_agent_loop_mcp_context()

    result = review_project(
        context=context,
        project_path=str(
            project_path,
        ),
        profile="security",
        report_dir=str(
            report_dir,
        ),
        allowed_root=str(
            tmp_path,
        ),
        include_globs="**/*.py",
        max_files=2,
        max_file_size_bytes=200_000,
    )

    assert result.status == "completed"
    assert result.selected_files_count == 2
    assert result.skipped_files_count >= 1
    assert result.scope["include_globs"] == [
        "**/*.py",
    ]
    assert result.scope["max_files"] == 2
    assert result.report_path.startswith(
        str(
            report_dir.resolve(),
        )
    )
    assert result.report_path.endswith(
        ".md",
    )    

def test_review_project_creates_review_run_package(tmp_path):
    project_path = create_security_project(
        tmp_path,
    )

    source_report_path = tmp_path / "source_report.md"
    reviews_dir = tmp_path / "reviews"

    context = build_agent_loop_mcp_context(
        report_path=str(
            source_report_path,
        )
    )

    result = review_project(
        context=context,
        project_path=str(
            project_path,
        ),
        profile="security",
        include_globs="**/*.py",
        reviewer="deterministic",
        reviews_dir=str(
            reviews_dir,
        ),
    )

    assert result.status == "completed"
    assert result.run_id
    assert result.run_dir

    assert Path(
        result.run_dir,
    ).exists()

    assert "report_markdown_path" in result.artifacts
    assert "report_html_path" in result.artifacts
    assert "summary_json_path" in result.artifacts
    assert "findings_json_path" in result.artifacts
    assert "reviewed_files_json_path" in result.artifacts
    assert "run_config_json_path" in result.artifacts
    assert "history_path" in result.artifacts

    assert Path(
        result.artifacts["report_html_path"],
    ).exists()

    assert Path(
        result.artifacts["history_path"],
    ).exists()    