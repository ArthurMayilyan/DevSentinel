import json
from pathlib import Path

from ask_rag_agent import (
    format_agent_rag_answer,
    run_from_args,
)


def create_knowledge_fixture(
    tmp_path: Path,
) -> Path:
    knowledge_path = tmp_path / "knowledge_base"
    knowledge_path.mkdir()

    security = knowledge_path / "security.md"
    security.write_text(
        "# Security Policy\n\n"
        "Token expiration policy: tokens must be signed and must expire.",
        encoding="utf-8",
    )

    return knowledge_path


def test_format_agent_rag_answer_formats_answer():
    assert format_agent_rag_answer(
        "Token expiration policy.\n\nSource: security.md",
    ) == "\n".join(
        [
            "Answer",
            "------",
            "Token expiration policy.\n\nSource: security.md",
        ]
    )


def test_run_from_args_returns_agent_rag_answer(tmp_path):
    knowledge_path = create_knowledge_fixture(
        tmp_path,
    )

    answer = run_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--query",
            "token expiration",
            "--strategy",
            "binary-overlap",
        ]
    )

    assert "Token expiration policy" in answer
    assert "Source:" in answer

def test_run_from_args_uses_deterministic_llm_by_default(tmp_path):
    knowledge_path = create_knowledge_fixture(
        tmp_path,
    )

    answer = run_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--query",
            "token expiration",
            "--strategy",
            "binary-overlap",
        ]
    )

    assert "Token expiration policy" in answer
    assert "Source:" in answer    

def test_run_from_args_accepts_explicit_deterministic_llm(tmp_path):
    knowledge_path = create_knowledge_fixture(
        tmp_path,
    )

    answer = run_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--query",
            "token expiration",
            "--strategy",
            "binary-overlap",
            "--llm",
            "deterministic",
        ]
    )

    assert "Token expiration policy" in answer
    assert "Source:" in answer    

def test_run_from_args_writes_json_and_markdown_outputs(tmp_path):
    knowledge_path = create_knowledge_fixture(
        tmp_path,
    )

    output_path = tmp_path / "result.json"
    report_output_path = tmp_path / "report.md"

    answer = run_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--query",
            "token expiration",
            "--strategy",
            "binary-overlap",
            "--output",
            str(output_path),
            "--report-output",
            str(report_output_path),
        ]
    )

    assert "Token expiration policy" in answer
    assert output_path.is_file()
    assert report_output_path.is_file()

    payload = json.loads(
        output_path.read_text(
            encoding="utf-8",
        )
    )

    assert payload["query"] == "token expiration"
    assert payload["strategy"] == "binary-overlap"
    assert "Token expiration policy" in payload["answer"]
    assert report_output_path.read_text(
        encoding="utf-8",
    ).startswith("# RAG Agent Run Report")    


def test_run_from_args_returns_short_query_relevant_answer(tmp_path):
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

    answer = run_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--query",
            "token expiration",
            "--strategy",
            "binary-overlap",
            "--llm",
            "deterministic",
        ]
    )

    assert "Token expiration policy" in answer
    assert "Credentials must not be hardcoded" not in answer
    assert "Debug mode must be disabled" not in answer    