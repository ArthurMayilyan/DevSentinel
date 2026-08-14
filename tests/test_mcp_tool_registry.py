from mcp_tool_catalog import list_mcp_tool_specs_for_mode
from mcp_tool_registry import build_mcp_tool_registry


def test_build_mcp_tool_registry_registers_specs():
    registry = build_mcp_tool_registry(
        list_mcp_tool_specs_for_mode(
            "rag_qa",
        )
    )

    assert [
        spec.name
        for spec in registry.list_specs()
    ] == [
        "search_knowledge",
    ]


def test_mcp_tool_registry_rejects_unknown_tool_execution():
    registry = build_mcp_tool_registry(
        list_mcp_tool_specs_for_mode(
            "rag_qa",
        )
    )

    result = registry.execute(
        name="unknown",
        arguments={},
    )

    assert result.success is False
    assert result.error == "unknown MCP tool: unknown"


def test_mcp_tool_registry_reports_missing_handler():
    registry = build_mcp_tool_registry(
        list_mcp_tool_specs_for_mode(
            "rag_qa",
        )
    )

    result = registry.execute(
        name="search_knowledge",
        arguments={
            "query": "token expiration",
        },
    )

    assert result.success is False
    assert result.error == "no handler registered for MCP tool: search_knowledge"


def test_mcp_tool_registry_executes_registered_handler():
    registry = build_mcp_tool_registry(
        list_mcp_tool_specs_for_mode(
            "rag_qa",
        )
    )

    registry.register_handler(
        name="search_knowledge",
        handler=lambda arguments: {
            "query": arguments["query"],
            "results": [],
        },
    )

    result = registry.execute(
        name="search_knowledge",
        arguments={
            "query": "token expiration",
        },
    )

    assert result.success is True
    assert result.result == {
        "query": "token expiration",
        "results": [],
    }