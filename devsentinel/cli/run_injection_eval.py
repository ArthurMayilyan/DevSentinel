import argparse
import json
import os
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devsentinel.cli.cli_defaults import (
    resolve_cli_max_output_tokens,
    resolve_cli_request_timeout_seconds,
)
from devsentinel.llm.injection_fake_llm import InjectionFollowingFakeLLM
from devsentinel.llm.openai_client_factory import (
    DEFAULT_OPENAI_MODEL,
    create_openai_llm_adapter,
    load_dotenv_if_available,
)
from devsentinel.llm.openai_llm_adapter import DEFAULT_OPENAI_MAX_OUTPUT_TOKENS
from devsentinel.review.injection_eval import (
    DEFAULT_MAX_FINDINGS,
    DEFAULT_MAX_RUNS,
    DEFAULT_MAX_STEPS,
    DEFAULT_REPETITIONS,
    MODE_DRY_RUN,
    MODE_LIVE,
    InjectionEvalConfig,
    format_injection_eval_markdown,
    run_injection_eval,
)


DEFAULT_CONTROL_PROJECT = "./sample_project"
DEFAULT_ATTACK_PROJECT = "./adversarial_project"
DEFAULT_CASES_PATH = "./eval_cases/injection_eval_cases.json"
DEFAULT_OUTPUT_DIR = "./eval_results"
DEFAULT_ARTIFACTS_DIR = "./injection_eval_artifacts"
DEFAULT_LIVE_REQUEST_TIMEOUT_SECONDS = 60.0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the prompt-injection evaluation. Dry run (scripted fake LLM, "
            "no network) unless --live is given."
        ),
    )

    parser.add_argument("--live", action="store_true",
                        help="Call the OpenAI model. Requires OPENAI_API_KEY.")
    parser.add_argument("--model", default=DEFAULT_OPENAI_MODEL)
    parser.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS,
                        help="Runs per condition (control and attack).")
    parser.add_argument("--max-runs", type=int, default=DEFAULT_MAX_RUNS,
                        help="Cost guard: refuse to start more than this many runs in total.")
    parser.add_argument("--max-steps", type=int, default=DEFAULT_MAX_STEPS)
    parser.add_argument("--max-findings", type=int, default=DEFAULT_MAX_FINDINGS)
    parser.add_argument("--max-output-tokens", type=int, default=DEFAULT_OPENAI_MAX_OUTPUT_TOKENS)
    parser.add_argument("--request-timeout-seconds", type=float,
                        default=DEFAULT_LIVE_REQUEST_TIMEOUT_SECONDS)
    parser.add_argument("--control-project", default=DEFAULT_CONTROL_PROJECT)
    parser.add_argument("--attack-project", default=DEFAULT_ATTACK_PROJECT)
    parser.add_argument("--cases", default=DEFAULT_CASES_PATH)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR,
                        help="Where the JSON results and Markdown summary are written.")
    parser.add_argument("--artifacts-dir", default=DEFAULT_ARTIFACTS_DIR,
                        help="Where raw per-run traces are copied (gitignored by default).")
    parser.add_argument("--fail-on-quality-gate", action="store_true",
                        help="Exit 1 if the application-level quality gate fails.")

    return parser


def require_openai_api_key(
    env: dict[str, str] | None = None,
) -> None:
    load_dotenv_if_available()
    environment = os.environ if env is None else env

    if not environment.get("OPENAI_API_KEY"):
        raise ValueError(
            "--live requires OPENAI_API_KEY in the environment or .env."
        )


def build_llm_factory(
    *,
    args: argparse.Namespace,
    openai_client_class: Any = None,
) -> Callable[[], Any]:
    if not args.live:
        return InjectionFollowingFakeLLM

    def create_live_llm() -> Any:
        return create_openai_llm_adapter(
            model=args.model,
            client_class=openai_client_class,
            max_output_tokens=resolve_cli_max_output_tokens(
                max_output_tokens=args.max_output_tokens,
            ),
            request_timeout_seconds=resolve_cli_request_timeout_seconds(
                request_timeout_seconds=args.request_timeout_seconds,
            ),
        )

    return create_live_llm


def build_config(
    args: argparse.Namespace,
) -> InjectionEvalConfig:
    return InjectionEvalConfig(
        control_project=Path(args.control_project),
        attack_project=Path(args.attack_project),
        cases_path=Path(args.cases),
        mode=MODE_LIVE if args.live else MODE_DRY_RUN,
        repetitions=args.repetitions,
        max_runs=args.max_runs,
        max_steps=args.max_steps,
        max_findings=args.max_findings,
        model=args.model if args.live else "",
        max_output_tokens=args.max_output_tokens if args.live else None,
        request_timeout_seconds=args.request_timeout_seconds if args.live else None,
        artifacts_dir=Path(args.artifacts_dir) if args.artifacts_dir else None,
    )


def build_output_paths(
    *,
    output_dir: Path,
    mode: str,
    started_at: datetime,
) -> tuple[Path, Path]:
    suffix = "" if mode == MODE_LIVE else "_dry_run"
    stem = f"injection_eval_{started_at.strftime('%Y%m%d')}{suffix}"

    return (
        output_dir / f"{stem}.json",
        output_dir / f"{stem}.md",
    )


def run_from_args(
    raw_args: list[str] | None = None,
    *,
    openai_client_class: Any = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    args = build_arg_parser().parse_args(raw_args)

    if args.live and openai_client_class is None:
        require_openai_api_key(env)

    config = build_config(args)
    started_at = datetime.now(timezone.utc)

    result = run_injection_eval(
        config=config,
        llm_factory=build_llm_factory(
            args=args,
            openai_client_class=openai_client_class,
        ),
        started_at=started_at,
    )

    json_path, markdown_path = build_output_paths(
        output_dir=Path(args.output_dir),
        mode=config.mode,
        started_at=started_at,
    )

    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(format_injection_eval_markdown(result), encoding="utf-8")

    result["output_paths"] = {
        "json": str(json_path),
        "markdown": str(markdown_path),
    }

    return result


def main() -> None:
    args = build_arg_parser().parse_args()
    result = run_from_args(sys.argv[1:])

    print(format_injection_eval_markdown(result))
    print(f"Results: {result['output_paths']['json']}")
    print(f"Summary: {result['output_paths']['markdown']}")

    if args.fail_on_quality_gate and not result["quality_gate"]["passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
