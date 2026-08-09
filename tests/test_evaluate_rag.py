import json
import pytest

from evaluate_rag import (
    build_arg_parser,
    format_rag_eval_summary,
    run_rag_eval_from_args,
)


def test_format_rag_eval_summary_includes_mrr_threshold():
    output = {
        "total_cases": 2,
        "passed_cases": 2,
        "failed_cases": 0,
        "hit_rate": 1.0,
        "top_1_accuracy": 0.0,
        "mean_reciprocal_rank": 0.5,
        "results": [],
        "min_mrr": 0.8,
        "mrr_threshold_passed": False,
        "threshold_passed": False,
    }

    assert format_rag_eval_summary(output) == "\n".join(
        [
            "RAG retrieval evaluation",
            "Total: 2",
            "Passed: 2",
            "Failed: 0",
            "Hit rate: 1.00",
            "Top-1 accuracy: 0.00",
            "MRR: 0.50",
            "MRR threshold: 0.80",
            "MRR threshold passed: false",
            "Overall threshold passed: false",
        ]
    )

def test_evaluate_rag_parser_accepts_required_arguments():
    parser = build_arg_parser()

    args = parser.parse_args(
        [
            "--knowledge-path",
            "./knowledge_base",
            "--cases",
            "./eval_cases/rag_eval_cases.json",
        ]
    )

    assert args.knowledge_path == "./knowledge_base"
    assert args.cases == "./eval_cases/rag_eval_cases.json"
    assert args.top_k == 3
    assert args.output is None
    assert args.min_hit_rate is None
    assert args.min_top_1_accuracy is None
    assert args.min_mrr is None
    assert args.summary_only is False


def test_evaluate_rag_parser_accepts_top_k_and_output():
    parser = build_arg_parser()

    args = parser.parse_args(
        [
            "--knowledge-path",
            "./knowledge_base",
            "--cases",
            "./eval_cases/rag_eval_cases.json",
            "--top-k",
            "5",
            "--output",
            "./rag_eval_summary.json",
        ]
    )

    assert args.top_k == 5
    assert args.output == "./rag_eval_summary.json"


def test_run_rag_eval_from_args_returns_summary(tmp_path):
    knowledge_path = tmp_path / "knowledge_base"
    knowledge_path.mkdir()

    security = knowledge_path / "security.md"
    security.write_text(
        "Tokens must be signed and must expire.",
        encoding="utf-8",
    )

    cases_path = tmp_path / "rag_eval_cases.json"
    cases_path.write_text(
        json.dumps(
            [
                {
                    "name": "token policy",
                    "query": "token expiration",
                    "expected_source_contains": "security.md",
                    "expected_text_contains": "Tokens must be signed",
                }
            ]
        ),
        encoding="utf-8",
    )

    output = run_rag_eval_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--cases",
            str(cases_path),
        ]
    )

    assert output["total_cases"] == 1
    assert output["passed_cases"] == 1
    assert output["failed_cases"] == 0
    assert output["hit_rate"] == 1.0
    assert output["top_1_accuracy"] == 1.0
    assert output["mean_reciprocal_rank"] == 1.0
    assert output["results"][0]["passed"] is True
    assert output["results"][0]["matched_rank"] == 1
    assert output["results"][0]["reciprocal_rank"] == 1.0
    assert output["results"][0]["retrieved_chunks"] == [
        {
            "rank": 1,
            "source": str(security),
            "chunk_index": 0,
            "score": 2,
            "text": "Tokens must be signed and must expire.",
        }
    ]    


def test_run_rag_eval_from_args_writes_output_file(tmp_path):
    knowledge_path = tmp_path / "knowledge_base"
    knowledge_path.mkdir()

    security = knowledge_path / "security.md"
    security.write_text(
        "Tokens must be signed and must expire.",
        encoding="utf-8",
    )

    cases_path = tmp_path / "rag_eval_cases.json"
    cases_path.write_text(
        json.dumps(
            [
                {
                    "name": "token policy",
                    "query": "token expiration",
                    "expected_source_contains": "security.md",
                    "expected_text_contains": "Tokens must be signed",
                }
            ]
        ),
        encoding="utf-8",
    )

    output_path = tmp_path / "rag_eval_summary.json"

    output = run_rag_eval_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--cases",
            str(cases_path),
            "--output",
            str(output_path),
        ]
    )

    saved_output = json.loads(
        output_path.read_text(encoding="utf-8")
    )

    assert saved_output == output
    assert saved_output["hit_rate"] == 1.0


def test_evaluate_rag_parser_accepts_min_hit_rate():
    parser = build_arg_parser()

    args = parser.parse_args(
        [
            "--knowledge-path",
            "./knowledge_base",
            "--cases",
            "./eval_cases/rag_eval_cases.json",
            "--min-hit-rate",
            "0.8",
        ]
    )

    assert args.min_hit_rate == 0.8
    assert args.min_mrr is None

def test_run_rag_eval_from_args_marks_threshold_as_passed(tmp_path):
    knowledge_path = tmp_path / "knowledge_base"
    knowledge_path.mkdir()

    security = knowledge_path / "security.md"
    security.write_text(
        "Tokens must be signed and must expire.",
        encoding="utf-8",
    )

    cases_path = tmp_path / "rag_eval_cases.json"
    cases_path.write_text(
        json.dumps(
            [
                {
                    "name": "token policy",
                    "query": "token expiration",
                    "expected_source_contains": "security.md",
                    "expected_text_contains": "Tokens must be signed",
                }
            ]
        ),
        encoding="utf-8",
    )

    output = run_rag_eval_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--cases",
            str(cases_path),
            "--min-hit-rate",
            "1.0",
        ]
    )

    assert output["hit_rate"] == 1.0
    assert output["min_hit_rate"] == 1.0
    assert output["threshold_passed"] is True
    assert output["hit_rate_threshold_passed"] is True
    assert output["threshold_passed"] is True    

def test_run_rag_eval_from_args_marks_threshold_as_failed(tmp_path):
    knowledge_path = tmp_path / "knowledge_base"
    knowledge_path.mkdir()

    security = knowledge_path / "security.md"
    security.write_text(
        "Tokens must be signed and must expire.",
        encoding="utf-8",
    )

    cases_path = tmp_path / "rag_eval_cases.json"
    cases_path.write_text(
        json.dumps(
            [
                {
                    "name": "coding style",
                    "query": "small function",
                    "expected_source_contains": "coding.md",
                    "expected_text_contains": "Functions should be small",
                }
            ]
        ),
        encoding="utf-8",
    )

    output = run_rag_eval_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--cases",
            str(cases_path),
            "--min-hit-rate",
            "0.8",
        ]
    )

    assert output["hit_rate"] == 0.0
    assert output["min_hit_rate"] == 0.8
    assert output["threshold_passed"] is False

def test_run_rag_eval_from_args_rejects_min_hit_rate_below_zero(tmp_path):
    knowledge_path = tmp_path / "knowledge_base"
    knowledge_path.mkdir()

    cases_path = tmp_path / "rag_eval_cases.json"
    cases_path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError):
        run_rag_eval_from_args(
            [
                "--knowledge-path",
                str(knowledge_path),
                "--cases",
                str(cases_path),
                "--min-hit-rate",
                "-0.1",
            ]
        )


def test_run_rag_eval_from_args_rejects_min_hit_rate_above_one(tmp_path):
    knowledge_path = tmp_path / "knowledge_base"
    knowledge_path.mkdir()

    cases_path = tmp_path / "rag_eval_cases.json"
    cases_path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError):
        run_rag_eval_from_args(
            [
                "--knowledge-path",
                str(knowledge_path),
                "--cases",
                str(cases_path),
                "--min-hit-rate",
                "1.1",
            ]
        )

def test_evaluate_rag_parser_accepts_summary_only():
    parser = build_arg_parser()

    args = parser.parse_args(
        [
            "--knowledge-path",
            "./knowledge_base",
            "--cases",
            "./eval_cases/rag_eval_cases.json",
            "--summary-only",
        ]
    )

    assert args.summary_only is True

def test_format_rag_eval_summary_formats_success_output():
    output = {
        "total_cases": 2,
        "passed_cases": 2,
        "failed_cases": 0,
        "hit_rate": 1.0,
        "top_1_accuracy": 1.0,
        "mean_reciprocal_rank": 1.0,
        "results": [],
        "min_hit_rate": 0.8,
        "hit_rate_threshold_passed": True,
        "min_top_1_accuracy": 0.7,
        "top_1_accuracy_threshold_passed": True,
        "threshold_passed": True,
    }

    assert format_rag_eval_summary(output) == "\n".join(
        [
            "RAG retrieval evaluation",
            "Total: 2",
            "Passed: 2",
            "Failed: 0",
            "Hit rate: 1.00",
            "Top-1 accuracy: 1.00",
            "MRR: 1.00",
            "Hit rate threshold: 0.80",
            "Hit rate threshold passed: true",
            "Top-1 accuracy threshold: 0.70",
            "Top-1 accuracy threshold passed: true",
            "Overall threshold passed: true",
        ]
    )

def test_format_rag_eval_summary_includes_failed_cases():
    output = {
        "total_cases": 2,
        "passed_cases": 1,
        "failed_cases": 1,
        "hit_rate": 0.5,
        "top_1_accuracy": 0.5,
        "mean_reciprocal_rank": 0.5,
        "results": [
            {
                "name": "token policy",
                "query": "token expiration",
                "passed": True,
                "expected_source_contains": "security.md",
                "expected_text_contains": "Tokens must be signed",
                "retrieved_sources": ["knowledge_base\\security.md"],
                "retrieved_texts": [
                    "Tokens must be signed and must expire.",
                ],
            },
            {
                "name": "coding style",
                "query": "small function",
                "passed": False,
                "expected_source_contains": "coding.md",
                "expected_text_contains": "Functions should be small",
                "retrieved_sources": ["knowledge_base\\_coding.md"],
                "retrieved_texts": [
                    "Functions should be small and readable.",
                ],
            },
        ],
        "min_hit_rate": 0.8,
        "hit_rate_threshold_passed": False,
        "min_top_1_accuracy": 0.7,
        "top_1_accuracy_threshold_passed": False,
        "threshold_passed": False,
    }

    assert format_rag_eval_summary(output) == "\n".join(
        [
            "RAG retrieval evaluation",
            "Total: 2",
            "Passed: 1",
            "Failed: 1",
            "Hit rate: 0.50",
            "Top-1 accuracy: 0.50",
            "MRR: 0.50",
            "Hit rate threshold: 0.80",
            "Hit rate threshold passed: false",
            "Top-1 accuracy threshold: 0.70",
            "Top-1 accuracy threshold passed: false",
            "Overall threshold passed: false",
            "",
            "Failed cases:",
            "- coding style",
            "  query: small function",
            "  expected source: coding.md",
            "  retrieved sources:",
            "    - knowledge_base\\_coding.md",
        ]
    )

def test_format_rag_eval_summary_shows_none_when_no_sources_retrieved():
    output = {
        "total_cases": 1,
        "passed_cases": 0,
        "failed_cases": 1,
        "hit_rate": 0.0,
        "top_1_accuracy": 0.0,
        "mean_reciprocal_rank": 0.0,
        "results": [
            {
                "name": "missing policy",
                "query": "unknown policy",
                "passed": False,
                "expected_source_contains": "policy.md",
                "expected_text_contains": "Policy text",
                "retrieved_sources": [],
                "retrieved_texts": [],
            },
        ],
    }

    assert format_rag_eval_summary(output) == "\n".join(
        [
            "RAG retrieval evaluation",
            "Total: 1",
            "Passed: 0",
            "Failed: 1",
            "Hit rate: 0.00",
            "Top-1 accuracy: 0.00",
            "MRR: 0.00",
            "",
            "Failed cases:",
            "- missing policy",
            "  query: unknown policy",
            "  expected source: policy.md",
            "  retrieved sources:",
            "    - <none>",
        ]
    )

def test_evaluate_rag_parser_accepts_min_mrr():
    parser = build_arg_parser()

    args = parser.parse_args(
        [
            "--knowledge-path",
            "./knowledge_base",
            "--cases",
            "./eval_cases/rag_eval_cases.json",
            "--min-mrr",
            "0.7",
        ]
    )

    assert args.min_mrr == 0.7


def test_run_rag_eval_from_args_marks_mrr_threshold_as_passed(tmp_path):
    knowledge_path = tmp_path / "knowledge_base"
    knowledge_path.mkdir()

    security = knowledge_path / "security.md"
    security.write_text(
        "Tokens must be signed and must expire.",
        encoding="utf-8",
    )

    cases_path = tmp_path / "rag_eval_cases.json"
    cases_path.write_text(
        json.dumps(
            [
                {
                    "name": "token policy",
                    "query": "token expiration",
                    "expected_source_contains": "security.md",
                    "expected_text_contains": "Tokens must be signed",
                }
            ]
        ),
        encoding="utf-8",
    )

    output = run_rag_eval_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--cases",
            str(cases_path),
            "--min-mrr",
            "1.0",
        ]
    )

    assert output["mean_reciprocal_rank"] == 1.0
    assert output["min_mrr"] == 1.0
    assert output["mrr_threshold_passed"] is True
    assert output["threshold_passed"] is True

def test_run_rag_eval_from_args_marks_mrr_threshold_as_failed(tmp_path):
    knowledge_path = tmp_path / "knowledge_base"
    knowledge_path.mkdir()

    noise = knowledge_path / "noise.md"
    noise.write_text(
        "token expiration token expiration",
        encoding="utf-8",
    )

    security = knowledge_path / "security.md"
    security.write_text(
        "Tokens must be signed and must expire.",
        encoding="utf-8",
    )

    cases_path = tmp_path / "rag_eval_cases.json"
    cases_path.write_text(
        json.dumps(
            [
                {
                    "name": "token policy",
                    "query": "token expiration",
                    "expected_source_contains": "security.md",
                    "expected_text_contains": "Tokens must be signed",
                }
            ]
        ),
        encoding="utf-8",
    )

    output = run_rag_eval_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--cases",
            str(cases_path),
            "--min-mrr",
            "0.8",
        ]
    )

    assert output["hit_rate"] == 1.0
    assert output["mean_reciprocal_rank"] == 0.5
    assert output["min_mrr"] == 0.8
    assert output["mrr_threshold_passed"] is False
    assert output["threshold_passed"] is False

def test_run_rag_eval_from_args_combines_hit_rate_top_1_and_mrr_thresholds(tmp_path):
    knowledge_path = tmp_path / "knowledge_base"
    knowledge_path.mkdir()

    noise = knowledge_path / "noise.md"
    noise.write_text(
        "token expiration token expiration",
        encoding="utf-8",
    )

    security = knowledge_path / "security.md"
    security.write_text(
        "Tokens must be signed and must expire.",
        encoding="utf-8",
    )

    cases_path = tmp_path / "rag_eval_cases.json"
    cases_path.write_text(
        json.dumps(
            [
                {
                    "name": "token policy",
                    "query": "token expiration",
                    "expected_source_contains": "security.md",
                    "expected_text_contains": "Tokens must be signed",
                }
            ]
        ),
        encoding="utf-8",
    )

    output = run_rag_eval_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--cases",
            str(cases_path),
            "--min-hit-rate",
            "1.0",
            "--min-top-1-accuracy",
            "0.8",
            "--min-mrr",
            "0.8",
        ]
    )

    assert output["hit_rate"] == 1.0
    assert output["top_1_accuracy"] == 0.0
    assert output["mean_reciprocal_rank"] == 0.5
    assert output["hit_rate_threshold_passed"] is True
    assert output["top_1_accuracy_threshold_passed"] is False
    assert output["mrr_threshold_passed"] is False
    assert output["threshold_passed"] is False

def test_run_rag_eval_from_args_rejects_min_mrr_below_zero(tmp_path):
    knowledge_path = tmp_path / "knowledge_base"
    knowledge_path.mkdir()

    cases_path = tmp_path / "rag_eval_cases.json"
    cases_path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError):
        run_rag_eval_from_args(
            [
                "--knowledge-path",
                str(knowledge_path),
                "--cases",
                str(cases_path),
                "--min-mrr",
                "-0.1",
            ]
        )


def test_run_rag_eval_from_args_rejects_min_mrr_above_one(tmp_path):
    knowledge_path = tmp_path / "knowledge_base"
    knowledge_path.mkdir()

    cases_path = tmp_path / "rag_eval_cases.json"
    cases_path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError):
        run_rag_eval_from_args(
            [
                "--knowledge-path",
                str(knowledge_path),
                "--cases",
                str(cases_path),
                "--min-mrr",
                "1.1",
            ]
        )

def test_evaluate_rag_parser_accepts_min_mrr():
    parser = build_arg_parser()

    args = parser.parse_args(
        [
            "--knowledge-path",
            "./knowledge_base",
            "--cases",
            "./eval_cases/rag_eval_cases.json",
            "--min-mrr",
            "0.7",
        ]
    )

    assert args.min_mrr == 0.7
    assert args.min_hit_rate is None

def test_evaluate_rag_parser_accepts_min_top_1_accuracy():
    parser = build_arg_parser()

    args = parser.parse_args(
        [
            "--knowledge-path",
            "./knowledge_base",
            "--cases",
            "./eval_cases/rag_eval_cases.json",
            "--min-top-1-accuracy",
            "0.7",
        ]
    )

    assert args.min_top_1_accuracy == 0.7
    assert args.min_hit_rate is None
    assert args.min_mrr is None

def test_run_rag_eval_from_args_marks_top_1_accuracy_threshold_as_passed(tmp_path):
    knowledge_path = tmp_path / "knowledge_base"
    knowledge_path.mkdir()

    security = knowledge_path / "security.md"
    security.write_text(
        "Tokens must be signed and must expire.",
        encoding="utf-8",
    )

    cases_path = tmp_path / "rag_eval_cases.json"
    cases_path.write_text(
        json.dumps(
            [
                {
                    "name": "token policy",
                    "query": "token expiration",
                    "expected_source_contains": "security.md",
                    "expected_text_contains": "Tokens must be signed",
                }
            ]
        ),
        encoding="utf-8",
    )

    output = run_rag_eval_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--cases",
            str(cases_path),
            "--min-top-1-accuracy",
            "1.0",
        ]
    )

    assert output["top_1_accuracy"] == 1.0
    assert output["min_top_1_accuracy"] == 1.0
    assert output["top_1_accuracy_threshold_passed"] is True
    assert output["threshold_passed"] is True

def test_run_rag_eval_from_args_marks_top_1_accuracy_threshold_as_failed(tmp_path):
    knowledge_path = tmp_path / "knowledge_base"
    knowledge_path.mkdir()

    noise = knowledge_path / "noise.md"
    noise.write_text(
        "token expiration token expiration",
        encoding="utf-8",
    )

    security = knowledge_path / "security.md"
    security.write_text(
        "Tokens must be signed and must expire.",
        encoding="utf-8",
    )

    cases_path = tmp_path / "rag_eval_cases.json"
    cases_path.write_text(
        json.dumps(
            [
                {
                    "name": "token policy",
                    "query": "token expiration",
                    "expected_source_contains": "security.md",
                    "expected_text_contains": "Tokens must be signed",
                }
            ]
        ),
        encoding="utf-8",
    )

    output = run_rag_eval_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--cases",
            str(cases_path),
            "--min-top-1-accuracy",
            "0.8",
        ]
    )

    assert output["hit_rate"] == 1.0
    assert output["top_1_accuracy"] == 0.0
    assert output["mean_reciprocal_rank"] == 0.5
    assert output["min_top_1_accuracy"] == 0.8
    assert output["top_1_accuracy_threshold_passed"] is False
    assert output["threshold_passed"] is False

def test_run_rag_eval_from_args_rejects_min_top_1_accuracy_below_zero(tmp_path):
    knowledge_path = tmp_path / "knowledge_base"
    knowledge_path.mkdir()

    cases_path = tmp_path / "rag_eval_cases.json"
    cases_path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError):
        run_rag_eval_from_args(
            [
                "--knowledge-path",
                str(knowledge_path),
                "--cases",
                str(cases_path),
                "--min-top-1-accuracy",
                "-0.1",
            ]
        )


def test_run_rag_eval_from_args_rejects_min_top_1_accuracy_above_one(tmp_path):
    knowledge_path = tmp_path / "knowledge_base"
    knowledge_path.mkdir()

    cases_path = tmp_path / "rag_eval_cases.json"
    cases_path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError):
        run_rag_eval_from_args(
            [
                "--knowledge-path",
                str(knowledge_path),
                "--cases",
                str(cases_path),
                "--min-top-1-accuracy",
                "1.1",
            ]
        )

def test_format_rag_eval_summary_includes_top_1_accuracy_threshold():
    output = {
        "total_cases": 2,
        "passed_cases": 1,
        "failed_cases": 1,
        "hit_rate": 0.5,
        "top_1_accuracy": 0.5,
        "mean_reciprocal_rank": 0.5,
        "results": [],
        "min_top_1_accuracy": 0.7,
        "top_1_accuracy_threshold_passed": False,
        "threshold_passed": False,
    }

    assert format_rag_eval_summary(output) == "\n".join(
        [
            "RAG retrieval evaluation",
            "Total: 2",
            "Passed: 1",
            "Failed: 1",
            "Hit rate: 0.50",
            "Top-1 accuracy: 0.50",
            "MRR: 0.50",
            "Top-1 accuracy threshold: 0.70",
            "Top-1 accuracy threshold passed: false",
            "Overall threshold passed: false",
        ]
    )

                                                                                       