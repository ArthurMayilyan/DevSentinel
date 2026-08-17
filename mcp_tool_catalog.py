from typing import Any

from mcp_tool_contract import McpToolSpec


def string_property(
    description: str,
) -> dict[str, Any]:
    return {
        "type": "string",
        "description": description,
    }


def integer_property(
    description: str,
) -> dict[str, Any]:
    return {
        "type": "integer",
        "description": description,
    }


def object_schema(
    *,
    properties: dict[str, Any],
    required: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required or [],
        "additionalProperties": False,
    }


def generic_output_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "result": {
                "description": "Tool result payload.",
            }
        },
        "required": [],
        "additionalProperties": True,
    }


def build_review_project_tool_spec() -> McpToolSpec:
    return McpToolSpec(
        name="review_project",
        description="Run a full project review workflow and write a report.",
        input_schema=object_schema(
            properties={
                "project_path": string_property(
                    "Local project directory to review.",
                ),
                "profile": {
                    "type": "string",
                    "description": "Review profile.",
                    "enum": [
                        "security",
                        "reliability",
                        "maintainability",
                        "full",
                    ],
                },
                "report_path": string_property(
                    "Optional exact report output path.",
                ),
                "report_dir": string_property(
                    "Optional directory where a timestamped report should be created.",
                ),
                "reviews_dir": string_property(
                    "Optional directory for persistent review run packages and history.",
                ),                
                "allowed_root": string_property(
                    "Optional root directory boundary. project_path must be inside it.",
                ),
                "include_globs": string_property(
                    "Optional comma-separated include globs, for example: **/*.py,**/*.ts.",
                ),
                "exclude_globs": string_property(
                    "Optional comma-separated exclude globs, for example: tests/**,docs/**.",
                ),
                "max_files": integer_property(
                    "Maximum number of files to inspect.",
                ),
                "max_file_size_bytes": integer_property(
                    "Maximum size of each inspected file in bytes.",
                ),
            },
            required=[
                "project_path",
            ],
        ),
        output_schema=generic_output_schema(),
    )


def build_list_files_tool_spec() -> McpToolSpec:
    return McpToolSpec(
        name="list_files",
        description="List files under a local project path.",
        input_schema=object_schema(
            properties={
                "path": string_property(
                    "Directory path to list.",
                ),
            },
            required=[
                "path",
            ],
        ),
        output_schema=generic_output_schema(),
    )


def build_read_file_tool_spec() -> McpToolSpec:
    return McpToolSpec(
        name="read_file",
        description="Read a local text file by path.",
        input_schema=object_schema(
            properties={
                "path": string_property(
                    "File path to read.",
                ),
            },
            required=[
                "path",
            ],
        ),
        output_schema=generic_output_schema(),
    )


def build_search_in_files_tool_spec() -> McpToolSpec:
    return McpToolSpec(
        name="search_in_files",
        description="Search for text inside files under a local path.",
        input_schema=object_schema(
            properties={
                "path": string_property(
                    "Directory path to search.",
                ),
                "query": string_property(
                    "Text query to search for.",
                ),
            },
            required=[
                "path",
                "query",
            ],
        ),
        output_schema=generic_output_schema(),
    )


def build_add_finding_tool_spec() -> McpToolSpec:
    return McpToolSpec(
        name="add_finding",
        description="Add a structured code review finding to agent state.",
        input_schema=object_schema(
            properties={
                "file": string_property(
                    "File path where the issue was found.",
                ),
                "severity": {
                    "type": "string",
                    "description": "Finding severity.",
                    "enum": [
                        "LOW",
                        "MEDIUM",
                        "HIGH",
                        "CRITICAL",
                    ],
                },
                "category": {
                    "type": "string",
                    "description": "Finding category.",
                    "enum": [
                        "SECURITY",
                        "MAINTAINABILITY",
                        "RELIABILITY",
                        "PERFORMANCE",
                    ],
                },
                "issue": string_property(
                    "Short issue description.",
                ),
                "evidence": string_property(
                    "Evidence supporting the finding.",
                ),
                "recommendation": string_property(
                    "Recommended fix.",
                ),
            },
            required=[
                "file",
                "severity",
                "category",
                "issue",
                "evidence",
                "recommendation",
            ],
        ),
        output_schema=generic_output_schema(),
    )


def build_write_report_tool_spec() -> McpToolSpec:
    return McpToolSpec(
        name="write_report",
        description="Generate and write the final code review report from current agent state.",
        input_schema=object_schema(
            properties={},
            required=[],
        ),
        output_schema=generic_output_schema(),
    )


def build_search_knowledge_tool_spec() -> McpToolSpec:
    return McpToolSpec(
        name="search_knowledge",
        description="Search the attached RAG knowledge base.",
        input_schema=object_schema(
            properties={
                "query": string_property(
                    "Knowledge search query.",
                ),
                "top_k": integer_property(
                    "Maximum number of chunks to return.",
                ),
            },
            required=[
                "query",
            ],
        ),
        output_schema=generic_output_schema(),
    )


def build_all_mcp_tool_specs() -> list[McpToolSpec]:
    return [
        build_list_files_tool_spec(),
        build_read_file_tool_spec(),
        build_search_in_files_tool_spec(),
        build_search_knowledge_tool_spec(),
        build_add_finding_tool_spec(),
        build_write_report_tool_spec(),
        build_review_project_tool_spec(),
    ]


def build_code_review_mcp_tool_specs() -> list[McpToolSpec]:
    return [
        build_list_files_tool_spec(),
        build_read_file_tool_spec(),
        build_search_in_files_tool_spec(),
        build_search_knowledge_tool_spec(),
        build_add_finding_tool_spec(),
        build_write_report_tool_spec(),
        build_review_project_tool_spec(),
    ]


def build_rag_qa_mcp_tool_specs() -> list[McpToolSpec]:
    return [
        build_search_knowledge_tool_spec(),
    ]


def list_mcp_tool_specs_for_mode(
    mode: str = "",
) -> list[McpToolSpec]:
    if mode == "code_review":
        return build_code_review_mcp_tool_specs()

    if mode == "rag_qa":
        return build_rag_qa_mcp_tool_specs()

    if not mode:
        return build_all_mcp_tool_specs()

    raise ValueError(
        f"unsupported mode for MCP tool catalog: {mode}"
    )