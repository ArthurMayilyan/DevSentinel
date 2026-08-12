import pytest

from rag_strategy_factory import build_rag_search_engine_for_strategy
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


def test_search_knowledge_accepts_strategy_wrapped_search_engine():
    store = InMemoryRagStore()
    store.add_document(
        source="security.md",
        text="Token expiration policy: tokens must be signed and must expire.",
    )

    search_engine = build_rag_search_engine_for_strategy(
        store=store,
        strategy="binary-overlap",
    )

    results = search_knowledge(
        store=search_engine,
        query="token expiration",
        top_k=1,
    )

    assert len(results) == 1
    assert results[0]["source"] == "security.md"
    assert "Token expiration policy" in results[0]["text"]


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

        