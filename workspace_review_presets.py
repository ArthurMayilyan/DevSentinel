from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app_settings import get_app_settings


WORKSPACE_PRESET_PYTHON_SECURITY = (
    "python-security"
)

WORKSPACE_PRESET_TYPESCRIPT_SECURITY = (
    "typescript-security"
)

WORKSPACE_PRESET_GENERAL_SECURITY = (
    "general-security"
)


def get_supported_workspace_presets() -> set[str]:
    settings = get_app_settings()

    return set(
        settings.presets.keys(),
    )


SUPPORTED_WORKSPACE_PRESETS = (
    get_supported_workspace_presets()
)


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

    settings = get_app_settings()

    preset_settings = settings.presets.get(
        normalized,
    )

    if preset_settings is None:
        supported = ", ".join(
            sorted(
                settings.presets.keys(),
            )
        )

        raise ValueError(
            f"Unsupported workspace review preset: "
            f"{preset}. Supported presets: {supported}"
        )

    return WorkspaceReviewPreset(
        name=preset_settings.name,
        profile=preset_settings.profile,
        include_globs=",".join(
            preset_settings.include_globs,
        ),
        exclude_globs=",".join(
            preset_settings.exclude_globs,
        ),
        max_files=preset_settings.max_files,
        max_file_size_bytes=(
            preset_settings.max_file_size_bytes
        ),
    )


def default_workspace_reviews_dir(
    workspace_path: str,
) -> str:
    workspace_root = Path(
        workspace_path,
    ).expanduser().resolve()

    settings = get_app_settings()

    return str(
        workspace_root
        / settings.artifacts.reviews_dir_name
    )