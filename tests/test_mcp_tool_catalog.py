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


def test_add_finding_spec_uses_runtime_issue_field():
    specs = list_mcp_tool_specs_for_mode(
        "code_review",
    )

    spec = next(
        item
        for item in specs
        if item.name == "add_finding"
    )

    assert "issue" in spec.input_schema["properties"]
    assert "title" not in spec.input_schema["properties"]
    assert "issue" in spec.input_schema["required"]
    assert spec.input_schema["properties"]["severity"]["enum"] == [
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    ]


def test_write_report_spec_has_no_llm_supplied_markdown():
    specs = list_mcp_tool_specs_for_mode(
        "code_review",
    )

    spec = next(
        item
        for item in specs
        if item.name == "write_report"
    )

    assert spec.input_schema["properties"] == {}
    assert spec.input_schema["required"] == []

        