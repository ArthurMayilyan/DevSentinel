import pytest
import json

from compare_rag_strategies import (
    build_arg_parser,
    format_strategy_comparison_summary,
    run_strategy_comparison_from_args,
    select_best_strategy_result,
)

def test_compare_rag_strategies_parser_accepts_required_arguments():
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
    assert args.strategies == ["default"]
    assert args.top_k == 3
    assert args.summary_only is False
    assert args.output is None


def test_compare_rag_strategies_parser_accepts_multiple_strategies():
    parser = build_arg_parser()

    args = parser.parse_args(
        [
            "--knowledge-path",
            "./knowledge_base",
            "--cases",
            "./eval_cases/rag_eval_cases.json",
            "--strategies",
            "default",
            "term-frequency",
            "binary-overlap",
            "hybrid-lexical",
        ]
    )

    assert args.strategies == [
        "default",
        "term-frequency",
        "binary-overlap",
        "hybrid-lexical",
    ]

def test_run_strategy_comparison_from_args_returns_results_for_each_strategy(tmp_path):
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

    output = run_strategy_comparison_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--cases",
            str(cases_path),
            "--strategies",
            "default",
            "binary-overlap",
        ]
    )

    assert output["knowledge_path"] == str(knowledge_path)
    assert output["cases"] == str(cases_path)
    assert output["strategies"] == [
        "default",
        "binary-overlap",
    ]

    assert [
        result["retrieval_strategy"]
        for result in output["results"]
    ] == [
        "default",
        "binary-overlap",
    ]

    assert [
        result["hit_rate"]
        for result in output["results"]
    ] == [
        1.0,
        1.0,
    ]
    assert output["best_strategy"] == "default"
    assert output["best_strategy_metrics"] == {
        "hit_rate": 1.0,
        "top_1_accuracy": 1.0,
        "mean_reciprocal_rank": 1.0,
    }


def test_run_strategy_comparison_from_args_writes_output_file(tmp_path):
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

    output_path = tmp_path / "strategy_comparison.json"

    output = run_strategy_comparison_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--cases",
            str(cases_path),
            "--strategies",
            "default",
            "binary-overlap",
            "--output",
            str(output_path),
        ]
    )

    saved_output = json.loads(
        output_path.read_text(encoding="utf-8")
    )

    assert saved_output == output
    assert len(saved_output["results"]) == 2


def test_format_strategy_comparison_summary():
    output = {
        "best_strategy": "binary-overlap",
        "best_strategy_metrics": {
            "hit_rate": 1.0,
            "top_1_accuracy": 1.0,
            "mean_reciprocal_rank": 1.0,
        },
        "results": [
            {
                "retrieval_strategy": "term-frequency",
                "hit_rate": 1.0,
                "top_1_accuracy": 0.0,
                "mean_reciprocal_rank": 0.5,
            },
            {
                "retrieval_strategy": "binary-overlap",
                "hit_rate": 1.0,
                "top_1_accuracy": 1.0,
                "mean_reciprocal_rank": 1.0,
            },
        ],
    }

    assert format_strategy_comparison_summary(output) == "\n".join(
        [
            "RAG strategy comparison",
            "strategy          hit_rate  top_1  mrr",
            "term-frequency    1.00      0.00   0.50",
            "binary-overlap    1.00      1.00   1.00",
            "",
            "Best strategy: binary-overlap (mrr=1.00, top_1=1.00, hit_rate=1.00)",
        ]
    )


def test_strategy_comparison_shows_binary_overlap_improves_over_term_frequency_on_noisy_data(tmp_path):
    knowledge_path = tmp_path / "knowledge_base_noisy"
    knowledge_path.mkdir()

    token_noise = knowledge_path / "noise_tokens.md"
    token_noise.write_text(
        "token token token token token token token token",
        encoding="utf-8",
    )

    security = knowledge_path / "security.md"
    security.write_text(
        "Token expiration policy: tokens must be signed and must expire.",
        encoding="utf-8",
    )

    function_noise = knowledge_path / "noise_functions.md"
    function_noise.write_text(
        "function function function function function function",
        encoding="utf-8",
    )

    coding = knowledge_path / "coding.md"
    coding.write_text(
        "Small function guidelines: functions should be small and readable.",
        encoding="utf-8",
    )

    cases_path = tmp_path / "noisy_rag_eval_cases.json"
    cases_path.write_text(
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

    output = run_strategy_comparison_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--cases",
            str(cases_path),
            "--strategies",
            "term-frequency",
            "binary-overlap",
        ]
    )

    term_frequency_result = output["results"][0]
    binary_overlap_result = output["results"][1]

    assert term_frequency_result["retrieval_strategy"] == "term-frequency"
    assert binary_overlap_result["retrieval_strategy"] == "binary-overlap"

    assert term_frequency_result["hit_rate"] == 1.0
    assert binary_overlap_result["hit_rate"] == 1.0

    assert term_frequency_result["top_1_accuracy"] == 0.0
    assert binary_overlap_result["top_1_accuracy"] == 1.0

    assert term_frequency_result["mean_reciprocal_rank"] == 0.5
    assert binary_overlap_result["mean_reciprocal_rank"] == 1.0

    assert output["best_strategy"] == "binary-overlap"
    assert output["best_strategy_metrics"] == {
        "hit_rate": 1.0,
        "top_1_accuracy": 1.0,
        "mean_reciprocal_rank": 1.0,
    }    

def test_strategy_comparison_shows_hybrid_lexical_improves_over_term_frequency_on_noisy_data(tmp_path):
    knowledge_path = tmp_path / "knowledge_base_noisy"
    knowledge_path.mkdir()

    token_noise = knowledge_path / "noise_tokens.md"
    token_noise.write_text(
        "token token token token token token token token",
        encoding="utf-8",
    )

    security = knowledge_path / "security.md"
    security.write_text(
        "Token expiration policy: tokens must be signed and must expire.",
        encoding="utf-8",
    )

    function_noise = knowledge_path / "noise_functions.md"
    function_noise.write_text(
        "function function function function function function",
        encoding="utf-8",
    )

    coding = knowledge_path / "coding.md"
    coding.write_text(
        "Small function guidelines: functions should be small and readable.",
        encoding="utf-8",
    )

    cases_path = tmp_path / "noisy_rag_eval_cases.json"
    cases_path.write_text(
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

    output = run_strategy_comparison_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--cases",
            str(cases_path),
            "--strategies",
            "term-frequency",
            "hybrid-lexical",
        ]
    )

    term_frequency_result = output["results"][0]
    hybrid_lexical_result = output["results"][1]

    assert term_frequency_result["retrieval_strategy"] == "term-frequency"
    assert hybrid_lexical_result["retrieval_strategy"] == "hybrid-lexical"

    assert term_frequency_result["hit_rate"] == 1.0
    assert hybrid_lexical_result["hit_rate"] == 1.0

    assert term_frequency_result["top_1_accuracy"] == 0.0
    assert hybrid_lexical_result["top_1_accuracy"] == 1.0

    assert term_frequency_result["mean_reciprocal_rank"] == 0.5
    assert hybrid_lexical_result["mean_reciprocal_rank"] == 1.0

    assert output["best_strategy"] == "hybrid-lexical"
    assert output["best_strategy_metrics"] == {
        "hit_rate": 1.0,
        "top_1_accuracy": 1.0,
        "mean_reciprocal_rank": 1.0,
    }    

def test_select_best_strategy_result_prefers_highest_mrr():
    strategy_results = [
        {
            "retrieval_strategy": "high-hit-rate",
            "hit_rate": 1.0,
            "top_1_accuracy": 0.5,
            "mean_reciprocal_rank": 0.6,
        },
        {
            "retrieval_strategy": "high-mrr",
            "hit_rate": 0.8,
            "top_1_accuracy": 0.5,
            "mean_reciprocal_rank": 0.9,
        },
    ]

    best_result = select_best_strategy_result(
        strategy_results,
    )

    assert best_result["retrieval_strategy"] == "high-mrr"

def test_select_best_strategy_result_uses_top_1_accuracy_as_tie_breaker():
    strategy_results = [
        {
            "retrieval_strategy": "lower-top-1",
            "hit_rate": 1.0,
            "top_1_accuracy": 0.5,
            "mean_reciprocal_rank": 0.8,
        },
        {
            "retrieval_strategy": "higher-top-1",
            "hit_rate": 1.0,
            "top_1_accuracy": 0.7,
            "mean_reciprocal_rank": 0.8,
        },
    ]

    best_result = select_best_strategy_result(
        strategy_results,
    )

    assert best_result["retrieval_strategy"] == "higher-top-1"

def test_select_best_strategy_result_uses_hit_rate_as_final_metric_tie_breaker():
    strategy_results = [
        {
            "retrieval_strategy": "lower-hit-rate",
            "hit_rate": 0.8,
            "top_1_accuracy": 0.7,
            "mean_reciprocal_rank": 0.8,
        },
        {
            "retrieval_strategy": "higher-hit-rate",
            "hit_rate": 1.0,
            "top_1_accuracy": 0.7,
            "mean_reciprocal_rank": 0.8,
        },
    ]

    best_result = select_best_strategy_result(
        strategy_results,
    )

    assert best_result["retrieval_strategy"] == "higher-hit-rate"

def test_select_best_strategy_result_keeps_first_strategy_when_metrics_tie():
    strategy_results = [
        {
            "retrieval_strategy": "first",
            "hit_rate": 1.0,
            "top_1_accuracy": 1.0,
            "mean_reciprocal_rank": 1.0,
        },
        {
            "retrieval_strategy": "second",
            "hit_rate": 1.0,
            "top_1_accuracy": 1.0,
            "mean_reciprocal_rank": 1.0,
        },
    ]

    best_result = select_best_strategy_result(
        strategy_results,
    )

    assert best_result["retrieval_strategy"] == "first"

def test_select_best_strategy_result_rejects_empty_results():
    with pytest.raises(ValueError):
        select_best_strategy_result([])        