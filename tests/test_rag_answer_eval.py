import pytest
import json

from rag_answer_eval import (
    RagAnswerEvalCase,
    RagAnswerEvidence,
    answer_contains,
    build_evidence_from_store,
    build_rag_answer,
    evaluate_rag_answer_case,
    evaluate_rag_answers,
    source_contains,
)
from rag_store import InMemoryRagStore


def build_test_store() -> InMemoryRagStore:
    store = InMemoryRagStore()

    store.add_document(
        source="knowledge_base/security.md",
        text=(
            "Token expiration policy: tokens must be signed "
            "and must expire."
        ),
    )

    store.add_document(
        source="knowledge_base/coding.md",
        text=(
            "Small function guidelines: functions should be "
            "small and readable."
        ),
    )

    return store


def evidence_answer_builder(
    *,
    query: str,
    evidence: list[RagAnswerEvidence],
) -> str:
    if not evidence:
        return "I do not have enough evidence to answer."

    return evidence[0].text


def empty_answer_builder(
    *,
    query: str,
    evidence: list[RagAnswerEvidence],
) -> str:
    return ""


def wrong_answer_builder(
    *,
    query: str,
    evidence: list[RagAnswerEvidence],
) -> str:
    return "This answer is unrelated."


def test_build_evidence_from_store_returns_ranked_evidence():
    store = build_test_store()

    evidence = build_evidence_from_store(
        store=store,
        query="token expiration",
        top_k=1,
    )

    assert len(evidence) == 1
    assert evidence[0].rank == 1
    assert evidence[0].source == "knowledge_base/security.md"
    assert "Token expiration policy" in evidence[0].text


def test_build_rag_answer_uses_answer_builder():
    store = build_test_store()

    result = build_rag_answer(
        store=store,
        query="token expiration",
        answer_builder=evidence_answer_builder,
        top_k=1,
    )

    assert result.query == "token expiration"
    assert "Token expiration policy" in result.answer
    assert result.evidence[0].source == "knowledge_base/security.md"


def test_source_contains_is_case_insensitive():
    assert (
        source_contains(
            source="knowledge_base/Security.md",
            expected_source_contains="security.md",
        )
        is True
    )


def test_answer_contains_is_case_insensitive():
    assert (
        answer_contains(
            answer="Token Expiration Policy",
            expected_answer_contains="token expiration",
        )
        is True
    )


def test_evaluate_rag_answer_case_passes_when_answer_and_source_match():
    store = build_test_store()

    result = evaluate_rag_answer_case(
        store=store,
        case=RagAnswerEvalCase(
            name="token expiration policy",
            query="token expiration",
            expected_answer_contains="Token expiration policy",
            expected_source_contains="security.md",
        ),
        answer_builder=evidence_answer_builder,
        top_k=1,
    )

    assert result.passed is True
    assert result.failure_reasons == []
    assert result.cited_sources == [
        "knowledge_base/security.md",
    ]


def test_evaluate_rag_answer_case_fails_when_answer_is_empty():
    store = build_test_store()

    result = evaluate_rag_answer_case(
        store=store,
        case=RagAnswerEvalCase(
            name="token expiration policy",
            query="token expiration",
            expected_answer_contains="Token expiration policy",
            expected_source_contains="security.md",
        ),
        answer_builder=empty_answer_builder,
        top_k=1,
    )

    assert result.passed is False
    assert "answer is empty" in result.failure_reasons
    assert "answer does not contain expected text" in result.failure_reasons


def test_evaluate_rag_answer_case_fails_when_answer_text_is_wrong():
    store = build_test_store()

    result = evaluate_rag_answer_case(
        store=store,
        case=RagAnswerEvalCase(
            name="token expiration policy",
            query="token expiration",
            expected_answer_contains="Token expiration policy",
            expected_source_contains="security.md",
        ),
        answer_builder=wrong_answer_builder,
        top_k=1,
    )

    assert result.passed is False
    assert "answer does not contain expected text" in result.failure_reasons


def test_evaluate_rag_answer_case_fails_when_expected_source_is_not_cited():
    store = build_test_store()

    result = evaluate_rag_answer_case(
        store=store,
        case=RagAnswerEvalCase(
            name="token expiration policy",
            query="token expiration",
            expected_answer_contains="Token expiration policy",
            expected_source_contains="missing.md",
        ),
        answer_builder=evidence_answer_builder,
        top_k=1,
    )

    assert result.passed is False
    assert "expected source was not cited" in result.failure_reasons


def test_evaluate_rag_answers_returns_summary():
    store = build_test_store()

    summary = evaluate_rag_answers(
        store=store,
        cases=[
            RagAnswerEvalCase(
                name="token expiration policy",
                query="token expiration",
                expected_answer_contains="Token expiration policy",
                expected_source_contains="security.md",
            ),
            RagAnswerEvalCase(
                name="small function guideline",
                query="small function",
                expected_answer_contains="Small function guidelines",
                expected_source_contains="coding.md",
            ),
        ],
        answer_builder=evidence_answer_builder,
        top_k=1,
    )

    assert summary.total_cases == 2
    assert summary.passed_cases == 2
    assert summary.failed_cases == 0
    assert summary.answer_accuracy == 1.0


def test_evaluate_rag_answers_rejects_empty_cases():
    store = build_test_store()

    with pytest.raises(ValueError):
        evaluate_rag_answers(
            store=store,
            cases=[],
            answer_builder=evidence_answer_builder,
            top_k=1,
        )


def test_build_rag_answer_rejects_non_string_answer():
    store = build_test_store()

    def invalid_answer_builder(
        *,
        query: str,
        evidence: list[RagAnswerEvidence],
    ) -> str:
        return 123  # type: ignore[return-value]

    with pytest.raises(ValueError):
        build_rag_answer(
            store=store,
            query="token expiration",
            answer_builder=invalid_answer_builder,
            top_k=1,
        )

def test_load_rag_answer_eval_cases_from_json_file_loads_cases(tmp_path):
    from rag_answer_eval import load_rag_answer_eval_cases_from_json_file

    cases_path = tmp_path / "rag_answer_eval_cases.json"
    cases_path.write_text(
        json.dumps(
            [
                {
                    "name": "token expiration answer",
                    "query": "token expiration",
                    "expected_answer_contains": "Token expiration policy",
                    "expected_source_contains": "security.md",
                }
            ]
        ),
        encoding="utf-8",
    )

    cases = load_rag_answer_eval_cases_from_json_file(
        str(cases_path),
    )

    assert len(cases) == 1
    assert cases[0].name == "token expiration answer"
    assert cases[0].query == "token expiration"
    assert cases[0].expected_answer_contains == "Token expiration policy"
    assert cases[0].expected_source_contains == "security.md"


def test_load_rag_answer_eval_cases_from_json_file_rejects_non_list(tmp_path):
    from rag_answer_eval import load_rag_answer_eval_cases_from_json_file

    cases_path = tmp_path / "rag_answer_eval_cases.json"
    cases_path.write_text(
        json.dumps(
            {
                "name": "not a list",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_rag_answer_eval_cases_from_json_file(
            str(cases_path),
        )


def test_load_rag_answer_eval_cases_from_json_file_rejects_missing_field(tmp_path):
    from rag_answer_eval import load_rag_answer_eval_cases_from_json_file

    cases_path = tmp_path / "rag_answer_eval_cases.json"
    cases_path.write_text(
        json.dumps(
            [
                {
                    "name": "token expiration answer",
                    "query": "token expiration",
                    "expected_answer_contains": "Token expiration policy",
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_rag_answer_eval_cases_from_json_file(
            str(cases_path),
        )        