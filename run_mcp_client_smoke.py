import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from mcp import Client

from agent_loop_mcp_server import create_agent_loop_mcp_server
from mcp_server_context import build_agent_loop_mcp_context


def serialize_tool_result(
    value: Any,
) -> Any:
    if hasattr(
        value,
        "model_dump",
    ):
        return value.model_dump(
            mode="json",
        )

    if isinstance(
        value,
        list,
    ):
        return [
            serialize_tool_result(
                item,
            )
            for item in value
        ]

    if isinstance(
        value,
        dict,
    ):
        return {
            key: serialize_tool_result(
                item,
            )
            for key, item in value.items()
        }

    return value


def extract_mcp_tool_payload(
    tool_result,
) -> Any:
    if getattr(
        tool_result,
        "structured_content",
        None,
    ) is not None:
        return serialize_tool_result(
            tool_result.structured_content,
        )

    content = getattr(
        tool_result,
        "content",
        None,
    )

    if not content:
        return None

    first_item = content[0]
    text = getattr(
        first_item,
        "text",
        None,
    )

    if text is None:
        return serialize_tool_result(
            content,
        )

    try:
        return json.loads(
            text,
        )
    except json.JSONDecodeError:
        return text


async def run_mcp_client_smoke(
    *,
    project_path: str,
    knowledge_path: str = "",
    index_path: str = "",
    report_path: str = "mcp_client_smoke_report.md",
) -> dict[str, Any]:
    context = build_agent_loop_mcp_context(
        knowledge_path=knowledge_path,
        index_path=index_path,
        report_path=report_path,
    )

    mcp = create_agent_loop_mcp_server(
        context=context,
    )

    async with Client(
        mcp,
    ) as client:
        tools_result = await client.list_tools()

        resources_result = await client.list_resources()
        prompts_result = await client.list_prompts()

        resource_uris = [
            str(
                resource.uri,
            )
            for resource in resources_result.resources
        ]

        prompt_names = [
            prompt.name
            for prompt in prompts_result.prompts
        ]

        project_guide_result = await client.read_resource(
            "agentloop://project-guide",
        )

        review_project_prompt = await client.get_prompt(
            "review_project",
            {
                "project_path": project_path,
            },
        )

        tool_names = [
            tool.name
            for tool in tools_result.tools
        ]

        list_files_result = await client.call_tool(
            "list_files",
            {
                "path": project_path,
            },
        )

        read_file_result = await client.call_tool(
            "read_file",
            {
                "path": str(
                    Path(
                        project_path,
                    )
                    / "app.py"
                ),
            },
        )

        add_finding_result = await client.call_tool(
            "add_finding",
            {
                "file": str(
                    Path(
                        project_path,
                    )
                    / "app.py"
                ),
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Hardcoded credential risk.",
                "evidence": "A sensitive value appears directly in source code.",
                "recommendation": "Move sensitive values to secure configuration.",
            },
        )

        write_report_result = await client.call_tool(
            "write_report",
            {},
        )

        review_project_result = await client.call_tool(
            "review_project",
            {
                "project_path": project_path,
                "profile": "security",
                "report_path": report_path,
            },
        )

        search_knowledge_payload = None

        if knowledge_path or index_path:
            search_knowledge_result = await client.call_tool(
                "search_knowledge",
                {
                    "query": "credentials production",
                },
            )

            search_knowledge_payload = extract_mcp_tool_payload(
                search_knowledge_result,
            )

        return {
            "tools": tool_names,
            "resources": resource_uris,
            "prompts": prompt_names,
            "project_guide": serialize_tool_result(
                project_guide_result.contents,
            ),
            "review_project_prompt": serialize_tool_result(
                review_project_prompt.messages,
            ),
            "list_files": extract_mcp_tool_payload(
                list_files_result,
            ),
            "read_file_is_error": read_file_result.is_error,
            "add_finding": extract_mcp_tool_payload(
                add_finding_result,
            ),
            "write_report": extract_mcp_tool_payload(
                write_report_result,
            ),
            "review_project": extract_mcp_tool_payload(
                review_project_result,
            ),
            "search_knowledge": search_knowledge_payload,
            "report_path": report_path,
        }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run an in-process MCP client smoke test."
    )

    parser.add_argument(
        "--project-path",
        default="./sample_project",
    )

    parser.add_argument(
        "--knowledge-path",
        default="",
    )

    parser.add_argument(
        "--index-path",
        default="",
    )

    parser.add_argument(
        "--report-path",
        default="mcp_client_smoke_report.md",
    )

    parser.add_argument(
        "--json",
        action="store_true",
    )

    return parser


def run_from_args(
    raw_args=None,
) -> str:
    parser = build_arg_parser()
    args = parser.parse_args(
        raw_args,
    )

    result = asyncio.run(
        run_mcp_client_smoke(
            project_path=args.project_path,
            knowledge_path=args.knowledge_path,
            index_path=args.index_path,
            report_path=args.report_path,
        )
    )

    if args.json:
        return json.dumps(
            result,
            indent=2,
        )

    lines = [
        "MCP client smoke test passed",
        "",
        "Tools:",
    ]

    for tool_name in result["tools"]:
        lines.append(
            f"- {tool_name}"
        )

    lines.extend(
        [
            "",
            "Resources:",
        ]
    )

    for resource_uri in result["resources"]:
        lines.append(
            f"- {resource_uri}"
        )

    lines.extend(
        [
            "",
            "Prompts:",
        ]
    )

    for prompt_name in result["prompts"]:
        lines.append(
            f"- {prompt_name}"
        )

    lines.extend(
        [
            "",
            "Product workflow:",
            "- review_project",
        ]
    )

    lines.extend(
        [
            "",
            f"Report path: {result['report_path']}",
        ]
    )

    return "\n".join(
        lines,
    )


def main() -> None:
    print(
        run_from_args()
    )


if __name__ == "__main__":
    main()

