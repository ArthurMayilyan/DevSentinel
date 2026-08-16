import pytest

from project_path_safety import (
    resolve_project_path,
    select_project_files,
)


def test_resolve_project_path_rejects_missing_path(tmp_path):
    with pytest.raises(ValueError):
        resolve_project_path(
            str(
                tmp_path / "missing",
            )
        )


def test_resolve_project_path_rejects_file_path(tmp_path):
    file_path = tmp_path / "app.py"
    file_path.write_text(
        "print('hello')",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        resolve_project_path(
            str(
                file_path,
            )
        )


def test_select_project_files_includes_supported_files_and_skips_ignored_dirs(tmp_path):
    project_path = tmp_path / "project"
    project_path.mkdir()

    app_path = project_path / "app.py"
    app_path.write_text(
        "print('hello')",
        encoding="utf-8",
    )

    ignored_dir = project_path / "__pycache__"
    ignored_dir.mkdir()

    ignored_file = ignored_dir / "app.py"
    ignored_file.write_text(
        "ignored",
        encoding="utf-8",
    )

    result = select_project_files(
        project_path=str(
            project_path,
        )
    )

    assert result.files == [
        str(
            app_path.resolve(),
        )
    ]

    assert str(
        ignored_file.resolve(),
    ) in result.skipped_files



def test_select_project_files_include_glob_matches_root_level_files(tmp_path):
    project_path = tmp_path / "project"
    project_path.mkdir()

    app_path = project_path / "app.py"
    app_path.write_text(
        "print('hello')",
        encoding="utf-8",
    )

    result = select_project_files(
        project_path=str(
            project_path,
        ),
        include_globs="**/*.py",
    )

    assert result.files == [
        str(
            app_path.resolve(),
        )
    ]    