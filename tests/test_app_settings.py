from pathlib import Path

import pytest

from app_settings import (
    load_app_settings,
)


def write_config(
    path: Path,
    content: str,
) -> None:
    path.write_text(
        content,
        encoding="utf-8",
    )


def test_load_app_settings_reads_project_config():
    settings = load_app_settings()

    assert settings.openai.model == "gpt-5.6-luna"
    assert settings.openai.request_timeout_seconds == 30.0
    assert settings.openai.max_output_tokens == 500
    assert settings.openai.review_max_content_chars == 12000

    assert settings.runtime.command_timeout_seconds == 120.0

    assert settings.review.max_files == 200
    assert settings.review.max_file_size_bytes == 200000

    assert settings.rag.top_k == 3
    assert settings.rag.chunk_max_chars == 1000
    assert settings.rag.chunk_overlap_chars == 100

    assert "python-security" in settings.presets
    assert "typescript-security" in settings.presets
    assert "general-security" in settings.presets


def test_environment_overrides_toml(tmp_path):
    config_path = tmp_path / "agentloop.toml"

    write_config(
        config_path,
        """
[openai]
model = "from-config"
request_timeout_seconds = 20
max_output_tokens = 300
review_max_content_chars = 5000

[runtime]
agent_mode_max_steps = 4
command_timeout_seconds = 60

[review]
default_reviewer = "deterministic"
max_findings = 5
max_files = 100
max_file_size_bytes = 100000

[rag]
top_k = 3
chunk_max_chars = 1000
chunk_overlap_chars = 100
agent_max_steps = 4
retrieval_strategy = "default"
""",
    )

    settings = load_app_settings(
        config_path=config_path,
        environ={
            "AGENTLOOP_OPENAI_MODEL": "from-environment",
            "AGENTLOOP_OPENAI_REQUEST_TIMEOUT_SECONDS": "45",
            "AGENTLOOP_COMMAND_TIMEOUT_SECONDS": "90",
            "AGENTLOOP_REVIEW_MAX_FILES": "250",
            "AGENTLOOP_RAG_TOP_K": "5",
        },
    )

    assert settings.openai.model == "from-environment"
    assert settings.openai.request_timeout_seconds == 45.0
    assert settings.runtime.command_timeout_seconds == 90.0
    assert settings.review.max_files == 250
    assert settings.rag.top_k == 5


def test_config_path_can_come_from_environment(tmp_path):
    config_path = tmp_path / "custom.toml"

    write_config(
        config_path,
        """
[openai]
model = "custom-model"
""",
    )

    settings = load_app_settings(
        environ={
            "AGENTLOOP_CONFIG_PATH": str(
                config_path,
            ),
        },
    )

    assert settings.openai.model == "custom-model"

    assert settings.config_path == str(
        config_path.resolve(),
    )


def test_invalid_rag_overlap_is_rejected(tmp_path):
    config_path = tmp_path / "invalid.toml"

    write_config(
        config_path,
        """
[rag]
chunk_max_chars = 100
chunk_overlap_chars = 100
""",
    )

    with pytest.raises(
        ValueError,
        match="chunk_overlap_chars",
    ):
        load_app_settings(
            config_path=config_path,
            environ={},
        )


def test_invalid_timeout_is_rejected(tmp_path):
    config_path = tmp_path / "invalid.toml"

    write_config(
        config_path,
        """
[openai]
request_timeout_seconds = 0
""",
    )

    with pytest.raises(
        ValueError,
        match="request_timeout_seconds",
    ):
        load_app_settings(
            config_path=config_path,
            environ={},
        )


def test_workspace_presets_are_loaded_from_toml():
    settings = load_app_settings()

    preset = settings.presets[
        "python-security"
    ]

    assert preset.profile == "security"

    assert preset.include_globs == (
        "**/*.py",
    )

    assert ".venv/**" in preset.exclude_globs

    assert preset.max_files == 200