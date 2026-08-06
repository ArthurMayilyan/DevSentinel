from argparse import Namespace

from agent_config import AgentConfig
from cli_defaults import (
    OPENAI_CLI_DEFAULT_MAX_OUTPUT_TOKENS,
    OPENAI_CLI_DEFAULT_REQUEST_TIMEOUT_SECONDS,
)
from cli_run_metadata import build_run_metadata


def test_build_run_metadata_for_demo_task():
    args = Namespace(
        llm="demo",
        model="gpt-5.6-luna",
        preset=None,
        path=None,
        max_findings=5,
        max_output_tokens=None,
        request_timeout_seconds=None,
    )
    config = AgentConfig(max_steps=8)

    metadata = build_run_metadata(
        args=args,
        task="Review manually.",
        config=config,
    )

    assert metadata["llm"] == "demo"
    assert metadata["model"] is None
    assert metadata["preset"] is None
    assert metadata["path"] is None
    assert metadata["max_findings"] is None
    assert metadata["max_steps"] == 8
    assert metadata["max_output_tokens"] is None
    assert metadata["request_timeout_seconds"] is None
    assert metadata["task"] == "Review manually."


def test_build_run_metadata_for_openai_preset_uses_resolved_defaults():
    args = Namespace(
        llm="openai",
        model="gpt-5.6-luna",
        preset="code-review",
        path="./sample_project",
        max_findings=5,
        max_output_tokens=None,
        request_timeout_seconds=None,
    )
    config = AgentConfig(max_steps=15)

    metadata = build_run_metadata(
        args=args,
        task="Review ./sample_project only.",
        config=config,
    )

    assert metadata["llm"] == "openai"
    assert metadata["model"] == "gpt-5.6-luna"
    assert metadata["preset"] == "code-review"
    assert metadata["path"] == "./sample_project"
    assert metadata["max_findings"] == 5
    assert metadata["max_steps"] == 15
    assert metadata["max_output_tokens"] == OPENAI_CLI_DEFAULT_MAX_OUTPUT_TOKENS
    assert (
        metadata["request_timeout_seconds"]
        == OPENAI_CLI_DEFAULT_REQUEST_TIMEOUT_SECONDS
    )
    assert metadata["task"] == "Review ./sample_project only."


def test_build_run_metadata_for_openai_uses_explicit_limits():
    args = Namespace(
        llm="openai",
        model="gpt-5.6-luna",
        preset="code-review",
        path="./sample_project",
        max_findings=3,
        max_output_tokens=500,
        request_timeout_seconds=20.0,
    )
    config = AgentConfig(max_steps=30)

    metadata = build_run_metadata(
        args=args,
        task="Review ./sample_project only.",
        config=config,
    )

    assert metadata["max_findings"] == 3
    assert metadata["max_steps"] == 30
    assert metadata["max_output_tokens"] == 500
    assert metadata["request_timeout_seconds"] == 20.0

    