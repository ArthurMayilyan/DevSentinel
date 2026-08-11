from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Protocol

from rag_search_engine import RagSearchEngine, validate_rag_search_engine


@dataclass(frozen=True)
class RagAnswerEvidence:
    rank: int
    source: str
    chunk_index: int
    score: int
    text: str


@dataclass(frozen=True)
class RagAnswerEvalCase:
    name: str
    query: str
    expected_answer_contains: str
    expected_source_contains: str


@dataclass(frozen=True)
class RagAnswerResult:
    query: str
    answer: str
    evidence: list[RagAnswerEvidence]


@dataclass(frozen=True)
class RagAnswerEvalResult:
    name: str
    query: str
    passed: bool
    answer: str
    cited_sources: list[str]
    expected_answer_contains: str
    expected_source_contains: str
    failure_reasons: list[str]


@dataclass(frozen=True)
class RagAnswerEvalSummary:
    total_cases: int
    passed_cases: int
    failed_cases: int
    answer_accuracy: float
    results: list[RagAnswerEvalResult]


class RagAnswerBuilder(Protocol):
    def __call__(
        self,
        *,
        query: str,
        evidence: list[RagAnswerEvidence],
    ) -> str:
        ...


def validate_answer_eval_case(
    case: RagAnswerEvalCase,
) -> None:
    if not isinstance(case, RagAnswerEvalCase):
        raise ValueError("case must be a RagAnswerEvalCase.")

    if not case.name.strip():
        raise ValueError("case name must not be empty.")

    if not case.query.strip():
        raise ValueError("case query must not be empty.")

    if not case.expected_answer_contains.strip():
        raise ValueError("expected_answer_contains must not be empty.")

    if not case.expected_source_contains.strip():
        raise ValueError("expected_source_contains must not be empty.")


def validate_answer_builder(
    answer_builder: RagAnswerBuilder,
) -> None:
    if not callable(answer_builder):
        raise ValueError("answer_builder must be callable.")

def load_rag_answer_eval_cases_from_json_file(
    path: str,
) -> list[RagAnswerEvalCase]:
    cases_path = Path(path)

    if not cases_path.is_file():
        raise ValueError(f"cases path must be a file: {path}")

    raw_cases = json.loads(
        cases_path.read_text(
            encoding="utf-8",
        )
    )

    if not isinstance(raw_cases, list):
        raise ValueError("answer eval cases file must contain a JSON list.")

    cases = []

    for index, raw_case in enumerate(raw_cases):
        if not isinstance(raw_case, dict):
            raise ValueError(
                f"answer eval case at index {index} must be an object."
            )

        try:
            case = RagAnswerEvalCase(
                name=raw_case["name"],
                query=raw_case["query"],
                expected_answer_contains=raw_case[
                    "expected_answer_contains"
                ],
                expected_source_contains=raw_case[
                    "expected_source_contains"
                ],
            )
        except KeyError as error:
            raise ValueError(
                f"answer eval case at index {index} is missing field: "
                f"{error.args[0]}"
            ) from error

        validate_answer_eval_case(
            case,
        )

        cases.append(
            case,
        )

    if not cases:
        raise ValueError("answer eval cases file must not be empty.")

    return cases

def build_evidence_from_store(
    *,
    store: RagSearchEngine,
    query: str,
    top_k: int = 3,
) -> list[RagAnswerEvidence]:
    validate_rag_search_engine(
        store,
    )

    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string.")

    if type(top_k) is not int:
        raise ValueError("top_k must be an integer.")

    if top_k <= 0:
        raise ValueError("top_k must be greater than 0.")

    retrieved_chunks = store.search(
        query=query,
        top_k=top_k,
    )

    return [
        RagAnswerEvidence(
            rank=index + 1,
            source=chunk.source,
            chunk_index=chunk.chunk_index,
            score=chunk.score,
            text=chunk.text,
        )
        for index, chunk in enumerate(retrieved_chunks)
    ]


def build_rag_answer(
    *,
    store: RagSearchEngine,
    query: str,
    answer_builder: RagAnswerBuilder,
    top_k: int = 3,
) -> RagAnswerResult:
    validate_answer_builder(
        answer_builder,
    )

    evidence = build_evidence_from_store(
        store=store,
        query=query,
        top_k=top_k,
    )

    answer = answer_builder(
        query=query,
        evidence=evidence,
    )

    if not isinstance(answer, str):
        raise ValueError("answer_builder must return a string.")

    return RagAnswerResult(
        query=query,
        answer=answer,
        evidence=evidence,
    )


def source_contains(
    *,
    source: str,
    expected_source_contains: str,
) -> bool:
    return expected_source_contains.lower() in source.lower()


def answer_contains(
    *,
    answer: str,
    expected_answer_contains: str,
) -> bool:
    return expected_answer_contains.lower() in answer.lower()


def evaluate_rag_answer_case(
    *,
    store: RagSearchEngine,
    case: RagAnswerEvalCase,
    answer_builder: RagAnswerBuilder,
    top_k: int = 3,
) -> RagAnswerEvalResult:
    validate_answer_eval_case(
        case,
    )

    result = build_rag_answer(
        store=store,
        query=case.query,
        answer_builder=answer_builder,
        top_k=top_k,
    )

    cited_sources = [
        evidence.source
        for evidence in result.evidence
    ]

    failure_reasons = []

    if not result.answer.strip():
        failure_reasons.append(
            "answer is empty"
        )

    if not answer_contains(
        answer=result.answer,
        expected_answer_contains=case.expected_answer_contains,
    ):
        failure_reasons.append(
            "answer does not contain expected text"
        )

    if not any(
        source_contains(
            source=source,
            expected_source_contains=case.expected_source_contains,
        )
        for source in cited_sources
    ):
        failure_reasons.append(
            "expected source was not cited"
        )

    return RagAnswerEvalResult(
        name=case.name,
        query=case.query,
        passed=not failure_reasons,
        answer=result.answer,
        cited_sources=cited_sources,
        expected_answer_contains=case.expected_answer_contains,
        expected_source_contains=case.expected_source_contains,
        failure_reasons=failure_reasons,
    )


def evaluate_rag_answers(
    *,
    store: RagSearchEngine,
    cases: list[RagAnswerEvalCase],
    answer_builder: RagAnswerBuilder,
    top_k: int = 3,
) -> RagAnswerEvalSummary:
    validate_rag_search_engine(
        store,
    )

    if not isinstance(cases, list):
        raise ValueError("cases must be a list.")

    if not cases:
        raise ValueError("cases must not be empty.")

    results = [
        evaluate_rag_answer_case(
            store=store,
            case=case,
            answer_builder=answer_builder,
            top_k=top_k,
        )
        for case in cases
    ]

    passed_cases = sum(
        1
        for result in results
        if result.passed
    )

    failed_cases = len(results) - passed_cases

    return RagAnswerEvalSummary(
        total_cases=len(results),
        passed_cases=passed_cases,
        failed_cases=failed_cases,
        answer_accuracy=passed_cases / len(results),
        results=results,
    )

