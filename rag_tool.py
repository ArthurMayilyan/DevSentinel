from typing import Any

from rag_search_engine import RagSearchEngine, validate_rag_search_engine


DEFAULT_RAG_TOP_K = 3


def search_knowledge(
    *,
    store: RagSearchEngine,
    query: str,
    top_k: int = DEFAULT_RAG_TOP_K,
) -> list[dict[str, Any]]:
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
        {
            "source": chunk.source,
            "chunk_index": chunk.chunk_index,
            "text": chunk.text,
            "score": chunk.score,
        }
        for chunk in chunks
    ]