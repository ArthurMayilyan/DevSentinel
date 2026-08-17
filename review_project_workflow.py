from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from datetime import datetime

from mcp_server_context import AgentLoopMcpContext
from project_path_safety import (
    DEFAULT_MAX_FILES,
    DEFAULT_MAX_FILE_SIZE_BYTES,
    select_project_files,
)
from rag_tool import search_knowledge as search_rag_knowledge
from review_profiles import (
    REVIEW_PROFILE_FULL,
    REVIEW_PROFILE_SECURITY,
    get_review_profile,
)
from review_run_artifacts import (
    create_review_run_package,
    review_run_artifacts_to_dict,
)

from openai_review_reviewer import OpenAIReviewReviewer
from reviewer_config import (
    DEFAULT_OPENAI_REVIEW_MODEL,
    DEFAULT_REVIEWER,
    REVIEWER_DETERMINISTIC,
    REVIEWER_OPENAI,
    validate_reviewer,
)
from finding_types import (
    FINDING_TYPE_SECURITY_DEBUG_MODE,
    FINDING_TYPE_SECURITY_HARDCODED_ADMIN_CREDENTIALS,
    FINDING_TYPE_SECURITY_HARDCODED_SECRET,
    FINDING_TYPE_SECURITY_INFORMATION_DISCLOSURE,
    FINDING_TYPE_SECURITY_TOKEN_EXPIRATION,
    FINDING_TYPE_SECURITY_TOKEN_VALIDATION,
    normalize_finding_type,
)

from tools import read_file as read_project_file
from tools import render_report_from_state
from tool_specs import IssueCategory, IssueSeverity


@dataclass(frozen=True)
class ReviewProjectResult:
    status: str
    profile: str
    reviewer: str
    model: str
    project_path: str
    inspected_files_count: int
    selected_files_count: int
    skipped_files_count: int
    findings_count: int
    severity_counts: dict[str, int]
    report_path: str
    summary: str
    scope: dict[str, Any]
    findings: list[dict[str, Any]]
    run_id: str
    run_dir: str
    artifacts: dict[str, Any]


def review_project_result_to_dict(
    result: ReviewProjectResult,
) -> dict[str, Any]:
    return asdict(
        result,
    )


def build_generated_report_path(
    *,
    project_path: str,
    report_dir: str,
    profile: str,
) -> str:
    project_name = Path(
        project_path,
    ).name or "project"

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S",
    )

    directory = Path(
        report_dir,
    ).expanduser().resolve()

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return str(
        directory / f"{project_name}_{profile}_review_{timestamp}.md"
    )


def append_unique(
    values: list[str],
    item: str,
) -> None:
    if item not in values:
        values.append(
            item,
        )


def normalize_enum_value(
    *,
    value: str,
    enum_cls,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("enum value must be a non-empty string.")

    try:
        return enum_cls(value).value
    except ValueError:
        upper_value = value.upper()

        try:
            return enum_cls(upper_value).value
        except ValueError:
            allowed = [
                item.value
                for item in enum_cls
            ]

            raise ValueError(
                f"Invalid value: {value}. Allowed values: {allowed}"
            )


def read_file_for_review(
    *,
    context: AgentLoopMcpContext,
    path: str,
) -> str:
    content = read_project_file(
        path,
    )

    append_unique(
        context.state.inspected_files,
        path,
    )

    return content


def write_report_for_review(
    *,
    context: AgentLoopMcpContext,
) -> str:
    report_path = Path(
        context.report_path,
    )

    markdown = render_report_from_state(
        context.state,
    )

    report_path.write_text(
        markdown,
        encoding="utf-8",
    )

    context.state.report_written = True
    context.state.report_path = str(
        report_path,
    )

    return str(
        report_path,
    )


def search_knowledge_for_review(
    *,
    context: AgentLoopMcpContext,
    query: str,
) -> list[dict[str, Any]]:
    if context.rag_store is None:
        return []

    return search_rag_knowledge(
        store=context.rag_store,
        query=query,
    )


def add_finding_for_review(
    *,
    context: AgentLoopMcpContext,
    finding: dict[str, Any],
) -> None:
    issue = str(
        finding["issue"],
    )

    evidence = str(
        finding["evidence"],
    )

    normalized_finding = {
        "finding_type": normalize_finding_type(
            str(
                finding.get(
                    "finding_type",
                    "",
                )
            ),
            issue=issue,
            evidence=evidence,
        ),
        "file": finding["file"],
        "severity": normalize_enum_value(
            value=finding["severity"],
            enum_cls=IssueSeverity,
        ),
        "category": normalize_enum_value(
            value=finding["category"],
            enum_cls=IssueCategory,
        ),
        "issue": issue,
        "evidence": evidence,
        "recommendation": finding["recommendation"],
    }

    existing_keys = {
        finding_key(
            existing,
        )
        for existing in context.state.findings
    }

    if finding_key(
        normalized_finding,
    ) in existing_keys:
        return

    context.state.findings.append(
        normalized_finding,
    )


def finding_key(
    finding: dict[str, Any],
) -> tuple[str, str]:
    file_name = Path(
        str(
            finding.get(
                "file",
                "",
            )
        )
    ).name.lower()

    finding_type = normalize_finding_type(
        str(
            finding.get(
                "finding_type",
                "",
            )
        ),
        issue=str(
            finding.get(
                "issue",
                "",
            )
        ),
        evidence=str(
            finding.get(
                "evidence",
                "",
            )
        ),
    )

    return (
        file_name,
        finding_type,
    )


def count_findings_by_severity(
    findings: list[dict[str, Any]],
) -> dict[str, int]:
    counts: dict[str, int] = {}

    for finding in findings:
        severity = str(
            finding.get(
                "severity",
                "UNKNOWN",
            )
        )

        counts[severity] = counts.get(
            severity,
            0,
        ) + 1

    return counts


def build_review_summary(
    *,
    result: ReviewProjectResult,
) -> str:
    scope_part = (
        f"Selected {result.selected_files_count} file(s), "
        f"skipped {result.skipped_files_count} file(s)."
    )

    if not result.findings_count:
        return (
            f"{result.profile} review completed. "
            f"Inspected {result.inspected_files_count} file(s). "
            f"{scope_part} "
            "No findings were detected. "
            f"Report: {result.report_path}"
        )

    severity_parts = [
        f"{severity}: {count}"
        for severity, count in sorted(
            result.severity_counts.items(),
        )
    ]

    return (
        f"{result.profile} review completed. "
        f"Inspected {result.inspected_files_count} file(s). "
        f"{scope_part} "
        f"Found {result.findings_count} issue(s) "
        f"({', '.join(severity_parts)}). "
        f"Report: {result.report_path}"
    )


def contains_any(
    text: str,
    tokens: list[str],
) -> bool:
    lowered = text.lower()

    return any(
        token.lower() in lowered
        for token in tokens
    )


def detect_security_findings_for_file(
    *,
    file_path: str,
    content: str,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    path_name = Path(
        file_path,
    ).name.lower()

    lowered = content.lower()

    if (
        "secret_key" in lowered
        and "=" in content
        and "os.environ" not in lowered
    ):
        findings.append(
            {
                "finding_type": FINDING_TYPE_SECURITY_HARDCODED_SECRET,
                "file": file_path,
                "severity": "CRITICAL",
                "category": "SECURITY",
                "issue": "Hardcoded SECRET_KEY.",
                "evidence": "SECRET_KEY appears to be assigned directly in source code.",
                "recommendation": "Load secret keys from a secure secret manager or environment configuration.",
            }
        )

    if contains_any(
        lowered,
        [
            "admin_password",
            "admin_username",
            "username == \"admin\"",
            "username == 'admin'",
            "password == \"admin\"",
            "password == 'admin'",
        ],
    ):
        findings.append(
            {
                "finding_type": FINDING_TYPE_SECURITY_HARDCODED_ADMIN_CREDENTIALS,
                "file": file_path,
                "severity": "CRITICAL",
                "category": "SECURITY",
                "issue": "Hardcoded admin credentials.",
                "evidence": "Administrative username or password logic appears directly in source code.",
                "recommendation": "Move credentials to secure storage and use a proper authentication provider.",
            }
        )

    if contains_any(
        lowered,
        [
            "debug = true",
            "debug=true",
            "app.run(debug=true",
        ],
    ):
        findings.append(
            {
                "finding_type": FINDING_TYPE_SECURITY_DEBUG_MODE,
                "file": file_path,
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Debug mode enabled.",
                "evidence": "Debug mode appears to be enabled in source code.",
                "recommendation": "Disable debug mode in production configuration.",
            }
        )

    if (
        "def verify_token" in lowered
        and contains_any(
            lowered,
            [
                "return bool(token)",
                "return token",
                "if token:",
                "return true",
            ],
        )
    ):
        findings.append(
            {
                "finding_type": FINDING_TYPE_SECURITY_TOKEN_VALIDATION,
                "file": file_path,
                "severity": "CRITICAL",
                "category": "SECURITY",
                "issue": "Token validation is incomplete.",
                "evidence": "Token verification appears to accept a token without cryptographic validation.",
                "recommendation": "Validate token signature, issuer, audience, and expiration before accepting it.",
            }
        )

    if (
        contains_any(
            lowered,
            [
                "create_token",
                "generate_token",
                "token =",
            ],
        )
        and "exp" not in lowered
        and "expires" not in lowered
    ):
        findings.append(
            {
                "finding_type": FINDING_TYPE_SECURITY_TOKEN_EXPIRATION,
                "file": file_path,
                "severity": "CRITICAL",
                "category": "SECURITY",
                "issue": "Tokens may be unsigned or non-expiring.",
                "evidence": "Token creation code does not show expiration handling.",
                "recommendation": "Use signed tokens with explicit expiration claims.",
            }
        )

    if (
        path_name == "app.py"
        and "debug" in lowered
        and contains_any(
            lowered,
            [
                "return",
                "jsonify",
                "response",
            ],
        )
    ):
        findings.append(
            {
                "finding_type": FINDING_TYPE_SECURITY_INFORMATION_DISCLOSURE,
                "file": file_path,
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Debug information may be exposed in API responses.",
                "evidence": "Application response logic appears to expose debug-related values.",
                "recommendation": "Do not expose debug flags or internal runtime details in external API responses.",
            }
        )

    return findings

def detect_findings_for_file(
    *,
    file_path: str,
    content: str,
    profile: str,
) -> list[dict[str, Any]]:
    if profile in {
        REVIEW_PROFILE_SECURITY,
        REVIEW_PROFILE_FULL,
    }:
        return detect_security_findings_for_file(
            file_path=file_path,
            content=content,
        )

    return []


def collect_knowledge_context(
    *,
    context: AgentLoopMcpContext,
    knowledge_queries: list[str],
) -> str:
    chunks = []

    for query in knowledge_queries:
        results = search_knowledge_for_review(
            context=context,
            query=query,
        )

        for item in results:
            source = (
                item.get(
                    "source",
                    "",
                )
                or item.get(
                    "document_id",
                    "",
                )
            )

            text = (
                item.get(
                    "text",
                    "",
                )
                or item.get(
                    "content",
                    "",
                )
            )

            if text:
                chunks.append(
                    f"Source: {source}\n{text}"
                )

    return "\n\n".join(
        chunks,
    )


def detect_findings_with_reviewer(
    *,
    reviewer: str,
    file_path: str,
    content: str,
    profile: str,
    policy_context: str,
    openai_reviewer: OpenAIReviewReviewer | None,
) -> list[dict[str, Any]]:
    if reviewer == REVIEWER_DETERMINISTIC:
        return detect_findings_for_file(
            file_path=file_path,
            content=content,
            profile=profile,
        )

    if reviewer == REVIEWER_OPENAI:
        if openai_reviewer is None:
            raise ValueError(
                "openai_reviewer is required for OpenAI reviewer."
            )

        return openai_reviewer.review_file(
            file_path=file_path,
            content=content,
            profile=profile,
            policy_context=policy_context,
        )

    raise ValueError(
        f"unsupported reviewer: {reviewer}"
    )


def review_project(
    *,
    context: AgentLoopMcpContext,
    project_path: str,
    profile: str = REVIEW_PROFILE_SECURITY,
    report_path: str = "",
    report_dir: str = "",
    allowed_root: str = "",
    include_globs: str | list[str] | None = None,
    exclude_globs: str | list[str] | None = None,
    max_files: int = DEFAULT_MAX_FILES,
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
    reviewer: str = DEFAULT_REVIEWER,
    model: str = DEFAULT_OPENAI_REVIEW_MODEL,
    reviews_dir: str = "",
    openai_client_class: Any = None,
) -> ReviewProjectResult:
    review_profile = get_review_profile(
        profile,
    )

    selected_reviewer = validate_reviewer(
        reviewer,
    )

    selected_files = select_project_files(
        project_path=project_path,
        allowed_root=allowed_root,
        include_globs=include_globs,
        exclude_globs=exclude_globs,
        max_files=max_files,
        max_file_size_bytes=max_file_size_bytes,
    )

    if report_path:
        context.report_path = report_path
    elif report_dir:
        context.report_path = build_generated_report_path(
            project_path=selected_files.project_path,
            report_dir=report_dir,
            profile=review_profile.name,
        )

    policy_context = collect_knowledge_context(
        context=context,
        knowledge_queries=review_profile.knowledge_queries,
    )

    openai_reviewer = None

    if selected_reviewer == REVIEWER_OPENAI:
        openai_reviewer = OpenAIReviewReviewer(
            model=model,
            client_class=openai_client_class,
        )

    for file_path in selected_files.files:
        content = read_file_for_review(
            context=context,
            path=file_path,
        )

        findings = detect_findings_with_reviewer(
            reviewer=selected_reviewer,
            file_path=file_path,
            content=content,
            profile=review_profile.name,
            policy_context=policy_context,
            openai_reviewer=openai_reviewer,
        )

        for finding in findings:
            add_finding_for_review(
                context=context,
                finding=finding,
            )

    written_report_path = write_report_for_review(
        context=context,
    )

    scope = {
        "selected_files_count": len(
            selected_files.files,
        ),
        "skipped_files_count": len(
            selected_files.skipped_files,
        ),
        "include_globs": selected_files.include_globs,
        "exclude_globs": selected_files.exclude_globs,
        "max_files": selected_files.max_files,
        "max_file_size_bytes": selected_files.max_file_size_bytes,
        "allowed_root": allowed_root,
    }

    result_without_summary = ReviewProjectResult(
        status="completed",
        profile=review_profile.name,
        reviewer=selected_reviewer,
        model=(
            model
            if selected_reviewer == REVIEWER_OPENAI
            else ""
        ),
        project_path=selected_files.project_path,
        inspected_files_count=len(
            context.state.inspected_files,
        ),
        selected_files_count=len(
            selected_files.files,
        ),
        skipped_files_count=len(
            selected_files.skipped_files,
        ),
        findings_count=len(
            context.state.findings,
        ),
        severity_counts=count_findings_by_severity(
            context.state.findings,
        ),
        report_path=written_report_path,
        summary="",
        scope=scope,
        findings=list(
            context.state.findings,
        ),
        run_id="",
        run_dir="",
        artifacts={},
    )

    summary = build_review_summary(
        result=result_without_summary,
    )

    run_id = ""
    run_dir = ""
    artifacts: dict[str, Any] = {}

    if reviews_dir:
        review_artifacts = create_review_run_package(
            reviews_dir=reviews_dir,
            project_path=result_without_summary.project_path,
            profile=result_without_summary.profile,
            reviewer=result_without_summary.reviewer,
            model=result_without_summary.model,
            status=result_without_summary.status,
            summary=summary,
            findings=result_without_summary.findings,
            selected_files=list(
                selected_files.files,
            ),
            skipped_files=list(
                selected_files.skipped_files,
            ),
            scope=result_without_summary.scope,
            source_report_path=result_without_summary.report_path,
            run_config={
                "project_path": project_path,
                "profile": profile,
                "reviewer": selected_reviewer,
                "model": (
                    model
                    if selected_reviewer == REVIEWER_OPENAI
                    else ""
                ),
                "report_path": report_path,
                "report_dir": report_dir,
                "reviews_dir": reviews_dir,
                "allowed_root": allowed_root,
                "include_globs": selected_files.include_globs,
                "exclude_globs": selected_files.exclude_globs,
                "max_files": max_files,
                "max_file_size_bytes": max_file_size_bytes,
            },
        )

        artifacts = review_run_artifacts_to_dict(
            review_artifacts,
        )

        run_id = review_artifacts.run_id
        run_dir = review_artifacts.run_dir

    return ReviewProjectResult(
        status=result_without_summary.status,
        profile=result_without_summary.profile,
        reviewer=result_without_summary.reviewer,
        model=result_without_summary.model,
        project_path=result_without_summary.project_path,
        inspected_files_count=result_without_summary.inspected_files_count,
        selected_files_count=result_without_summary.selected_files_count,
        skipped_files_count=result_without_summary.skipped_files_count,
        findings_count=result_without_summary.findings_count,
        severity_counts=result_without_summary.severity_counts,
        report_path=result_without_summary.report_path,
        summary=summary,
        scope=result_without_summary.scope,
        findings=result_without_summary.findings,
        run_id=run_id,
        run_dir=run_dir,
        artifacts=artifacts,
    )