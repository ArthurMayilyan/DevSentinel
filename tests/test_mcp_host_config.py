import json

import pytest

from mcp_host_config import (
    build_agentloop_launch_command,
    build_mcp_host_config,
    mcp_host_config_to_json,
    quote_command_part,
)


def test_build_agentloop_launch_command_uses_absolute_server_path():
    command = build_agentloop_launch_command(
        server_script_path="run_mcp_server.py",
        python_executable="python",
    )

    assert command.command == "python"
    assert command.args[0].endswith(
        "run_mcp_server.py",
    )
    assert command.args[1:3] == [
        "--transport",
        "stdio",
    ]
    assert "--report-path" in command.args


def test_build_agentloop_launch_command_adds_knowledge_path():
    command = build_agentloop_launch_command(
        server_script_path="run_mcp_server.py",
        knowledge_path="./knowledge_base_noisy",
        python_executable="python",
    )

    assert "--knowledge-path" in command.args
    assert "./knowledge_base_noisy" not in command.args


def test_build_cursor_mcp_config():
    config = build_mcp_host_config(
        host="cursor",
        server_name="agentloop",
        server_script_path="run_mcp_server.py",
        python_executable="python",
    )

    assert config["mcpServers"]["agentloop"]["command"] == "python"
    assert "run_mcp_server.py" in config["mcpServers"]["agentloop"]["args"][0]


def test_build_claude_desktop_mcp_config_has_stdio_type():
    config = build_mcp_host_config(
        host="claude-desktop",
        server_name="agentloop",
        server_script_path="run_mcp_server.py",
        python_executable="python",
    )

    server = config["mcpServers"]["agentloop"]

    assert server["type"] == "stdio"
    assert server["command"] == "python"


def test_build_vscode_mcp_config_uses_servers_key():
    config = build_mcp_host_config(
        host="vscode",
        server_name="agentloop",
        server_script_path="run_mcp_server.py",
        python_executable="python",
    )

    assert "servers" in config
    assert config["servers"]["agentloop"]["type"] == "stdio"


def test_build_claude_code_mcp_command():
    command = build_mcp_host_config(
        host="claude-code",
        server_name="agentloop",
        server_script_path="run_mcp_server.py",
        python_executable="python",
    )

    assert command.startswith(
        "claude mcp add agentloop -- python "
    )
    assert "run_mcp_server.py" in command


def test_build_mcp_host_config_rejects_unknown_host():
    with pytest.raises(ValueError):
        build_mcp_host_config(
            host="unknown",
        )


def test_mcp_host_config_to_json_serializes_config():
    config = build_mcp_host_config(
        host="cursor",
        server_name="agentloop",
        server_script_path="run_mcp_server.py",
        python_executable="python",
    )

    payload = json.loads(
        mcp_host_config_to_json(
            config,
        )
    )

    assert "mcpServers" in payload


def test_quote_command_part_quotes_values_with_spaces():
    assert quote_command_part(
        "C:/Program Files/Python/python.exe",
    ) == '"C:/Program Files/Python/python.exe"'