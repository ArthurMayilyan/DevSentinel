from typing import Any

from mcp_server_context import AgentLoopMcpContext
from review_project_workflow import (
    review_project,
    review_project_result_to_dict,
)
from reviewer_config import (
    DEFAULT_OPENAI_REVIEW_MODEL,
    DEFAULT_REVIEWER,
)
from workspace_review_presets import (
    WORKSPACE_PRESET_PYTHON_SECURITY,
    default_workspace_reviews_dir,
    get_workspace_review_preset,
)


def review_workspace(
    *,
    context: AgentLoopMcpContext,
    workspace_path: str,
    preset: str = WORKSPACE_PRESET_PYTHON_SECURITY,
    reviewer: str = DEFAULT_REVIEWER,
    model: str = DEFAULT_OPENAI_REVIEW_MODEL,
    reviews_dir: str = "",
) -> dict[str, Any]:
    selected_preset = get_workspace_review_preset(
        preset,
    )

    effective_reviews_dir = (
        reviews_dir
        or default_workspace_reviews_dir(
            workspace_path,
        )
    )

    result = review_project(
        context=context,
        project_path=workspace_path,
        profile=selected_preset.profile,
        allowed_root=workspace_path,
        include_globs=selected_preset.include_globs,
        exclude_globs=selected_preset.exclude_globs,
        max_files=selected_preset.max_files,
        max_file_size_bytes=selected_preset.max_file_size_bytes,
        reviewer=reviewer,
        model=model,
        reviews_dir=effective_reviews_dir,
    )

    payload = review_project_result_to_dict(
        result,
    )

    payload["workspace_preset"] = (
        selected_preset.name
    )

    return payload