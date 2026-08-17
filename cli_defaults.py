from app_settings import get_app_settings


_SETTINGS = get_app_settings()


DEMO_CLI_DEFAULT_MAX_STEPS = (
    _SETTINGS.agent.max_steps
)

OPENAI_CLI_DEFAULT_MAX_STEPS = (
    _SETTINGS.cli.openai_max_steps
)

OPENAI_CLI_DEFAULT_MAX_OUTPUT_TOKENS = (
    _SETTINGS.cli.openai_max_output_tokens
)

OPENAI_CLI_DEFAULT_REQUEST_TIMEOUT_SECONDS = (
    _SETTINGS.cli.openai_request_timeout_seconds
)


def resolve_cli_max_steps(
    *,
    llm: str,
    max_steps: int | None,
) -> int:
    if max_steps is not None:
        return max_steps

    if llm == "openai":
        return OPENAI_CLI_DEFAULT_MAX_STEPS

    return DEMO_CLI_DEFAULT_MAX_STEPS


def resolve_cli_max_output_tokens(
    *,
    max_output_tokens: int | None,
) -> int:
    if max_output_tokens is not None:
        return max_output_tokens

    return OPENAI_CLI_DEFAULT_MAX_OUTPUT_TOKENS


def resolve_cli_request_timeout_seconds(
    *,
    request_timeout_seconds: float | None,
) -> float:
    if request_timeout_seconds is not None:
        return request_timeout_seconds

    return OPENAI_CLI_DEFAULT_REQUEST_TIMEOUT_SECONDS