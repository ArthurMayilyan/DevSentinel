import argparse
import json
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
) -> dict[str, Any]:
    output = run_strategy_comparison_from_args(
        [
            "--config",
            str(config_path),
        ]
    )

    return build_profile_run_summary(
        config_path=config_path,
        output=output,
    )


def run_profile_configs(
    config_paths: list[Path],
) -> dict[str, Any]:
    profile_summaries = [
        run_profile_config(
            config_path,
        )
        for config_path in config_paths
    ]

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

    summary = run_profile_configs(
        config_paths,
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

    return summary


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    config_paths = discover_profile_configs(
        args.config_dir,
    )

    summary = run_profile_configs(
        config_paths,
    )

    print(
        format_profiles_summary(
            summary,
        )
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

    if should_fail_due_to_profiles_quality_gate(
        summary=summary,
        fail_on_quality_gate=args.fail_on_quality_gate,
    ):
        sys.exit(1)


if __name__ == "__main__":
    main()


    