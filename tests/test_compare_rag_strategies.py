import json

from compare_rag_strategies import (
    build_arg_parser,
    format_strategy_comparison_summary,
    run_strategy_comparison_from_args,
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
        ]
    )

    assert args.strategies == [
        "default",
        "term-frequency",
        "binary-overlap",
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
        "results": [
            {
                "retrieval_strategy": "default",
                "hit_rate": 1.0,
                "top_1_accuracy": 0.5,
                "mean_reciprocal_rank": 0.75,
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
            "default           1.00      0.50   0.75",
            "binary-overlap    1.00      1.00   1.00",
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

            