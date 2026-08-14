import pytest

from mcp_tool_contract import (
    McpToolSpec,
    mcp_tool_spec_to_dict,
    mcp_tool_spec_to_mcp_tool,
    validate_mcp_tool_spec,
)


def build_valid_spec():
    return McpToolSpec(
        name="example_tool",
        description="Example tool.",
        input_schema={
            "type": "object",
            "properties": {},
            "required": [],
        },
        output_schema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )


def test_validate_mcp_tool_spec_accepts_valid_spec():
    validate_mcp_tool_spec(
        build_valid_spec(),
    )


def test_validate_mcp_tool_spec_rejects_empty_name():
    with pytest.raises(ValueError):
        validate_mcp_tool_spec(
            McpToolSpec(
                name="",
                description="Example tool.",
                input_schema={
                    "type": "object",
                },
                output_schema={
                    "type": "object",
                },
            )
        )


def test_mcp_tool_spec_to_dict_serializes_spec():
    payload = mcp_tool_spec_to_dict(
        build_valid_spec(),
    )

    assert payload["name"] == "example_tool"
    assert payload["description"] == "Example tool."


def test_mcp_tool_spec_to_mcp_tool_uses_mcp_input_schema_key():
    payload = mcp_tool_spec_to_mcp_tool(
        build_valid_spec(),
    )

    assert payload == {
        "name": "example_tool",
        "description": "Example tool.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    }