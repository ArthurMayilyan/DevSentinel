import pytest
import json

from compare_rag_strategies import (
    build_arg_parser,
    build_improvement_gate_result,
    build_regression_gate_result,
    build_strategy_diagnostics,
    compare_strategy_result_against_baseline,
    format_strategy_comparison_summary,
    normalize_strategy_list,
    run_strategy_comparison_from_args,
    select_best_strategy_result,
    should_fail_due_to_improvement_gate,
    should_fail_due_to_regression_gate,
    validate_regression_gate_args,
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
    assert args.baseline_strategy is None
    assert args.max_regressed_cases is None
    assert args.fail_on_regression_gate is False
    assert args.min_improved_cases is None
    assert args.fail_on_improvement_gate is False


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

def test_compare_rag_strategies_parser_accepts_baseline_strategy():
    parser = build_arg_parser()

    args = parser.parse_args(
        [
            "--knowledge-path",
            "./knowledge_base",
            "--cases",
            "./eval_cases/rag_eval_cases.json",
            "--baseline-strategy",
            "term-frequency",
        ]
    )

    assert args.baseline_strategy == "term-frequency"

def test_normalize_strategy_list_returns_original_strategies_without_baseline():
    assert normalize_strategy_list(
        strategies=[
            "binary-overlap",
            "hybrid-lexical",
        ],
        baseline_strategy=None,
    ) == [
        "binary-overlap",
        "hybrid-lexical",
    ]


def test_normalize_strategy_list_adds_baseline_first_when_missing():
    assert normalize_strategy_list(
        strategies=[
            "binary-overlap",
            "hybrid-lexical",
        ],
        baseline_strategy="term-frequency",
    ) == [
        "term-frequency",
        "binary-overlap",
        "hybrid-lexical",
    ]


def test_normalize_strategy_list_does_not_duplicate_baseline():
    assert normalize_strategy_list(
        strategies=[
            "term-frequency",
            "binary-overlap",
        ],
        baseline_strategy="term-frequency",
    ) == [
        "term-frequency",
        "binary-overlap",
    ]

def test_compare_strategy_result_against_baseline_detects_improved_case():
    baseline_result = {
        "retrieval_strategy": "term-frequency",
        "results": [
            {
                "name": "token expiration policy",
                "query": "token expiration",
                "matched_rank": 2,
                "reciprocal_rank": 0.5,
            }
        ],
    }

    candidate_result = {
        "retrieval_strategy": "binary-overlap",
        "results": [
            {
                "name": "token expiration policy",
                "query": "token expiration",
                "matched_rank": 1,
                "reciprocal_rank": 1.0,
            }
        ],
    }

    diagnostic = compare_strategy_result_against_baseline(
        baseline_result=baseline_result,
        candidate_result=candidate_result,
    )

    assert diagnostic["baseline_strategy"] == "term-frequency"
    assert diagnostic["strategy"] == "binary-overlap"
    assert diagnostic["improved_count"] == 1
    assert diagnostic["regressed_count"] == 0
    assert diagnostic["unchanged_count"] == 0
    assert diagnostic["improved_cases"] == [
        {
            "name": "token expiration policy",
            "query": "token expiration",
            "baseline_matched_rank": 2,
            "candidate_matched_rank": 1,
            "baseline_reciprocal_rank": 0.5,
            "candidate_reciprocal_rank": 1.0,
        }
    ]

def test_compare_strategy_result_against_baseline_detects_regressed_case():
    baseline_result = {
        "retrieval_strategy": "binary-overlap",
        "results": [
            {
                "name": "token expiration policy",
                "query": "token expiration",
                "matched_rank": 1,
                "reciprocal_rank": 1.0,
            }
        ],
    }

    candidate_result = {
        "retrieval_strategy": "term-frequency",
        "results": [
            {
                "name": "token expiration policy",
                "query": "token expiration",
                "matched_rank": 2,
                "reciprocal_rank": 0.5,
            }
        ],
    }

    diagnostic = compare_strategy_result_against_baseline(
        baseline_result=baseline_result,
        candidate_result=candidate_result,
    )

    assert diagnostic["improved_count"] == 0
    assert diagnostic["regressed_count"] == 1
    assert diagnostic["unchanged_count"] == 0
    assert diagnostic["regressed_cases"][0]["name"] == "token expiration policy"

def test_compare_strategy_result_against_baseline_detects_unchanged_case():
    baseline_result = {
        "retrieval_strategy": "binary-overlap",
        "results": [
            {
                "name": "token expiration policy",
                "query": "token expiration",
                "matched_rank": 1,
                "reciprocal_rank": 1.0,
            }
        ],
    }

    candidate_result = {
        "retrieval_strategy": "hybrid-lexical",
        "results": [
            {
                "name": "token expiration policy",
                "query": "token expiration",
                "matched_rank": 1,
                "reciprocal_rank": 1.0,
            }
        ],
    }

    diagnostic = compare_strategy_result_against_baseline(
        baseline_result=baseline_result,
        candidate_result=candidate_result,
    )

    assert diagnostic["improved_count"] == 0
    assert diagnostic["regressed_count"] == 0
    assert diagnostic["unchanged_count"] == 1
    assert diagnostic["unchanged_cases"][0]["name"] == "token expiration policy"


def test_build_strategy_diagnostics_compares_all_candidates_to_baseline():
    strategy_results = [
        {
            "retrieval_strategy": "term-frequency",
            "results": [
                {
                    "name": "token expiration policy",
                    "query": "token expiration",
                    "matched_rank": 2,
                    "reciprocal_rank": 0.5,
                }
            ],
        },
        {
            "retrieval_strategy": "binary-overlap",
            "results": [
                {
                    "name": "token expiration policy",
                    "query": "token expiration",
                    "matched_rank": 1,
                    "reciprocal_rank": 1.0,
                }
            ],
        },
        {
            "retrieval_strategy": "hybrid-lexical",
            "results": [
                {
                    "name": "token expiration policy",
                    "query": "token expiration",
                    "matched_rank": 1,
                    "reciprocal_rank": 1.0,
                }
            ],
        },
    ]

    diagnostics = build_strategy_diagnostics(
        strategy_results=strategy_results,
        baseline_strategy="term-frequency",
    )

    assert [
        diagnostic["strategy"]
        for diagnostic in diagnostics
    ] == [
        "binary-overlap",
        "hybrid-lexical",
    ]

    assert [
        diagnostic["improved_count"]
        for diagnostic in diagnostics
    ] == [
        1,
        1,
    ]

def test_run_strategy_comparison_from_args_adds_baseline_diagnostics(tmp_path):
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
            "--baseline-strategy",
            "term-frequency",
            "--strategies",
            "binary-overlap",
            "hybrid-lexical",
        ]
    )

    assert output["strategies"] == [
        "term-frequency",
        "binary-overlap",
        "hybrid-lexical",
    ]
    assert output["baseline_strategy"] == "term-frequency"
    assert output["best_strategy"] == "binary-overlap"

    assert [
        diagnostic["strategy"]
        for diagnostic in output["strategy_diagnostics"]
    ] == [
        "binary-overlap",
        "hybrid-lexical",
    ]

    assert [
        diagnostic["improved_count"]
        for diagnostic in output["strategy_diagnostics"]
    ] == [
        2,
        2,
    ]

    assert [
        diagnostic["regressed_count"]
        for diagnostic in output["strategy_diagnostics"]
    ] == [
        0,
        0,
    ]

def test_format_strategy_comparison_summary_includes_baseline_diagnostics():
    output = {
        "best_strategy": "binary-overlap",
        "best_strategy_metrics": {
            "hit_rate": 1.0,
            "top_1_accuracy": 1.0,
            "mean_reciprocal_rank": 1.0,
        },
        "baseline_strategy": "term-frequency",
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
        "strategy_diagnostics": [
            {
                "baseline_strategy": "term-frequency",
                "strategy": "binary-overlap",
                "improved_count": 1,
                "regressed_count": 0,
                "unchanged_count": 0,
                "improved_cases": [
                    {
                        "name": "token expiration policy",
                        "query": "token expiration",
                        "baseline_matched_rank": 2,
                        "candidate_matched_rank": 1,
                        "baseline_reciprocal_rank": 0.5,
                        "candidate_reciprocal_rank": 1.0,
                    }
                ],
                "regressed_cases": [],
                "unchanged_cases": [],
            }
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
            "",
            "Baseline strategy: term-frequency",
            "Strategy diagnostics vs baseline:",
            "binary-overlap: improved=1, regressed=0, unchanged=0",
            "  improved:",
            "    - token expiration policy: rank 2 -> 1",
        ]
    )

def test_compare_rag_strategies_parser_accepts_max_regressed_cases():
    parser = build_arg_parser()

    args = parser.parse_args(
        [
            "--knowledge-path",
            "./knowledge_base",
            "--cases",
            "./eval_cases/rag_eval_cases.json",
            "--baseline-strategy",
            "term-frequency",
            "--max-regressed-cases",
            "0",
        ]
    )

    assert args.baseline_strategy == "term-frequency"
    assert args.max_regressed_cases == 0


def test_validate_regression_gate_args_allows_gate_with_baseline():
    validate_regression_gate_args(
        baseline_strategy="term-frequency",
        max_regressed_cases=0,
    )


def test_validate_regression_gate_args_allows_missing_gate_without_baseline():
    validate_regression_gate_args(
        baseline_strategy=None,
        max_regressed_cases=None,
    )


def test_validate_regression_gate_args_rejects_gate_without_baseline():
    with pytest.raises(ValueError):
        validate_regression_gate_args(
            baseline_strategy=None,
            max_regressed_cases=0,
        )


def test_validate_regression_gate_args_rejects_negative_max_regressed_cases():
    with pytest.raises(ValueError):
        validate_regression_gate_args(
            baseline_strategy="term-frequency",
            max_regressed_cases=-1,
        )

def test_build_regression_gate_result_passes_when_regressions_are_within_limit():
    strategy_diagnostics = [
        {
            "strategy": "binary-overlap",
            "regressed_count": 0,
        },
        {
            "strategy": "hybrid-lexical",
            "regressed_count": 0,
        },
    ]

    gate = build_regression_gate_result(
        strategy_diagnostics=strategy_diagnostics,
        max_regressed_cases=0,
    )

    assert gate == {
        "max_regressed_cases": 0,
        "total_regressed_cases": 0,
        "passed": True,
    }


def test_build_regression_gate_result_fails_when_regressions_exceed_limit():
    strategy_diagnostics = [
        {
            "strategy": "candidate-a",
            "regressed_count": 1,
        },
        {
            "strategy": "candidate-b",
            "regressed_count": 0,
        },
    ]

    gate = build_regression_gate_result(
        strategy_diagnostics=strategy_diagnostics,
        max_regressed_cases=0,
    )

    assert gate == {
        "max_regressed_cases": 0,
        "total_regressed_cases": 1,
        "passed": False,
    }

def test_run_strategy_comparison_from_args_adds_passing_regression_gate(tmp_path):
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
            "--baseline-strategy",
            "term-frequency",
            "--strategies",
            "binary-overlap",
            "hybrid-lexical",
            "--max-regressed-cases",
            "0",
        ]
    )

    assert output["regression_gate"] == {
        "max_regressed_cases": 0,
        "total_regressed_cases": 0,
        "passed": True,
    }

def test_run_strategy_comparison_from_args_rejects_regression_gate_without_baseline(tmp_path):
    knowledge_path = tmp_path / "knowledge_base"
    knowledge_path.mkdir()

    cases_path = tmp_path / "rag_eval_cases.json"
    cases_path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError):
        run_strategy_comparison_from_args(
            [
                "--knowledge-path",
                str(knowledge_path),
                "--cases",
                str(cases_path),
                "--strategies",
                "binary-overlap",
                "--max-regressed-cases",
                "0",
            ]
        )

def test_format_strategy_comparison_summary_includes_regression_gate():
    output = {
        "best_strategy": "binary-overlap",
        "best_strategy_metrics": {
            "hit_rate": 1.0,
            "top_1_accuracy": 1.0,
            "mean_reciprocal_rank": 1.0,
        },
        "baseline_strategy": "term-frequency",
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
        "strategy_diagnostics": [
            {
                "baseline_strategy": "term-frequency",
                "strategy": "binary-overlap",
                "improved_count": 1,
                "regressed_count": 0,
                "unchanged_count": 0,
                "improved_cases": [
                    {
                        "name": "token expiration policy",
                        "query": "token expiration",
                        "baseline_matched_rank": 2,
                        "candidate_matched_rank": 1,
                        "baseline_reciprocal_rank": 0.5,
                        "candidate_reciprocal_rank": 1.0,
                    }
                ],
                "regressed_cases": [],
                "unchanged_cases": [],
            }
        ],
        "regression_gate": {
            "max_regressed_cases": 0,
            "total_regressed_cases": 0,
            "passed": True,
        },
    }

    assert format_strategy_comparison_summary(output) == "\n".join(
        [
            "RAG strategy comparison",
            "strategy          hit_rate  top_1  mrr",
            "term-frequency    1.00      0.00   0.50",
            "binary-overlap    1.00      1.00   1.00",
            "",
            "Best strategy: binary-overlap (mrr=1.00, top_1=1.00, hit_rate=1.00)",
            "",
            "Baseline strategy: term-frequency",
            "Strategy diagnostics vs baseline:",
            "binary-overlap: improved=1, regressed=0, unchanged=0",
            "  improved:",
            "    - token expiration policy: rank 2 -> 1",
            "",
            "Regression gate: max_regressed_cases=0, total_regressed_cases=0, passed=true",
        ]
    )

def test_compare_rag_strategies_parser_accepts_fail_on_regression_gate():
    parser = build_arg_parser()

    args = parser.parse_args(
        [
            "--knowledge-path",
            "./knowledge_base",
            "--cases",
            "./eval_cases/rag_eval_cases.json",
            "--baseline-strategy",
            "term-frequency",
            "--max-regressed-cases",
            "0",
            "--fail-on-regression-gate",
        ]
    )

    assert args.baseline_strategy == "term-frequency"
    assert args.max_regressed_cases == 0
    assert args.fail_on_regression_gate is True

def test_validate_regression_gate_args_allows_fail_on_regression_gate_with_gate():
    validate_regression_gate_args(
        baseline_strategy="term-frequency",
        max_regressed_cases=0,
        fail_on_regression_gate=True,
    )


def test_validate_regression_gate_args_rejects_fail_on_regression_gate_without_gate():
    with pytest.raises(ValueError):
        validate_regression_gate_args(
            baseline_strategy="term-frequency",
            max_regressed_cases=None,
            fail_on_regression_gate=True,
        )

def test_should_fail_due_to_regression_gate_returns_false_when_flag_is_disabled():
    output = {
        "regression_gate": {
            "passed": False,
        },
    }

    assert should_fail_due_to_regression_gate(
        output=output,
        fail_on_regression_gate=False,
    ) is False

def test_should_fail_due_to_regression_gate_returns_false_when_gate_passed():
    output = {
        "regression_gate": {
            "passed": True,
        },
    }

    assert should_fail_due_to_regression_gate(
        output=output,
        fail_on_regression_gate=True,
    ) is False

def test_should_fail_due_to_regression_gate_returns_true_when_gate_failed():
    output = {
        "regression_gate": {
            "passed": False,
        },
    }

    assert should_fail_due_to_regression_gate(
        output=output,
        fail_on_regression_gate=True,
    ) is True

def test_should_fail_due_to_regression_gate_rejects_missing_gate_when_flag_enabled():
    with pytest.raises(ValueError):
        should_fail_due_to_regression_gate(
            output={},
            fail_on_regression_gate=True,
        )

def test_run_strategy_comparison_from_args_adds_failing_regression_gate(tmp_path):
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
            "--baseline-strategy",
            "binary-overlap",
            "--strategies",
            "term-frequency",
            "--max-regressed-cases",
            "0",
            "--fail-on-regression-gate",
        ]
    )

    assert output["regression_gate"] == {
        "max_regressed_cases": 0,
        "total_regressed_cases": 2,
        "passed": False,
    }

    assert should_fail_due_to_regression_gate(
        output=output,
        fail_on_regression_gate=True,
    ) is True

def test_compare_rag_strategies_parser_accepts_min_improved_cases():
    parser = build_arg_parser()

    args = parser.parse_args(
        [
            "--knowledge-path",
            "./knowledge_base",
            "--cases",
            "./eval_cases/rag_eval_cases.json",
            "--baseline-strategy",
            "term-frequency",
            "--min-improved-cases",
            "1",
        ]
    )

    assert args.baseline_strategy == "term-frequency"
    assert args.min_improved_cases == 1


def test_compare_rag_strategies_parser_accepts_fail_on_improvement_gate():
    parser = build_arg_parser()

    args = parser.parse_args(
        [
            "--knowledge-path",
            "./knowledge_base",
            "--cases",
            "./eval_cases/rag_eval_cases.json",
            "--baseline-strategy",
            "term-frequency",
            "--min-improved-cases",
            "1",
            "--fail-on-improvement-gate",
        ]
    )

    assert args.baseline_strategy == "term-frequency"
    assert args.min_improved_cases == 1
    assert args.fail_on_improvement_gate is True

def test_validate_regression_gate_args_allows_improvement_gate_with_baseline():
    validate_regression_gate_args(
        baseline_strategy="term-frequency",
        max_regressed_cases=None,
        min_improved_cases=1,
    )


def test_validate_regression_gate_args_rejects_improvement_gate_without_baseline():
    with pytest.raises(ValueError):
        validate_regression_gate_args(
            baseline_strategy=None,
            max_regressed_cases=None,
            min_improved_cases=1,
        )


def test_validate_regression_gate_args_rejects_negative_min_improved_cases():
    with pytest.raises(ValueError):
        validate_regression_gate_args(
            baseline_strategy="term-frequency",
            max_regressed_cases=None,
            min_improved_cases=-1,
        )


def test_validate_regression_gate_args_allows_fail_on_improvement_gate_with_gate():
    validate_regression_gate_args(
        baseline_strategy="term-frequency",
        max_regressed_cases=None,
        min_improved_cases=1,
        fail_on_improvement_gate=True,
    )


def test_validate_regression_gate_args_rejects_fail_on_improvement_gate_without_gate():
    with pytest.raises(ValueError):
        validate_regression_gate_args(
            baseline_strategy="term-frequency",
            max_regressed_cases=None,
            min_improved_cases=None,
            fail_on_improvement_gate=True,
        )


def test_build_improvement_gate_result_passes_when_improvements_meet_requirement():
    strategy_diagnostics = [
        {
            "strategy": "binary-overlap",
            "improved_count": 2,
        },
        {
            "strategy": "hybrid-lexical",
            "improved_count": 2,
        },
    ]

    gate = build_improvement_gate_result(
        strategy_diagnostics=strategy_diagnostics,
        min_improved_cases=1,
    )

    assert gate == {
        "min_improved_cases": 1,
        "total_improved_cases": 4,
        "passed": True,
    }


def test_build_improvement_gate_result_fails_when_improvements_are_below_requirement():
    strategy_diagnostics = [
        {
            "strategy": "hybrid-lexical",
            "improved_count": 0,
        },
    ]

    gate = build_improvement_gate_result(
        strategy_diagnostics=strategy_diagnostics,
        min_improved_cases=1,
    )

    assert gate == {
        "min_improved_cases": 1,
        "total_improved_cases": 0,
        "passed": False,
    }


def test_should_fail_due_to_improvement_gate_returns_false_when_flag_is_disabled():
    output = {
        "improvement_gate": {
            "passed": False,
        },
    }

    assert should_fail_due_to_improvement_gate(
        output=output,
        fail_on_improvement_gate=False,
    ) is False


def test_should_fail_due_to_improvement_gate_returns_false_when_gate_passed():
    output = {
        "improvement_gate": {
            "passed": True,
        },
    }

    assert should_fail_due_to_improvement_gate(
        output=output,
        fail_on_improvement_gate=True,
    ) is False


def test_should_fail_due_to_improvement_gate_returns_true_when_gate_failed():
    output = {
        "improvement_gate": {
            "passed": False,
        },
    }

    assert should_fail_due_to_improvement_gate(
        output=output,
        fail_on_improvement_gate=True,
    ) is True


def test_should_fail_due_to_improvement_gate_rejects_missing_gate_when_flag_enabled():
    with pytest.raises(ValueError):
        should_fail_due_to_improvement_gate(
            output={},
            fail_on_improvement_gate=True,
        )

def test_run_strategy_comparison_from_args_adds_passing_improvement_gate(tmp_path):
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
            "--baseline-strategy",
            "term-frequency",
            "--strategies",
            "binary-overlap",
            "--min-improved-cases",
            "1",
            "--fail-on-improvement-gate",
        ]
    )

    assert output["improvement_gate"] == {
        "min_improved_cases": 1,
        "total_improved_cases": 2,
        "passed": True,
    }

    assert should_fail_due_to_improvement_gate(
        output=output,
        fail_on_improvement_gate=True,
    ) is False


def test_run_strategy_comparison_from_args_adds_failing_improvement_gate(tmp_path):
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
            "--baseline-strategy",
            "binary-overlap",
            "--strategies",
            "hybrid-lexical",
            "--min-improved-cases",
            "1",
            "--fail-on-improvement-gate",
        ]
    )

    assert output["improvement_gate"] == {
        "min_improved_cases": 1,
        "total_improved_cases": 0,
        "passed": False,
    }

    assert should_fail_due_to_improvement_gate(
        output=output,
        fail_on_improvement_gate=True,
    ) is True


def test_format_strategy_comparison_summary_includes_improvement_gate():
    output = {
        "best_strategy": "binary-overlap",
        "best_strategy_metrics": {
            "hit_rate": 1.0,
            "top_1_accuracy": 1.0,
            "mean_reciprocal_rank": 1.0,
        },
        "baseline_strategy": "term-frequency",
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
        "strategy_diagnostics": [
            {
                "baseline_strategy": "term-frequency",
                "strategy": "binary-overlap",
                "improved_count": 1,
                "regressed_count": 0,
                "unchanged_count": 0,
                "improved_cases": [
                    {
                        "name": "token expiration policy",
                        "query": "token expiration",
                        "baseline_matched_rank": 2,
                        "candidate_matched_rank": 1,
                        "baseline_reciprocal_rank": 0.5,
                        "candidate_reciprocal_rank": 1.0,
                    }
                ],
                "regressed_cases": [],
                "unchanged_cases": [],
            }
        ],
        "improvement_gate": {
            "min_improved_cases": 1,
            "total_improved_cases": 1,
            "passed": True,
        },
    }

    assert format_strategy_comparison_summary(output) == "\n".join(
        [
            "RAG strategy comparison",
            "strategy          hit_rate  top_1  mrr",
            "term-frequency    1.00      0.00   0.50",
            "binary-overlap    1.00      1.00   1.00",
            "",
            "Best strategy: binary-overlap (mrr=1.00, top_1=1.00, hit_rate=1.00)",
            "",
            "Baseline strategy: term-frequency",
            "Strategy diagnostics vs baseline:",
            "binary-overlap: improved=1, regressed=0, unchanged=0",
            "  improved:",
            "    - token expiration policy: rank 2 -> 1",
            "",
            "Improvement gate: min_improved_cases=1, total_improved_cases=1, passed=true",
        ]
    )

    