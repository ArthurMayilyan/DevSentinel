from collections.abc import Callable
from pathlib import Path
from typing import Any

from openai_llm_adapter import (
    DEFAULT_OPENAI_MAX_OUTPUT_TOKENS,
    DEFAULT_OPENAI_REQUEST_TIMEOUT_SECONDS,
)


DEFAULT_OPENAI_MODEL = "gpt-5.6-luna"


def load_dotenv_if_available(
    *,
    dotenv_path: str | Path = ".env",
) -> bool:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return False

    return bool(load_dotenv(dotenv_path=dotenv_path))


def create_openai_client(
    *,
    api_key: str | None = None,
    client_class: Callable[..., Any] | None = None,
    dotenv_path: str | Path = ".env",
) -> Any:
    load_dotenv_if_available(dotenv_path=dotenv_path)

    if client_class is None:
        from openai import OpenAI

        client_class = OpenAI

    if api_key is None:
        return client_class()

    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("api_key must be a non-empty string when provided.")

    return client_class(api_key=api_key)


def create_openai_llm_adapter(
    *,
    model: str = DEFAULT_OPENAI_MODEL,
    api_key: str | None = None,
    client_class: Callable[..., Any] | None = None,
    dotenv_path: str | Path = ".env",
    max_output_tokens: int = DEFAULT_OPENAI_MAX_OUTPUT_TOKENS,
    request_timeout_seconds: float = DEFAULT_OPENAI_REQUEST_TIMEOUT_SECONDS,
) -> Any:
    from openai_llm_adapter import OpenAILLMAdapter

    client = create_openai_client(
        api_key=api_key,
        client_class=client_class,
        dotenv_path=dotenv_path,
    )

    return OpenAILLMAdapter(
        client=client,
        model=model,
        max_output_tokens=max_output_tokens,
        request_timeout_seconds=request_timeout_seconds,
    )