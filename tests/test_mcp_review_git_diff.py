import subprocess
from pathlib import Path

from mcp_review_git_diff import (
    mcp_review_git_diff,
)
from mcp_server_context import (
    build_agent_loop_mcp_context,
)


def run_git(
    repository_path: Path,
    *args: str,
) -> None:
    subprocess.run(
        [
            "git",
            "-C",
            str(
                repository_path,
            ),
            *args,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )


def create_repository(
    tmp_path: Path,
) -> Path:
    repository_path = (
        tmp_path
        / "repository"
    )

    repository_path.mkdir()

    run_git(
        repository_path,
        "init",
    )

    run_git(
        repository_path,
        "branch",
        "-M",
        "main",
    )

    run_git(
        repository_path,
        "config",
        "user.email",
        "agentloop@example.com",
    )

    run_git(
        repository_path,
        "config",
        "user.name",
        "AgentLoop Test",
    )

    config_path = (
        repository_path
        / "config.py"
    )

    config_path.write_text(
        (
            'SECRET_KEY = '
            'os.environ["SECRET_KEY"]\n'
            "DEBUG = False\n"
        ),
        encoding="utf-8",
    )

    run_git(
        repository_path,
        "add",
        "-A",
    )

    run_git(
        repository_path,
        "commit",
        "-m",
        "initial",
    )

    config_path.write_text(
        (
            'SECRET_KEY = '
            '"changed-secret"\n'
            "DEBUG = True\n"
        ),
        encoding="utf-8",
    )

    run_git(
        repository_path,
        "add",
        "-A",
    )

    run_git(
        repository_path,
        "commit",
        "-m",
        "security change",
    )

    return repository_path


def test_mcp_review_git_diff_returns_serializable_payload(
    tmp_path,
):
    repository_path = (
        create_repository(
            tmp_path,
        )
    )

    context = (
        build_agent_loop_mcp_context()
    )

    payload = mcp_review_git_diff(
        context=context,
        repository_path=str(
            repository_path,
        ),
        base_ref="HEAD~1",
        target_ref="HEAD",
        preset="python-security",
        reviewer="deterministic",
        reviews_dir=str(
            tmp_path
            / "reviews",
        ),
    )

    assert (
        payload["status"]
        == "completed"
    )

    assert (
        payload["mode"]
        == "refs"
    )

    assert (
        payload[
            "changed_files_count"
        ]
        == 1
    )

    assert (
        payload[
            "selected_files_count"
        ]
        == 1
    )

    assert (
        payload[
            "findings_count"
        ]
        >= 2
    )

    finding_types = {
        finding[
            "finding_type"
        ]
        for finding
        in payload[
            "findings"
        ]
    }

    assert (
        "security.hardcoded_secret"
        in finding_types
    )

    assert (
        "security.debug_mode"
        in finding_types
    )

    assert payload[
        "run_id"
    ]

    assert Path(
        payload[
            "run_dir"
        ],
    ).exists()

    assert Path(
        payload[
            "artifacts"
        ][
            "report_markdown_path"
        ],
    ).exists()

    assert Path(
        payload[
            "artifacts"
        ][
            "report_html_path"
        ],
    ).exists()