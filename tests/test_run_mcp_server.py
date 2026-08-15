import pytest

from run_mcp_server import (
    build_arg_parser,
    format_server_description,
    run_from_args,
)


def test_build_arg_parser_accepts_describe():
    parser = build_arg_parser()

    args = parser.parse_args(
        [
            "--describe",
        ]
    )

    assert args.describe is True
    assert args.transport == "stdio"


def test_format_server_description_lists_tools():
    output = format_server_description()

    assert output.splitlines() == [
        "AgentLoop MCP server",
        "",
        "Tools:",
        "- list_files",
        "- read_file",
        "- search_in_files",
        "- add_finding",
        "- write_report",
        "- search_knowledge",
    ]


def test_run_from_args_describe_does_not_start_server():
    output = run_from_args(
        [
            "--describe",
        ]
    )

    assert "AgentLoop MCP server" in output
    assert "- search_knowledge" in output


def test_build_arg_parser_rejects_unknown_transport():
    parser = build_arg_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "--transport",
                "unknown",
            ]
        )

        