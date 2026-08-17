from pathlib import Path

from mcp_server_context import (
    build_agent_loop_mcp_context,
)
from workspace_review import review_workspace


def create_python_workspace(tmp_path):
    workspace_path = tmp_path / "workspace"

    workspace_path.mkdir()

    (workspace_path / "config.py").write_text(
        'SECRET_KEY = "secret"\nDEBUG = True\n',
        encoding="utf-8",
    )

    (workspace_path / "README.md").write_text(
        "# Test project",
        encoding="utf-8",
    )

    return workspace_path


def test_review_workspace_uses_python_security_preset(tmp_path):
    workspace_path = create_python_workspace(
        tmp_path,
    )

    context = build_agent_loop_mcp_context()

    result = review_workspace(
        context=context,
        workspace_path=str(
            workspace_path,
        ),
        preset="python-security",
        reviewer="deterministic",
    )

    assert result["status"] == "completed"

    assert result["workspace_preset"] == (
        "python-security"
    )

    assert result["selected_files_count"] == 1

    assert result["findings_count"] >= 1

    assert result["run_id"]

    assert Path(
        result["run_dir"],
    ).exists()

    assert Path(
        result["artifacts"]["report_html_path"],
    ).exists()