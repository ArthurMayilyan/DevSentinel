import pytest

from tool_path_utils import normalize_tool_path


def test_normalize_tool_path_keeps_posix_path():
    assert (
        normalize_tool_path(
            "sample_project/auth.py"
        )
        == "sample_project/auth.py"
    )


def test_normalize_tool_path_converts_windows_path():
    assert (
        normalize_tool_path(
            "sample_project\\auth.py"
        )
        == "sample_project/auth.py"
    )


def test_normalize_tool_path_rejects_empty_path():
    with pytest.raises(ValueError):
        normalize_tool_path(
            "",
        )


def test_normalize_tool_path_rejects_non_string_path():
    with pytest.raises(ValueError):
        normalize_tool_path(
            123,  # type: ignore[arg-type]
        )