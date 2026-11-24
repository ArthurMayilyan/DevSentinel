from dataclasses import dataclass

from devsentinel.core.agent_state import AgentState
from devsentinel.core.tool_path_utils import (
    ProjectScope,
    build_project_scope,
)
from devsentinel.config.app_settings import get_app_settings
from devsentinel.rag.rag_index import (
    build_store_from_rag_index,
    load_rag_index,
)
from devsentinel.rag.rag_loader import load_rag_store_from_path
from devsentinel.rag.rag_search_engine import RagSearchEngine


_SETTINGS = get_app_settings()

DEFAULT_MCP_REPORT_PATH = (
    _SETTINGS.artifacts.default_report_path
)


@dataclass
class DevSentinelMcpContext:
    state: AgentState
    rag_store: RagSearchEngine | None = None
    report_path: str = DEFAULT_MCP_REPORT_PATH
    # Root for list_files/read_file/search_in_files. None means those
    # tools reject every path instead of using the working directory.
    project_scope: ProjectScope | None = None


def build_devsentinel_mcp_context(
    *,
    knowledge_path: str = "",
    index_path: str = "",
    report_path: str = DEFAULT_MCP_REPORT_PATH,
    project_root: str = "",
    path_base_dir: str = "",
) -> DevSentinelMcpContext:
    rag_store = None
    project_scope = None

    if project_root:
        project_scope = build_project_scope(
            root=project_root,
            base_dir=path_base_dir or None,
        )

    elif path_base_dir:
        raise ValueError(
            "path_base_dir requires project_root."
        )

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

    return DevSentinelMcpContext(
        state=AgentState(),
        rag_store=rag_store,
        report_path=report_path,
        project_scope=project_scope,
    )