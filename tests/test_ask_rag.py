import json
from pathlib import Path

from ask_rag import (
    format_rag_answer_text,
    run_from_args,
)
from rag_defaults import (
    DEFAULT_RAG_TOP_K,
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

    coding = knowledge_path / "coding.md"
    coding.write_text(
        "# Coding Guidelines\n\n"
        "Small function guidelines: functions should be small and readable.",
        encoding="utf-8",
    )

    return knowledge_path


def test_format_rag_answer_text_formats_answer_strategy_and_sources():
    output = {
        "answer": "Token expiration policy\n\nSource: knowledge_base/security.md",
        "strategy": "binary-overlap",
        "cited_sources": [
            "knowledge_base/security.md",
        ],
    }

    assert format_rag_answer_text(output) == "\n".join(
        [
            "Answer",
            "------",
            "Token expiration policy\n\nSource: knowledge_base/security.md",
            "",
            "Strategy",
            "--------",
            "binary-overlap",
            "",
            "Sources",
            "-------",
            "- knowledge_base/security.md",
        ]
    )


def test_run_from_args_returns_answer_output(tmp_path):
    knowledge_path = create_knowledge_fixture(
        tmp_path,
    )

    output = run_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--query",
            "token expiration",
            "--top-k",
            "1",
            "--strategy",
            "binary-overlap",
        ]
    )

    assert output["query"] == "token expiration"
    assert "Token expiration policy" in output["answer"]
    assert output["cited_sources"] == [
        str(knowledge_path / "security.md"),
    ]
    assert output["strategy"] == "binary-overlap"


def test_run_from_args_writes_json_output(tmp_path):
    knowledge_path = create_knowledge_fixture(
        tmp_path,
    )

    output_path = tmp_path / "outputs" / "answer.json"

    run_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--query",
            "small function",
            "--top-k",
            "1",
            "--output",
            str(output_path),
            "--strategy",
            "binary-overlap",            
        ]
    )

    assert output_path.is_file()

    output = json.loads(
        output_path.read_text(
            encoding="utf-8",
        )
    )

    assert output["query"] == "small function"
    assert "Small function guidelines" in output["answer"]
    assert output["strategy"] == "binary-overlap"

def create_noisy_knowledge_fixture(
    tmp_path: Path,
) -> Path:
    knowledge_path = tmp_path / "knowledge_base_noisy"
    knowledge_path.mkdir()

    token_noise = knowledge_path / "noise_tokens.md"
    token_noise.write_text(
        "# Token Noise\n\n"
        "token token token token token token token token",
        encoding="utf-8",
    )

    security = knowledge_path / "security.md"
    security.write_text(
        "# Security Policy\n\n"
        "Token expiration policy: tokens must be signed and must expire.",
        encoding="utf-8",
    )

    return knowledge_path


def test_run_from_args_uses_selected_strategy_on_noisy_data(tmp_path):
    knowledge_path = create_noisy_knowledge_fixture(
        tmp_path,
    )

    term_frequency_output = run_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--query",
            "token expiration",
            "--top-k",
            "1",
            "--strategy",
            "term-frequency",
        ]
    )

    binary_overlap_output = run_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--query",
            "token expiration",
            "--top-k",
            "1",
            "--strategy",
            "binary-overlap",
        ]
    )

    assert term_frequency_output["strategy"] == "term-frequency"
    assert binary_overlap_output["strategy"] == "binary-overlap"

    assert term_frequency_output["cited_sources"] == [
        str(knowledge_path / "noise_tokens.md"),
    ]

    assert binary_overlap_output["cited_sources"] == [
        str(knowledge_path / "security.md"),
    ]



         