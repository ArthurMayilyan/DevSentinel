import json
from pathlib import Path

import web_ui


def test_run_review_request_routes_workspace(
    monkeypatch,
):
    captured = {}

    def fake_review_workspace(
        **kwargs,
    ):
        captured.update(
            kwargs,
        )

        return {
            "status": "completed",
        }

    monkeypatch.setattr(
        web_ui,
        "mcp_review_workspace",
        fake_review_workspace,
    )

    context = object()

    result = (
        web_ui.run_review_request(
            context=context,
            payload={
                "mode": "workspace",
                "project_path": (
                    "D:\\Projects\\Demo"
                ),
                "preset": (
                    "python-security"
                ),
                "reviewer": (
                    "deterministic"
                ),
                "model": "test-model",
            },
        )
    )

    assert result == {
        "status": "completed",
    }

    assert (
        captured["context"]
        is context
    )

    assert captured[
        "workspace_path"
    ] == "D:\\Projects\\Demo"

    assert captured[
        "preset"
    ] == "python-security"

    assert captured[
        "reviewer"
    ] == "deterministic"


def test_run_review_request_routes_staged_git_review(
    monkeypatch,
):
    captured = {}

    def fake_review_git_diff(
        **kwargs,
    ):
        captured.update(
            kwargs,
        )

        return {
            "status": "completed",
        }

    monkeypatch.setattr(
        web_ui,
        "mcp_review_git_diff",
        fake_review_git_diff,
    )

    context = object()

    result = (
        web_ui.run_review_request(
            context=context,
            payload={
                "mode": "staged",
                "project_path": (
                    "D:\\Projects\\Demo"
                ),
                "preset": (
                    "python-security"
                ),
                "reviewer": (
                    "deterministic"
                ),
                "model": "test-model",
            },
        )
    )

    assert result == {
        "status": "completed",
    }

    assert (
        captured["context"]
        is context
    )

    assert captured[
        "repository_path"
    ] == "D:\\Projects\\Demo"

    assert (
        captured[
            "staged_only"
        ]
        is True
    )

    assert captured[
        "base_ref"
    ] == "main"

    assert captured[
        "target_ref"
    ] == "HEAD"


def test_run_review_request_routes_git_refs(
    monkeypatch,
):
    captured = {}

    def fake_review_git_diff(
        **kwargs,
    ):
        captured.update(
            kwargs,
        )

        return {
            "status": "completed",
        }

    monkeypatch.setattr(
        web_ui,
        "mcp_review_git_diff",
        fake_review_git_diff,
    )

    web_ui.run_review_request(
        context=object(),
        payload={
            "mode": "git",
            "project_path": (
                "D:\\Projects\\Demo"
            ),
            "base_ref": "main",
            "target_ref": "dev",
            "preset": (
                "python-security"
            ),
            "reviewer": (
                "deterministic"
            ),
        },
    )

    assert (
        captured[
            "staged_only"
        ]
        is False
    )

    assert captured[
        "base_ref"
    ] == "main"

    assert captured[
        "target_ref"
    ] == "dev"


def test_load_recent_reviews_reads_existing_runs(
    tmp_path,
):
    project_path = (
        tmp_path
        / "project"
    )

    reviews_dir = (
        project_path
        / "reviews"
    )

    run_dir = (
        reviews_dir
        / "20260818_120000_demo_security_deterministic"
    )

    run_dir.mkdir(
        parents=True,
    )

    (
        run_dir
        / "summary.json"
    ).write_text(
        json.dumps(
            {
                "summary": (
                    "Review completed."
                ),
                "findings_count": 2,
            }
        ),
        encoding="utf-8",
    )

    (
        run_dir
        / "run_config.json"
    ).write_text(
        json.dumps(
            {
                "workflow": (
                    "git_diff"
                ),
                "reviewer": (
                    "deterministic"
                ),
            }
        ),
        encoding="utf-8",
    )

    (
        run_dir
        / "report.html"
    ).write_text(
        "<html></html>",
        encoding="utf-8",
    )

    history = (
        web_ui.load_recent_reviews(
            project_path=str(
                project_path,
            ),
        )
    )

    assert len(
        history,
    ) == 1

    assert history[0][
        "run_id"
    ] == run_dir.name

    assert history[0][
        "workflow"
    ] == "git_diff"

    assert history[0][
        "reviewer"
    ] == "deterministic"

    assert history[0][
        "findings_count"
    ] == 2

    assert history[0][
        "summary"
    ] == "Review completed."

    assert Path(
        history[0][
            "_report_html_path"
        ],
    ).exists()


def test_load_recent_reviews_falls_back_to_findings_file(
    tmp_path,
):
    project_path = (
        tmp_path
        / "project"
    )

    run_dir = (
        project_path
        / "reviews"
        / "20260818_run"
    )

    run_dir.mkdir(
        parents=True,
    )

    (
        run_dir
        / "summary.json"
    ).write_text(
        json.dumps(
            {
                "summary": (
                    "Review completed."
                )
            }
        ),
        encoding="utf-8",
    )

    (
        run_dir
        / "findings.json"
    ).write_text(
        json.dumps(
            [
                {
                    "issue": "one",
                },
                {
                    "issue": "two",
                },
                {
                    "issue": "three",
                },
            ]
        ),
        encoding="utf-8",
    )

    history = (
        web_ui.load_recent_reviews(
            project_path=str(
                project_path,
            ),
        )
    )

    assert history[0][
        "findings_count"
    ] == 3