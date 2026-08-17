from mcp_server_context import AgentLoopMcpContext, build_agent_loop_mcp_context
from mcp_server_handlers import (
    mcp_add_finding,
    mcp_list_files,
    mcp_read_file,
    mcp_review_project,
    mcp_search_in_files,
    mcp_search_knowledge,
    mcp_write_report,
)
from mcp_product_content import (
    build_answer_policy_question_prompt,
    build_available_workflows_resource,
    build_code_review_policy_resource,
    build_current_state_resource,
    build_project_guide_resource,
    build_review_file_prompt,
    build_review_project_prompt,
    build_write_security_report_prompt,
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

    @mcp.tool()
    def review_project(
        project_path: str,
        profile: str = "security",
        report_path: str = "",
        report_dir: str = "",
        reviews_dir: str = "",
        allowed_root: str = "",
        include_globs: str = "",
        exclude_globs: str = "",
        max_files: int = 200,
        max_file_size_bytes: int = 200_000,
        reviewer: str = "deterministic",
        model: str = "gpt-5.6-luna",
    ) -> dict:
        """Run a full project review workflow and write a report."""
        return mcp_review_project(
            context=context,
            project_path=project_path,
            profile=profile,
            report_path=report_path,
            report_dir=report_dir,
            reviews_dir=reviews_dir,
            allowed_root=allowed_root,
            include_globs=include_globs,
            exclude_globs=exclude_globs,
            max_files=max_files,
            max_file_size_bytes=max_file_size_bytes,
            reviewer=reviewer,
            model=model,
        )

    @mcp.resource(
        "agentloop://project-guide",
    )
    def project_guide() -> str:
        """AgentLoop project guide."""
        return build_project_guide_resource()

    @mcp.resource(
        "agentloop://available-workflows",
    )
    def available_workflows() -> str:
        """AgentLoop available workflows."""
        return build_available_workflows_resource()

    @mcp.resource(
        "agentloop://code-review-policy",
    )
    def code_review_policy() -> str:
        """AgentLoop code review policy."""
        return build_code_review_policy_resource()

    @mcp.resource(
        "agentloop://current-state",
    )
    def current_state() -> str:
        """Current AgentLoop MCP server state."""
        return build_current_state_resource(
            context,
        )

    @mcp.prompt(
        title="Review Project",
    )
    def review_project(
        project_path: str = "./sample_project",
    ) -> str:
        """Review a local project using AgentLoop MCP tools."""
        return build_review_project_prompt(
            project_path=project_path,
        )

    @mcp.prompt(
        title="Review File",
    )
    def review_file(
        file_path: str,
    ) -> str:
        """Review one file using AgentLoop MCP tools."""
        return build_review_file_prompt(
            file_path=file_path,
        )

    @mcp.prompt(
        title="Answer Policy Question",
    )
    def answer_policy_question(
        question: str,
    ) -> str:
        """Answer a policy question using AgentLoop knowledge search."""
        return build_answer_policy_question_prompt(
            question=question,
        )

    @mcp.prompt(
        title="Write Security Report",
    )
    def write_security_report() -> str:
        """Write the final AgentLoop security report."""
        return build_write_security_report_prompt()    

    return mcp


def create_default_agent_loop_mcp_server():
    return create_agent_loop_mcp_server(
        context=build_agent_loop_mcp_context(),
    )