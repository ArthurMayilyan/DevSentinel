from dataclasses import dataclass

from rag_store import InMemoryRagStore, RetrievedChunk, tokenize


def validate_search_query(
    query: str,
) -> None:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string.")


def validate_top_k(
    top_k: int,
) -> None:
    if type(top_k) is not int:
        raise ValueError("top_k must be an integer.")

    if top_k <= 0:
        raise ValueError("top_k must be greater than 0.")


def score_binary_token_overlap(
    *,
    query: str,
    text: str,
) -> int:
    validate_search_query(query)

    if not isinstance(text, str):
        raise ValueError("text must be a string.")

    query_tokens = set(tokenize(query))
    text_tokens = set(tokenize(text))

    return len(query_tokens & text_tokens)


@dataclass(frozen=True)
class BinaryOverlapRagRetriever:
    store: InMemoryRagStore

    def __post_init__(self) -> None:
        if not isinstance(self.store, InMemoryRagStore):
            raise ValueError("store must be an InMemoryRagStore.")

    def search(
        self,
        *,
        query: str,
        top_k: int = 3,
    ) -> list[RetrievedChunk]:
        validate_search_query(query)
        validate_top_k(top_k)

        scored_chunks = []

        for chunk in self.store.chunks:
            score = score_binary_token_overlap(
                query=query,
                text=chunk.text,
            )

            if score <= 0:
                continue

            scored_chunks.append(
                RetrievedChunk(
                    source=chunk.source,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    score=score,
                )
            )

        return sorted(
            scored_chunks,
            key=lambda chunk: (
                -chunk.score,
                chunk.source,
                chunk.chunk_index,
            ),
        )[:top_k]

    