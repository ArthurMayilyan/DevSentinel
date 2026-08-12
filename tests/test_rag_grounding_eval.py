import json

import pytest

from rag_answer_eval import RagAnswerEvidence
from rag_grounding_eval import (
    RagGroundingEvalCase,
    answer_contains_forbidden_text,
    evaluate_rag_grounding,
    evaluate_rag_grounding_case,
    find_cited_sources_not_in_evidence,
    load_rag_grounding_eval_cases_from_json_file,
)
from rag_pipeline import RagPipelineResult


def build_pipeline_result(
    *,
    answer: str = "Token expiration policy: tokens must be signed and must expire.\n\nSource: security.md",
    cited_sources: list[str] | None = None,
    evidence_sources: list[str] | None = None,
) -> RagPipelineResult:
    if cited_sources is None:
        cited_sources = [
            "security.md",
        ]

    if evidence_sources is None:
        evidence_sources = [
            "security.md",
        ]

    return RagPipelineResult(
        query="token expiration",
        answer=answer,
        cited_sources=cited_sources,
        evidence=[
            RagAnswerEvidence(
                rank=index + 1,
                source=source,
                chunk_index=0,
                score=1,
                text="Token expiration policy: tokens must be signed and must expire.",
            )
            for index, source in enumerate(evidence_sources)
        ],
    )


def test_answer_contains_forbidden_text_detects_case_insensitive_match():
    assert answer_contains_forbidden_text(
        answer="Tokens expire after 24 HOURS.",
        forbidden_answer_contains=[
            "24 hours",
        ],
    ) == [
        "24 hours",
    ]


def test_find_cited_sources_not_in_evidence_returns_invalid_sources():
    assert find_cited_sources_not_in_evidence(
        cited_sources=[
            "security.md",
            "unknown.md",
        ],
        evidence_sources=[
            "security.md",
        ],
    ) == [
        "unknown.md",
    ]


def test_evaluate_rag_grounding_case_passes_grounded_answer():
    case = RagGroundingEvalCase(
        name="token expiration grounding",
        query="token expiration",
        should_have_answer=True,
        forbidden_answer_contains=[
            "24 hours",
        ],
    )

    result = evaluate_rag_grounding_case(
        case=case,
        result=build_pipeline_result(),
    )

    assert result.passed is True
    assert result.failure_reasons == []


def test_evaluate_rag_grounding_case_fails_for_forbidden_claim():
    case = RagGroundingEvalCase(
        name="token expiration grounding",
        query="token expiration",
        should_have_answer=True,
        forbidden_answer_contains=[
            "24 hours",
        ],
    )

    result = evaluate_rag_grounding_case(
        case=case,
        result=build_pipeline_result(
            answer="Token expiration policy says tokens expire after 24 hours.\n\nSource: security.md",
        ),
    )

    assert result.passed is False
    assert any(
        "forbidden" in reason.lower()
        for reason in result.failure_reasons
    )


def test_evaluate_rag_grounding_case_fails_for_citation_not_in_evidence():
    case = RagGroundingEvalCase(
        name="token expiration grounding",
        query="token expiration",
        should_have_answer=True,
        forbidden_answer_contains=[],
    )

    result = evaluate_rag_grounding_case(
        case=case,
        result=build_pipeline_result(
            cited_sources=[
                "security.md",
                "unknown.md",
            ],
            evidence_sources=[
                "security.md",
            ],
        ),
    )

    assert result.passed is False
    assert any(
        "not retrieved" in reason.lower()
        for reason in result.failure_reasons
    )


def test_evaluate_rag_grounding_case_fails_when_answer_expected_but_no_evidence():
    case = RagGroundingEvalCase(
        name="token expiration grounding",
        query="token expiration",
        should_have_answer=True,
        forbidden_answer_contains=[],
    )

    result = evaluate_rag_grounding_case(
        case=case,
        result=RagPipelineResult(
            query="token expiration",
            answer="I do not have enough evidence to answer.",
            cited_sources=[],
            evidence=[],
        ),
    )

    assert result.passed is False
    assert result.failure_reasons


def test_evaluate_rag_grounding_summarizes_results():
    case = RagGroundingEvalCase(
        name="token expiration grounding",
        query="token expiration",
        should_have_answer=True,
        forbidden_answer_contains=[],
    )

    summary = evaluate_rag_grounding(
        cases=[
            case,
        ],
        results_by_case_name={
            "token expiration grounding": build_pipeline_result(),
        },
    )

    assert summary.total_cases == 1
    assert summary.passed_cases == 1
    assert summary.failed_cases == 0
    assert summary.grounding_accuracy == 1.0


def test_evaluate_rag_grounding_rejects_empty_cases():
    with pytest.raises(ValueError):
        evaluate_rag_grounding(
            cases=[],
            results_by_case_name={},
        )


def test_load_rag_grounding_eval_cases_from_json_file_loads_cases(tmp_path):
    cases_path = tmp_path / "grounding_cases.json"
    cases_path.write_text(
        json.dumps(
            [
                {
                    "name": "token expiration grounding",
                    "query": "token expiration",
                    "should_have_answer": True,
                    "forbidden_answer_contains": [
                        "24 hours",
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )

    cases = load_rag_grounding_eval_cases_from_json_file(
        str(cases_path),
    )

    assert len(cases) == 1
    assert cases[0].name == "token expiration grounding"
    assert cases[0].forbidden_answer_contains == [
        "24 hours",
    ]