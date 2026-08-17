from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


WORKSPACE_PRESET_PYTHON_SECURITY = "python-security"
WORKSPACE_PRESET_TYPESCRIPT_SECURITY = "typescript-security"
WORKSPACE_PRESET_GENERAL_SECURITY = "general-security"


SUPPORTED_WORKSPACE_PRESETS = {
    WORKSPACE_PRESET_PYTHON_SECURITY,
    WORKSPACE_PRESET_TYPESCRIPT_SECURITY,
    WORKSPACE_PRESET_GENERAL_SECURITY,
}


@dataclass(frozen=True)
class WorkspaceReviewPreset:
    name: str
    profile: str
    include_globs: str
    exclude_globs: str
    max_files: int
    max_file_size_bytes: int


def workspace_review_preset_to_dict(
    preset: WorkspaceReviewPreset,
) -> dict[str, Any]:
    return asdict(
        preset,
    )


def get_workspace_review_preset(
    preset: str,
) -> WorkspaceReviewPreset:
    normalized = (
        preset.strip().lower()
        if isinstance(
            preset,
            str,
        )
        else ""
    )

    if normalized == WORKSPACE_PRESET_PYTHON_SECURITY:
        return WorkspaceReviewPreset(
            name=WORKSPACE_PRESET_PYTHON_SECURITY,
            profile="security",
            include_globs="**/*.py",
            exclude_globs=(
                ".venv/**,"
                "__pycache__/**,"
                ".pytest_cache/**,"
                "tests/**,"
                "dist/**,"
                "build/**"
            ),
            max_files=200,
            max_file_size_bytes=200_000,
        )

    if normalized == WORKSPACE_PRESET_TYPESCRIPT_SECURITY:
        return WorkspaceReviewPreset(
            name=WORKSPACE_PRESET_TYPESCRIPT_SECURITY,
            profile="security",
            include_globs=(
                "**/*.ts,"
                "**/*.tsx,"
                "**/*.js,"
                "**/*.jsx"
            ),
            exclude_globs=(
                "node_modules/**,"
                "dist/**,"
                "build/**,"
                "coverage/**,"
                "tests/**"
            ),
            max_files=200,
            max_file_size_bytes=200_000,
        )

    if normalized == WORKSPACE_PRESET_GENERAL_SECURITY:
        return WorkspaceReviewPreset(
            name=WORKSPACE_PRESET_GENERAL_SECURITY,
            profile="security",
            include_globs="",
            exclude_globs=(
                ".git/**,"
                ".venv/**,"
                "node_modules/**,"
                "__pycache__/**,"
                ".pytest_cache/**,"
                "dist/**,"
                "build/**,"
                "coverage/**"
            ),
            max_files=200,
            max_file_size_bytes=200_000,
        )

    supported = ", ".join(
        sorted(
            SUPPORTED_WORKSPACE_PRESETS,
        )
    )

    raise ValueError(
        f"Unsupported workspace review preset: {preset}. "
        f"Supported presets: {supported}"
    )


def default_workspace_reviews_dir(
    workspace_path: str,
) -> str:
    workspace_root = Path(
        workspace_path,
    ).expanduser().resolve()

    return str(
        workspace_root / "reviews"
    )