import os
import pathlib
from pathlib import Path

import pytest

from devsentinel.core.tool_path_utils import (
    PATH_REJECTION_FILE_TOO_LARGE,
    PATH_REJECTION_NOT_REGULAR_FILE,
    PATH_REJECTION_OUTSIDE_PROJECT_ROOT,
    PATH_REJECTION_PROJECT_ROOT_NOT_CONFIGURED,
    ToolPathRejectedError,
    build_project_scope,
    resolve_within_root,
)
from devsentinel.core.tools import (
    list_files,
    read_file,
    search_in_files,
)


CANARY_TOKEN = "CANARY-tool-path-confinement-7f3a9c"

windows_only = pytest.mark.skipif(
    os.name != "nt",
    reason="Windows path semantics",
)


@pytest.fixture
def layout(tmp_path):
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    (project / "src" / "app.py").write_text(
        "DEBUG = True\n",
        encoding="utf-8",
    )

    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    (outside_dir / "secrets.py").write_text(
        f"TOKEN = '{CANARY_TOKEN}'\n",
        encoding="utf-8",
    )

    canary = tmp_path / "canary.txt"
    canary.write_text(
        CANARY_TOKEN,
        encoding="utf-8",
    )

    return {
        "project": project,
        "outside_dir": outside_dir,
        "canary": canary,
        "scope": build_project_scope(root=project),
    }


def assert_outside_root(
    *,
    scope,
    requested: str,
) -> ToolPathRejectedError:
    with pytest.raises(ToolPathRejectedError) as error_info:
        read_file(
            requested,
            scope=scope,
        )

    error = error_info.value

    assert error.code == PATH_REJECTION_OUTSIDE_PROJECT_ROOT
    assert CANARY_TOKEN not in str(error)

    return error


def create_directory_link_or_skip(
    *,
    link: Path,
    target: Path,
) -> None:
    try:
        link.symlink_to(
            target,
            target_is_directory=True,
        )
    except (OSError, NotImplementedError):
        pytest.skip("Creating directory symlinks is not permitted here")


def create_junction_or_skip(
    *,
    link: Path,
    target: Path,
) -> None:
    if os.name != "nt":
        pytest.skip("Junctions are Windows-only")

    import _winapi

    try:
        _winapi.CreateJunction(
            str(target),
            str(link),
        )
    except OSError:
        pytest.skip("Creating junctions is not permitted here")


# ---------------------------------------------------------------------------
# resolve_within_root / read_file
# ---------------------------------------------------------------------------


def test_relative_path_inside_root_is_allowed(layout):
    assert read_file("src/app.py", scope=layout["scope"]) == "DEBUG = True\n"


def test_backslash_relative_path_inside_root_is_allowed(layout):
    assert read_file("src\\app.py", scope=layout["scope"]) == "DEBUG = True\n"


def test_absolute_path_inside_root_is_allowed(layout):
    absolute = str(layout["project"] / "src" / "app.py")

    assert read_file(absolute, scope=layout["scope"]) == "DEBUG = True\n"


def test_parent_traversal_is_rejected(layout):
    error = assert_outside_root(
        scope=layout["scope"],
        requested="../canary.txt",
    )

    assert error.requested_path == "../canary.txt"
    assert "'..'" in error.detail


def test_backslash_parent_traversal_is_rejected(layout):
    assert_outside_root(
        scope=layout["scope"],
        requested="..\\canary.txt",
    )


def test_nested_parent_traversal_is_rejected(layout):
    assert_outside_root(
        scope=layout["scope"],
        requested="src/../../canary.txt",
    )


def test_parent_segment_that_stays_inside_root_is_still_rejected(layout):
    # Policy: any '..' segment is refused, even if it would resolve inside.
    assert_outside_root(
        scope=layout["scope"],
        requested="src/../src/app.py",
    )


def test_absolute_path_outside_root_is_rejected(layout):
    assert_outside_root(
        scope=layout["scope"],
        requested=str(layout["canary"]),
    )


def test_root_prefix_sibling_is_rejected(tmp_path):
    # "project_evil" shares a string prefix with "project" but is outside it.
    project = tmp_path / "project"
    project.mkdir()
    sibling = tmp_path / "project_evil"
    sibling.mkdir()
    (sibling / "x.py").write_text(CANARY_TOKEN, encoding="utf-8")

    assert_outside_root(
        scope=build_project_scope(root=project),
        requested=str(sibling / "x.py"),
    )


@pytest.mark.parametrize(
    "requested",
    [
        "",
        "   ",
        "src/app.py\x00.txt",
    ],
)
def test_empty_and_nul_paths_are_rejected(layout, requested):
    assert_outside_root(
        scope=layout["scope"],
        requested=requested,
    )


def test_non_string_path_is_rejected(layout):
    with pytest.raises(ToolPathRejectedError) as error_info:
        resolve_within_root(
            root=layout["scope"].root,
            requested=123,  # type: ignore[arg-type]
        )

    assert error_info.value.code == PATH_REJECTION_OUTSIDE_PROJECT_ROOT


@pytest.mark.parametrize(
    "requested",
    [
        "\\\\attacker-host\\share\\canary.txt",
        "//attacker-host/share/canary.txt",
        "\\\\?\\C:\\Windows\\win.ini",
        "\\\\.\\pipe\\devsentinel",
        "\\\\?\\UNC\\attacker-host\\share\\x",
    ],
)
def test_unc_and_device_paths_are_rejected_before_filesystem_access(
    layout,
    monkeypatch,
    requested,
):
    def fail_resolve(self, strict=False):
        raise AssertionError(f"resolve() must not be called for {self}")

    monkeypatch.setattr(pathlib.Path, "resolve", fail_resolve)

    with pytest.raises(ToolPathRejectedError) as error_info:
        resolve_within_root(
            root=layout["scope"].root,
            requested=requested,
        )

    assert error_info.value.code == PATH_REJECTION_OUTSIDE_PROJECT_ROOT
    assert "UNC" in error_info.value.detail


def test_drive_relative_path_is_rejected(layout):
    drive = layout["scope"].root.drive or "C:"

    assert_outside_root(
        scope=layout["scope"],
        requested=f"{drive}canary.txt",
    )


@windows_only
def test_other_drive_is_rejected_before_filesystem_access(layout, monkeypatch):
    root_drive = layout["scope"].root.drive.upper()
    other_drive = "Z:" if root_drive != "Z:" else "Y:"

    def fail_resolve(self, strict=False):
        raise AssertionError("resolve() must not be called for another drive")

    monkeypatch.setattr(pathlib.Path, "resolve", fail_resolve)

    with pytest.raises(ToolPathRejectedError) as error_info:
        resolve_within_root(
            root=layout["scope"].root,
            requested=f"{other_drive}\\canary.txt",
        )

    assert error_info.value.code == PATH_REJECTION_OUTSIDE_PROJECT_ROOT
    assert "another drive" in error_info.value.detail


@pytest.mark.skipif(os.name == "nt", reason="POSIX-only behaviour")
def test_windows_drive_path_is_rejected_on_posix(layout):
    assert_outside_root(
        scope=layout["scope"],
        requested="C:\\Users\\canary.txt",
    )


def test_rooted_path_without_drive_is_rejected(layout):
    # On Windows "/canary.txt" means the root of the current drive.
    assert_outside_root(
        scope=layout["scope"],
        requested="/canary.txt",
    )


@windows_only
def test_case_variant_relative_path_is_allowed_on_windows(layout):
    assert read_file("SRC\\APP.PY", scope=layout["scope"]) == "DEBUG = True\n"


@windows_only
def test_case_variant_absolute_root_is_allowed_on_windows(layout):
    upper = str(layout["project"]).upper() + "\\SRC\\APP.PY"

    assert read_file(upper, scope=layout["scope"]) == "DEBUG = True\n"


@windows_only
def test_case_variant_outside_root_is_rejected_on_windows(layout):
    assert_outside_root(
        scope=layout["scope"],
        requested=str(layout["canary"]).upper(),
    )


def test_file_symlink_pointing_outside_root_is_rejected(layout):
    link = layout["project"] / "linked.txt"

    try:
        link.symlink_to(layout["canary"])
    except (OSError, NotImplementedError):
        pytest.skip("Creating file symlinks is not permitted here")

    assert_outside_root(
        scope=layout["scope"],
        requested="linked.txt",
    )


def test_file_symlink_inside_root_is_allowed(layout):
    link = layout["project"] / "alias.py"

    try:
        link.symlink_to(layout["project"] / "src" / "app.py")
    except (OSError, NotImplementedError):
        pytest.skip("Creating file symlinks is not permitted here")

    assert read_file("alias.py", scope=layout["scope"]) == "DEBUG = True\n"


def test_directory_symlink_pointing_outside_root_is_rejected(layout):
    create_directory_link_or_skip(
        link=layout["project"] / "escape",
        target=layout["outside_dir"],
    )

    assert_outside_root(
        scope=layout["scope"],
        requested="escape/secrets.py",
    )


def test_junction_pointing_outside_root_is_rejected(layout):
    create_junction_or_skip(
        link=layout["project"] / "escape",
        target=layout["outside_dir"],
    )

    assert_outside_root(
        scope=layout["scope"],
        requested="escape\\secrets.py",
    )


def test_junction_inside_root_is_allowed_for_read(layout):
    create_junction_or_skip(
        link=layout["project"] / "src_alias",
        target=layout["project"] / "src",
    )

    assert read_file("src_alias\\app.py", scope=layout["scope"]) == "DEBUG = True\n"


def test_oversized_file_is_rejected(layout):
    scope = build_project_scope(
        root=layout["project"],
        max_file_size_bytes=4,
    )

    with pytest.raises(ToolPathRejectedError) as error_info:
        read_file("src/app.py", scope=scope)

    assert error_info.value.code == PATH_REJECTION_FILE_TOO_LARGE


def test_directory_is_not_a_regular_file(layout):
    with pytest.raises(ToolPathRejectedError) as error_info:
        read_file("src", scope=layout["scope"])

    assert error_info.value.code == PATH_REJECTION_NOT_REGULAR_FILE


def test_missing_file_inside_root_is_not_found(layout):
    with pytest.raises(FileNotFoundError):
        read_file("src/missing.py", scope=layout["scope"])


def test_missing_scope_rejects_instead_of_using_working_directory(layout):
    for call in (
        lambda: read_file("src/app.py", scope=None),
        lambda: list_files(".", scope=None),
        lambda: search_in_files("DEBUG", ".", scope=None),
    ):
        with pytest.raises(ToolPathRejectedError) as error_info:
            call()

        assert error_info.value.code == PATH_REJECTION_PROJECT_ROOT_NOT_CONFIGURED


def test_relative_paths_use_explicit_base_dir_but_root_still_applies(tmp_path):
    workspace = tmp_path / "workspace"
    project = workspace / "project"
    project.mkdir(parents=True)
    (project / "app.py").write_text("A = 1\n", encoding="utf-8")
    (workspace / ".env").write_text(CANARY_TOKEN, encoding="utf-8")

    scope = build_project_scope(
        root=project,
        base_dir=workspace,
    )

    assert read_file("project/app.py", scope=scope) == "A = 1\n"

    assert_outside_root(
        scope=scope,
        requested=".env",
    )


def test_rejection_message_is_truncated_for_long_paths(layout):
    long_request = "../" + "a" * 1000

    error = assert_outside_root(
        scope=layout["scope"],
        requested=long_request,
    )

    assert len(error.requested_path) < 400
    assert error.requested_path.endswith("...[truncated]")


# ---------------------------------------------------------------------------
# build_project_scope
# ---------------------------------------------------------------------------


def test_build_project_scope_requires_existing_directory(tmp_path):
    with pytest.raises(ValueError):
        build_project_scope(root=tmp_path / "missing")

    file_path = tmp_path / "file.py"
    file_path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError):
        build_project_scope(root=file_path)

    with pytest.raises(ValueError):
        build_project_scope(root="")


def test_build_project_scope_rejects_invalid_size_limit(tmp_path):
    with pytest.raises(ValueError):
        build_project_scope(root=tmp_path, max_file_size_bytes=0)


# ---------------------------------------------------------------------------
# list_files / search_in_files
# ---------------------------------------------------------------------------


def test_list_files_returns_paths_relative_to_base_dir(layout):
    assert list_files(".", scope=layout["scope"]) == [
        str(Path("src") / "app.py"),
    ]


def test_list_files_returns_absolute_paths_for_absolute_request(layout):
    files = list_files(str(layout["project"]), scope=layout["scope"])

    assert files == [
        str(layout["project"] / "src" / "app.py"),
    ]


def test_list_files_rejects_directory_outside_root(layout):
    for requested in ("..", str(layout["outside_dir"])):
        with pytest.raises(ToolPathRejectedError) as error_info:
            list_files(requested, scope=layout["scope"])

        assert error_info.value.code == PATH_REJECTION_OUTSIDE_PROJECT_ROOT


def test_search_rejects_directory_outside_root(layout):
    with pytest.raises(ToolPathRejectedError) as error_info:
        search_in_files(CANARY_TOKEN, "..", scope=layout["scope"])

    assert error_info.value.code == PATH_REJECTION_OUTSIDE_PROJECT_ROOT


def test_list_and_search_do_not_follow_junction_out_of_root(layout):
    create_junction_or_skip(
        link=layout["project"] / "escape",
        target=layout["outside_dir"],
    )

    files = list_files(".", scope=layout["scope"])
    matches = search_in_files(CANARY_TOKEN, ".", scope=layout["scope"])

    assert files == [str(Path("src") / "app.py")]
    assert matches == []


def test_list_and_search_do_not_follow_directory_symlink_out_of_root(layout):
    create_directory_link_or_skip(
        link=layout["project"] / "escape",
        target=layout["outside_dir"],
    )

    assert list_files(".", scope=layout["scope"]) == [str(Path("src") / "app.py")]
    assert search_in_files(CANARY_TOKEN, ".", scope=layout["scope"]) == []


def test_list_and_search_skip_file_symlink_out_of_root(layout):
    link = layout["project"] / "linked.txt"

    try:
        link.symlink_to(layout["canary"])
    except (OSError, NotImplementedError):
        pytest.skip("Creating file symlinks is not permitted here")

    assert list_files(".", scope=layout["scope"]) == [str(Path("src") / "app.py")]
    assert search_in_files(CANARY_TOKEN, ".", scope=layout["scope"]) == []


def test_list_files_does_not_loop_on_junction_to_ancestor(layout):
    create_junction_or_skip(
        link=layout["project"] / "src" / "loop",
        target=layout["project"],
    )

    assert list_files(".", scope=layout["scope"]) == [str(Path("src") / "app.py")]


def test_search_skips_files_over_size_limit(layout):
    (layout["project"] / "big.py").write_text(
        "DEBUG = True\n" * 10,
        encoding="utf-8",
    )

    scope = build_project_scope(
        root=layout["project"],
        max_file_size_bytes=20,
    )

    matches = search_in_files("DEBUG", ".", scope=scope)

    assert [match["file"] for match in matches] == [str(Path("src") / "app.py")]


def test_search_returns_relative_paths_inside_root(layout):
    assert search_in_files("DEBUG", ".", scope=layout["scope"]) == [
        {
            "file": str(Path("src") / "app.py"),
            "line": 1,
            "text": "DEBUG = True",
        }
    ]
