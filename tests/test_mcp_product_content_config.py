from mcp_product_content import (
    build_review_project_prompt,
)


def test_review_project_prompt_uses_configuration(
    tmp_path,
    monkeypatch,
):
    config_path = (
        tmp_path
        / "agentloop.toml"
    )

    config_path.write_text(
        """
[review]
default_reviewer = "deterministic"
max_findings = 5
max_files = 77
max_file_size_bytes = 123456

[artifacts]
default_report_path = "report.md"
reviews_dir_name = "custom-reviews"
comparisons_dir_name = "comparisons"

[presets.python-security]
profile = "security"
include_globs = [
    "src/**/*.py",
]
exclude_globs = [
    ".venv/**",
]
max_files = 42
max_file_size_bytes = 654321
""",
        encoding="utf-8",
    )

    monkeypatch.setenv(
        "AGENTLOOP_CONFIG_PATH",
        str(
            config_path,
        ),
    )

    prompt = build_review_project_prompt(
        project_path="./demo-project",
    )

    assert (
        "project_path: ./demo-project"
        in prompt
    )

    assert (
        "include_globs: src/**/*.py"
        in prompt
    )

    # Preset-specific limits override general
    # review defaults for this generated workflow.
    assert "max_files: 42" in prompt

    assert (
        "max_file_size_bytes: 654321"
        in prompt
    )

    assert (
        "reviews_dir: ./custom-reviews"
        in prompt
    )