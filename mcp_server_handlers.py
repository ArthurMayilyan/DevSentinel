from pathlib import Path
from typing import Any

from mcp_server_context import AgentLoopMcpContext
from rag_tool import DEFAULT_RAG_TOP_K, search_knowledge as search_rag_knowledge
from tool_specs import IssueCategory, IssueSeverity
from tools import (
    list_files as list_project_files,
    read_file as read_project_file,
    render_report_from_state,
    search_in_files as search_project_files,
)

from review_project_workflow import review_project_result_to_dict, review_project




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


def mcp_list_files(
    *,
    context: AgentLoopMcpContext,
    path: str,
) -> list[str]:
    files = list_project_files(
        path,
    )

    for file in files:
        append_unique(
            context.state.discovered_files,
            file,
        )

    return files


def mcp_read_file(
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


def mcp_search_in_files(
    *,
    context: AgentLoopMcpContext,
    path: str,
    query: str,
) -> list[dict[str, Any]]:
    return search_project_files(
        path=path,
        query=query,
    )


def mcp_search_knowledge(
    *,
    context: AgentLoopMcpContext,
    query: str,
    top_k: int = DEFAULT_RAG_TOP_K,
) -> list[dict[str, Any]]:
    if context.rag_store is None:
        raise ValueError(
            "search_knowledge requires knowledge_path or index_path."
        )

    return search_rag_knowledge(
        store=context.rag_store,
        query=query,
        top_k=top_k,
    )


def mcp_add_finding(
    *,
    context: AgentLoopMcpContext,
    file: str,
    severity: str,
    category: str,
    issue: str,
    evidence: str,
    recommendation: str,
) -> str:
    normalized_severity = normalize_enum_value(
        value=severity,
        enum_cls=IssueSeverity,
    )

    normalized_category = normalize_enum_value(
        value=category,
        enum_cls=IssueCategory,
    )

    finding = {
        "file": file,
        "severity": normalized_severity,
        "category": normalized_category,
        "issue": issue,
        "evidence": evidence,
        "recommendation": recommendation,
    }

    context.state.findings.append(
        finding,
    )

    return "Finding added."


def mcp_write_report(
    *,
    context: AgentLoopMcpContext,
) -> str:
    markdown = render_report_from_state(
        context.state,
    )

    report_path = Path(
        context.report_path,
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

def mcp_review_project(
    *,
    context: AgentLoopMcpContext,
    project_path: str,
    profile: str = "security",
    report_path: str = "",
) -> dict[str, Any]:
    result = review_project(
        context=context,
        project_path=project_path,
        profile=profile,
        report_path=report_path,
    )

    return review_project_result_to_dict(
        result,
    )