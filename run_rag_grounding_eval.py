import argparse
import json
import sys
from pathlib import Path
from typing import Any

from rag_grounding_eval import (
    evaluate_rag_grounding,
    load_rag_grounding_eval_cases_from_json_file,
    rag_grounding_eval_summary_to_dict,
)
from rag_loader import load_rag_store_from_path
from rag_pipeline import run_rag_pipeline
from rag_strategy_factory import (
    RETRIEVAL_STRATEGY_DEFAULT,
    SUPPORTED_RETRIEVAL_STRATEGIES,
    build_rag_search_engine_for_strategy,
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run RAG grounding evaluation.",
    )

    parser.add_argument(
        "--knowledge-path",
        required=True,
    )

    parser.add_argument(
        "--cases",
        required=True,
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
    )

    parser.add_argument(
        "--strategy",
        choices=sorted(SUPPORTED_RETRIEVAL_STRATEGIES),
        default=RETRIEVAL_STRATEGY_DEFAULT,
    )

    parser.add_argument(
        "--min-grounding-accuracy",
        type=float,
        default=1.0,
    )

    parser.add_argument(
        "--output",
        default=None,
    )

    parser.add_argument(
        "--report-output",
        default=None,
    )

    parser.add_argument(
        "--summary-only",
        action="store_true",
    )

    parser.add_argument(
        "--fail-on-quality-gate",
        action="store_true",
    )

    return parser


def build_grounding_quality_gate(
    *,
    summary: dict[str, Any],
    min_grounding_accuracy: float,
) -> dict[str, Any]:
    if min_grounding_accuracy < 0 or min_grounding_accuracy > 1:
        raise ValueError("min_grounding_accuracy must be between 0 and 1.")

    actual_grounding_accuracy = summary["grounding_accuracy"]

    return {
        "min_grounding_accuracy": min_grounding_accuracy,
        "actual_grounding_accuracy": actual_grounding_accuracy,
        "passed": actual_grounding_accuracy >= min_grounding_accuracy,
    }


def build_output(
    *,
    knowledge_path: str,
    cases_path: str,
    top_k: int,
    strategy: str,
    min_grounding_accuracy: float,
    summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "knowledge_path": knowledge_path,
        "cases": cases_path,
        "top_k": top_k,
        "strategy": strategy,
        "min_grounding_accuracy": min_grounding_accuracy,
        "summary": summary,
        "quality_gate": build_grounding_quality_gate(
            summary=summary,
            min_grounding_accuracy=min_grounding_accuracy,
        ),
    }


def format_grounding_eval_summary(
    output: dict[str, Any],
) -> str:
    summary = output["summary"]
    quality_gate = output["quality_gate"]

    return "\n".join(
        [
            "RAG grounding eval",
            f"strategy: {output['strategy']}",
            f"cases: {summary['total_cases']}",
            f"passed: {summary['passed_cases']}",
            f"failed: {summary['failed_cases']}",
            f"grounding_accuracy: {summary['grounding_accuracy']:.2f}",
            f"quality_gate: {'passed' if quality_gate['passed'] else 'failed'}",
        ]
    )


def format_grounding_eval_markdown_report(
    output: dict[str, Any],
) -> str:
    summary = output["summary"]

    lines = [
        "# RAG Grounding Eval Report",
        "",
        "## Configuration",
        "",
        f"Knowledge path: `{output['knowledge_path']}`",
        f"Cases path: `{output['cases']}`",
        f"Top K: `{output['top_k']}`",
        f"Strategy: `{output['strategy']}`",
        f"Min grounding accuracy: `{output['min_grounding_accuracy']}`",
        "",
        "## Summary",
        "",
        f"Grounding accuracy: **{summary['grounding_accuracy']:.2f}**",
        f"Passed cases: **{summary['passed_cases']}**",
        f"Failed cases: **{summary['failed_cases']}**",
        "",
        "## Cases",
        "",
        "| Case | Passed | Failures |",
        "|---|---:|---|",
    ]

    for result in summary["results"]:
        failures = "; ".join(
            result["failure_reasons"],
        )

        lines.append(
            f"| {result['name']} | {str(result['passed']).lower()} | {failures} |"
        )

    return "\n".join(
        lines,
    )


def should_fail_due_to_grounding_quality_gate(
    *,
    output: dict[str, Any],
    fail_on_quality_gate: bool,
) -> bool:
    if not fail_on_quality_gate:
        return False

    return not output["quality_gate"]["passed"]


def run_from_args(
    raw_args: list[str] | None = None,
) -> dict[str, Any]:
    parser = build_arg_parser()
    args = parser.parse_args(
        raw_args,
    )

    store = load_rag_store_from_path(
        path=args.knowledge_path,
    )

    search_engine = build_rag_search_engine_for_strategy(
        store=store,
        strategy=args.strategy,
    )

    cases = load_rag_grounding_eval_cases_from_json_file(
        path=args.cases,
    )

    results_by_case_name = {}

    for case in cases:
        results_by_case_name[case.name] = run_rag_pipeline(
            store=search_engine,
            query=case.query,
            top_k=args.top_k,
        )

    summary = rag_grounding_eval_summary_to_dict(
        evaluate_rag_grounding(
            cases=cases,
            results_by_case_name=results_by_case_name,
        )
    )

    output = build_output(
        knowledge_path=args.knowledge_path,
        cases_path=args.cases,
        top_k=args.top_k,
        strategy=args.strategy,
        min_grounding_accuracy=args.min_grounding_accuracy,
        summary=summary,
    )

    if args.output:
        output_path = Path(
            args.output,
        )
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        output_path.write_text(
            json.dumps(
                output,
                indent=2,
            ),
            encoding="utf-8",
        )

    if args.report_output:
        report_output_path = Path(
            args.report_output,
        )
        report_output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        report_output_path.write_text(
            format_grounding_eval_markdown_report(
                output,
            ),
            encoding="utf-8",
        )

    return output


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    raw_args = [
        "--knowledge-path",
        args.knowledge_path,
        "--cases",
        args.cases,
        "--top-k",
        str(args.top_k),
        "--strategy",
        args.strategy,
        "--min-grounding-accuracy",
        str(args.min_grounding_accuracy),
    ]

    if args.output:
        raw_args.extend(
            [
                "--output",
                args.output,
            ]
        )

    if args.report_output:
        raw_args.extend(
            [
                "--report-output",
                args.report_output,
            ]
        )

    output = run_from_args(
        raw_args,
    )

    if args.summary_only:
        print(
            format_grounding_eval_summary(
                output,
            )
        )
    else:
        print(
            json.dumps(
                output,
                indent=2,
            )
        )

    if should_fail_due_to_grounding_quality_gate(
        output=output,
        fail_on_quality_gate=args.fail_on_quality_gate,
    ):
        sys.exit(1)


if __name__ == "__main__":
    main()