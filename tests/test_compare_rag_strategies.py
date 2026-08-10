import pytest
import json
import argparse

from compare_rag_strategies import (
    build_arg_parser,
    build_candidate_strategy_decision,
    build_candidate_strategy_decisions,
    build_improvement_gate_result,
    build_quality_gate_result,
    build_regression_gate_result,
    build_strategy_diagnostics,
    compare_strategy_result_against_baseline,
    format_strategy_comparison_markdown_report,
    format_strategy_comparison_summary,
    normalize_strategy_list,
    run_strategy_comparison_from_args,
    select_best_accepted_strategy_result,
    select_best_strategy_result,
    should_fail_due_to_improvement_gate,
    should_fail_due_to_quality_gate,
    should_fail_due_to_regression_gate,
    validate_regression_gate_args,
    build_input_fingerprints,
    build_run_metadata,
    calculate_file_sha256,
    collect_path_fingerprints,
    apply_config_to_args,
    apply_default_args,
    build_arg_parser,
    build_input_fingerprints,
    build_run_metadata,
    load_json_config,
    resolve_comparison_args,
    validate_comparison_args,    
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

    assert args.config is None
    assert args.knowledge_path == "./knowledge_base"
    assert args.cases == "./eval_cases/rag_eval_cases.json"

    # Parser no longer applies these defaults.
    # Defaults are applied by resolve_comparison_args().
    assert args.strategies is None
    assert args.top_k is None

    assert args.baseline_strategy is None
    assert args.summary_only is False
    assert args.output is None
    assert args.report_output is None
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

    assert output["quality_gate"] == {
        "enabled_gates": [
            "regression",
        ],
        "failed_gates": [],
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

    assert output["quality_gate"] == {
        "enabled_gates": [
            "regression",
        ],
        "failed_gates": [
            "regression",
        ],
        "passed": False,
    }    

    assert output["candidate_decisions"] == [
        {
            "strategy": "term-frequency",
            "baseline_strategy": "binary-overlap",
            "improved_count": 0,
            "regressed_count": 2,
            "unchanged_count": 0,
            "accepted": False,
            "rejection_reasons": [
                "too_many_regressions",
            ],
        }
    ]

    assert output["best_accepted_strategy"] is None
    assert output["best_accepted_strategy_metrics"] is None    


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

    assert output["quality_gate"] == {
        "enabled_gates": [
            "improvement",
        ],
        "failed_gates": [],
        "passed": True,
    }    


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

    assert output["quality_gate"] == {
        "enabled_gates": [
            "improvement",
        ],
        "failed_gates": [
            "improvement",
        ],
        "passed": False,
    }    

    assert output["candidate_decisions"] == [
        {
            "strategy": "hybrid-lexical",
            "baseline_strategy": "binary-overlap",
            "improved_count": 0,
            "regressed_count": 0,
            "unchanged_count": 2,
            "accepted": False,
            "rejection_reasons": [
                "insufficient_improvements",
            ],
        }
    ]

    assert output["best_accepted_strategy"] is None
    assert output["best_accepted_strategy_metrics"] is None    


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

def test_build_quality_gate_result_returns_none_when_no_gates_enabled():
    assert build_quality_gate_result(
        output={},
    ) is None

def test_build_quality_gate_result_passes_when_regression_gate_passed():
    quality_gate = build_quality_gate_result(
        output={
            "regression_gate": {
                "passed": True,
            },
        },
    )

    assert quality_gate == {
        "enabled_gates": ["regression"],
        "failed_gates": [],
        "passed": True,
    }

def test_build_quality_gate_result_fails_when_improvement_gate_failed():
    quality_gate = build_quality_gate_result(
        output={
            "improvement_gate": {
                "passed": False,
            },
        },
    )

    assert quality_gate == {
        "enabled_gates": ["improvement"],
        "failed_gates": ["improvement"],
        "passed": False,
    }        

def test_build_quality_gate_result_fails_when_any_gate_failed():
    quality_gate = build_quality_gate_result(
        output={
            "regression_gate": {
                "passed": True,
            },
            "improvement_gate": {
                "passed": False,
            },
        },
    )

    assert quality_gate == {
        "enabled_gates": [
            "regression",
            "improvement",
        ],
        "failed_gates": [
            "improvement",
        ],
        "passed": False,
    }

def test_build_quality_gate_result_passes_when_all_enabled_gates_passed():
    quality_gate = build_quality_gate_result(
        output={
            "regression_gate": {
                "passed": True,
            },
            "improvement_gate": {
                "passed": True,
            },
        },
    )

    assert quality_gate == {
        "enabled_gates": [
            "regression",
            "improvement",
        ],
        "failed_gates": [],
        "passed": True,
    }

def test_should_fail_due_to_quality_gate_returns_false_when_no_fail_flags_enabled():
    output = {
        "quality_gate": {
            "passed": False,
        },
    }

    assert should_fail_due_to_quality_gate(
        output=output,
        fail_on_regression_gate=False,
        fail_on_improvement_gate=False,
    ) is False        

def test_should_fail_due_to_quality_gate_returns_false_when_quality_gate_passed():
    output = {
        "quality_gate": {
            "passed": True,
        },
    }

    assert should_fail_due_to_quality_gate(
        output=output,
        fail_on_regression_gate=True,
        fail_on_improvement_gate=False,
    ) is False


def test_should_fail_due_to_quality_gate_returns_true_when_quality_gate_failed():
    output = {
        "quality_gate": {
            "passed": False,
        },
    }

    assert should_fail_due_to_quality_gate(
        output=output,
        fail_on_regression_gate=False,
        fail_on_improvement_gate=True,
    ) is True    

def test_should_fail_due_to_quality_gate_rejects_missing_quality_gate_when_fail_flag_enabled():
    with pytest.raises(ValueError):
        should_fail_due_to_quality_gate(
            output={},
            fail_on_regression_gate=True,
            fail_on_improvement_gate=False,
        )

def test_run_strategy_comparison_from_args_adds_combined_quality_gate(tmp_path):
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
            "--max-regressed-cases",
            "0",
            "--min-improved-cases",
            "1",
        ]
    )

    assert output["regression_gate"] == {
        "max_regressed_cases": 0,
        "total_regressed_cases": 0,
        "passed": True,
    }

    assert output["improvement_gate"] == {
        "min_improved_cases": 1,
        "total_improved_cases": 2,
        "passed": True,
    }

    assert output["quality_gate"] == {
        "enabled_gates": [
            "regression",
            "improvement",
        ],
        "failed_gates": [],
        "passed": True,
    }

    assert output["candidate_decisions"] == [
        {
            "strategy": "binary-overlap",
            "baseline_strategy": "term-frequency",
            "improved_count": 2,
            "regressed_count": 0,
            "unchanged_count": 0,
            "accepted": True,
            "rejection_reasons": [],
        }
    ]

    assert output["best_accepted_strategy"] == "binary-overlap"
    assert output["best_accepted_strategy_metrics"] == {
        "hit_rate": 1.0,
        "top_1_accuracy": 1.0,
        "mean_reciprocal_rank": 1.0,
    }    


def test_format_strategy_comparison_summary_includes_passing_quality_gate():
    output = {
        "best_strategy": "binary-overlap",
        "best_strategy_metrics": {
            "hit_rate": 1.0,
            "top_1_accuracy": 1.0,
            "mean_reciprocal_rank": 1.0,
        },
        "results": [
            {
                "retrieval_strategy": "binary-overlap",
                "hit_rate": 1.0,
                "top_1_accuracy": 1.0,
                "mean_reciprocal_rank": 1.0,
            },
        ],
        "regression_gate": {
            "max_regressed_cases": 0,
            "total_regressed_cases": 0,
            "passed": True,
        },
        "quality_gate": {
            "enabled_gates": [
                "regression",
            ],
            "failed_gates": [],
            "passed": True,
        },
    }

    assert format_strategy_comparison_summary(output) == "\n".join(
        [
            "RAG strategy comparison",
            "strategy          hit_rate  top_1  mrr",
            "binary-overlap    1.00      1.00   1.00",
            "",
            "Best strategy: binary-overlap (mrr=1.00, top_1=1.00, hit_rate=1.00)",
            "",
            "Regression gate: max_regressed_cases=0, total_regressed_cases=0, passed=true",
            "",
            "Quality gate: passed=true",
        ]
    )

def test_format_strategy_comparison_summary_includes_failed_quality_gate():
    output = {
        "best_strategy": "binary-overlap",
        "best_strategy_metrics": {
            "hit_rate": 1.0,
            "top_1_accuracy": 1.0,
            "mean_reciprocal_rank": 1.0,
        },
        "results": [
            {
                "retrieval_strategy": "binary-overlap",
                "hit_rate": 1.0,
                "top_1_accuracy": 1.0,
                "mean_reciprocal_rank": 1.0,
            },
        ],
        "improvement_gate": {
            "min_improved_cases": 1,
            "total_improved_cases": 0,
            "passed": False,
        },
        "quality_gate": {
            "enabled_gates": [
                "improvement",
            ],
            "failed_gates": [
                "improvement",
            ],
            "passed": False,
        },
    }

    assert format_strategy_comparison_summary(output) == "\n".join(
        [
            "RAG strategy comparison",
            "strategy          hit_rate  top_1  mrr",
            "binary-overlap    1.00      1.00   1.00",
            "",
            "Best strategy: binary-overlap (mrr=1.00, top_1=1.00, hit_rate=1.00)",
            "",
            "Improvement gate: min_improved_cases=1, total_improved_cases=0, passed=false",
            "",
            "Quality gate: passed=false, failed_gates=improvement",
        ]
    )


def test_build_candidate_strategy_decision_accepts_candidate_within_gates():
    diagnostic = {
        "baseline_strategy": "term-frequency",
        "strategy": "binary-overlap",
        "improved_count": 2,
        "regressed_count": 0,
        "unchanged_count": 0,
    }

    decision = build_candidate_strategy_decision(
        diagnostic=diagnostic,
        max_regressed_cases=0,
        min_improved_cases=1,
    )

    assert decision == {
        "strategy": "binary-overlap",
        "baseline_strategy": "term-frequency",
        "improved_count": 2,
        "regressed_count": 0,
        "unchanged_count": 0,
        "accepted": True,
        "rejection_reasons": [],
    }

def test_build_candidate_strategy_decision_rejects_candidate_with_too_many_regressions():
    diagnostic = {
        "baseline_strategy": "binary-overlap",
        "strategy": "term-frequency",
        "improved_count": 0,
        "regressed_count": 2,
        "unchanged_count": 0,
    }

    decision = build_candidate_strategy_decision(
        diagnostic=diagnostic,
        max_regressed_cases=0,
        min_improved_cases=None,
    )

    assert decision["accepted"] is False
    assert decision["rejection_reasons"] == [
        "too_many_regressions",
    ]

def test_build_candidate_strategy_decision_rejects_candidate_with_insufficient_improvements():
    diagnostic = {
        "baseline_strategy": "binary-overlap",
        "strategy": "hybrid-lexical",
        "improved_count": 0,
        "regressed_count": 0,
        "unchanged_count": 2,
    }

    decision = build_candidate_strategy_decision(
        diagnostic=diagnostic,
        max_regressed_cases=None,
        min_improved_cases=1,
    )

    assert decision["accepted"] is False
    assert decision["rejection_reasons"] == [
        "insufficient_improvements",
    ]

def test_build_candidate_strategy_decision_can_reject_for_multiple_reasons():
    diagnostic = {
        "baseline_strategy": "strong-baseline",
        "strategy": "weak-candidate",
        "improved_count": 0,
        "regressed_count": 2,
        "unchanged_count": 0,
    }

    decision = build_candidate_strategy_decision(
        diagnostic=diagnostic,
        max_regressed_cases=0,
        min_improved_cases=1,
    )

    assert decision["accepted"] is False
    assert decision["rejection_reasons"] == [
        "too_many_regressions",
        "insufficient_improvements",
    ]

def test_build_candidate_strategy_decisions_builds_one_decision_per_diagnostic():
    diagnostics = [
        {
            "baseline_strategy": "term-frequency",
            "strategy": "binary-overlap",
            "improved_count": 2,
            "regressed_count": 0,
            "unchanged_count": 0,
        },
        {
            "baseline_strategy": "term-frequency",
            "strategy": "hybrid-lexical",
            "improved_count": 2,
            "regressed_count": 0,
            "unchanged_count": 0,
        },
    ]

    decisions = build_candidate_strategy_decisions(
        strategy_diagnostics=diagnostics,
        max_regressed_cases=0,
        min_improved_cases=1,
    )

    assert [
        decision["strategy"]
        for decision in decisions
    ] == [
        "binary-overlap",
        "hybrid-lexical",
    ]

    assert [
        decision["accepted"]
        for decision in decisions
    ] == [
        True,
        True,
    ]


def test_select_best_accepted_strategy_result_selects_best_among_accepted_candidates():
    strategy_results = [
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
        {
            "retrieval_strategy": "hybrid-lexical",
            "hit_rate": 1.0,
            "top_1_accuracy": 1.0,
            "mean_reciprocal_rank": 1.0,
        },
    ]

    candidate_decisions = [
        {
            "strategy": "binary-overlap",
            "accepted": True,
        },
        {
            "strategy": "hybrid-lexical",
            "accepted": True,
        },
    ]

    best_result = select_best_accepted_strategy_result(
        strategy_results=strategy_results,
        candidate_decisions=candidate_decisions,
    )

    assert best_result["retrieval_strategy"] == "binary-overlap"


def test_select_best_accepted_strategy_result_skips_rejected_candidates():
    strategy_results = [
        {
            "retrieval_strategy": "strong-but-rejected",
            "hit_rate": 1.0,
            "top_1_accuracy": 1.0,
            "mean_reciprocal_rank": 1.0,
        },
        {
            "retrieval_strategy": "weaker-but-accepted",
            "hit_rate": 1.0,
            "top_1_accuracy": 0.5,
            "mean_reciprocal_rank": 0.75,
        },
    ]

    candidate_decisions = [
        {
            "strategy": "strong-but-rejected",
            "accepted": False,
        },
        {
            "strategy": "weaker-but-accepted",
            "accepted": True,
        },
    ]

    best_result = select_best_accepted_strategy_result(
        strategy_results=strategy_results,
        candidate_decisions=candidate_decisions,
    )

    assert best_result["retrieval_strategy"] == "weaker-but-accepted"


def test_select_best_accepted_strategy_result_returns_none_when_no_candidates_accepted():
    strategy_results = [
        {
            "retrieval_strategy": "candidate-a",
            "hit_rate": 1.0,
            "top_1_accuracy": 0.5,
            "mean_reciprocal_rank": 0.75,
        },
    ]

    candidate_decisions = [
        {
            "strategy": "candidate-a",
            "accepted": False,
        },
    ]

    assert select_best_accepted_strategy_result(
        strategy_results=strategy_results,
        candidate_decisions=candidate_decisions,
    ) is None


def test_run_strategy_comparison_from_args_adds_candidate_decisions_for_multiple_candidates(tmp_path):
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
            "--min-improved-cases",
            "1",
        ]
    )

    assert [
        decision["strategy"]
        for decision in output["candidate_decisions"]
    ] == [
        "binary-overlap",
        "hybrid-lexical",
    ]

    assert [
        decision["accepted"]
        for decision in output["candidate_decisions"]
    ] == [
        True,
        True,
    ]

    assert output["best_accepted_strategy"] == "binary-overlap"

def test_format_strategy_comparison_summary_includes_accepted_candidate_decisions():
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
                "improved_count": 2,
                "regressed_count": 0,
                "unchanged_count": 0,
                "improved_cases": [],
                "regressed_cases": [],
                "unchanged_cases": [],
            }
        ],
        "candidate_decisions": [
            {
                "strategy": "binary-overlap",
                "baseline_strategy": "term-frequency",
                "improved_count": 2,
                "regressed_count": 0,
                "unchanged_count": 0,
                "accepted": True,
                "rejection_reasons": [],
            }
        ],
        "best_accepted_strategy": "binary-overlap",
        "best_accepted_strategy_metrics": {
            "hit_rate": 1.0,
            "top_1_accuracy": 1.0,
            "mean_reciprocal_rank": 1.0,
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
            "binary-overlap: improved=2, regressed=0, unchanged=0",
            "",
            "Candidate decisions:",
            "binary-overlap: accepted=true, improved=2, regressed=0",
            "",
            "Best accepted strategy: binary-overlap",
        ]
    )

def test_format_strategy_comparison_summary_includes_rejected_candidate_decisions():
    output = {
        "best_strategy": "binary-overlap",
        "best_strategy_metrics": {
            "hit_rate": 1.0,
            "top_1_accuracy": 1.0,
            "mean_reciprocal_rank": 1.0,
        },
        "baseline_strategy": "binary-overlap",
        "results": [
            {
                "retrieval_strategy": "binary-overlap",
                "hit_rate": 1.0,
                "top_1_accuracy": 1.0,
                "mean_reciprocal_rank": 1.0,
            },
            {
                "retrieval_strategy": "term-frequency",
                "hit_rate": 1.0,
                "top_1_accuracy": 0.0,
                "mean_reciprocal_rank": 0.5,
            },
        ],
        "strategy_diagnostics": [
            {
                "baseline_strategy": "binary-overlap",
                "strategy": "term-frequency",
                "improved_count": 0,
                "regressed_count": 2,
                "unchanged_count": 0,
                "improved_cases": [],
                "regressed_cases": [],
                "unchanged_cases": [],
            }
        ],
        "candidate_decisions": [
            {
                "strategy": "term-frequency",
                "baseline_strategy": "binary-overlap",
                "improved_count": 0,
                "regressed_count": 2,
                "unchanged_count": 0,
                "accepted": False,
                "rejection_reasons": [
                    "too_many_regressions",
                    "insufficient_improvements",
                ],
            }
        ],
        "best_accepted_strategy": None,
        "best_accepted_strategy_metrics": None,
    }

    assert format_strategy_comparison_summary(output) == "\n".join(
        [
            "RAG strategy comparison",
            "strategy          hit_rate  top_1  mrr",
            "binary-overlap    1.00      1.00   1.00",
            "term-frequency    1.00      0.00   0.50",
            "",
            "Best strategy: binary-overlap (mrr=1.00, top_1=1.00, hit_rate=1.00)",
            "",
            "Baseline strategy: binary-overlap",
            "Strategy diagnostics vs baseline:",
            "term-frequency: improved=0, regressed=2, unchanged=0",
            "",
            "Candidate decisions:",
            "term-frequency: accepted=false, improved=0, regressed=2, reasons=too_many_regressions,insufficient_improvements",
            "",
            "Best accepted strategy: <none>",
        ]
    )


def test_compare_rag_strategies_parser_accepts_report_output():
    parser = build_arg_parser()

    args = parser.parse_args(
        [
            "--knowledge-path",
            "./knowledge_base",
            "--cases",
            "./eval_cases/rag_eval_cases.json",
            "--report-output",
            "./rag_strategy_report.md",
        ]
    )

    assert args.report_output == "./rag_strategy_report.md"

def test_format_strategy_comparison_markdown_report_formats_minimal_report():
    output = {
        "best_strategy": "binary-overlap",
        "best_strategy_metrics": {
            "hit_rate": 1.0,
            "top_1_accuracy": 1.0,
            "mean_reciprocal_rank": 1.0,
        },
        "results": [
            {
                "retrieval_strategy": "binary-overlap",
                "hit_rate": 1.0,
                "top_1_accuracy": 1.0,
                "mean_reciprocal_rank": 1.0,
            },
        ],
    }

    assert format_strategy_comparison_markdown_report(output) == "\n".join(
        [
            "# RAG Strategy Comparison Report",
            "",
            "## Summary",
            "",
            "| Strategy | Hit rate | Top-1 accuracy | MRR |",
            "|---|---:|---:|---:|",
            "| binary-overlap | 1.00 | 1.00 | 1.00 |",
            "",
            "Best strategy: **binary-overlap**",
            "",
            "Best strategy metrics: MRR=1.00, Top-1=1.00, Hit rate=1.00",
            "",
        ]
    )

def test_format_strategy_comparison_markdown_report_includes_diagnostics_decisions_and_gates():
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
        "candidate_decisions": [
            {
                "strategy": "binary-overlap",
                "baseline_strategy": "term-frequency",
                "improved_count": 1,
                "regressed_count": 0,
                "unchanged_count": 0,
                "accepted": True,
                "rejection_reasons": [],
            }
        ],
        "best_accepted_strategy": "binary-overlap",
        "best_accepted_strategy_metrics": {
            "hit_rate": 1.0,
            "top_1_accuracy": 1.0,
            "mean_reciprocal_rank": 1.0,
        },
        "regression_gate": {
            "max_regressed_cases": 0,
            "total_regressed_cases": 0,
            "passed": True,
        },
        "improvement_gate": {
            "min_improved_cases": 1,
            "total_improved_cases": 1,
            "passed": True,
        },
        "quality_gate": {
            "enabled_gates": [
                "regression",
                "improvement",
            ],
            "failed_gates": [],
            "passed": True,
        },
    }

    assert format_strategy_comparison_markdown_report(output) == "\n".join(
        [
            "# RAG Strategy Comparison Report",
            "",
            "## Summary",
            "",
            "| Strategy | Hit rate | Top-1 accuracy | MRR |",
            "|---|---:|---:|---:|",
            "| term-frequency | 1.00 | 0.00 | 0.50 |",
            "| binary-overlap | 1.00 | 1.00 | 1.00 |",
            "",
            "Best strategy: **binary-overlap**",
            "",
            "Best strategy metrics: MRR=1.00, Top-1=1.00, Hit rate=1.00",
            "",
            "## Baseline",
            "",
            "Baseline strategy: **term-frequency**",
            "",
            "## Strategy diagnostics vs baseline",
            "",
            "### binary-overlap",
            "",
            "Improved: **1**, regressed: **0**, unchanged: **0**",
            "",
            "Improved cases:",
            "",
            "- token expiration policy: rank 2 → 1",
            "",
            "## Candidate decisions",
            "",
            "| Candidate | Accepted | Improved | Regressed | Reasons |",
            "|---|---:|---:|---:|---|",
            "| binary-overlap | true | 1 | 0 |  |",
            "",
            "Best accepted strategy: **binary-overlap**",
            "",
            "## Regression gate",
            "",
            "Max regressed cases: **0**  Total regressed cases: **0**  Passed: **true**",
            "",
            "## Improvement gate",
            "",
            "Min improved cases: **1**  Total improved cases: **1**  Passed: **true**",
            "",
            "## Quality gate",
            "",
            "Passed: **true**",
            "",
        ]
    )

def test_format_strategy_comparison_markdown_report_includes_failed_quality_gate():
    output = {
        "best_strategy": "binary-overlap",
        "best_strategy_metrics": {
            "hit_rate": 1.0,
            "top_1_accuracy": 1.0,
            "mean_reciprocal_rank": 1.0,
        },
        "results": [
            {
                "retrieval_strategy": "binary-overlap",
                "hit_rate": 1.0,
                "top_1_accuracy": 1.0,
                "mean_reciprocal_rank": 1.0,
            },
        ],
        "quality_gate": {
            "enabled_gates": [
                "improvement",
            ],
            "failed_gates": [
                "improvement",
            ],
            "passed": False,
        },
    }

    assert format_strategy_comparison_markdown_report(output) == "\n".join(
        [
            "# RAG Strategy Comparison Report",
            "",
            "## Summary",
            "",
            "| Strategy | Hit rate | Top-1 accuracy | MRR |",
            "|---|---:|---:|---:|",
            "| binary-overlap | 1.00 | 1.00 | 1.00 |",
            "",
            "Best strategy: **binary-overlap**",
            "",
            "Best strategy metrics: MRR=1.00, Top-1=1.00, Hit rate=1.00",
            "",
            "## Quality gate",
            "",
            "Passed: **false**",
            "Failed gates: **improvement**",
            "",
        ]
    )



def test_run_strategy_comparison_from_args_writes_markdown_report_file(tmp_path):
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
            ]
        ),
        encoding="utf-8",
    )

    report_output_path = tmp_path / "rag_strategy_report.md"

    run_strategy_comparison_from_args(
        [
            "--knowledge-path",
            str(knowledge_path),
            "--cases",
            str(cases_path),
            "--baseline-strategy",
            "term-frequency",
            "--strategies",
            "binary-overlap",
            "--max-regressed-cases",
            "0",
            "--min-improved-cases",
            "1",
            "--report-output",
            str(report_output_path),
        ]
    )

    report = report_output_path.read_text(
        encoding="utf-8",
    )

    assert report.startswith("# RAG Strategy Comparison Report")
    assert "| term-frequency | 1.00 | 0.00 | 0.50 |" in report
    assert "| binary-overlap | 1.00 | 1.00 | 1.00 |" in report
    assert "Best accepted strategy: **binary-overlap**" in report
    assert "Passed: **true**" in report
    assert "## Run metadata" in report
    assert "## Input fingerprints" in report
    assert "security.md" in report
    assert "noisy_rag_eval_cases.json" in report
    assert "SHA256" in report    


def test_calculate_file_sha256_returns_stable_hash(tmp_path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text(
        "hello",
        encoding="utf-8",
    )

    assert (
        calculate_file_sha256(file_path)
        == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e730"
        "43362938b9824"
    )


def test_collect_path_fingerprints_collects_directory_files_sorted(tmp_path):
    knowledge_path = tmp_path / "knowledge"
    knowledge_path.mkdir()

    second = knowledge_path / "b.md"
    second.write_text("second", encoding="utf-8")

    first = knowledge_path / "a.md"
    first.write_text("first", encoding="utf-8")

    fingerprints = collect_path_fingerprints(
        str(knowledge_path),
    )

    assert [
        fingerprint["relative_path"]
        for fingerprint in fingerprints
    ] == [
        "a.md",
        "b.md",
    ]

    assert [
        fingerprint["size_bytes"]
        for fingerprint in fingerprints
    ] == [
        len("first"),
        len("second"),
    ]

    assert all(
        len(fingerprint["sha256"]) == 64
        for fingerprint in fingerprints
    )


def test_collect_path_fingerprints_collects_single_file(tmp_path):
    cases_path = tmp_path / "cases.json"
    cases_path.write_text("[]", encoding="utf-8")

    fingerprints = collect_path_fingerprints(
        str(cases_path),
    )

    assert len(fingerprints) == 1
    assert fingerprints[0]["relative_path"] == "cases.json"
    assert fingerprints[0]["size_bytes"] == 2
    assert len(fingerprints[0]["sha256"]) == 64


def test_build_run_metadata_includes_eval_configuration():
    args = resolve_comparison_args(
        [
            "--knowledge-path",
            "./knowledge_base_noisy",
            "--cases",
            "./eval_cases/noisy_rag_eval_cases.json",
            "--baseline-strategy",
            "term-frequency",
            "--strategies",
            "binary-overlap",
            "--max-regressed-cases",
            "0",
            "--min-improved-cases",
            "1",
            "--fail-on-regression-gate",
            "--fail-on-improvement-gate",
        ]
    )

    metadata = build_run_metadata(
        args=args,
    )

    assert isinstance(metadata["created_at_utc"], str)
    assert metadata["knowledge_path"] == "./knowledge_base_noisy"
    assert metadata["cases"] == "./eval_cases/noisy_rag_eval_cases.json"
    assert metadata["top_k"] == 3
    assert metadata["strategies"] == ["binary-overlap"]
    assert metadata["baseline_strategy"] == "term-frequency"
    assert metadata["max_regressed_cases"] == 0
    assert metadata["min_improved_cases"] == 1
    assert metadata["fail_on_regression_gate"] is True
    assert metadata["fail_on_improvement_gate"] is True


def test_build_input_fingerprints_includes_knowledge_and_case_files(tmp_path):
    knowledge_path = tmp_path / "knowledge"
    knowledge_path.mkdir()

    security = knowledge_path / "security.md"
    security.write_text("security", encoding="utf-8")

    cases_path = tmp_path / "cases.json"
    cases_path.write_text("[]", encoding="utf-8")

    fingerprints = build_input_fingerprints(
        knowledge_path=str(knowledge_path),
        cases_path=str(cases_path),
    )

    assert [
        fingerprint["relative_path"]
        for fingerprint in fingerprints["knowledge_files"]
    ] == [
        "security.md",
    ]

    assert [
        fingerprint["relative_path"]
        for fingerprint in fingerprints["case_files"]
    ] == [
        "cases.json",
    ]


def test_format_strategy_comparison_markdown_report_includes_run_metadata_and_fingerprints():
    output = {
        "run_metadata": {
            "created_at_utc": "2026-08-10T12:00:00+00:00",
            "knowledge_path": "./knowledge_base_noisy",
            "cases": "./eval_cases/noisy_rag_eval_cases.json",
            "top_k": 3,
            "strategies": [
                "term-frequency",
                "binary-overlap",
            ],
            "baseline_strategy": "term-frequency",
            "max_regressed_cases": 0,
            "min_improved_cases": 1,
            "fail_on_regression_gate": False,
            "fail_on_improvement_gate": False,
        },
        "input_fingerprints": {
            "knowledge_files": [
                {
                    "relative_path": "security.md",
                    "size_bytes": 12,
                    "sha256": "a" * 64,
                }
            ],
            "case_files": [
                {
                    "relative_path": "noisy_rag_eval_cases.json",
                    "size_bytes": 34,
                    "sha256": "b" * 64,
                }
            ],
        },
        "best_strategy": "binary-overlap",
        "best_strategy_metrics": {
            "hit_rate": 1.0,
            "top_1_accuracy": 1.0,
            "mean_reciprocal_rank": 1.0,
        },
        "results": [
            {
                "retrieval_strategy": "binary-overlap",
                "hit_rate": 1.0,
                "top_1_accuracy": 1.0,
                "mean_reciprocal_rank": 1.0,
            },
        ],
    }

    report = format_strategy_comparison_markdown_report(output)

    assert "## Run metadata" in report
    assert "Created at UTC: `2026-08-10T12:00:00+00:00`" in report
    assert "Knowledge path: `./knowledge_base_noisy`" in report
    assert "Strategies: `term-frequency,binary-overlap`" in report
    assert "## Input fingerprints" in report
    assert "| security.md | 12 | `" + ("a" * 64) + "` |" in report
    assert "| noisy_rag_eval_cases.json | 34 | `" + ("b" * 64) + "` |" in report


def test_resolve_comparison_args_applies_defaults_for_cli_args():
    args = resolve_comparison_args(
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

def test_apply_default_args_sets_default_strategy_and_top_k():
    args = argparse.Namespace(
        strategies=None,
        top_k=None,
    )

    merged = apply_default_args(
        args,
    )

    assert merged.strategies == ["default"]
    assert merged.top_k == 3

def test_apply_default_args_keeps_existing_strategy_and_top_k():
    args = argparse.Namespace(
        strategies=["binary-overlap"],
        top_k=5,
    )

    merged = apply_default_args(
        args,
    )

    assert merged.strategies == ["binary-overlap"]
    assert merged.top_k == 5


def test_run_strategy_comparison_from_args_applies_default_top_k(tmp_path):
    knowledge_path = tmp_path / "knowledge_base"
    knowledge_path.mkdir()

    security = knowledge_path / "security.md"
    security.write_text(
        "Token expiration policy: tokens must be signed and must expire.",
        encoding="utf-8",
    )

    cases_path = tmp_path / "rag_eval_cases.json"
    cases_path.write_text(
        json.dumps(
            [
                {
                    "name": "token expiration policy",
                    "query": "token expiration",
                    "expected_source_contains": "security.md",
                    "expected_text_contains": "Token expiration policy",
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
        ]
    )

    assert output["top_k"] == 3
    assert output["strategies"] == ["default"]

def test_compare_rag_strategies_parser_accepts_config():
    parser = build_arg_parser()

    args = parser.parse_args(
        [
            "--config",
            "./eval_configs/rag_strategy_noisy.json",
        ]
    )

    assert args.config == "./eval_configs/rag_strategy_noisy.json"
    assert args.knowledge_path is None
    assert args.cases is None                                                            


def test_load_json_config_loads_config_object(tmp_path):
    config_path = tmp_path / "rag_eval_config.json"
    config_path.write_text(
        json.dumps(
            {
                "knowledge_path": "./knowledge_base_noisy",
                "cases": "./eval_cases/noisy_rag_eval_cases.json",
                "strategies": [
                    "binary-overlap",
                ],
            }
        ),
        encoding="utf-8",
    )

    assert load_json_config(
        str(config_path),
    ) == {
        "knowledge_path": "./knowledge_base_noisy",
        "cases": "./eval_cases/noisy_rag_eval_cases.json",
        "strategies": [
            "binary-overlap",
        ],
    }

def test_load_json_config_rejects_unknown_keys(tmp_path):
    config_path = tmp_path / "rag_eval_config.json"
    config_path.write_text(
        json.dumps(
            {
                "knowledge_path": "./knowledge_base_noisy",
                "cases": "./eval_cases/noisy_rag_eval_cases.json",
                "baseline_stategy": "term-frequency",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_json_config(
            str(config_path),
        )

def test_apply_config_to_args_fills_missing_values_from_config():
    args = argparse.Namespace(
        config="./config.json",
        knowledge_path=None,
        cases=None,
        strategies=None,
        baseline_strategy=None,
        top_k=None,
        summary_only=False,
        output=None,
        report_output=None,
        max_regressed_cases=None,
        min_improved_cases=None,
        fail_on_regression_gate=False,
        fail_on_improvement_gate=False,
    )

    merged = apply_config_to_args(
        args=args,
        config={
            "knowledge_path": "./knowledge_base_noisy",
            "cases": "./eval_cases/noisy_rag_eval_cases.json",
            "strategies": [
                "binary-overlap",
            ],
            "baseline_strategy": "term-frequency",
            "top_k": 5,
            "summary_only": True,
            "max_regressed_cases": 0,
            "min_improved_cases": 1,
            "fail_on_regression_gate": True,
            "fail_on_improvement_gate": True,
        },
    )

    assert merged.knowledge_path == "./knowledge_base_noisy"
    assert merged.cases == "./eval_cases/noisy_rag_eval_cases.json"
    assert merged.strategies == ["binary-overlap"]
    assert merged.baseline_strategy == "term-frequency"
    assert merged.top_k == 5
    assert merged.summary_only is True
    assert merged.max_regressed_cases == 0
    assert merged.min_improved_cases == 1
    assert merged.fail_on_regression_gate is True
    assert merged.fail_on_improvement_gate is True


def test_apply_config_to_args_keeps_cli_values_over_config_values():
    args = argparse.Namespace(
        config="./config.json",
        knowledge_path="./cli_knowledge",
        cases="./cli_cases.json",
        strategies=[
            "hybrid-lexical",
        ],
        baseline_strategy="binary-overlap",
        top_k=10,
        summary_only=True,
        output="./cli.json",
        report_output="./cli.md",
        max_regressed_cases=1,
        min_improved_cases=2,
        fail_on_regression_gate=True,
        fail_on_improvement_gate=True,
    )

    merged = apply_config_to_args(
        args=args,
        config={
            "knowledge_path": "./config_knowledge",
            "cases": "./config_cases.json",
            "strategies": [
                "binary-overlap",
            ],
            "baseline_strategy": "term-frequency",
            "top_k": 3,
            "summary_only": False,
            "output": "./config.json",
            "report_output": "./config.md",
            "max_regressed_cases": 0,
            "min_improved_cases": 1,
            "fail_on_regression_gate": False,
            "fail_on_improvement_gate": False,
        },
    )

    assert merged.knowledge_path == "./cli_knowledge"
    assert merged.cases == "./cli_cases.json"
    assert merged.strategies == ["hybrid-lexical"]
    assert merged.baseline_strategy == "binary-overlap"
    assert merged.top_k == 10
    assert merged.summary_only is True
    assert merged.output == "./cli.json"
    assert merged.report_output == "./cli.md"
    assert merged.max_regressed_cases == 1
    assert merged.min_improved_cases == 2
    assert merged.fail_on_regression_gate is True
    assert merged.fail_on_improvement_gate is True


def test_validate_comparison_args_rejects_missing_knowledge_path():
    args = argparse.Namespace(
        knowledge_path=None,
        cases="./cases.json",
        top_k=3,
        strategies=[
            "default",
        ],
    )

    with pytest.raises(ValueError):
        validate_comparison_args(args)


def test_validate_comparison_args_rejects_missing_cases():
    args = argparse.Namespace(
        knowledge_path="./knowledge",
        cases=None,
        top_k=3,
        strategies=[
            "default",
        ],
    )

    with pytest.raises(ValueError):
        validate_comparison_args(args)


def test_validate_comparison_args_rejects_non_integer_top_k():
    args = argparse.Namespace(
        knowledge_path="./knowledge",
        cases="./cases.json",
        top_k=None,
        strategies=[
            "default",
        ],
    )

    with pytest.raises(ValueError):
        validate_comparison_args(args)


def test_validate_comparison_args_rejects_non_positive_top_k():
    args = argparse.Namespace(
        knowledge_path="./knowledge",
        cases="./cases.json",
        top_k=0,
        strategies=[
            "default",
        ],
    )

    with pytest.raises(ValueError):
        validate_comparison_args(args)


def test_validate_comparison_args_rejects_unsupported_strategy_from_config():
    args = argparse.Namespace(
        knowledge_path="./knowledge",
        cases="./cases.json",
        top_k=3,
        strategies=[
            "unknown-strategy",
        ],
    )

    with pytest.raises(ValueError):
        validate_comparison_args(args)


def test_resolve_comparison_args_loads_config_file(tmp_path):
    config_path = tmp_path / "rag_eval_config.json"
    config_path.write_text(
        json.dumps(
            {
                "knowledge_path": "./knowledge_base_noisy",
                "cases": "./eval_cases/noisy_rag_eval_cases.json",
                "strategies": [
                    "binary-overlap",
                    "hybrid-lexical",
                ],
                "baseline_strategy": "term-frequency",
                "top_k": 5,
                "summary_only": True,
                "max_regressed_cases": 0,
                "min_improved_cases": 1,
            }
        ),
        encoding="utf-8",
    )

    args = resolve_comparison_args(
        [
            "--config",
            str(config_path),
        ]
    )

    assert args.knowledge_path == "./knowledge_base_noisy"
    assert args.cases == "./eval_cases/noisy_rag_eval_cases.json"
    assert args.strategies == [
        "binary-overlap",
        "hybrid-lexical",
    ]
    assert args.baseline_strategy == "term-frequency"
    assert args.top_k == 5
    assert args.summary_only is True
    assert args.max_regressed_cases == 0
    assert args.min_improved_cases == 1


def test_resolve_comparison_args_allows_cli_to_override_config(tmp_path):
    config_path = tmp_path / "rag_eval_config.json"
    config_path.write_text(
        json.dumps(
            {
                "knowledge_path": "./config_knowledge",
                "cases": "./config_cases.json",
                "strategies": [
                    "binary-overlap",
                ],
                "baseline_strategy": "term-frequency",
                "top_k": 3,
            }
        ),
        encoding="utf-8",
    )

    args = resolve_comparison_args(
        [
            "--config",
            str(config_path),
            "--knowledge-path",
            "./cli_knowledge",
            "--cases",
            "./cli_cases.json",
            "--strategies",
            "hybrid-lexical",
            "--top-k",
            "7",
        ]
    )

    assert args.knowledge_path == "./cli_knowledge"
    assert args.cases == "./cli_cases.json"
    assert args.strategies == [
        "hybrid-lexical",
    ]
    assert args.top_k == 7


def test_run_strategy_comparison_from_args_runs_from_config_file(tmp_path):
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

    report_output_path = tmp_path / "rag_strategy_report.md"

    config_path = tmp_path / "rag_eval_config.json"
    config_path.write_text(
        json.dumps(
            {
                "knowledge_path": str(knowledge_path),
                "cases": str(cases_path),
                "strategies": [
                    "binary-overlap",
                    "hybrid-lexical",
                ],
                "baseline_strategy": "term-frequency",
                "top_k": 3,
                "max_regressed_cases": 0,
                "min_improved_cases": 1,
                "summary_only": True,
                "report_output": str(report_output_path),
            }
        ),
        encoding="utf-8",
    )

    output = run_strategy_comparison_from_args(
        [
            "--config",
            str(config_path),
        ]
    )

    assert output["strategies"] == [
        "term-frequency",
        "binary-overlap",
        "hybrid-lexical",
    ]
    assert output["top_k"] == 3
    assert output["best_strategy"] == "binary-overlap"
    assert output["quality_gate"] == {
        "enabled_gates": [
            "regression",
            "improvement",
        ],
        "failed_gates": [],
        "passed": True,
    }

    assert report_output_path.is_file()


