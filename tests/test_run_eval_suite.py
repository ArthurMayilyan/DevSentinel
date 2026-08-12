import json
from pathlib import Path

import pytest

from run_eval_suite import (
    build_eval_suite_summary,
    format_eval_suite_markdown_summary,
    format_eval_suite_summary,
    load_eval_suite_config,
    run_from_args,
    should_fail_due_to_eval_suite_quality_gate,
    write_github_step_summary,
)


def create_eval_suite_fixture(
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

    function_noise = knowledge_path / "noise_functions.md"
    function_noise.write_text(
        "# Function Noise\n\n"
        "function function function function function function",
        encoding="utf-8",
    )

    coding = knowledge_path / "coding.md"
    coding.write_text(
        "# Coding Guidelines\n\n"
        "Small function guidelines: functions should be small and readable.",
        encoding="utf-8",
    )

    retrieval_cases_path = tmp_path / "noisy_rag_eval_cases.json"
    retrieval_cases_path.write_text(
        json.dumps(
            [
                {
                    "name": "token expiration policy",
                    "query": "token expiration",
                    "expected_source_contains": "security.md",
                    "expected_text_contains": "Token expiration policy",
                },
                {
                    "name": "small function guideline",
                    "query": "small function",
                    "expected_source_contains": "coding.md",
                    "expected_text_contains": "Small function guidelines",
                },
            ]
        ),
        encoding="utf-8",
    )

    answer_cases_path = tmp_path / "rag_answer_eval_cases.json"
    answer_cases_path.write_text(
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

    retrieval_config_dir = tmp_path / "eval_configs"
    retrieval_config_dir.mkdir()

    retrieval_config_path = retrieval_config_dir / "rag_strategy_noisy.json"
    retrieval_config_path.write_text(
        json.dumps(
            {
                "knowledge_path": str(knowledge_path),
                "cases": str(retrieval_cases_path),
                "strategies": [
                    "binary-overlap",
                    "hybrid-lexical",
                ],
                "baseline_strategy": "term-frequency",
                "top_k": 3,
                "max_regressed_cases": 0,
                "min_improved_cases": 1,
                "summary_only": True,
            }
        ),
        encoding="utf-8",
    )

    suite_config_path = tmp_path / "eval_suite.json"
    suite_config_path.write_text(
        json.dumps(
            {
                "retrieval": {
                    "config_dir": str(retrieval_config_dir),
                },
                "answer": {
                    "knowledge_path": str(knowledge_path),
                    "cases": str(answer_cases_path),
                    "top_k": 1,
                    "min_answer_accuracy": 1.0,
                },
            }
        ),
        encoding="utf-8",
    )

    return suite_config_path


def test_load_eval_suite_config_loads_config(tmp_path):
    suite_config_path = tmp_path / "eval_suite.json"
    suite_config_path.write_text(
        json.dumps(
            {
                "retrieval": {
                    "config_dir": "./eval_configs",
                },
                "answer": {
                    "knowledge_path": "./knowledge_base_noisy",
                    "cases": "./eval_cases/rag_answer_eval_cases.json",
                    "top_k": 3,
                    "min_answer_accuracy": 1.0,
                },
            }
        ),
        encoding="utf-8",
    )

    config = load_eval_suite_config(
        str(suite_config_path),
    )

    assert config["retrieval"]["config_dir"] == "./eval_configs"
    assert config["answer"]["knowledge_path"] == "./knowledge_base_noisy"
    assert config["answer"]["top_k"] == 3


def test_load_eval_suite_config_rejects_unknown_top_level_keys(tmp_path):
    suite_config_path = tmp_path / "eval_suite.json"
    suite_config_path.write_text(
        json.dumps(
            {
                "retrieval": {
                    "config_dir": "./eval_configs",
                },
                "answer": {
                    "knowledge_path": "./knowledge_base_noisy",
                    "cases": "./eval_cases/rag_answer_eval_cases.json",
                },
                "extra": True,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_eval_suite_config(
            str(suite_config_path),
        )


def test_build_eval_suite_summary_passes_when_both_layers_pass():
    summary = build_eval_suite_summary(
        retrieval_summary={
            "passed": True,
            "failed_profiles": [],
            "profiles": [],
        },
        answer_output={
            "quality_gate": {
                "passed": True,
            },
            "summary": {
                "answer_accuracy": 1.0,
                "passed_cases": 2,
                "failed_cases": 0,
                "total_cases": 2,
            },
        },
    )

    assert summary["passed"] is True
    assert summary["retrieval"]["passed"] is True
    assert summary["answer"]["passed"] is True


def test_build_eval_suite_summary_fails_when_answer_fails():
    summary = build_eval_suite_summary(
        retrieval_summary={
            "passed": True,
            "failed_profiles": [],
            "profiles": [],
        },
        answer_output={
            "quality_gate": {
                "passed": False,
            },
            "summary": {
                "answer_accuracy": 0.5,
                "passed_cases": 1,
                "failed_cases": 1,
                "total_cases": 2,
            },
        },
    )

    assert summary["passed"] is False
    assert summary["retrieval"]["passed"] is True
    assert summary["answer"]["passed"] is False


def test_format_eval_suite_summary_formats_text():
    summary = {
        "passed": True,
        "retrieval": {
            "passed": True,
        },
        "answer": {
            "passed": True,
            "answer_accuracy": 1.0,
        },
    }

    assert format_eval_suite_summary(summary) == "\n".join(
        [
            "Eval suite",
            "overall: passed",
            "retrieval: passed",
            "answer: passed",
            "answer_accuracy: 1.00",
        ]
    )


def test_format_eval_suite_markdown_summary_formats_markdown():
    summary = {
        "passed": True,
        "retrieval": {
            "passed": True,
            "failed_profiles": [],
            "profiles": [
                {
                    "profile": "rag_strategy_noisy.json",
                    "quality_gate_status": "passed",
                    "best_accepted_strategy": "binary-overlap",
                }
            ],
        },
        "answer": {
            "passed": True,
            "answer_accuracy": 1.0,
            "passed_cases": 2,
            "failed_cases": 0,
            "total_cases": 2,
        },
    }

    markdown = format_eval_suite_markdown_summary(
        summary,
    )

    assert markdown.startswith("# Eval Suite Summary")
    assert "Overall: **passed**" in markdown
    assert "| rag_strategy_noisy.json | passed | binary-overlap |" in markdown
    assert "Answer accuracy: **1.00**" in markdown


def test_should_fail_due_to_eval_suite_quality_gate_returns_true_when_enabled_and_failed():
    assert (
        should_fail_due_to_eval_suite_quality_gate(
            summary={
                "passed": False,
            },
            fail_on_quality_gate=True,
        )
        is True
    )


def test_should_fail_due_to_eval_suite_quality_gate_returns_false_when_disabled():
    assert (
        should_fail_due_to_eval_suite_quality_gate(
            summary={
                "passed": False,
            },
            fail_on_quality_gate=False,
        )
        is False
    )


def test_write_github_step_summary_writes_summary_file(tmp_path):
    summary_path = tmp_path / "github_step_summary.md"

    written = write_github_step_summary(
        summary={
            "passed": True,
            "retrieval": {
                "passed": True,
                "failed_profiles": [],
                "profiles": [],
            },
            "answer": {
                "passed": True,
                "answer_accuracy": 1.0,
                "passed_cases": 2,
                "failed_cases": 0,
                "total_cases": 2,
            },
        },
        env={
            "GITHUB_STEP_SUMMARY": str(summary_path),
        },
    )

    assert written is True
    assert summary_path.is_file()
    assert summary_path.read_text(
        encoding="utf-8",
    ).startswith("# Eval Suite Summary")


def test_run_from_args_runs_full_eval_suite_and_writes_artifacts(tmp_path):
    suite_config_path = create_eval_suite_fixture(
        tmp_path,
    )

    artifacts_dir = tmp_path / "eval_suite_artifacts"

    summary = run_from_args(
        [
            "--config",
            str(suite_config_path),
            "--artifacts-dir",
            str(artifacts_dir),
        ]
    )

    assert summary["passed"] is True
    assert summary["retrieval"]["passed"] is True
    assert summary["answer"]["passed"] is True

    assert (artifacts_dir / "suite_summary.json").is_file()
    assert (artifacts_dir / "suite_summary.md").is_file()

    assert (artifacts_dir / "retrieval" / "profiles_summary.json").is_file()
    assert (artifacts_dir / "retrieval" / "profiles_summary.md").is_file()
    assert (artifacts_dir / "retrieval" / "index.md").is_file()

    assert (
        artifacts_dir
        / "retrieval"
        / "rag_strategy_noisy"
        / "comparison.json"
    ).is_file()

    assert (
        artifacts_dir
        / "retrieval"
        / "rag_strategy_noisy"
        / "report.md"
    ).is_file()

    assert (artifacts_dir / "answer" / "result.json").is_file()
    assert (artifacts_dir / "answer" / "report.md").is_file()

    