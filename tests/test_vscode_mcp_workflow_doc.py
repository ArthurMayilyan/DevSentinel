from pathlib import Path


def test_vscode_mcp_workflow_doc_exists_and_mentions_product_workflow():
    path = Path(
        "docs/vscode_mcp_workflow.md",
    )

    assert path.exists()

    content = path.read_text(
        encoding="utf-8",
    )

    assert "AgentLoop MCP in VS Code" in content
    assert ".vscode/mcp.json" in content

    assert "list_files" in content
    assert "read_file" in content
    assert "search_in_files" in content
    assert "search_knowledge" in content
    assert "add_finding" in content
    assert "write_report" in content
    assert "review_project" in content

    assert "Product workflow prompt" in content
    assert "Manual fallback prompt" in content
    assert "Real repository workflow prompt" in content

    assert "/mcp.agentloop.review_project" in content
    assert "allowed_root" in content
    assert "include_globs" in content
    assert "exclude_globs" in content
    assert "max_files" in content
    assert "max_file_size_bytes" in content
    assert "report_dir" in content
    assert "Review run package" in content
    assert "reviews_dir" in content
    assert "report.html" in content
    assert "history.json" in content
    assert "summary.json" in content
    assert "findings.json" in content    