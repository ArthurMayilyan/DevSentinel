import argparse
import json
from pathlib import Path
from typing import Any

from rag_eval import evaluate_rag_retrieval
from rag_eval_loader import load_rag_retrieval_eval_cases_from_json_file
from rag_loader import load_rag_store_from_path
from rag_retrievers import (
    BinaryOverlapRagRetriever,
    TermFrequencyRagRetriever,
)

RETRIEVAL_STRATEGY_DEFAULT = "default"
RETRIEVAL_STRATEGY_BINARY_OVERLAP = "binary-overlap"
RETRIEVAL_STRATEGY_TERM_FREQUENCY = "term-frequency"

SUPPORTED_RETRIEVAL_STRATEGIES = {
    RETRIEVAL_STRATEGY_DEFAULT,
    RETRIEVAL_STRATEGY_BINARY_OVERLAP,
    RETRIEVAL_STRATEGY_TERM_FREQUENCY,
}


def build_rag_search_engine(
    *,
    store,
    retrieval_strategy: str,
):
    if retrieval_strategy == RETRIEVAL_STRATEGY_DEFAULT:
        return store

    if retrieval_strategy == RETRIEVAL_STRATEGY_BINARY_OVERLAP:
        return BinaryOverlapRagRetriever(
            store=store,
        )

    if retrieval_strategy == RETRIEVAL_STRATEGY_TERM_FREQUENCY:
        return TermFrequencyRagRetriever(
            store=store,
        )    

    raise ValueError(f"Unsupported retrieval strategy: {retrieval_strategy}")

def validate_min_top_1_accuracy(
    min_top_1_accuracy: float | None,
) -> None:
    validate_optional_unit_interval(
        name="min_top_1_accuracy",
        value=min_top_1_accuracy,
    )

def format_rag_eval_summary(
    output: dict[str, Any],
) -> str:
    lines = [
        "RAG retrieval evaluation",
    ]

    if "retrieval_strategy" in output:
        lines.append(
            f"Strategy: {output['retrieval_strategy']}"
        )

    lines.extend(
        [
            f"Total: {output['total_cases']}",
            f"Passed: {output['passed_cases']}",
            f"Failed: {output['failed_cases']}",
            f"Hit rate: {output['hit_rate']:.2f}",
            f"Top-1 accuracy: {output['top_1_accuracy']:.2f}",
            f"MRR: {output['mean_reciprocal_rank']:.2f}",
        ]
    )

    if "min_hit_rate" in output:
        lines.append(
            f"Hit rate threshold: {output['min_hit_rate']:.2f}"
        )
        lines.append(
            "Hit rate threshold passed: "
            f"{str(output['hit_rate_threshold_passed']).lower()}"
        )

    if "min_top_1_accuracy" in output:
        lines.append(
            f"Top-1 accuracy threshold: {output['min_top_1_accuracy']:.2f}"
        )
        lines.append(
            "Top-1 accuracy threshold passed: "
            f"{str(output['top_1_accuracy_threshold_passed']).lower()}"
        )

    if "min_mrr" in output:
        lines.append(
            f"MRR threshold: {output['min_mrr']:.2f}"
        )
        lines.append(
            "MRR threshold passed: "
            f"{str(output['mrr_threshold_passed']).lower()}"
        )

    if "threshold_passed" in output:
        lines.append(
            f"Overall threshold passed: {str(output['threshold_passed']).lower()}"
        )

    failed_results = [
        result
        for result in output.get("results", [])
        if result.get("passed") is False
    ]

    if failed_results:
        lines.append("")
        lines.append("Failed cases:")

        for result in failed_results:
            lines.append(f"- {result['name']}")
            lines.append(f"  query: {result['query']}")
            lines.append(
                f"  expected source: {result['expected_source_contains']}"
            )
            lines.append("  retrieved sources:")

            retrieved_sources = result.get("retrieved_sources", [])

            if retrieved_sources:
                for source in retrieved_sources:
                    lines.append(f"    - {source}")
            else:
                lines.append("    - <none>")

    return "\n".join(lines)

def validate_optional_unit_interval(
    *,
    name: str,
    value: float | None,
) -> None:
    if value is None:
        return

    if not isinstance(value, float):
        raise ValueError(f"{name} must be a float or None.")

    if value < 0.0 or value > 1.0:
        raise ValueError(f"{name} must be between 0.0 and 1.0.")

def validate_min_hit_rate(
    min_hit_rate: float | None,
) -> None:
    validate_optional_unit_interval(
        name="min_hit_rate",
        value=min_hit_rate,
    )


def validate_min_mrr(
    min_mrr: float | None,
) -> None:
    validate_optional_unit_interval(
        name="min_mrr",
        value=min_mrr,
    )    

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate RAG retrieval quality against JSON eval cases.",
    )

    parser.add_argument(
        "--knowledge-path",
        required=True,
        help="Path to a knowledge base file or directory.",
    )

    parser.add_argument(
        "--cases",
        required=True,
        help="Path to a JSON file with RAG retrieval eval cases.",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of retrieved chunks to evaluate per query.",
    )

    parser.add_argument(
        "--output",
        default=None,
        help="Optional path where evaluation summary JSON should be written.",
    )

    parser.add_argument(
        "--min-hit-rate",
        type=float,
        default=None,
        help="Optional minimum acceptable hit rate. Must be between 0.0 and 1.0.",
    )

    parser.add_argument(
        "--min-mrr",
        type=float,
        default=None,
        help="Optional minimum acceptable mean reciprocal rank. Must be between 0.0 and 1.0.",
    )

    parser.add_argument(
        "--min-top-1-accuracy",
        type=float,
        default=None,
        help="Optional minimum acceptable top-1 accuracy. Must be between 0.0 and 1.0.",
    )

    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print a compact human-readable summary instead of full JSON.",
    )    

    parser.add_argument(
        "--retrieval-strategy",
        choices=sorted(SUPPORTED_RETRIEVAL_STRATEGIES),
        default=RETRIEVAL_STRATEGY_DEFAULT,
        help="Retrieval strategy to use for evaluation.",
    )    

    return parser


def run_rag_eval(
    args: argparse.Namespace,
) -> dict[str, Any]:
    validate_min_hit_rate(args.min_hit_rate)
    validate_min_top_1_accuracy(args.min_top_1_accuracy)
    validate_min_mrr(args.min_mrr)

    store = load_rag_store_from_path(
        path=args.knowledge_path,
    )

    search_engine = build_rag_search_engine(
        store=store,
        retrieval_strategy=args.retrieval_strategy,
    )    

    cases = load_rag_retrieval_eval_cases_from_json_file(
        path=args.cases,
    )

    summary = evaluate_rag_retrieval(
        store=search_engine,
        cases=cases,
        top_k=args.top_k,
    )

    output = summary.to_dict()
    output["retrieval_strategy"] = args.retrieval_strategy

    if args.min_hit_rate is not None:
        output["min_hit_rate"] = args.min_hit_rate
        output["threshold_passed"] = summary.hit_rate >= args.min_hit_rate

    threshold_checks = []

    if args.min_hit_rate is not None:
        hit_rate_passed = summary.hit_rate >= args.min_hit_rate
        output["min_hit_rate"] = args.min_hit_rate
        output["hit_rate_threshold_passed"] = hit_rate_passed
        threshold_checks.append(hit_rate_passed)

    if args.min_top_1_accuracy is not None:
        top_1_accuracy_passed = (
            summary.top_1_accuracy >= args.min_top_1_accuracy
        )
        output["min_top_1_accuracy"] = args.min_top_1_accuracy
        output["top_1_accuracy_threshold_passed"] = top_1_accuracy_passed
        threshold_checks.append(top_1_accuracy_passed)

    if args.min_mrr is not None:
        mrr_passed = summary.mean_reciprocal_rank >= args.min_mrr
        output["min_mrr"] = args.min_mrr
        output["mrr_threshold_passed"] = mrr_passed
        threshold_checks.append(mrr_passed)

    if threshold_checks:
        output["threshold_passed"] = all(threshold_checks)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(
            json.dumps(output, indent=2),
            encoding="utf-8",
        )

    return output


def run_rag_eval_from_args(
    raw_args: list[str] | None = None,
) -> dict[str, Any]:
    parser = build_arg_parser()
    args = parser.parse_args(raw_args)

    return run_rag_eval(args)



def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    output = run_rag_eval(args)

    if args.summary_only:
        print(format_rag_eval_summary(output))
    else:
        print(
            json.dumps(
                output,
                indent=2,
            )
        )

    if output.get("threshold_passed") is False:
        raise SystemExit(1)

    
if __name__ == "__main__":
    main()
