import argparse
import json

from mcp_tool_catalog import list_mcp_tool_specs_for_mode
from mcp_tool_contract import (
    mcp_tool_spec_to_dict,
    mcp_tool_spec_to_mcp_tool,
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List MCP-ready tool specifications."
    )

    parser.add_argument(
        "--mode",
        choices=[
            "",
            "code_review",
            "rag_qa",
        ],
        default="",
    )

    parser.add_argument(
        "--json",
        action="store_true",
    )

    parser.add_argument(
        "--mcp-json",
        action="store_true",
    )

    return parser


def format_tool_list(
    specs,
) -> str:
    return "\n".join(
        spec.name
        for spec in specs
    )


def run_from_args(
    raw_args=None,
) -> str:
    parser = build_arg_parser()
    args = parser.parse_args(
        raw_args,
    )

    specs = list_mcp_tool_specs_for_mode(
        args.mode,
    )

    if args.mcp_json:
        return json.dumps(
            [
                mcp_tool_spec_to_mcp_tool(
                    spec,
                )
                for spec in specs
            ],
            indent=2,
        )

    if args.json:
        return json.dumps(
            [
                mcp_tool_spec_to_dict(
                    spec,
                )
                for spec in specs
            ],
            indent=2,
        )

    return format_tool_list(
        specs,
    )


def main() -> None:
    print(
        run_from_args()
    )


if __name__ == "__main__":
    main()

    