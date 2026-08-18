from typing import Any

from git_diff_review import (
    git_diff_review_result_to_dict,
    review_git_diff,
)
from mcp_server_context import AgentLoopMcpContext
from reviewer_config import (
    DEFAULT_OPENAI_REVIEW_MODEL,
    DEFAULT_REVIEWER,
)
from workspace_review_presets import (
    WORKSPACE_PRESET_PYTHON_SECURITY,
)


def mcp_review_git_diff(
    *,
    context: AgentLoopMcpContext,
    repository_path: str,
    base_ref: str = "main",
    target_ref: str = "HEAD",
    staged_only: bool = False,
    preset: str = WORKSPACE_PRESET_PYTHON_SECURITY,
    reviewer: str = DEFAULT_REVIEWER,
    model: str = DEFAULT_OPENAI_REVIEW_MODEL,
    reviews_dir: str = "",
) -> dict[str, Any]:
    result = review_git_diff(
        context=context,
        repository_path=repository_path,
        base_ref=base_ref,
        target_ref=target_ref,
        staged_only=staged_only,
        preset=preset,
        reviewer=reviewer,
        model=model,
        reviews_dir=reviews_dir,
    )

    return git_diff_review_result_to_dict(
        result,
    )