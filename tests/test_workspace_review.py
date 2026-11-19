from pathlib import Path

from devsentinel.mcp.mcp_server_context import (
    build_devsentinel_mcp_context,
)
from devsentinel.review.workspace_review import review_workspace


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

    context = build_devsentinel_mcp_context()

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


def test_workspace_reviews_do_not_share_findings(tmp_path):
    insecure = create_python_workspace(tmp_path)
    clean = tmp_path / "clean"
    clean.mkdir()
    (clean / "hello.py").write_text("def hello():\n    return 1\n", encoding="utf-8")
    context = build_devsentinel_mcp_context()

    first = review_workspace(
        context=context, workspace_path=str(insecure), reviews_dir=str(tmp_path / "runs")
    )
    second = review_workspace(
        context=context, workspace_path=str(clean), reviews_dir=str(tmp_path / "runs")
    )

    assert first["findings_count"] > 0
    assert second["findings_count"] == 0
    assert first["report_path"] != second["report_path"]
    assert Path(second["report_path"]).is_file()
