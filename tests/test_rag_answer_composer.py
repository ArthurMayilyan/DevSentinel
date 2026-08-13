import pytest

from rag_answer_composer import (
    compose_rag_answer,
    select_relevant_sentences,
    split_into_sentences,
)


def build_security_evidence():
    return [
        {
            "source": "knowledge_base_noisy\\security.md",
            "text": (
                "# Security Policy\n\n"
                "Token expiration policy: tokens must be signed and must expire.\n"
                "Credentials must not be hardcoded in source code.\n"
                "Debug mode must be disabled in production."
            ),
        }
    ]


def test_split_into_sentences_ignores_markdown_headings():
    assert split_into_sentences(
        "# Security Policy\n\n"
        "Token expiration policy: tokens must be signed and must expire."
    ) == [
        "Token expiration policy: tokens must be signed and must expire.",
    ]


def test_select_relevant_sentences_selects_query_matching_sentence():
    selected = select_relevant_sentences(
        query="token expiration",
        evidence=build_security_evidence(),
        max_sentences=1,
    )

    assert selected == [
        (
            0,
            "knowledge_base_noisy\\security.md",
            "Token expiration policy: tokens must be signed and must expire.",
        )
    ]


def test_compose_rag_answer_returns_short_query_relevant_answer():
    composed = compose_rag_answer(
        query="token expiration",
        evidence=build_security_evidence(),
        max_sentences=1,
    )

    assert composed.answer == (
        "Token expiration policy: tokens must be signed and must expire.\n\n"
        "Source: knowledge_base_noisy\\security.md"
    )
    assert composed.source == "knowledge_base_noisy\\security.md"
    assert composed.selected_sentences == [
        "Token expiration policy: tokens must be signed and must expire.",
    ]
    assert composed.used_evidence_indexes == [
        0,
    ]
    assert composed.fallback_used is False


def test_compose_rag_answer_falls_back_to_first_sentence_when_no_query_match():
    composed = compose_rag_answer(
        query="unknown topic",
        evidence=build_security_evidence(),
        max_sentences=1,
    )

    assert composed.answer == (
        "Token expiration policy: tokens must be signed and must expire.\n\n"
        "Source: knowledge_base_noisy\\security.md"
    )
    assert composed.fallback_used is True


def test_compose_rag_answer_returns_insufficient_evidence_when_empty():
    composed = compose_rag_answer(
        query="token expiration",
        evidence=[],
    )

    assert composed.answer == "I do not have enough evidence to answer."
    assert composed.source == ""
    assert composed.selected_sentences == []
    assert composed.used_evidence_indexes == []
    assert composed.fallback_used is True


def test_compose_rag_answer_rejects_empty_query():
    with pytest.raises(ValueError):
        compose_rag_answer(
            query="",
            evidence=build_security_evidence(),
        )