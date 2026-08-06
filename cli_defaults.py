from agent_config import AgentConfig


DEMO_CLI_DEFAULT_MAX_STEPS = AgentConfig().max_steps

OPENAI_CLI_DEFAULT_MAX_STEPS = 15
OPENAI_CLI_DEFAULT_MAX_OUTPUT_TOKENS = 250
OPENAI_CLI_DEFAULT_REQUEST_TIMEOUT_SECONDS = 10.0


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

