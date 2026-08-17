import json
from pathlib import Path

from run_mcp_client_smoke import run_from_args


def test_run_from_args_runs_mcp_client_smoke(tmp_path):
    report_path = tmp_path / "mcp_report.md"

    output = run_from_args(
        [
            "--project-path",
            "./sample_project",
            "--report-path",
            str(
                report_path,
            ),
        ]
    )

    assert "MCP client smoke test passed" in output
    assert "- list_files" in output
    assert "- write_report" in output
    assert report_path.exists()

    report = report_path.read_text(
        encoding="utf-8",
    )

    assert "Hardcoded credential risk." in report
    assert "HIGH" in report
    assert "SECURITY" in report
    assert "Product workflow:" in output
    assert "- review_project" in output    


def test_run_from_args_returns_json(tmp_path):
    report_path = tmp_path / "mcp_report.md"

    output = run_from_args(
        [
            "--project-path",
            "./sample_project",
            "--report-path",
            str(
                report_path,
            ),
            "--json",
        ]
    )

    payload = json.loads(
        output,
    )

    assert "list_files" in payload["tools"]
    assert "read_file" in payload["tools"]
    assert "add_finding" in payload["tools"]
    assert "write_report" in payload["tools"]
    assert payload["read_file_is_error"] is False
    assert payload["report_path"] == str(
        report_path,
    )
    assert "review_project" in payload["tools"]
    assert "compare_review_runs" in payload["tools"]
    assert payload["review_project"] is not None

    serialized_review = json.dumps(
        payload["review_project"],
    )

    assert "completed" in serialized_review
    assert "report_path" in serialized_review    


def test_run_from_args_can_call_search_knowledge(tmp_path):
    knowledge_path = tmp_path / "knowledge"
    knowledge_path.mkdir()

    policy_path = knowledge_path / "security.md"
    policy_path.write_text(
        "Credentials must not be hardcoded in source code.",
        encoding="utf-8",
    )

    report_path = tmp_path / "mcp_report.md"

    output = run_from_args(
        [
            "--project-path",
            "./sample_project",
            "--knowledge-path",
            str(
                knowledge_path,
            ),
            "--report-path",
            str(
                report_path,
            ),
            "--json",
        ]
    )

    payload = json.loads(
        output,
    )

    assert payload["search_knowledge"] is not None

    serialized = json.dumps(
        payload["search_knowledge"],
    )

    assert "Credentials must not be hardcoded" in serialized