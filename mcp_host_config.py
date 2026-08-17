import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app_settings import get_app_settings


_SETTINGS = get_app_settings()

DEFAULT_MCP_HOST_REPORT_PATH = (
    _SETTINGS.artifacts.default_report_path
)

SUPPORTED_MCP_HOSTS = {
    "cursor",
    "claude-desktop",
    "claude-code",
    "vscode",
}


@dataclass(frozen=True)
class McpHostLaunchCommand:
    command: str
    args: list[str]
    env: dict[str, str]


def resolve_path(
    path: str,
) -> str:
    return str(
        Path(
            path,
        )
        .expanduser()
        .resolve()
    )


def build_agentloop_launch_command(
    *,
    server_script_path: str = "run_mcp_server.py",
    knowledge_path: str = "",
    index_path: str = "",
    report_path: str = DEFAULT_MCP_HOST_REPORT_PATH,
    python_executable: str = "",
) -> McpHostLaunchCommand:
    command = python_executable or sys.executable

    args = [
        resolve_path(
            server_script_path,
        ),
        "--transport",
        "stdio",
    ]

    if knowledge_path:
        args.extend(
            [
                "--knowledge-path",
                resolve_path(
                    knowledge_path,
                ),
            ]
        )

    if index_path:
        args.extend(
            [
                "--index-path",
                resolve_path(
                    index_path,
                ),
            ]
        )

    if report_path:
        args.extend(
            [
                "--report-path",
                resolve_path(
                    report_path,
                ),
            ]
        )

    return McpHostLaunchCommand(
        command=command,
        args=args,
        env={},
    )


def build_cursor_mcp_config(
    *,
    server_name: str,
    launch_command: McpHostLaunchCommand,
) -> dict[str, Any]:
    return {
        "mcpServers": {
            server_name: {
                "command": launch_command.command,
                "args": launch_command.args,
                "env": launch_command.env,
            }
        }
    }


def build_claude_desktop_mcp_config(
    *,
    server_name: str,
    launch_command: McpHostLaunchCommand,
) -> dict[str, Any]:
    return {
        "mcpServers": {
            server_name: {
                "type": "stdio",
                "command": launch_command.command,
                "args": launch_command.args,
                "env": launch_command.env,
            }
        }
    }


def build_vscode_mcp_config(
    *,
    server_name: str,
    launch_command: McpHostLaunchCommand,
) -> dict[str, Any]:
    return {
        "servers": {
            server_name: {
                "type": "stdio",
                "command": launch_command.command,
                "args": launch_command.args,
                "env": launch_command.env,
            }
        }
    }


def build_claude_code_mcp_command(
    *,
    server_name: str,
    launch_command: McpHostLaunchCommand,
) -> str:
    parts = [
        "claude",
        "mcp",
        "add",
        server_name,
        "--",
        launch_command.command,
        *launch_command.args,
    ]

    return " ".join(
        quote_command_part(
            part,
        )
        for part in parts
    )


def quote_command_part(
    value: str,
) -> str:
    if not value:
        return '""'

    if any(
        char.isspace()
        for char in value
    ):
        escaped = value.replace(
            '"',
            '\\"',
        )

        return f'"{escaped}"'

    return value


def build_mcp_host_config(
    *,
    host: str,
    server_name: str = "agentloop",
    server_script_path: str = "run_mcp_server.py",
    knowledge_path: str = "",
    index_path: str = "",
    report_path: str = DEFAULT_MCP_HOST_REPORT_PATH,
    python_executable: str = "",
) -> dict[str, Any] | str:
    if host not in SUPPORTED_MCP_HOSTS:
        supported = ", ".join(
            sorted(
                SUPPORTED_MCP_HOSTS,
            )
        )

        raise ValueError(
            f"unsupported MCP host: {host}. Supported hosts: {supported}"
        )

    launch_command = build_agentloop_launch_command(
        server_script_path=server_script_path,
        knowledge_path=knowledge_path,
        index_path=index_path,
        report_path=report_path,
        python_executable=python_executable,
    )

    if host == "cursor":
        return build_cursor_mcp_config(
            server_name=server_name,
            launch_command=launch_command,
        )

    if host == "claude-desktop":
        return build_claude_desktop_mcp_config(
            server_name=server_name,
            launch_command=launch_command,
        )

    if host == "vscode":
        return build_vscode_mcp_config(
            server_name=server_name,
            launch_command=launch_command,
        )

    if host == "claude-code":
        return build_claude_code_mcp_command(
            server_name=server_name,
            launch_command=launch_command,
        )

    raise ValueError(
        f"unsupported MCP host: {host}"
    )


def mcp_host_config_to_json(
    config: dict[str, Any],
) -> str:
    return json.dumps(
        config,
        indent=2,
    )

