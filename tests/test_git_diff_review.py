import subprocess
from pathlib import Path

import pytest

from git_diff_review import (
    get_git_changed_files,
    parse_git_name_status_z,
    review_git_diff,
)
from mcp_server_context import (
    build_agent_loop_mcp_context,
)


def run_git(
    repository_path: Path,
    *args: str,
) -> str:
    completed = subprocess.run(
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

    return completed.stdout


def create_git_repository(
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

    return repository_path


def commit_all(
    repository_path: Path,
    message: str,
) -> None:
    run_git(
        repository_path,
        "add",
        "-A",
    )

    run_git(
        repository_path,
        "commit",
        "-m",
        message,
    )


def test_parse_git_name_status_z_supports_rename_and_delete():
    changed_files = (
        parse_git_name_status_z(
            "M\x00app.py\x00"
            "R100\x00old.py\x00new.py\x00"
            "D\x00gone.py\x00"
        )
    )

    assert [
        item.status
        for item in changed_files
    ] == [
        "M",
        "R100",
        "D",
    ]

    assert (
        changed_files[0].path
        == "app.py"
    )

    assert (
        changed_files[1].old_path
        == "old.py"
    )

    assert (
        changed_files[1].path
        == "new.py"
    )

    assert (
        changed_files[2].path
        == "gone.py"
    )


def test_get_git_changed_files_compares_refs(
    tmp_path,
):
    repository_path = (
        create_git_repository(
            tmp_path,
        )
    )

    (
        repository_path
        / "config.py"
    ).write_text(
        'SECRET_KEY = os.environ["SECRET_KEY"]\n',
        encoding="utf-8",
    )

    commit_all(
        repository_path,
        "initial",
    )

    (
        repository_path
        / "config.py"
    ).write_text(
        'SECRET_KEY = "secret"\n',
        encoding="utf-8",
    )

    (
        repository_path
        / "README.md"
    ).write_text(
        "changed\n",
        encoding="utf-8",
    )

    commit_all(
        repository_path,
        "changed",
    )

    changed_files = (
        get_git_changed_files(
            repository_path=str(
                repository_path,
            ),
            base_ref="HEAD~1",
            target_ref="HEAD",
        )
    )

    assert {
        item.path
        for item in changed_files
    } == {
        "README.md",
        "config.py",
    }


def test_review_git_diff_reviews_only_selected_changed_files(
    tmp_path,
):
    repository_path = (
        create_git_repository(
            tmp_path,
        )
    )

    (
        repository_path
        / "config.py"
    ).write_text(
        (
            'SECRET_KEY = os.environ["SECRET_KEY"]\n'
            "DEBUG = False\n"
        ),
        encoding="utf-8",
    )

    (
        repository_path
        / "deleted.py"
    ).write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )

    (
        repository_path
        / "README.md"
    ).write_text(
        "initial\n",
        encoding="utf-8",
    )

    commit_all(
        repository_path,
        "initial",
    )

    (
        repository_path
        / "config.py"
    ).write_text(
        (
            'SECRET_KEY = "secret"\n'
            "DEBUG = True\n"
        ),
        encoding="utf-8",
    )

    (
        repository_path
        / "README.md"
    ).write_text(
        "changed\n",
        encoding="utf-8",
    )

    (
        repository_path
        / "deleted.py"
    ).unlink()

    commit_all(
        repository_path,
        "security regression",
    )

    reviews_dir = (
        tmp_path
        / "reviews"
    )

    context = (
        build_agent_loop_mcp_context()
    )

    result = review_git_diff(
        context=context,
        repository_path=str(
            repository_path,
        ),
        base_ref="HEAD~1",
        target_ref="HEAD",
        preset="python-security",
        reviewer="deterministic",
        reviews_dir=str(
            reviews_dir,
        ),
    )

    assert result.status == "completed"
    assert result.mode == "refs"

    assert (
        result.changed_files_count
        == 3
    )

    # Only config.py matches python-security.
    # README is excluded by include_globs,
    # deleted.py cannot be reviewed.
    assert (
        result.selected_files_count
        == 1
    )

    assert (
        result.skipped_files_count
        == 2
    )

    assert (
        result.findings_count
        >= 2
    )

    finding_types = {
        finding[
            "finding_type"
        ]
        for finding in result.findings
    }

    assert (
        "security.hardcoded_secret"
        in finding_types
    )

    assert (
        "security.debug_mode"
        in finding_types
    )

    skipped_reasons = {
        item[
            "reason"
        ]
        for item in result.skipped_files
    }

    assert (
        "deleted"
        in skipped_reasons
    )

    assert (
        "not_included_by_preset"
        in skipped_reasons
    )

    assert result.run_id

    assert Path(
        result.run_dir,
    ).exists()

    assert Path(
        result.artifacts[
            "report_markdown_path"
        ],
    ).exists()

    assert Path(
        result.artifacts[
            "report_html_path"
        ],
    ).exists()

    assert Path(
        result.artifacts[
            "findings_json_path"
        ],
    ).exists()

    assert Path(
        result.artifacts[
            "run_config_json_path"
        ],
    ).exists()


def test_review_git_diff_staged_mode_reads_index_snapshot(
    tmp_path,
):
    repository_path = (
        create_git_repository(
            tmp_path,
        )
    )

    config_path = (
        repository_path
        / "config.py"
    )

    config_path.write_text(
        'SECRET_KEY = os.environ["SECRET_KEY"]\n',
        encoding="utf-8",
    )

    commit_all(
        repository_path,
        "initial",
    )

    # Put insecure version into Git index.
    config_path.write_text(
        'SECRET_KEY = "staged-secret"\n',
        encoding="utf-8",
    )

    run_git(
        repository_path,
        "add",
        "config.py",
    )

    # Now make the working tree safe again WITHOUT staging it.
    #
    # If review_git_diff incorrectly reads the working tree,
    # it will see no hardcoded secret.
    #
    # If it correctly reads the Git index, it will detect it.
    config_path.write_text(
        'SECRET_KEY = os.environ["SECRET_KEY"]\n',
        encoding="utf-8",
    )

    context = (
        build_agent_loop_mcp_context()
    )

    result = review_git_diff(
        context=context,
        repository_path=str(
            repository_path,
        ),
        staged_only=True,
        preset="python-security",
        reviewer="deterministic",
        reviews_dir=str(
            tmp_path
            / "reviews",
        ),
    )

    assert result.mode == "staged"

    assert (
        result.changed_files_count
        == 1
    )

    assert (
        result.selected_files_count
        == 1
    )

    finding_types = {
        finding[
            "finding_type"
        ]
        for finding in result.findings
    }

    assert (
        "security.hardcoded_secret"
        in finding_types
    )

    # Refs are intentionally empty in staged mode.
    assert result.base_ref == ""
    assert result.target_ref == ""


def test_review_git_diff_rejects_non_git_directory(
    tmp_path,
):
    context = (
        build_agent_loop_mcp_context()
    )

    with pytest.raises(
        ValueError,
        match="Git",
    ):
        review_git_diff(
            context=context,
            repository_path=str(
                tmp_path,
            ),
            reviews_dir=str(
                tmp_path
                / "reviews",
            ),
        )