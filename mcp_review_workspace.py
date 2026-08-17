from typing import Any

from mcp_server_context import AgentLoopMcpContext
from reviewer_config import (
    DEFAULT_OPENAI_REVIEW_MODEL,
    DEFAULT_REVIEWER,
)
from workspace_review import review_workspace
from workspace_review_presets import (
    WORKSPACE_PRESET_PYTHON_SECURITY,
)


def mcp_review_workspace(
    *,
    context: AgentLoopMcpContext,
    workspace_path: str,
    preset: str = WORKSPACE_PRESET_PYTHON_SECURITY,
    reviewer: str = DEFAULT_REVIEWER,
    model: str = DEFAULT_OPENAI_REVIEW_MODEL,
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