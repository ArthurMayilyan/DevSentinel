import pytest

from rag_store import InMemoryRagStore
from rag_tool import DEFAULT_RAG_TOP_K, search_knowledge


def test_search_knowledge_returns_serializable_chunks():
    store = InMemoryRagStore()
    store.add_document(
        source="security.md",
        text="Tokens must be signed and must expire.",
    )

    results = search_knowledge(
        store=store,
        query="signed tokens",
    )

    assert results == [
        {
            "source": "security.md",
            "chunk_index": 0,
            "text": "Tokens must be signed and must expire.",
            "score": 2,
        }
    ]


def test_search_knowledge_respects_top_k():
    store = InMemoryRagStore()
    store.add_document(source="a.md", text="agent memory")
    store.add_document(source="b.md", text="agent planning")
    store.add_document(source="c.md", text="agent tools")

    results = search_knowledge(
        store=store,
        query="agent",
        top_k=2,
    )

    assert len(results) == 2


def test_search_knowledge_uses_default_top_k():
    assert DEFAULT_RAG_TOP_K == 3


def test_search_knowledge_returns_empty_list_when_no_match():
    store = InMemoryRagStore()
    store.add_document(
        source="security.md",
        text="Tokens must be signed.",
    )

    assert search_knowledge(
        store=store,
        query="database",
    ) == []


def test_search_knowledge_rejects_non_rag_store():
    with pytest.raises(ValueError):
        search_knowledge(
            store="not a store",
            query="agent",
        )


def test_search_knowledge_rejects_empty_query():
    store = InMemoryRagStore()

    with pytest.raises(ValueError):
        search_knowledge(
            store=store,
            query="",
        )


def test_search_knowledge_rejects_invalid_top_k():
    store = InMemoryRagStore()

    with pytest.raises(ValueError):
        search_knowledge(
            store=store,
            query="agent",
            top_k=0,
        )

        