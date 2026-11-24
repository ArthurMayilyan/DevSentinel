from pathlib import Path

from devsentinel.core.tool_path_utils import (
    ProjectScope,
    build_project_scope,
)


PROJECT_ROOT_HELP = (
    "Directory that model-facing file tools are confined to. "
    "Defaults to --path when given, otherwise the directory the command "
    "was launched from. The chosen root is recorded in run metadata."
)


def build_cli_project_scope(
    *,
    project_root: str | None,
    path: str | None,
    launch_dir: Path,
) -> ProjectScope:
    """Choose the file-tool root at the CLI boundary.

    Relative tool paths keep their existing meaning (relative to the launch
    directory), but every resolved path must stay inside the chosen root.
    """
    selected_root = project_root or path or str(launch_dir)

    return build_project_scope(
        root=launch_dir / selected_root,
        base_dir=launch_dir,
    )
