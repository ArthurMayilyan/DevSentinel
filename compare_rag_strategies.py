import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluate_rag import (
    RETRIEVAL_STRATEGY_DEFAULT,
    SUPPORTED_RETRIEVAL_STRATEGIES,
    build_rag_search_engine,
)
from rag_eval import evaluate_rag_retrieval
from rag_eval_loader import load_rag_retrieval_eval_cases_from_json_file
from rag_loader import load_rag_store_from_path


CONFIG_ALLOWED_KEYS = {
    "knowledge_path",
    "cases",
    "strategies",
    "baseline_strategy",
    "top_k",
    "summary_only",
    "output",
    "report_output",
    "max_regressed_cases",
    "min_improved_cases",
    "fail_on_regression_gate",
    "fail_on_improvement_gate",
}


def load_json_config(
    path: str,
) -> dict[str, Any]:
    config_path = Path(path)

    if not config_path.is_file():
        raise ValueError(f"config path must be a file: {path}")

    config = json.loads(
        config_path.read_text(
            encoding="utf-8",
        )
    )

    if not isinstance(config, dict):
        raise ValueError("config file must contain a JSON object.")

    unknown_keys = sorted(
        set(config.keys()) - CONFIG_ALLOWED_KEYS
    )

    if unknown_keys:
        raise ValueError(
            "config contains unsupported keys: "
            + ", ".join(unknown_keys)
        )

    return config


def apply_config_to_args(
    *,
    args: argparse.Namespace,
    config: dict[str, Any],
) -> argparse.Namespace:
    merged = argparse.Namespace(**vars(args))

    for key, value in config.items():
        current_value = getattr(
            merged,
            key,
        )

        if key in {
            "summary_only",
            "fail_on_regression_gate",
            "fail_on_improvement_gate",
        }:
            if current_value is False:
                setattr(
                    merged,
                    key,
                    value,
                )
            continue

        if current_value is None:
            setattr(
                merged,
                key,
                value,
            )

    return merged


def apply_default_args(
    args: argparse.Namespace,
) -> argparse.Namespace:
    merged = argparse.Namespace(**vars(args))

    if merged.strategies is None:
        merged.strategies = [
            RETRIEVAL_STRATEGY_DEFAULT,
        ]

    if merged.top_k is None:
        merged.top_k = 3

    return merged


def validate_comparison_args(
    args: argparse.Namespace,
) -> None:
    if not args.knowledge_path:
        raise ValueError("knowledge_path is required.")

    if not args.cases:
        raise ValueError("cases is required.")

    if type(args.top_k) is not int:
        raise ValueError("top_k must be an integer.")

    if args.top_k <= 0:
        raise ValueError("top_k must be greater than 0.")

    if not isinstance(args.strategies, list) or not args.strategies:
        raise ValueError("strategies must be a non-empty list.")

    unsupported_strategies = sorted(
        set(args.strategies) - SUPPORTED_RETRIEVAL_STRATEGIES
    )

    if unsupported_strategies:
        raise ValueError(
            "unsupported strategies: "
            + ", ".join(unsupported_strategies)
        )


def resolve_comparison_args(
    raw_args: list[str] | None = None,
) -> argparse.Namespace:
    parser = build_arg_parser()
    args = parser.parse_args(raw_args)

    if args.config is not None:
        config = load_json_config(
            args.config,
        )

        args = apply_config_to_args(
            args=args,
            config=config,
        )

    args = apply_default_args(
        args,
    )

    validate_comparison_args(
        args,
    )

    return args


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare RAG retrieval strategies against the same eval cases.",
    )

    parser.add_argument(
        "--config",
        default=None,
        help="Optional JSON config file with comparison arguments.",
    )

    parser.add_argument(
        "--knowledge-path",
        default=None,
        help="Path to a knowledge base file or directory.",
    )

    parser.add_argument(
        "--cases",
        default=None,
        help="Path to a JSON file with RAG retrieval eval cases.",
    )

    parser.add_argument(
        "--strategies",
        nargs="+",
        choices=sorted(SUPPORTED_RETRIEVAL_STRATEGIES),
        default=None,
        help="Retrieval strategies to compare.",
    )

    parser.add_argument(
        "--baseline-strategy",
        choices=sorted(SUPPORTED_RETRIEVAL_STRATEGIES),
        default=None,
        help=(
            "Optional baseline strategy for per-case diagnostics. "
            "If omitted, no baseline diagnostics are produced."
        ),
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Number of retrieved chunks to evaluate per query.",
    )

    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print a compact human-readable comparison instead of full JSON.",
    )

    parser.add_argument(
        "--output",
        default=None,
        help="Optional path where comparison JSON should be written.",
    )

    parser.add_argument(
        "--report-output",
        default=None,
        help="Optional path where a Markdown comparison report should be written.",
    )    

    parser.add_argument(
        "--max-regressed-cases",
        type=int,
        default=None,
        help=(
            "Optional maximum allowed number of regressed cases across all "
            "baseline diagnostics. Requires --baseline-strategy."
        ),
    )    

    parser.add_argument(
        "--fail-on-regression-gate",
        action="store_true",
        help=(
            "Exit with code 1 when the regression gate fails. "
            "Requires --max-regressed-cases."
        ),
    )

    parser.add_argument(
        "--min-improved-cases",
        type=int,
        default=None,
        help=(
            "Optional minimum required number of improved cases across all "
            "baseline diagnostics. Requires --baseline-strategy."
        ),
    )

    parser.add_argument(
        "--fail-on-improvement-gate",
        action="store_true",
        help=(
            "Exit with code 1 when the improvement gate fails. "
            "Requires --min-improved-cases."
        ),
    )

    return parser

def get_case_reciprocal_rank(
    case_result: dict[str, Any],
) -> float:
    reciprocal_rank = case_result.get("reciprocal_rank")

    if reciprocal_rank is None:
        return 0.0

    return float(reciprocal_rank)

def build_case_rank_delta(
    *,
    baseline_case: dict[str, Any],
    candidate_case: dict[str, Any],
) -> dict[str, Any]:
    return {
        "name": candidate_case["name"],
        "query": candidate_case["query"],
        "baseline_matched_rank": baseline_case.get("matched_rank"),
        "candidate_matched_rank": candidate_case.get("matched_rank"),
        "baseline_reciprocal_rank": get_case_reciprocal_rank(baseline_case),
        "candidate_reciprocal_rank": get_case_reciprocal_rank(candidate_case),
    }

def compare_strategy_result_against_baseline(
    *,
    baseline_result: dict[str, Any],
    candidate_result: dict[str, Any],
) -> dict[str, Any]:
    baseline_cases = index_strategy_cases_by_name(
        baseline_result,
    )
    candidate_cases = index_strategy_cases_by_name(
        candidate_result,
    )

    improved_cases = []
    regressed_cases = []
    unchanged_cases = []

    for case_name, baseline_case in baseline_cases.items():
        if case_name not in candidate_cases:
            raise ValueError(
                f"Candidate strategy is missing case result: {case_name}"
            )

        candidate_case = candidate_cases[case_name]

        baseline_rr = get_case_reciprocal_rank(
            baseline_case,
        )
        candidate_rr = get_case_reciprocal_rank(
            candidate_case,
        )

        case_delta = build_case_rank_delta(
            baseline_case=baseline_case,
            candidate_case=candidate_case,
        )

        if candidate_rr > baseline_rr:
            improved_cases.append(case_delta)
        elif candidate_rr < baseline_rr:
            regressed_cases.append(case_delta)
        else:
            unchanged_cases.append(case_delta)

    return {
        "baseline_strategy": baseline_result["retrieval_strategy"],
        "strategy": candidate_result["retrieval_strategy"],
        "improved_count": len(improved_cases),
        "regressed_count": len(regressed_cases),
        "unchanged_count": len(unchanged_cases),
        "improved_cases": improved_cases,
        "regressed_cases": regressed_cases,
        "unchanged_cases": unchanged_cases,
    }

def find_strategy_result(
    *,
    strategy_results: list[dict[str, Any]],
    strategy: str,
) -> dict[str, Any]:
    for strategy_result in strategy_results:
        if strategy_result["retrieval_strategy"] == strategy:
            return strategy_result

    raise ValueError(f"Strategy result not found: {strategy}")

def build_strategy_diagnostics(
    *,
    strategy_results: list[dict[str, Any]],
    baseline_strategy: str,
) -> list[dict[str, Any]]:
    baseline_result = find_strategy_result(
        strategy_results=strategy_results,
        strategy=baseline_strategy,
    )

    diagnostics = []

    for candidate_result in strategy_results:
        if candidate_result["retrieval_strategy"] == baseline_strategy:
            continue

        diagnostics.append(
            compare_strategy_result_against_baseline(
                baseline_result=baseline_result,
                candidate_result=candidate_result,
            )
        )

    return diagnostics


def build_candidate_strategy_decision(
    *,
    diagnostic: dict[str, Any],
    max_regressed_cases: int | None,
    min_improved_cases: int | None,
) -> dict[str, Any]:
    rejection_reasons = []

    if (
        max_regressed_cases is not None
        and diagnostic["regressed_count"] > max_regressed_cases
    ):
        rejection_reasons.append("too_many_regressions")

    if (
        min_improved_cases is not None
        and diagnostic["improved_count"] < min_improved_cases
    ):
        rejection_reasons.append("insufficient_improvements")

    return {
        "strategy": diagnostic["strategy"],
        "baseline_strategy": diagnostic["baseline_strategy"],
        "improved_count": diagnostic["improved_count"],
        "regressed_count": diagnostic["regressed_count"],
        "unchanged_count": diagnostic["unchanged_count"],
        "accepted": len(rejection_reasons) == 0,
        "rejection_reasons": rejection_reasons,
    }


def build_candidate_strategy_decisions(
    *,
    strategy_diagnostics: list[dict[str, Any]],
    max_regressed_cases: int | None,
    min_improved_cases: int | None,
) -> list[dict[str, Any]]:
    return [
        build_candidate_strategy_decision(
            diagnostic=diagnostic,
            max_regressed_cases=max_regressed_cases,
            min_improved_cases=min_improved_cases,
        )
        for diagnostic in strategy_diagnostics
    ]


def select_best_accepted_strategy_result(
    *,
    strategy_results: list[dict[str, Any]],
    candidate_decisions: list[dict[str, Any]],
) -> dict[str, Any] | None:
    accepted_strategies = {
        decision["strategy"]
        for decision in candidate_decisions
        if decision["accepted"]
    }

    accepted_results = [
        result
        for result in strategy_results
        if result["retrieval_strategy"] in accepted_strategies
    ]

    if not accepted_results:
        return None

    return select_best_strategy_result(
        accepted_results,
    )


def build_regression_gate_result(
    *,
    strategy_diagnostics: list[dict[str, Any]],
    max_regressed_cases: int,
) -> dict[str, Any]:
    total_regressed_cases = sum(
        diagnostic["regressed_count"]
        for diagnostic in strategy_diagnostics
    )

    passed = total_regressed_cases <= max_regressed_cases

    return {
        "max_regressed_cases": max_regressed_cases,
        "total_regressed_cases": total_regressed_cases,
        "passed": passed,
    }


def build_improvement_gate_result(
    *,
    strategy_diagnostics: list[dict[str, Any]],
    min_improved_cases: int,
) -> dict[str, Any]:
    total_improved_cases = sum(
        diagnostic["improved_count"]
        for diagnostic in strategy_diagnostics
    )

    passed = total_improved_cases >= min_improved_cases

    return {
        "min_improved_cases": min_improved_cases,
        "total_improved_cases": total_improved_cases,
        "passed": passed,
    }


def build_quality_gate_result(
    *,
    output: dict[str, Any],
) -> dict[str, Any] | None:
    failed_gates = []
    enabled_gates = []

    regression_gate = output.get("regression_gate")
    if regression_gate is not None:
        enabled_gates.append("regression")

        if not regression_gate["passed"]:
            failed_gates.append("regression")

    improvement_gate = output.get("improvement_gate")
    if improvement_gate is not None:
        enabled_gates.append("improvement")

        if not improvement_gate["passed"]:
            failed_gates.append("improvement")

    if not enabled_gates:
        return None

    return {
        "enabled_gates": enabled_gates,
        "failed_gates": failed_gates,
        "passed": len(failed_gates) == 0,
    }


def should_fail_due_to_regression_gate(
    *,
    output: dict[str, Any],
    fail_on_regression_gate: bool,
) -> bool:
    if not fail_on_regression_gate:
        return False

    regression_gate = output.get("regression_gate")

    if regression_gate is None:
        raise ValueError(
            "fail_on_regression_gate requires regression_gate in output."
        )

    return not regression_gate["passed"]


def should_fail_due_to_improvement_gate(
    *,
    output: dict[str, Any],
    fail_on_improvement_gate: bool,
) -> bool:
    if not fail_on_improvement_gate:
        return False

    improvement_gate = output.get("improvement_gate")

    if improvement_gate is None:
        raise ValueError(
            "fail_on_improvement_gate requires improvement_gate in output."
        )

    return not improvement_gate["passed"]


def should_fail_due_to_quality_gate(
    *,
    output: dict[str, Any],
    fail_on_regression_gate: bool,
    fail_on_improvement_gate: bool,
) -> bool:
    should_enforce_quality_gate = (
        fail_on_regression_gate
        or fail_on_improvement_gate
    )

    if not should_enforce_quality_gate:
        return False

    quality_gate = output.get("quality_gate")

    if quality_gate is None:
        raise ValueError(
            "fail-on gate flags require quality_gate in output."
        )

    return not quality_gate["passed"]


def evaluate_strategy(
    *,
    store,
    cases,
    strategy: str,
    top_k: int,
) -> dict[str, Any]:
    search_engine = build_rag_search_engine(
        store=store,
        retrieval_strategy=strategy,
    )

    summary = evaluate_rag_retrieval(
        store=search_engine,
        cases=cases,
        top_k=top_k,
    )

    output = summary.to_dict()
    output["retrieval_strategy"] = strategy

    return output

def select_best_strategy_result(
    strategy_results: list[dict[str, Any]],
) -> dict[str, Any]:
    if not strategy_results:
        raise ValueError("strategy_results must not be empty.")

    return max(
        strategy_results,
        key=lambda result: (
            result["mean_reciprocal_rank"],
            result["top_1_accuracy"],
            result["hit_rate"],
        ),
    )


def format_matched_rank(
    value: Any,
) -> str:
    if value is None:
        return "<missing>"

    return str(value)

def format_markdown_bool(
    value: bool,
) -> str:
    return str(value).lower()


def format_markdown_optional_text(
    value: Any,
) -> str:
    if value is None:
        return "<none>"

    if isinstance(value, list):
        return ",".join(str(item) for item in value)

    return str(value)


def format_markdown_metric(
    value: float,
) -> str:
    return f"{value:.2f}"


def format_strategy_comparison_summary(
    output: dict[str, Any],
) -> str:
    lines = [
        "RAG strategy comparison",
        "strategy          hit_rate  top_1  mrr",
    ]

    for result in output["results"]:
        strategy = result["retrieval_strategy"]
        hit_rate = result["hit_rate"]
        top_1_accuracy = result["top_1_accuracy"]
        mean_reciprocal_rank = result["mean_reciprocal_rank"]

        lines.append(
            f"{strategy:<17} "
            f"{hit_rate:.2f}      "
            f"{top_1_accuracy:.2f}   "
            f"{mean_reciprocal_rank:.2f}"
        )

    if "best_strategy" in output:
        metrics = output["best_strategy_metrics"]

        lines.extend(
            [
                "",
                (
                    f"Best strategy: {output['best_strategy']} "
                    f"(mrr={metrics['mean_reciprocal_rank']:.2f}, "
                    f"top_1={metrics['top_1_accuracy']:.2f}, "
                    f"hit_rate={metrics['hit_rate']:.2f})"
                ),
            ]
        )

    if "strategy_diagnostics" in output:
        lines.extend(
            [
                "",
                f"Baseline strategy: {output['baseline_strategy']}",
                "Strategy diagnostics vs baseline:",
            ]
        )

        for diagnostic in output["strategy_diagnostics"]:
            lines.append(
                f"{diagnostic['strategy']}: "
                f"improved={diagnostic['improved_count']}, "
                f"regressed={diagnostic['regressed_count']}, "
                f"unchanged={diagnostic['unchanged_count']}"
            )

            if diagnostic["improved_cases"]:
                lines.append("  improved:")

                for case_delta in diagnostic["improved_cases"]:
                    lines.append(
                        f"    - {case_delta['name']}: "
                        f"rank {format_matched_rank(case_delta['baseline_matched_rank'])} "
                        f"-> {format_matched_rank(case_delta['candidate_matched_rank'])}"
                    )

            if diagnostic["regressed_cases"]:
                lines.append("  regressed:")

                for case_delta in diagnostic["regressed_cases"]:
                    lines.append(
                        f"    - {case_delta['name']}: "
                        f"rank {format_matched_rank(case_delta['baseline_matched_rank'])} "
                        f"-> {format_matched_rank(case_delta['candidate_matched_rank'])}"
                    )

    if "candidate_decisions" in output:
        lines.extend(
            [
                "",
                "Candidate decisions:",
            ]
        )

        for decision in output["candidate_decisions"]:
            line = (
                f"{decision['strategy']}: "
                f"accepted={str(decision['accepted']).lower()}, "
                f"improved={decision['improved_count']}, "
                f"regressed={decision['regressed_count']}"
            )

            if decision["rejection_reasons"]:
                line += (
                    ", reasons="
                    + ",".join(decision["rejection_reasons"])
                )

            lines.append(line)

        best_accepted_strategy = output.get("best_accepted_strategy")

        lines.extend(
            [
                "",
                (
                    "Best accepted strategy: "
                    f"{best_accepted_strategy if best_accepted_strategy is not None else '<none>'}"
                ),
            ]
        )


    if "regression_gate" in output:
        gate = output["regression_gate"]

        lines.extend(
            [
                "",
                (
                    "Regression gate: "
                    f"max_regressed_cases={gate['max_regressed_cases']}, "
                    f"total_regressed_cases={gate['total_regressed_cases']}, "
                    f"passed={str(gate['passed']).lower()}"
                ),
            ]
        )

    if "improvement_gate" in output:
        gate = output["improvement_gate"]

        lines.extend(
            [
                "",
                (
                    "Improvement gate: "
                    f"min_improved_cases={gate['min_improved_cases']}, "
                    f"total_improved_cases={gate['total_improved_cases']}, "
                    f"passed={str(gate['passed']).lower()}"
                ),
            ]
        )   

    if "quality_gate" in output:
        gate = output["quality_gate"]

        if gate["failed_gates"]:
            failed_gates = ",".join(gate["failed_gates"])

            lines.extend(
                [
                    "",
                    (
                        "Quality gate: "
                        f"passed={str(gate['passed']).lower()}, "
                        f"failed_gates={failed_gates}"
                    ),
                ]
            )
        else:
            lines.extend(
                [
                    "",
                    (
                        "Quality gate: "
                        f"passed={str(gate['passed']).lower()}"
                    ),
                ]
            )             

    return "\n".join(lines)


def format_strategy_comparison_markdown_report(
    output: dict[str, Any],
) -> str:
    lines = [
        "# RAG Strategy Comparison Report",
    ]

    if "run_metadata" in output:
        metadata = output["run_metadata"]

        lines.extend(
            [
                "",
                "## Run metadata",
                "",
                f"Created at UTC: `{metadata['created_at_utc']}`",
                f"Knowledge path: `{metadata['knowledge_path']}`",
                f"Cases path: `{metadata['cases']}`",
                f"Top K: `{metadata['top_k']}`",
                f"Strategies: `{','.join(metadata['strategies'])}`",
            ]
        )

        if metadata["baseline_strategy"] is not None:
            lines.append(
                f"Baseline strategy: `{metadata['baseline_strategy']}`"
            )

        if metadata["max_regressed_cases"] is not None:
            lines.append(
                f"Max regressed cases: `{metadata['max_regressed_cases']}`"
            )

        if metadata["min_improved_cases"] is not None:
            lines.append(
                f"Min improved cases: `{metadata['min_improved_cases']}`"
            )    

    if "input_fingerprints" in output:
        fingerprints = output["input_fingerprints"]

        lines.extend(
            [
                "",
                "## Input fingerprints",
                "",
                "### Knowledge files",
                "",
                "| Relative path | Size bytes | SHA256 |",
                "|---|---:|---|",
            ]
        )

        for fingerprint in fingerprints["knowledge_files"]:
            lines.append(
                "| "
                f"{fingerprint['relative_path']} | "
                f"{fingerprint['size_bytes']} | "
                f"`{fingerprint['sha256']}` |"
            )

        lines.extend(
            [
                "",
                "### Case files",
                "",
                "| Relative path | Size bytes | SHA256 |",
                "|---|---:|---|",
            ]
        )

        for fingerprint in fingerprints["case_files"]:
            lines.append(
                "| "
                f"{fingerprint['relative_path']} | "
                f"{fingerprint['size_bytes']} | "
                f"`{fingerprint['sha256']}` |"
            )

    lines.extend(
        [
            "",
            "## Summary",
            "",
            "| Strategy | Hit rate | Top-1 accuracy | MRR |",
            "|---|---:|---:|---:|",
        ]
    )

    for result in output["results"]:
        lines.append(
            "| "
            f"{result['retrieval_strategy']} | "
            f"{format_markdown_metric(result['hit_rate'])} | "
            f"{format_markdown_metric(result['top_1_accuracy'])} | "
            f"{format_markdown_metric(result['mean_reciprocal_rank'])} |"
        )

    lines.extend(
        [
            "",
            f"Best strategy: **{output['best_strategy']}**",
        ]
    )

    if "best_strategy_metrics" in output:
        metrics = output["best_strategy_metrics"]

        lines.extend(
            [
                "",
                (
                    "Best strategy metrics: "
                    f"MRR={format_markdown_metric(metrics['mean_reciprocal_rank'])}, "
                    f"Top-1={format_markdown_metric(metrics['top_1_accuracy'])}, "
                    f"Hit rate={format_markdown_metric(metrics['hit_rate'])}"
                ),
            ]
        )

    if "baseline_strategy" in output:
        lines.extend(
            [
                "",
                "## Baseline",
                "",
                f"Baseline strategy: **{output['baseline_strategy']}**",
            ]
        )

    if "strategy_diagnostics" in output:
        lines.extend(
            [
                "",
                "## Strategy diagnostics vs baseline",
            ]
        )

        for diagnostic in output["strategy_diagnostics"]:
            lines.extend(
                [
                    "",
                    f"### {diagnostic['strategy']}",
                    "",
                    (
                        f"Improved: **{diagnostic['improved_count']}**, "
                        f"regressed: **{diagnostic['regressed_count']}**, "
                        f"unchanged: **{diagnostic['unchanged_count']}**"
                    ),
                ]
            )

            if diagnostic["improved_cases"]:
                lines.extend(
                    [
                        "",
                        "Improved cases:",
                        "",
                    ]
                )

                for case_delta in diagnostic["improved_cases"]:
                    lines.append(
                        "- "
                        f"{case_delta['name']}: "
                        f"rank {format_matched_rank(case_delta['baseline_matched_rank'])} "
                        f"→ {format_matched_rank(case_delta['candidate_matched_rank'])}"
                    )

            if diagnostic["regressed_cases"]:
                lines.extend(
                    [
                        "",
                        "Regressed cases:",
                        "",
                    ]
                )

                for case_delta in diagnostic["regressed_cases"]:
                    lines.append(
                        "- "
                        f"{case_delta['name']}: "
                        f"rank {format_matched_rank(case_delta['baseline_matched_rank'])} "
                        f"→ {format_matched_rank(case_delta['candidate_matched_rank'])}"
                    )

    if "candidate_decisions" in output:
        lines.extend(
            [
                "",
                "## Candidate decisions",
                "",
                "| Candidate | Accepted | Improved | Regressed | Reasons |",
                "|---|---:|---:|---:|---|",
            ]
        )

        for decision in output["candidate_decisions"]:
            lines.append(
                "| "
                f"{decision['strategy']} | "
                f"{format_markdown_bool(decision['accepted'])} | "
                f"{decision['improved_count']} | "
                f"{decision['regressed_count']} | "
                f"{format_markdown_optional_text(decision['rejection_reasons'])} |"
            )

        lines.extend(
            [
                "",
                (
                    "Best accepted strategy: "
                    f"**{format_markdown_optional_text(output['best_accepted_strategy'])}**"
                ),
            ]
        )

    if "regression_gate" in output:
        gate = output["regression_gate"]

        lines.extend(
            [
                "",
                "## Regression gate",
                "",
                (
                    f"Max regressed cases: **{gate['max_regressed_cases']}**  "
                    f"Total regressed cases: **{gate['total_regressed_cases']}**  "
                    f"Passed: **{format_markdown_bool(gate['passed'])}**"
                ),
            ]
        )

    if "improvement_gate" in output:
        gate = output["improvement_gate"]

        lines.extend(
            [
                "",
                "## Improvement gate",
                "",
                (
                    f"Min improved cases: **{gate['min_improved_cases']}**  "
                    f"Total improved cases: **{gate['total_improved_cases']}**  "
                    f"Passed: **{format_markdown_bool(gate['passed'])}**"
                ),
            ]
        )

    if "quality_gate" in output:
        gate = output["quality_gate"]

        lines.extend(
            [
                "",
                "## Quality gate",
                "",
                f"Passed: **{format_markdown_bool(gate['passed'])}**",
            ]
        )

        if gate["failed_gates"]:
            lines.append(
                "Failed gates: "
                f"**{format_markdown_optional_text(gate['failed_gates'])}**"
            )

    lines.append("")

    return "\n".join(lines)


def normalize_strategy_list(
    *,
    strategies: list[str],
    baseline_strategy: str | None,
) -> list[str]:
    normalized_strategies = []

    if baseline_strategy is not None:
        normalized_strategies.append(baseline_strategy)

    for strategy in strategies:
        if strategy not in normalized_strategies:
            normalized_strategies.append(strategy)

    return normalized_strategies

def index_strategy_cases_by_name(
    strategy_result: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    cases_by_name = {}

    for case_result in strategy_result["results"]:
        case_name = case_result["name"]

        if case_name in cases_by_name:
            raise ValueError(f"Duplicate case name: {case_name}")

        cases_by_name[case_name] = case_result

    return cases_by_name


def validate_regression_gate_args(
    *,
    baseline_strategy: str | None,
    max_regressed_cases: int | None,
    fail_on_regression_gate: bool = False,
    min_improved_cases: int | None = None,
    fail_on_improvement_gate: bool = False,
) -> None:
    if not isinstance(fail_on_regression_gate, bool):
        raise ValueError("fail_on_regression_gate must be a boolean.")

    if not isinstance(fail_on_improvement_gate, bool):
        raise ValueError("fail_on_improvement_gate must be a boolean.")

    if fail_on_regression_gate and max_regressed_cases is None:
        raise ValueError(
            "fail_on_regression_gate requires max_regressed_cases."
        )

    if fail_on_improvement_gate and min_improved_cases is None:
        raise ValueError(
            "fail_on_improvement_gate requires min_improved_cases."
        )

    if max_regressed_cases is not None:
        if baseline_strategy is None:
            raise ValueError(
                "max_regressed_cases requires baseline_strategy."
            )

        if type(max_regressed_cases) is not int:
            raise ValueError("max_regressed_cases must be an integer.")

        if max_regressed_cases < 0:
            raise ValueError(
                "max_regressed_cases must be greater than or equal to 0."
            )

    if min_improved_cases is not None:
        if baseline_strategy is None:
            raise ValueError(
                "min_improved_cases requires baseline_strategy."
            )

        if type(min_improved_cases) is not int:
            raise ValueError("min_improved_cases must be an integer.")

        if min_improved_cases < 0:
            raise ValueError(
                "min_improved_cases must be greater than or equal to 0."
            )

def calculate_file_sha256(
    path: Path,
) -> str:
    if not path.is_file():
        raise ValueError(f"path must be a file: {path}")

    hasher = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def collect_file_fingerprint(
    *,
    path: Path,
    root_path: Path,
) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"path must be a file: {path}")

    return {
        "path": str(path),
        "relative_path": str(path.relative_to(root_path)),
        "size_bytes": path.stat().st_size,
        "sha256": calculate_file_sha256(path),
    }


def collect_path_fingerprints(
    path: str,
) -> list[dict[str, Any]]:
    input_path = Path(path)

    if not input_path.exists():
        raise ValueError(f"path does not exist: {path}")

    if input_path.is_file():
        return [
            collect_file_fingerprint(
                path=input_path,
                root_path=input_path.parent,
            )
        ]

    if input_path.is_dir():
        files = [
            file_path
            for file_path in input_path.rglob("*")
            if file_path.is_file()
        ]

        return [
            collect_file_fingerprint(
                path=file_path,
                root_path=input_path,
            )
            for file_path in sorted(files)
        ]

    raise ValueError(f"path must be a file or directory: {path}")

def build_run_metadata(
    *,
    args: argparse.Namespace,
) -> dict[str, Any]:
    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "knowledge_path": args.knowledge_path,
        "cases": args.cases,
        "top_k": args.top_k,
        "strategies": list(args.strategies),
        "baseline_strategy": args.baseline_strategy,
        "max_regressed_cases": args.max_regressed_cases,
        "min_improved_cases": args.min_improved_cases,
        "fail_on_regression_gate": args.fail_on_regression_gate,
        "fail_on_improvement_gate": args.fail_on_improvement_gate,
    }    

def build_input_fingerprints(
    *,
    knowledge_path: str,
    cases_path: str,
) -> dict[str, Any]:
    return {
        "knowledge_files": collect_path_fingerprints(
            knowledge_path,
        ),
        "case_files": collect_path_fingerprints(
            cases_path,
        ),
    }

def run_strategy_comparison(
    args: argparse.Namespace,
) -> dict[str, Any]:
    validate_regression_gate_args(
        baseline_strategy=args.baseline_strategy,
        max_regressed_cases=args.max_regressed_cases,
        fail_on_regression_gate=args.fail_on_regression_gate,
        min_improved_cases=args.min_improved_cases,
        fail_on_improvement_gate=args.fail_on_improvement_gate,
    )

    run_metadata = build_run_metadata(
        args=args,
    )

    input_fingerprints = build_input_fingerprints(
        knowledge_path=args.knowledge_path,
        cases_path=args.cases,
    )

    store = load_rag_store_from_path(
        path=args.knowledge_path,
    )

    cases = load_rag_retrieval_eval_cases_from_json_file(
        path=args.cases,
    )

    strategy_names = normalize_strategy_list(
        strategies=args.strategies,
        baseline_strategy=args.baseline_strategy,
    )

    run_metadata["strategies"] = strategy_names

    strategy_results = [
        evaluate_strategy(
            store=store,
            cases=cases,
            strategy=strategy,
            top_k=args.top_k,
        )
        for strategy in strategy_names
    ]

    best_result = select_best_strategy_result(
        strategy_results,
    )    

    output = {
        "run_metadata": run_metadata,
        "input_fingerprints": input_fingerprints,
        "knowledge_path": args.knowledge_path,
        "cases": args.cases,
        "top_k": args.top_k,
        "strategies": strategy_names,
        "best_strategy": best_result["retrieval_strategy"],
        "best_strategy_metrics": {
            "hit_rate": best_result["hit_rate"],
            "top_1_accuracy": best_result["top_1_accuracy"],
            "mean_reciprocal_rank": best_result["mean_reciprocal_rank"],
        },
        "results": strategy_results,
    }

    if args.baseline_strategy is not None:
        output["baseline_strategy"] = args.baseline_strategy
        output["strategy_diagnostics"] = build_strategy_diagnostics(
            strategy_results=strategy_results,
            baseline_strategy=args.baseline_strategy,
        )

        output["candidate_decisions"] = build_candidate_strategy_decisions(
            strategy_diagnostics=output["strategy_diagnostics"],
            max_regressed_cases=args.max_regressed_cases,
            min_improved_cases=args.min_improved_cases,
        )

        best_accepted_result = select_best_accepted_strategy_result(
            strategy_results=strategy_results,
            candidate_decisions=output["candidate_decisions"],
        )

        if best_accepted_result is None:
            output["best_accepted_strategy"] = None
            output["best_accepted_strategy_metrics"] = None
        else:
            output["best_accepted_strategy"] = best_accepted_result[
                "retrieval_strategy"
            ]
            output["best_accepted_strategy_metrics"] = {
                "hit_rate": best_accepted_result["hit_rate"],
                "top_1_accuracy": best_accepted_result["top_1_accuracy"],
                "mean_reciprocal_rank": best_accepted_result[
                    "mean_reciprocal_rank"
                ],
            }

        if args.max_regressed_cases is not None:
            output["regression_gate"] = build_regression_gate_result(
                strategy_diagnostics=output["strategy_diagnostics"],
                max_regressed_cases=args.max_regressed_cases,
            )

        if args.min_improved_cases is not None:
            output["improvement_gate"] = build_improvement_gate_result(
                strategy_diagnostics=output["strategy_diagnostics"],
                min_improved_cases=args.min_improved_cases,
            )


    quality_gate = build_quality_gate_result(
        output=output,
    )

    if quality_gate is not None:
        output["quality_gate"] = quality_gate            

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(
            json.dumps(output, indent=2),
            encoding="utf-8",
        )

    if args.report_output:
        report_output_path = Path(args.report_output)
        report_output_path.write_text(
            format_strategy_comparison_markdown_report(output),
            encoding="utf-8",
        )

    return output


def run_strategy_comparison_from_args(
    raw_args: list[str] | None = None,
) -> dict[str, Any]:
    args = resolve_comparison_args(
        raw_args,
    )

    return run_strategy_comparison(
        args,
    )


def main() -> None:
    args = resolve_comparison_args()

    output = run_strategy_comparison(
        args,
    )

    if args.summary_only:
        print(
            format_strategy_comparison_summary(output)
        )
    else:
        print(
            json.dumps(
                output,
                indent=2,
            )
        )

    if should_fail_due_to_quality_gate(
        output=output,
        fail_on_regression_gate=args.fail_on_regression_gate,
        fail_on_improvement_gate=args.fail_on_improvement_gate,
    ):
        sys.exit(1)


if __name__ == "__main__":
    main()