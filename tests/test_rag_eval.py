import pytest

from rag_eval import (
    RagRetrievalEvalCase,
    RagRetrievalEvalResult,
    RagRetrievedChunkEvalItem,
    evaluate_rag_retrieval,
    evaluate_rag_retrieval_case,
    find_matched_rank,
    source_matches_expected_source,
)
from rag_store import InMemoryRagStore


def test_rag_retrieval_eval_case_requires_non_empty_name():
    with pytest.raises(ValueError):
        RagRetrievalEvalCase(
            name="",
            query="token expiration",
            expected_source_contains="security.md",
            expected_text_contains="Tokens must be signed",
        )


def test_evaluate_rag_retrieval_case_passes_when_expected_chunk_is_found():
    store = InMemoryRagStore()
    store.add_document(
        source="knowledge/security.md",
        text="Tokens must be signed and must expire.",
    )

    case = RagRetrievalEvalCase(
        name="token expiration policy",
        query="token expiration",
        expected_source_contains="security.md",
        expected_text_contains="Tokens must be signed",
    )

    result = evaluate_rag_retrieval_case(
        store=store,
        case=case,
    )

    assert result.passed is True
    assert result.retrieved_sources == ["knowledge/security.md"]
    assert result.retrieved_texts == [
        "Tokens must be signed and must expire."
    ]
    assert len(result.retrieved_chunks) == 1
    assert result.retrieved_chunks[0].rank == 1
    assert result.retrieved_chunks[0].source == "knowledge/security.md"
    assert result.retrieved_chunks[0].chunk_index == 0
    assert result.retrieved_chunks[0].score == 2
    assert result.retrieved_chunks[0].text == "Tokens must be signed and must expire."    
    assert result.matched_rank == 1
    assert result.reciprocal_rank == 1.0


def test_evaluate_rag_retrieval_case_fails_when_expected_chunk_is_not_found():
    store = InMemoryRagStore()
    store.add_document(
        source="knowledge/coding.md",
        text="Functions should be small and readable.",
    )

    case = RagRetrievalEvalCase(
        name="token expiration policy",
        query="token expiration",
        expected_source_contains="security.md",
        expected_text_contains="Tokens must be signed",
    )

    result = evaluate_rag_retrieval_case(
        store=store,
        case=case,
    )

    assert result.passed is False
    assert result.retrieved_sources == []
    assert result.matched_rank is None
    assert result.reciprocal_rank == 0.0


def test_rag_retrieval_eval_result_can_be_serialized_to_dict():
    result = RagRetrievalEvalResult(
        name="token policy",
        query="token expiration",
        passed=True,
        expected_source_contains="security.md",
        expected_text_contains="Tokens must be signed",
        retrieved_sources=["knowledge/security.md"],
        retrieved_texts=["Tokens must be signed and must expire."],
    )

    assert result.to_dict() == {
        "name": "token policy",
        "query": "token expiration",
        "passed": True,
        "expected_source_contains": "security.md",
        "expected_text_contains": "Tokens must be signed",
        "retrieved_sources": ["knowledge/security.md"],
        "retrieved_texts": ["Tokens must be signed and must expire."],
        "matched_rank": None,
        "reciprocal_rank": 0.0,
        "retrieved_chunks": [],
    }


def test_evaluate_rag_retrieval_returns_summary():
    store = InMemoryRagStore()
    store.add_document(
        source="knowledge/security.md",
        text="Tokens must be signed and must expire.",
    )
    store.add_document(
        source="knowledge/coding.md",
        text="Functions should be small and readable.",
    )

    summary = evaluate_rag_retrieval(
        store=store,
        cases=[
            RagRetrievalEvalCase(
                name="token policy",
                query="token expiration",
                expected_source_contains="security.md",
                expected_text_contains="Tokens must be signed",
            ),
            RagRetrievalEvalCase(
                name="coding style",
                query="small function",
                expected_source_contains="coding.md",
                expected_text_contains="Functions should be small",
            ),
        ],
    )

    assert summary.total_cases == 2
    assert summary.passed_cases == 2
    assert summary.failed_cases == 0
    assert [result.passed for result in summary.results] == [True, True]
    assert summary.hit_rate == 1.0
    assert summary.top_1_accuracy == 1.0
    assert summary.mean_reciprocal_rank == 1.0

def test_evaluate_rag_retrieval_calculates_failed_cases_hit_rate_and_mrr():
    store = InMemoryRagStore()
    store.add_document(
        source="knowledge/security.md",
        text="Tokens must be signed and must expire.",
    )

    summary = evaluate_rag_retrieval(
        store=store,
        cases=[
            RagRetrievalEvalCase(
                name="token policy",
                query="token expiration",
                expected_source_contains="security.md",
                expected_text_contains="Tokens must be signed",
            ),
            RagRetrievalEvalCase(
                name="coding style",
                query="small function",
                expected_source_contains="coding.md",
                expected_text_contains="Functions should be small",
            ),
        ],
    )

    assert summary.total_cases == 2
    assert summary.passed_cases == 1
    assert summary.failed_cases == 1
    assert summary.hit_rate == 0.5
    assert summary.top_1_accuracy == 0.5
    assert summary.mean_reciprocal_rank == 0.5
    

def test_evaluate_rag_retrieval_summary_can_be_serialized_to_dict():
    store = InMemoryRagStore()
    store.add_document(
        source="knowledge/security.md",
        text="Tokens must be signed and must expire.",
    )

    summary = evaluate_rag_retrieval(
        store=store,
        cases=[
            RagRetrievalEvalCase(
                name="token policy",
                query="token expiration",
                expected_source_contains="security.md",
                expected_text_contains="Tokens must be signed",
            ),
        ],
    )

    assert summary.to_dict() == {
        "total_cases": 1,
        "passed_cases": 1,
        "failed_cases": 0,
        "hit_rate": 1.0,
        "top_1_accuracy": 1.0,
        "mean_reciprocal_rank": 1.0,
        "results": [
            {
                "name": "token policy",
                "query": "token expiration",
                "passed": True,
                "expected_source_contains": "security.md",
                "expected_text_contains": "Tokens must be signed",
                "retrieved_sources": ["knowledge/security.md"],
                "retrieved_texts": [
                    "Tokens must be signed and must expire."
                ],
                "matched_rank": 1,
                "reciprocal_rank": 1.0,
                "retrieved_chunks": [
                    {
                        "rank": 1,
                        "source": "knowledge/security.md",
                        "chunk_index": 0,
                        "score": 2,
                        "text": "Tokens must be signed and must expire.",
                    }
                ],
            }
        ],
    }


def test_evaluate_rag_retrieval_rejects_empty_cases():
    store = InMemoryRagStore()

    with pytest.raises(ValueError):
        evaluate_rag_retrieval(
            store=store,
            cases=[],
        )


def test_evaluate_rag_retrieval_rejects_invalid_top_k():
    store = InMemoryRagStore()

    with pytest.raises(ValueError):
        evaluate_rag_retrieval(
            store=store,
            cases=[
                RagRetrievalEvalCase(
                    name="token policy",
                    query="token expiration",
                    expected_source_contains="security.md",
                    expected_text_contains="Tokens must be signed",
                ),
            ],
            top_k=0,
        )

def test_source_matches_expected_source_matches_file_name():
    assert source_matches_expected_source(
        source="knowledge_base\\coding.md",
        expected_source="coding.md",
    ) is True


def test_source_matches_expected_source_rejects_similar_file_name():
    assert source_matches_expected_source(
        source="knowledge_base\\_coding.md",
        expected_source="coding.md",
    ) is False


def test_source_matches_expected_source_rejects_backup_file_name():
    assert source_matches_expected_source(
        source="knowledge_base\\coding.md.backup",
        expected_source="coding.md",
    ) is False


def test_source_matches_expected_source_matches_path_suffix():
    assert source_matches_expected_source(
        source="D:\\Projects\\AgentLoop\\knowledge_base\\security.md",
        expected_source="knowledge_base/security.md",
    ) is True

def test_evaluate_rag_retrieval_case_fails_for_similar_but_wrong_source_name():
    store = InMemoryRagStore()
    store.add_document(
        source="knowledge_base\\_coding.md",
        text="Functions should be small and readable.",
    )

    case = RagRetrievalEvalCase(
        name="coding style",
        query="small function",
        expected_source_contains="coding.md",
        expected_text_contains="Functions should be small",
    )

    result = evaluate_rag_retrieval_case(
        store=store,
        case=case,
    )

    assert result.passed is False
    assert result.retrieved_sources == ["knowledge_base\\_coding.md"]


def test_rag_retrieved_chunk_eval_item_can_be_serialized_to_dict():
    item = RagRetrievedChunkEvalItem(
        rank=1,
        source="knowledge/security.md",
        chunk_index=0,
        score=2,
        text="Tokens must be signed and must expire.",
    )

    assert item.to_dict() == {
        "rank": 1,
        "source": "knowledge/security.md",
        "chunk_index": 0,
        "score": 2,
        "text": "Tokens must be signed and must expire.",
    }

def test_rag_retrieved_chunk_eval_item_rejects_invalid_rank():
    with pytest.raises(ValueError):
        RagRetrievedChunkEvalItem(
            rank=0,
            source="knowledge/security.md",
            chunk_index=0,
            score=2,
            text="Tokens must be signed and must expire.",
        )


def test_find_matched_rank_returns_rank_of_matching_chunk():
    retrieved_chunks = [
        RagRetrievedChunkEvalItem(
            rank=1,
            source="knowledge/noise.md",
            chunk_index=0,
            score=3,
            text="Token expiration token expiration.",
        ),
        RagRetrievedChunkEvalItem(
            rank=2,
            source="knowledge/security.md",
            chunk_index=0,
            score=2,
            text="Tokens must be signed and must expire.",
        ),
    ]

    assert find_matched_rank(
        retrieved_chunks=retrieved_chunks,
        expected_source="security.md",
        expected_text="Tokens must be signed",
    ) == 2


def test_find_matched_rank_returns_none_when_no_chunk_matches():
    retrieved_chunks = [
        RagRetrievedChunkEvalItem(
            rank=1,
            source="knowledge/noise.md",
            chunk_index=0,
            score=3,
            text="Token expiration token expiration.",
        ),
    ]

    assert find_matched_rank(
        retrieved_chunks=retrieved_chunks,
        expected_source="security.md",
        expected_text="Tokens must be signed",
    ) is None

def test_evaluate_rag_retrieval_case_calculates_rank_two_reciprocal_rank():
    store = InMemoryRagStore()
    store.add_document(
        source="knowledge/noise.md",
        text="token expiration token expiration",
    )
    store.add_document(
        source="knowledge/security.md",
        text="Tokens must be signed and must expire.",
    )

    case = RagRetrievalEvalCase(
        name="token policy",
        query="token expiration",
        expected_source_contains="security.md",
        expected_text_contains="Tokens must be signed",
    )

    result = evaluate_rag_retrieval_case(
        store=store,
        case=case,
        top_k=3,
    )

    assert result.passed is True
    assert result.matched_rank == 2
    assert result.reciprocal_rank == 0.5
    assert result.retrieved_sources == [
        "knowledge/noise.md",
        "knowledge/security.md",
    ]


def test_evaluate_rag_retrieval_calculates_top_1_accuracy_separately_from_hit_rate():
    store = InMemoryRagStore()
    store.add_document(
        source="knowledge/noise.md",
        text="token expiration token expiration",
    )
    store.add_document(
        source="knowledge/security.md",
        text="Tokens must be signed and must expire.",
    )

    summary = evaluate_rag_retrieval(
        store=store,
        cases=[
            RagRetrievalEvalCase(
                name="token policy",
                query="token expiration",
                expected_source_contains="security.md",
                expected_text_contains="Tokens must be signed",
            ),
        ],
        top_k=3,
    )

    assert summary.total_cases == 1
    assert summary.passed_cases == 1
    assert summary.failed_cases == 0
    assert summary.hit_rate == 1.0
    assert summary.top_1_accuracy == 0.0
    assert summary.mean_reciprocal_rank == 0.5
    assert summary.results[0].matched_rank == 2


def test_evaluate_rag_retrieval_case_rejects_store_without_search_method():
    case = RagRetrievalEvalCase(
        name="token policy",
        query="token expiration",
        expected_source_contains="security.md",
        expected_text_contains="Tokens must be signed",
    )

    with pytest.raises(ValueError):
        evaluate_rag_retrieval_case(
            store=object(),
            case=case,
        )
                                       