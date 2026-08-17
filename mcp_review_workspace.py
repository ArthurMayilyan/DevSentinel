from typing import Any

from mcp_server_context import AgentLoopMcpContext
from workspace_review import review_workspace


def mcp_review_workspace(
    *,
    context: AgentLoopMcpContext,
    workspace_path: str,
    preset: str = "python-security",
    reviewer: str = "deterministic",
    model: str = "gpt-5.6-luna",
    reviews_dir: str = "",
) -> dict[str, Any]:
    return review_workspace(
        context=context,
        workspace_path=workspace_path,
        preset=preset,
        reviewer=reviewer,
        model=model,
        reviews_dir=reviews_dir,
    )