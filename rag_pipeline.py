from dataclasses import asdict, dataclass
from typing import Any

from rag_answer_eval import RagAnswerEvidence
from rag_search_engine import RagSearchEngine, validate_rag_search_engine


@dataclass(frozen=True)
class RagPipelineResult:
    query: str
    answer: str
    cited_sources: list[str]
    evidence: list[RagAnswerEvidence]


def build_extractive_answer_from_evidence(
    *,
    query: str,
    evidence: list[RagAnswerEvidence],
) -> str:
    if not evidence:
        return "I do not have enough evidence to answer."

    best_evidence = evidence[0]

    return best_evidence.text


def build_cited_extractive_answer_from_evidence(
    *,
    query: str,
    evidence: list[RagAnswerEvidence],
) -> str:
    if not evidence:
        return "I do not have enough evidence to answer."

    best_evidence = evidence[0]

    return (
        f"{best_evidence.text}\n\n"
        f"Source: {best_evidence.source}"
    )


def retrieve_evidence(
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

    chunks = store.search(
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
        for index, chunk in enumerate(chunks)
    ]


def run_rag_pipeline(
    *,
    store: RagSearchEngine,
    query: str,
    top_k: int = 3,
) -> RagPipelineResult:
    evidence = retrieve_evidence(
        store=store,
        query=query,
        top_k=top_k,
    )

    answer = build_cited_extractive_answer_from_evidence(
        query=query,
        evidence=evidence,
    )

    cited_sources = [
        item.source
        for item in evidence
    ]

    return RagPipelineResult(
        query=query,
        answer=answer,
        cited_sources=cited_sources,
        evidence=evidence,
    )


def rag_pipeline_result_to_dict(
    result: RagPipelineResult,
) -> dict[str, Any]:
    return asdict(
        result,
    )