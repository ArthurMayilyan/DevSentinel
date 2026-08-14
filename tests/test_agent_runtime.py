import json

import pytest

from agent_modes import AGENT_MODE_CODE_REVIEW, AGENT_MODE_RAG_QA
from agent_runtime import (
    AgentRuntimeRequest,
    agent_runtime_result_to_dict,
    run_agent_runtime,
    validate_agent_runtime_request,
)


def create_knowledge_fixture(tmp_path):
    knowledge_path = tmp_path / "knowledge_base"
    knowledge_path.mkdir()

    security = knowledge_path / "security.md"
    security.write_text(
        "# Security Policy\n\n"
        "Token expiration policy: tokens must be signed and must expire.\n"
        "Credentials must not be hardcoded in source code.\n"
        "Debug mode must be disabled in production.",
        encoding="utf-8",
    )

    return knowledge_path


def test_validate_agent_runtime_request_requires_task():
    with pytest.raises(ValueError):
        validate_agent_runtime_request(
            AgentRuntimeRequest(
                mode=AGENT_MODE_RAG_QA,
                task="",
                knowledge_path="./knowledge_base",
            )
        )


def test_validate_agent_runtime_request_requires_knowledge_path_for_rag_qa():
    with pytest.raises(ValueError):
        validate_agent_runtime_request(
            AgentRuntimeRequest(
                mode=AGENT_MODE_RAG_QA,
                task="token expiration",
            )
        )


def test_run_agent_runtime_runs_rag_qa_mode(tmp_path):
    knowledge_path = create_knowledge_fixture(
        tmp_path,
    )

    result = run_agent_runtime(
        AgentRuntimeRequest(
            mode=AGENT_MODE_RAG_QA,
            task="token expiration",
            knowledge_path=str(
                knowledge_path,
            ),
            strategy="binary-overlap",
            llm_name="deterministic",
        )
    )

    assert result.mode == AGENT_MODE_RAG_QA
    assert "Token expiration policy" in result.answer
    assert result.result_dict["strategy"] == "binary-overlap"


def test_run_agent_runtime_writes_artifact_bundle(tmp_path):
    knowledge_path = create_knowledge_fixture(
        tmp_path,
    )
    artifacts_dir = tmp_path / "artifacts"

    result = run_agent_runtime(
        AgentRuntimeRequest(
            mode=AGENT_MODE_RAG_QA,
            task="token expiration",
            knowledge_path=str(
                knowledge_path,
            ),
            strategy="binary-overlap",
            llm_name="deterministic",
            artifacts_dir=str(
                artifacts_dir,
            ),
        )
    )

    result_json_path = artifacts_dir / "result.json"
    report_path = artifacts_dir / "report.md"

    assert result.result_json_path == str(
        result_json_path,
    )
    assert result.report_path == str(
        report_path,
    )
    assert result_json_path.exists()
    assert report_path.exists()

    payload = json.loads(
        result_json_path.read_text(
            encoding="utf-8",
        )
    )

    assert payload["answer"] == result.answer
    assert "Token expiration policy" in report_path.read_text(
        encoding="utf-8",
    )


def test_agent_runtime_result_to_dict_contains_generic_and_mode_result(tmp_path):
    knowledge_path = create_knowledge_fixture(
        tmp_path,
    )

    result = run_agent_runtime(
        AgentRuntimeRequest(
            mode=AGENT_MODE_RAG_QA,
            task="token expiration",
            knowledge_path=str(
                knowledge_path,
            ),
            strategy="binary-overlap",
            llm_name="deterministic",
        )
    )

    payload = agent_runtime_result_to_dict(
        result,
    )

    assert payload["mode"] == AGENT_MODE_RAG_QA
    assert payload["task"] == "token expiration"
    assert "answer" in payload
    assert "result" in payload


def test_validate_agent_runtime_request_requires_task_or_preset_for_code_review():
    with pytest.raises(ValueError):
        validate_agent_runtime_request(
            AgentRuntimeRequest(
                mode=AGENT_MODE_CODE_REVIEW,
            )
        )


def test_validate_agent_runtime_request_requires_path_for_code_review_preset():
    with pytest.raises(ValueError):
        validate_agent_runtime_request(
            AgentRuntimeRequest(
                mode=AGENT_MODE_CODE_REVIEW,
                preset="code-review",
            )
        )


def test_run_agent_runtime_runs_code_review_mode():
    result = run_agent_runtime(
        AgentRuntimeRequest(
            mode=AGENT_MODE_CODE_REVIEW,
            preset="code-review",
            path="./sample_project",
            llm_name="demo",
            max_steps=20,
        )
    )

    assert result.mode == AGENT_MODE_CODE_REVIEW
    assert result.answer == "Review complete. Report written to report.md."
    assert result.result_dict["status"] == "completed"
    assert result.result_dict["run"]["preset"] == "code-review"


def test_run_agent_runtime_writes_code_review_artifact_bundle(tmp_path):
    artifacts_dir = tmp_path / "code_review_artifacts"

    result = run_agent_runtime(
        AgentRuntimeRequest(
            mode=AGENT_MODE_CODE_REVIEW,
            preset="code-review",
            path="./sample_project",
            llm_name="demo",
            max_steps=20,
            artifacts_dir=str(
                artifacts_dir,
            ),
        )
    )

    result_json_path = artifacts_dir / "result.json"
    report_path = artifacts_dir / "report.md"

    assert result_json_path.exists()
    assert report_path.exists()
    assert result.result_json_path == str(result_json_path)
    assert result.report_path == str(report_path)

    payload = json.loads(
        result_json_path.read_text(
            encoding="utf-8",
        )
    )

    assert payload["status"] == "completed"
    assert payload["run"]["preset"] == "code-review"
    assert "Code Review Agent Run Report" in report_path.read_text(
        encoding="utf-8",
    )    