from dataclasses import dataclass, field
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
class RagRetrievedChunkEvalItem:
    rank: int
    source: str
    chunk_index: int
    score: int | float
    text: str

    def __post_init__(self) -> None:
        if type(self.rank) is not int:
            raise ValueError("rank must be an integer.")

        if self.rank <= 0:
            raise ValueError("rank must be greater than 0.")

        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("source must be a non-empty string.")

        if type(self.chunk_index) is not int:
            raise ValueError("chunk_index must be an integer.")

        if self.chunk_index < 0:
            raise ValueError("chunk_index must be greater than or equal to 0.")

        if isinstance(self.score, bool) or not isinstance(self.score, int | float):
            raise ValueError("score must be a number.")

        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("text must be a non-empty string.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "source": self.source,
            "chunk_index": self.chunk_index,
            "score": self.score,
            "text": self.text,
        }


def find_matched_rank(
    *,
    retrieved_chunks: list[RagRetrievedChunkEvalItem],
    expected_source: str,
    expected_text: str,
) -> int | None:
    normalized_expected_text = expected_text.lower()

    for chunk in retrieved_chunks:
        if (
            source_matches_expected_source(
                source=chunk.source,
                expected_source=expected_source,
            )
            and normalized_expected_text in chunk.text.lower()
        ):
            return chunk.rank

    return None


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
    matched_rank: int | None = None
    reciprocal_rank: float = 0.0
    retrieved_chunks: list[RagRetrievedChunkEvalItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "query": self.query,
            "passed": self.passed,
            "expected_source_contains": self.expected_source_contains,
            "expected_text_contains": self.expected_text_contains,
            "retrieved_sources": self.retrieved_sources,
            "retrieved_texts": self.retrieved_texts,
            "matched_rank": self.matched_rank,
            "reciprocal_rank": self.reciprocal_rank,
            "retrieved_chunks": [
                chunk.to_dict()
                for chunk in self.retrieved_chunks
            ],
        }


@dataclass(frozen=True)
class RagRetrievalEvalSummary:
    total_cases: int
    passed_cases: int
    failed_cases: int
    hit_rate: float
    top_1_accuracy: float
    mean_reciprocal_rank: float
    results: list[RagRetrievalEvalResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_cases": self.total_cases,
            "passed_cases": self.passed_cases,
            "failed_cases": self.failed_cases,
            "hit_rate": self.hit_rate,
            "top_1_accuracy": self.top_1_accuracy,
            "mean_reciprocal_rank": self.mean_reciprocal_rank,
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

    retrieved_items = [
        RagRetrievedChunkEvalItem(
            rank=index + 1,
            source=chunk.source,
            chunk_index=chunk.chunk_index,
            score=chunk.score,
            text=chunk.text,
        )
        for index, chunk in enumerate(retrieved_chunks)
    ]

    matched_rank = find_matched_rank(
        retrieved_chunks=retrieved_items,
        expected_source=case.expected_source_contains,
        expected_text=case.expected_text_contains,
    )

    reciprocal_rank = 0.0
    if matched_rank is not None:
        reciprocal_rank = 1.0 / matched_rank

    passed = matched_rank is not None

    return RagRetrievalEvalResult(
        name=case.name,
        query=case.query,
        passed=passed,
        expected_source_contains=case.expected_source_contains,
        expected_text_contains=case.expected_text_contains,
        retrieved_sources=[
            item.source
            for item in retrieved_items
        ],
        retrieved_texts=[
            item.text
            for item in retrieved_items
        ],
        matched_rank=matched_rank,
        reciprocal_rank=reciprocal_rank,
        retrieved_chunks=retrieved_items,
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

    top_1_matches = sum(
        1
        for result in results
        if result.matched_rank == 1
    )

    top_1_accuracy = top_1_matches / total_cases

    mean_reciprocal_rank = sum(
        result.reciprocal_rank
        for result in results
    ) / total_cases

    return RagRetrievalEvalSummary(
        total_cases=total_cases,
        passed_cases=passed_cases,
        failed_cases=failed_cases,
        hit_rate=passed_cases / total_cases,
        top_1_accuracy=top_1_accuracy,
        mean_reciprocal_rank=mean_reciprocal_rank,
        results=results,
    )
