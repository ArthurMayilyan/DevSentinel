from dataclasses import dataclass
from pathlib import Path


DEFAULT_IGNORED_DIRS = {
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "coverage",
}

DEFAULT_REVIEW_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".cs",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".go",
    ".rb",
    ".php",
    ".json",
    ".yml",
    ".yaml",
    ".md",
    ".txt",
}

DEFAULT_MAX_FILE_SIZE_BYTES = 200_000


@dataclass(frozen=True)
class SelectedProjectFiles:
    project_path: str
    files: list[str]
    skipped_files: list[str]


def resolve_project_path(
    project_path: str,
) -> Path:
    if not isinstance(project_path, str) or not project_path.strip():
        raise ValueError("project_path must be a non-empty string.")

    resolved = Path(
        project_path,
    ).expanduser().resolve()

    if not resolved.exists():
        raise ValueError(
            f"project_path does not exist: {resolved}"
        )

    if not resolved.is_dir():
        raise ValueError(
            f"project_path must be a directory: {resolved}"
        )

    return resolved


def is_ignored_path(
    *,
    path: Path,
    project_root: Path,
    ignored_dirs: set[str] = DEFAULT_IGNORED_DIRS,
) -> bool:
    relative_parts = path.relative_to(
        project_root,
    ).parts

    return any(
        part in ignored_dirs
        for part in relative_parts
    )


def is_supported_review_file(
    *,
    path: Path,
    supported_extensions: set[str] = DEFAULT_REVIEW_EXTENSIONS,
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
) -> bool:
    if not path.is_file():
        return False

    if path.suffix.lower() not in supported_extensions:
        return False

    if path.stat().st_size > max_file_size_bytes:
        return False

    return True


def select_project_files(
    *,
    project_path: str,
    ignored_dirs: set[str] = DEFAULT_IGNORED_DIRS,
    supported_extensions: set[str] = DEFAULT_REVIEW_EXTENSIONS,
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
) -> SelectedProjectFiles:
    project_root = resolve_project_path(
        project_path,
    )

    files = []
    skipped_files = []

    for path in sorted(
        project_root.rglob("*"),
    ):
        if is_ignored_path(
            path=path,
            project_root=project_root,
            ignored_dirs=ignored_dirs,
        ):
            skipped_files.append(
                str(
                    path,
                )
            )
            continue

        if is_supported_review_file(
            path=path,
            supported_extensions=supported_extensions,
            max_file_size_bytes=max_file_size_bytes,
        ):
            files.append(
                str(
                    path,
                )
            )
        elif path.is_file():
            skipped_files.append(
                str(
                    path,
                )
            )

    return SelectedProjectFiles(
        project_path=str(
            project_root,
        ),
        files=files,
        skipped_files=skipped_files,
    )