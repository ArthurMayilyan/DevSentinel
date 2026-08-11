import sys

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