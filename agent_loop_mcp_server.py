from mcp_server_context import AgentLoopMcpContext, build_agent_loop_mcp_context
from mcp_server_handlers import (
    mcp_add_finding,
    mcp_list_files,
    mcp_read_file,
    mcp_search_in_files,
    mcp_search_knowledge,
    mcp_write_report,
)
from rag_tool import DEFAULT_RAG_TOP_K


def import_mcp_server_class():
    try:
        from mcp.server import MCPServer
    except ImportError as exc:
        raise RuntimeError(
            "MCP SDK is not installed. Install it with: "
            'python -m pip install "mcp[cli]>=2,<3"'
        ) from exc

    return MCPServer


def create_agent_loop_mcp_server(
    *,
    context: AgentLoopMcpContext,
):
    MCPServer = import_mcp_server_class()

    mcp = MCPServer(
        "AgentLoop",
    )

    @mcp.tool()
    def list_files(
        path: str,
    ) -> list[str]:
        """List files under a local project path."""
        return mcp_list_files(
            context=context,
            path=path,
        )

    @mcp.tool()
    def read_file(
        path: str,
    ) -> str:
        """Read a local text file by path."""
        return mcp_read_file(
            context=context,
            path=path,
        )

    @mcp.tool()
    def search_in_files(
        path: str,
        query: str,
    ) -> list[dict]:
        """Search for text inside files under a local path."""
        return mcp_search_in_files(
            context=context,
            path=path,
            query=query,
        )

    @mcp.tool()
    def search_knowledge(
        query: str,
        top_k: int = DEFAULT_RAG_TOP_K,
    ) -> list[dict]:
        """Search the attached RAG knowledge base."""
        return mcp_search_knowledge(
            context=context,
            query=query,
            top_k=top_k,
        )

    @mcp.tool()
    def add_finding(
        file: str,
        severity: str,
        category: str,
        issue: str,
        evidence: str,
        recommendation: str,
    ) -> str:
        """Add a structured code review finding to agent state."""
        return mcp_add_finding(
            context=context,
            file=file,
            severity=severity,
            category=category,
            issue=issue,
            evidence=evidence,
            recommendation=recommendation,
        )

    @mcp.tool()
    def write_report() -> str:
        """Generate and write the final code review report."""
        return mcp_write_report(
            context=context,
        )

    return mcp


def create_default_agent_loop_mcp_server():
    return create_agent_loop_mcp_server(
        context=build_agent_loop_mcp_context(),
    )