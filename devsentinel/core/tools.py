from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Any

from devsentinel.core.agent_state import AgentState
from devsentinel.core.tool_path_utils import (
    ProjectScope,
    display_tool_path,
    iter_files_within_root,
    require_project_scope,
    resolve_file_for_read,
    resolve_search_location,
)
from devsentinel.config.app_settings import get_app_settings


_SETTINGS = get_app_settings()


def is_absolute_request(
    path: str,
) -> bool:
    return Path(path.strip()).is_absolute()


def list_files(
    path: str,
    *,
    scope: ProjectScope | None = None,
) -> list[str]:
    active_scope = require_project_scope(
        scope=scope,
        requested=path,
    )

    directory = resolve_search_location(
        scope=active_scope,
        requested=path,
    )

    if not directory.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")

    return [
        display_tool_path(
            scope=active_scope,
            path=file_path,
            absolute=is_absolute_request(path),
        )
        for file_path in iter_files_within_root(
            root=active_scope.root,
            start=directory,
        )
    ]


def read_file(
    path: str,
    *,
    scope: ProjectScope | None = None,
) -> str:
    file_path = resolve_file_for_read(
        scope=scope,
        requested=path,
    )

    return file_path.read_text(encoding="utf-8")


def search_in_files(
    query: str,
    path: str,
    *,
    scope: ProjectScope | None = None,
) -> list[dict]:
    active_scope = require_project_scope(
        scope=scope,
        requested=path,
    )

    location = resolve_search_location(
        scope=active_scope,
        requested=path,
    )

    results = []

    for file_path in iter_files_within_root(
        root=active_scope.root,
        start=location,
    ):
        if file_path.stat().st_size > active_scope.max_file_size_bytes:
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for line_number, line in enumerate(content.splitlines(), start=1):
            if query in line:
                results.append({
                    "file": display_tool_path(
                        scope=active_scope,
                        path=file_path,
                        absolute=is_absolute_request(path),
                    ),
                    "line": line_number,
                    "text": line.strip()
                })

    return results


def build_project_file_tools(
    *,
    scope: ProjectScope | None,
) -> dict[str, Callable[..., Any]]:
    """Return list_files/read_file/search_in_files bound to one project scope.

    With scope=None every call is rejected with project_root_not_configured;
    the tools never fall back to the process working directory.
    """
    return {
        "list_files": partial(list_files, scope=scope),
        "read_file": partial(read_file, scope=scope),
        "search_in_files": partial(search_in_files, scope=scope),
    }

def render_report_from_state(state: AgentState) -> str:
    lines = []

    lines.append("# Code Review Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")

    findings_count = len(state.findings)

    lines.append(
        f"Reviewed the project and found {findings_count} issue(s)."
    )
    lines.append("")

    if state.inspected_files:
        lines.append("## Inspected Files")
        lines.append("")

        for file in state.inspected_files:
            lines.append(f"- `{file}`")

        lines.append("")

    lines.append("## Findings")
    lines.append("")

    if not state.findings:
        lines.append("No findings were recorded.")
        lines.append("")
    else:
        for index, finding in enumerate(state.findings, start=1):
            lines.append(f"### {index}. {finding['issue']}")
            lines.append("")
            lines.append(f"- **File:** `{finding['file']}`")
            lines.append(f"- **Severity:** {finding['severity']}")
            lines.append(f"- **Category:** {finding['category']}")
            lines.append(f"- **Evidence:** {finding['evidence']}")
            lines.append(f"- **Recommendation:** {finding['recommendation']}")
            lines.append("")

    if state.errors:
        lines.append("## Errors")
        lines.append("")

        for error in state.errors:
            lines.append(f"- {error}")

        lines.append("")

    lines.append("## Overall Recommendation")
    lines.append("")

    if state.findings:
        lines.append(
            "Prioritize HIGH severity findings first, especially security issues "
            "related to authentication, secrets, and access control."
        )
    else:
        lines.append(
            "No issues were recorded by the agent. Review evaluator results to confirm coverage."
        )

    lines.append("")

    return "\n".join(lines)


def write_report(
    state: AgentState,
    *,
    report_path: str | None = None,
) -> str:
    markdown = render_report_from_state(
        state,
    )

    report_file = Path(
        report_path or _SETTINGS.artifacts.default_report_path,
    )

    report_file.write_text(
        markdown,
        encoding="utf-8",
    )

    state.report_written = True
    state.report_path = str(
        report_file,
    )

    return str(
        report_file,
    )