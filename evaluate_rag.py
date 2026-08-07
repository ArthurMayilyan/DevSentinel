import argparse
import json
from pathlib import Path
from typing import Any

from rag_eval import evaluate_rag_retrieval
from rag_eval_loader import load_rag_retrieval_eval_cases_from_json_file
from rag_loader import load_rag_store_from_path


def validate_min_hit_rate(
    min_hit_rate: float | None,
) -> None:
    if min_hit_rate is None:
        return

    if not isinstance(min_hit_rate, float):
        raise ValueError("min_hit_rate must be a float or None.")

    if min_hit_rate < 0.0 or min_hit_rate > 1.0:
        raise ValueError("min_hit_rate must be between 0.0 and 1.0.")
    

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

    return parser


def run_rag_eval_from_args(
    raw_args: list[str] | None = None,
) -> dict[str, Any]:
    parser = build_arg_parser()
    args = parser.parse_args(raw_args)

    validate_min_hit_rate(args.min_hit_rate)

    store = load_rag_store_from_path(
        path=args.knowledge_path,
    )

    cases = load_rag_retrieval_eval_cases_from_json_file(
        path=args.cases,
    )

    summary = evaluate_rag_retrieval(
        store=store,
        cases=cases,
        top_k=args.top_k,
    )

    output = summary.to_dict()

    if args.min_hit_rate is not None:
        output["min_hit_rate"] = args.min_hit_rate
        output["threshold_passed"] = summary.hit_rate >= args.min_hit_rate

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(
            json.dumps(output, indent=2),
            encoding="utf-8",
        )

    return output


def main() -> None:
    output = run_rag_eval_from_args()

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