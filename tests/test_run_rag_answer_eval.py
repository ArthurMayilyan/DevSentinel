import json
from pathlib import Path

from run_rag_answer_eval import (
    build_answer_quality_gate,
    build_output,
    extractive_answer_builder,
    format_answer_eval_markdown_report,
    format_answer_eval_summary,
    run_from_args,
    should_fail_due_to_answer_quality_gate,
)
from rag_answer_eval import RagAnswerEvalSummary, RagAnswerEvalResult


def create_answer_eval_fixture(
    tmp_path: Path,
) -> tuple[Path, Path]:
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

    cases_path = tmp_path / "rag_answer_eval_cases.json"
    cases_path.write_text(
        json.dumps(
            [
                {
                    "name": "token expiration answer",
                    "query": "token expiration",
                    "expected_answer_contains": "Token expiration policy",
                    "expected_source_contains": "security.md",
                },
                {
                    "name": "small function answer",
                    "query": "small function",
                    "expected_answer_contains": "Small function guidelines",
                    "expected_source_contains": "coding.md",
                },
            ]
        ),
        encoding="utf-8",
    )

    return knowledge_path, cases_path


def build_test_summary(
    *,
    answer_accuracy: float = 1.0,
) -> RagAnswerEvalSummary:
    passed = answer_accuracy == 1.0

    return RagAnswerEvalSummary(
        total_cases=1,
        passed_cases=1 if passed else 0,
        failed_cases=0 if passed else 1,
        answer_accuracy=answer_accuracy,
        results=[
            RagAnswerEvalResult(
                name="token expiration answer",
                query="token expiration",
                passed=passed,
                answer="Token expiration policy",
                cited_sources=[
                    "knowledge_base/security.md",
                ],
                expected_answer_contains="Token expiration policy",
                expected_source_contains="security.md",
                failure_reasons=[] if passed else [
                    "answer does not contain expected text",
                ],
            )
        ],
    )


def test_build_answer_quality_gate_passes_when_accuracy_meets_threshold():
    summary = build_test_summary(
        answer_accuracy=1.0,
    )

    assert build_answer_quality_gate(
        summary=summary,
        min_answer_accuracy=1.0,
    ) == {
        "min_answer_accuracy": 1.0,
        "actual_answer_accuracy": 1.0,
        "passed": True,
    }


def test_build_answer_quality_gate_fails_when_accuracy_is_below_threshold():
    summary = build_test_summary(
        answer_accuracy=0.5,
    )

    assert build_answer_quality_gate(
        summary=summary,
        min_answer_accuracy=1.0,
    ) == {
        "min_answer_accuracy": 1.0,
        "actual_answer_accuracy": 0.5,
        "passed": False,
    }


def test_build_output_contains_summary_and_quality_gate():
    summary = build_test_summary(
        answer_accuracy=1.0,
    )

    output = build_output(
        knowledge_path="./knowledge_base",
        cases_path="./eval_cases/rag_answer_eval_cases.json",
        top_k=3,
        strategy="binary-overlap",
        min_answer_accuracy=1.0,
        summary=summary,
    )

    assert output["knowledge_path"] == "./knowledge_base"
    assert output["cases"] == "./eval_cases/rag_answer_eval_cases.json"
    assert output["top_k"] == 3
    assert output["strategy"] == "binary-overlap"
    assert output["summary"]["answer_accuracy"] == 1.0
    assert output["quality_gate"]["passed"] is True


def test_format_answer_eval_summary_formats_concise_text():
    output = build_output(
        knowledge_path="./knowledge_base",
        cases_path="./cases.json",
        top_k=3,
        strategy="binary-overlap",
        min_answer_accuracy=1.0,
        summary=build_test_summary(),
    )

    assert format_answer_eval_summary(output) == "\n".join(
        [
            "RAG answer eval",
            "strategy: binary-overlap",
            "cases: 1",
            "passed: 1",
            "failed: 0",
            "answer_accuracy: 1.00",
            "quality_gate: passed",
        ]
    )


def test_format_answer_eval_markdown_report_formats_report():
    output = build_output(
        knowledge_path="./knowledge_base",
        cases_path="./cases.json",
        top_k=3,
        strategy="binary-overlap",
        min_answer_accuracy=1.0,
        summary=build_test_summary(),
    )

    report = format_answer_eval_markdown_report(
        output,
    )

    assert report.startswith("# RAG Answer Eval Report")
    assert "Answer accuracy: **1.00**" in report
    assert "Strategy: `binary-overlap`" in report
    assert "| token expiration answer | true |" in report


def test_should_fail_due_to_answer_quality_gate_returns_false_when_flag_disabled():
    output = {
        "quality_gate": {
            "passed": False,
        },
    }

    assert (
        should_fail_due_to_answer_quality_gate(
            output=output,
            fail_on_quality_gate=False,
        )
        is False
    )


def test_should_fail_due_to_answer_quality_gate_returns_true_when_gate_failed():
    output = {
        "quality_gate": {
            "passed": False,
        },
    }

    assert (
        should_fail_due_to_answer_quality_gate(
            output=output,
            fail_on_quality_gate=True,
        )
        is True
    )


def test_run_from_args_returns_answer_eval_output(tmp_path):
    knowledge_path, cases_path = create_answer_eval_fixture(
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
    assert output["summary"]["answer_accuracy"] == 1.0
    assert output["quality_gate"]["passed"] is True


def test_run_from_args_writes_output_and_report(tmp_path):
    knowledge_path, cases_path = create_answer_eval_fixture(
        tmp_path,
    )

    output_path = tmp_path / "answer_eval_output.json"
    report_output_path = tmp_path / "answer_eval_report.md"

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

    saved_output = json.loads(
        output_path.read_text(
            encoding="utf-8",
        )
    )

    assert saved_output["strategy"] == "binary-overlap"
    assert saved_output["quality_gate"]["passed"] is True
    assert report_output_path.read_text(
        encoding="utf-8",
    ).startswith("# RAG Answer Eval Report")

def test_run_from_args_creates_output_parent_directories(tmp_path):
    knowledge_path, cases_path = create_answer_eval_fixture(
        tmp_path,
    )

    output_path = tmp_path / "artifacts" / "answer" / "result.json"
    report_output_path = tmp_path / "artifacts" / "answer" / "report.md"

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

def create_noisy_answer_eval_fixture(
    tmp_path: Path,
) -> tuple[Path, Path]:
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

    cases_path = tmp_path / "rag_answer_eval_cases.json"
    cases_path.write_text(
        json.dumps(
            [
                {
                    "name": "token expiration answer",
                    "query": "token expiration",
                    "expected_answer_contains": "Token expiration policy",
                    "expected_source_contains": "security.md",
                }
            ]
        ),
        encoding="utf-8",
    )

    return knowledge_path, cases_path    

def test_run_from_args_uses_strategy_for_answer_eval_on_noisy_data(tmp_path):
    knowledge_path, cases_path = create_noisy_answer_eval_fixture(
        tmp_path,
    )

    term_frequency_output = run_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--cases",
            str(cases_path),
            "--top-k",
            "1",
            "--strategy",
            "term-frequency",
            "--min-answer-accuracy",
            "1.0",
        ]
    )

    binary_overlap_output = run_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--cases",
            str(cases_path),
            "--top-k",
            "1",
            "--strategy",
            "binary-overlap",
            "--min-answer-accuracy",
            "1.0",
        ]
    )

    assert term_frequency_output["strategy"] == "term-frequency"
    assert term_frequency_output["summary"]["answer_accuracy"] == 0.0
    assert term_frequency_output["quality_gate"]["passed"] is False

    assert binary_overlap_output["strategy"] == "binary-overlap"
    assert binary_overlap_output["summary"]["answer_accuracy"] == 1.0
    assert binary_overlap_output["quality_gate"]["passed"] is True