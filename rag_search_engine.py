from typing import Any, Protocol

from rag_store import RetrievedChunk


class RagSearchEngine(Protocol):
    def search(
        self,
        *,
        query: str,
        top_k: int = 3,
    ) -> list[RetrievedChunk]:
        ...


def validate_rag_search_engine(
    value: Any,
) -> None:
    search = getattr(value, "search", None)

    if not callable(search):
        raise ValueError("store must provide a callable search method.")