import pytest

from workspace_review_presets import (
    WORKSPACE_PRESET_GENERAL_SECURITY,
    WORKSPACE_PRESET_PYTHON_SECURITY,
    WORKSPACE_PRESET_TYPESCRIPT_SECURITY,
    default_workspace_reviews_dir,
    get_workspace_review_preset,
)


def test_python_security_preset():
    preset = get_workspace_review_preset(
        WORKSPACE_PRESET_PYTHON_SECURITY,
    )

    assert preset.profile == "security"
    assert preset.include_globs == "**/*.py"
    assert ".venv/**" in preset.exclude_globs
    assert preset.max_files == 200


def test_typescript_security_preset():
    preset = get_workspace_review_preset(
        WORKSPACE_PRESET_TYPESCRIPT_SECURITY,
    )

    assert preset.profile == "security"
    assert "**/*.ts" in preset.include_globs
    assert "node_modules/**" in preset.exclude_globs


def test_general_security_preset():
    preset = get_workspace_review_preset(
        WORKSPACE_PRESET_GENERAL_SECURITY,
    )

    assert preset.profile == "security"
    assert preset.include_globs == ""


def test_unknown_preset_is_rejected():
    with pytest.raises(ValueError):
        get_workspace_review_preset(
            "unknown",
        )


def test_default_workspace_reviews_dir(tmp_path):
    result = default_workspace_reviews_dir(
        str(
            tmp_path,
        )
    )

    assert result.endswith(
        "reviews"
    )