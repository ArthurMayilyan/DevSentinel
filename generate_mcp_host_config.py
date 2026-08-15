import argparse
from pathlib import Path

from mcp_host_config import (
    SUPPORTED_MCP_HOSTS,
    build_mcp_host_config,
    mcp_host_config_to_json,
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate external MCP host configuration for AgentLoop."
    )

    parser.add_argument(
        "--host",
        choices=sorted(
            SUPPORTED_MCP_HOSTS,
        ),
        required=True,
    )

    parser.add_argument(
        "--server-name",
        default="agentloop",
    )

    parser.add_argument(
        "--server-script-path",
        default="run_mcp_server.py",
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
        default="report.md",
    )

    parser.add_argument(
        "--python-executable",
        default="",
    )

    parser.add_argument(
        "--output",
        default="",
    )

    return parser


def run_from_args(
    raw_args=None,
) -> str:
    parser = build_arg_parser()
    args = parser.parse_args(
        raw_args,
    )

    config = build_mcp_host_config(
        host=args.host,
        server_name=args.server_name,
        server_script_path=args.server_script_path,
        knowledge_path=args.knowledge_path,
        index_path=args.index_path,
        report_path=args.report_path,
        python_executable=args.python_executable,
    )

    if isinstance(
        config,
        str,
    ):
        output = config
    else:
        output = mcp_host_config_to_json(
            config,
        )

    if args.output:
        output_path = Path(
            args.output,
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            output,
            encoding="utf-8",
        )

    return output


def main() -> None:
    print(
        run_from_args()
    )


if __name__ == "__main__":
    main()