from dataclasses import dataclass

from agent_state import AgentState
from app_settings import get_app_settings
from rag_index import (
    build_store_from_rag_index,
    load_rag_index,
)
from rag_loader import load_rag_store_from_path
from rag_search_engine import RagSearchEngine


_SETTINGS = get_app_settings()

DEFAULT_MCP_REPORT_PATH = (
    _SETTINGS.artifacts.default_report_path
)


@dataclass
class AgentLoopMcpContext:
    state: AgentState
    rag_store: RagSearchEngine | None = None
    report_path: str = DEFAULT_MCP_REPORT_PATH


def build_agent_loop_mcp_context(
    *,
    knowledge_path: str = "",
    index_path: str = "",
    report_path: str = DEFAULT_MCP_REPORT_PATH,
) -> AgentLoopMcpContext:
    rag_store = None

    if index_path:
        rag_store = build_store_from_rag_index(
            index=load_rag_index(
                path=index_path,
            )
        )

    elif knowledge_path:
        rag_store = load_rag_store_from_path(
            path=knowledge_path,
        )

    return AgentLoopMcpContext(
        state=AgentState(),
        rag_store=rag_store,
        report_path=report_path,
    )