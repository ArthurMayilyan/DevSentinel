from app_settings import get_app_settings
from agent_config import AgentConfig
from cli_defaults import (
    OPENAI_CLI_DEFAULT_MAX_OUTPUT_TOKENS,
    OPENAI_CLI_DEFAULT_MAX_STEPS,
    OPENAI_CLI_DEFAULT_REQUEST_TIMEOUT_SECONDS,
)
from openai_client_factory import (
    DEFAULT_OPENAI_MODEL,
)
from openai_llm_adapter import (
    DEFAULT_OPENAI_MAX_OUTPUT_TOKENS,
    DEFAULT_OPENAI_REQUEST_TIMEOUT_SECONDS,
)
from project_path_safety import (
    DEFAULT_MAX_FILES,
    DEFAULT_MAX_FILE_SIZE_BYTES,
)
from rag_defaults import (
    DEFAULT_RAG_AGENT_MAX_STEPS,
    DEFAULT_RAG_CHUNK_MAX_CHARS,
    DEFAULT_RAG_CHUNK_OVERLAP_CHARS,
    DEFAULT_RAG_TOP_K,
)
from reviewer_config import (
    DEFAULT_OPENAI_REVIEW_MODEL,
    DEFAULT_REVIEWER,
)
from task_presets import (
    DEFAULT_CODE_REVIEW_MAX_FINDINGS,
)
from workspace_review_presets import (
    get_workspace_review_preset,
)


def test_runtime_defaults_match_agentloop_config():
    settings = get_app_settings()

    assert DEFAULT_OPENAI_MODEL == (
        settings.openai.model
    )

    assert DEFAULT_OPENAI_REVIEW_MODEL == (
        settings.openai.model
    )

    assert DEFAULT_OPENAI_MAX_OUTPUT_TOKENS == (
        settings.openai.max_output_tokens
    )

    assert (
        DEFAULT_OPENAI_REQUEST_TIMEOUT_SECONDS
        == settings.openai.request_timeout_seconds
    )

    assert DEFAULT_REVIEWER == (
        settings.review.default_reviewer
    )

    assert DEFAULT_MAX_FILES == (
        settings.review.max_files
    )

    assert DEFAULT_MAX_FILE_SIZE_BYTES == (
        settings.review.max_file_size_bytes
    )

    assert DEFAULT_CODE_REVIEW_MAX_FINDINGS == (
        settings.review.max_findings
    )


def test_agent_defaults_match_agentloop_config():
    settings = get_app_settings()

    config = AgentConfig()

    assert config.max_steps == (
        settings.agent.max_steps
    )

    assert config.max_rejected_final_answers == (
        settings.agent.max_rejected_final_answers
    )

    assert config.max_rejected_tool_calls == (
        settings.agent.max_rejected_tool_calls
    )

    assert config.max_invalid_llm_outputs == (
        settings.agent.max_invalid_llm_outputs
    )


def test_cli_defaults_match_agentloop_config():
    settings = get_app_settings()

    assert OPENAI_CLI_DEFAULT_MAX_STEPS == (
        settings.cli.openai_max_steps
    )

    assert (
        OPENAI_CLI_DEFAULT_MAX_OUTPUT_TOKENS
        == settings.cli.openai_max_output_tokens
    )

    assert (
        OPENAI_CLI_DEFAULT_REQUEST_TIMEOUT_SECONDS
        == settings.cli.openai_request_timeout_seconds
    )


def test_rag_defaults_match_agentloop_config():
    settings = get_app_settings()

    assert DEFAULT_RAG_TOP_K == (
        settings.rag.top_k
    )

    assert DEFAULT_RAG_CHUNK_MAX_CHARS == (
        settings.rag.chunk_max_chars
    )

    assert DEFAULT_RAG_CHUNK_OVERLAP_CHARS == (
        settings.rag.chunk_overlap_chars
    )

    assert DEFAULT_RAG_AGENT_MAX_STEPS == (
        settings.rag.agent_max_steps
    )


def test_workspace_preset_is_loaded_from_agentloop_config():
    settings = get_app_settings()

    preset = get_workspace_review_preset(
        "python-security",
    )

    source = settings.presets[
        "python-security"
    ]

    assert preset.profile == source.profile

    assert preset.include_globs == ",".join(
        source.include_globs,
    )

    assert preset.exclude_globs == ",".join(
        source.exclude_globs,
    )

    assert preset.max_files == (
        source.max_files
    )

    assert preset.max_file_size_bytes == (
        source.max_file_size_bytes
    )