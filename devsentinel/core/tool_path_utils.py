import os
import stat
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath

from devsentinel.config.app_settings import get_app_settings


_SETTINGS = get_app_settings()

DEFAULT_TOOL_MAX_FILE_SIZE_BYTES = (
    _SETTINGS.review.max_file_size_bytes
)

PATH_REJECTION_OUTSIDE_PROJECT_ROOT = "path_outside_project_root"
PATH_REJECTION_NOT_REGULAR_FILE = "path_not_regular_file"
PATH_REJECTION_FILE_TOO_LARGE = "file_too_large"
PATH_REJECTION_PROJECT_ROOT_NOT_CONFIGURED = "project_root_not_configured"

PATH_REJECTION_CODES = {
    PATH_REJECTION_OUTSIDE_PROJECT_ROOT,
    PATH_REJECTION_NOT_REGULAR_FILE,
    PATH_REJECTION_FILE_TOO_LARGE,
    PATH_REJECTION_PROJECT_ROOT_NOT_CONFIGURED,
}

MAX_REPORTED_PATH_CHARS = 300


def normalize_tool_path(
    path: str,
) -> str:
    if not isinstance(path, str) or not path.strip():
        raise ValueError("path must be a non-empty string.")

    return path.replace("\\", "/")


def shorten_requested_path(
    requested: object,
) -> str:
    text = requested if isinstance(requested, str) else repr(requested)

    if len(text) <= MAX_REPORTED_PATH_CHARS:
        return text

    return text[:MAX_REPORTED_PATH_CHARS] + "...[truncated]"


class ToolPathRejectedError(ValueError):
    """A model-requested path was refused before any file content was read."""

    def __init__(
        self,
        *,
        code: str,
        requested_path: object,
        detail: str,
    ) -> None:
        if code not in PATH_REJECTION_CODES:
            raise ValueError(f"Unknown path rejection code: {code}")

        self.code = code
        self.requested_path = shorten_requested_path(
            requested_path,
        )
        self.detail = detail

        super().__init__(
            f"{code}: {detail} Requested path: {self.requested_path!r}"
        )

    def to_trace_dict(
        self,
        *,
        tool_name: str,
    ) -> dict[str, str]:
        return {
            "code": self.code,
            "tool": tool_name,
            "requested_path": self.requested_path,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class ProjectScope:
    """Where model-facing file tools may read.

    root: resolved directory that every resolved path must stay inside.
    base_dir: resolved directory that relative tool paths are joined to.
        It is chosen explicitly by the caller (CLI, MCP server, eval runner);
        tools never consult the process working directory themselves.
    """

    root: Path
    base_dir: Path
    max_file_size_bytes: int = DEFAULT_TOOL_MAX_FILE_SIZE_BYTES

    def to_dict(self) -> dict[str, object]:
        return {
            "root": str(self.root),
            "base_dir": str(self.base_dir),
            "max_file_size_bytes": self.max_file_size_bytes,
        }


def resolve_existing_directory(
    *,
    name: str,
    value: str | Path,
) -> Path:
    if isinstance(value, str) and not value.strip():
        raise ValueError(f"{name} must be a non-empty path.")

    if not isinstance(value, (str, Path)):
        raise ValueError(f"{name} must be a string or Path.")

    resolved = Path(value).expanduser().resolve()

    if not resolved.is_dir():
        raise ValueError(f"{name} must be an existing directory: {resolved}")

    return resolved


def build_project_scope(
    *,
    root: str | Path,
    base_dir: str | Path | None = None,
    max_file_size_bytes: int = DEFAULT_TOOL_MAX_FILE_SIZE_BYTES,
) -> ProjectScope:
    if type(max_file_size_bytes) is not int or max_file_size_bytes <= 0:
        raise ValueError("max_file_size_bytes must be a positive integer.")

    resolved_root = resolve_existing_directory(
        name="project root",
        value=root,
    )

    resolved_base_dir = (
        resolved_root
        if base_dir is None
        else resolve_existing_directory(
            name="path base directory",
            value=base_dir,
        )
    )

    return ProjectScope(
        root=resolved_root,
        base_dir=resolved_base_dir,
        max_file_size_bytes=max_file_size_bytes,
    )


def reject_outside_root(
    *,
    requested: object,
    detail: str,
) -> ToolPathRejectedError:
    return ToolPathRejectedError(
        code=PATH_REJECTION_OUTSIDE_PROJECT_ROOT,
        requested_path=requested,
        detail=detail,
    )


def check_requested_path_text(
    *,
    root: Path,
    requested: object,
) -> str:
    """Lexical checks that run before the filesystem is touched.

    UNC and device paths are refused here so that resolving them can never
    trigger a network or device access.
    """
    if not isinstance(requested, str) or not requested.strip():
        raise reject_outside_root(
            requested=requested,
            detail="Path must be a non-empty string.",
        )

    if "\x00" in requested:
        raise reject_outside_root(
            requested=requested,
            detail="Path must not contain NUL characters.",
        )

    text = requested.strip()
    backslash_form = text.replace("/", "\\")

    if backslash_form.startswith("\\\\"):
        raise reject_outside_root(
            requested=requested,
            detail="UNC and device paths are not allowed.",
        )

    windows_form = PureWindowsPath(text)

    if windows_form.drive:
        if not windows_form.root:
            raise reject_outside_root(
                requested=requested,
                detail="Drive-relative paths are not allowed.",
            )

        if os.name != "nt":
            raise reject_outside_root(
                requested=requested,
                detail="Windows drive paths are not allowed on this platform.",
            )

        if windows_form.drive.casefold() != root.drive.casefold():
            raise reject_outside_root(
                requested=requested,
                detail="Paths on another drive are outside the project root.",
            )

    parts = text.replace("\\", "/").split("/")

    if ".." in parts:
        raise reject_outside_root(
            requested=requested,
            detail="Parent-directory segments ('..') are not allowed.",
        )

    return text


def resolve_within_root(
    *,
    root: Path,
    requested: str,
    base_dir: Path | None = None,
) -> Path:
    """Resolve a tool path and require the result to stay inside root.

    root and base_dir must already be resolved absolute directories (see
    build_project_scope). Relative paths are joined to base_dir, which
    defaults to root. Symlinks and Windows junctions are followed by
    resolve(), so a link that points outside root is rejected.
    """
    text = check_requested_path_text(
        root=root,
        requested=requested,
    )

    anchor = root if base_dir is None else base_dir

    if os.name != "nt":
        text = text.replace("\\", "/")

    requested_path = Path(text)

    candidate = (
        requested_path
        if requested_path.is_absolute()
        else anchor / requested_path
    )

    try:
        resolved = candidate.resolve(strict=False)
    except (OSError, RuntimeError) as error:
        raise reject_outside_root(
            requested=requested,
            detail=f"Path could not be resolved ({type(error).__name__}).",
        ) from error

    if not resolved.is_relative_to(root):
        raise reject_outside_root(
            requested=requested,
            detail="Resolved path is outside the project root.",
        )

    return resolved


def require_project_scope(
    *,
    scope: ProjectScope | None,
    requested: object,
) -> ProjectScope:
    if scope is None:
        raise ToolPathRejectedError(
            code=PATH_REJECTION_PROJECT_ROOT_NOT_CONFIGURED,
            requested_path=requested,
            detail="No project root is configured for file tools.",
        )

    return scope


def resolve_file_for_read(
    *,
    scope: ProjectScope | None,
    requested: str,
) -> Path:
    active_scope = require_project_scope(
        scope=scope,
        requested=requested,
    )

    resolved = resolve_within_root(
        root=active_scope.root,
        requested=requested,
        base_dir=active_scope.base_dir,
    )

    if not resolved.exists():
        raise FileNotFoundError(f"File does not exist: {requested}")

    if not resolved.is_file():
        raise ToolPathRejectedError(
            code=PATH_REJECTION_NOT_REGULAR_FILE,
            requested_path=requested,
            detail="Path is not a regular file.",
        )

    if resolved.stat().st_size > active_scope.max_file_size_bytes:
        raise ToolPathRejectedError(
            code=PATH_REJECTION_FILE_TOO_LARGE,
            requested_path=requested,
            detail=(
                "File is larger than the configured limit of "
                f"{active_scope.max_file_size_bytes} bytes."
            ),
        )

    return resolved


def resolve_search_location(
    *,
    scope: ProjectScope | None,
    requested: str,
) -> Path:
    active_scope = require_project_scope(
        scope=scope,
        requested=requested,
    )

    resolved = resolve_within_root(
        root=active_scope.root,
        requested=requested,
        base_dir=active_scope.base_dir,
    )

    if not resolved.exists():
        raise FileNotFoundError(f"Path does not exist: {requested}")

    return resolved


def is_redirecting_directory(
    path: Path,
) -> bool:
    """True for directory symlinks and Windows junctions.

    Python 3.11 reports junctions as is_symlink() == False, and both
    os.walk(followlinks=False) and Path.rglob() descend into them. Other
    reparse points (for example cloud-sync placeholders) resolve to
    themselves and are not treated as links.
    """
    try:
        info = os.lstat(path)
    except OSError:
        return True

    if stat.S_ISLNK(info.st_mode):
        return True

    attributes = getattr(info, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)

    if not attributes & reparse_flag:
        return False

    try:
        resolved = path.resolve(strict=False)
    except (OSError, RuntimeError):
        return True

    return os.path.normcase(str(resolved)) != os.path.normcase(str(path))


def is_regular_file_within_root(
    *,
    root: Path,
    path: Path,
) -> bool:
    try:
        resolved = path.resolve(strict=False)
    except (OSError, RuntimeError):
        return False

    return resolved.is_relative_to(root) and resolved.is_file()


def iter_files_within_root(
    *,
    root: Path,
    start: Path,
) -> Iterator[Path]:
    """Yield regular files under start whose resolved target is inside root.

    Linked directories (symlinks and junctions) are never descended into,
    even when they point inside root, so walks cannot loop or escape. File
    links are yielded only when their target is a regular file inside root.
    """
    if start.is_file():
        if is_regular_file_within_root(root=root, path=start):
            yield start
        return

    for dirpath, dirnames, filenames in os.walk(
        start,
        followlinks=False,
    ):
        current = Path(dirpath)

        dirnames[:] = sorted(
            name
            for name in dirnames
            if not is_redirecting_directory(current / name)
        )

        for name in sorted(filenames):
            file_path = current / name

            if is_regular_file_within_root(root=root, path=file_path):
                yield file_path


def display_tool_path(
    *,
    scope: ProjectScope,
    path: Path,
    absolute: bool,
) -> str:
    if absolute:
        return str(path)

    try:
        return str(path.relative_to(scope.base_dir))
    except ValueError:
        return str(path)
