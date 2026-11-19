from typing import Any

from devsentinel.mcp.mcp_server_context import DevSentinelMcpContext
from devsentinel.config.reviewer_config import (
    DEFAULT_OPENAI_REVIEW_MODEL,
    DEFAULT_REVIEWER,
)
from devsentinel.review.workspace_review import review_workspace
from devsentinel.review.workspace_review_presets import (
    WORKSPACE_PRESET_PYTHON_SECURITY,
)


def mcp_review_workspace(
    *,
    context: DevSentinelMcpContext,
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