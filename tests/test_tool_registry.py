import pytest

from tool_contracts import TOOL_ARGUMENT_CONTRACTS
from runtime_tool_registry import ToolRegistry
from tool_specs import TOOL_SPECS
from tool_registry import ToolSpec


def dummy_read_file(path: str) -> str:
    return f"read: {path}"


def make_registry() -> ToolRegistry:
    registry = ToolRegistry()

    registry.register(
        name="read_file",
        function=dummy_read_file,
        spec=TOOL_SPECS["read_file"],
        contract=TOOL_ARGUMENT_CONTRACTS["read_file"],
    )

    return registry


def test_register_tool_and_list_names():
    registry = make_registry()

    assert registry.names() == ["read_file"]
    assert registry.has("read_file") is True
    assert registry.has("write_report") is False


def test_get_registered_tool():
    registry = make_registry()

    registered_tool = registry.get("read_file")

    assert registered_tool.name == "read_file"
    assert registered_tool.spec.name == "read_file"
    assert registered_tool.contract == TOOL_ARGUMENT_CONTRACTS["read_file"]
    assert callable(registered_tool.function)


def test_get_unknown_tool_fails():
    registry = make_registry()

    with pytest.raises(KeyError):
        registry.get("unknown_tool")


def test_register_duplicate_tool_fails():
    registry = make_registry()

    with pytest.raises(ValueError):
        registry.register(
            name="read_file",
            function=dummy_read_file,
            spec=TOOL_SPECS["read_file"],
            contract=TOOL_ARGUMENT_CONTRACTS["read_file"],
        )


def test_register_non_callable_tool_fails():
    registry = ToolRegistry()

    with pytest.raises(ValueError):
        registry.register(
            name="read_file",
            function="not callable",
            spec=TOOL_SPECS["read_file"],
            contract=TOOL_ARGUMENT_CONTRACTS["read_file"],
        )


def test_registry_validates_arguments():
    registry = make_registry()

    allowed, reason = registry.validate_arguments(
        tool_name="read_file",
        arguments={
            "path": "sample_project/auth.py",
        },
    )

    assert allowed is True
    assert reason == ""


def test_registry_rejects_invalid_arguments():
    registry = make_registry()

    allowed, reason = registry.validate_arguments(
        tool_name="read_file",
        arguments={},
    )

    assert allowed is False
    assert "missing" in reason.lower()
    assert "path" in reason


def test_registry_executes_tool():
    registry = make_registry()

    result = registry.execute(
        tool_name="read_file",
        arguments={
            "path": "sample_project/auth.py",
        },
    )

    assert result == "read: sample_project/auth.py"


def test_registry_execute_rejects_invalid_arguments():
    registry = make_registry()

    with pytest.raises(ValueError):
        registry.execute(
            tool_name="read_file",
            arguments={},
        )

def test_registry_returns_registered_tools_sorted_by_name():
    registry = ToolRegistry()

    registry.register(
        name="read_file",
        function=dummy_read_file,
        spec=TOOL_SPECS["read_file"],
        contract=TOOL_ARGUMENT_CONTRACTS["read_file"],
    )

    registered_tools = registry.registered_tools()

    assert len(registered_tools) == 1
    assert registered_tools[0].name == "read_file"
    assert registered_tools[0].spec.name == "read_file"
    assert registered_tools[0].contract == TOOL_ARGUMENT_CONTRACTS["read_file"]        

def test_registry_formats_tools_for_prompt():
    registry = make_registry()

    text = registry.format_tools_for_prompt()

    assert "Tool: read_file" in text
    assert "Description:" in text
    assert "Argument contract:" in text
    assert "Required arguments" in text
    assert "Allowed arguments" in text
    assert "path" in text


def test_registry_prompt_format_does_not_include_unregistered_tools():
    registry = make_registry()

    text = registry.format_tools_for_prompt()

    assert "Tool: read_file" in text
    assert "Tool: write_report" not in text
    assert "Tool: add_finding" not in text    

def test_tool_registry_returns_registered_specs_sorted_by_name():
    registry = ToolRegistry()

    registry.register(
        name="b_tool",
        function=lambda: "b",
        spec=ToolSpec(
            name="b_tool",
            description="B tool.",
            parameters={},
            returns="B.",
            when_to_use="Use for B.",
            when_not_to_use="Do not use for not B.",
            function=None,
        ),
        contract=TOOL_ARGUMENT_CONTRACTS["write_report"],
    )

    registry.register(
        name="a_tool",
        function=lambda: "a",
        spec=ToolSpec(
            name="a_tool",
            description="A tool.",
            parameters={},
            returns="A.",
            when_to_use="Use for A.",
            when_not_to_use="Do not use for not A.",
            function=None,
        ),
        contract=TOOL_ARGUMENT_CONTRACTS["write_report"],
    )

    assert [spec.name for spec in registry.specs()] == [
        "a_tool",
        "b_tool",
    ]

        