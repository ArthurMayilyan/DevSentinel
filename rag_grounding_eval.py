from dataclasses import asdict, dataclass
from typing import Any

from rag_pipeline import RagPipelineResult


@dataclass(frozen=True)
class RagGroundingEvalCase:
    name: str
    query: str
    should_have_answer: bool
    forbidden_answer_contains: list[str]


@dataclass(frozen=True)
class RagGroundingEvalResult:
    name: str
    query: str
    passed: bool
    answer: str
    cited_sources: list[str]
    evidence_sources: list[str]
    failure_reasons: list[str]


@dataclass(frozen=True)
class RagGroundingEvalSummary:
    total_cases: int
    passed_cases: int
    failed_cases: int
    grounding_accuracy: float
    results: list[RagGroundingEvalResult]


def validate_grounding_eval_case(
    case: RagGroundingEvalCase,
) -> None:
    if not isinstance(case.name, str) or not case.name.strip():
        raise ValueError("case name must be a non-empty string.")

    if not isinstance(case.query, str) or not case.query.strip():
        raise ValueError("case query must be a non-empty string.")

    if not isinstance(case.should_have_answer, bool):
        raise ValueError("should_have_answer must be a boolean.")

    if not isinstance(case.forbidden_answer_contains, list):
        raise ValueError("forbidden_answer_contains must be a list.")

    for item in case.forbidden_answer_contains:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(
                "forbidden_answer_contains values must be non-empty strings."
            )


def normalize_text(
    text: str,
) -> str:
    return " ".join(
        text.lower().split()
    )


def answer_contains_forbidden_text(
    *,
    answer: str,
    forbidden_answer_contains: list[str],
) -> list[str]:
    normalized_answer = normalize_text(
        answer,
    )

    return [
        forbidden_text
        for forbidden_text in forbidden_answer_contains
        if normalize_text(forbidden_text) in normalized_answer
    ]


def get_evidence_sources(
    result: RagPipelineResult,
) -> list[str]:
    return [
        item.source
        for item in result.evidence
    ]


def find_cited_sources_not_in_evidence(
    *,
    cited_sources: list[str],
    evidence_sources: list[str],
) -> list[str]:
    evidence_source_set = set(
        evidence_sources,
    )

    return [
        source
        for source in cited_sources
        if source not in evidence_source_set
    ]


def answer_has_no_evidence_message(
    answer: str,
) -> bool:
    return (
        "do not have enough evidence"
        in normalize_text(
            answer,
        )
    )


def evaluate_rag_grounding_case(
    *,
    case: RagGroundingEvalCase,
    result: RagPipelineResult,
) -> RagGroundingEvalResult:
    validate_grounding_eval_case(
        case,
    )

    failure_reasons = []

    evidence_sources = get_evidence_sources(
        result,
    )

    invalid_cited_sources = find_cited_sources_not_in_evidence(
        cited_sources=result.cited_sources,
        evidence_sources=evidence_sources,
    )

    if invalid_cited_sources:
        failure_reasons.append(
            f"answer cited sources that were not retrieved: {invalid_cited_sources}"
        )

    forbidden_matches = answer_contains_forbidden_text(
        answer=result.answer,
        forbidden_answer_contains=case.forbidden_answer_contains,
    )

    if forbidden_matches:
        failure_reasons.append(
            f"answer contains forbidden unsupported text: {forbidden_matches}"
        )

    if case.should_have_answer:
        if answer_has_no_evidence_message(
            result.answer,
        ):
            failure_reasons.append(
                "answer said there was not enough evidence, but case expected an answer."
            )

        if not result.evidence:
            failure_reasons.append(
                "case expected an answer, but no evidence was retrieved."
            )

        if not result.cited_sources:
            failure_reasons.append(
                "case expected an answer, but no sources were cited."
            )

    if not case.should_have_answer:
        if result.evidence:
            failure_reasons.append(
                "case expected no answer, but evidence was retrieved."
            )

        if not answer_has_no_evidence_message(
            result.answer,
        ):
            failure_reasons.append(
                "case expected no answer, but answer did not say evidence was insufficient."
            )

    return RagGroundingEvalResult(
        name=case.name,
        query=case.query,
        passed=not failure_reasons,
        answer=result.answer,
        cited_sources=result.cited_sources,
        evidence_sources=evidence_sources,
        failure_reasons=failure_reasons,
    )


def evaluate_rag_grounding(
    *,
    cases: list[RagGroundingEvalCase],
    results_by_case_name: dict[str, RagPipelineResult],
) -> RagGroundingEvalSummary:
    if not cases:
        raise ValueError("grounding eval cases must not be empty.")

    results = []

    for case in cases:
        if case.name not in results_by_case_name:
            raise ValueError(f"missing pipeline result for case: {case.name}")

        results.append(
            evaluate_rag_grounding_case(
                case=case,
                result=results_by_case_name[case.name],
            )
        )

    passed_cases = sum(
        1
        for result in results
        if result.passed
    )

    total_cases = len(
        results,
    )

    return RagGroundingEvalSummary(
        total_cases=total_cases,
        passed_cases=passed_cases,
        failed_cases=total_cases - passed_cases,
        grounding_accuracy=passed_cases / total_cases,
        results=results,
    )


def rag_grounding_eval_summary_to_dict(
    summary: RagGroundingEvalSummary,
) -> dict[str, Any]:
    return asdict(
        summary,
    )


def load_rag_grounding_eval_cases_from_json_file(
    path: str,
) -> list[RagGroundingEvalCase]:
    import json
    from pathlib import Path

    raw = json.loads(
        Path(path).read_text(
            encoding="utf-8",
        )
    )

    if not isinstance(raw, list):
        raise ValueError("grounding eval cases file must contain a JSON list.")

    cases = []

    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("each grounding eval case must be an object.")

        case = RagGroundingEvalCase(
            name=item["name"],
            query=item["query"],
            should_have_answer=item["should_have_answer"],
            forbidden_answer_contains=item.get(
                "forbidden_answer_contains",
                [],
            ),
        )

        validate_grounding_eval_case(
            case,
        )

        cases.append(
            case,
        )

    return cases