from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RagAgentEvalCase:
    name: str
    query: str
    expected_answer_contains: list[str]
    forbidden_answer_contains: list[str]


@dataclass(frozen=True)
class RagAgentEvalResult:
    name: str
    query: str
    passed: bool
    answer: str
    search_knowledge_called: bool
    failure_reasons: list[str]


@dataclass(frozen=True)
class RagAgentEvalSummary:
    total_cases: int
    passed_cases: int
    failed_cases: int
    agent_answer_accuracy: float
    results: list[RagAgentEvalResult]


def normalize_text(
    text: str,
) -> str:
    return " ".join(
        text.lower().split()
    )


def validate_rag_agent_eval_case(
    case: RagAgentEvalCase,
) -> None:
    if not isinstance(case.name, str) or not case.name.strip():
        raise ValueError("case name must be a non-empty string.")

    if not isinstance(case.query, str) or not case.query.strip():
        raise ValueError("case query must be a non-empty string.")

    if not isinstance(case.expected_answer_contains, list):
        raise ValueError("expected_answer_contains must be a list.")

    if not case.expected_answer_contains:
        raise ValueError("expected_answer_contains must not be empty.")

    for item in case.expected_answer_contains:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(
                "expected_answer_contains values must be non-empty strings."
            )

    if not isinstance(case.forbidden_answer_contains, list):
        raise ValueError("forbidden_answer_contains must be a list.")

    for item in case.forbidden_answer_contains:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(
                "forbidden_answer_contains values must be non-empty strings."
            )


def answer_contains_all_expected_text(
    *,
    answer: str,
    expected_answer_contains: list[str],
) -> bool:
    normalized_answer = normalize_text(
        answer,
    )

    return all(
        normalize_text(expected_text) in normalized_answer
        for expected_text in expected_answer_contains
    )


def find_forbidden_answer_matches(
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


def trace_has_search_knowledge_call(
    trace_steps: list[dict[str, Any]],
) -> bool:
    for step in trace_steps:
        step_text = str(
            step,
        )

        if "search_knowledge" in step_text:
            return True

    return False


def evaluate_rag_agent_case(
    *,
    case: RagAgentEvalCase,
    answer: str,
    trace_steps: list[dict[str, Any]],
) -> RagAgentEvalResult:
    validate_rag_agent_eval_case(
        case,
    )

    failure_reasons = []

    search_knowledge_called = trace_has_search_knowledge_call(
        trace_steps,
    )

    if not search_knowledge_called:
        failure_reasons.append(
            "Agent did not call search_knowledge."
        )

    if not isinstance(answer, str) or not answer.strip():
        failure_reasons.append(
            "Agent returned an empty answer."
        )
    else:
        if not answer_contains_all_expected_text(
            answer=answer,
            expected_answer_contains=case.expected_answer_contains,
        ):
            failure_reasons.append(
                "Answer did not contain all expected text."
            )

        if "source:" not in normalize_text(
            answer,
        ):
            failure_reasons.append(
                "Answer did not cite a source."
            )

        forbidden_matches = find_forbidden_answer_matches(
            answer=answer,
            forbidden_answer_contains=case.forbidden_answer_contains,
        )

        if forbidden_matches:
            failure_reasons.append(
                f"Answer contained forbidden text: {forbidden_matches}"
            )

    return RagAgentEvalResult(
        name=case.name,
        query=case.query,
        passed=not failure_reasons,
        answer=answer,
        search_knowledge_called=search_knowledge_called,
        failure_reasons=failure_reasons,
    )


def evaluate_rag_agent_cases(
    *,
    cases: list[RagAgentEvalCase],
    answers_by_case_name: dict[str, str],
    trace_steps_by_case_name: dict[str, list[dict[str, Any]]],
) -> RagAgentEvalSummary:
    if not cases:
        raise ValueError("RAG agent eval cases must not be empty.")

    results = []

    for case in cases:
        if case.name not in answers_by_case_name:
            raise ValueError(f"missing answer for case: {case.name}")

        if case.name not in trace_steps_by_case_name:
            raise ValueError(f"missing trace steps for case: {case.name}")

        results.append(
            evaluate_rag_agent_case(
                case=case,
                answer=answers_by_case_name[case.name],
                trace_steps=trace_steps_by_case_name[case.name],
            )
        )

    total_cases = len(
        results,
    )

    passed_cases = sum(
        1
        for result in results
        if result.passed
    )

    return RagAgentEvalSummary(
        total_cases=total_cases,
        passed_cases=passed_cases,
        failed_cases=total_cases - passed_cases,
        agent_answer_accuracy=passed_cases / total_cases,
        results=results,
    )


def rag_agent_eval_summary_to_dict(
    summary: RagAgentEvalSummary,
) -> dict[str, Any]:
    return asdict(
        summary,
    )


def load_rag_agent_eval_cases_from_json_file(
    path: str,
) -> list[RagAgentEvalCase]:
    import json
    from pathlib import Path

    raw = json.loads(
        Path(path).read_text(
            encoding="utf-8",
        )
    )

    if not isinstance(raw, list):
        raise ValueError("RAG agent eval cases file must contain a JSON list.")

    cases = []

    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("each RAG agent eval case must be an object.")

        case = RagAgentEvalCase(
            name=item["name"],
            query=item["query"],
            expected_answer_contains=item["expected_answer_contains"],
            forbidden_answer_contains=item.get(
                "forbidden_answer_contains",
                [],
            ),
        )

        validate_rag_agent_eval_case(
            case,
        )

        cases.append(
            case,
        )

    return cases