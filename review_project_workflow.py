from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from mcp_server_context import AgentLoopMcpContext
from project_path_safety import select_project_files
from rag_tool import search_knowledge as search_rag_knowledge
from review_profiles import (
    REVIEW_PROFILE_FULL,
    REVIEW_PROFILE_SECURITY,
    get_review_profile,
)
from tools import read_file as read_project_file
from tools import render_report_from_state
from tool_specs import IssueCategory, IssueSeverity


@dataclass(frozen=True)
class ReviewProjectResult:
    status: str
    profile: str
    project_path: str
    inspected_files_count: int
    findings_count: int
    severity_counts: dict[str, int]
    report_path: str
    summary: str
    findings: list[dict[str, Any]]


def review_project_result_to_dict(
    result: ReviewProjectResult,
) -> dict[str, Any]:
    return asdict(
        result,
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
    normalized_finding = {
        "file": finding["file"],
        "severity": normalize_enum_value(
            value=finding["severity"],
            enum_cls=IssueSeverity,
        ),
        "category": normalize_enum_value(
            value=finding["category"],
            enum_cls=IssueCategory,
        ),
        "issue": finding["issue"],
        "evidence": finding["evidence"],
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
) -> tuple[str, str, str]:
    return (
        str(
            finding.get(
                "file",
                "",
            )
        ),
        str(
            finding.get(
                "issue",
                "",
            )
        ),
        str(
            finding.get(
                "evidence",
                "",
            )
        ),
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
    if not result.findings_count:
        return (
            f"{result.profile} review completed. "
            f"Inspected {result.inspected_files_count} file(s). "
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

    if "secret_key" in lowered and "=" in content and "os.environ" not in lowered:
        findings.append(
            {
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
                "file": file_path,
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Debug mode enabled.",
                "evidence": "Debug mode appears to be enabled in source code.",
                "recommendation": "Disable debug mode in production configuration.",
            }
        )

    if "def verify_token" in lowered and contains_any(
        lowered,
        [
            "return bool(token)",
            "return token",
            "if token:",
            "return true",
        ],
    ):
        findings.append(
            {
                "file": file_path,
                "severity": "CRITICAL",
                "category": "SECURITY",
                "issue": "Token validation is incomplete.",
                "evidence": "Token verification appears to accept a token without cryptographic validation.",
                "recommendation": "Validate token signature, issuer, audience, and expiration before accepting it.",
            }
        )

    if contains_any(
        lowered,
        [
            "create_token",
            "generate_token",
            "token =",
        ],
    ) and "exp" not in lowered and "expires" not in lowered:
        findings.append(
            {
                "file": file_path,
                "severity": "CRITICAL",
                "category": "SECURITY",
                "issue": "Tokens may be unsigned or non-expiring.",
                "evidence": "Token creation code does not show expiration handling.",
                "recommendation": "Use signed tokens with explicit expiration claims.",
            }
        )

    if path_name == "app.py" and "debug" in lowered and contains_any(
        lowered,
        [
            "return",
            "jsonify",
            "response",
        ],
    ):
        findings.append(
            {
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


def warm_up_knowledge_context(
    *,
    context: AgentLoopMcpContext,
    knowledge_queries: list[str],
) -> None:
    for query in knowledge_queries:
        search_knowledge_for_review(
            context=context,
            query=query,
        )


def review_project(
    *,
    context: AgentLoopMcpContext,
    project_path: str,
    profile: str = REVIEW_PROFILE_SECURITY,
    report_path: str = "",
) -> ReviewProjectResult:
    review_profile = get_review_profile(
        profile,
    )

    if report_path:
        context.report_path = report_path

    selected_files = select_project_files(
        project_path=project_path,
    )

    warm_up_knowledge_context(
        context=context,
        knowledge_queries=review_profile.knowledge_queries,
    )

    for file_path in selected_files.files:
        content = read_file_for_review(
            context=context,
            path=file_path,
        )

        findings = detect_findings_for_file(
            file_path=file_path,
            content=content,
            profile=review_profile.name,
        )

        for finding in findings:
            add_finding_for_review(
                context=context,
                finding=finding,
            )

    written_report_path = write_report_for_review(
        context=context,
    )

    result_without_summary = ReviewProjectResult(
        status="completed",
        profile=review_profile.name,
        project_path=selected_files.project_path,
        inspected_files_count=len(
            context.state.inspected_files,
        ),
        findings_count=len(
            context.state.findings,
        ),
        severity_counts=count_findings_by_severity(
            context.state.findings,
        ),
        report_path=written_report_path,
        summary="",
        findings=list(
            context.state.findings,
        ),
    )

    summary = build_review_summary(
        result=result_without_summary,
    )

    return ReviewProjectResult(
        status=result_without_summary.status,
        profile=result_without_summary.profile,
        project_path=result_without_summary.project_path,
        inspected_files_count=result_without_summary.inspected_files_count,
        findings_count=result_without_summary.findings_count,
        severity_counts=result_without_summary.severity_counts,
        report_path=result_without_summary.report_path,
        summary=summary,
        findings=result_without_summary.findings,
    )