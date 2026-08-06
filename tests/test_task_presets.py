import pytest

from task_presets import (
    DEFAULT_CODE_REVIEW_MAX_FINDINGS,
    SUPPORTED_TASK_PRESETS,
    build_code_review_task,
    build_task_from_preset,
)


def test_supported_task_presets_contains_code_review():
    assert "code-review" in SUPPORTED_TASK_PRESETS


def test_build_code_review_task_contains_path_and_workflow():
    task = build_code_review_task(path="./sample_project")

    assert "Review ./sample_project only." in task
    assert "Start with list_files path ./sample_project." in task
    assert "Read all Python files." in task
    assert (
        f"Add no more than {DEFAULT_CODE_REVIEW_MAX_FINDINGS} most important findings."
        in task
    )
    assert "Then call write_report." in task
    assert "Then return final_answer." in task
    assert "Return exactly one JSON object per response." in task


def test_build_code_review_task_accepts_custom_max_findings():
    task = build_code_review_task(
        path="./sample_project",
        max_findings=5,
    )

    assert "Add no more than 5 most important findings." in task


def test_build_task_from_preset_builds_code_review_task():
    task = build_task_from_preset(
        preset="code-review",
        path="./sample_project",
        max_findings=2,
    )

    assert "Review ./sample_project only." in task
    assert "Add no more than 2 most important findings." in task


def test_build_task_from_preset_rejects_unknown_preset():
    with pytest.raises(ValueError):
        build_task_from_preset(
            preset="unknown",
            path="./sample_project",
        )


def test_build_code_review_task_rejects_empty_path():
    with pytest.raises(ValueError):
        build_code_review_task(path="")


def test_build_code_review_task_rejects_non_string_path():
    with pytest.raises(ValueError):
        build_code_review_task(path=None)


def test_build_code_review_task_rejects_zero_max_findings():
    with pytest.raises(ValueError):
        build_code_review_task(
            path="./sample_project",
            max_findings=0,
        )


def test_build_code_review_task_rejects_bool_max_findings():
    with pytest.raises(ValueError):
        build_code_review_task(
            path="./sample_project",
            max_findings=True,
        )

        