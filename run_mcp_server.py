import argparse

from mcp_tool_catalog import list_mcp_tool_specs_for_mode
from agent_loop_mcp_server import create_agent_loop_mcp_server
from mcp_server_context import (
    DEFAULT_MCP_REPORT_PATH,
    build_agent_loop_mcp_context,
)

SUPPORTED_MCP_TRANSPORTS = {
    "stdio",
    "streamable-http",
}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the AgentLoop MCP server."
    )

    parser.add_argument(
        "--transport",
        choices=sorted(
            SUPPORTED_MCP_TRANSPORTS,
        ),
        default="stdio",
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
        default=DEFAULT_MCP_REPORT_PATH,
    )

    parser.add_argument(
        "--describe",
        action="store_true",
    )

    return parser


def format_server_description() -> str:
    specs = list_mcp_tool_specs_for_mode()

    lines = [
        "AgentLoop MCP server",
        "",
        "Tools:",
    ]

    for spec in specs:
        lines.append(
            f"- {spec.name}"
        )

    return "\n".join(
        lines,
    )


def run_from_args(
    raw_args=None,
) -> str:
    parser = build_arg_parser()
    args = parser.parse_args(
        raw_args,
    )

    if args.describe:
        return format_server_description()

    context = build_agent_loop_mcp_context(
        knowledge_path=args.knowledge_path,
        index_path=args.index_path,
        report_path=args.report_path,
    )

    mcp = create_agent_loop_mcp_server(
        context=context,
    )

    if args.transport == "stdio":
        mcp.run()
        return ""

    if args.transport == "streamable-http":
        mcp.run(
            "streamable-http",
        )
        return ""

    raise ValueError(
        f"unsupported MCP transport: {args.transport}"
    )


def main() -> None:
    output = run_from_args()

    if output:
        print(
            output,
        )


if __name__ == "__main__":
    main()