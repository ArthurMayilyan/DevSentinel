from typing import Any

from rag_store import InMemoryRagStore


DEFAULT_RAG_TOP_K = 3


def search_knowledge(
    *,
    store: InMemoryRagStore,
    query: str,
    top_k: int = DEFAULT_RAG_TOP_K,
) -> list[dict[str, Any]]:
    if not isinstance(store, InMemoryRagStore):
        raise ValueError("store must be an InMemoryRagStore.")

    results = store.search(
        query=query,
        top_k=top_k,
    )

    return [chunk.to_dict() for chunk in results]