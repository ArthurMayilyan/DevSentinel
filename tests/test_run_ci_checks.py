import sys
from pathlib import Path
import pytest

from scripts.run_ci_checks import run_command


def test_run_command_allows_successful_command():
    run_command(
        [
            sys.executable,
            "-c",
            "print('ok')",
        ]
    )


def test_run_command_exits_on_failed_command():
    with pytest.raises(SystemExit) as error:
        run_command(
            [
                sys.executable,
                "-c",
                "import sys; sys.exit(7)",
            ]
        )

    assert error.value.code == 7

def test_run_ci_checks_requests_github_step_summary():
    script = Path("scripts/run_ci_checks.py").read_text(
        encoding="utf-8",
    )

    assert "--github-step-summary" in script

def test_run_ci_checks_runs_unified_eval_suite():
    script = Path("scripts/run_ci_checks.py").read_text(
        encoding="utf-8",
    )

    assert "run_eval_suite.py" in script
    assert "./eval_suites/default.json" in script
    assert "./eval_suite_artifacts" in script
    assert "--github-step-summary" in script
    assert "--fail-on-quality-gate" in script    

def test_run_ci_checks_runs_unified_eval_suite():
    script = Path("scripts/run_ci_checks.py").read_text(
        encoding="utf-8",
    )

    assert "run_eval_suite.py" in script
    assert "./eval_suites/default.json" in script
    assert "./eval_suite_artifacts" in script
    assert "--fail-on-quality-gate" in script    