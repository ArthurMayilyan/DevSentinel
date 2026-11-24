import asyncio
import os
from pathlib import Path
from uuid import uuid4

import pytest

from devsentinel.core.tool_path_utils import (
    PATH_REJECTION_OUTSIDE_PROJECT_ROOT,
    PATH_REJECTION_PROJECT_ROOT_NOT_CONFIGURED,
    ToolPathRejectedError,
)
from devsentinel.mcp.mcp_product_content import build_current_state_resource
from devsentinel.mcp.mcp_server_context import build_devsentinel_mcp_context
from devsentinel.mcp.mcp_server_handlers import (
    mcp_list_files,
    mcp_read_file,
    mcp_search_in_files,
)


@pytest.fixture
def sandbox(tmp_path):
    token = f"CANARY-{uuid4().hex}"
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.py").write_text("DEBUG = True\n", encoding="utf-8")

    canary = tmp_path / "canary.txt"
    canary.write_text(token, encoding="utf-8")

    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    (outside_dir / "leak.py").write_text(f"TOKEN = '{token}'\n", encoding="utf-8")

    context = build_devsentinel_mcp_context(
        project_root=str(project),
        report_path=str(tmp_path / "report.md"),
    )

    return {
        "token": token,
        "project": project,
        "canary": canary,
        "outside_dir": outside_dir,
        "context": context,
    }


def escape_paths(sandbox) -> list[str]:
    paths = [
        "../canary.txt",
        "..\\canary.txt",
        "nested/../../canary.txt",
        str(sandbox["canary"]),
        "\\\\attacker-host\\share\\canary.txt",
        "//attacker-host/share/canary.txt",
    ]

    if os.name == "nt":
        root_drive = sandbox["project"].drive.upper()
        other_drive = "Z:" if root_drive != "Z:" else "Y:"
        paths.extend([
            f"{other_drive}\\canary.txt",
            str(sandbox["canary"]).upper(),
        ])

    return paths


def test_mcp_read_file_rejects_escape_attempts(sandbox):
    context = sandbox["context"]

    for requested in escape_paths(sandbox):
        with pytest.raises(ToolPathRejectedError) as error_info:
            mcp_read_file(context=context, path=requested)

        assert error_info.value.code == PATH_REJECTION_OUTSIDE_PROJECT_ROOT
        assert sandbox["token"] not in str(error_info.value)

    assert context.state.inspected_files == []


def test_mcp_list_files_rejects_directories_outside_root(sandbox):
    context = sandbox["context"]

    for requested in ("..", str(sandbox["outside_dir"]), str(sandbox["project"].parent)):
        with pytest.raises(ToolPathRejectedError):
            mcp_list_files(context=context, path=requested)

    assert context.state.discovered_files == []


def test_mcp_search_rejects_directories_outside_root(sandbox):
    with pytest.raises(ToolPathRejectedError):
        mcp_search_in_files(
            context=sandbox["context"],
            path="..",
            query=sandbox["token"],
        )


def test_mcp_tools_work_inside_root(sandbox):
    context = sandbox["context"]

    assert mcp_list_files(context=context, path=".") == ["app.py"]
    assert mcp_read_file(context=context, path="app.py") == "DEBUG = True\n"
    assert mcp_search_in_files(context=context, path=".", query="DEBUG") == [
        {"file": "app.py", "line": 1, "text": "DEBUG = True"},
    ]


def test_mcp_list_and_search_do_not_follow_junction_out_of_root(sandbox):
    if os.name != "nt":
        pytest.skip("Junctions are Windows-only")

    import _winapi

    try:
        _winapi.CreateJunction(
            str(sandbox["outside_dir"]),
            str(sandbox["project"] / "escape"),
        )
    except OSError:
        pytest.skip("Creating junctions is not permitted here")

    context = sandbox["context"]

    assert mcp_list_files(context=context, path=".") == ["app.py"]
    assert mcp_search_in_files(context=context, path=".", query=sandbox["token"]) == []

    with pytest.raises(ToolPathRejectedError):
        mcp_read_file(context=context, path="escape\\leak.py")


def test_mcp_context_without_root_rejects_file_tools(tmp_path):
    (tmp_path / "app.py").write_text("A = 1\n", encoding="utf-8")
    context = build_devsentinel_mcp_context()

    with pytest.raises(ToolPathRejectedError) as error_info:
        mcp_read_file(context=context, path=str(tmp_path / "app.py"))

    assert error_info.value.code == PATH_REJECTION_PROJECT_ROOT_NOT_CONFIGURED
    assert "not configured" in build_current_state_resource(context)


def test_mcp_context_rejects_base_dir_without_root(tmp_path):
    with pytest.raises(ValueError):
        build_devsentinel_mcp_context(path_base_dir=str(tmp_path))


def test_current_state_resource_shows_project_root(sandbox):
    resource = build_current_state_resource(sandbox["context"])

    assert str(sandbox["project"].resolve()) in resource


def test_mcp_server_returns_tool_error_for_escape_without_leaking(sandbox):
    mcp_module = pytest.importorskip("mcp")
    from devsentinel.mcp.devsentinel_mcp_server import create_devsentinel_mcp_server

    server = create_devsentinel_mcp_server(context=sandbox["context"])

    async def call_escape():
        async with mcp_module.Client(server) as client:
            return await client.call_tool(
                "read_file",
                {"path": "../canary.txt"},
            )

    result = asyncio.run(call_escape())
    text = " ".join(
        getattr(item, "text", "")
        for item in result.content
    )

    assert result.is_error is True
    assert PATH_REJECTION_OUTSIDE_PROJECT_ROOT in text
    assert sandbox["token"] not in text


def test_run_mcp_server_defaults_root_to_launch_directory(monkeypatch, tmp_path, capsys):
    from devsentinel.cli import run_mcp_server

    captured = {}

    def fake_create_server(*, context):
        captured["context"] = context

        class FakeServer:
            def run(self, *args):
                return None

        return FakeServer()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(run_mcp_server, "create_devsentinel_mcp_server", fake_create_server)

    run_mcp_server.run_from_args(["--report-path", str(tmp_path / "r.md")])

    assert captured["context"].project_scope.root == Path(tmp_path).resolve()
    assert str(Path(tmp_path).resolve()) in capsys.readouterr().err


def test_run_mcp_server_accepts_explicit_project_root(monkeypatch, tmp_path):
    from devsentinel.cli import run_mcp_server

    project = tmp_path / "project"
    project.mkdir()
    captured = {}

    def fake_create_server(*, context):
        captured["context"] = context

        class FakeServer:
            def run(self, *args):
                return None

        return FakeServer()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(run_mcp_server, "create_devsentinel_mcp_server", fake_create_server)

    run_mcp_server.run_from_args([
        "--project-root",
        "project",
        "--report-path",
        str(tmp_path / "r.md"),
    ])

    scope = captured["context"].project_scope

    assert scope.root == project.resolve()
    assert scope.base_dir == Path(tmp_path).resolve()
