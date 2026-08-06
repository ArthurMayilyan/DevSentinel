from cli_defaults import (
    DEMO_CLI_DEFAULT_MAX_STEPS,
    OPENAI_CLI_DEFAULT_MAX_OUTPUT_TOKENS,
    OPENAI_CLI_DEFAULT_MAX_STEPS,
    OPENAI_CLI_DEFAULT_REQUEST_TIMEOUT_SECONDS,
    resolve_cli_max_output_tokens,
    resolve_cli_max_steps,
    resolve_cli_request_timeout_seconds,
)


def test_resolve_cli_max_steps_uses_demo_default_for_demo_llm():
    assert resolve_cli_max_steps(
        llm="demo",
        max_steps=None,
    ) == DEMO_CLI_DEFAULT_MAX_STEPS


def test_resolve_cli_max_steps_uses_openai_default_for_openai_llm():
    assert resolve_cli_max_steps(
        llm="openai",
        max_steps=None,
    ) == OPENAI_CLI_DEFAULT_MAX_STEPS


def test_resolve_cli_max_steps_uses_explicit_value():
    assert resolve_cli_max_steps(
        llm="openai",
        max_steps=30,
    ) == 30


def test_resolve_cli_max_output_tokens_uses_openai_cli_default():
    assert resolve_cli_max_output_tokens(
        max_output_tokens=None,
    ) == OPENAI_CLI_DEFAULT_MAX_OUTPUT_TOKENS


def test_resolve_cli_max_output_tokens_uses_explicit_value():
    assert resolve_cli_max_output_tokens(
        max_output_tokens=500,
    ) == 500


def test_resolve_cli_request_timeout_seconds_uses_openai_cli_default():
    assert resolve_cli_request_timeout_seconds(
        request_timeout_seconds=None,
    ) == OPENAI_CLI_DEFAULT_REQUEST_TIMEOUT_SECONDS


def test_resolve_cli_request_timeout_seconds_uses_explicit_value():
    assert resolve_cli_request_timeout_seconds(
        request_timeout_seconds=20.0,
    ) == 20.0

    