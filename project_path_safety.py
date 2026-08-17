from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

from app_settings import get_app_settings


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

_SETTINGS = get_app_settings()

DEFAULT_MAX_FILE_SIZE_BYTES = (
    _SETTINGS.review.max_file_size_bytes
)

DEFAULT_MAX_FILES = (
    _SETTINGS.review.max_files
)


@dataclass(frozen=True)
class SelectedProjectFiles:
    project_path: str
    files: list[str]
    skipped_files: list[str]
    include_globs: list[str]
    exclude_globs: list[str]
    max_files: int
    max_file_size_bytes: int


def parse_glob_list(
    value: str | list[str] | None,
) -> list[str]:
    if value is None:
        return []

    if isinstance(
        value,
        list,
    ):
        return [
            item.strip()
            for item in value
            if isinstance(
                item,
                str,
            )
            and item.strip()
        ]

    if not isinstance(
        value,
        str,
    ):
        raise ValueError("glob list must be a string or list of strings.")

    return [
        item.strip()
        for item in value.split(
            ",",
        )
        if item.strip()
    ]


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


def resolve_allowed_root(
    allowed_root: str,
) -> Path | None:
    if not allowed_root:
        return None

    resolved = Path(
        allowed_root,
    ).expanduser().resolve()

    if not resolved.exists():
        raise ValueError(
            f"allowed_root does not exist: {resolved}"
        )

    if not resolved.is_dir():
        raise ValueError(
            f"allowed_root must be a directory: {resolved}"
        )

    return resolved


def ensure_project_inside_allowed_root(
    *,
    project_root: Path,
    allowed_root: Path | None,
) -> None:
    if allowed_root is None:
        return

    try:
        project_root.relative_to(
            allowed_root,
        )
    except ValueError as exc:
        raise ValueError(
            f"project_path must be inside allowed_root. "
            f"project_path={project_root}, allowed_root={allowed_root}"
        ) from exc


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


def matches_any_glob(
    *,
    path: Path,
    project_root: Path,
    patterns: list[str],
) -> bool:
    if not patterns:
        return False

    relative_text = path.relative_to(
        project_root,
    ).as_posix()

    for pattern in patterns:
        normalized_pattern = pattern.replace(
            "\\",
            "/",
        )

        if fnmatch(
            relative_text,
            normalized_pattern,
        ):
            return True

        if normalized_pattern.startswith(
            "**/",
        ) and fnmatch(
            relative_text,
            normalized_pattern[3:],
        ):
            return True

    return False


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


def should_include_file(
    *,
    path: Path,
    project_root: Path,
    include_globs: list[str],
    exclude_globs: list[str],
    supported_extensions: set[str],
    max_file_size_bytes: int,
) -> bool:
    if not path.is_file():
        return False

    if exclude_globs and matches_any_glob(
        path=path,
        project_root=project_root,
        patterns=exclude_globs,
    ):
        return False

    if include_globs:
        return matches_any_glob(
            path=path,
            project_root=project_root,
            patterns=include_globs,
        ) and path.stat().st_size <= max_file_size_bytes

    return is_supported_review_file(
        path=path,
        supported_extensions=supported_extensions,
        max_file_size_bytes=max_file_size_bytes,
    )


def select_project_files(
    *,
    project_path: str,
    allowed_root: str = "",
    include_globs: str | list[str] | None = None,
    exclude_globs: str | list[str] | None = None,
    ignored_dirs: set[str] = DEFAULT_IGNORED_DIRS,
    supported_extensions: set[str] = DEFAULT_REVIEW_EXTENSIONS,
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
    max_files: int = DEFAULT_MAX_FILES,
) -> SelectedProjectFiles:
    if max_files <= 0:
        raise ValueError("max_files must be greater than zero.")

    if max_file_size_bytes <= 0:
        raise ValueError("max_file_size_bytes must be greater than zero.")

    project_root = resolve_project_path(
        project_path,
    )

    resolved_allowed_root = resolve_allowed_root(
        allowed_root,
    )

    ensure_project_inside_allowed_root(
        project_root=project_root,
        allowed_root=resolved_allowed_root,
    )

    parsed_include_globs = parse_glob_list(
        include_globs,
    )

    parsed_exclude_globs = parse_glob_list(
        exclude_globs,
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

        if should_include_file(
            path=path,
            project_root=project_root,
            include_globs=parsed_include_globs,
            exclude_globs=parsed_exclude_globs,
            supported_extensions=supported_extensions,
            max_file_size_bytes=max_file_size_bytes,
        ):
            if len(
                files,
            ) < max_files:
                files.append(
                    str(
                        path,
                    )
                )
            else:
                skipped_files.append(
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
        include_globs=parsed_include_globs,
        exclude_globs=parsed_exclude_globs,
        max_files=max_files,
        max_file_size_bytes=max_file_size_bytes,
    )