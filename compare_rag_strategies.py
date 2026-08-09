import argparse
import json
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


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare RAG retrieval strategies against the same eval cases.",
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
        "--strategies",
        nargs="+",
        choices=sorted(SUPPORTED_RETRIEVAL_STRATEGIES),
        default=[RETRIEVAL_STRATEGY_DEFAULT],
        help="Retrieval strategies to compare.",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
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

    return parser


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


def run_strategy_comparison_from_args(
    raw_args: list[str] | None = None,
) -> dict[str, Any]:
    parser = build_arg_parser()
    args = parser.parse_args(raw_args)

    store = load_rag_store_from_path(
        path=args.knowledge_path,
    )

    cases = load_rag_retrieval_eval_cases_from_json_file(
        path=args.cases,
    )

    strategy_results = [
        evaluate_strategy(
            store=store,
            cases=cases,
            strategy=strategy,
            top_k=args.top_k,
        )
        for strategy in args.strategies
    ]

    output = {
        "knowledge_path": args.knowledge_path,
        "cases": args.cases,
        "top_k": args.top_k,
        "strategies": args.strategies,
        "results": strategy_results,
    }

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(
            json.dumps(output, indent=2),
            encoding="utf-8",
        )

    return output


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

    return "\n".join(lines)


def run_strategy_comparison(
    args: argparse.Namespace,
) -> dict[str, Any]:
    store = load_rag_store_from_path(
        path=args.knowledge_path,
    )

    cases = load_rag_retrieval_eval_cases_from_json_file(
        path=args.cases,
    )

    strategy_results = [
        evaluate_strategy(
            store=store,
            cases=cases,
            strategy=strategy,
            top_k=args.top_k,
        )
        for strategy in args.strategies
    ]

    output = {
        "knowledge_path": args.knowledge_path,
        "cases": args.cases,
        "top_k": args.top_k,
        "strategies": args.strategies,
        "results": strategy_results,
    }

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(
            json.dumps(output, indent=2),
            encoding="utf-8",
        )

    return output


def run_strategy_comparison_from_args(
    raw_args: list[str] | None = None,
) -> dict[str, Any]:
    parser = build_arg_parser()
    args = parser.parse_args(raw_args)

    return run_strategy_comparison(args)

def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    output = run_strategy_comparison(args)

    if args.summary_only:
        print(format_strategy_comparison_summary(output))
    else:
        print(
            json.dumps(
                output,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()