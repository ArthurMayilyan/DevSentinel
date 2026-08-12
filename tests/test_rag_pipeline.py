import pytest

from rag_pipeline import (
    build_cited_extractive_answer_from_evidence,
    build_extractive_answer_from_evidence,
    rag_pipeline_result_to_dict,
    retrieve_evidence,
    run_rag_pipeline,
)
from rag_store import InMemoryRagStore


def build_test_store() -> InMemoryRagStore:
    store = InMemoryRagStore()

    store.add_document(
        source="knowledge_base/security.md",
        text="Token expiration policy: tokens must be signed and must expire.",
    )

    store.add_document(
        source="knowledge_base/coding.md",
        text="Small function guidelines: functions should be small and readable.",
    )

    return store


def test_retrieve_evidence_returns_ranked_evidence():
    store = build_test_store()

    evidence = retrieve_evidence(
        store=store,
        query="token expiration",
        top_k=1,
    )

    assert len(evidence) == 1
    assert evidence[0].rank == 1
    assert evidence[0].source == "knowledge_base/security.md"
    assert "Token expiration policy" in evidence[0].text


def test_retrieve_evidence_rejects_empty_query():
    store = build_test_store()

    with pytest.raises(ValueError):
        retrieve_evidence(
            store=store,
            query="",
            top_k=1,
        )


def test_build_extractive_answer_from_evidence_returns_best_evidence_text():
    store = build_test_store()

    evidence = retrieve_evidence(
        store=store,
        query="small function",
        top_k=1,
    )

    answer = build_extractive_answer_from_evidence(
        query="small function",
        evidence=evidence,
    )

    assert "Small function guidelines" in answer


def test_build_extractive_answer_from_evidence_handles_empty_evidence():
    answer = build_extractive_answer_from_evidence(
        query="unknown",
        evidence=[],
    )

    assert answer == "I do not have enough evidence to answer."


def test_build_cited_extractive_answer_from_evidence_includes_source():
    store = build_test_store()

    evidence = retrieve_evidence(
        store=store,
        query="token expiration",
        top_k=1,
    )

    answer = build_cited_extractive_answer_from_evidence(
        query="token expiration",
        evidence=evidence,
    )

    assert "Token expiration policy" in answer
    assert "Source: knowledge_base/security.md" in answer


def test_run_rag_pipeline_returns_answer_sources_and_evidence():
    store = build_test_store()

    result = run_rag_pipeline(
        store=store,
        query="token expiration",
        top_k=1,
    )

    assert result.query == "token expiration"
    assert "Token expiration policy" in result.answer
    assert result.cited_sources == [
        "knowledge_base/security.md",
    ]
    assert len(result.evidence) == 1


def test_rag_pipeline_result_to_dict_converts_result():
    store = build_test_store()

    result = run_rag_pipeline(
        store=store,
        query="token expiration",
        top_k=1,
    )

    output = rag_pipeline_result_to_dict(
        result,
    )

    assert output["query"] == "token expiration"
    assert "Token expiration policy" in output["answer"]
    assert output["cited_sources"] == [
        "knowledge_base/security.md",
    ]
    assert output["evidence"][0]["source"] == "knowledge_base/security.md"