import json
from pathlib import Path

from run_rag_grounding_eval import (
    build_grounding_quality_gate,
    format_grounding_eval_markdown_report,
    format_grounding_eval_summary,
    run_from_args,
    should_fail_due_to_grounding_quality_gate,
)


def create_grounding_eval_fixture(
    tmp_path: Path,
) -> tuple[Path, Path]:
    knowledge_path = tmp_path / "knowledge_base_noisy"
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

    cases_path = tmp_path / "rag_grounding_eval_cases.json"
    cases_path.write_text(
        json.dumps(
            [
                {
                    "name": "token expiration grounding",
                    "query": "token expiration",
                    "should_have_answer": True,
                    "forbidden_answer_contains": [
                        "24 hours",
                    ],
                },
                {
                    "name": "small function grounding",
                    "query": "small function",
                    "should_have_answer": True,
                    "forbidden_answer_contains": [
                        "maximum 10 lines",
                    ],
                },
            ]
        ),
        encoding="utf-8",
    )

    return knowledge_path, cases_path


def test_build_grounding_quality_gate_passes_when_accuracy_meets_threshold():
    assert build_grounding_quality_gate(
        summary={
            "grounding_accuracy": 1.0,
        },
        min_grounding_accuracy=1.0,
    ) == {
        "min_grounding_accuracy": 1.0,
        "actual_grounding_accuracy": 1.0,
        "passed": True,
    }


def test_build_grounding_quality_gate_fails_when_accuracy_below_threshold():
    assert build_grounding_quality_gate(
        summary={
            "grounding_accuracy": 0.5,
        },
        min_grounding_accuracy=1.0,
    ) == {
        "min_grounding_accuracy": 1.0,
        "actual_grounding_accuracy": 0.5,
        "passed": False,
    }


def test_format_grounding_eval_summary_formats_text():
    output = {
        "strategy": "binary-overlap",
        "summary": {
            "total_cases": 2,
            "passed_cases": 2,
            "failed_cases": 0,
            "grounding_accuracy": 1.0,
        },
        "quality_gate": {
            "passed": True,
        },
    }

    assert format_grounding_eval_summary(
        output,
    ) == "\n".join(
        [
            "RAG grounding eval",
            "strategy: binary-overlap",
            "cases: 2",
            "passed: 2",
            "failed: 0",
            "grounding_accuracy: 1.00",
            "quality_gate: passed",
        ]
    )


def test_format_grounding_eval_markdown_report_formats_report():
    output = {
        "knowledge_path": "./knowledge_base_noisy",
        "cases": "./eval_cases/rag_grounding_eval_cases.json",
        "top_k": 1,
        "strategy": "binary-overlap",
        "min_grounding_accuracy": 1.0,
        "summary": {
            "grounding_accuracy": 1.0,
            "passed_cases": 1,
            "failed_cases": 0,
            "results": [
                {
                    "name": "token expiration grounding",
                    "passed": True,
                    "failure_reasons": [],
                }
            ],
        },
    }

    report = format_grounding_eval_markdown_report(
        output,
    )

    assert report.startswith("# RAG Grounding Eval Report")
    assert "Strategy: `binary-overlap`" in report
    assert "Grounding accuracy: **1.00**" in report
    assert "| token expiration grounding | true |" in report


def test_should_fail_due_to_grounding_quality_gate_returns_true_when_enabled_and_failed():
    assert (
        should_fail_due_to_grounding_quality_gate(
            output={
                "quality_gate": {
                    "passed": False,
                },
            },
            fail_on_quality_gate=True,
        )
        is True
    )


def test_should_fail_due_to_grounding_quality_gate_returns_false_when_disabled():
    assert (
        should_fail_due_to_grounding_quality_gate(
            output={
                "quality_gate": {
                    "passed": False,
                },
            },
            fail_on_quality_gate=False,
        )
        is False
    )


def test_run_from_args_returns_grounding_eval_output(tmp_path):
    knowledge_path, cases_path = create_grounding_eval_fixture(
        tmp_path,
    )

    output = run_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--cases",
            str(cases_path),
            "--top-k",
            "1",
            "--strategy",
            "binary-overlap",
        ]
    )

    assert output["strategy"] == "binary-overlap"
    assert output["summary"]["total_cases"] == 2
    assert output["summary"]["passed_cases"] == 2
    assert output["summary"]["grounding_accuracy"] == 1.0
    assert output["quality_gate"]["passed"] is True


def test_run_from_args_writes_output_and_report(tmp_path):
    knowledge_path, cases_path = create_grounding_eval_fixture(
        tmp_path,
    )

    output_path = tmp_path / "grounding" / "result.json"
    report_output_path = tmp_path / "grounding" / "report.md"

    run_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--cases",
            str(cases_path),
            "--top-k",
            "1",
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