from typing import Any

from demo_llm import DemoCodeReviewLLM
from openai_client_factory import create_openai_llm_adapter
from openai_llm_adapter import (
    DEFAULT_OPENAI_MAX_OUTPUT_TOKENS,
    DEFAULT_OPENAI_REQUEST_TIMEOUT_SECONDS,
)

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
            max_output_tokens=getattr(
                args,
                "max_output_tokens",
                DEFAULT_OPENAI_MAX_OUTPUT_TOKENS,
            ),
            request_timeout_seconds=getattr(
                args,
                "request_timeout_seconds",
                DEFAULT_OPENAI_REQUEST_TIMEOUT_SECONDS,
            ),
        )

    raise ValueError(f"Unsupported LLM backend: {args.llm}")