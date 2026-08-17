import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from typing import Any

from agent_state import AgentState
from app_settings import get_app_settings
from mcp_server_context import AgentLoopMcpContext
from openai_review_reviewer import OpenAIReviewReviewer
from project_path_safety import (
    DEFAULT_IGNORED_DIRS,
    DEFAULT_REVIEW_EXTENSIONS,
    matches_any_glob,
    parse_glob_list,
    resolve_project_path,
)
from review_project_workflow import (
    add_finding_for_review,
    append_unique,
    collect_knowledge_context,
    count_findings_by_severity,
    detect_findings_with_reviewer,
    write_report_for_review,
)
from review_profiles import get_review_profile
from review_run_artifacts import (
    create_review_run_package,
    review_run_artifacts_to_dict,
)
from reviewer_config import (
    DEFAULT_OPENAI_REVIEW_MODEL,
    DEFAULT_REVIEWER,
    REVIEWER_OPENAI,
    validate_reviewer,
)
from workspace_review_presets import (
    WORKSPACE_PRESET_PYTHON_SECURITY,
    default_workspace_reviews_dir,
    get_workspace_review_preset,
)


@dataclass(frozen=True)
class GitChangedFile:
    status: str
    path: str
    old_path: str = ""


@dataclass(frozen=True)
class GitDiffReviewResult:
    status: str
    repository_path: str
    mode: str
    base_ref: str
    target_ref: str
    preset: str
    profile: str
    reviewer: str
    model: str

    changed_files_count: int
    selected_files_count: int
    skipped_files_count: int
    inspected_files_count: int

    findings_count: int
    severity_counts: dict[str, int]

    changed_files: list[dict[str, str]]
    selected_files: list[str]
    skipped_files: list[dict[str, str]]
    findings: list[dict[str, Any]]

    summary: str
    scope: dict[str, Any]

    report_path: str
    run_id: str
    run_dir: str
    artifacts: dict[str, Any]


def git_diff_review_result_to_dict(
    result: GitDiffReviewResult,
) -> dict[str, Any]:
    return asdict(
        result,
    )


def run_git_command(
    *,
    repository_path: str | Path,
    args: list[str],
    command_timeout_seconds: float | None = None,
) -> str:
    repository_root = Path(
        repository_path,
    ).expanduser().resolve()

    settings = get_app_settings()

    effective_timeout = (
        command_timeout_seconds
        if command_timeout_seconds is not None
        else settings.runtime.command_timeout_seconds
    )

    if effective_timeout <= 0:
        raise ValueError(
            "command_timeout_seconds must be greater than zero."
        )

    command = [
        "git",
        "-c",
        "core.quotepath=false",
        "-C",
        str(
            repository_root,
        ),
        *args,
    ]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=effective_timeout,
        )

    except FileNotFoundError as exc:
        raise RuntimeError(
            "Git executable was not found. "
            "Ensure git is installed and available on PATH."
        ) from exc

    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            "Git command timed out after "
            f"{effective_timeout} seconds: "
            f"{' '.join(args)}"
        ) from exc

    if completed.returncode != 0:
        error_text = (
            completed.stderr.strip()
            or completed.stdout.strip()
            or "unknown git error"
        )

        raise ValueError(
            f"Git command failed: {' '.join(args)}. "
            f"Error: {error_text}"
        )

    return completed.stdout


def validate_git_repository(
    *,
    repository_path: str,
    command_timeout_seconds: float | None = None,
) -> Path:
    repository_root = resolve_project_path(
        repository_path,
    )

    result = run_git_command(
        repository_path=repository_root,
        args=[
            "rev-parse",
            "--is-inside-work-tree",
        ],
        command_timeout_seconds=command_timeout_seconds,
    ).strip()

    if result.lower() != "true":
        raise ValueError(
            f"Path is not a Git working tree: {repository_root}"
        )

    return repository_root


def validate_git_ref(
    *,
    repository_root: Path,
    ref: str,
    name: str,
    command_timeout_seconds: float | None = None,
) -> str:
    if not isinstance(
        ref,
        str,
    ) or not ref.strip():
        raise ValueError(
            f"{name} must be a non-empty Git reference."
        )

    normalized = ref.strip()

    if (
        normalized.startswith("-")
        or "\x00" in normalized
        or "\n" in normalized
        or "\r" in normalized
    ):
        raise ValueError(
            f"Invalid {name}: {ref}"
        )

    run_git_command(
        repository_path=repository_root,
        args=[
            "rev-parse",
            "--verify",
            f"{normalized}^{{commit}}",
        ],
        command_timeout_seconds=command_timeout_seconds,
    )

    return normalized


def parse_git_name_status_z(
    output: str,
) -> list[GitChangedFile]:
    if not output:
        return []

    tokens = output.split(
        "\x00",
    )

    if tokens and tokens[-1] == "":
        tokens.pop()

    changed_files = []
    index = 0

    while index < len(tokens):
        status = tokens[index]
        index += 1

        if not status:
            raise ValueError(
                "Git diff contained an empty file status."
            )

        status_code = status[0].upper()

        if status_code in {
            "R",
            "C",
        }:
            if index + 1 >= len(tokens):
                raise ValueError(
                    "Git diff contained an incomplete rename/copy entry."
                )

            old_path = tokens[index]
            new_path = tokens[index + 1]
            index += 2

            changed_files.append(
                GitChangedFile(
                    status=status,
                    path=new_path,
                    old_path=old_path,
                )
            )

            continue

        if index >= len(tokens):
            raise ValueError(
                "Git diff contained an incomplete file entry."
            )

        path = tokens[index]
        index += 1

        changed_files.append(
            GitChangedFile(
                status=status,
                path=path,
            )
        )

    return changed_files


def get_git_changed_files(
    *,
    repository_path: str,
    base_ref: str = "main",
    target_ref: str = "HEAD",
    staged_only: bool = False,
    command_timeout_seconds: float | None = None,
) -> list[GitChangedFile]:
    repository_root = validate_git_repository(
        repository_path=repository_path,
        command_timeout_seconds=command_timeout_seconds,
    )

    if staged_only:
        args = [
            "diff",
            "--cached",
            "--name-status",
            "-z",
            "--find-renames",
            "--",
        ]

    else:
        validated_base_ref = validate_git_ref(
            repository_root=repository_root,
            ref=base_ref,
            name="base_ref",
            command_timeout_seconds=command_timeout_seconds,
        )

        validated_target_ref = validate_git_ref(
            repository_root=repository_root,
            ref=target_ref,
            name="target_ref",
            command_timeout_seconds=command_timeout_seconds,
        )

        # Triple-dot is intentional:
        # compare target changes since the merge base,
        # which is closer to normal PR semantics.
        args = [
            "diff",
            "--name-status",
            "-z",
            "--find-renames",
            f"{validated_base_ref}...{validated_target_ref}",
            "--",
        ]

    output = run_git_command(
        repository_path=repository_root,
        args=args,
        command_timeout_seconds=command_timeout_seconds,
    )

    return parse_git_name_status_z(
        output,
    )


def build_absolute_git_path(
    *,
    repository_root: Path,
    relative_path: str,
) -> Path | None:
    pure_path = PurePosixPath(
        relative_path,
    )

    if (
        pure_path.is_absolute()
        or ".." in pure_path.parts
    ):
        return None

    candidate = repository_root.joinpath(
        *pure_path.parts,
    ).resolve(
        strict=False,
    )

    try:
        candidate.relative_to(
            repository_root,
        )

    except ValueError:
        return None

    return candidate


def is_ignored_git_path(
    relative_path: str,
) -> bool:
    parts = PurePosixPath(
        relative_path,
    ).parts

    return any(
        part in DEFAULT_IGNORED_DIRS
        for part in parts
    )


def read_git_snapshot_file(
    *,
    repository_root: Path,
    relative_path: str,
    target_ref: str,
    staged_only: bool,
    command_timeout_seconds: float | None = None,
) -> str:
    if staged_only:
        # Read exactly the version from the Git index.
        object_spec = (
            f":{relative_path}"
        )

    else:
        # Read exactly the target revision, not the current
        # working-tree version.
        object_spec = (
            f"{target_ref}:{relative_path}"
        )

    return run_git_command(
        repository_path=repository_root,
        args=[
            "show",
            object_spec,
        ],
        command_timeout_seconds=command_timeout_seconds,
    )


def select_changed_files_for_review(
    *,
    repository_root: Path,
    changed_files: list[GitChangedFile],
    preset: str,
    target_ref: str,
    staged_only: bool,
    command_timeout_seconds: float | None = None,
):
    selected_preset = get_workspace_review_preset(
        preset,
    )

    include_globs = parse_glob_list(
        selected_preset.include_globs,
    )

    exclude_globs = parse_glob_list(
        selected_preset.exclude_globs,
    )

    selected_files: list[dict[str, Any]] = []
    skipped_files: list[dict[str, str]] = []

    for changed_file in changed_files:
        status_code = changed_file.status[
            0
        ].upper()

        if status_code == "D":
            skipped_files.append(
                {
                    "path": changed_file.path,
                    "status": changed_file.status,
                    "reason": "deleted",
                }
            )
            continue

        if status_code not in {
            "A",
            "M",
            "R",
            "C",
        }:
            skipped_files.append(
                {
                    "path": changed_file.path,
                    "status": changed_file.status,
                    "reason": "unsupported_status",
                }
            )
            continue

        absolute_path = build_absolute_git_path(
            repository_root=repository_root,
            relative_path=changed_file.path,
        )

        if absolute_path is None:
            skipped_files.append(
                {
                    "path": changed_file.path,
                    "status": changed_file.status,
                    "reason": "unsafe_path",
                }
            )
            continue

        if is_ignored_git_path(
            changed_file.path,
        ):
            skipped_files.append(
                {
                    "path": changed_file.path,
                    "status": changed_file.status,
                    "reason": "ignored_path",
                }
            )
            continue

        if (
            exclude_globs
            and matches_any_glob(
                path=absolute_path,
                project_root=repository_root,
                patterns=exclude_globs,
            )
        ):
            skipped_files.append(
                {
                    "path": changed_file.path,
                    "status": changed_file.status,
                    "reason": "excluded_by_preset",
                }
            )
            continue

        if include_globs:
            if not matches_any_glob(
                path=absolute_path,
                project_root=repository_root,
                patterns=include_globs,
            ):
                skipped_files.append(
                    {
                        "path": changed_file.path,
                        "status": changed_file.status,
                        "reason": "not_included_by_preset",
                    }
                )
                continue

        elif (
            absolute_path.suffix.lower()
            not in DEFAULT_REVIEW_EXTENSIONS
        ):
            skipped_files.append(
                {
                    "path": changed_file.path,
                    "status": changed_file.status,
                    "reason": "unsupported_extension",
                }
            )
            continue

        if (
            len(selected_files)
            >= selected_preset.max_files
        ):
            skipped_files.append(
                {
                    "path": changed_file.path,
                    "status": changed_file.status,
                    "reason": "max_files_reached",
                }
            )
            continue

        content = read_git_snapshot_file(
            repository_root=repository_root,
            relative_path=changed_file.path,
            target_ref=target_ref,
            staged_only=staged_only,
            command_timeout_seconds=command_timeout_seconds,
        )

        content_size_bytes = len(
            content.encode(
                "utf-8",
            )
        )

        if (
            content_size_bytes
            > selected_preset.max_file_size_bytes
        ):
            skipped_files.append(
                {
                    "path": changed_file.path,
                    "status": changed_file.status,
                    "reason": "file_too_large",
                }
            )
            continue

        selected_files.append(
            {
                "changed_file": changed_file,
                "absolute_path": str(
                    absolute_path,
                ),
                "content": content,
            }
        )

    return (
        selected_preset,
        selected_files,
        skipped_files,
    )


def build_git_diff_review_summary(
    *,
    profile: str,
    comparison: str,
    changed_files_count: int,
    selected_files_count: int,
    skipped_files_count: int,
    findings_count: int,
    severity_counts: dict[str, int],
) -> str:
    base = (
        f"Git diff {profile} review completed for {comparison}. "
        f"Changed {changed_files_count} file(s), "
        f"reviewed {selected_files_count} file(s), "
        f"skipped {skipped_files_count} file(s)."
    )

    if not findings_count:
        return (
            f"{base} No findings were detected."
        )

    severity_parts = [
        f"{severity}: {count}"
        for severity, count in sorted(
            severity_counts.items(),
        )
    ]

    return (
        f"{base} "
        f"Found {findings_count} issue(s) "
        f"({', '.join(severity_parts)})."
    )


def review_git_diff(
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
    command_timeout_seconds: float | None = None,
    openai_client_class: Any = None,
) -> GitDiffReviewResult:
    repository_root = validate_git_repository(
        repository_path=repository_path,
        command_timeout_seconds=command_timeout_seconds,
    )

    settings = get_app_settings()

    effective_command_timeout = (
        command_timeout_seconds
        if command_timeout_seconds is not None
        else settings.runtime.command_timeout_seconds
    )

    changed_files = get_git_changed_files(
        repository_path=str(
            repository_root,
        ),
        base_ref=base_ref,
        target_ref=target_ref,
        staged_only=staged_only,
        command_timeout_seconds=effective_command_timeout,
    )

    (
        selected_preset,
        selected_files,
        skipped_files,
    ) = select_changed_files_for_review(
        repository_root=repository_root,
        changed_files=changed_files,
        preset=preset,
        target_ref=target_ref,
        staged_only=staged_only,
        command_timeout_seconds=effective_command_timeout,
    )

    review_profile = get_review_profile(
        selected_preset.profile,
    )

    selected_reviewer = validate_reviewer(
        reviewer,
    )

    effective_reviews_dir = (
        reviews_dir
        or default_workspace_reviews_dir(
            str(
                repository_root,
            )
        )
    )

    mode = (
        "staged"
        if staged_only
        else "refs"
    )

    comparison = (
        "staged changes"
        if staged_only
        else f"{base_ref}...{target_ref}"
    )

    with TemporaryDirectory(
        prefix="agentloop_git_review_",
    ) as temporary_directory:
        temporary_report_path = str(
            Path(
                temporary_directory,
            )
            / "report.md"
        )

        # High-level Git review is isolated from any state
        # already stored in the shared MCP context.
        run_context = AgentLoopMcpContext(
            state=AgentState(),
            rag_store=context.rag_store,
            report_path=temporary_report_path,
        )

        policy_context = collect_knowledge_context(
            context=run_context,
            knowledge_queries=review_profile.knowledge_queries,
        )

        openai_reviewer = None

        if (
            selected_reviewer
            == REVIEWER_OPENAI
        ):
            openai_reviewer = (
                OpenAIReviewReviewer(
                    model=model,
                    client_class=openai_client_class,
                )
            )

        for selected_file in selected_files:
            absolute_path = str(
                selected_file[
                    "absolute_path"
                ]
            )

            content = str(
                selected_file[
                    "content"
                ]
            )

            append_unique(
                run_context.state.inspected_files,
                absolute_path,
            )

            findings = (
                detect_findings_with_reviewer(
                    reviewer=selected_reviewer,
                    file_path=absolute_path,
                    content=content,
                    profile=review_profile.name,
                    policy_context=policy_context,
                    openai_reviewer=openai_reviewer,
                )
            )

            for finding in findings:
                add_finding_for_review(
                    context=run_context,
                    finding=finding,
                )

        source_report_path = (
            write_report_for_review(
                context=run_context,
            )
        )

        severity_counts = (
            count_findings_by_severity(
                run_context.state.findings,
            )
        )

        summary = (
            build_git_diff_review_summary(
                profile=review_profile.name,
                comparison=comparison,
                changed_files_count=len(
                    changed_files,
                ),
                selected_files_count=len(
                    selected_files,
                ),
                skipped_files_count=len(
                    skipped_files,
                ),
                findings_count=len(
                    run_context.state.findings,
                ),
                severity_counts=severity_counts,
            )
        )

        scope = {
            "workflow": "git_diff",
            "mode": mode,
            "base_ref": (
                ""
                if staged_only
                else base_ref
            ),
            "target_ref": (
                ""
                if staged_only
                else target_ref
            ),
            "preset": selected_preset.name,
            "include_globs": parse_glob_list(
                selected_preset.include_globs,
            ),
            "exclude_globs": parse_glob_list(
                selected_preset.exclude_globs,
            ),
            "max_files": (
                selected_preset.max_files
            ),
            "max_file_size_bytes": (
                selected_preset.max_file_size_bytes
            ),
            "command_timeout_seconds": (
                effective_command_timeout
            ),
            "changed_files_count": len(
                changed_files,
            ),
        }

        selected_file_paths = [
            str(
                item[
                    "absolute_path"
                ]
            )
            for item in selected_files
        ]

        skipped_file_paths = [
            item[
                "path"
            ]
            for item in skipped_files
        ]

        review_artifacts = (
            create_review_run_package(
                reviews_dir=effective_reviews_dir,
                project_path=str(
                    repository_root,
                ),
                profile=review_profile.name,
                reviewer=selected_reviewer,
                model=(
                    model
                    if selected_reviewer
                    == REVIEWER_OPENAI
                    else ""
                ),
                status="completed",
                summary=summary,
                findings=list(
                    run_context.state.findings,
                ),
                selected_files=selected_file_paths,
                skipped_files=skipped_file_paths,
                scope=scope,
                source_report_path=source_report_path,
                run_config={
                    "workflow": "git_diff",
                    "repository_path": str(
                        repository_root,
                    ),
                    "mode": mode,
                    "base_ref": (
                        ""
                        if staged_only
                        else base_ref
                    ),
                    "target_ref": (
                        ""
                        if staged_only
                        else target_ref
                    ),
                    "preset": (
                        selected_preset.name
                    ),
                    "profile": (
                        review_profile.name
                    ),
                    "reviewer": (
                        selected_reviewer
                    ),
                    "model": (
                        model
                        if selected_reviewer
                        == REVIEWER_OPENAI
                        else ""
                    ),
                    "reviews_dir": (
                        effective_reviews_dir
                    ),
                    "command_timeout_seconds": (
                        effective_command_timeout
                    ),
                    "max_files": (
                        selected_preset.max_files
                    ),
                    "max_file_size_bytes": (
                        selected_preset.max_file_size_bytes
                    ),
                },
            )
        )

        artifacts = (
            review_run_artifacts_to_dict(
                review_artifacts,
            )
        )

        findings = list(
            run_context.state.findings,
        )

    return GitDiffReviewResult(
        status="completed",
        repository_path=str(
            repository_root,
        ),
        mode=mode,
        base_ref=(
            ""
            if staged_only
            else base_ref
        ),
        target_ref=(
            ""
            if staged_only
            else target_ref
        ),
        preset=selected_preset.name,
        profile=review_profile.name,
        reviewer=selected_reviewer,
        model=(
            model
            if selected_reviewer
            == REVIEWER_OPENAI
            else ""
        ),
        changed_files_count=len(
            changed_files,
        ),
        selected_files_count=len(
            selected_files,
        ),
        skipped_files_count=len(
            skipped_files,
        ),
        inspected_files_count=len(
            selected_files,
        ),
        findings_count=len(
            findings,
        ),
        severity_counts=severity_counts,
        changed_files=[
            asdict(
                item,
            )
            for item in changed_files
        ],
        selected_files=selected_file_paths,
        skipped_files=skipped_files,
        findings=findings,
        summary=summary,
        scope=scope,
        report_path=artifacts[
            "report_markdown_path"
        ],
        run_id=review_artifacts.run_id,
        run_dir=review_artifacts.run_dir,
        artifacts=artifacts,
    )