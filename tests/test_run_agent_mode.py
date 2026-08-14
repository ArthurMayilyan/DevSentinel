import json

import pytest

from run_agent_mode import run_from_args


def create_knowledge_fixture(tmp_path):
    knowledge_path = tmp_path / "knowledge_base"
    knowledge_path.mkdir()

    security = knowledge_path / "security.md"
    security.write_text(
        "# Security Policy\n\n"
        "Token expiration policy: tokens must be signed and must expire.\n"
        "Credentials must not be hardcoded in source code.",
        encoding="utf-8",
    )

    return knowledge_path


def test_run_from_args_lists_modes():
    output = run_from_args(
        [
            "--list-modes",
        ]
    )

    assert "Supported agent modes" in output
    assert "rag_qa" in output


def test_run_from_args_runs_rag_qa_mode(tmp_path):
    knowledge_path = create_knowledge_fixture(
        tmp_path,
    )

    output = run_from_args(
        [
            "--mode",
            "rag_qa",
            "--task",
            "token expiration",
            "--knowledge-path",
            str(
                knowledge_path,
            ),
            "--strategy",
            "binary-overlap",
            "--llm",
            "deterministic",
        ]
    )

    assert "Token expiration policy" in output
    assert "Source:" in output


def test_run_from_args_returns_json_output(tmp_path):
    knowledge_path = create_knowledge_fixture(
        tmp_path,
    )

    output = run_from_args(
        [
            "--mode",
            "rag_qa",
            "--task",
            "token expiration",
            "--knowledge-path",
            str(
                knowledge_path,
            ),
            "--strategy",
            "binary-overlap",
            "--llm",
            "deterministic",
            "--json",
        ]
    )

    payload = json.loads(
        output,
    )

    assert payload["mode"] == "rag_qa"
    assert payload["task"] == "token expiration"
    assert "Token expiration policy" in payload["answer"]


def test_run_from_args_writes_artifacts(tmp_path):
    knowledge_path = create_knowledge_fixture(
        tmp_path,
    )
    artifacts_dir = tmp_path / "artifacts"

    output = run_from_args(
        [
            "--mode",
            "rag_qa",
            "--task",
            "token expiration",
            "--knowledge-path",
            str(
                knowledge_path,
            ),
            "--strategy",
            "binary-overlap",
            "--llm",
            "deterministic",
            "--artifacts-dir",
            str(
                artifacts_dir,
            ),
        ]
    )

    assert "Token expiration policy" in output
    assert (
        artifacts_dir / "result.json"
    ).exists()
    assert (
        artifacts_dir / "report.md"
    ).exists()


def test_run_from_args_requires_task_for_normal_run(tmp_path):
    knowledge_path = create_knowledge_fixture(
        tmp_path,
    )

    with pytest.raises(ValueError):
        run_from_args(
            [
                "--mode",
                "rag_qa",
                "--knowledge-path",
                str(
                    knowledge_path,
                ),
            ]
        )