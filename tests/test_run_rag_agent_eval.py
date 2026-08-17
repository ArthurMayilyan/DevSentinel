import json
from pathlib import Path

from run_rag_agent_eval import (
    build_agent_quality_gate,
    format_rag_agent_eval_markdown_report,
    format_rag_agent_eval_summary,
    run_from_args,
    should_fail_due_to_agent_quality_gate,
)
from openai_client_factory import (
    DEFAULT_OPENAI_MODEL,
)


def create_agent_eval_fixture(
    tmp_path: Path,
) -> tuple[Path, Path]:
    knowledge_path = tmp_path / "knowledge_base_noisy"
    knowledge_path.mkdir()

    security = knowledge_path / "security.md"
    security.write_text(
        "# Security Policy\n\n"
        "Token expiration policy: tokens must be signed and must expire.\n"
        "Credentials must not be hardcoded in source code.\n"
        "Debug mode must be disabled in production.",
        encoding="utf-8",
    )

    coding = knowledge_path / "coding.md"
    coding.write_text(
        "# Coding Guidelines\n\n"
        "Small function guidelines: functions should be small and readable.",
        encoding="utf-8",
    )

    cases_path = tmp_path / "rag_agent_eval_cases.json"
    cases_path.write_text(
        json.dumps(
            [
                {
                    "name": "agent token expiration answer",
                    "query": "token expiration",
                    "expected_answer_contains": [
                        "Token expiration policy",
                        "tokens must be signed",
                        "must expire",
                    ],
                    "forbidden_answer_contains": [
                        "24 hours",
                    ],
                },
                {
                    "name": "agent small function answer",
                    "query": "small function",
                    "expected_answer_contains": [
                        "Small function",
                    ],
                    "forbidden_answer_contains": [
                        "maximum 10 lines",
                    ],
                },
            ]
        ),
        encoding="utf-8",
    )

    return knowledge_path, cases_path


def test_build_agent_quality_gate_passes_when_accuracy_meets_threshold():
    assert build_agent_quality_gate(
        summary={
            "agent_answer_accuracy": 1.0,
        },
        min_agent_answer_accuracy=1.0,
    ) == {
        "min_agent_answer_accuracy": 1.0,
        "actual_agent_answer_accuracy": 1.0,
        "passed": True,
    }


def test_build_agent_quality_gate_fails_when_accuracy_below_threshold():
    assert build_agent_quality_gate(
        summary={
            "agent_answer_accuracy": 0.5,
        },
        min_agent_answer_accuracy=1.0,
    ) == {
        "min_agent_answer_accuracy": 1.0,
        "actual_agent_answer_accuracy": 0.5,
        "passed": False,
    }


def test_format_rag_agent_eval_summary_formats_text():
    output = {
        "strategy": "binary-overlap",
        "llm": "deterministic",
        "model": "gpt-5",
        "summary": {
            "total_cases": 2,
            "passed_cases": 2,
            "failed_cases": 0,
            "agent_answer_accuracy": 1.0,
            "guardrail_checked_cases": 0,
            "guardrail_passed_cases": 0,
            "fallback_used_cases": 0,
        },
        "quality_gate": {
            "passed": True,
        },
    }

    assert format_rag_agent_eval_summary(
        output,
    ) == "\n".join(
        [
            "RAG agent eval",
            "strategy: binary-overlap",
            "llm: deterministic",
            "model: gpt-5",
            "cases: 2",
            "passed: 2",
            "failed: 0",
            "agent_answer_accuracy: 1.00",
            "guardrail_checked_cases: 0",
            "guardrail_passed_cases: 0",
            "fallback_used_cases: 0",
            "quality_gate: passed",
        ]
    )


def test_format_rag_agent_eval_markdown_report_formats_report():
    output = {
        "knowledge_path": "./knowledge_base_noisy",
        "cases": "./eval_cases/rag_agent_eval_cases.json",
        "strategy": "binary-overlap",
        "llm": "deterministic",
        "model": "gpt-5",        
        "max_steps": 4,
        "min_agent_answer_accuracy": 1.0,
        "summary": {
            "agent_answer_accuracy": 1.0,
            "passed_cases": 1,
            "failed_cases": 0,
            "guardrail_checked_cases": 0,
            "guardrail_passed_cases": 0,
            "fallback_used_cases": 0,            
            "results": [
                {
                    "name": "agent token expiration answer",
                    "passed": True,
                    "search_knowledge_called": True,
                    "failure_reasons": [],
                    "sources": [
                        "security.md",
                    ],
                    "guardrail_passed": None,
                    "fallback_used": False,                    
                }
            ],
        },
    }

    report = format_rag_agent_eval_markdown_report(
        output,
    )

    assert report.startswith("# RAG Agent Eval Report")
    assert "Strategy: `binary-overlap`" in report
    assert "Agent answer accuracy: **1.00**" in report
    assert "| agent token expiration answer | true | true | none | false |" in report
    assert "LLM: `deterministic`" in report
    assert "Model: `gpt-5`" in report
    assert "Fallback used cases: **0**" in report


def test_should_fail_due_to_agent_quality_gate_returns_true_when_enabled_and_failed():
    assert (
        should_fail_due_to_agent_quality_gate(
            output={
                "quality_gate": {
                    "passed": False,
                },
            },
            fail_on_quality_gate=True,
        )
        is True
    )


def test_should_fail_due_to_agent_quality_gate_returns_false_when_disabled():
    assert (
        should_fail_due_to_agent_quality_gate(
            output={
                "quality_gate": {
                    "passed": False,
                },
            },
            fail_on_quality_gate=False,
        )
        is False
    )


def test_run_from_args_returns_agent_eval_output(tmp_path):
    knowledge_path, cases_path = create_agent_eval_fixture(
        tmp_path,
    )

    output = run_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--cases",
            str(cases_path),
            "--strategy",
            "binary-overlap",
        ]
    )

    assert output["strategy"] == "binary-overlap"
    assert output["summary"]["total_cases"] == 2
    assert output["summary"]["passed_cases"] == 2
    assert output["summary"]["agent_answer_accuracy"] == 1.0
    assert output["quality_gate"]["passed"] is True
    assert output["llm"] == "deterministic"
    assert output["model"] == DEFAULT_OPENAI_MODEL
    assert output["summary"]["guardrail_checked_cases"] == 0
    assert output["summary"]["fallback_used_cases"] == 0


def test_run_from_args_writes_output_and_report(tmp_path):
    knowledge_path, cases_path = create_agent_eval_fixture(
        tmp_path,
    )

    output_path = tmp_path / "agent_eval" / "result.json"
    report_output_path = tmp_path / "agent_eval" / "report.md"

    run_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--cases",
            str(cases_path),
            "--strategy",
            "binary-overlap",
            "--output",
            str(output_path),
            "--report-output",
            str(report_output_path),
        ]
    )

    assert output_path.is_file()
    assert report_output_path.is_file()

    output = json.loads(
        output_path.read_text(
            encoding="utf-8",
        )
    )

    assert output["strategy"] == "binary-overlap"
    assert output["quality_gate"]["passed"] is True
    assert report_output_path.read_text(
        encoding="utf-8",
    ).startswith("# RAG Agent Eval Report")
    assert output["llm"] == "deterministic"
    assert output["model"] == DEFAULT_OPENAI_MODEL    


def test_run_from_args_supports_openai_llm_mode_with_guardrail_metrics(
    tmp_path,
    monkeypatch,
):
    _, cases_path = create_agent_eval_fixture(
        tmp_path,
    )

    class FakeRunResult:
        def __init__(
            self,
            *,
            answer: str,
        ):
            self.answer = answer
            self.trace_steps = [
                {
                    "tool": "search_knowledge",
                }
            ]
            self.sources = [
                "security.md",
            ]
            self.guardrail_passed = True
            self.fallback_used = False

    def fake_run_rag_agent(
        *,
        knowledge_path,
        query,
        strategy,
        llm_name,
        model,
        max_steps,
    ):
        assert knowledge_path == "./knowledge_base_noisy"
        assert strategy == "binary-overlap"
        assert llm_name == "openai"

        # Explicit CLI argument must override the model
        # configured in agentloop.toml.
        assert model == "gpt-5"

        if query == "small function":
            return FakeRunResult(
                answer=(
                    "Small function guidelines: functions should be small "
                    "and readable.\n\n"
                    "Source: coding.md"
                ),
            )

        return FakeRunResult(
            answer=(
                "Token expiration policy: tokens must be signed "
                "and must expire.\n\n"
                "Source: security.md"
            ),
        )

    monkeypatch.setattr(
        "run_rag_agent_eval.run_rag_agent",
        fake_run_rag_agent,
    )

    output = run_from_args(
        [
            "--knowledge-path",
            "./knowledge_base_noisy",
            "--cases",
            str(
                cases_path,
            ),
            "--strategy",
            "binary-overlap",
            "--llm",
            "openai",
            "--model",
            "gpt-5",
        ]
    )

    assert output["llm"] == "openai"

    # Explicit --model value has higher priority than
    # DEFAULT_OPENAI_MODEL / agentloop.toml.
    assert output["model"] == "gpt-5"

    assert output["summary"]["total_cases"] == 2
    assert output["summary"]["passed_cases"] == 2
    assert output["summary"]["agent_answer_accuracy"] == 1.0

    assert output["summary"]["guardrail_checked_cases"] == 2
    assert output["summary"]["guardrail_passed_cases"] == 2
    assert output["summary"]["fallback_used_cases"] == 0

    assert output["quality_gate"]["passed"] is True