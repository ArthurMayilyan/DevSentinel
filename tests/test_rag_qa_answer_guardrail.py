from rag_qa_answer_guardrail import (
    INSUFFICIENT_EVIDENCE_ANSWER,
    answer_cites_evidence_source,
    answer_has_evidence_overlap,
    build_evidence_fallback_answer,
    validate_rag_qa_answer,
)


def build_evidence():
    return [
        {
            "source": "knowledge_base_noisy\\security.md",
            "text": "Token expiration policy: tokens must be signed and must expire.",
        }
    ]


def test_answer_cites_evidence_source_accepts_full_source_path():
    assert (
        answer_cites_evidence_source(
            answer=(
                "Tokens must be signed and must expire. "
                "Source: knowledge_base_noisy\\security.md"
            ),
            evidence=build_evidence(),
        )
        is True
    )


def test_answer_cites_evidence_source_accepts_basename():
    assert (
        answer_cites_evidence_source(
            answer="Tokens must be signed. Source: security.md",
            evidence=build_evidence(),
        )
        is True
    )


def test_answer_cites_evidence_source_rejects_unknown_source():
    assert (
        answer_cites_evidence_source(
            answer="Tokens must be signed. Source: unknown.md",
            evidence=build_evidence(),
        )
        is False
    )


def test_answer_has_evidence_overlap_passes_when_content_matches():
    assert (
        answer_has_evidence_overlap(
            answer="Tokens must be signed and must expire. Source: security.md",
            evidence=build_evidence(),
        )
        is True
    )


def test_answer_has_evidence_overlap_fails_when_content_unrelated():
    assert (
        answer_has_evidence_overlap(
            answer="OAuth refresh tokens expire after 24 hours. Source: security.md",
            evidence=build_evidence(),
        )
        is False
    )


def test_validate_rag_qa_answer_passes_grounded_answer():
    result = validate_rag_qa_answer(
        answer="Tokens must be signed and must expire. Source: security.md",
        evidence=build_evidence(),
    )

    assert result.passed is True
    assert result.failure_reasons == []


def test_validate_rag_qa_answer_fails_when_source_missing():
    result = validate_rag_qa_answer(
        answer="Tokens must be signed and must expire.",
        evidence=build_evidence(),
    )

    assert result.passed is False
    assert "answer must cite a retrieved evidence source." in result.failure_reasons


def test_validate_rag_qa_answer_fails_when_source_not_retrieved():
    result = validate_rag_qa_answer(
        answer="Tokens must be signed and must expire. Source: unknown.md",
        evidence=build_evidence(),
    )

    assert result.passed is False
    assert "answer must cite a retrieved evidence source." in result.failure_reasons


def test_validate_rag_qa_answer_allows_insufficient_evidence_fallback_with_empty_evidence():
    result = validate_rag_qa_answer(
        answer=INSUFFICIENT_EVIDENCE_ANSWER,
        evidence=[],
    )

    assert result.passed is True


def test_validate_rag_qa_answer_rejects_non_fallback_answer_with_empty_evidence():
    result = validate_rag_qa_answer(
        answer="Token expiration policy. Source: security.md",
        evidence=[],
    )

    assert result.passed is False
    assert (
        "answer must use insufficient evidence fallback when evidence is empty."
        in result.failure_reasons
    )


def test_build_evidence_fallback_answer_uses_first_evidence_item():
    assert build_evidence_fallback_answer(
        evidence=build_evidence(),
    ) == (
        "Token expiration policy: tokens must be signed and must expire.\n\n"
        "Source: knowledge_base_noisy\\security.md"
    )


def test_build_evidence_fallback_answer_returns_insufficient_evidence_when_empty():
    assert build_evidence_fallback_answer(
        evidence=[],
    ) == INSUFFICIENT_EVIDENCE_ANSWER



def test_build_evidence_fallback_answer_uses_query_relevant_sentence():
    answer = build_evidence_fallback_answer(
        query="token expiration",
        evidence=[
            {
                "source": "security.md",
                "text": (
                    "# Security Policy\n\n"
                    "Token expiration policy: tokens must be signed and must expire.\n"
                    "Credentials must not be hardcoded in source code.\n"
                    "Debug mode must be disabled in production."
                ),
            }
        ],
    )

    assert answer == (
        "Token expiration policy: tokens must be signed and must expire.\n\n"
        "Source: security.md"
    )
        