import subprocess
import sys


def run_command(
    command: list[str],
) -> None:
    completed_process = subprocess.run(
        command,
        check=False,
    )

    if completed_process.returncode != 0:
        sys.exit(completed_process.returncode)


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
            "run_rag_eval_profiles.py",
            "--config-dir",
            "./eval_configs",
            "--artifacts-dir",
            "./rag_eval_artifacts",
            "--github-step-summary",
            "--fail-on-quality-gate",
        ]
    )


if __name__ == "__main__":
    main()