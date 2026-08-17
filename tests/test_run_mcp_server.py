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
        "- search_knowledge",
        "- add_finding",
        "- write_report",
        "- review_project",
        "- review_workspace",
        "- compare_review_runs",
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


def test_run_from_args_server_mode_is_silent(monkeypatch):
    class FakeMcpServer:
        def run(self, *args):
            return None

    monkeypatch.setattr(
        "run_mcp_server.create_agent_loop_mcp_server",
        lambda context: FakeMcpServer(),
    )

    output = run_from_args(
        [
            "--transport",
            "stdio",
        ]
    )

    assert output == ""

def test_run_from_args_streamable_http_mode_is_silent(monkeypatch):
    class FakeMcpServer:
        def __init__(self):
            self.args = None

        def run(self, *args):
            self.args = args
            return None

    fake_server = FakeMcpServer()

    monkeypatch.setattr(
        "run_mcp_server.create_agent_loop_mcp_server",
        lambda context: fake_server,
    )

    output = run_from_args(
        [
            "--transport",
            "streamable-http",
        ]
    )

    assert output == ""
    assert fake_server.args == (
        "streamable-http",
    )

        