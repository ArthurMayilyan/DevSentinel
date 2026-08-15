import agent_loop_mcp_server


def test_agent_loop_mcp_server_module_import_does_not_start_server():
    assert hasattr(
        agent_loop_mcp_server,
        "create_agent_loop_mcp_server",
    )


def test_import_mcp_server_class_has_clear_error_when_sdk_missing(monkeypatch):
    original_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "mcp.server":
            raise ImportError("missing mcp")

        return original_import(
            name,
            *args,
            **kwargs,
        )

    monkeypatch.setattr(
        "builtins.__import__",
        fake_import,
    )

    try:
        agent_loop_mcp_server.import_mcp_server_class()
    except RuntimeError as exc:
        assert "MCP SDK is not installed" in str(
            exc,
        )

        