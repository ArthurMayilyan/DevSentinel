from typing import Any

from rag_search_engine import RagSearchEngine, validate_rag_search_engine
from rag_tool import search_knowledge


def build_search_knowledge_runtime_tool(
    *,
    store: RagSearchEngine,
):
    validate_rag_search_engine(
        store,
    )

    def search_knowledge_runtime_tool(
        query: str,
    ) -> list[dict[str, Any]]:
        return search_knowledge(
            store=store,
            query=query,
        )

    return search_knowledge_runtime_tool