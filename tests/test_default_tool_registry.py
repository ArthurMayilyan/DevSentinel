import pytest

from default_tool_registry import build_default_tool_registry
from tool_specs import TOOL_SPECS
from rag_store import InMemoryRagStore
from tools import list_files, read_file, search_in_files, write_report


def fake_add_finding(**kwargs):
    return "Finding added."


def make_tool_functions():
    return {
        "list_files": list_files,
        "read_file": read_file,
        "search_in_files": search_in_files,
        "write_report": write_report,
        "add_finding": fake_add_finding,
    }


def dummy_read_file(path: str) -> str:
    return f"read: {path}"


def test_build_default_tool_registry_registers_tool():
    registry = build_default_tool_registry(
        tool_functions={
            "read_file": dummy_read_file,
        }
    )

    assert registry.names() == ["read_file"]
    assert registry.has("read_file") is True


def test_build_default_tool_registry_uses_matching_spec_and_contract():
    registry = build_default_tool_registry(
        tool_functions={
            "read_file": dummy_read_file,
        }
    )

    registered_tool = registry.get("read_file")

    assert registered_tool.name == "read_file"
    assert registered_tool.spec.name == "read_file"
    assert registered_tool.contract.required == {"path"}
    assert registered_tool.contract.allowed == {"path"}


def test_build_default_tool_registry_rejects_unknown_tool_name():
    with pytest.raises(KeyError):
        build_default_tool_registry(
            tool_functions={
                "unknown_tool": dummy_read_file,
            }
        )


def test_build_default_tool_registry_registers_all_tool_specs_when_all_functions_given():
    def dummy_tool(**kwargs):
        return kwargs

    tool_functions = {
        tool_name: dummy_tool
        for tool_name in TOOL_SPECS.keys()
    }

    registry = build_default_tool_registry(
        tool_functions=tool_functions,
    )

    assert set(registry.names()) == set(TOOL_SPECS.keys())

def test_default_tool_registry_does_not_register_search_knowledge_without_rag_store():
    registry = build_default_tool_registry(
        tool_functions=make_tool_functions(),
    )

    assert "search_knowledge" not in registry.names()


def test_default_tool_registry_executes_search_knowledge_with_rag_store():
    rag_store = InMemoryRagStore()
    rag_store.add_document(
        source="security.md",
        text="Tokens must be signed and must expire.",
    )

    registry = build_default_tool_registry(
        tool_functions=make_tool_functions(),
        rag_store=rag_store,
    )

    result = registry.execute(
        tool_name="search_knowledge",
        arguments={
            "query": "signed tokens",
        },
    )

    assert result == [
        {
            "source": "security.md",
            "chunk_index": 0,
            "text": "Tokens must be signed and must expire.",
            "score": 2,
        }
    ]

def test_default_tool_registry_executes_search_knowledge_with_rag_store():
    rag_store = InMemoryRagStore()
    rag_store.add_document(
        source="security.md",
        text="Tokens must be signed and must expire.",
    )

    registry = build_default_tool_registry(
        tool_functions=make_tool_functions(),
        rag_store=rag_store,
    )

    result = registry.execute(
        tool_name="search_knowledge",
        arguments={
            "query": "signed tokens",
        },
    )

    assert result == [
        {
            "source": "security.md",
            "chunk_index": 0,
            "text": "Tokens must be signed and must expire.",
            "score": 2,
        }
    ]