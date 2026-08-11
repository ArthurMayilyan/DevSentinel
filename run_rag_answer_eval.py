import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from rag_answer_eval import (
    RagAnswerEvidence,
    RagAnswerEvalSummary,
    evaluate_rag_answers,
    load_rag_answer_eval_cases_from_json_file,
)
from rag_loader import load_rag_store_from_path


def extractive_answer_builder(
    *,
    query: str,
    evidence: list[RagAnswerEvidence],
) -> str:
    if not evidence:
        return "I do not have enough evidence to answer."

    return evidence[0].text


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run end-to-end RAG answer evaluation.",
    )

    parser.add_argument(
        "--knowledge-path",
        required=True,
        help="Path to a knowledge base file or directory.",
    )

    parser.add_argument(
        "--cases",
        required=True,
        help="Path to a JSON file with RAG answer eval cases.",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of retrieved chunks to provide as answer evidence.",
    )

    parser.add_argument(
        "--min-answer-accuracy",
        type=float,
        default=1.0,
        help="Minimum answer accuracy required for the quality gate.",
    )

    parser.add_argument(
        "--output",
        default=None,
        help="Optional path for JSON eval output.",
    )

    parser.add_argument(
        "--report-output",
        default=None,
        help="Optional path for Markdown eval report.",
    )

    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print a concise text summary instead of full JSON.",
    )

    parser.add_argument(
        "--fail-on-quality-gate",
        action="store_true",
        help="Exit with code 1 when the answer quality gate fails.",
    )

    return parser


def build_answer_quality_gate(
    *,
    summary: RagAnswerEvalSummary,
    min_answer_accuracy: float,
) -> dict[str, Any]:
    if not isinstance(min_answer_accuracy, float):
        raise ValueError("min_answer_accuracy must be a float.")

    if min_answer_accuracy < 0 or min_answer_accuracy > 1:
        raise ValueError("min_answer_accuracy must be between 0 and 1.")

    return {
        "min_answer_accuracy": min_answer_accuracy,
        "actual_answer_accuracy": summary.answer_accuracy,
        "passed": summary.answer_accuracy >= min_answer_accuracy,
    }


def rag_answer_eval_summary_to_dict(
    summary: RagAnswerEvalSummary,
) -> dict[str, Any]:
    return asdict(
        summary,
    )


def build_output(
    *,
    knowledge_path: str,
    cases_path: str,
    top_k: int,
    min_answer_accuracy: float,
    summary: RagAnswerEvalSummary,
) -> dict[str, Any]:
    quality_gate = build_answer_quality_gate(
        summary=summary,
        min_answer_accuracy=min_answer_accuracy,
    )

    return {
        "knowledge_path": knowledge_path,
        "cases": cases_path,
        "top_k": top_k,
        "min_answer_accuracy": min_answer_accuracy,
        "summary": rag_answer_eval_summary_to_dict(
            summary,
        ),
        "quality_gate": quality_gate,
    }


def format_answer_eval_summary(
    output: dict[str, Any],
) -> str:
    summary = output["summary"]
    quality_gate = output["quality_gate"]

    return "\n".join(
        [
            "RAG answer eval",
            f"cases: {summary['total_cases']}",
            f"passed: {summary['passed_cases']}",
            f"failed: {summary['failed_cases']}",
            f"answer_accuracy: {summary['answer_accuracy']:.2f}",
            f"quality_gate: {'passed' if quality_gate['passed'] else 'failed'}",
        ]
    )


def format_answer_eval_markdown_report(
    output: dict[str, Any],
) -> str:
    summary = output["summary"]
    quality_gate = output["quality_gate"]

    lines = [
        "# RAG Answer Eval Report",
        "",
        "## Configuration",
        "",
        f"Knowledge path: `{output['knowledge_path']}`",
        f"Cases path: `{output['cases']}`",
        f"Top K: `{output['top_k']}`",
        f"Min answer accuracy: `{output['min_answer_accuracy']}`",
        "",
        "## Summary",
        "",
        f"Total cases: **{summary['total_cases']}**",
        f"Passed cases: **{summary['passed_cases']}**",
        f"Failed cases: **{summary['failed_cases']}**",
        f"Answer accuracy: **{summary['answer_accuracy']:.2f}**",
        "",
        "## Quality gate",
        "",
        f"Passed: **{str(quality_gate['passed']).lower()}**",
        "",
        "## Cases",
        "",
        "| Case | Passed | Expected answer text | Expected source | Failure reasons |",
        "|---|---:|---|---|---|",
    ]

    for result in summary["results"]:
        failure_reasons = ", ".join(
            result["failure_reasons"],
        )

        lines.append(
            "| "
            f"{result['name']} | "
            f"{str(result['passed']).lower()} | "
            f"{result['expected_answer_contains']} | "
            f"{result['expected_source_contains']} | "
            f"{failure_reasons} |"
        )

    lines.append("")

    return "\n".join(lines)


def should_fail_due_to_answer_quality_gate(
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
    args = parser.parse_args(raw_args)

    store = load_rag_store_from_path(
        path=args.knowledge_path,
    )

    cases = load_rag_answer_eval_cases_from_json_file(
        path=args.cases,
    )

    summary = evaluate_rag_answers(
        store=store,
        cases=cases,
        answer_builder=extractive_answer_builder,
        top_k=args.top_k,
    )

    output = build_output(
        knowledge_path=args.knowledge_path,
        cases_path=args.cases,
        top_k=args.top_k,
        min_answer_accuracy=args.min_answer_accuracy,
        summary=summary,
    )

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(
            json.dumps(
                output,
                indent=2,
            ),
            encoding="utf-8",
        )

    if args.report_output:
        report_output_path = Path(args.report_output)
        report_output_path.write_text(
            format_answer_eval_markdown_report(
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
        "--min-answer-accuracy",
        str(args.min_answer_accuracy),
    ]

    if args.output is not None:
        raw_args.extend(
            [
                "--output",
                args.output,
            ]
        )

    if args.report_output is not None:
        raw_args.extend(
            [
                "--report-output",
                args.report_output,
            ]
        )

    if args.summary_only:
        raw_args.append(
            "--summary-only",
        )

    if args.fail_on_quality_gate:
        raw_args.append(
            "--fail-on-quality-gate",
        )

    output = run_from_args(
        raw_args,
    )

    if args.summary_only:
        print(
            format_answer_eval_summary(
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

    if should_fail_due_to_answer_quality_gate(
        output=output,
        fail_on_quality_gate=args.fail_on_quality_gate,
    ):
        sys.exit(1)


if __name__ == "__main__":
    main()