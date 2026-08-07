import json
import pytest

from evaluate_rag import build_arg_parser, run_rag_eval_from_args


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
    assert output["results"][0]["passed"] is True


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

                    