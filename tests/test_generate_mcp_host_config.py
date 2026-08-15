import json

from generate_mcp_host_config import run_from_args


def test_run_from_args_generates_cursor_json():
    output = run_from_args(
        [
            "--host",
            "cursor",
            "--server-name",
            "agentloop",
            "--python-executable",
            "python",
        ]
    )

    payload = json.loads(
        output,
    )

    assert "mcpServers" in payload
    assert payload["mcpServers"]["agentloop"]["command"] == "python"


def test_run_from_args_generates_claude_code_command():
    output = run_from_args(
        [
            "--host",
            "claude-code",
            "--server-name",
            "agentloop",
            "--python-executable",
            "python",
        ]
    )

    assert output.startswith(
        "claude mcp add agentloop -- python "
    )


def test_run_from_args_writes_output_file(tmp_path):
    output_path = tmp_path / "mcp.json"

    output = run_from_args(
        [
            "--host",
            "cursor",
            "--server-name",
            "agentloop",
            "--python-executable",
            "python",
            "--output",
            str(
                output_path,
            ),
        ]
    )

    assert output_path.exists()
    assert output_path.read_text(
        encoding="utf-8",
    ) == output