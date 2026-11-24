from pathlib import Path

import pytest

from devsentinel.cli.cli_project_scope import build_cli_project_scope
from devsentinel.cli.run_agent import run_agent_from_args


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_explicit_project_root_wins(tmp_path):
    project = tmp_path / "project"
    other = tmp_path / "other"
    project.mkdir()
    other.mkdir()

    scope = build_cli_project_scope(
        project_root="project",
        path="other",
        launch_dir=tmp_path,
    )

    assert scope.root == project.resolve()
    assert scope.base_dir == tmp_path.resolve()


def test_path_is_used_when_project_root_is_missing(tmp_path):
    (tmp_path / "project").mkdir()

    scope = build_cli_project_scope(
        project_root=None,
        path="./project",
        launch_dir=tmp_path,
    )

    assert scope.root == (tmp_path / "project").resolve()


def test_launch_directory_is_the_explicit_last_resort(tmp_path):
    scope = build_cli_project_scope(
        project_root=None,
        path=None,
        launch_dir=tmp_path,
    )

    assert scope.root == tmp_path.resolve()


def test_missing_project_root_is_an_error(tmp_path):
    with pytest.raises(ValueError):
        build_cli_project_scope(
            project_root="missing",
            path=None,
            launch_dir=tmp_path,
        )


def test_run_agent_records_project_root_in_metadata(monkeypatch):
    monkeypatch.chdir(REPOSITORY_ROOT)

    output = run_agent_from_args([
        "--preset",
        "code-review",
        "--path",
        "./sample_project",
        "--llm",
        "demo",
    ])

    assert output["status"] == "completed"
    assert output["run"]["project_root"] == str(
        (REPOSITORY_ROOT / "sample_project").resolve()
    )
