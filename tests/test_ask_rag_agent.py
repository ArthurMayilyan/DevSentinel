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