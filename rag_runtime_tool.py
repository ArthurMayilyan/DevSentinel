from typing import Any

from rag_store import InMemoryRagStore
from rag_tool import search_knowledge


def build_search_knowledge_runtime_tool(
    *,
    store: InMemoryRagStore,
):
    if not isinstance(store, InMemoryRagStore):
        raise ValueError("store must be an InMemoryRagStore.")

    def search_knowledge_runtime_tool(*, query: str) -> list[dict[str, Any]]:
        return search_knowledge(
            store=store,
            query=query,
        )

    return search_knowledge_runtime_tool

