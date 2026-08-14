from mcp_tool_catalog import (
    list_mcp_tool_specs_for_mode,
)


def get_names(specs):
    return [
        spec.name
        for spec in specs
    ]


def test_list_mcp_tool_specs_for_all_tools():
    specs = list_mcp_tool_specs_for_mode()

    assert get_names(
        specs,
    ) == [
        "list_files",
        "read_file",
        "search_in_files",
        "add_finding",
        "write_report",
        "search_knowledge",
    ]


def test_list_mcp_tool_specs_for_rag_qa_mode():
    specs = list_mcp_tool_specs_for_mode(
        "rag_qa",
    )

    assert get_names(
        specs,
    ) == [
        "search_knowledge",
    ]


def test_list_mcp_tool_specs_for_code_review_mode():
    specs = list_mcp_tool_specs_for_mode(
        "code_review",
    )

    assert get_names(
        specs,
    ) == [
        "list_files",
        "read_file",
        "search_in_files",
        "add_finding",
        "write_report",
        "search_knowledge",
    ]


def test_search_knowledge_spec_has_query_input():
    specs = list_mcp_tool_specs_for_mode(
        "rag_qa",
    )

    spec = specs[0]

    assert spec.name == "search_knowledge"
    assert "query" in spec.input_schema["properties"]
    assert "query" in spec.input_schema["required"]