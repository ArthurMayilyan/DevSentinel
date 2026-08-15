from pathlib import Path

import pytest

from mcp_server_context import build_agent_loop_mcp_context
from mcp_server_handlers import (
    mcp_add_finding,
    mcp_list_files,
    mcp_read_file,
    mcp_search_in_files,
    mcp_search_knowledge,
    mcp_write_report,
)


def test_mcp_list_files_returns_files_and_updates_state(tmp_path):
    project_path = tmp_path / "project"
    project_path.mkdir()

    app_path = project_path / "app.py"
    app_path.write_text(
        "DEBUG = True",
        encoding="utf-8",
    )

    context = build_agent_loop_mcp_context()

    files = mcp_list_files(
        context=context,
        path=str(
            project_path,
        ),
    )

    assert files == [
        str(
            app_path,
        )
    ]

    assert context.state.discovered_files == [
        str(
            app_path,
        )
    ]


def test_mcp_read_file_returns_content_and_updates_state(tmp_path):
    file_path = tmp_path / "app.py"
    file_path.write_text(
        "DEBUG = True",
        encoding="utf-8",
    )

    context = build_agent_loop_mcp_context()

    content = mcp_read_file(
        context=context,
        path=str(
            file_path,
        ),
    )

    assert content == "DEBUG = True"
    assert context.state.inspected_files == [
        str(
            file_path,
        )
    ]


def test_mcp_search_in_files_returns_matches(tmp_path):
    project_path = tmp_path / "project"
    project_path.mkdir()

    app_path = project_path / "app.py"
    app_path.write_text(
        "DEBUG = True",
        encoding="utf-8",
    )

    context = build_agent_loop_mcp_context()

    results = mcp_search_in_files(
        context=context,
        path=str(
            project_path,
        ),
        query="DEBUG",
    )

    assert results == [
        {
            "file": str(
                app_path,
            ),
            "line": 1,
            "text": "DEBUG = True",
        }
    ]


def test_mcp_search_knowledge_requires_store():
    context = build_agent_loop_mcp_context()

    with pytest.raises(ValueError):
        mcp_search_knowledge(
            context=context,
            query="credentials",
        )


def test_mcp_search_knowledge_returns_results(tmp_path):
    knowledge_path = tmp_path / "knowledge"
    knowledge_path.mkdir()

    policy_path = knowledge_path / "security.md"
    policy_path.write_text(
        "Credentials must not be hardcoded in source code.",
        encoding="utf-8",
    )

    context = build_agent_loop_mcp_context(
        knowledge_path=str(
            knowledge_path,
        )
    )

    results = mcp_search_knowledge(
        context=context,
        query="credentials",
    )

    assert results[0]["source"] == str(
        policy_path,
    )

    assert "Credentials must not be hardcoded" in results[0]["text"]


def test_mcp_add_finding_updates_state():
    context = build_agent_loop_mcp_context()

    result = mcp_add_finding(
        context=context,
        file="sample_project/app.py",
        severity="high",
        category="security",
        issue="Hardcoded credential risk.",
        evidence="A sensitive value appears directly in source code.",
        recommendation="Move sensitive values to secure configuration.",
    )

    assert result == "Finding added."

    assert context.state.findings == [
        {
            "file": "sample_project/app.py",
            "severity": "HIGH",
            "category": "SECURITY",
            "issue": "Hardcoded credential risk.",
            "evidence": "A sensitive value appears directly in source code.",
            "recommendation": "Move sensitive values to secure configuration.",
        }
    ]


def test_mcp_write_report_writes_report_from_state(tmp_path):
    report_path = tmp_path / "report.md"

    context = build_agent_loop_mcp_context(
        report_path=str(
            report_path,
        )
    )

    mcp_add_finding(
        context=context,
        file="sample_project/app.py",
        severity="HIGH",
        category="SECURITY",
        issue="Hardcoded credential risk.",
        evidence="A sensitive value appears directly in source code.",
        recommendation="Move sensitive values to secure configuration.",
    )

    result = mcp_write_report(
        context=context,
    )

    assert result == str(
        report_path,
    )

    report = report_path.read_text(
        encoding="utf-8",
    )

    assert "Hardcoded credential risk." in report
    assert "HIGH" in report
    assert "SECURITY" in report
    assert context.state.report_written is True
    assert context.state.report_path == str(
        report_path,
    )

    