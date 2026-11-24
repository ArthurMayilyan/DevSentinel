import argparse
import sys
from pathlib import Path

from devsentinel.mcp.mcp_tool_catalog import list_mcp_tool_specs_for_mode
from devsentinel.mcp.devsentinel_mcp_server import create_devsentinel_mcp_server
from devsentinel.mcp.mcp_server_context import (
    DEFAULT_MCP_REPORT_PATH,
    build_devsentinel_mcp_context,
)

SUPPORTED_MCP_TRANSPORTS = {
    "stdio",
    "streamable-http",
}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the DevSentinel MCP server."
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
        "--project-root",
        default="",
        help=(
            "Directory that list_files, read_file and search_in_files are "
            "confined to. Defaults to the directory the server was launched "
            "from; the chosen root is logged to stderr at startup."
        ),
    )

    parser.add_argument(
        "--describe",
        action="store_true",
    )

    return parser


def format_server_description() -> str:
    specs = list_mcp_tool_specs_for_mode()

    lines = [
        "DevSentinel MCP server",
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

    launch_dir = Path.cwd()

    context = build_devsentinel_mcp_context(
        knowledge_path=args.knowledge_path,
        index_path=args.index_path,
        report_path=args.report_path,
        project_root=str(
            launch_dir / (args.project_root or "."),
        ),
        path_base_dir=str(launch_dir),
    )

    # stderr only: stdout carries the MCP stdio protocol.
    print(
        f"DevSentinel MCP: file tools confined to {context.project_scope.root}",
        file=sys.stderr,
    )

    mcp = create_devsentinel_mcp_server(
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