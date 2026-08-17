import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(
    __file__,
).resolve().parents[1]

if str(
    PROJECT_ROOT,
) not in sys.path:
    sys.path.insert(
        0,
        str(
            PROJECT_ROOT,
        ),
    )


from app_settings import get_app_settings


_SETTINGS = get_app_settings()

COMMAND_TIMEOUT_SECONDS = (
    _SETTINGS.runtime.command_timeout_seconds
)


def run_command(
    command: list[str],
) -> None:
    try:
        completed_process = subprocess.run(
            command,
            check=False,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )

    except subprocess.TimeoutExpired:
        print(
            "Command timed out after "
            f"{COMMAND_TIMEOUT_SECONDS} seconds: "
            f"{' '.join(command)}",
            file=sys.stderr,
        )

        sys.exit(
            124,
        )

    if completed_process.returncode != 0:
        sys.exit(
            completed_process.returncode,
        )


def main() -> None:
    run_command(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
        ]
    )

    run_command(
        [
            sys.executable,
            "run_eval_suite.py",
            "--config",
            "./eval_suites/default.json",
            "--artifacts-dir",
            "./eval_suite_artifacts",
            "--github-step-summary",
            "--fail-on-quality-gate",
        ]
    )


if __name__ == "__main__":
    main()