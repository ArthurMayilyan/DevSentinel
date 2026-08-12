import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from run_rag_answer_eval import run_from_args as run_answer_eval_from_args
from run_rag_eval_profiles import (
    discover_profile_configs,
    run_profile_configs,
    write_suite_artifacts as write_retrieval_suite_artifacts,
)

ALLOWED_SUITE_CONFIG_KEYS = {
    "retrieval",
    "answer",
}

ALLOWED_RETRIEVAL_CONFIG_KEYS = {
    "config_dir",
}

ALLOWED_ANSWER_CONFIG_KEYS = {
    "knowledge_path",
    "cases",
    "top_k",
    "min_answer_accuracy",
}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the complete eval suite.",
    )

    parser.add_argument(
        "--config",
        required=True,
        help="Path to eval suite JSON config.",
    )

    parser.add_argument(
        "--artifacts-dir",
        default="./eval_suite_artifacts",
        help="Directory where suite artifacts should be written.",
    )

    parser.add_argument(
        "--github-step-summary",
        action="store_true",
        help="Write suite Markdown summary to GitHub Actions step summary.",
    )

    parser.add_argument(
        "--fail-on-quality-gate",
        action="store_true",
        help="Exit with code 1 when any suite quality gate fails.",
    )

    return parser


def load_eval_suite_config(
    path: str,
) -> dict[str, Any]:
    config_path = Path(path)

    if not config_path.is_file():
        raise ValueError(f"suite config path must be a file: {path}")

    config = json.loads(
        config_path.read_text(
            encoding="utf-8",
        )
    )

    if not isinstance(config, dict):
        raise ValueError("suite config must contain a JSON object.")

    unknown_keys = sorted(
        set(config.keys()) - ALLOWED_SUITE_CONFIG_KEYS
    )

    if unknown_keys:
        raise ValueError(
            "suite config contains unsupported keys: "
            + ", ".join(unknown_keys)
        )

    if "retrieval" not in config:
        raise ValueError("suite config must contain retrieval section.")

    if "answer" not in config:
        raise ValueError("suite config must contain answer section.")

    validate_retrieval_suite_config(
        config["retrieval"],
    )

    validate_answer_suite_config(
        config["answer"],
    )

    return config


def validate_retrieval_suite_config(
    config: Any,
) -> None:
    if not isinstance(config, dict):
        raise ValueError("retrieval config must be an object.")

    unknown_keys = sorted(
        set(config.keys()) - ALLOWED_RETRIEVAL_CONFIG_KEYS
    )

    if unknown_keys:
        raise ValueError(
            "retrieval config contains unsupported keys: "
            + ", ".join(unknown_keys)
        )

    if not config.get("config_dir"):
        raise ValueError("retrieval config must contain config_dir.")


def validate_answer_suite_config(
    config: Any,
) -> None:
    if not isinstance(config, dict):
        raise ValueError("answer config must be an object.")

    unknown_keys = sorted(
        set(config.keys()) - ALLOWED_ANSWER_CONFIG_KEYS
    )

    if unknown_keys:
        raise ValueError(
            "answer config contains unsupported keys: "
            + ", ".join(unknown_keys)
        )

    if not config.get("knowledge_path"):
        raise ValueError("answer config must contain knowledge_path.")

    if not config.get("cases"):
        raise ValueError("answer config must contain cases.")

    top_k = config.get(
        "top_k",
        3,
    )

    if type(top_k) is not int:
        raise ValueError("answer top_k must be an integer.")

    if top_k <= 0:
        raise ValueError("answer top_k must be greater than 0.")

    min_answer_accuracy = config.get(
        "min_answer_accuracy",
        1.0,
    )

    if type(min_answer_accuracy) not in {
        int,
        float,
    }:
        raise ValueError("min_answer_accuracy must be a number.")

    if min_answer_accuracy < 0 or min_answer_accuracy > 1:
        raise ValueError("min_answer_accuracy must be between 0 and 1.")


def run_retrieval_suite(
    *,
    config: dict[str, Any],
    artifacts_dir: Path,
) -> dict[str, Any]:
    config_paths = discover_profile_configs(
        config["config_dir"],
    )

    summary = run_profile_configs(
        config_paths,
        artifacts_dir=artifacts_dir,
    )

    write_retrieval_suite_artifacts(
        summary=summary,
        artifacts_dir=artifacts_dir,
    )

    return summary


def run_answer_suite(
    *,
    config: dict[str, Any],
    artifacts_dir: Path,
) -> dict[str, Any]:
    output_path = artifacts_dir / "result.json"
    report_output_path = artifacts_dir / "report.md"

    raw_args = [
        "--knowledge-path",
        config["knowledge_path"],
        "--cases",
        config["cases"],
        "--top-k",
        str(
            config.get(
                "top_k",
                3,
            )
        ),
        "--min-answer-accuracy",
        str(
            config.get(
                "min_answer_accuracy",
                1.0,
            )
        ),
        "--output",
        str(output_path),
        "--report-output",
        str(report_output_path),
    ]

    return run_answer_eval_from_args(
        raw_args,
    )


def build_eval_suite_summary(
    *,
    retrieval_summary: dict[str, Any],
    answer_output: dict[str, Any],
) -> dict[str, Any]:
    retrieval_passed = retrieval_summary["passed"]
    answer_passed = answer_output["quality_gate"]["passed"]

    return {
        "passed": retrieval_passed and answer_passed,
        "retrieval": {
            "passed": retrieval_passed,
            "failed_profiles": retrieval_summary["failed_profiles"],
            "profiles": retrieval_summary["profiles"],
        },
        "answer": {
            "passed": answer_passed,
            "answer_accuracy": answer_output["summary"]["answer_accuracy"],
            "passed_cases": answer_output["summary"]["passed_cases"],
            "failed_cases": answer_output["summary"]["failed_cases"],
            "total_cases": answer_output["summary"]["total_cases"],
            "quality_gate": answer_output["quality_gate"],
        },
    }


def format_eval_suite_summary(
    summary: dict[str, Any],
) -> str:
    return "\n".join(
        [
            "Eval suite",
            f"overall: {'passed' if summary['passed'] else 'failed'}",
            f"retrieval: {'passed' if summary['retrieval']['passed'] else 'failed'}",
            f"answer: {'passed' if summary['answer']['passed'] else 'failed'}",
            f"answer_accuracy: {summary['answer']['answer_accuracy']:.2f}",
        ]
    )


def format_eval_suite_markdown_summary(
    summary: dict[str, Any],
) -> str:
    lines = [
        "# Eval Suite Summary",
        "",
        f"Overall: **{'passed' if summary['passed'] else 'failed'}**",
        "",
        "## Retrieval eval",
        "",
        f"Passed: **{str(summary['retrieval']['passed']).lower()}**",
        "",
        "| Profile | Quality gate | Best accepted strategy |",
        "|---|---|---|",
    ]

    for profile in summary["retrieval"]["profiles"]:
        lines.append(
            "| "
            f"{profile['profile']} | "
            f"{profile['quality_gate_status']} | "
            f"{profile['best_accepted_strategy']} |"
        )

    lines.extend(
        [
            "",
            "## Answer eval",
            "",
            f"Passed: **{str(summary['answer']['passed']).lower()}**",
            f"Total cases: **{summary['answer']['total_cases']}**",
            f"Passed cases: **{summary['answer']['passed_cases']}**",
            f"Failed cases: **{summary['answer']['failed_cases']}**",
            f"Answer accuracy: **{summary['answer']['answer_accuracy']:.2f}**",
            "",
        ]
    )

    if summary["retrieval"]["failed_profiles"]:
        lines.extend(
            [
                "Failed retrieval profiles: "
                + ", ".join(summary["retrieval"]["failed_profiles"]),
                "",
            ]
        )

    return "\n".join(lines)


def write_eval_suite_artifacts(
    *,
    summary: dict[str, Any],
    artifacts_dir: Path,
) -> None:
    artifacts_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary_json_path = artifacts_dir / "suite_summary.json"
    summary_json_path.write_text(
        json.dumps(
            summary,
            indent=2,
        ),
        encoding="utf-8",
    )

    summary_markdown_path = artifacts_dir / "suite_summary.md"
    summary_markdown_path.write_text(
        format_eval_suite_markdown_summary(
            summary,
        ),
        encoding="utf-8",
    )


def write_github_step_summary(
    *,
    summary: dict[str, Any],
    env: dict[str, str] | None = None,
) -> bool:
    if env is None:
        env = dict(os.environ)

    summary_path = env.get("GITHUB_STEP_SUMMARY")

    if not summary_path:
        return False

    path = Path(summary_path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        format_eval_suite_markdown_summary(
            summary,
        ),
        encoding="utf-8",
    )

    return True


def should_fail_due_to_eval_suite_quality_gate(
    *,
    summary: dict[str, Any],
    fail_on_quality_gate: bool,
) -> bool:
    if not fail_on_quality_gate:
        return False

    return not summary["passed"]


def run_from_args(
    raw_args: list[str] | None = None,
) -> dict[str, Any]:
    parser = build_arg_parser()
    args = parser.parse_args(raw_args)

    config = load_eval_suite_config(
        args.config,
    )

    artifacts_dir = Path(
        args.artifacts_dir,
    )

    retrieval_artifacts_dir = artifacts_dir / "retrieval"
    answer_artifacts_dir = artifacts_dir / "answer"

    retrieval_summary = run_retrieval_suite(
        config=config["retrieval"],
        artifacts_dir=retrieval_artifacts_dir,
    )

    answer_output = run_answer_suite(
        config=config["answer"],
        artifacts_dir=answer_artifacts_dir,
    )

    summary = build_eval_suite_summary(
        retrieval_summary=retrieval_summary,
        answer_output=answer_output,
    )

    write_eval_suite_artifacts(
        summary=summary,
        artifacts_dir=artifacts_dir,
    )

    if args.github_step_summary:
        write_github_step_summary(
            summary=summary,
        )

    return summary


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    summary = run_from_args(
        [
            "--config",
            args.config,
            "--artifacts-dir",
            args.artifacts_dir,
            *(
                [
                    "--github-step-summary",
                ]
                if args.github_step_summary
                else []
            ),
            *(
                [
                    "--fail-on-quality-gate",
                ]
                if args.fail_on_quality_gate
                else []
            ),
        ]
    )

    print(
        format_eval_suite_summary(
            summary,
        )
    )

    if should_fail_due_to_eval_suite_quality_gate(
        summary=summary,
        fail_on_quality_gate=args.fail_on_quality_gate,
    ):
        sys.exit(1)


if __name__ == "__main__":
    main()