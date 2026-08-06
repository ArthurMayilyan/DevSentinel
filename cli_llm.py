from typing import Any

from cli_defaults import (
    resolve_cli_max_output_tokens,
    resolve_cli_request_timeout_seconds,
)
from demo_llm import DemoCodeReviewLLM
from openai_client_factory import create_openai_llm_adapter


def build_llm_from_args(
    args: Any,
    *,
    openai_client_class: Any = None,
) -> Any:
    if args.llm == "demo":
        return DemoCodeReviewLLM()

    if args.llm == "openai":
        return create_openai_llm_adapter(
            model=args.model,
            client_class=openai_client_class,
            max_output_tokens=resolve_cli_max_output_tokens(
                max_output_tokens=getattr(args, "max_output_tokens", None),
            ),
            request_timeout_seconds=resolve_cli_request_timeout_seconds(
                request_timeout_seconds=getattr(args, "request_timeout_seconds", None),
            ),
        )

    raise ValueError(f"Unsupported LLM backend: {args.llm}")