import pytest

from rag_eval import RagRetrievalEvalCase, evaluate_rag_retrieval_case
from rag_retrievers import (
    BinaryOverlapRagRetriever,
    TermFrequencyRagRetriever,
    score_binary_token_overlap,
    score_term_frequency_token_overlap,
)
from rag_store import InMemoryRagStore


def test_score_binary_token_overlap_counts_unique_query_token_matches():
    assert score_binary_token_overlap(
        query="token expiration",
        text="token token token",
    ) == 1

    assert score_binary_token_overlap(
        query="token expiration",
        text="token expiration",
    ) == 2


def test_binary_overlap_retriever_ranks_by_unique_query_token_coverage():
    store = InMemoryRagStore()
    store.add_document(
        source="knowledge/repeated.md",
        text="token token token token",
    )
    store.add_document(
        source="knowledge/complete.md",
        text="token expiration",
    )

    retriever = BinaryOverlapRagRetriever(
        store=store,
    )

    results = retriever.search(
        query="token expiration",
    )

    assert [result.source for result in results] == [
        "knowledge/complete.md",
        "knowledge/repeated.md",
    ]

    assert [result.score for result in results] == [
        2,
        1,
    ]


def test_binary_overlap_retriever_returns_empty_list_when_no_chunks_match():
    store = InMemoryRagStore()
    store.add_document(
        source="knowledge/coding.md",
        text="Functions should be small.",
    )

    retriever = BinaryOverlapRagRetriever(
        store=store,
    )

    assert retriever.search(query="token expiration") == []


def test_binary_overlap_retriever_can_be_used_by_rag_eval():
    store = InMemoryRagStore()
    store.add_document(
        source="knowledge/repeated.md",
        text="token token token token",
    )
    store.add_document(
        source="knowledge/complete.md",
        text="token expiration",
    )

    retriever = BinaryOverlapRagRetriever(
        store=store,
    )

    case = RagRetrievalEvalCase(
        name="complete token expiration",
        query="token expiration",
        expected_source_contains="complete.md",
        expected_text_contains="token expiration",
    )

    result = evaluate_rag_retrieval_case(
        store=retriever,
        case=case,
    )

    assert result.passed is True
    assert result.matched_rank == 1
    assert result.reciprocal_rank == 1.0
    assert result.retrieved_sources == [
        "knowledge/complete.md",
        "knowledge/repeated.md",
    ]


def test_binary_overlap_retriever_rejects_invalid_top_k():
    store = InMemoryRagStore()
    retriever = BinaryOverlapRagRetriever(
        store=store,
    )

    with pytest.raises(ValueError):
        retriever.search(
            query="token expiration",
            top_k=0,
        )


def test_binary_overlap_retriever_rejects_empty_query():
    store = InMemoryRagStore()
    retriever = BinaryOverlapRagRetriever(
        store=store,
    )

    with pytest.raises(ValueError):
        retriever.search(
            query="",
        )

def test_score_term_frequency_token_overlap_counts_repeated_matches():
    assert score_term_frequency_token_overlap(
        query="token expiration",
        text="token token token",
    ) == 3

    assert score_term_frequency_token_overlap(
        query="token expiration",
        text="token expiration",
    ) == 2

def test_term_frequency_retriever_can_rank_repeated_noise_above_complete_match():
    store = InMemoryRagStore()
    store.add_document(
        source="knowledge/repeated.md",
        text="token token token token",
    )
    store.add_document(
        source="knowledge/complete.md",
        text="token expiration",
    )

    retriever = TermFrequencyRagRetriever(
        store=store,
    )

    results = retriever.search(
        query="token expiration",
    )

    assert [result.source for result in results] == [
        "knowledge/repeated.md",
        "knowledge/complete.md",
    ]

    assert [result.score for result in results] == [
        4,
        2,
    ]

def test_term_frequency_retriever_can_be_used_by_rag_eval():
    store = InMemoryRagStore()
    store.add_document(
        source="knowledge/repeated.md",
        text="token token token token",
    )
    store.add_document(
        source="knowledge/complete.md",
        text="token expiration",
    )

    retriever = TermFrequencyRagRetriever(
        store=store,
    )

    case = RagRetrievalEvalCase(
        name="complete token expiration",
        query="token expiration",
        expected_source_contains="complete.md",
        expected_text_contains="token expiration",
    )

    result = evaluate_rag_retrieval_case(
        store=retriever,
        case=case,
    )

    assert result.passed is True
    assert result.matched_rank == 2
    assert result.reciprocal_rank == 0.5
    assert result.retrieved_sources == [
        "knowledge/repeated.md",
        "knowledge/complete.md",
    ]

            