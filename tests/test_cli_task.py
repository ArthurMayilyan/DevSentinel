from argparse import Namespace

import pytest

from cli_task import build_task_from_args


def test_build_task_from_args_returns_explicit_task():
    args = Namespace(
        task="Review manually.",
        preset=None,
        path=None,
        max_findings=3,
    )

    assert build_task_from_args(args) == "Review manually."


def test_build_task_from_args_builds_task_from_code_review_preset():
    args = Namespace(
        task=None,
        preset="code-review",
        path="./sample_project",
        max_findings=3,
    )

    task = build_task_from_args(args)

    assert "Review ./sample_project only." in task
    assert "Start with list_files path ./sample_project." in task
    assert "Add up to 3 distinct findings." in task
    assert "Do not merge unrelated issues into one finding." in task
    assert (
        "Group issues only when they have the same root cause and the same recommended fix."
        in task
    )

def test_build_task_from_args_rejects_task_and_preset_together():
    args = Namespace(
        task="Review manually.",
        preset="code-review",
        path="./sample_project",
        max_findings=3,
    )

    with pytest.raises(ValueError):
        build_task_from_args(args)


def test_build_task_from_args_rejects_preset_without_path():
    args = Namespace(
        task=None,
        preset="code-review",
        path=None,
        max_findings=3,
    )

    with pytest.raises(ValueError):
        build_task_from_args(args)


def test_build_task_from_args_rejects_missing_task_and_preset():
    args = Namespace(
        task=None,
        preset=None,
        path=None,
        max_findings=3,
    )

    with pytest.raises(ValueError):
        build_task_from_args(args)


def test_build_task_from_args_passes_custom_max_findings():
    args = Namespace(
        task=None,
        preset="code-review",
        path="./sample_project",
        max_findings=5,
    )

    task = build_task_from_args(args)

    assert "Add up to 5 distinct findings." in task

