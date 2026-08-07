import pytest

from rag_runtime_tool import build_search_knowledge_runtime_tool
from rag_store import InMemoryRagStore


def test_search_knowledge_runtime_tool_injects_store():
    store = InMemoryRagStore()
    store.add_document(
        source="security.md",
        text="Tokens must be signed and must expire.",
    )

    tool = build_search_knowledge_runtime_tool(store=store)

    results = tool(query="signed tokens")

    assert results == [
        {
            "source": "security.md",
            "chunk_index": 0,
            "text": "Tokens must be signed and must expire.",
            "score": 2,
        }
    ]


def test_search_knowledge_runtime_tool_rejects_invalid_store():
    with pytest.raises(ValueError):
        build_search_knowledge_runtime_tool(
            store="not a rag store",
        )

        