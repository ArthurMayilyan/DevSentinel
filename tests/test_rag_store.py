import pytest

from rag_store import (
    InMemoryRagStore,
    RetrievedChunk,
    chunk_text,
    normalize_token,
    tokenize,
)


def test_tokenize_lowercases_and_extracts_words():
    assert tokenize("Hello, RAG! Hello agent_1.") == {
        "hello",
        "rag",
        "agent_1",
    }


def test_chunk_text_returns_single_chunk_for_short_text():
    assert chunk_text("Small document.", max_chars=100, overlap_chars=10) == [
        "Small document."
    ]


def test_chunk_text_splits_long_text_with_overlap():
    chunks = chunk_text(
        "abcdefghij",
        max_chars=4,
        overlap_chars=1,
    )

    assert chunks == [
        "abcd",
        "defg",
        "ghij",
    ]


def test_chunk_text_rejects_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_text(
            "abcdefghij",
            max_chars=4,
            overlap_chars=4,
        )


def test_retrieved_chunk_can_be_serialized_to_dict():
    chunk = RetrievedChunk(
        source="doc.md",
        chunk_index=0,
        text="Agent memory and retrieval.",
        score=2,
    )

    assert chunk.to_dict() == {
        "source": "doc.md",
        "chunk_index": 0,
        "text": "Agent memory and retrieval.",
        "score": 2,
    }


def test_rag_store_adds_document_chunks():
    store = InMemoryRagStore()

    store.add_document(
        source="doc.md",
        text="abcdefghij",
        max_chars=4,
        overlap_chars=1,
    )

    assert [chunk.text for chunk in store.chunks] == [
        "abcd",
        "defg",
        "ghij",
    ]


def test_rag_store_search_returns_matching_chunks_by_score():
    store = InMemoryRagStore()

    store.add_document(
        source="agents.md",
        text="RAG helps agents retrieve relevant context.",
    )
    store.add_document(
        source="cooking.md",
        text="Pasta recipe with tomato sauce.",
    )

    results = store.search(
        query="agent rag context",
        top_k=2,
    )

    assert len(results) == 1
    assert results[0].source == "agents.md"
    assert results[0].score == 3


def test_rag_store_search_respects_top_k():
    store = InMemoryRagStore()

    store.add_document(source="a.md", text="agent memory")
    store.add_document(source="b.md", text="agent planning")
    store.add_document(source="c.md", text="agent tools")

    results = store.search(
        query="agent",
        top_k=2,
    )

    assert len(results) == 2


def test_rag_store_search_returns_empty_list_when_no_match():
    store = InMemoryRagStore()

    store.add_document(
        source="doc.md",
        text="Planning and tool use.",
    )

    assert store.search(query="database") == []


def test_rag_store_search_rejects_empty_query():
    store = InMemoryRagStore()

    with pytest.raises(ValueError):
        store.search(query="")


def test_normalize_token_lowercases_token():
    assert normalize_token("Token") == "token"


def test_normalize_token_normalizes_plural_tokens():
    assert normalize_token("tokens") == "token"


def test_normalize_token_normalizes_ies_plural():
    assert normalize_token("policies") == "policy"


def test_normalize_token_normalizes_validation_family():
    assert normalize_token("validation") == "valid"
    assert normalize_token("validate") == "valid"
    assert normalize_token("validated") == "valid"


def test_normalize_token_normalizes_expiration_family():
    assert normalize_token("expiration") == "expir"
    assert normalize_token("expires") == "expir"


def test_normalize_token_rejects_empty_token():
    with pytest.raises(ValueError):
        normalize_token("")

def test_rag_store_search_matches_normalized_tokens():
    store = InMemoryRagStore()

    store.add_document(
        source="security.md",
        text="Tokens must be signed and must expire.",
    )

    results = store.search(
        query="token expiration",
    )

    assert results == [
        RetrievedChunk(
            source="security.md",
            chunk_index=0,
            text="Tokens must be signed and must expire.",
            score=2,
        )
    ]

                    