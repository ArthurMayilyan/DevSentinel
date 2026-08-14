import json
from pathlib import Path

from rag_agent_runtime import (
    extract_latest_evidence_from_trace_steps,
    extract_sources_from_evidence,
    format_rag_agent_markdown_report,
    run_rag_agent,
    write_rag_agent_markdown_report,
    write_rag_agent_result_json,
)


def normalize_path(
    value: str,
) -> str:
    return value.replace(
        "\\",
        "/",
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


def test_extract_sources_from_evidence_returns_unique_sources():
    assert extract_sources_from_evidence(
        [
            {
                "source": "security.md",
                "text": "Security text.",
            },
            {
                "source": "security.md",
                "text": "More security text.",
            },
            {
                "source": "coding.md",
                "text": "Coding text.",
            },
        ]
    ) == [
        "security.md",
        "coding.md",
    ]


def test_extract_latest_evidence_from_trace_steps_reads_embedded_tool_result():
    evidence = extract_latest_evidence_from_trace_steps(
        [
            {
                "step": 1,
                "observation": (
                    "Observation: "
                    "[{'source': 'security.md', "
                    "'text': 'Token expiration policy.'}]"
                ),
            }
        ]
    )

    assert evidence == [
        {
            "source": "security.md",
            "text": "Token expiration policy.",
        }
    ]


def test_run_rag_agent_returns_structured_result(tmp_path):
    knowledge_path = create_knowledge_fixture(
        tmp_path,
    )

    result = run_rag_agent(
        knowledge_path=str(knowledge_path),
        query="token expiration",
        strategy="binary-overlap",
        llm_name="deterministic",
        model="gpt-5",
        max_steps=4,
    )

    assert result.query == "token expiration"
    assert "Token expiration policy" in result.answer
    assert result.strategy == "binary-overlap"
    assert result.llm == "deterministic"
    assert result.model == "gpt-5"
    assert result.max_steps == 4
    assert len(result.sources) == 1
    assert normalize_path(
        result.sources[0],
    ).endswith(
        "/knowledge_base/security.md",
    )
    assert result.evidence
    assert result.trace_steps
    assert result.guardrail_passed is None
    assert result.fallback_used is False


def test_format_rag_agent_markdown_report_includes_runtime_details(tmp_path):
    knowledge_path = create_knowledge_fixture(
        tmp_path,
    )

    result = run_rag_agent(
        knowledge_path=str(knowledge_path),
        query="token expiration",
        strategy="binary-overlap",
        llm_name="deterministic",
        model="gpt-5",
    )

    report = format_rag_agent_markdown_report(
        result,
    )

    assert report.startswith("# RAG Agent Run Report")
    assert "Strategy: `binary-overlap`" in report
    assert "LLM: `deterministic`" in report
    assert "## Answer" in report
    assert "## Evidence" in report
    assert "## Trace" in report


def test_write_rag_agent_result_json_writes_file(tmp_path):
    knowledge_path = create_knowledge_fixture(
        tmp_path,
    )

    result = run_rag_agent(
        knowledge_path=str(knowledge_path),
        query="token expiration",
        strategy="binary-overlap",
    )

    output_path = tmp_path / "result" / "rag_agent_result.json"

    write_rag_agent_result_json(
        result=result,
        output_path=str(output_path),
    )

    assert output_path.is_file()

    payload = json.loads(
        output_path.read_text(
            encoding="utf-8",
        )
    )

    assert payload["query"] == "token expiration"
    assert "Token expiration policy" in payload["answer"]
    assert payload["strategy"] == "binary-overlap"


def test_write_rag_agent_markdown_report_writes_file(tmp_path):
    knowledge_path = create_knowledge_fixture(
        tmp_path,
    )

    result = run_rag_agent(
        knowledge_path=str(knowledge_path),
        query="token expiration",
        strategy="binary-overlap",
    )

    output_path = tmp_path / "report" / "rag_agent_report.md"

    write_rag_agent_markdown_report(
        result=result,
        output_path=str(output_path),
    )

    assert output_path.is_file()
    assert output_path.read_text(
        encoding="utf-8",
    ).startswith("# RAG Agent Run Report")


def test_run_rag_agent_collects_evidence_from_multiple_search_steps(tmp_path):
    knowledge_path = create_knowledge_fixture(
        tmp_path,
    )

    security = knowledge_path / "security.md"
    security.write_text(
        "# Security Policy\n\n"
        "Credentials must not be hardcoded in source code.\n"
        "Debug mode must be disabled in production.",
        encoding="utf-8",
    )

    result = run_rag_agent(
        knowledge_path=str(knowledge_path),
        query="How should credentials and debug mode be handled in production?",
        strategy="binary-overlap",
        llm_name="deterministic",
        model="gpt-5",
        max_steps=4,
    )

    assert "Credentials must not be hardcoded" in result.answer
    assert "Debug mode must be disabled" in result.answer
    assert len(result.trace_steps) == 3
    assert len(result.evidence) >= 1
    assert result.sources