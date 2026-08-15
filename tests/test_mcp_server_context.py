from mcp_server_context import build_agent_loop_mcp_context


def test_build_agent_loop_mcp_context_without_knowledge_base():
    context = build_agent_loop_mcp_context()

    assert context.rag_store is None
    assert context.report_path == "report.md"
    assert context.state.findings == []


def test_build_agent_loop_mcp_context_with_knowledge_path(tmp_path):
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

    assert context.rag_store is not None

    