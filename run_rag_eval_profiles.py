import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from compare_rag_strategies import run_strategy_comparison_from_args


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run multiple RAG evaluation profiles.",
    )

    parser.add_argument(
        "--config-dir",
        required=True,
        help="Directory containing RAG eval profile JSON files.",
    )

    parser.add_argument(
        "--output",
        default=None,
        help="Optional path for a JSON summary of all profile runs.",
    )

    parser.add_argument(
        "--artifacts-dir",
        default=None,
        help=(
            "Optional directory where profile JSON/Markdown artifacts and "
            "suite summaries should be written."
        ),
    )   

    parser.add_argument(
        "--github-step-summary",
        action="store_true",
        help=(
            "Write the profiles Markdown summary to GitHub Actions step summary "
            "when GITHUB_STEP_SUMMARY is available."
        ),
    )     

    parser.add_argument(
        "--fail-on-quality-gate",
        action="store_true",
        help="Exit with code 1 if any profile quality gate fails.",
    )


    return parser


def discover_profile_configs(
    config_dir: str,
) -> list[Path]:
    directory = Path(config_dir)

    if not directory.is_dir():
        raise ValueError(f"config_dir must be a directory: {config_dir}")

    configs = sorted(
        path
        for path in directory.glob("*.json")
        if path.is_file()
    )

    if not configs:
        raise ValueError(
            f"config_dir contains no JSON config files: {config_dir}"
        )

    return configs


def build_profile_artifacts_dir(
    *,
    artifacts_dir: Path,
    config_path: Path,
) -> Path:
    return artifacts_dir / config_path.stem


def build_profile_artifact_paths(
    *,
    artifacts_dir: Path,
    config_path: Path,
) -> dict[str, Path]:
    profile_dir = build_profile_artifacts_dir(
        artifacts_dir=artifacts_dir,
        config_path=config_path,
    )

    return {
        "profile_dir": profile_dir,
        "comparison_json": profile_dir / "comparison.json",
        "report_markdown": profile_dir / "report.md",
    }

def format_artifact_link_path(
    path: str,
) -> str:
    return path.replace("\\", "/")


def ensure_artifact_directories(
    *,
    artifact_paths: dict[str, Path],
) -> None:
    artifact_paths["profile_dir"].mkdir(
        parents=True,
        exist_ok=True,
    )


def get_profile_quality_gate_status(
    output: dict[str, Any],
) -> str:
    quality_gate = output.get("quality_gate")

    if quality_gate is None:
        return "not_configured"

    if quality_gate["passed"]:
        return "passed"

    return "failed"


def build_profile_run_summary(
    *,
    config_path: Path,
    output: dict[str, Any],
) -> dict[str, Any]:
    return {
        "profile": config_path.name,
        "config_path": str(config_path),
        "best_strategy": output.get("best_strategy"),
        "best_accepted_strategy": output.get("best_accepted_strategy"),
        "quality_gate_status": get_profile_quality_gate_status(
            output,
        ),
        "quality_gate": output.get("quality_gate"),
    }


def run_profile_config(
    config_path: Path,
    artifact_paths: dict[str, Path] | None = None,
) -> dict[str, Any]:
    raw_args = [
        "--config",
        str(config_path),
    ]

    if artifact_paths is not None:
        ensure_artifact_directories(
            artifact_paths=artifact_paths,
        )

        raw_args.extend(
            [
                "--output",
                str(artifact_paths["comparison_json"]),
                "--report-output",
                str(artifact_paths["report_markdown"]),
            ]
        )

    output = run_strategy_comparison_from_args(
        raw_args,
    )

    summary = build_profile_run_summary(
        config_path=config_path,
        output=output,
    )

    if artifact_paths is not None:
        summary["artifacts"] = {
            "comparison_json": str(artifact_paths["comparison_json"]),
            "report_markdown": str(artifact_paths["report_markdown"]),
        }

    return summary


def run_profile_configs(
    config_paths: list[Path],
    artifacts_dir: Path | None = None,
) -> dict[str, Any]:
    profile_summaries = []

    for config_path in config_paths:
        artifact_paths = None

        if artifacts_dir is not None:
            artifact_paths = build_profile_artifact_paths(
                artifacts_dir=artifacts_dir,
                config_path=config_path,
            )

        profile_summaries.append(
            run_profile_config(
                config_path=config_path,
                artifact_paths=artifact_paths,
            )
        )

    failed_profiles = [
        summary["profile"]
        for summary in profile_summaries
        if summary["quality_gate_status"] == "failed"
    ]

    return {
        "profiles": profile_summaries,
        "failed_profiles": failed_profiles,
        "passed": len(failed_profiles) == 0,
    }


def format_profiles_summary(
    summary: dict[str, Any],
) -> str:
    lines = [
        "RAG eval profiles",
        "profile                         quality_gate  best_accepted_strategy",
    ]

    for profile in summary["profiles"]:
        lines.append(
            f"{profile['profile']:<31} "
            f"{profile['quality_gate_status']:<13} "
            f"{profile['best_accepted_strategy']}"
        )

    lines.extend(
        [
            "",
            f"Overall: {'passed' if summary['passed'] else 'failed'}",
        ]
    )

    if summary["failed_profiles"]:
        lines.append(
            "Failed profiles: "
            + ", ".join(summary["failed_profiles"])
        )

    return "\n".join(lines)


def format_profiles_markdown_summary(
    summary: dict[str, Any],
) -> str:
    lines = [
        "# RAG Eval Profiles Summary",
        "",
        "| Profile | Quality gate | Best accepted strategy |",
        "|---|---|---|",
    ]

    for profile in summary["profiles"]:
        lines.append(
            "| "
            f"{profile['profile']} | "
            f"{profile['quality_gate_status']} | "
            f"{profile['best_accepted_strategy']} |"
        )

    lines.extend(
        [
            "",
            f"Overall: **{'passed' if summary['passed'] else 'failed'}**",
        ]
    )

    if summary["failed_profiles"]:
        lines.extend(
            [
                "",
                "Failed profiles: "
                + ", ".join(summary["failed_profiles"]),
            ]
        )

    lines.append("")

    return "\n".join(lines)


def format_profiles_artifact_index(
    summary: dict[str, Any],
) -> str:
    lines = [
        "# RAG Eval Artifact Index",
        "",
        f"Overall: **{'passed' if summary['passed'] else 'failed'}**",
        "",
        "| Profile | Quality gate | Best accepted strategy | Report | JSON |",
        "|---|---|---|---|---|",
    ]

    for profile in summary["profiles"]:
        artifacts = profile.get("artifacts", {})

        report_path = artifacts.get(
            "report_markdown",
            "",
        )
        comparison_path = artifacts.get(
            "comparison_json",
            "",
        )

        lines.append(
            "| "
            f"{profile['profile']} | "
            f"{profile['quality_gate_status']} | "
            f"{profile['best_accepted_strategy']} | "
            f"{format_artifact_link_path(report_path)} | "
            f"{format_artifact_link_path(comparison_path)} |"
        )

    if summary["failed_profiles"]:
        lines.extend(
            [
                "",
                "Failed profiles: "
                + ", ".join(summary["failed_profiles"]),
            ]
        )

    lines.append("")

    return "\n".join(lines)


def write_suite_artifacts(
    *,
    summary: dict[str, Any],
    artifacts_dir: Path,
) -> None:
    artifacts_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary_json_path = artifacts_dir / "profiles_summary.json"
    summary_json_path.write_text(
        json.dumps(
            summary,
            indent=2,
        ),
        encoding="utf-8",
    )

    summary_markdown_path = artifacts_dir / "profiles_summary.md"
    summary_markdown_path.write_text(
        format_profiles_markdown_summary(
            summary,
        ),
        encoding="utf-8",
    )

    index_markdown_path = artifacts_dir / "index.md"
    index_markdown_path.write_text(
        format_profiles_artifact_index(
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
        format_profiles_markdown_summary(
            summary,
        ),
        encoding="utf-8",
    )

    return True

def should_fail_due_to_profiles_quality_gate(
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

    config_paths = discover_profile_configs(
        args.config_dir,
    )

    artifacts_dir = (
        Path(args.artifacts_dir)
        if args.artifacts_dir is not None
        else None
    )

    summary = run_profile_configs(
        config_paths,
        artifacts_dir=artifacts_dir,
    )

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(
            json.dumps(
                summary,
                indent=2,
            ),
            encoding="utf-8",
        )

    if artifacts_dir is not None:
        write_suite_artifacts(
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

    raw_args = [
        "--config-dir",
        args.config_dir,
    ]

    if args.output is not None:
        raw_args.extend(
            [
                "--output",
                args.output,
            ]
        )

    if args.artifacts_dir is not None:
        raw_args.extend(
            [
                "--artifacts-dir",
                args.artifacts_dir,
            ]
        )

    if args.github_step_summary:
        raw_args.append(
            "--github-step-summary",
        )

    if args.fail_on_quality_gate:
        raw_args.append(
            "--fail-on-quality-gate",
        )

    summary = run_from_args(
        raw_args,
    )

    print(
        format_profiles_summary(
            summary,
        )
    )

    if should_fail_due_to_profiles_quality_gate(
        summary=summary,
        fail_on_quality_gate=args.fail_on_quality_gate,
    ):
        sys.exit(1)


if __name__ == "__main__":
    main()


