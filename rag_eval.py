from dataclasses import dataclass
from typing import Any

from rag_store import InMemoryRagStore


def normalize_source_path(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("source path value must be a non-empty string.")

    return value.strip().lower().replace("\\", "/")


def source_matches_expected_source(
    *,
    source: str,
    expected_source: str,
) -> bool:
    normalized_source = normalize_source_path(source)
    normalized_expected = normalize_source_path(expected_source)

    if "/" in normalized_expected:
        return normalized_source.endswith(normalized_expected)

    source_file_name = normalized_source.split("/")[-1]

    return source_file_name == normalized_expected


@dataclass(frozen=True)
class RagRetrievalEvalCase:
    name: str
    query: str
    expected_source_contains: str
    expected_text_contains: str

    def __post_init__(self) -> None:
        self._validate_non_empty_string("name", self.name)
        self._validate_non_empty_string("query", self.query)
        self._validate_non_empty_string(
            "expected_source_contains",
            self.expected_source_contains,
        )
        self._validate_non_empty_string(
            "expected_text_contains",
            self.expected_text_contains,
        )

    @staticmethod
    def _validate_non_empty_string(name: str, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string.")


@dataclass(frozen=True)
class RagRetrievalEvalResult:
    name: str
    query: str
    passed: bool
    expected_source_contains: str
    expected_text_contains: str
    retrieved_sources: list[str]
    retrieved_texts: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "query": self.query,
            "passed": self.passed,
            "expected_source_contains": self.expected_source_contains,
            "expected_text_contains": self.expected_text_contains,
            "retrieved_sources": self.retrieved_sources,
            "retrieved_texts": self.retrieved_texts,
        }


@dataclass(frozen=True)
class RagRetrievalEvalSummary:
    total_cases: int
    passed_cases: int
    failed_cases: int
    hit_rate: float
    results: list[RagRetrievalEvalResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_cases": self.total_cases,
            "passed_cases": self.passed_cases,
            "failed_cases": self.failed_cases,
            "hit_rate": self.hit_rate,
            "results": [
                result.to_dict()
                for result in self.results
            ],
        }


def evaluate_rag_retrieval_case(
    *,
    store: InMemoryRagStore,
    case: RagRetrievalEvalCase,
    top_k: int = 3,
) -> RagRetrievalEvalResult:
    if not isinstance(store, InMemoryRagStore):
        raise ValueError("store must be an InMemoryRagStore.")

    if not isinstance(case, RagRetrievalEvalCase):
        raise ValueError("case must be a RagRetrievalEvalCase.")

    retrieved_chunks = store.search(
        query=case.query,
        top_k=top_k,
    )

    expected_text = case.expected_text_contains.lower()

    passed = any(
        source_matches_expected_source(
            source=chunk.source,
            expected_source=case.expected_source_contains,
        )
        and expected_text in chunk.text.lower()
        for chunk in retrieved_chunks
    )

    return RagRetrievalEvalResult(
        name=case.name,
        query=case.query,
        passed=passed,
        expected_source_contains=case.expected_source_contains,
        expected_text_contains=case.expected_text_contains,
        retrieved_sources=[
            chunk.source
            for chunk in retrieved_chunks
        ],
        retrieved_texts=[
            chunk.text
            for chunk in retrieved_chunks
        ],
    )


def evaluate_rag_retrieval(
    *,
    store: InMemoryRagStore,
    cases: list[RagRetrievalEvalCase],
    top_k: int = 3,
) -> RagRetrievalEvalSummary:
    if not isinstance(store, InMemoryRagStore):
        raise ValueError("store must be an InMemoryRagStore.")

    if not isinstance(cases, list):
        raise ValueError("cases must be a list.")

    if not cases:
        raise ValueError("cases must not be empty.")

    if type(top_k) is not int:
        raise ValueError("top_k must be an integer.")

    if top_k <= 0:
        raise ValueError("top_k must be greater than 0.")

    results = [
        evaluate_rag_retrieval_case(
            store=store,
            case=case,
            top_k=top_k,
        )
        for case in cases
    ]

    passed_cases = sum(
        1
        for result in results
        if result.passed
    )

    total_cases = len(results)
    failed_cases = total_cases - passed_cases

    return RagRetrievalEvalSummary(
        total_cases=total_cases,
        passed_cases=passed_cases,
        failed_cases=failed_cases,
        hit_rate=passed_cases / total_cases,
        results=results,
    )

